#!/usr/bin/env python3
import json
import urllib.request
import urllib.parse
import ssl

def fetch_tencent(keyword, page_size=50, page_index=0):
    encoded = urllib.parse.quote(keyword)
    url = f"https://careers.tencent.com/tencentcareer/api/post/Query?keyword={encoded}&pageSize={page_size}&pageIndex={page_index}"
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            posts = data.get('Data', {}).get('Posts', [])
            return posts if posts else []
    except Exception as e:
        print(f"Error fetching '{keyword}': {e}")
        return []

# Load existing URLs
with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json') as f:
    existing = json.load(f)
existing_urls = {j.get('url', '') for j in existing}

CHINA_LOCS = ['Shenzhen', 'Hong Kong', 'Guangzhou', 'Shanghai', 'Beijing', 'China', 'HK']
SKIP = ['intern', 'internship', 'junior', 'entry level']

new_jobs = []
for kw in ['product manager', 'strategy', 'growth', 'commercial', 'business development']:
    posts = fetch_tencent(kw)
    print(f"  '{kw}': {len(posts)} posts found")
    for p in posts:
        name = p.get('RecruitPostName', '')
        loc = p.get('LocationName', '')
        url = p.get('PostURL', '')
        update = p.get('LastUpdateTime', '')
        
        if any(skip in name.lower() for skip in SKIP):
            continue
        if not any(cl in loc for cl in CHINA_LOCS):
            continue
        if url not in existing_urls:
            new_jobs.append({
                'company': 'Tencent',
                'title': name,
                'location': loc,
                'url': url,
                'posted': update,
                'source': 'tencent_careers'
            })

print(f"\nNEW TENCENT JOBS: {len(new_jobs)}")
for j in new_jobs:
    print(f"  {j['title']} | {j['location']}")
    print(f"    {j['url']}")
