#!/usr/bin/env python3
"""Scan Greenhouse job boards for relevant positions."""
import json
import urllib.request
import re
from datetime import datetime

TODAY = datetime.now().strftime('%Y-%m-%d')

# Load existing jobs
with open('OKComputer_职位搜索清单/jobs-all.json') as f:
    existing_jobs = json.load(f)

existing_urls = set()
existing_gh_ids = set()
for j in existing_jobs:
    url = j.get('url', '')
    existing_urls.add(url)
    gh_id = j.get('greenhouse_id')
    if gh_id:
        existing_gh_ids.add(str(gh_id))

print(f"Existing jobs: {len(existing_jobs)}, URLs: {len(existing_urls)}, GH IDs: {len(existing_gh_ids)}")

# Companies to scan
COMPANIES = {
    'okx': 'https://boards-api.greenhouse.io/v1/jobs/okx',
    'stripe': 'https://boards-api.greenhouse.io/v1/jobs/stripe',
    'airwallex': 'https://boards-api.greenhouse.io/v1/jobs/airwallex',
    'coupang': 'https://boards-api.greenhouse.io/v1/jobs/coupang',
    'bybit': 'https://boards-api.greenhouse.io/v1/jobs/bybit',
}

# Title keywords for PM/Strategy/BizOps/Growth/GM roles
TITLE_KEYWORDS = [
    'product manager', 'strategy', 'bizops', 'business operations',
    'growth', 'general manager', 'gm ', 'head of', 'chief of staff',
    'program manager', 'commercial', 'expansion',
]

# Target locations
TARGET_LOCS = [
    'shenzhen', 'hong kong', 'shanghai', 'guangzhou',
    'singapore', 'tokyo', 'taipei', 'kuala lumpur',
    'seoul', 'korea', 'malaysia', 'japan', 'indonesia',
    'remote', 'apac',
]

# Roles to skip
SKIP_KEYWORDS = [
    'director', 'vp ', 'vice president', 'intern', 'internship',
    'software engineer', 'frontend', 'backend', 'devops',
    'data scientist', 'analyst', 'designer', 'recruiter',
    'accountant', 'legal', 'paralegal', 'receptionist',
]

def should_skip_title(title):
    tl = title.lower()
    for kw in SKIP_KEYWORDS:
        if kw in tl:
            return True
    return False

def matches_title(title):
    tl = title.lower()
    for kw in TITLE_KEYWORDS:
        if kw in tl:
            return True
    return False

def matches_location(loc):
    ll = loc.lower()
    for tl in TARGET_LOCS:
        if tl in ll:
            return True
    return False

def is_english_friendly(title, description=''):
    """Check if job seems English-friendly."""
    combined = (title + ' ' + description).lower()
    cn_keywords = ['中文', '普通话', 'mandarin required', 'chinese required',
                   'bilingual', '粤语', 'cantonese']
    for kw in cn_keywords:
        if kw in combined:
            return False
    return True

new_jobs = []

for company, api_url in COMPANIES.items():
    print(f"\n--- Scanning {company} ---")
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"  ERROR: {e}")
        continue

    jobs = data.get('jobs', [])
    print(f"  Total jobs on board: {len(jobs)}")

    matched = 0
    for j in jobs:
        title = j.get('title', '')
        loc = j.get('location', {}).get('name', '')
        gh_id = str(j.get('id', ''))

        if gh_id in existing_gh_ids:
            continue
        if not matches_title(title):
            continue
        if should_skip_title(title):
            continue
        if not matches_location(loc):
            continue

        desc_raw = j.get('content', '') or ''
        # Strip HTML tags for keyword check
        desc_clean = re.sub(r'<[^>]+>', '', desc_raw)[:2000]

        if not is_english_friendly(title, desc_clean):
            continue

        url = f"https://boards.greenhouse.io/{company}/jobs/{j['id']}"

        new_job = {
            'company': company.title() if company != 'okx' else 'OKX',
            'title': title,
            'location': loc,
            'salary': 'Not listed',
            'url': url,
            'greenhouse_id': int(gh_id),
            'scanned_date': TODAY,
            'date_source': 'from_scanned_date',
            'source': 'greenhouse_api',
            'english_friendly': True,
            'category': 'product',
            'grade': 'A-1',
            'city_normalized': loc.split(',')[0] if ',' in loc else loc,
            'quality_score': 57,
            'quality_tier': 'B',
            'description': desc_clean[:500] if desc_clean else ''
        }
        new_jobs.append(new_job)
        matched += 1
        print(f"  NEW: {title} | {loc}")

    print(f"  New matches: {matched}")

print(f"\n=== Total new jobs found: {len(new_jobs)} ===")
for j in new_jobs:
    print(f"  {j['company']}: {j['title']} @ {j['location']}")
    print(f"    {j['url']}")

# Write new jobs to a temp file for later merging
with open('/tmp/greenhouse_new_jobs.json', 'w') as f:
    json.dump(new_jobs, f, ensure_ascii=False, indent=2)

print(f"\nWrote {len(new_jobs)} new jobs to /tmp/greenhouse_new_jobs.json")
