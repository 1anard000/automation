#!/usr/bin/env python3
"""Extended Greenhouse scrape with additional companies + Figma from the new batch."""
import json, subprocess, os, hashlib
from datetime import datetime

existing_urls = set(json.load(open('/tmp/all_urls.json')))
existing_titles = set(json.load(open('/tmp/all_titles.json')))

APAC_KW = ['singapore', 'hong kong', 'shanghai', 'shenzhen', 'guangzhou',
            'taipei', 'tokyo', 'seoul', 'bangkok', 'apac', 'asia pacific',
            'china', 'beijing', 'hong kong sar', 'malaysia', 'jakarta',
            'ho chi minh', 'vietnam', 'philippines', 'manila']
PM_KW = ['product manager', 'product lead', 'strategy', 'growth',
          'program manager', 'bizops', 'business operations',
          'general manager', 'marketing strategy', 'strategic',
          'product operations', 'go-to-market', 'gtm', 'partnerships',
          'product specialist', 'product marketing', 'product ops']
EXCLUDE_KW = ['director', 'vp', 'vice president', 'chief', 'head of',
               'intern', 'internship', 'staff+', 'distinguished',
               'engineer', 'data scientist', 'designer', 'ux designer',
               'recruiter', 'talent', 'coordinator', 'associate',
               'analyst', 'consultant', 'architect',
               'software', 'backend', 'frontend', 'fullstack', 'full stack',
               'devops', 'sre', 'qa', 'test', 'research', 'scientist',
               'marketer', 'sales', 'account', 'support', 'operations manager',
               'general manager of']

# Extended list including companies from references + new attempts
BOARDS = [
    # Tier 1 (already scraped, included for completeness check)
    'okx', 'stripe', 'coinbase', 'twilio', 'flexport', 'agoda',
    'databricks', 'anthropic', 'xendit', 'bybit', 'airbnb',
    # Tier 2
    'figma', 'cloudflare', 'bitmex', 'postman', 'gemini',
    'sendbird', 'braze', 'payoneer',
    # New attempts
    'plaid', 'n26', 'wise', 'mercury', 'vercel',
    'brex', 'ramp', 'rippling', 'deel',
    'mercadolibre', 'xiaomi', 'oppo', 'vivo',
    'shopee', 'propertyguru', 'ninja-van',
    'line', 'rakuten', 'samsung', 'naver',
    'careem', 'noon', 'talabat',
    'flipkart', 'meesho', 'phonepe',
    'lalamove', 'ghostrider', 'carro',
    'tiki', 'sendo', 'thegioididong',
]

new_jobs = []
errors = []
boards_scraped = 0

for board in BOARDS:
    fpath = f'/tmp/gh2_{board}.json'
    try:
        r = subprocess.run(
            ['curl', '-s', '-m', '15', f'https://boards-api.greenhouse.io/v1/boards/{board}/jobs', '-o', fpath],
            capture_output=True, text=True, timeout=20
        )
        if not os.path.exists(fpath) or os.path.getsize(fpath) < 10:
            continue
        with open(fpath, 'r') as f:
            data = json.load(f)
        jobs = data.get('jobs', [])
        if not jobs:
            continue
        boards_scraped += 1
    except Exception as e:
        errors.append(f'{board}: {str(e)[:80]}')
        continue

    for j in jobs:
        loc = j.get('location', {}).get('name', '').lower()
        title = j.get('title', '')
        title_lower = title.lower()
        url = j.get('absolute_url', '')
        
        if not any(k in loc for k in APAC_KW):
            continue
        if not any(k in title_lower for k in PM_KW):
            continue
        if any(k in title_lower for k in EXCLUDE_KW):
            continue
        if url in existing_urls:
            continue
        if title_lower.strip() in existing_titles:
            continue
        
        new_jobs.append({
            'title': title,
            'company': board.upper() if board in ['okx','stripe','coinbase','shopify'] else board.title(),
            'location': j.get('location', {}).get('name', ''),
            'url': url,
            'salary': j.get('salary', '') or '',
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

result = {
    'new_jobs': new_jobs,
    'errors': errors,
    'boards_scraped': boards_scraped,
    'boards_total': len(BOARDS),
    'new_count': len(new_jobs)
}
json.dump(result, open('/tmp/greenhouse_results2.json', 'w'), indent=2)
print(f'Extended Greenhouse: {len(new_jobs)} new APAC PM jobs from {boards_scraped}/{len(BOARDS)} active boards')
for j in new_jobs:
    print(f'  {j["title"]} @ {j["company"]} - {j["location"]} - {j["url"]}')
