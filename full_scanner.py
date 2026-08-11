#!/usr/bin/env python3
"""Comprehensive job scanner - Greenhouse + Tencent careers API."""
import json
import urllib.request
import urllib.parse
import os

DB_PATH = os.path.expanduser("~/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json")

with open(DB_PATH) as f:
    existing = json.load(f)

existing_urls = set()
existing_keys = set()
for j in existing:
    if j.get('url'):
        existing_urls.add(j['url'].strip().lower().rstrip('/'))
    if j.get('title') and j.get('company'):
        existing_keys.add((j['title'].strip().lower(), j['company'].strip().lower()))

print(f"Existing jobs: {len(existing)}")

APAC_KEYWORDS = ['hong kong', 'shenzhen', 'singapore', 'shanghai', 'guangzhou', 'apac', 'asia', 'taipei', 'tokyo', 'seoul', 'malaysia', 'kuala lumpur', 'bangkok', 'jakarta']
ROLE_KEYWORDS = ['product', 'strategy', 'growth', 'business', 'operations', 'gm', 'lead', 'manager', 'director', 'bd', 'partnership', 'commercial']
SKIP_TITLE_KEYWORDS = [
    'director', 'vp ', 'vice president', 'chief',
    'compliance', 'legal', 'counsel', 'audit', 'security',
    'payroll', 'compensation', 'employee relation',
    'real estate', 'procurement', 'logistics', 'loss prevention',
    'information security', 'infrastructure procurement',
    'customer service', 'contact center',
    'data security', 'privacy',
    'staff engineer', 'backend engineer', 'frontend engineer', 'blockchain engineer',
    'test development', 'sre ', 'techops', 'hrbp',
    'linehaul', 'robotics', 'computer vision',
    'intern', 'internship', 'junior',
]

TARGET_LOCATIONS = ['hong kong', 'shenzhen', 'singapore', 'shanghai', 'guangzhou', 'taipei', 'apac']

new_jobs = []

def is_relevant(title, location):
    title_lower = title.lower()
    loc_lower = location.lower()
    if any(k in title_lower for k in SKIP_TITLE_KEYWORDS):
        return False
    if not any(k in loc_lower for k in TARGET_LOCATIONS):
        return False
    if any(k in title_lower for k in ['vp', 'vice president', 'chief']):
        return False
    return True

def is_duplicate(title, company, url):
    check_url = url.strip().lower().rstrip('/')
    check_key = (title.strip().lower(), company.strip().lower())
    return check_url in existing_urls or check_key in existing_keys

# === GREENHOUSE ===
greenhouse_companies = ['okx', 'airwallex', 'coupang', 'figma', 'bybit']
for company in greenhouse_companies:
    api_url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
    print(f"\n--- {company} ---")
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        jobs = data.get('jobs', [])
        print(f"  Total: {len(jobs)}")
        count = 0
        for j in jobs:
            loc = j.get('location', {}).get('name', '')
            title = j.get('title', '')
            abs_url = j.get('absolute_url', '')
            if not is_relevant(title, loc):
                continue
            if is_duplicate(title, company, abs_url):
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
            count += 1
        print(f"  New relevant: {count}")
    except Exception as e:
        print(f"  Error: {e}")

# === TENCENT CAREERS ===
tencent_queries = [
    ('product', 'Shenzhen'),
    ('strategy', 'Shenzhen'),
    ('growth', 'Shenzhen'),
    ('business', 'Shenzhen'),
    ('product', 'Singapore'),
    ('strategy', 'Singapore'),
    ('product', 'Hong Kong'),
    ('strategy', 'Hong Kong'),
    ('product', 'Shanghai'),
]
print(f"\n--- Tencent Careers ---")
for keyword, location in tencent_queries:
    url = f"https://careers.tencent.com/tencentcareer/api/post/Query?keyword={urllib.parse.quote(keyword)}&location={urllib.parse.quote(location)}&pageSize=20&pageIndex=0&language=en-us"
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://careers.tencent.com/'
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        posts = data.get('Data', {}).get('Posts', [])
        count = 0
        for p in posts:
            title = p.get('RecruitPostName', '')
            loc = p.get('LocationName', '')
            post_id = p.get('PostID', '')
            category = p.get('CategoryName', '')
            # Construct URL
            job_url = f"https://careers.tencent.com/en-us/search.html?keyword={urllib.parse.quote(title)}"
            
            if not is_relevant(title, loc):
                continue
            if is_duplicate(title, 'Tencent', job_url):
                continue
            
            new_jobs.append({
                'title': title,
                'company': 'Tencent',
                'location': loc,
                'salary': '',
                'url': job_url,
                'source': 'tencent_careers',
                'scanned_date': '2026-08-11',
                'en_title': title,
                'english_friendly': True,
                'category': 'tech_giant',
                'company_type': 'tech_giant',
                'funding_stage': 'established',
                'grade': 'A-2',
                'quality_tier': 'A',
                'quality_score': 75,
                'date': '2026-08-11',
                'date_source': 'scanned_today'
            })
            count += 1
        if posts:
            print(f"  {keyword} {location}: {len(posts)} found, {count} new")
    except Exception as e:
        print(f"  Error {keyword} {location}: {e}")

print(f"\n\n=== TOTAL NEW JOBS: {len(new_jobs)} ===")
for j in new_jobs:
    print(f"\n📌 {j['title']} @ {j['company']}")
    print(f"📍 {j['location']}")
    print(f"🔗 {j['url']}")

# Save
output_path = os.path.expanduser("~/.openclaw/workspace/new_jobs_final.json")
with open(output_path, 'w') as f:
    json.dump(new_jobs, f, indent=2, ensure_ascii=False)
print(f"\nSaved to {output_path}")
