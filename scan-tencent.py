#!/usr/bin/env python3
"""Scan Tencent careers API for APAC PM/Strategy/Growth roles."""
import json, urllib.request, sys, re
from datetime import datetime

keywords = ['product manager', 'growth', 'bizops', 'general manager']
all_results = []

for kw in keywords:
    url = f"https://careers.tencent.com/tencentcareer/api/post/Query?keyword={kw.replace(' ','%20')}&countryId=&cityId=&areaId=&bgId=&skillId=&pageIndex=1&pageSize=30&language=en-us&area=ap"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        posts = data.get('Data', {}).get('Posts', [])
        print(f"Tencent '{kw}': {len(posts)} results")
        for p in posts:
            loc = p.get('LocationName', '')
            title = p.get('RecruitPostName', '')
            tl = title.lower()
            ll = loc.lower()
            if 'intern' in tl:
                continue
            if not any(k in ll for k in ['shenzhen', 'hong kong', 'singapore', 'shanghai', 'guangzhou', 'taipei', 'tokyo']):
                continue
            if not any(k in tl for k in ['product', 'strategy', 'growth', 'gm', 'head', 'manager']):
                continue
            if any(k in tl for k in ['intern', 'junior', 'engineer', 'designer']):
                continue
            url_post = p.get('PostURL', '')
            all_results.append({
                'title': title,
                'company': 'Tencent',
                'location': loc,
                'url': url_post,
                'source': 'tencent_api',
                'salary': '',
                'scanned_date': datetime.now().strftime('%Y-%m-%d'),
                'role_type': 'unknown',
                'quality_score': 80,
                'quality_tier': 'A'
            })
    except Exception as e:
        print(f"Tencent '{kw}': {e}", file=sys.stderr)

# Dedup by URL
seen = set()
deduped = []
for r in all_results:
    if r['url'] not in seen:
        seen.add(r['url'])
        deduped.append(r)

with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/tencent-scan.json', 'w') as f:
    json.dump(deduped, f, ensure_ascii=False, indent=2)
print(f"\nTotal Tencent candidates: {len(deduped)}")
for r in deduped:
    print(f"  📌 {r['title']} @ {r['company']} | {r['location']} | {r['url']}")
