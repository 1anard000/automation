#!/usr/bin/env python3
"""Fetch Greenhouse API jobs and filter for APAC PM roles."""
import json, subprocess, os, hashlib
from datetime import datetime

# Load existing URLs for dedup
existing_urls = set(json.load(open('/tmp/all_urls.json')))
existing_titles = set(json.load(open('/tmp/all_titles.json')))

APAC_KW = ['singapore', 'hong kong', 'shanghai', 'shenzhen', 'guangzhou',
            'taipei', 'tokyo', 'seoul', 'bangkok', 'apac', 'asia pacific',
            'china', 'beijing', 'hong kong sar']
PM_KW = ['product manager', 'product lead', 'strategy', 'growth',
          'program manager', 'bizops', 'business operations',
          'general manager', 'marketing strategy', 'strategic',
          'product operations', 'go-to-market', 'gtm', 'partnerships',
          'product specialist', 'product marketing']
EXCLUDE_KW = ['director', 'vp', 'vice president', 'chief', 'head of',
               'intern', 'internship', 'staff+', 'distinguished',
               'engineer', 'data scientist', 'designer', 'ux designer',
               'recruiter', 'talent', 'coordinator', 'associate',
               'analyst', 'specialist', 'consultant', 'architect',
               'software', 'backend', 'frontend', 'fullstack', 'full stack',
               'devops', 'sre', 'qa', 'test']

BOARDS = [
    'okx', 'stripe', 'coinbase', 'twilio', 'flexport', 'agoda',
    'databricks', 'anthropic', 'xendit', 'bybit', 'airbnb',
    'figma', 'cloudflare', 'bitmex', 'postman', 'gemini',
    'sendbird', 'braze', 'payoneer', 'lazada', 'shopee',
    'grab', 'gojek', 'traveloka', 'carousell', 'ramp'
]

new_jobs = []
errors = []

for board in BOARDS:
    fpath = f'/tmp/gh_{board}.json'
    try:
        r = subprocess.run(
            ['curl', '-s', '-m', '15', f'https://boards-api.greenhouse.io/v1/boards/{board}/jobs', '-o', fpath],
            capture_output=True, text=True, timeout=20
        )
        if not os.path.exists(fpath) or os.path.getsize(fpath) < 10:
            errors.append(f'{board}: empty response')
            continue
        data = json.load(open(fpath))
        jobs = data.get('jobs', [])
    except Exception as e:
        errors.append(f'{board}: {str(e)[:80]}')
        continue

    for j in jobs:
        loc = j.get('location', {}).get('name', '').lower()
        title = j.get('title', '')
        title_lower = title.lower()
        url = j.get('absolute_url', '')
        
        # Must be APAC
        if not any(k in loc for k in APAC_KW):
            continue
        # Must match PM/strategy/growth
        if not any(k in title_lower for k in PM_KW):
            continue
        # Exclude senior/irrelevant
        if any(k in title_lower for k in EXCLUDE_KW):
            continue
        # Dedup against existing
        if url in existing_urls:
            continue
        if title_lower.strip() in existing_titles:
            continue
        
        salary = j.get('salary', '')
        
        new_jobs.append({
            'title': title,
            'company': board.upper() if board in ['okx','stripe','coinbase'] else board.title(),
            'location': j.get('location', {}).get('name', ''),
            'url': url,
            'salary': salary if salary else '',
            'source': 'greenhouse-api',
            'scanned_date': datetime.now().strftime('%Y-%m-%d'),
            'job_id': hashlib.md5(url.encode()).hexdigest()[:12],
            'status': 'not_applied',
            'status_date': datetime.now().strftime('%Y-%m-%d'),
            'last_touch_date': datetime.now().strftime('%Y-%m-%d'),
            'role_type': 'Product Management',
            'english_friendly': True,
            'has_direct_link': True,
            'url_type': 'direct',
            'quality_score': None,
            'quality_tier': '',
            'low_quality': False
        })

# Output
result = {
    'new_jobs': new_jobs,
    'errors': errors,
    'boards_scraped': len(BOARDS),
    'new_count': len(new_jobs)
}
json.dump(result, open('/tmp/greenhouse_results.json', 'w'), indent=2)
print(f'Greenhouse: {len(new_jobs)} new APAC PM jobs from {len(BOARDS)} boards')
print(f'Errors: {len(errors)} - {errors[:5]}')
for j in new_jobs[:10]:
    print(f'  {j["title"]} @ {j["company"]} - {j["location"]} - {j["url"]}')
