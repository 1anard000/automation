#!/usr/bin/env python3
"""Scan Greenhouse boards for relevant jobs."""
import json
import urllib.request
import sys
from datetime import datetime

COMPANIES = {
    'okx': 'OKX',
    'stripe': 'Stripe',
    'airwallex': 'Airwallex',
    'coupang': 'Coupang',
    'agoda': 'Agoda',
}

KEYWORDS = ['product', 'strategy', 'growth', 'bizops', 'general manager', 
            'head of', 'business development', 'partnerships', 'operations']

TARGET_LOCATIONS = ['shenzhen', 'hong kong', 'guangzhou', 'shanghai', 'singapore', 
                    'beijing', 'bangkok', 'taipei', 'tokyo', 'seoul']

def fetch_greenhouse_jobs(company_slug):
    """Fetch all jobs from a Greenhouse board."""
    url = f"https://boards-api.greenhouse.io/v1/jobs/{company_slug}?content=false"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            return data.get('jobs', [])
    except Exception as e:
        print(f"  Error fetching {company_slug}: {e}", file=sys.stderr)
        return []

def is_relevant(job, company_name):
    """Check if a job matches our target profile."""
    title = job.get('title', '').lower()
    location = job.get('location', {}).get('name', '').lower()
    
    # Must match at least one keyword
    if not any(kw in title for kw in KEYWORDS):
        return False
    
    # Skip director/VP level
    skip_levels = ['director', 'vp ', 'vice president', 'managing director', 'chief']
    if any(skip in title for skip in skip_levels):
        return False
    
    # Skip internships
    if 'intern' in title:
        return False
    
    # Check location relevance
    location_match = any(loc in location for loc in TARGET_LOCATIONS)
    
    return True

def main():
    all_new_jobs = []
    
    for slug, name in COMPANIES.items():
        print(f"\n=== Scanning {name} ({slug}) ===")
        jobs = fetch_greenhouse_jobs(slug)
        print(f"  Total jobs: {len(jobs)}")
        
        relevant = [j for j in jobs if is_relevant(j, name)]
        print(f"  Relevant jobs: {len(relevant)}")
        
        for job in relevant:
            location = job.get('location', {}).get('name', 'Unknown')
            print(f"  [{job['id']}] {job['title']} | {location}")
            all_new_jobs.append({
                'company': name,
                'title': job['title'],
                'location': location,
                'url': f"https://job-boards.greenhouse.io/{slug}/jobs/{job['id']}",
                'posted': job.get('updated_at', ''),
                'source': 'greenhouse'
            })
    
    print(f"\n=== Summary ===")
    print(f"Total relevant jobs found: {len(all_new_jobs)}")
    
    # Save to temp file
    with open('/Users/iancolrick/.openclaw/workspace/tmp_greenhouse_results.json', 'w') as f:
        json.dump(all_new_jobs, f, indent=2)
    print("Results saved to tmp_greenhouse_results.json")

if __name__ == '__main__':
    main()
