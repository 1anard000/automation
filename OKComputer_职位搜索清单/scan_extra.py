#!/usr/bin/env python3
"""Scan additional Greenhouse boards for relevant jobs."""
import json
import urllib.request
import os
from datetime import datetime

JOBS_DB = os.path.expanduser("~/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json")
TODAY = datetime.now().strftime("%Y-%m-%d")

# Additional companies to check
EXTRA_COMPANIES = {
    "agoda": "Agoda",
    "xendit": "Xendit",
    "thunes": "Thunes",
    "grab": "Grab",
    "gojek": "Gojek",
    "payoneer": "Payoneer",
}

TARGET_LOCATIONS = [
    "shenzhen", "hong kong", "guangzhou", "shanghai", "singapore",
    "taipei", "tokyo", "seoul", "apac", "asia", "bangkok",
    "indonesia", "malaysia", "philippines", "vietnam", "india", "bengaluru"
]

TARGET_KEYWORDS = [
    "product manager", "product management", "strategy", "bizops", "biz ops",
    "growth", "general manager", "business development", "partnerships",
    "operations", "monetization", "commercial", "lead", "senior manager"
]

SKIP_KEYWORDS = [
    "director", "vp", "vice president", "managing director", "intern",
    "internship", "co-op", "staff engineer", "software engineer",
    "data scientist", "ml engineer", "devops", "sre", "qa engineer",
    "security analyst", "back-end engineer", "front-end engineer",
    "system engineer", "network engineer", "cloud engineer"
]

def load_existing_jobs():
    with open(JOBS_DB, 'r') as f:
        return json.load(f)

def save_jobs(jobs):
    with open(JOBS_DB, 'w') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

def is_target_location(loc_name):
    loc_lower = loc_name.lower()
    return any(k in loc_lower for k in TARGET_LOCATIONS)

def is_target_role(title):
    title_lower = title.lower()
    return any(k in title_lower for k in TARGET_KEYWORDS)

def should_skip(title):
    title_lower = title.lower()
    return any(k in title_lower for k in SKIP_KEYWORDS)

def fetch_greenhouse_board(board_token):
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return None

def main():
    print(f"=== Extra Company Scan: {TODAY} ===")
    
    existing = load_existing_jobs()
    existing_urls = set(j.get('url', '') for j in existing)
    existing_titles_company = set(
        (j.get('title', '').lower().strip(), j.get('company', '').lower().strip())
        for j in existing
    )
    
    new_jobs = []
    
    for board_token, company_name in EXTRA_COMPANIES.items():
        print(f"\n--- {company_name} ({board_token}) ---")
        data = fetch_greenhouse_board(board_token)
        if not data:
            print(f"  Skipped (API error)")
            continue
        
        jobs = data.get('jobs', [])
        count = 0
        for j in jobs:
            loc = j.get('location', {}).get('name', 'Unknown')
            title = j.get('title', '')
            jid = j.get('id', '')
            url = f"https://job-boards.greenhouse.io/{board_token}/jobs/{jid}"
            updated = j.get('updated_at', '')
            
            if url in existing_urls:
                continue
            
            title_lower = title.lower().strip()
            company_lower = company_name.lower().strip()
            if (title_lower, company_lower) in existing_titles_company:
                continue
            
            if not is_target_location(loc):
                continue
            
            if not is_target_role(title):
                continue
            
            if should_skip(title):
                continue
            
            new_job = {
                "title": title,
                "company": company_name,
                "location": loc,
                "salary": "Not listed",
                "url": url,
                "source": f"greenhouse_{board_token}",
                "role_type": "target_profile",
                "description": "",
                "scanned_date": TODAY,
                "posted_date": updated if updated else TODAY,
                "grade": "A-1"
            }
            new_jobs.append(new_job)
            count += 1
            print(f"  NEW: {title} @ {company_name} | {loc}")
        
        print(f"  New relevant: {count}")
    
    if new_jobs:
        existing.extend(new_jobs)
        save_jobs(existing)
        print(f"\n=== Added {len(new_jobs)} new jobs ===")
    else:
        print(f"\n=== No new jobs found ===")
    
    print(f"\nEXTRA_NEW={len(new_jobs)}")
    for j in new_jobs:
        print(f"NEW_JOB: {j['title']} @ {j['company']} | {j['location']} | {j['url']}")

if __name__ == "__main__":
    main()
