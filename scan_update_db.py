#!/usr/bin/env python3
"""Filter and add new jobs to the database."""
import json
from datetime import date

# Load existing database
db_path = '/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json'
with open(db_path) as f:
    existing = json.load(f)

existing_urls = {j.get('url', '') for j in existing}
existing_keys = {(j.get('title', '').strip(), j.get('company', '').strip()) for j in existing}

# Load new greenhouse jobs
with open('/tmp/new_greenhouse_jobs.json') as f:
    raw_new = json.load(f)

# Filter for target profile
# Skip: engineering roles, sales, support, compliance, junior, director/VP
skip_title_kw = [
    'engineer', 'software engineer', 'backend', 'frontend', 'full stack',
    'staff ', 'senior staff', 'architect', 'developer',
    'account executive', 'sales', 'support specialist', 'advisor',
    'compliance', 'junior', 'intern', 'internship',
    'director', 'vp ', 'vice president',
]
# Include: product manager, product owner, growth (non-eng), strategy, bizops, lead (non-eng)
include_title_kw = [
    'product manager', 'product owner', 'product lead',
    'growth manager', 'growth lead',
    'strategy', 'bizops', 'business operations',
    'gm', 'general manager', 'head of',
    'partnerships', 'expansion',
]

today = str(date.today())
new_added = []

for job in raw_new:
    title = job.get('title', '').strip()
    title_lower = title.lower()
    url = job.get('url', '')
    company = job.get('company', '')
    
    # Already in DB?
    if url in existing_urls:
        continue
    key = (title.strip(), company.strip())
    if key in existing_keys:
        continue
    
    # Skip by title
    skip = False
    for kw in skip_title_kw:
        if kw in title_lower:
            skip = True
            break
    if skip:
        continue
    
    # Must match include keywords
    include = False
    for kw in include_title_kw:
        if kw in title_lower:
            include = True
            break
    if not include:
        continue
    
    # Grade the job
    location = job.get('location', '')
    loc_lower = location.lower()
    
    if 'hong kong' in loc_lower or 'hk' in loc_lower:
        grade = 'A-2'
        quality_tier = 'B'
    elif 'shenzhen' in loc_lower:
        grade = 'A-1'
        quality_tier = 'A'
    elif 'singapore' in loc_lower:
        grade = 'A-2'
        quality_tier = 'B'
    elif 'shanghai' in loc_lower:
        grade = 'A-2'
        quality_tier = 'B'
    elif 'guangzhou' in loc_lower:
        grade = 'A-2'
        quality_tier = 'B'
    else:
        grade = 'B'
        quality_tier = 'C'
    
    enriched = {
        'title': title,
        'company': company,
        'location': location,
        'salary': job.get('salary', 'Not listed'),
        'url': url,
        'source': 'greenhouse_api',
        'role_type': job.get('role_type', ''),
        'description': job.get('description', '')[:500],
        'grade': grade,
        'quality_tier': quality_tier,
        'english_friendly': True,
        'scanned_date': today,
        'en_title': title,
        'summary': f'{title} at {company} in {location}',
    }
    new_added.append(enriched)
    print(f'ADD: {title} @ {company} | {location} | {url} | Grade: {grade}')

print(f'\nTotal qualifying new jobs to add: {len(new_added)}')

# Add to database
if new_added:
    existing.extend(new_added)
    with open(db_path, 'w') as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    print(f'Database updated: {len(existing)} total jobs')
else:
    print('No new qualifying jobs to add.')

# Output summary for report
with open('/tmp/scan_summary.json', 'w') as f:
    json.dump({
        'total_greenhouse_raw': len(raw_new),
        'qualifying_added': len(new_added),
        'jobs_added': [{'title': j['title'], 'company': j['company'], 'location': j['location'], 'url': j['url'], 'grade': j['grade']} for j in new_added],
        'total_db': len(existing),
    }, f, indent=2, ensure_ascii=False)
