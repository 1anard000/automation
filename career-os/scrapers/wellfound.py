#!/usr/bin/env python3
"""
Wellfound (AngelList) job scraper.
Scrapes startup PM roles in Asia-Pacific.
Uses web search as Wellfound blocks direct scraping.
"""
import json, sys, os, re, time
from urllib.request import urlopen, Request
from urllib.parse import quote_plus
from datetime import datetime

SEARCH_QUERIES = [
    'site:wellfound.com "product manager" Singapore OR "Hong Kong"',
    'site:wellfound.com "senior product manager" Asia',
    'site:wellfound.com "director of product" Singapore',
    'site:wellfound.com "head of product" Singapore OR "Hong Kong"',
    'site:wellfound.com "product lead" Singapore',
]

TITLE_KEYWORDS = [
    "product manager", "program manager", "strategy",
    "head of product", "director", "vp product",
    "product lead", "principal", "senior",
    "cross-border", "e-commerce", "ecommerce", "growth",
]

def search_ddg(query, max_results=8):
    """Search DuckDuckGo HTML version."""
    try:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        })
        with urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        
        results = []
        # DuckDuckGo result pattern
        pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?'
            r'(?:<a[^>]+class="result__snippet"[^>]*>(.*?)</a>)?',
            re.DOTALL
        )
        
        for m in pattern.finditer(html):
            raw_url = m.group(1)
            title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            snippet = re.sub(r'<[^>]+>', '', m.group(3)).strip() if m.group(3) else ""
            
            # Clean DuckDuckGo redirect
            if "uddg=" in raw_url:
                url_match = re.search(r'uddg=([^&]+)', raw_url)
                if url_match:
                    from urllib.parse import unquote
                    raw_url = unquote(url_match.group(1))
            
            if title and raw_url.startswith("http"):
                results.append({"title": title, "url": raw_url, "snippet": snippet})
        
        return results[:max_results]
    except Exception as e:
        print(f"  [WARN] Search failed: {e}", file=sys.stderr)
        return []

def is_relevant(title, snippet):
    text = f"{title} {snippet}".lower()
    has_pm = any(kw in text for kw in TITLE_KEYWORDS)
    has_senior = any(kw in text for kw in ["senior", "director", "head", "vp", "principal", "lead", "manager"])
    return has_pm and has_senior

def extract_location(title, snippet):
    text = f"{title} {snippet}".lower()
    if "singapore" in text:
        return "Singapore"
    if "hong kong" in text or "hongkong" in text:
        return "Hong Kong"
    if "shenzhen" in text:
        return "Shenzhen"
    if "remote" in text:
        return "Remote"
    return ""

def classify_role_type(title):
    t = title.lower()
    if "strategy" in t:
        return "Strategy/Ops"
    if "program" in t:
        return "Program Management"
    return "Product Management"

def main():
    print("Wellfound scraper: searching for startup PM roles...")
    all_results = []
    
    for i, query in enumerate(SEARCH_QUERIES):
        print(f"  [{i+1}/{len(SEARCH_QUERIES)}] {query[:60]}...")
        results = search_ddg(query)
        all_results.extend(results)
        time.sleep(1.5)
    
    print(f"\nRaw results: {len(all_results)}")
    
    seen_urls = set()
    formatted = []
    for r in all_results:
        url = r["url"]
        title = r["title"]
        snippet = r.get("snippet", "")
        
        if url in seen_urls or not is_relevant(title, snippet):
            continue
        seen_urls.add(url)
        
        # Clean title
        clean_title = re.sub(r'\s*(?:at|@)\s+[^-|–]+$', '', title).strip()
        
        # Extract company from URL pattern: wellfound.com/company/name or wellfound.com/jobs/id
        company = ""
        company_match = re.search(r'wellfound\.com/company/([^/]+)', url)
        if company_match:
            company = company_match.group(1).replace("-", " ").title()
        
        formatted.append({
            "title": clean_title,
            "company": company,
            "location": extract_location(title, snippet),
            "grade": "A-1" if any(k in clean_title.lower() for k in ["director", "vp", "head"]) else "A-2",
            "url": url,
            "role_type": classify_role_type(clean_title),
            "salary": "",
            "scanned_date": datetime.now().strftime("%Y-%m-%d"),
            "source": "wellfound",
        })
    
    print(f"Filtered: {len(formatted)} jobs")
    
    output_path = os.path.join(os.path.dirname(__file__), "wellfound-results.json")
    with open(output_path, "w") as f:
        json.dump(formatted, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")
    return formatted

if __name__ == "__main__":
    main()
