#!/usr/bin/env python3
"""Scan Greenhouse APIs for new jobs."""
import json
import urllib.request
import os
from datetime import datetime

JOBS_DB = os.path.expanduser("~/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json")
TODAY = datetime.now().strftime("%Y-%m-%d")

# Target locations
TARGET_LOCATIONS = [
    "shenzhen", "hong kong", "guangzhou", "shanghai", "singapore",
    "taipei", "tokyo", "seoul", "apac", "asia", "bangkok",
    "indonesia", "malaysia", "philippines", "vietnam", "india", "bengaluru"
]

# Keywords for filtering
TARGET_KEYWORDS = [
    "product manager", "product management", "strategy", "bizops", "biz ops",
    "growth", "general manager", "business development", "partnerships",
    "operations", "monetization", "commercial", "lead", "senior manager"
]

# Skip titles
SKIP_KEYWORDS = [
    "director", "vp", "vice president", "managing director", "intern",
    "internship", "co-op", "staff engineer", "software engineer",
    "data scientist", "ml engineer", "devops", "sre", "qa engineer"
]

# Companies to scan via Greenhouse
GREENHOUSE_COMPANIES = {
    "okx": "OKX",
    "stripe": "Stripe",
    "airwallex": "Airwallex",
    "coupang": "Coupang",
}

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
    """Fetch all jobs from a Greenhouse board."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  Error fetching {board_token}: {e}")
        return None

def fetch_greenhouse_job_detail(board_token, job_id):
    """Fetch job content from Greenhouse."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs/{job_id}?content=true"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  Error fetching job {job_id}: {e}")
        return None

def extract_description(html_content):
    """Extract text from HTML content."""
    if not html_content:
        return ""
    import re
    text = re.sub(r'<[^>]+>', ' ', html_content)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:500]

def main():
    print(f"=== Job Scanner Run: {TODAY} ===")
    
    existing = load_existing_jobs()
    existing_urls = set(j.get('url', '') for j in existing)
    existing_titles_company = set(
        (j.get('title', '').lower().strip(), j.get('company', '').lower().strip())
        for j in existing
    )
    
    print(f"Existing jobs in DB: {len(existing)}")
    print(f"Unique URLs: {len(existing_urls)}")
    
    new_jobs = []
    
    for board_token, company_name in GREENHOUSE_COMPANIES.items():
        print(f"\n--- Scanning {company_name} ({board_token}) ---")
        data = fetch_greenhouse_board(board_token)
        if not data:
            continue
        
        jobs = data.get('jobs', [])
        print(f"  Total jobs on board: {len(jobs)}")
        
        count = 0
        for j in jobs:
            loc = j.get('location', {}).get('name', 'Unknown')
            title = j.get('title', '')
            jid = j.get('id', '')
            url = f"https://job-boards.greenhouse.io/{board_token}/jobs/{jid}"
            updated = j.get('updated_at', '')
            
            # Check if already in DB
            if url in existing_urls:
                continue
            
            title_lower = title.lower().strip()
            company_lower = company_name.lower().strip()
            if (title_lower, company_lower) in existing_titles_company:
                continue
            
            # Filter by location
            if not is_target_location(loc):
                continue
            
            # Filter by role type
            if not is_target_role(title):
                continue
            
            # Skip unwanted roles
            if should_skip(title):
                continue
            
            # Fetch job details for description
            detail = fetch_greenhouse_job_detail(board_token, jid)
            desc = ""
            if detail:
                desc = extract_description(detail.get('content', ''))
            
            new_job = {
                "title": title,
                "company": company_name,
                "location": loc,
                "salary": "Not listed",
                "url": url,
                "source": f"greenhouse_{board_token}",
                "role_type": "target_profile",
                "description": desc,
                "scanned_date": TODAY,
                "posted_date": updated if updated else TODAY,
                "grade": "A-1"
            }
            new_jobs.append(new_job)
            count += 1
            print(f"  NEW: {title} @ {company_name} | {loc}")
        
        print(f"  New relevant jobs found: {count}")
    
    # Add all new jobs to the database
    if new_jobs:
        existing.extend(new_jobs)
        save_jobs(existing)
        print(f"\n=== Added {len(new_jobs)} new jobs to database ===")
    else:
        print(f"\n=== No new jobs found ===")
    
    # Output summary for the cron job
    print(f"\n=== SUMMARY ===")
    print(f"NEW_JOBS_COUNT={len(new_jobs)}")
    for j in new_jobs:
        print(f"NEW_JOB: {j['title']} @ {j['company']} | {j['location']} | {j['url']}")
    
    return new_jobs

if __name__ == "__main__":
    main()
