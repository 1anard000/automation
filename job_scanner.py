#!/usr/bin/env python3
"""Job scanner - fetches from Greenhouse APIs and deduplicates against existing DB."""
import json
import urllib.request
import os
import sys

DB_PATH = os.path.expanduser("~/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json")

# Load existing jobs for dedup
with open(DB_PATH) as f:
    existing = json.load(f)

existing_urls = set()
existing_keys = set()
for j in existing:
    if j.get('url'):
        existing_urls.add(j['url'].strip().lower().rstrip('/'))
    if j.get('title') and j.get('company'):
        existing_keys.add((j['title'].strip().lower(), j['company'].strip().lower()))

print(f"Existing jobs: {len(existing)}, URLs: {len(existing_urls)}, Title+Company keys: {len(existing_keys)}")

APAC_KEYWORDS = ['hong kong', 'shenzhen', 'singapore', 'shanghai', 'guangzhou', 'apac', 'asia', 'taipei', 'tokyo', 'seoul', 'malaysia', 'kuala lumpur', 'bangkok', 'jakarta']
ROLE_KEYWORDS = ['product', 'strategy', 'growth', 'business', 'operations', 'gm', 'lead', 'manager', 'director', 'bd', 'partnership', 'commercial']
SKIP_KEYWORDS = ['intern', 'internship', 'junior', 'intern']

greenhouse_companies = ['okx', 'stripe', 'airwallex', 'coupang', 'bytedance']

new_jobs = []

for company in greenhouse_companies:
    url = f"https://boards-api.greenhouse.io/v1/jobs/{company}?content=true"
    print(f"\n--- Fetching {company} ---")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        jobs = data.get('jobs', [])
        print(f"  Total jobs: {len(jobs)}")
        
        for j in jobs:
            loc = j.get('location', {}).get('name', '')
            title = j.get('title', '')
            jid = j.get('id', '')
            abs_url = j.get('absolute_url', '')
            loc_lower = loc.lower()
            title_lower = title.lower()
            
            # Skip if location not in APAC
            if not any(k in loc_lower for k in APAC_KEYWORDS):
                continue
            
            # Skip if not a relevant role
            if not any(k in title_lower for k in ROLE_KEYWORDS):
                continue
            
            # Skip interns
            if any(k in title_lower for k in SKIP_KEYWORDS):
                continue
            
            # Skip Director/VP roles
            if any(k in title_lower for k in ['vp', 'vice president', 'chief']):
                continue
                
            # Dedup by URL
            check_url = abs_url.strip().lower().rstrip('/')
            check_key = (title.strip().lower(), company.lower())
            
            if check_url in existing_urls or check_key in existing_keys:
                continue
            
            new_jobs.append({
                'title': title,
                'company': company.title(),
                'location': loc,
                'salary': '',
                'url': abs_url,
                'source': 'greenhouse_api',
                'scanned_date': '2026-08-11',
                'en_title': title,
                'english_friendly': True,
                'category': 'product_management',
                'grade': 'A-2',
                'quality_tier': 'A',
                'quality_score': 75,
                'date': '2026-08-11',
                'date_source': 'scanned_today'
            })
            
    except Exception as e:
        print(f"  Error fetching {company}: {e}")

print(f"\n\n=== NEW JOBS FOUND: {len(new_jobs)} ===")
for j in new_jobs:
    print(f"\n📌 {j['title']} @ {j['company']}")
    print(f"📍 {j['location']}")
    print(f"🔗 {j['url']}")

# Save new jobs to temp file for later merge
output_path = os.path.expanduser("~/.openclaw/workspace/new_jobs_temp.json")
with open(output_path, 'w') as f:
    json.dump(new_jobs, f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(new_jobs)} new jobs to {output_path}")
