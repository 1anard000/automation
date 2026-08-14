#!/usr/bin/env python3
"""
Greenhouse scanner - filtered for Senior PM / Strategy / BizOps / Growth / GM roles.
Only outputs jobs that match the target profile.
"""
import json
import urllib.request
import sys
import os
import re

COMPANIES = {
    "okx": "https://boards-api.greenhouse.io/v1/boards/okx/jobs",
    "stripe": "https://boards-api.greenhouse.io/v1/boards/stripe/jobs",
    "coupang": "https://boards-api.greenhouse.io/v1/boards/coupang/jobs",
    "bybit": "https://boards-api.greenhouse.io/v1/boards/bybit/jobs",
}

# Strong match: these titles ARE the target
STRONG_KEYWORDS = [
    "product manager",
    "product management",
    "business strategy",
    "business development manager",
    "growth product",
    "growth manager",
    "strategy project manager",
    "strategy manager",
    "business operations",
    "bizops",
    "general manager",
]

# Location keywords
LOCATION_KEYWORDS = [
    "singapore", "hong kong", "shenzhen", "guangzhou", "shanghai",
    "taipei", "malaysia", "kuala lumpur", "apac", "asia",
    "southeast asia", "remote",
]

# Exclude these roles
EXCLUDE_KEYWORDS = [
    "designer", "engineer", "developer", "sre", "devops", "hrbp",
    "compliance", "aml", "legal", "recruiter", "talent", "head of hr",
    "head of organization", "test development", "techops", "security",
    "data scientist", "data analyst", "backend", "frontend", "blockchain",
    "infrastructure", "finance manager", "accounting", "catalog",
    "audit", "wholesale", "communications", "pr ", "total rewards",
    "custody operations", "card operations", "b2b payment risk",
]

def fetch_jobs(company, base_url, max_pages=3):
    """Fetch jobs from a Greenhouse board."""
    jobs = []
    for page in range(max_pages):
        url = f"{base_url}?page={page}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            print(f"  Error {company} p{page}: {e}", file=sys.stderr)
            break
        batch = data.get("jobs", [])
        if not batch:
            break
        jobs.extend(batch)
        if len(batch) < 50:
            break
    return jobs

def is_relevant(job):
    """Strict filter for target profile."""
    title = job.get("title", "").lower()
    location = job.get("location", {}).get("name", "").lower()
    
    # Exclude unwanted roles
    for ex in EXCLUDE_KEYWORDS:
        if ex in title:
            return False
    
    # Must match strong keyword
    matches = any(kw in title for kw in STRONG_KEYWORDS)
    if not matches:
        return False
    
    # Must be in target location
    loc_match = any(loc in location for loc in LOCATION_KEYWORDS)
    if not loc_match:
        return False
    
    return True

def main():
    # Load existing jobs
    db_path = "/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json"
    try:
        with open(db_path) as f:
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
        print(f"  Total: {len(jobs)}, matching...", file=sys.stderr)
        
        count = 0
        for job in jobs:
            if not is_relevant(job):
                continue
            
            gid = job.get("id")
            if gid in existing_ids:
                continue
            
            location = job.get("location", {}).get("name", "Remote")
            url = f"https://boards.greenhouse.io/{company}/jobs/{gid}"
            
            if url in existing_urls:
                continue
            
            company_name = company.upper() if company in ("okx",) else company.title()
            
            entry = {
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
            }
            new_jobs.append(entry)
            count += 1
            print(f"  NEW: {company_name} - {job.get('title','')} @ {location}", file=sys.stderr)
        
        print(f"  New relevant: {count}", file=sys.stderr)
    
    # Deduplicate by greenhouse_id
    seen = set()
    deduped = []
    for j in new_jobs:
        gid = j.get("greenhouse_id")
        if gid not in seen:
            seen.add(gid)
            deduped.append(j)
    
    print(f"\nTotal new (deduplicated): {len(deduped)}", file=sys.stderr)
    print(json.dumps(deduped, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
