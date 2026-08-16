#!/usr/bin/env python3
"""Merge new jobs into the database and rebuild dashboard."""
import json, subprocess, sys
from datetime import datetime

TODAY = datetime.now().strftime('%Y-%m-%d')
DB_PATH = '/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json'

# Load existing
with open(DB_PATH) as f:
    existing = json.load(f)

existing_urls = {j.get('url', '') for j in existing}
existing_titles = set()
for j in existing:
    existing_titles.add((j.get('company', '').lower().strip(), j.get('title', '').lower().strip()))

print(f'Existing jobs: {len(existing)}')

# New jobs to add (filtered from Greenhouse scan)
new_jobs = [
    {
        "company": "OKX",
        "title": "AI Agent Product Expert (Middleware)",
        "location": "Hong Kong, Hong Kong SAR",
        "url": "https://boards.greenhouse.io/okx/jobs/7731745003",
        "greenhouse_id": 7731745003,
        "scanned_date": TODAY,
        "date_source": "from_scanned_date",
        "source": "greenhouse_api",
        "english_friendly": True,
        "category": "ai_product",
        "grade": "A-1",
        "city_normalized": "Hong Kong",
        "quality_score": 57,
        "quality_tier": "B",
        "description": "AI Agent Product Expert for Middleware at OKX in Hong Kong. Build and optimize AI agent middleware infrastructure for intelligent trading and automation workflows."
    },
    {
        "company": "OKX",
        "title": "Product Owner, Structured Products",
        "location": "Hong Kong, Hong Kong SAR",
        "url": "https://boards.greenhouse.io/okx/jobs/7793353003",
        "greenhouse_id": 7793353003,
        "scanned_date": TODAY,
        "date_source": "from_scanned_date",
        "source": "greenhouse_api",
        "english_friendly": True,
        "category": "product",
        "grade": "A-1",
        "city_normalized": "Hong Kong",
        "quality_score": 57,
        "quality_tier": "B",
        "description": "Product Owner for Structured Products at OKX in Hong Kong. Define product roadmap and strategy for structured financial products on the crypto exchange platform."
    },
    {
        "company": "OKX",
        "title": "Product Owner, Structured Products",
        "location": "Singapore, Singapore",
        "url": "https://boards.greenhouse.io/okx/jobs/7793352003",
        "greenhouse_id": 7793352003,
        "scanned_date": TODAY,
        "date_source": "from_scanned_date",
        "source": "greenhouse_api",
        "english_friendly": True,
        "category": "product",
        "grade": "A-1",
        "city_normalized": "Singapore",
        "quality_score": 57,
        "quality_tier": "B",
        "description": "Product Owner for Structured Products at OKX in Singapore. Own the product lifecycle for structured financial products."
    },
    {
        "company": "OKX",
        "title": "Product Design Manager",
        "location": "Singapore, Singapore",
        "url": "https://boards.greenhouse.io/okx/jobs/6246528003",
        "greenhouse_id": 6246528003,
        "scanned_date": TODAY,
        "date_source": "from_scanned_date",
        "source": "greenhouse_api",
        "english_friendly": True,
        "category": "product",
        "grade": "A-1",
        "city_normalized": "Singapore",
        "quality_score": 57,
        "quality_tier": "B",
        "description": "Product Design Manager at OKX in Singapore. Lead design strategy and UX for crypto exchange product features."
    },
    {
        "company": "Stripe",
        "title": "Enterprise Product Support Manager",
        "location": "Singapore",
        "url": "https://boards.greenhouse.io/stripe/jobs/7894387",
        "scanned_date": TODAY,
        "date_source": "from_scanned_date",
        "source": "greenhouse_api",
        "english_friendly": True,
        "category": "product",
        "grade": "A-1",
        "city_normalized": "Singapore",
        "quality_score": 57,
        "quality_tier": "B",
        "description": "Enterprise Product Support Manager at Stripe Singapore. Manage product support operations for enterprise clients across APAC."
    },
    {
        "company": "Coupang",
        "title": "Retail Onboarding Manager (Product Compliance Operation)",
        "location": "Taipei, Taiwan",
        "url": "https://boards.greenhouse.io/coupang/jobs/8023116",
        "greenhouse_id": 8023116,
        "scanned_date": TODAY,
        "date_source": "from_scanned_date",
        "source": "greenhouse_api",
        "english_friendly": True,
        "category": "product",
        "grade": "A-1",
        "city_normalized": "Taipei",
        "quality_score": 57,
        "quality_tier": "B",
        "description": "Retail Onboarding Manager at Coupang Taipei. Manage product compliance operations for retail merchant onboarding."
    },
]

# Add only truly new jobs
added = 0
for j in new_jobs:
    key = (j['company'].lower().strip(), j['title'].lower().strip())
    if key not in existing_titles and j['url'] not in existing_urls:
        existing.append(j)
        added += 1
        print(f'ADDED: {j["company"]} | {j["title"]} | {j["location"]}')
    else:
        print(f'SKIP (exists): {j["company"]} | {j["title"]}')

print(f'\nTotal added: {added}')
print(f'Total jobs now: {len(existing)}')

# Save updated database
with open(DB_PATH, 'w') as f:
    json.dump(existing, f, ensure_ascii=False, indent=2)
print(f'Saved to {DB_PATH}')

# Rebuild dashboard
print('\nRebuilding dashboard...')
result = subprocess.run(
    ['python3', '/Users/iancolrick/.openclaw/workspace/rebuild-dashboard.py'],
    cwd='/Users/iancolrick/.openclaw/workspace',
    capture_output=True, text=True, timeout=30
)
if result.returncode == 0:
    print(f'Dashboard rebuilt successfully')
    if result.stdout:
        print(result.stdout[:500])
else:
    print(f'Dashboard rebuild ERROR: {result.stderr[:500]}')

# Git commit and push
print('\nGit commit and push...')
for cmd in [
    ['git', 'add', 'OKComputer_职位搜索清单/jobs-all.json', 'dashboard.html'],
    ['git', 'commit', '-m', f'Job scan {TODAY}: +{added} new jobs from Greenhouse APIs'],
    ['git', 'push']
]:
    r = subprocess.run(cmd, cwd='/Users/iancolrick/.openclaw/workspace', capture_output=True, text=True)
    print(f'{" ".join(cmd[:3])}: {r.returncode}')
    if r.stdout:
        print(f'  {r.stdout.strip()[:200]}')
    if r.stderr:
        print(f'  {r.stderr.strip()[:200]}')
