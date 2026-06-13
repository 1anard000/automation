#!/usr/bin/env python3
"""
Company career page scraper.
Scrapes career APIs/pages for ByteDance, Shopee, Sea Group, Grab, Alibaba, etc.
"""
import json, sys, os, re
from urllib.request import urlopen, Request
from urllib.error import URLError
from datetime import datetime

# Company career API endpoints and scraping strategies
COMPANY_CONFIGS = [
    {
        "name": "ByteDance",
        "type": "api",
        "url": "https://jobs.bytedance.com/api/v1/search/position?keyword=product+manager&location=City_深圳,City_新加坡,City_香港&limit=50",
        "alt_urls": [
            "https://jobs.bytedance.com/experienced/position?keywords=product%20manager&category=&location=CT_11,CT_72,CT_83&project=&type=&job_hot_flag=&current=1&limit=20",
        ]
    },
    {
        "name": "Shopee",
        "type": "api",
        "url": "https://careers.shopee.com/api/v1/job/search?query=product+manager&location=singapore&limit=50",
        "alt_urls": [
            "https://careers.shopee.sg/api/job/list?keyword=product+manager&page_size=50",
        ]
    },
    {
        "name": "Grab",
        "type": "greenhouse",
        "board": "grab",
    },
    {
        "name": "Alibaba International",
        "type": "web",
        "url": "https://talent.alibaba.com/off-campus/position-list?lang=en&search=product+manager&location=hongkong,singapore,shenzhen",
    },
    {
        "name": "Tencent International",
        "type": "web",
        "url": "https://careers.tencent.com/search.html?keyword=product+manager&locationId=",
    },
    {
        "name": "Sea Group",
        "type": "greenhouse",
        "board": "sea",
    },
    {
        "name": "GoTo",
        "type": "greenhouse",
        "board": "goto",
    },
    {
        "name": "Airwallex",
        "type": "greenhouse",
        "board": "airwallex",
    },
    {
        "name": "Razer",
        "type": "greenhouse",
        "board": "razer",
    },
    {
        "name": "PropertyGuru",
        "type": "greenhouse",
        "board": "propertyguru",
    },
    {
        "name": "Carousell",
        "type": "greenhouse",
        "board": "carousell",
    },
]

TITLE_KEYWORDS = [
    "product manager", "program manager", "strategy",
    "head of product", "director of product", "vp product",
    "product lead", "principal product", "senior product",
    "cross-border", "e-commerce", "ecommerce", "growth",
    "business development", "partnerships",
]

LOCATIONS = ["hong kong", "singapore", "shenzhen", "guangzhou", "remote"]

def fetch_json(url, timeout=15):
    try:
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json",
        })
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (URLError, json.JSONDecodeError, OSError) as e:
        print(f"  [WARN] Failed to fetch {url}: {e}", file=sys.stderr)
        return None

def fetch_html(url, timeout=15):
    try:
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        })
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (URLError, OSError) as e:
        print(f"  [WARN] Failed to fetch {url}: {e}", file=sys.stderr)
        return ""

def location_matches(loc):
    if not loc:
        return False
    loc = loc.lower()
    return any(kw in loc for kw in LOCATIONS)

def title_matches(title):
    if not title:
        return False
    t = title.lower()
    return any(kw in t for kw in TITLE_KEYWORDS)

def classify_role_type(title):
    t = title.lower()
    if "strategy" in t or "strategic" in t:
        return "Strategy/Ops"
    if "program" in t:
        return "Program Management"
    if "product" in t:
        return "Product Management"
    return "Product Management"

def scrape_greenhouse(company_name, board_slug):
    """Scrape from Greenhouse API."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_slug}/jobs"
    data = fetch_json(url)
    if not data or "jobs" not in data:
        return []
    
    jobs = []
    for job in data["jobs"]:
        loc = job.get("location", {}).get("name", "")
        title = job.get("title", "")
        if not location_matches(loc):
            continue
        if not title_matches(title):
            continue
        jobs.append({
            "title": title,
            "company": company_name,
            "location": loc,
            "grade": "A-1" if any(k in title.lower() for k in ["director", "vp", "head", "principal"]) else "A-2",
            "url": job.get("absolute_url", ""),
            "role_type": classify_role_type(title),
            "salary": "",
            "scanned_date": datetime.now().strftime("%Y-%m-%d"),
            "source": "company_site",
        })
    return jobs

def scrape_bytedance(config):
    """Scrape ByteDance careers."""
    jobs = []
    for url in [config["url"]] + config.get("alt_urls", []):
        data = fetch_json(url)
        if not data:
            continue
        
        # ByteDance API returns different formats
        positions = data.get("data", {}).get("position_list", []) if isinstance(data.get("data"), dict) else []
        if not positions and isinstance(data, list):
            positions = data
        
        for pos in positions:
            title = pos.get("name", "") or pos.get("title", "")
            loc = pos.get("location", "") or pos.get("city", "")
            if isinstance(loc, list):
                loc = ", ".join(loc)
            if not title_matches(title):
                continue
            if not location_matches(loc):
                continue
            jobs.append({
                "title": title,
                "company": "ByteDance",
                "location": loc,
                "grade": "A-1" if any(k in title.lower() for k in ["director", "vp", "head"]) else "A-2",
                "url": pos.get("url", "") or pos.get("link", config["url"]),
                "role_type": classify_role_type(title),
                "salary": "",
                "scanned_date": datetime.now().strftime("%Y-%m-%d"),
                "source": "company_site",
            })
    return jobs

def scrape_web_page(config):
    """Generic web page scraper using regex."""
    url = config.get("url", "")
    if not url:
        return []
    
    html = fetch_html(url)
    if not html:
        return []
    
    jobs = []
    # Try JSON-LD
    jsonld_pattern = re.compile(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.DOTALL)
    for match in jsonld_pattern.finditer(html):
        try:
            ld = json.loads(match.group(1))
            items = ld if isinstance(ld, list) else [ld]
            for item in items:
                if isinstance(item, dict) and item.get("@type") == "JobPosting":
                    title = item.get("title", "")
                    loc = item.get("jobLocation", {}).get("address", {}).get("addressLocality", "") if isinstance(item.get("jobLocation"), dict) else ""
                    if title_matches(title) and location_matches(loc):
                        jobs.append({
                            "title": title,
                            "company": config["name"],
                            "location": loc,
                            "grade": "A-2",
                            "url": item.get("url", url),
                            "role_type": classify_role_type(title),
                            "salary": "",
                            "scanned_date": datetime.now().strftime("%Y-%m-%d"),
                            "source": "company_site",
                        })
        except (json.JSONDecodeError, AttributeError):
            pass
    
    # Fallback: regex for job links
    if not jobs:
        link_patterns = [
            re.compile(r'href="([^"]*(?:job|position|opening)[^"]*)"[^>]*>([^<]{10,100})<', re.IGNORECASE),
            re.compile(r'>([^<]*(?:product|program|manager|director)[^<]{5,80})<', re.IGNORECASE),
        ]
        for pattern in link_patterns:
            for m in pattern.finditer(html[:50000]):
                if len(m.groups()) >= 2:
                    href, title = m.group(1), m.group(2)
                    if title_matches(title):
                        jobs.append({
                            "title": title.strip(),
                            "company": config["name"],
                            "location": "",
                            "grade": "A-2",
                            "url": href if href.startswith("http") else url,
                            "role_type": classify_role_type(title),
                            "salary": "",
                            "scanned_date": datetime.now().strftime("%Y-%m-%d"),
                            "source": "company_site",
                        })
    
    return jobs

def main():
    print(f"Company careers scraper: scanning {len(COMPANY_CONFIGS)} companies...")
    all_jobs = []
    
    for config in COMPANY_CONFIGS:
        name = config["name"]
        scrape_type = config.get("type", "web")
        print(f"  Scanning {name} ({scrape_type})...")
        
        try:
            if scrape_type == "greenhouse":
                jobs = scrape_greenhouse(name, config["board"])
            elif name == "ByteDance":
                jobs = scrape_bytedance(config)
            else:
                jobs = scrape_web_page(config)
            
            all_jobs.extend(jobs)
            print(f"    Found {len(jobs)} matching jobs")
        except Exception as e:
            print(f"    [ERROR] {e}", file=sys.stderr)
    
    print(f"\nCompany careers total: {len(all_jobs)} jobs")
    output_path = os.path.join(os.path.dirname(__file__), "company-results.json")
    with open(output_path, "w") as f:
        json.dump(all_jobs, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")
    return all_jobs

if __name__ == "__main__":
    main()
