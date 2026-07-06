#!/usr/bin/env python3
"""Add new jobs to the database."""
import json
import os
from datetime import datetime

DB_PATH = '/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json'
NEW_JOBS_PATH = '/Users/iancolrick/.openclaw/workspace/tmp_new_jobs.json'

# Load existing database
with open(DB_PATH, 'r') as f:
    existing_jobs = json.load(f)

existing_urls = set(j.get('url', '') for j in existing_jobs)

# Load new jobs
with open(NEW_JOBS_PATH, 'r') as f:
    new_jobs = json.load(f)

# Filter to only truly new jobs (not in database)
truly_new = [j for j in new_jobs if j['url'] not in existing_urls]

print(f"Existing jobs: {len(existing_jobs)}")
print(f"New jobs to add: {len(truly_new)}")

# Prepare jobs for database
today = datetime.now().strftime('%Y-%m-%d')
added_jobs = []

for job in truly_new[:50]:  # Add top 50 to keep database manageable
    db_entry = {
        'title': job['title'],
        'company': job['company'],
        'location': job['location'],
        'url': job['url'],
        'source': 'greenhouse',
        'scanned_date': today,
        'grade': 'A-1' if job.get('quality_score', 0) >= 10 else 'B',
        'english_friendly': job['company'] in ['Stripe', 'Agoda', 'Airwallex', 'OKX'],
        'quality_score': job.get('quality_score', 0),
        'city_normalized': job['location'].split(',')[0] if ',' in job['location'] else job['location']
    }
    added_jobs.append(db_entry)

# Add to database
existing_jobs.extend(added_jobs)

# Save updated database
with open(DB_PATH, 'w') as f:
    json.dump(existing_jobs, f, indent=2, ensure_ascii=False)

print(f"Added {len(added_jobs)} new jobs to database")
print(f"Total jobs now: {len(existing_jobs)}")

# Print summary of what was added
print("\nNew jobs added:")
for j in added_jobs:
    print(f"  - {j['title']} @ {j['company']} | {j['location']}")
