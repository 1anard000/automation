#!/usr/bin/env python3
"""Add top new jobs to the database."""
import json
from datetime import datetime

# Load existing jobs
with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json') as f:
    existing = json.load(f)

# Load top new jobs
with open('/Users/iancolrick/.openclaw/workspace/top_new_jobs.json') as f:
    new_jobs = json.load(f)

# Dedup by URL
existing_urls = set(j.get('url', '').rstrip('/') for j in existing)

added = 0
for j in new_jobs:
    url = j['url'].rstrip('/')
    if url in existing_urls:
        print(f"SKIP (dup): {j['title']} @ {j['company']}")
        continue
    
    # Create job entry
    entry = {
        'title': j['title'],
        'company': j['company'],
        'location': j['location'],
        'salary': 'Not listed',
        'url': j['url'],
        'source': j.get('source', 'greenhouse_api'),
        'role_type': 'Product Management' if 'product' in j['title'].lower() else 'Strategy',
        'grade': 'A' if j.get('score', 0) >= 16 else 'B',
        'posted_date': j.get('posted', ''),
        'scanned_date': datetime.now().strftime('%Y-%m-%d'),
        'discovered': datetime.now().strftime('%Y-%m-%d'),
        'en_title': j['title'],
        'summary': f"{j['title']} at {j['company']} in {j['location']}",
        'quality_score': j.get('score', 50) * 5,
        'quality_tier': 'A' if j.get('score', 0) >= 16 else 'B',
        'status': 'not_applied',
        'status_date': datetime.now().strftime('%Y-%m-%d'),
        'has_direct_link': True,
        'english_friendly': True,
    }
    
    existing.append(entry)
    existing_urls.add(url)
    added += 1
    print(f"✅ Added: {j['title']} @ {j['company']} ({j['location']})")

print(f"\n=== SUMMARY ===")
print(f"Added: {added} new jobs")
print(f"Skipped (dups): {len(new_jobs) - added}")
print(f"Total jobs now: {len(existing)}")

# Save updated database
with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json', 'w') as f:
    json.dump(existing, f, indent=2, ensure_ascii=False)

print("Database saved!")
