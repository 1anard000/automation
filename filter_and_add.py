#!/usr/bin/env python3
"""Filter Greenhouse results and add new jobs to database."""
import json, urllib.request, ssl, re
from datetime import datetime

ssl._create_default_https_context = ssl._create_unverified_context

# Load existing jobs
jobs = json.load(open('OKComputer_职位搜索清单/jobs-all.json'))
existing_urls = set(j.get('url', '').lower().strip() for j in jobs)
existing_title_company = set(
    (j.get('title', '').lower().strip(), j.get('company', '').lower().strip()) 
    for j in jobs
)

print(f"Existing jobs: {len(jobs)}")
print(f"Existing URLs: {len(existing_urls)}")

def fetch_url(url, headers=None):
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': '*/*'
        }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read()
        for enc in ['utf-8', 'gbk', 'latin-1']:
            try:
                return raw.decode(enc)
            except:
                continue
        return raw.decode('utf-8', errors='ignore')

# Title keywords to match
TITLE_MATCH = [
    'product manager', 'strategy', 'growth', 'gm', 'head of',
    'bizops', 'business operations', 'commercial', 'business development',
    'cross-border', 'marketplace', 'fintech', 'payments', 'platform',
    'lead', 'chief of staff', 'go-to-market', 'gtm',
    'expansion', 'partnerships'
]

# Title keywords to skip
SKIP_TITLE = [
    'intern', 'internship', 'staff engineer', 'software engineer',
    'data scientist', 'devops', 'sre', 'ux designer', 'designer',
    'recruiter', 'recruiting', 'talent acquisition', 'accountant',
    'legal counsel', 'paralegal', 'receptionist', 'admin assistant',
    'frontend', 'backend', 'full stack', 'quant developer',
    'data engineer', 'data analyst', 'architect'
]

# Seniority to skip
SKIP_SENIORITY = [
    'vice president', 'svp', 'evp', 'chief ', 'cfo', 'cto', 'ceo', 'coo',
    'account executive', 'hunter'
]

# Location keywords
LOC_MATCH = [
    'shenzhen', 'hong kong', 'singapore', 'shanghai', 'guangzhou',
    'asia', 'apac', 'greater china', 'china', 'sea', 'southeast',
    'bangkok', 'taipei', 'tokyo', 'manila', 'jakarta', 'kuala lumpur'
]

# Companies to skip (crypto exchanges per rules)
SKIP_COMPANIES = ['binance', 'okx', 'coins.ph', 'bitdeer', 'bullish', 'coinmarketcap',
                  'btse', 'decard', 'gate', 'osl', 'bitget', 'huobi', 'kucoin', 'bybit', 'kraken']

today = datetime.now().strftime('%Y-%m-%d')
new_jobs = []

# Scan boards
boards = {
    'affirm': 'https://boards-api.greenhouse.io/v1/boards/affirm/jobs',
    'agoda': 'https://boards-api.greenhouse.io/v1/boards/agoda/jobs',
    'stripe': 'https://boards-api.greenhouse.io/v1/boards/stripe/jobs',
}

for board_name, api_url in boards.items():
    try:
        text = fetch_url(api_url)
        data = json.loads(text)
        board_jobs = data.get('jobs', [])
        print(f"\n=== {board_name.upper()} ({len(board_jobs)} total) ===")
        
        matches = 0
        for j in board_jobs:
            title = j.get('title', '')
            loc = j.get('location', {}).get('name', '') if j.get('location') else ''
            tl = title.lower()
            ll = loc.lower()
            
            # Skip unwanted roles
            if any(k in tl for k in SKIP_TITLE):
                continue
            if any(k in tl for k in SKIP_SENIORITY):
                continue
            
            # Check title relevance
            title_match = any(k in tl for k in TITLE_MATCH)
            # Check location relevance
            loc_match = any(k in ll for k in LOC_MATCH)
            
            if not (title_match and loc_match):
                continue
            
            # Build URL
            job_url = f"https://job-boards.greenhouse.io/{board_name}/jobs/{j.get('id', '')}"
            
            # Check if already in database
            if job_url.lower().strip() in existing_urls:
                continue
            if (title.lower().strip(), board_name.lower().strip()) in existing_title_company:
                continue
            
            # Check salary if available
            salary = ''
            if j.get('salary'):
                salary = j['salary']
            
            # Add to new jobs
            new_jobs.append({
                'company': board_name.title(),
                'title': title,
                'location': loc,
                'url': job_url,
                'salary': salary if salary else 'Not listed',
                'source': 'greenhouse_api',
                'scanned_date': today,
                'posted_date': j.get('updated_at', ''),
                'quality_score': 75,  # Default for Greenhouse API
                'quality_tier': 'B',
                'grade': 'B',
                'english_friendly': True,
                'platform': 'Greenhouse',
                'low_quality': False,
                'summary': f"{title} at {board_name.title()} in {loc}."
            })
            matches += 1
        
        print(f"  New matches: {matches}")
    except Exception as e:
        print(f"  Error: {e}")

print(f"\n=== TOTAL NEW JOBS TO ADD: {len(new_jobs)} ===")
for j in new_jobs:
    print(f"  {j['company']} | {j['title']} | {j['location']}")

# Save new jobs
with open('/tmp/new_jobs_to_add.json', 'w') as f:
    json.dump(new_jobs, f, ensure_ascii=False, indent=2)
print("\nSaved to /tmp/new_jobs_to_add.json")
