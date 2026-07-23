import json
import urllib.request

# Load existing jobs
with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json', 'r') as f:
    existing = json.load(f)

# Load filtered new jobs
with open('/Users/iancolrick/.openclaw/workspace/new_jobs_filtered.json', 'r') as f:
    new_jobs = json.load(f)

# Also load all greenhouse new jobs for the full merge
with open('/Users/iancolrick/.openclaw/workspace/new_jobs_greenhouse.json', 'r') as f:
    all_greenhouse_new = json.load(f)

# Create URL lookup
existing_urls = set()
for j in existing:
    existing_urls.add(j.get('url', ''))

# Also check by job ID
existing_ids = set()
for url in existing_urls:
    # Extract job ID from URL
    import re
    ids = re.findall(r'/jobs/(\d+)', url)
    for id_val in ids:
        existing_ids.add(id_val)

print(f"Existing jobs: {len(existing)}")
print(f"Existing URLs: {len(existing_urls)}")

# Filter new jobs to only truly new ones
truly_new = []
for j in all_greenhouse_new:
    # Check URL
    if j['url'] in existing_urls:
        continue
    
    # Check job ID
    import re
    ids = re.findall(r'/jobs/(\d+)', j['url'])
    id_match = False
    for id_val in ids:
        if id_val in existing_ids:
            id_match = True
            break
    if id_match:
        continue
    
    truly_new.append(j)

print(f"Truly new jobs (not in database): {len(truly_new)}")

# Filter to top-tier roles
priority_locations = ['hong kong', 'shenzhen', 'singapore', 'shanghai', 'guangzhou']
exclude_keywords = [
    'engineer', 'designer', 'data scientist', 'lawyer', 'counsel',
    'compliance', 'hr', 'human resource', 'accounting', 'audit',
    'legal', 'tax', 'operations manager', 'talent',
    'communications', 'marketing manager', 'compensation'
]

top_new = []
for j in truly_new:
    title_lower = j['title'].lower()
    loc_lower = j['location'].lower()
    
    # Skip if title contains excluded keywords
    if any(k in title_lower for k in exclude_keywords):
        continue
    
    # Calculate priority score
    score = 0
    
    # Location score
    for i, loc in enumerate(priority_locations):
        if loc in loc_lower:
            score += (5 - i) * 10
            break
    
    # Role type score
    if 'product manager' in title_lower or 'product director' in title_lower:
        score += 30
    if 'strategy' in title_lower:
        score += 25
    if 'growth' in title_lower:
        score += 20
    if 'business development' in title_lower or 'partnership' in title_lower:
        score += 15
    if 'commercial' in title_lower:
        score += 15
    if 'principal' in title_lower or 'staff' in title_lower:
        score += 10
    if 'senior' in title_lower:
        score += 5
    
    j['priority_score'] = score
    top_new.append(j)

# Sort by score
top_new.sort(key=lambda x: x['priority_score'], reverse=True)

print(f"\nTop new jobs to add ({len(top_new)}):")
for j in top_new[:20]:
    print(f"  [{j['priority_score']}] {j['company']} | {j['title']} | {j['location']}")
    print(f"       {j['url']}")

# Add to existing database
added = 0
for j in top_new:
    # Skip Director/VP
    title_lower = j['title'].lower()
    if any(k in title_lower for k in ['vice president', 'managing director']):
        continue
    
    # Add the job
    existing.append({
        'title': j['title'],
        'company': j['company'],
        'location': j['location'],
        'salary': j.get('salary', 'Not listed'),
        'url': j['url'],
        'source': j.get('source', 'greenhouse_api'),
        'role_type': j.get('role_type', 'Product Management'),
        'scanned_date': '2026-07-23',
        'posted_date': j.get('posted_date', '')
    })
    added += 1

print(f"\nAdded {added} new jobs to database")
print(f"Total jobs now: {len(existing)}")

# Save updated database
with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json', 'w') as f:
    json.dump(existing, f, indent=2, ensure_ascii=False)

print("Database saved!")
