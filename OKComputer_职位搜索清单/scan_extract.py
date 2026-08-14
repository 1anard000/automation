#!/usr/bin/env python3
"""
Extract the best new jobs from Greenhouse scan, filtered for target profile.
Outputs JSON array of new jobs to merge.
"""
import json
import urllib.request
import sys

COMPANIES = {
    "okx": "https://boards-api.greenhouse.io/v1/boards/okx/jobs",
    "stripe": "https://boards-api.greenhouse.io/v1/boards/stripe/jobs",
    "coupang": "https://boards-api.greenhouse.io/v1/boards/coupang/jobs",
    "bybit": "https://boards-api.greenhouse.io/v1/boards/bybit/jobs",
}

# Strong match keywords for target profile
STRONG_KEYWORDS = [
    "product manager",
    "business strategy",
    "business development manager",
    "growth product",
    "growth manager",
    "strategy project manager",
    "strategy manager",
    "business operations",
    "general manager",
]

# Locations of interest
LOCATION_KEYWORDS = [
    "singapore", "hong kong", "shenzhen", "guangzhou", "shanghai",
    "taipei", "malaysia", "kuala lumpur", "apac", "asia",
    "southeast asia", "remote",
]

# Exclude
EXCLUDE_KEYWORDS = [
    "designer", "engineer", "developer", "sre", "devops", "hrbp",
    "compliance", "aml", "legal", "recruiter", "talent", "head of hr",
    "head of organization", "test development", "techops", "security",
    "data scientist", "data analyst", "backend", "frontend", "blockchain",
    "infrastructure", "finance manager", "accounting", "catalog",
    "audit", "wholesale", "communications", "pr ", "total rewards",
    "custody operations", "card operations", "b2b payment risk",
    "fraud strategy manager",  # too operational
]

EXCLUDE_LOCATIONS = ["pakistan", "germany", "netherlands", "australia", "uk ", "brazil", "india", "japan"]
SKIP_TITLES = ["director", "vp ", "vice president", "managing director", "chief", "intern"]

def fetch_jobs(company, base_url, max_pages=3):
    jobs = []
    for page in range(max_pages):
        url = f"{base_url}?page={page}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            break
        batch = data.get("jobs", [])
        if not batch:
            break
        jobs.extend(batch)
        if len(batch) < 50:
            break
    return jobs

def is_relevant(job):
    title = job.get("title", "").lower()
    location = job.get("location", {}).get("name", "").lower()
    
    for ex in EXCLUDE_KEYWORDS:
        if ex in title:
            return False
    for skip in SKIP_TITLES:
        if skip in title:
            return False
    
    matches = any(kw in title for kw in STRONG_KEYWORDS)
    if not matches:
        return False
    
    loc_match = any(loc in location for loc in LOCATION_KEYWORDS)
    if not loc_match:
        return False
    
    # Exclude bad locations
    for bad in EXCLUDE_LOCATIONS:
        if bad in location:
            return False
    
    return True

def main():
    # Load existing IDs
    db_path = "/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json"
    with open(db_path) as f:
        existing = json.load(f)
    
    existing_gids = set()
    for j in existing:
        gid = j.get("greenhouse_id")
        if gid:
            existing_gids.add(gid)
    existing_urls = {j.get("url", "") for j in existing}
    
    new_jobs = []
    
    for company, base_url in COMPANIES.items():
        jobs = fetch_jobs(company, base_url)
        for job in jobs:
            if not is_relevant(job):
                continue
            gid = job.get("id")
            if gid in existing_gids:
                continue
            url = f"https://boards.greenhouse.io/{company}/jobs/{gid}"
            if url in existing_urls:
                continue
            
            location = job.get("location", {}).get("name", "Remote")
            company_name = company.upper() if company in ("okx",) else company.title()
            
            new_jobs.append({
                "company": company_name,
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
                "description": "",
            })
    
    # Dedup by greenhouse_id
    seen = set()
    deduped = []
    for j in new_jobs:
        gid = j.get("greenhouse_id")
        if gid not in seen:
            seen.add(gid)
            deduped.append(j)
    
    print(json.dumps(deduped, indent=2, ensure_ascii=False))
    print(f"New jobs found: {len(deduped)}", file=sys.stderr)

if __name__ == "__main__":
    main()
