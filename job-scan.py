#!/usr/bin/env python3
"""Scan Greenhouse APIs for new jobs matching the target profile."""
import json
import urllib.request
import re
from datetime import datetime

# Target keywords for matching
PM_KEYWORDS = [
    'product manager', 'product management', 'senior product',
    'growth product', 'strategy', 'strategic', 'business operations',
    'bizops', 'growth', 'general manager', 'partnerships',
    'business development', 'cross-border', 'marketplace', 'fintech',
    'ai product', 'platform', 'commercial', 'senior manager',
    'lead product', 'head of product'
]

# Exclude titles
EXCLUDE_KEYWORDS = ['intern', 'internship', 'director', 'vp ', 'vice president', 'managing director', 'staff']

# Location priority
GOOD_LOCATIONS = ['shenzhen', 'hong kong', 'hk', 'guangzhou', 'shanghai', 'singapore', 'kuala lumpur', 'taipei', 'apac', 'remote', 'asia', 'japan', 'tokyo', 'taiwan']

# Load existing jobs
with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json') as f:
    existing = json.load(f)

existing_urls = {j.get('url', '') for j in existing}
existing_titles = {(j.get('company', '').lower(), j.get('title', '').lower()) for j in existing}

print(f"Existing jobs in DB: {len(existing)}")

# Companies to scan via Greenhouse API (correct URL format)
COMPANIES = {
    'okx': 'OKX',
    'stripe': 'Stripe',
    'bybit': 'Bybit',
    'coupang': 'Coupang',
    'agoda': 'Agoda',
}

new_jobs = []

for company_slug, company_name in COMPANIES.items():
    url = f'https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"ERROR fetching {company_name}: {e}")
        continue

    jobs = data.get('jobs', [])
    print(f"\n{company_name}: {len(jobs)} total jobs")

    for j in jobs:
        title = j.get('title', '')
        loc = j.get('location', {}).get('name', '')
        job_url = j.get('absolute_url', '')

        # Skip if already in DB
        if job_url in existing_urls:
            continue
        if (company_name.lower(), title.lower()) in existing_titles:
            continue

        # Filter by keywords
        title_lower = title.lower()
        matched = any(kw in title_lower for kw in PM_KEYWORDS)
        if not matched:
            continue

        # Exclude low levels
        if any(ex in title_lower for ex in EXCLUDE_KEYWORDS):
            continue

        # Check location relevance
        loc_lower = loc.lower()
        loc_relevant = any(gl in loc_lower for gl in GOOD_LOCATIONS)
        if not loc_relevant:
            continue

        new_job = {
            'title': title,
            'company': company_name,
            'location': loc,
            'salary': 'Not listed',
            'url': job_url,
            'source': 'greenhouse_api',
            'role_type': 'Product Management',
            'scanned_date': datetime.now().strftime('%Y-%m-%d'),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'posted': datetime.now().strftime('%Y-%m-%d'),
            'english_friendly': True,
            'category': 'greenhouse_scan',
            'quality_tier': 'A',
            'grade': 'A-2'
        }
        new_jobs.append(new_job)
        print(f"  NEW: [{loc}] {title}")
        print(f"    URL: {job_url}")

print(f"\n=== SUMMARY ===")
print(f"New jobs found: {len(new_jobs)}")
for j in new_jobs:
    print(f"  {j['title']} @ {j['company']} ({j['location']})")

# Save new jobs to temp file for later merging
with open('/tmp/new-jobs-scan.json', 'w') as f:
    json.dump(new_jobs, f, indent=2, ensure_ascii=False)

print(f"\nSaved to /tmp/new-jobs-scan.json")
