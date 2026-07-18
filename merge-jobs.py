#!/usr/bin/env python3
"""Merge all scan results with existing database, find new jobs, and rebuild dashboard."""
import json, sys, os, re
from datetime import datetime
from collections import Counter
from difflib import SequenceMatcher

WORKSPACE = '/Users/iancolrick/.openclaw/workspace'
DB_PATH = os.path.join(WORKSPACE, 'OKComputer_职位搜索清单/jobs-all.json')

# Load existing database
with open(DB_PATH) as f:
    existing = json.load(f)

existing_urls = set()
existing_title_company = set()
for j in existing:
    if j.get('url'):
        existing_urls.add(j['url'].strip().rstrip('/'))
    # Also track title+company combos for dedup
    t = re.sub(r'\s+', ' ', j.get('title', '').lower().strip())
    c = j.get('company', '').lower().strip()
    existing_title_company.add(f"{t}|{c}")

print(f"Existing database: {len(existing)} jobs")

# Load all scan results
new_jobs = []
scan_files = [
    'greenhouse-scan.json',
    'tencent-scan.json'
]

for sf in scan_files:
    path = os.path.join(WORKSPACE, 'OKComputer_职位搜索清单', sf)
    if not os.path.exists(path):
        print(f"  ⚠️  {sf} not found, skipping")
        continue
    with open(path) as f:
        jobs = json.load(f)
    print(f"  {sf}: {len(jobs)} candidates")
    for j in jobs:
        url = j.get('url', '').strip().rstrip('/')
        t = re.sub(r'\s+', ' ', j.get('title', '').lower().strip())
        c = j.get('company', '').lower().strip()
        tc_key = f"{t}|{c}"
        
        # Skip if URL already in database
        if url and url in existing_urls:
            continue
        # Skip if title+company already in database
        if tc_key in existing_title_company:
            continue
        
        # Quality filter: skip low quality
        if j.get('quality_score', 0) < 60:
            continue
        
        # Skip Director/VP roles
        title_lower = j.get('title', '').lower()
        if any(k in title_lower for k in ['director', 'vp ', 'vice president']):
            continue
        
        # Skip interns
        if any(k in title_lower for k in ['intern', 'internship']):
            continue
        
        # Add enrichment
        j['quality_score'] = max(j.get('quality_score', 70), 75)
        j['quality_tier'] = 'A' if j['quality_score'] >= 85 else 'B'
        j['grade'] = j['quality_tier']
        j['posted'] = j.get('scanned_date', datetime.now().strftime('%Y-%m-%d'))
        
        new_jobs.append(j)
        existing_title_company.add(tc_key)
        if url:
            existing_urls.add(url)

print(f"\nNew jobs found: {len(new_jobs)}")
for j in new_jobs:
    print(f"  📌 {j['title']} @ {j['company']} | {j.get('location', '')} | {j.get('url', '')}")

# Add new jobs to database
if new_jobs:
    existing.extend(new_jobs)
    with open(DB_PATH, 'w') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Database updated: {len(existing)} total jobs")
else:
    print("\n✅ No new jobs to add")

# Save new jobs list for reporting
with open(os.path.join(WORKSPACE, 'OKComputer_职位搜索清单', 'new-jobs-this-scan.json'), 'w') as f:
    json.dump(new_jobs, f, ensure_ascii=False, indent=2)
