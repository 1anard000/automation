#!/usr/bin/env python3
"""Scan Liepin API for APAC PM/Strategy/Growth roles."""
import json, urllib.request, urllib.parse, sys
from datetime import datetime

# Liepin search API
keywords = ['产品经理', '商业策略', '增长策略', 'product manager']
all_results = []

for kw in keywords:
    url = f"https://api-c.liepin.com/api/com.liepin.searchfront4c.pc-search-job?key={urllib.parse.quote(kw)}&dq=050090&curPage=0&pageSize=20&scene=condition"
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://www.liepin.com/',
            'Accept': 'application/json'
        })
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        jobs = data.get('data', {}).get('data', {}).get('jobCardList', [])
        print(f"Liepin '{kw}': {len(jobs)} results")
        for j in jobs:
            title = j.get('job', {}).get('title', '')
            company = j.get('comp', {}).get('compName', '')
            loc = j.get('job', {}).get('dq', '')
            salary = j.get('job', {}).get('salary', '')
            job_id = j.get('job', {}).get('algoId', '') or j.get('job', {}).get('jobId', '')
            job_url = f"https://www.liepin.com/job/{job_id}" if job_id else ''
            tl = title.lower()
            if any(k in tl for k in ['intern', '实习', 'director', 'vp']):
                continue
            all_results.append({
                'title': title,
                'company': company,
                'location': loc,
                'url': job_url,
                'source': 'liepin',
                'salary': salary,
                'scanned_date': datetime.now().strftime('%Y-%m-%d'),
                'role_type': 'unknown',
                'quality_score': 70,
                'quality_tier': 'B'
            })
    except Exception as e:
        print(f"Liepin '{kw}': {e}", file=sys.stderr)

# Dedup by URL
seen = set()
deduped = []
for r in all_results:
    if r['url'] and r['url'] not in seen:
        seen.add(r['url'])
        deduped.append(r)

with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/liepin-scan.json', 'w') as f:
    json.dump(deduped, f, ensure_ascii=False, indent=2)
print(f"\nTotal Liepin candidates: {len(deduped)}")
for r in deduped[:20]:
    print(f"  📌 {r['title']} @ {r['company']} | {r['location']} | {r['url']}")
if len(deduped) > 20:
    print(f"  ... and {len(deduped)-20} more")
