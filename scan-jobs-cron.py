#!/usr/bin/env python3
"""Job scanner — Greenhouse API for known companies + local DB stats."""
import json, subprocess, os, sys
from datetime import datetime

WORKSPACE = "/Users/iancolrick/.openclaw/workspace"
DB_PATH = os.path.join(WORKSPACE, "OKComputer_职位搜索清单", "jobs-all.json")

# Load existing jobs for dedup
existing = json.load(open(DB_PATH))
existing_urls = set(j.get("url", "") for j in existing)
existing_keys = set(
    (j.get("title", "").lower().strip(), j.get("company", "").lower().strip())
    for j in existing
)

# Target profile filter
TARGET_KEYWORDS = [
    "product manager", "strategy", "bizops", "business operations",
    "growth", "gm", "general manager", "lead", "senior manager",
    "commercial", "cross-border", "marketplace", "fintech", "ai product",
]
SKIP_KEYWORDS = ["director", "vp ", "vice president", "managing director", "intern", "internship"]
MIN_SALARY_RMB = 90000  # annual → ~7500/mo; or we check listed salary

# Greenhouse companies to scan
GREENHOUSE_COMPANIES = {
    "okx": "OKX",
    "stripe": "Stripe",
    "airwallex": "Airwallex",
    "coupang": "Coupang",
    "plaid": "Plaid",
}

def fetch_greenhouse(company_slug, company_name):
    """Fetch jobs from Greenhouse API for a company."""
    url = f"https://boards-api.greenhouse.io/v1/jobs/{company_slug}?content=false"
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "15", url],
            capture_output=True, text=True, timeout=20
        )
        data = json.loads(result.stdout)
        jobs = data.get("jobs", [])
        print(f"  [{company_name}] {len(jobs)} total jobs on Greenhouse")
        
        new_jobs = []
        for job in jobs:
            title = job.get("title", "")
            location = job.get("location", {}).get("name", "")
            job_url = job.get("absolute_url", "")
            
            # Filter: must be in Asia/SZ/HK/SG
            asia_keywords = ["shenzhen", "hong kong", "singapore", "guangzhou", "shanghai", "beijing", "asia", "apac", "remote"]
            if not any(k in location.lower() for k in asia_keywords):
                continue
            
            # Filter: skip Director/VP/Intern
            title_lower = title.lower()
            if any(k in title_lower for k in SKIP_KEYWORDS):
                continue
            
            # Check if matches target profile
            matches_target = any(k in title_lower for k in TARGET_KEYWORDS)
            if not matches_target:
                continue
            
            # Dedup
            if job_url in existing_urls:
                continue
            key = (title.lower().strip(), company_name.lower().strip())
            if key in existing_keys:
                continue
            
            new_jobs.append({
                "title": title,
                "company": company_name,
                "location": location,
                "salary": "Not listed",
                "url": job_url,
                "source": "greenhouse",
                "role_type": "target_profile",
                "description": f"Greenhouse listing for {company_name} in {location}",
                "scanned_date": datetime.now().strftime("%Y-%m-%d"),
                "posted_date": datetime.now().isoformat(),
            })
            existing_urls.add(job_url)
            existing_keys.add(key)
        
        return new_jobs
    except Exception as e:
        print(f"  [{company_name}] Error: {e}")
        return []

def main():
    print(f"=== Job Scanner Run: {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    print(f"Existing jobs in DB: {len(existing)}")
    print()
    
    all_new = []
    
    # 1. Scan Greenhouse APIs
    print("--- Greenhouse API Scan ---")
    for slug, name in GREENHOUSE_COMPANIES.items():
        new = fetch_greenhouse(slug, name)
        all_new.extend(new)
        if new:
            print(f"  → {len(new)} new jobs from {name}")
    
    # 2. Note: Browser-based scraping not available in this cron session
    print()
    print("--- Browser-based sites ---")
    print("  51job, Liepin, Tencent Careers, ByteDance Careers: SKIPPED (no browser tool in cron)")
    print("  Recommendation: Enable browser tool or use separate session for web scraping")
    
    # 3. Add new jobs to DB
    print()
    if all_new:
        print(f"=== Adding {len(all_new)} new jobs to database ===")
        for j in all_new:
            print(f"  📌 {j['title']} @ {j['company']} ({j['location']})")
        existing.extend(all_new)
        with open(DB_PATH, "w") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        print(f"  Database updated: {len(existing)} total jobs")
    else:
        print("=== No new jobs found from Greenhouse APIs ===")
    
    # 4. Dashboard stats
    print()
    print("--- Dashboard Stats ---")
    from collections import Counter
    sources = Counter(j.get("source", "unknown") for j in existing)
    locations = Counter(j.get("location", "unknown") for j in existing)
    print(f"  Total jobs: {len(existing)}")
    print(f"  Sources: {dict(sources)}")
    top_locs = locations.most_common(5)
    print(f"  Top locations: {top_locs}")
    
    # Output summary for WeChat message
    print()
    print("=== WECHAT SUMMARY ===")
    print(f"NEW_JOBS_COUNT={len(all_new)}")
    for j in all_new:
        print(f"NEW_JOB|{j['title']}|{j['company']}|{j['location']}|{j['url']}")
    print(f"TOTAL_JOBS={len(existing)}")
    print(f"SCAN_DATE={datetime.now().strftime('%Y-%m-%d %H:%M')}")

if __name__ == "__main__":
    main()
