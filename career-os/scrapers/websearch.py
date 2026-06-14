#!/usr/bin/env python3
"""
Web search-based job scraper.
Uses DuckDuckGo search to find PM jobs from Indeed, Glassdoor, JobsDB, and general web.
This is a meta-scraper that parses search results for job listings.
"""
import json, sys, os, re, subprocess, time
from datetime import datetime

# Search queries to run
QUERIES = [
    # Indeed / global aggregators
    'site:indeed.com "senior product manager" Singapore OR "Hong Kong" 2026',
    'site:indeed.com "product director" Singapore OR "Hong Kong"',
    'site:indeed.com "head of product" Singapore OR Shenzhen',
    'site:glassdoor.com "senior product manager" Singapore OR "Hong Kong"',
    'site:glassdoor.com "product director" Singapore',
    'site:glassdoor.com "program manager" Singapore fintech',
    'site:jobsdb.com "senior product manager" "Hong Kong" OR Singapore',
    'site:jobsdb.com "product manager" "Hong Kong" fintech OR ecommerce',
    'site:jobsdb.com "product director" Singapore',
    'site:wellfound.com "senior product manager" ecommerce',
    'site:builtin.com "product manager" Singapore',
    'site:builtin.com "director of product" Singapore',
    'site:careers.bytedance.com "product manager" Singapore OR Shenzhen',
    'site:careers.bytedance.com "product director" ecommerce',
    'site:careers.shopee.com "product manager" Singapore OR Shenzhen',
    'site:careers.shopee.com "product director" ecommerce',
    'site:grab.careers "product manager" Singapore',
    'site:grab.careers "program manager" Singapore',
    # Strategic channels for Monday leads (not viral apps)
    'site:terraform.io/careers "senior product" ecommerce',
    'site:shopify.com/careers "product manager" singapore OR remote',
    'site:stripe.com/jobs "product" singapore',
    'site:airwallex.com/careers "product director" singapore',
    'site:coinbase.com/careers "senior product" singapore',
    'site:nium.com/careers "product manager" singapore',
    'site:xendit.com/careers "product" singapore',
    'site:career001.com "product manager" singapore',
    'site:recruit.com.hk "product manager" hong kong',
    # Executive / board-led roles
    'site:refind.com "product director" singapore',
    'site:efinancialcareers.com "product manager" Singapore OR "Hong Kong"',
    # LinkedIn (supplement existing)
    'site:linkedin.com/jobs "senior product manager" "Hong Kong" cross-border',
    'site:linkedin.com/jobs "product director" Singapore ecommerce',
    'site:linkedin.com/jobs "head of product" singapore',
]

# Keywords to filter relevant results
TITLE_KEYWORDS = [
    "product manager", "program manager", "strategy",
    "head of product", "director of product", "vp product",
    "product lead", "principal product", "senior product",
    "cross-border", "e-commerce", "ecommerce", "growth",
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
    """Check if job result is relevant to Ian's profile."""
    text = f"{title} {snippet}".lower()
    has_title = any(kw in text for kw in TITLE_KEYWORDS)
    has_senior = any(kw in text for kw in ["senior", "director", "head", "vp", "principal", "lead", "manager"])
    return has_title and has_senior

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
