#!/usr/bin/env python3
"""Try alternative data sources for job scanning."""
import json, urllib.request, urllib.parse, ssl, re, xml.etree.ElementTree as ET

ssl._create_default_https_context = ssl._create_unverified_context

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

all_new = []

# === 1. Try Greenhouse with different board IDs ===
print("=== Greenhouse Boards (trying variations) ===")
# From existing DB, we know these boards work: affirm, agoda, okx, stripe, airwallex
# Try with job-boards subdomain
boards_to_try = [
    ('affirm', 'https://boards-api.greenhouse.io/v1/boards/affirm/jobs'),
    ('agoda', 'https://boards-api.greenhouse.io/v1/boards/agoda/jobs'),
    ('okx', 'https://boards-api.greenhouse.io/v1/boards/okx/jobs'),
    ('stripe', 'https://boards-api.greenhouse.io/v1/boards/stripe/jobs'),
    ('airwallex', 'https://boards-api.greenhouse.io/v1/boards/airwallex/jobs'),
]

for board_name, url in boards_to_try:
    try:
        text = fetch_url(url)
        data = json.loads(text)
        jobs = data.get('jobs', [])
        print(f"  {board_name}: {len(jobs)} jobs")
        
        # Filter for relevant roles
        for j in jobs:
            title = j.get('title', '')
            loc = j.get('location', {}).get('name', '') if j.get('location') else ''
            tl = title.lower()
            ll = loc.lower()
            
            # Skip unwanted roles
            if any(k in tl for k in ['intern', 'internship', 'staff engineer', 'software engineer',
                                      'data scientist', 'devops', 'sre', 'ux designer', 'designer',
                                      'recruiter', 'recruiting', 'talent acquisition', 'accountant',
                                      'legal counsel', 'paralegal', 'receptionist', 'admin assistant']):
                continue
            if any(k in tl for k in ['vice president', 'svp', 'evp', 'chief ', 'cfo', 'cto', 'ceo', 'coo']):
                continue
            
            # Check title relevance
            title_match = any(k in tl for k in ['product manager', 'strategy', 'growth', 'gm', 'head of', 
                                                'bizops', 'business operations', 'commercial', 'business development',
                                                'cross-border', 'marketplace', 'fintech', 'payments', 'platform',
                                                'director', 'lead', 'chief of staff', 'go-to-market', 'gtm',
                                                'expansion', 'partnerships'])
            # Check location relevance
            loc_match = any(k in ll for k in ['shenzhen', 'hong kong', 'singapore', 'shanghai', 'guangzhou',
                                              'asia', 'apac', 'greater china', 'china', 'sea', 'southeast'])
            
            if title_match and loc_match:
                job_url = f"https://job-boards.greenhouse.io/{board_name}/jobs/{j.get('id', '')}"
                all_new.append({
                    'company': board_name.title(),
                    'title': title,
                    'location': loc,
                    'url': job_url,
                    'source': 'greenhouse_api',
                    'posted': j.get('updated_at', '')
                })
                print(f"    ✅ {title} | {loc}")
    except Exception as e:
        print(f"  {board_name}: Error - {e}")

# === 2. Try Lever API ===
print("\n=== Lever API ===")
lever_companies = ['okx', 'airwallex', 'stripe', 'shopee']
for company in lever_companies:
    try:
        url = f'https://api.lever.co/v0/postings/{company}?mode=json'
        text = fetch_url(url)
        data = json.loads(text)
        print(f"  {company}: {len(data)} jobs")
        
        for j in data:
            title = j.get('text', '')
            loc = j.get('categories', {}).get('location', '') if j.get('categories') else ''
            tl = title.lower()
            ll = loc.lower()
            
            if any(k in tl for k in ['product manager', 'strategy', 'growth', 'head of', 'bizops', 'business operations',
                                      'commercial', 'business development', 'cross-border', 'marketplace', 'fintech',
                                      'payments', 'platform', 'director', 'lead', 'go-to-market', 'gtm']):
                if any(k in ll for k in ['shenzhen', 'hong kong', 'singapore', 'shanghai', 'guangzhou', 'asia', 'apac']):
                    if not any(k in tl for k in ['intern', 'director', 'vp ', 'vice president']):
                        job_url = j.get('hostedUrl', '')
                        all_new.append({
                            'company': company.title(),
                            'title': title,
                            'location': loc,
                            'url': job_url,
                            'source': 'lever_api'
                        })
                        print(f"    ✅ {title} | {loc}")
    except Exception as e:
        print(f"  {company}: Error - {e}")

# === 3. Try Ashby API ===
print("\n=== Ashby API ===")
ashby_companies = ['anthropic', 'figma']
for company in ashby_companies:
    try:
        url = f'https://api.ashbyhq.com/posting-api/job-board/{company}'
        text = fetch_url(url)
        data = json.loads(text)
        jobs = data.get('jobPostings', [])
        print(f"  {company}: {len(jobs)} jobs")
        
        for j in jobs:
            title = j.get('title', '')
            loc = j.get('locationName', '') if j.get('locationName') else ''
            tl = title.lower()
            ll = loc.lower()
            
            if any(k in tl for k in ['product manager', 'strategy', 'growth', 'head of', 'bizops',
                                      'business operations', 'commercial', 'business development',
                                      'cross-border', 'marketplace', 'fintech', 'payments', 'platform']):
                if any(k in ll for k in ['shenzhen', 'hong kong', 'singapore', 'shanghai', 'guangzhou', 'asia', 'apac', 'remote']):
                    if not any(k in tl for k in ['intern', 'director', 'vp ', 'vice president', 'staff engineer']):
                        job_url = j.get('jobUrl', '')
                        all_new.append({
                            'company': company.title(),
                            'title': title,
                            'location': loc,
                            'url': job_url,
                            'source': 'ashby_api'
                        })
                        print(f"    ✅ {title} | {loc}")
    except Exception as e:
        print(f"  {company}: Error - {e}")

print(f"\n=== TOTAL NEW JOBS FOUND: {len(all_new)} ===")
for j in all_new:
    print(f"  {j['company']} | {j['title']} | {j['location']}")

# Save results
with open('/tmp/altscan_results.json', 'w') as f:
    json.dump(all_new, f, ensure_ascii=False, indent=2)
