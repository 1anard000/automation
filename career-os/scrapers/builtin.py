#!/usr/bin/env python3
"""
Built In job scraper.
Scrapes builtin.com for Senior PM roles in Hong Kong, Singapore, and Remote.
"""
import json, sys, os, re
from urllib.request import urlopen, Request
from urllib.error import URLError
from datetime import datetime
from html.parser import HTMLParser

SEARCH_URLS = [
    "https://builtin.com/jobs/senior-product-manager/hong-kong",
    "https://builtin.com/jobs/senior-product-manager/singapore",
    "https://builtin.com/jobs/product-manager/hong-kong",
    "https://builtin.com/jobs/product-manager/singapore",
    "https://builtin.com/jobs/director-product/hong-kong",
    "https://builtin.com/jobs/director-product/singapore",
    "https://builtin.com/jobs/head-product/singapore",
    "https://builtin.com/jobs/head-product/hong-kong",
]

TITLE_KEYWORDS = [
    "product manager", "program manager", "strategy",
    "head of product", "director", "vp product",
    "product lead", "principal", "senior", "staff",
    "cross-border", "e-commerce", "ecommerce", "growth",
]

def fetch_page(url, timeout=15):
    """Fetch HTML page."""
    try:
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (URLError, OSError) as e:
        print(f"  [WARN] Failed to fetch {url}: {e}", file=sys.stderr)
        return ""

def parse_builtin_jobs(html, location_hint):
    """Parse Built In HTML to extract job listings."""
    jobs = []
    
    # Extract job cards using regex patterns from the HTML
    # Built In uses data attributes and structured HTML
    # Pattern: job title links with company names
    
    # Find job card sections
    job_pattern = re.compile(
        r'href="(/job/[^"]+)"[^>]*>.*?<(?:h2|span|div)[^>]*class="[^"]*job[^"]*"[^>]*>(.*?)</(?:h2|span|div)>',
        re.DOTALL | re.IGNORECASE
    )
    
    # Simpler pattern: find /job/ links
    link_pattern = re.compile(r'href="(/job/[^"]+/(\d+))"')
    title_pattern = re.compile(r'<(?:h2|h3|a)[^>]*>([^<]*(?:product|manager|director|head|strategy|program)[^<]*)</(?:h2|h3|a)>', re.IGNORECASE)
    company_pattern = re.compile(r'class="[^"]*company[^"]*"[^>]*>([^<]+)<', re.IGNORECASE)
    
    # Try JSON-LD structured data first
    jsonld_pattern = re.compile(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.DOTALL)
    for match in jsonld_pattern.finditer(html):
        try:
            ld = json.loads(match.group(1))
            if isinstance(ld, dict) and ld.get("@type") == "JobPosting":
                jobs.append({
                    "title": ld.get("title", ""),
                    "company": ld.get("hiringOrganization", {}).get("name", ""),
                    "location": ld.get("jobLocation", {}).get("address", {}).get("addressLocality", location_hint),
                    "url": ld.get("url", ""),
                    "salary": ld.get("baseSalary", {}).get("value", {}).get("value", "") if isinstance(ld.get("baseSalary"), dict) else "",
                })
            elif isinstance(ld, list):
                for item in ld:
                    if isinstance(item, dict) and item.get("@type") == "JobPosting":
                        jobs.append({
                            "title": item.get("title", ""),
                            "company": item.get("hiringOrganization", {}).get("name", ""),
                            "location": item.get("jobLocation", {}).get("address", {}).get("addressLocality", location_hint),
                            "url": item.get("url", ""),
                            "salary": "",
                        })
        except (json.JSONDecodeError, AttributeError):
            pass
    
    # Fallback: extract from job links
    if not jobs:
        seen_urls = set()
        for match in link_pattern.finditer(html):
            path = match.group(1)
            job_id = match.group(2)
            if path in seen_urls:
                continue
            seen_urls.add(path)
            
            # Try to find title near the link
            start = max(0, match.start() - 500)
            end = min(len(html), match.end() + 500)
            context = html[start:end]
            
            # Clean title from context
            title_match = re.search(r'>([^<]{10,80})<', context)
            title = title_match.group(1).strip() if title_match else ""
            
            # Skip navigation/footer links
            if not title or len(title) < 5:
                continue
                
            # Check if it looks like a job title
            title_lower = title.lower()
            if not any(kw in title_lower for kw in TITLE_KEYWORDS):
                continue
            
            jobs.append({
                "title": title,
                "company": "",
                "location": location_hint,
                "url": f"https://builtin.com{path}",
                "salary": "",
            })
    
    return jobs

def classify_role_type(title):
    t = title.lower()
    if "strategy" in t or "strategic" in t:
        return "Strategy/Ops"
    if "program" in t:
        return "Program Management"
    if "product" in t:
        return "Product Management"
    return "Product Management"

def main():
    print("Built In scraper: scanning for PM roles...")
    all_jobs = []
    
    for url in SEARCH_URLS:
        loc_hint = "Hong Kong" if "hong-kong" in url else "Singapore"
        print(f"  Fetching {url.split('.com')[1]}...")
        html = fetch_page(url)
        if not html:
            continue
        jobs = parse_builtin_jobs(html, loc_hint)
        all_jobs.extend(jobs)
        print(f"    Found {len(jobs)} jobs")
    
    # Deduplicate by URL
    seen = set()
    unique_jobs = []
    for j in all_jobs:
        key = j.get("url", "")
        if key and key not in seen:
            seen.add(key)
            unique_jobs.append(j)
    
    # Format output
    formatted = []
    for j in unique_jobs:
        title = j.get("title", "").strip()
        if not title:
            continue
        formatted.append({
            "title": title,
            "company": j.get("company", ""),
            "location": j.get("location", ""),
            "grade": "A-1" if any(k in title.lower() for k in ["director", "vp", "head"]) else "A-2",
            "url": j.get("url", ""),
            "role_type": classify_role_type(title),
            "salary": j.get("salary", ""),
            "scanned_date": datetime.now().strftime("%Y-%m-%d"),
            "source": "builtin",
        })
    
    print(f"\nBuilt In total: {len(formatted)} jobs")
    output_path = os.path.join(os.path.dirname(__file__), "builtin-results.json")
    with open(output_path, "w") as f:
        json.dump(formatted, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")
    return formatted

if __name__ == "__main__":
    main()
