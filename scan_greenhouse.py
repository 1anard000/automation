#!/usr/bin/env python3
"""Scan Greenhouse boards API for target companies."""
import json
import urllib.request
from datetime import datetime

with open('/Users/iancolrick/.openclaw/workspace/existing_urls.json') as f:
    existing_urls = set(json.load(f))

companies = {
    'adyen': 'Adyen',
    'agoda': 'Agoda',
    'okx': 'OKX',
    'stripe': 'Stripe',
    'coupang': 'Coupang',
    'mercury': 'Mercury',
    'vercel': 'Vercel',
    'figma': 'Figma',
    'anthropic': 'Anthropic',
    'coinbase': 'Coinbase',
    'flexport': 'Flexport',
    'reddit': 'Reddit',
    'airbnb': 'Airbnb',
    'gitlab': 'GitLab',
    'affirm': 'Affirm',
    'bybit': 'Bybit',
    'chime': 'Chime',
    'xendit': 'Xendit',
    'tripadvisor': 'TripAdvisor',
}

keywords = [
    'product manager', 'product lead', 'senior product',
    'strategy', 'strategic',
    'bizops', 'business operations',
    'growth', 'general manager',
    'senior manager', 'director of product',
    'head of product', 'head of growth', 'head of strategy',
    'commercial manager', 'gm ',
]

target_locations = ['shenzhen', 'hong kong', 'hk', 'singapore', 'guangzhou', 'shanghai', 'remote', 'asia', 'apac', 'greater china', 'bangkok', 'tokyo']

skip_words = ['director', 'vp ', 'vice president', 'intern', 'internship', 'legal', 'counsel', 'recruiter', 'talent']

new_jobs = []
scanned = 0
errors = []

for company_slug, company_name in companies.items():
    try:
        url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        jobs = data.get('jobs', [])
        scanned += 1
        print(f"[{scanned}/{len(companies)}] {company_name}: {len(jobs)} jobs", flush=True)
        
        for j in jobs:
            title = j.get('title', '')
            title_lower = title.lower()
            loc = j.get('location', {}).get('name', '').lower()
            abs_url = j.get('absolute_url', '')
            
            if abs_url.rstrip('/') in existing_urls:
                continue
            
            title_match = any(k in title_lower for k in keywords)
            loc_match = any(l in loc for l in target_locations) or loc == ''
            
            if title_match and loc_match:
                if any(s in title_lower for s in skip_words):
                    continue
                
                new_jobs.append({
                    'title': title,
                    'company': company_name,
                    'location': j.get('location', {}).get('name', ''),
                    'url': abs_url,
                    'source': 'greenhouse_api',
                    'posted': j.get('first_published', ''),
                    'updated': j.get('updated_at', ''),
                    'scanned_date': datetime.now().strftime('%Y-%m-%d'),
                })
    except Exception as e:
        errors.append(f"{company_name}: {e}")

print(f"\n=== RESULTS ===")
print(f"Scanned: {scanned}/{len(companies)}")
print(f"New jobs found: {len(new_jobs)}")
print(f"Errors: {len(errors)}")
for err in errors:
    print(f"  ERR: {err}")

for j in new_jobs:
    print(f"\n📌 {j['title']} @ {j['company']}")
    print(f"   📍 {j['location']}")
    print(f"   🔗 {j['url']}")
    print(f"   📅 Posted: {j['posted'][:10] if j['posted'] else 'unknown'}")

with open('/Users/iancolrick/.openclaw/workspace/new_greenhouse_jobs.json', 'w') as f:
    json.dump(new_jobs, f, indent=2)
