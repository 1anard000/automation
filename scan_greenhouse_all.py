#!/usr/bin/env python3
"""Get detailed job info from Greenhouse for relevant new roles."""
import json, urllib.request, sys
from datetime import datetime

TODAY = datetime.now().strftime('%Y-%m-%d')

# Load existing
with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json') as f:
    existing = json.load(f)
existing_urls = {j.get('url', '') for j in existing}
existing_titles = set()
for j in existing:
    existing_titles.add((j.get('company', '').lower(), j.get('title', '').lower().strip()))

new_jobs = []

# Scan more Greenhouse companies
COMPANIES = {
    'okx': 'OKX',
    'stripe': 'Stripe',
    'coupang': 'Coupang',
    'wise': 'Wise',
    'plaid': 'Plaid',
    'checkout.com': 'Checkout.com',
    'mercadopago': 'MercadoPago',
    'shopee': 'Shopee',
    'lazada': 'Lazada',
    'grab': 'Grab',
    'klook': 'Klook',
    'futu': 'Futu',
    'carousell': 'Carousell',
    'bytedance': 'ByteDance',
    'tiktok': 'TikTok',
}

APAC_LOCS = ['singapore', 'hong kong', 'shenzhen', 'shanghai', 'guangzhou', 
             'taipei', 'bangkok', 'kuala lumpur', 'manila', 'ho chi minh',
             'johor', 'asia', 'apac', 'southeast asia', 'china']
SKIP_TITLE = ['director', 'vp ', 'vice president', 'intern', 'internship', 
              'chief ', 'head of', 'counsel', 'legal', 'design', 'data scientist',
              'software engineer', 'backend', 'frontend', 'devops', 'sre',
              'accountant', 'analyst', 'recruiter', 'recruiting', 'hr ']

TARGET_ROLES = ['product manager', 'product owner', 'product', 'strategy', 
                'business operation', 'growth', 'program manager', 'general manager',
                'bizops', 'commercial', 'marketing manager', 'go-to-market']

for board_slug, company_name in COMPANIES.items():
    url = f'https://boards-api.greenhouse.io/v1/boards/{board_slug}/jobs?content=false'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        jobs = data.get('jobs', [])
        
        count = 0
        for j in jobs:
            jid = str(j.get('id', ''))
            title = j.get('title', '')
            loc = j.get('location', {}).get('name', '')
            posted = (j.get('posted_at') or '')[:10]
            updated = (j.get('updated_at') or '')[:10]
            job_url = f'https://boards.greenhouse.io/{board_slug}/jobs/{jid}'
            
            loc_lower = loc.lower()
            if not any(t in loc_lower for t in APAC_LOCS):
                continue
            
            title_lower = title.lower()
            if any(s in title_lower for s in SKIP_TITLE):
                continue
            if not any(r in title_lower for r in TARGET_ROLES):
                continue
            
            is_new = (company_name.lower(), title.lower().strip()) not in existing_titles and job_url not in existing_urls
            
            if is_new:
                new_jobs.append({
                    'company': company_name,
                    'title': title,
                    'location': loc,
                    'url': job_url,
                    'greenhouse_id': int(jid) if jid else None,
                    'posted': posted,
                    'updated': updated,
                    'scanned_date': TODAY,
                    'source': 'greenhouse_api',
                    'english_friendly': True,
                    'category': 'product',
                    'grade': 'A-1'
                })
                count += 1
        
        print(f'{company_name}: {len(jobs)} total, {count} new APAC matches')
    except Exception as e:
        print(f'{company_name}: ERROR - {e}')

print(f'\n=== All new Greenhouse jobs: {len(new_jobs)} ===')
for j in new_jobs:
    print(f'  NEW: {j["company"]} | {j["title"]} | {j["location"]} | {j["url"]}')

with open('/tmp/new_greenhouse_all.json', 'w') as f:
    json.dump(new_jobs, f, ensure_ascii=False, indent=2)
