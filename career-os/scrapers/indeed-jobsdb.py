#!/usr/bin/env python3
"""
Indeed & JobsDB job scraper via DuckDuckGo site: queries.
Targets PM/program/strategy roles in APAC cities.
"""
import json, sys, os, re, time, urllib.request, urllib.parse
from datetime import datetime

QUERIES = [
    # Indeed - Singapore
    'site:indeed.com "senior product manager" Singapore',
    'site:indeed.com "product director" Singapore',
    'site:indeed.com "head of product" Singapore',
    'site:indeed.com "program manager" Singapore fintech',
    # Indeed - Hong Kong
    'site:indeed.com "senior product manager" "Hong Kong"',
    'site:indeed.com "product director" "Hong Kong"',
    'site:indeed.com "head of strategy" "Hong Kong"',
    # Indeed - China cities
    'site:indeed.com "product manager" Shenzhen cross-border',
    'site:indeed.com "product manager" Guangzhou',
    'site:indeed.com "product manager" Shanghai ecommerce',
    'site:indeed.com "program manager" Shenzhen OR Guangzhou',
    # JobsDB - Hong Kong
    'site:jobsdb.com "senior product manager" "Hong Kong"',
    'site:jobsdb.com "product director" "Hong Kong"',
    'site:jobsdb.com "head of product" "Hong Kong"',
    'site:jobsdb.com "program manager" "Hong Kong" fintech',
    # JobsDB - Singapore
    'site:jobsdb.com "senior product manager" Singapore',
    'site:jobsdb.com "product director" Singapore',
    'site:jobsdb.com "head of product" Singapore ecommerce',
    # JobsDB - broader
    'site:jobsdb.com "product manager" Shenzhen OR Guangzhou cross-border',
    'site:jobsdb.com "strategy director" Singapore OR "Hong Kong"',
]

TITLE_KEYWORDS = [
    "product manager", "program manager", "strategy",
    "head of product", "director of product", "vp product",
    "product lead", "principal product", "senior product",
    "cross-border", "e-commerce", "ecommerce", "growth",
]

SENIORITY_KEYWORDS = [
    "senior", "sr.", "director", "head", "vp", "vice president",
    "lead", "principal", "staff", "manager", "chief",
]

def run_ddg_search(query, max_results=10):
    """Run a DuckDuckGo HTML search and parse results."""
    try:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        results = []
        pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?'
            r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
            re.DOTALL,
        )
        for m in pattern.finditer(html):
            rurl = m.group(1)
            title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            snippet = re.sub(r'<[^>]+>', '', m.group(3)).strip()
            if "uddg=" in rurl:
                um = re.search(r'uddg=([^&]+)', rurl)
                if um:
                    rurl = urllib.parse.unquote(um.group(1))
            if title and rurl.startswith("http"):
                results.append({"title": title, "url": rurl, "snippet": snippet})
        return results[:max_results]
    except Exception as e:
        print(f"  [WARN] Search failed: {e}", file=sys.stderr)
        return []

def extract_source(url):
    u = url.lower()
    if "indeed.com" in u:
        return "indeed"
    if "jobsdb.com" in u:
        return "jobsdb"
    return "web_search"

def extract_company(title, url):
    at_match = re.search(r'\s+(?:at|@)\s+([^-|–]+?)(?:\s*[-|–]|\s*$)', title, re.IGNORECASE)
    if at_match:
        return at_match.group(1).strip()
    dash_match = re.search(r'[-|–]\s*([^-|–]+?)$', title)
    if dash_match:
        c = dash_match.group(1).strip()
        if len(c) < 50 and not any(kw in c.lower() for kw in ["singapore", "hong kong", "remote", "shenzhen", "guangzhou", "shanghai"]):
            return c
    return ""

def extract_location(title, snippet):
    text = f"{title} {snippet}".lower()
    locations = {
        "Singapore": ["singapore"],
        "Hong Kong": ["hong kong", "hongkong"],
        "Shenzhen": ["shenzhen"],
        "Guangzhou": ["guangzhou"],
        "Shanghai": ["shanghai"],
        "Remote": ["remote"],
    }
    for loc, kws in locations.items():
        if any(kw in text for kw in kws):
            return loc
    return ""

def is_relevant(title, snippet):
    text = f"{title} {snippet}".lower()
    has_role = any(kw in text for kw in TITLE_KEYWORDS)
    has_seniority = any(kw in text for kw in SENIORITY_KEYWORDS)
    return has_role and has_seniority

def classify_role_type(title):
    t = title.lower()
    if "strategy" in t or "strategic" in t:
        return "Strategy/Ops"
    if "program" in t:
        return "Program Management"
    if "product" in t:
        return "Product Management"
    if "growth" in t:
        return "Growth"
    return "Product Management"

def classify_grade(title):
    t = title.lower()
    if any(k in t for k in ["vp", "vice president", "c-level", "chief"]):
        return "S-1"
    if any(k in t for k in ["director", "head of"]):
        return "A-1"
    if any(k in t for k in ["principal", "staff"]):
        return "A-1"
    if "senior" in t or "sr." in t:
        return "A-2"
    return "A-2"

def main():
    print(f"Indeed/JobsDB scraper: running {len(QUERIES)} queries...")
    all_results = []
    for i, query in enumerate(QUERIES):
        print(f"  [{i+1}/{len(QUERIES)}] {query[:60]}...")
        results = run_ddg_search(query, max_results=8)
        all_results.extend(results)
        time.sleep(1.5)

    print(f"\nRaw results: {len(all_results)}")

    seen_urls = set()
    formatted = []
    for r in all_results:
        url = r.get("url", "")
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        if not url or not title:
            continue
        if url in seen_urls:
            continue
        if not is_relevant(title, snippet):
            continue
        seen_urls.add(url)
        location = extract_location(title, snippet)
        company = extract_company(title, url)
        source = extract_source(url)
        clean_title = re.sub(r'\s*(?:at|@)\s+[^-|–]+$', '', title).strip()
        clean_title = re.sub(r'\s*[-|–]\s*[^-|–]+$', '', clean_title).strip()
        formatted.append({
            "title": clean_title,
            "company": company,
            "location": location,
            "grade": classify_grade(clean_title),
            "url": url,
            "role_type": classify_role_type(clean_title),
            "salary": "",
            "scanned_date": datetime.now().strftime("%Y-%m-%d"),
            "source": source,
        })

    print(f"Filtered & formatted: {len(formatted)} jobs")

    output_path = os.path.join(os.path.dirname(__file__), "indeed-jobsdb-results.json")
    with open(output_path, "w") as f:
        json.dump(formatted, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")
    return formatted

if __name__ == "__main__":
    main()
