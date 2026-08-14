#!/usr/bin/env python3
"""Scan Greenhouse job boards for new positions."""
import json
import urllib.request
import sys

COMPANIES = {
    "okx": "https://boards-api.greenhouse.io/v1/boards/okx/jobs",
    "stripe": "https://boards-api.greenhouse.io/v1/boards/stripe/jobs",
    "airwallex": "https://boards-api.greenhouse.io/v1/boards/airwallex/jobs",
    "coupang": "https://boards-api.greenhouse.io/v1/boards/coupang/jobs",
    "bybit": "https://boards-api.greenhouse.io/v1/boards/bybit/jobs",
}

KEYWORDS_PM = [
    "product manager", "product management", "senior product",
    "principal product", "growth product", "strategy", "operations",
    "business development", "bizops", "business strategy",
    "growth", "lead", "head of", "gm", "general manager",
    "program manager", "project manager", "data product",
]

SKIP_KEYWORDS = ["intern", "internship", "director", "vp ", "vice president", "managing director", "chief", "c-level"]

# Locations of interest
LOCATION_KEYWORDS = [
    "singapore", "hong kong", "shenzhen", "guangzhou", "shanghai",
    "taipei", "malaysia", "kuala lumpur", "apac", "asia",
]

def fetch_jobs(company, base_url):
    """Fetch all jobs from a Greenhouse board."""
    jobs = []
    page = 0
    while True:
        url = f"{base_url}?page={page}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            print(f"  Error fetching {company} page {page}: {e}", file=sys.stderr)
            break
        
        batch = data.get("jobs", [])
        if not batch:
            break
        jobs.extend(batch)
        page += 1
        if len(batch) < 50:  # Greenhouse default page size
            break
    
    return jobs

def is_relevant(job):
    """Check if job matches our target profile."""
    title = job.get("title", "").lower()
    location = job.get("location", {}).get("name", "").lower()
    
    # Skip interns and director/VP
    for skip in SKIP_KEYWORDS:
        if skip in title:
            return False
    
    # Must match at least one keyword
    matches_keyword = any(kw in title for kw in KEYWORDS_PM)
    if not matches_keyword:
        return False
    
    # Must be in a relevant location
    matches_location = any(loc in location for loc in LOCATION_KEYWORDS)
    if not matches_location:
        return False
    
    return True

def main():
    # Load existing jobs
    try:
        with open("/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json") as f:
            existing = json.load(f)
    except:
        existing = []
    
    existing_urls = {j.get("url", "") for j in existing}
    existing_ids = set()
    for j in existing:
        gid = j.get("greenhouse_id")
        if gid:
            existing_ids.add(gid)
    
    new_jobs = []
    
    for company, base_url in COMPANIES.items():
        print(f"Scanning {company}...", file=sys.stderr)
        jobs = fetch_jobs(company, base_url)
        print(f"  Found {len(jobs)} total jobs", file=sys.stderr)
        
        relevant = [j for j in jobs if is_relevant(j)]
        print(f"  Relevant: {len(relevant)}", file=sys.stderr)
        
        for job in relevant:
            gid = job.get("id")
            if gid in existing_ids:
                continue
            
            location = job.get("location", {}).get("name", "Remote")
            url = f"https://boards.greenhouse.io/{company}/jobs/{gid}"
            
            if url in existing_urls:
                continue
            
            entry = {
                "company": company.title() if company != "okx" else "OKX",
                "title": job.get("title", ""),
                "location": location,
                "url": url,
                "greenhouse_id": gid,
                "posted": job.get("updated_at", "")[:10] if job.get("updated_at") else "",
                "source": "greenhouse_api",
                "scanned_date": "2026-08-14",
                "date_source": "from_scanned_date",
                "english_friendly": True,
                "category": "product",
                "grade": "A-1",
                "description": job.get("content", "")[:500] if job.get("content") else "",
            }
            new_jobs.append(entry)
    
    print(f"\nNew jobs found: {len(new_jobs)}", file=sys.stderr)
    
    # Output as JSON to stdout
    print(json.dumps(new_jobs, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
