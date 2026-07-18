#!/usr/bin/env python3
"""Scan Tencent careers API."""
import json
import urllib.request
from datetime import datetime

with open('/Users/iancolrick/.openclaw/workspace/existing_urls.json') as f:
    existing_urls = set(json.load(f))

keywords = ['product manager', 'strategy', 'bizops', 'business operations', 'growth', 'general manager', 'senior manager', 'head of', 'lead', 'commercial']
skip_words = ['director', 'vp ', 'intern', 'internship', 'legal', 'counsel', 'recruiter']

new_jobs = []

for keyword in ['strategy', 'product manager', 'growth']:
    try:
        url = f"https://careers.tencent.com/tencentcareer/api/post/Query?timestamp=1721311200&countryId=&cityId=&bgIds=&parentId=&瓜Id=&keyword={keyword}&language=0&area=cn"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        jobs = data.get('Data', {}).get('Posts', [])
        print(f"Tencent '{keyword}': {len(jobs)} jobs", flush=True)
        
        for j in jobs:
            title = j.get('RecruitPostName', '')
            title_lower = title.lower()
            loc = j.get('LocationName', '').lower()
            post_url = j.get('PostURL', '')
            
            if not post_url:
                continue
            if post_url in existing_urls:
                continue
            
            title_match = any(k in title_lower for k in keywords)
            loc_match = any(l in loc for l in ['shenzhen', 'hong kong', 'shanghai', 'guangzhou', 'singapore', 'tianjin', '成都'])
            
            if title_match and loc_match:
                if any(s in title_lower for s in skip_words):
                    continue
                new_jobs.append({
                    'title': title,
                    'company': 'Tencent',
                    'location': j.get('LocationName', ''),
                    'url': post_url,
                    'source': 'tencent_api',
                    'posted': j.get('CreateTime', ''),
                    'scanned_date': datetime.now().strftime('%Y-%m-%d'),
                })
    except Exception as e:
        print(f"Tencent '{keyword}' error: {e}", flush=True)

# Also scan ByteDance
for keyword in ['产品经理', 'strategy', 'growth']:
    try:
        url = f"https://jobs.bytedance.com/api/v1/search/position?keyword={keyword}&limit=20&offset=0&job_category=1&recruit_type=4&city_code=7611"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        jobs = data.get('data', {}).get('job_post_list', [])
        print(f"ByteDance '{keyword}': {len(jobs)} jobs", flush=True)
        
        for j in jobs:
            title = j.get('job_post_info', {}).get('name', '')
            title_lower = title.lower()
            desc = j.get('job_post_info', {}).get('description', '').lower()
            loc = j.get('job_post_info', {}).get('city', {}).get('name', '')
            post_id = j.get('job_post_info', {}).get('id', '')
            post_url = f"https://jobs.bytedance.com/experienced/position/{post_id}/detail"
            
            if not post_id:
                continue
            
            # Check title/desc for keywords
            combined = title_lower + ' ' + desc
            title_match = any(k in combined for k in ['产品经理', 'product manager', 'strategy', 'bizops', 'growth', '商业化'])
            loc_match = any(l in (loc or '').lower() for l in ['深圳', '上海', '广州', '新加坡', 'shenzhen', 'hong kong'])
            
            if title_match and loc_match:
                new_jobs.append({
                    'title': title,
                    'company': 'ByteDance',
                    'location': loc,
                    'url': post_url,
                    'source': 'bytedance_api',
                    'posted': '',
                    'scanned_date': datetime.now().strftime('%Y-%m-%d'),
                })
    except Exception as e:
        print(f"ByteDance '{keyword}' error: {e}", flush=True)

print(f"\n=== Tencent+ByteDance RESULTS ===")
print(f"New jobs found: {len(new_jobs)}")
for j in new_jobs:
    print(f"📌 {j['title']} @ {j['company']}")
    print(f"   📍 {j['location']}")
    print(f"   🔗 {j['url']}")

with open('/Users/iancolrick/.openclaw/workspace/new_tencent_bytedance_jobs.json', 'w') as f:
    json.dump(new_jobs, f, indent=2)
