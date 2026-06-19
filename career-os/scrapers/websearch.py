#!/usr/bin/env python3
"""
Web search-based job scraper.
Uses DuckDuckGo search to find PM, Strategy, BizOps, Chief of Staff,
Growth, and GM roles from Indeed, Glassdoor, JobsDB, and general web.
Balanced across role types per Ian's profile: strategy/ops/biz ops core,
with PM as one of several directions.
"""
import json, sys, os, re, subprocess, time
from datetime import datetime

# Search queries to run
QUERIES = [
    # === PRODUCT MANAGEMENT (8 queries — 22%) ===
    'site:indeed.com "senior product manager" Singapore OR "Hong Kong" 2026',
    'site:jobsdb.com "product manager" "Hong Kong" OR Singapore',
    'site:careers.bytedance.com "product manager" Singapore OR Shenzhen',
    'site:careers.shopee.com "product manager" Singapore OR Shenzhen',
    'site:glassdoor.com "product director" Singapore OR Shenzhen',
    'site:builtin.com "director of product" Singapore',
    'site:linkedin.com/jobs "senior product manager" "Hong Kong" cross-border',
    'site:grab.careers "product manager" Singapore',
    # === STRATEGY / BIZ OPS (10 queries — 28%) ===
    'site:indeed.com "business operations" OR "bizops" Singapore OR "Hong Kong"',
    'site:indeed.com "strategy manager" OR "head of strategy" Singapore OR Shenzhen',
    'site:jobsdb.com "business strategy" OR "corporate strategy" "Hong Kong" OR Singapore',
    'site:linkedin.com/jobs "business operations" manager Singapore OR "Hong Kong"',
    'site:linkedin.com/jobs "chief of staff" Singapore OR Shenzhen OR "Hong Kong"',
    'site:glassdoor.com "strategy operations" OR "strategic operations" Singapore',
    'site:glassdoor.com "business operations" director "Hong Kong"',
    'site:wellfound.com "bizops" OR "business operations" lead Singapore',
    'site:builtin.com "business operations" Singapore',
    'site:efinancialcareers.com "business strategy" OR "bizops" Singapore OR "Hong Kong"',
    # === GROWTH / EXPANSION / GM (10 queries — 28%) ===
    'site:indeed.com "head of growth" OR "growth manager" Singapore OR Shenzhen',
    'site:indeed.com "general manager" OR "country manager" Singapore OR "Hong Kong"',
    'site:jobsdb.com "general manager" "Hong Kong" OR Singapore fintech OR ecommerce',
    'site:linkedin.com/jobs "regional manager" OR "expansion lead" APAC Singapore',
    'site:linkedin.com/jobs "head of growth" "Hong Kong" OR Shenzhen',
    'site:glassdoor.com "general manager" ecommerce Singapore',
    'site:glassdoor.com "market expansion" OR "business expansion" APAC',
    'site:grab.careers "general manager" OR "growth" Singapore',
    'site:builtin.com "general manager" OR "country manager" Singapore',
    'site:wellfound.com "head of growth" OR "growth lead" Singapore OR Hong Kong',
    # === PROGRAM / PROJECT MANAGEMENT (4 queries — 11%) ===
    'site:indeed.com "program manager" senior Singapore OR "Hong Kong"',
    'site:glassdoor.com "program manager" fintech Singapore',
    'site:linkedin.com/jobs "senior program manager" "Hong Kong" OR Shenzhen',
    'site:jobsdb.com "program manager" "Hong Kong" OR Singapore',
    # === CROSS-BORDER / MARKETPLACE / PLATFORM (4 queries — 11%) ===
    'site:indeed.com "cross-border" OR "marketplace" operations manager Singapore OR Shenzhen',
    'site:linkedin.com/jobs "marketplace operations" OR "platform operations" APAC',
    'site:jobsdb.com "cross-border" OR "ecommerce" operations "Hong Kong"',
    'site:glassdoor.com "marketplace" OR "platform" director Singapore OR Shenzhen',
]

# Keywords to filter relevant results
TITLE_KEYWORDS = [
    # PM
    "product manager", "product director", "head of product", "vp product",
    "product lead", "principal product", "senior product",
    # Strategy / BizOps
    "business operations", "bizops", "strategy", "strategic",
    "chief of staff", "corporate strategy", "business strategy",
    # Growth / GM / Expansion
    "head of growth", "growth manager", "growth lead",
    "general manager", "country manager", "regional manager",
    "market expansion", "business expansion", "expansion lead",
    # Program / Project
    "program manager", "project manager",
    # Cross-border / Marketplace / Platform
    "cross-border", "e-commerce", "ecommerce", "marketplace",
    "platform operations", "marketplace operations",
]

def run_ddg_search(query, max_results=10):
    """Run a search using DuckDuckGo via CLI or API."""
    try:
        import urllib.request
        import urllib.parse
        
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        })
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        
        # Parse results
        results = []
        # DuckDuckGo HTML results pattern
        result_pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?'
            r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
            re.DOTALL
        )
        
        for match in result_pattern.finditer(html):
            url = match.group(1)
            title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            snippet = re.sub(r'<[^>]+>', '', match.group(3)).strip()
            
            # Clean up DuckDuckGo redirect URLs
            if "uddg=" in url:
                url_match = re.search(r'uddg=([^&]+)', url)
                if url_match:
                    import urllib.parse
                    url = urllib.parse.unquote(url_match.group(1))
            
            if title and url.startswith("http"):
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                })
        
        return results[:max_results]
    except Exception as e:
        print(f"  [WARN] Search failed for '{query[:50]}...': {e}", file=sys.stderr)
        return []

def extract_source(url):
    """Determine source from URL."""
    url_lower = url.lower()
    if "indeed.com" in url_lower:
        return "indeed"
    if "glassdoor.com" in url_lower:
        return "glassdoor"
    if "jobsdb.com" in url_lower:
        return "jobsdb"
    if "linkedin.com" in url_lower:
        return "linkedin_search"
    if "efinancialcareers.com" in url_lower:
        return "efinancialcareers"
    if "builtin.com" in url_lower:
        return "builtin"
    if "greenhouse.io" in url_lower:
        return "greenhouse"
    if "bytedance" in url_lower or "tiktok" in url_lower:
        return "bytedance"
    if "shopee" in url_lower:
        return "shopee"
    if "grab" in url_lower:
        return "grab"
    return "web_search"

def extract_company(title, url, snippet):
    """Try to extract company name from title or URL."""
    # Pattern: "at Company" or "- Company" in title
    at_match = re.search(r'\s+(?:at|@)\s+([^-|–]+?)(?:\s*[-|–]|\s*$)', title, re.IGNORECASE)
    if at_match:
        return at_match.group(1).strip()
    
    dash_match = re.search(r'[-|–]\s*([^-|–]+?)$', title)
    if dash_match:
        candidate = dash_match.group(1).strip()
        if len(candidate) < 50 and not any(kw in candidate.lower() for kw in ["singapore", "hong kong", "remote"]):
            return candidate
    
    # From URL
    if "indeed.com" in url:
        return ""
    if "glassdoor.com" in url:
        return ""
    
    return ""

def extract_location(title, snippet):
    """Extract location from title or snippet."""
    text = f"{title} {snippet}"
    locations = {
        "Singapore": ["singapore"],
        "Hong Kong": ["hong kong", "hongkong"],
        "Shenzhen": ["shenzhen"],
        "Guangzhou": ["guangzhou"],
        "Remote": ["remote"],
    }
    for loc, keywords in locations.items():
        if any(kw in text.lower() for kw in keywords):
            return loc
    return ""

def is_relevant(title, snippet):
    """Check if job result is relevant to [CANDIDATE]'s profile."""
    text = f"{title} {snippet}".lower()
    has_title = any(kw in text for kw in TITLE_KEYWORDS)
    has_senior = any(kw in text for kw in ["senior", "director", "head", "vp", "principal", "lead", "manager"])
    return has_title and has_senior

def classify_role_type(title):
    t = title.lower()
    # Strategy / BizOps
    if "chief of staff" in t:
        return "Chief of Staff"
    if "business operations" in t or "bizops" in t:
        return "Business Operations"
    if "strategy" in t or "strategic" in t:
        return "Strategy/Ops"
    # Growth / GM / Expansion
    if "general manager" in t or "country manager" in t or "regional manager" in t:
        return "General Manager"
    if "growth" in t or "expansion" in t:
        return "Growth/Expansion"
    # PM
    if "product" in t:
        return "Product Management"
    # Program / Project
    if "program" in t or "project" in t:
        return "Program Management"
    # Cross-border / Marketplace / Platform
    if "cross-border" in t or "marketplace" in t or "platform" in t:
        return "Cross-border/Platform"
    return "Other"

def main():
    print(f"Web search scraper: running {len(QUERIES)} queries...")
    all_results = []
    
    for i, query in enumerate(QUERIES):
        print(f"  [{i+1}/{len(QUERIES)}] {query[:60]}...")
        results = run_ddg_search(query, max_results=8)
        all_results.extend(results)
        time.sleep(1.5)  # Rate limiting
    
    print(f"\nRaw results: {len(all_results)}")
    
    # Filter and format
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
        company = extract_company(title, url, snippet)
        source = extract_source(url)
        
        # Clean title
        clean_title = re.sub(r'\s*(?:at|@)\s+[^-|–]+$', '', title).strip()
        clean_title = re.sub(r'\s*[-|–]\s*[^-|–]+$', '', clean_title).strip()
        
        formatted.append({
            "title": clean_title,
            "company": company,
            "location": location,
            "grade": "A-1" if any(k in clean_title.lower() for k in ["director", "vp", "head"]) else "A-2",
            "url": url,
            "role_type": classify_role_type(clean_title),
            "salary": "",
            "scanned_date": datetime.now().strftime("%Y-%m-%d"),
            "source": source,
        })
    
    print(f"Filtered & formatted: {len(formatted)} jobs")
    
    output_path = os.path.join(os.path.dirname(__file__), "websearch-results.json")
    with open(output_path, "w") as f:
        json.dump(formatted, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")
    return formatted

if __name__ == "__main__":
    main()
