#!/usr/bin/env python3
"""Scan Greenhouse APIs for new jobs."""
import json, urllib.request, sys
from datetime import datetime

COMPANIES = ['okx', 'stripe', 'coupang']
TODAY = datetime.now().strftime('%Y-%m-%d')

# Load existing jobs for dedup
with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json') as f:
    existing = json.load(f)

existing_urls = {j.get('url', '') for j in existing}
existing_greenhouse_ids = set()
for j in existing:
    gid = j.get('greenhouse_id')
    if gid:
        existing_greenhouse_ids.add(str(gid))

new_jobs = []
all_jobs = []

for company in COMPANIES:
    url = f'https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=false'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        jobs = data.get('jobs', [])
        print(f'{company}: {len(jobs)} total jobs')
        
        for j in jobs:
            jid = str(j.get('id', ''))
            title = j.get('title', '')
            loc = j.get('location', {}).get('name', '')
            posted = (j.get('posted_at') or '')[:10]
            updated = (j.get('updated_at') or '')[:10]
            job_url = f'https://boards.greenhouse.io/{company}/jobs/{jid}'
            
            # Filter: target locations and roles
            loc_lower = loc.lower()
            target_locs = ['singapore', 'hong kong', 'shenzhen', 'shanghai', 'guangzhou', 
                          'remote', 'asia', 'apac', 'southeast asia', 'china', 'taiwan']
            if not any(t in loc_lower for t in target_locs):
                continue
            
            # Filter: target roles (PM/Strategy/BizOps/Growth)
            title_lower = title.lower()
            target_roles = ['product manager', 'product', 'strategy', 'business operation', 
                          'growth', 'program manager', 'general manager', 'bizops', 
                          'chief of staff', 'marketing manager', 'commercial']
            if not any(r in title_lower for r in target_roles):
                continue
            
            # Skip Director/VP
            skip_roles = ['director', 'vp ', 'vice president', 'intern', 'internship', 'chief ']
            if any(s in title_lower for s in skip_roles):
                continue
            
            is_new = jid not in existing_greenhouse_ids and job_url not in existing_urls
            
            all_jobs.append({
                'company': company.title(),
                'title': title,
                'location': loc,
                'url': job_url,
                'greenhouse_id': int(jid) if jid else None,
                'posted': posted,
                'updated': updated,
                'is_new': is_new,
                'scanned_date': TODAY,
                'source': 'greenhouse_api'
            })
            
            if is_new:
                new_jobs.append({
                    'company': company.title(),
                    'title': title,
                    'location': loc,
                    'url': job_url,
                    'greenhouse_id': int(jid) if jid else None,
                    'posted': posted,
                    'updated': updated,
                    'scanned_date': TODAY,
                    'source': 'greenhouse_api',
                    'english_friendly': True,
                    'category': 'product',
                    'grade': 'A-1'
                })
    except Exception as e:
        print(f'{company}: ERROR - {e}')

print(f'\n--- Summary ---')
print(f'Total matching jobs found: {len(all_jobs)}')
print(f'NEW jobs (not in DB): {len(new_jobs)}')
for j in new_jobs:
    print(f'  NEW: {j["company"]} | {j["title"]} | {j["location"]} | {j["url"]}')
    print(f'       posted={j["posted"]} updated={j["updated"]}')

# Save new jobs for later merging
with open('/tmp/new_greenhouse_jobs.json', 'w') as f:
    json.dump(new_jobs, f, ensure_ascii=False, indent=2)
