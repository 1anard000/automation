#!/usr/bin/env python3
"""Job scanner — Greenhouse API for known companies."""
import json, subprocess, os
from datetime import datetime
from collections import Counter

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
    "analytics", "monetization", "pricing", "operations", "data strategy",
    "machine learning", "go-to-market", "gtm", "revenue",
]
SKIP_KEYWORDS = ["intern", "internship"]
SKIP_TITLE_WORDS = ["director", "vp ", "vice president", "managing director", "chief"]

# Asia locations filter
ASIA_LOCATIONS = ["shenzhen", "hong kong", "singapore", "guangzhou", "shanghai",
                  "beijing", "asia", "apac", "sea ", "southeast", "remote",
                  "kuala lumpur", "taipei", "tokyo", "bangkok", "jakarta",
                  "manila", "ho chi minh", "hcmc"]

# Greenhouse companies to scan (using /v1/boards/{slug}/jobs)
GREENHOUSE_COMPANIES = {
    "okx": "OKX",
    "stripe": "Stripe",
    "coupang": "Coupang",
    "adyen": "Adyen",
    "agoda": "Agoda",
    "xendit": "Xendit",
    "grab": "Grab",
}

def fetch_greenhouse(company_slug, company_name):
    """Fetch jobs from Greenhouse API for a company."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs"
    try:
        result = subprocess.run(
            ["curl", "-s", "-L", "--max-time", "20", url],
            capture_output=True, text=True, timeout=25
        )
        data = json.loads(result.stdout)
        jobs = data.get("jobs", [])
        print(f"  [{company_name}] {len(jobs)} total jobs")
        
        new_jobs = []
        for job in jobs:
            title = job.get("title", "")
            location = job.get("location", {}).get("name", "")
            job_url = job.get("absolute_url", "")
            
            # Filter: must be in Asia
            if not any(k in location.lower() for k in ASIA_LOCATIONS):
                continue
            
            # Filter: skip internships
            title_lower = title.lower()
            if any(k in title_lower for k in SKIP_KEYWORDS):
                continue
            
            # Check if matches target profile
            matches_target = any(k in title_lower for k in TARGET_KEYWORDS)
            if not matches_target:
                continue
            
            # Skip Director/VP/Managing Director/Chief
            # But allow "Lead" and "Senior Manager"
            if any(k in title_lower for k in SKIP_TITLE_WORDS):
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
                "source": "greenhouse_api",
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
    now = datetime.now()
    print(f"=== Job Scanner Run: {now.strftime('%Y-%m-%d %H:%M')} ===")
    print(f"Existing jobs in DB: {len(existing)}")
    print()
    
    all_new = []
    
    # 1. Scan Greenhouse APIs
    print("--- Greenhouse API Scan ---")
    for slug, name in GREENHOUSE_COMPANIES.items():
        new = fetch_greenhouse(slug, name)
        all_new.extend(new)
        if new:
            print(f"  → {len(new)} NEW matching jobs from {name}")
            for j in new:
                print(f"    📌 {j['title']} ({j['location']})")
        else:
            print(f"  → 0 new matching jobs from {name}")
    
    # 2. Note: Browser-based scraping not available
    print()
    print("--- Browser-based sites (not available in cron) ---")
    print("  51job, Liepin, Tencent Careers, ByteDance Careers require browser tool")
    
    # 3. Add new jobs to DB
    print()
    if all_new:
        print(f"=== ADDING {len(all_new)} NEW JOBS ===")
        existing.extend(all_new)
        with open(DB_PATH, "w") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        print(f"Database updated: {len(existing)} total jobs")
    else:
        print("=== No new jobs found ===")
    
    # 4. Stats
    print()
    print("--- Current Dashboard Stats ---")
    sources = Counter(j.get("source", "unknown") for j in existing)
    print(f"  Total jobs: {len(existing)}")
    print(f"  Top sources: {sources.most_common(5)}")
    
    # 5. Build WeChat output
    print()
    print("=== WECHAT_OUTPUT_START ===")
    print(f"NEW_COUNT|{len(all_new)}")
    print(f"TOTAL|{len(existing)}")
    print(f"DATE|{now.strftime('%Y-%m-%d %H:%M')}")
    for j in all_new:
        print(f"JOB|{j['title']}|{j['company']}|{j['location']}|{j['url']}")
    print("=== WECHAT_OUTPUT_END ===")

if __name__ == "__main__":
    main()
