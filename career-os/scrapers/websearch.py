#!/usr/bin/env python3
"""
Web search-based job scraper — best-effort from China.
Tries Bing CN and DuckDuckGo, but both are unreliable from mainland China.
The real value comes from API-based scrapers (Greenhouse, Ashby).

This scraper is a fallback — if it finds nothing, that's expected.
The agent-driven cron job uses Hermes web_search which has a better backend.
"""
import json, sys, os, re, time, random
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.parse import quote_plus
from urllib.error import URLError, HTTPError

# Simplified queries — fewer, more targeted
QUERIES = [
    # Job board searches (if Bing cooperates)
    'site:indeed.com "product manager" Singapore "Hong Kong"',
    'site:jobsdb.com "product manager" OR "program manager" "Hong Kong" Singapore',
    '"senior product manager" OR "head of product" Shenzhen OR "Hong Kong" OR Singapore',
    '"business operations" OR "bizops" manager Singapore OR "Hong Kong" fintech',
    '"growth manager" OR "head of growth" APAC Singapore OR Shenzhen',
    '"cross-border" ecommerce product manager China OR Singapore',
    '"general manager" OR "country manager" fintech ecommerce APAC',
    '"chief of staff" tech Singapore OR "Hong Kong" OR Shenzhen',
]

TITLE_KEYWORDS = [
    "product manager", "product director", "head of product", "vp product",
    "product lead", "principal product", "senior product",
    "business operations", "bizops", "strategy", "strategic",
    "chief of staff", "corporate strategy", "business strategy",
    "head of growth", "growth manager", "growth lead",
    "general manager", "country manager", "regional manager",
    "program manager", "project manager",
    "cross-border", "e-commerce", "ecommerce", "marketplace",
]

BLOCKED_DOMAINS = [
    "linkedin.com", "glassdoor.com", "google.com",
    "twitter.com", "x.com", "facebook.com",
]


def try_bing(query, max_results=8):
    """Try Bing CN — often fails from China for English queries."""
    try:
        encoded = quote_plus(query)
        url = f"https://www.bing.com/search?q={encoded}&mkt=en-US&setlang=en"
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        })
        with urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        results = []
        for m in re.finditer(
            r'class="b_algo"[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
            html, re.DOTALL
        ):
            link = m.group(1)
            title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            if any(d in link.lower() for d in BLOCKED_DOMAINS):
                continue
            if title and link.startswith("http") and len(title) > 10:
                # Skip dictionary/encyclopedia results
                if any(kw in link.lower() for kw in ["iciba", "baike", "zhihu", "dict"]):
                    continue
                results.append({"title": title, "url": link, "snippet": ""})
        return results[:max_results]
    except Exception:
        return []


def try_ddg(query, max_results=8):
    """Try DuckDuckGo — often blocked or slow from China."""
    try:
        encoded = quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36",
        })
        with urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        results = []
        for m in re.finditer(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
            html, re.DOTALL
        ):
            link = m.group(1)
            title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            if "uddg=" in link:
                um = re.search(r'uddg=([^&]+)', link)
                if um:
                    from urllib.parse import unquote
                    link = unquote(um.group(1))
            if any(d in link.lower() for d in BLOCKED_DOMAINS):
                continue
            if title and link.startswith("http"):
                results.append({"title": title, "url": link, "snippet": ""})
        return results[:max_results]
    except Exception:
        return []


def search(query, max_results=8):
    """Try Bing first, fall back to DDG."""
    results = try_bing(query, max_results)
    if results:
        return results
    return try_ddg(query, max_results)


def extract_source(url):
    url_lower = url.lower()
    if "indeed.com" in url_lower: return "indeed"
    if "jobsdb.com" in url_lower: return "jobsdb"
    if "greenhouse.io" in url_lower: return "greenhouse"
    if "ashbyhq.com" in url_lower: return "ashby"
    if "bytedance" in url_lower or "tiktok" in url_lower: return "bytedance"
    if "shopee" in url_lower: return "shopee"
    if "zhipin.com" in url_lower: return "boss_zhipin"
    if "liepin.com" in url_lower: return "liepin"
    return "web_search"


def extract_company(title, url):
    at_match = re.search(r'\s+(?:at|@)\s+([^-|–]+?)(?:\s*[-|–]|\s*$)', title, re.IGNORECASE)
    if at_match:
        return at_match.group(1).strip()
    dash_match = re.search(r'[-|–]\s*([^-|–]+?)$', title)
    if dash_match:
        candidate = dash_match.group(1).strip()
        if len(candidate) < 50 and not any(kw in candidate.lower()
                for kw in ["singapore", "hong kong", "remote", "shenzhen"]):
            return candidate
    return ""


def extract_location(title, snippet):
    text = f"{title} {snippet}".lower()
    for loc, keywords in {
        "Singapore": ["singapore"], "Hong Kong": ["hong kong"],
        "Shenzhen": ["shenzhen"], "Guangzhou": ["guangzhou"],
        "Shanghai": ["shanghai"], "Beijing": ["beijing"],
    }.items():
        if any(kw in text for kw in keywords):
            return loc
    return ""


def is_relevant(title, snippet):
    text = f"{title} {snippet}".lower()
    has_title = any(kw in text for kw in TITLE_KEYWORDS)
    has_senior = any(kw in text for kw in [
        "senior", "director", "head", "vp", "principal", "lead", "manager",
        "总监", "负责人", "资深", "高级"
    ])
    return has_title and has_senior


def classify_role_type(title):
    t = title.lower()
    if "chief of staff" in t: return "Chief of Staff"
    if "business operations" in t or "bizops" in t: return "Business Operations"
    if "strategy" in t or "strategic" in t: return "Strategy/Ops"
    if "general manager" in t or "country manager" in t: return "General Manager"
    if "growth" in t or "expansion" in t: return "Growth/Expansion"
    if "product" in t: return "Product Management"
    if "program" in t or "project" in t: return "Program Management"
    return "Other"


def main():
    print(f"Web search scraper: running {len(QUERIES)} queries (best-effort from China)...")
    all_results = []

    for i, query in enumerate(QUERIES):
        print(f"  [{i+1}/{len(QUERIES)}] {query[:70]}...")
        results = search(query, max_results=8)
        if results:
            print(f"    → {len(results)} results")
        else:
            print(f"    → 0 results (expected from China)")
        all_results.extend(results)
        time.sleep(2 + random.uniform(0, 1))

    print(f"\nRaw results: {len(all_results)}")

    seen_urls = set()
    formatted = []
    for r in all_results:
        url = r.get("url", "")
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        if not url or not title or url in seen_urls:
            continue
        if any(d in url.lower() for d in BLOCKED_DOMAINS):
            continue
        if not is_relevant(title, snippet):
            continue
        seen_urls.add(url)
        formatted.append({
            "title": title,
            "company": extract_company(title, url),
            "location": extract_location(title, snippet),
            "grade": "A-2",
            "url": url,
            "role_type": classify_role_type(title),
            "salary": "",
            "scanned_date": datetime.now().strftime("%Y-%m-%d"),
            "source": extract_source(url),
        })

    print(f"Filtered & formatted: {len(formatted)} jobs")
    output_path = os.path.join(os.path.dirname(__file__), "websearch-results.json")
    with open(output_path, "w") as f:
        json.dump(formatted, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")
    return formatted


if __name__ == "__main__":
    main()
