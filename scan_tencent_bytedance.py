#!/usr/bin/env python3
"""Scan Tencent and ByteDance career sites."""
import json, urllib.request
from datetime import datetime

TODAY = datetime.now().strftime('%Y-%m-%d')

# Load existing
with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json') as f:
    existing = json.load(f)
existing_urls = {j.get('url', '') for j in existing}

new_jobs = []

# Tencent API - search for strategy/PM roles
print("=== Tencent Careers ===")
try:
    tencent_url = 'https://careers.tencent.com/tencentcareer/api/post/Query?keyword=strategy&cityId=&categoryId=&industryId=&language=&area=Chn&subArea=&page=1&pageSize=20&language=en'
    req = urllib.request.Request(tencent_url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Referer': 'https://careers.tencent.com/'
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    
    jobs = data.get('Data', {}).get('Posts', [])
    total = data.get('Data', {}).get('Count', 0)
    print(f'Tencent strategy: {len(jobs)} results (total: {total})')
    
    for j in jobs:
        title = j.get('RecruitPostName', '')
        loc = j.get('LocationName', '')
        job_id = j.get('PostId', '')
        job_url = f'https://careers.tencent.com/en-us/position/{job_id}.html'
        
        title_lower = title.lower()
        if any(s in title_lower for s in ['intern', '实习', 'junior', '助理']):
            continue
        
        is_new = job_url not in existing_urls
        new_jobs.append({
            'company': 'Tencent',
            'title': title,
            'location': loc,
            'url': job_url,
            'source': 'tencent_careers',
            'scanned_date': TODAY,
            'is_new': is_new
        })
except Exception as e:
    print(f'Tencent: ERROR - {e}')

# Try product manager
try:
    tencent_pm_url = 'https://careers.tencent.com/tencentcareer/api/post/Query?keyword=product+manager&cityId=&categoryId=&industryId=&language=&area=Chn&subArea=&page=1&pageSize=20&language=en'
    req = urllib.request.Request(tencent_pm_url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Referer': 'https://careers.tencent.com/'
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    
    jobs = data.get('Data', {}).get('Posts', [])
    total = data.get('Data', {}).get('Count', 0)
    print(f'Tencent PM: {len(jobs)} results (total: {total})')
    
    for j in jobs:
        title = j.get('RecruitPostName', '')
        loc = j.get('LocationName', '')
        job_id = j.get('PostId', '')
        job_url = f'https://careers.tencent.com/en-us/position/{job_id}.html'
        
        title_lower = title.lower()
        if any(s in title_lower for s in ['intern', '实习', 'junior', '助理']):
            continue
        
        is_new = job_url not in existing_urls
        new_jobs.append({
            'company': 'Tencent',
            'title': title,
            'location': loc,
            'url': job_url,
            'source': 'tencent_careers',
            'scanned_date': TODAY,
            'is_new': is_new
        })
except Exception as e:
    print(f'Tencent PM: ERROR - {e}')

# ByteDance API
print("\n=== ByteDance Careers ===")
try:
    bytedance_url = 'https://jobs.bytedance.com/api/v1/search/job/posts?keyword=产品经理&location=&limit=20&offset=0&job_category_id=&recruit_type=4'
    req = urllib.request.Request(bytedance_url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Referer': 'https://jobs.bytedance.com/'
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    
    jobs = data.get('data', {}).get('job_post_list', [])
    total = data.get('data', {}).get('count', 0)
    print(f'ByteDance PM: {len(jobs)} results (total: {total})')
    
    for j in jobs:
        title = j.get('title', '')
        loc = j.get('location', {}).get('name', '')
        job_id = j.get('id', '')
        job_url = f'https://jobs.bytedance.com/experienced/position/{job_id}/detail'
        
        title_lower = title.lower()
        if any(s in title_lower for s in ['intern', '实习', 'junior', '助理']):
            continue
        
        is_new = job_url not in existing_urls
        new_jobs.append({
            'company': 'ByteDance',
            'title': title,
            'location': loc,
            'url': job_url,
            'source': 'bytedance_careers',
            'scanned_date': TODAY,
            'is_new': is_new
        })
except Exception as e:
    print(f'ByteDance: ERROR - {e}')

print(f'\n--- Summary ---')
actual_new = [j for j in new_jobs if j['is_new']]
print(f'Total results: {len(new_jobs)}')
print(f'NEW (not in DB): {len(actual_new)}')
for j in actual_new[:20]:
    print(f'  NEW: {j["company"]} | {j["title"]} | {j["location"]} | {j["url"][:80]}')

with open('/tmp/new_tencent_bytedance_jobs.json', 'w') as f:
    json.dump(new_jobs, f, ensure_ascii=False, indent=2)
