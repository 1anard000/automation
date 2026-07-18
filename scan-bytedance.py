#!/usr/bin/env python3
"""Scan ByteDance careers API for APAC PM/Strategy/Growth roles."""
import json, urllib.request, sys, re
from datetime import datetime

# ByteDance API endpoint
url = "https://jobs.bytedance.com/api/v1/search/position"
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Content-Type': 'application/json'
}

# Try multiple search keywords
keywords = ['product manager', 'strategy', 'growth', '商业策略', '产品经理', '增长']
all_results = []

for kw in keywords:
    params = {
        "keyword": kw,
        "limit": 50,
        "offset": 0,
        "position_type": [],
        "job_category": [],
        "city_code": [],
        "area_code": ["040090", "040020", "040030", "040080"],  # SZ, HK, GZ, SH
        "type": "all"
    }
    try:
        data = json.dumps(params).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        positions = result.get('data', {}).get('position_list', [])
        print(f"ByteDance '{kw}': {len(positions)} results")
        for p in positions:
            title = p.get('name', '')
            loc = p.get('city', {}).get('name', '') if isinstance(p.get('city'), dict) else str(p.get('city', ''))
            job_id = p.get('id', '')
            all_results.append({
                'title': title,
                'company': 'ByteDance',
                'location': loc,
                'url': f'https://jobs.bytedance.com/experienced/position/{job_id}/detail',
                'source': 'bytedance_api',
                'salary': '',
                'scanned_date': datetime.now().strftime('%Y-%m-%d'),
                'role_type': 'unknown',
                'quality_score': 75,
                'quality_tier': 'B'
            })
    except Exception as e:
        print(f"ByteDance '{kw}': {e}", file=sys.stderr)

# Dedup by URL
seen = set()
deduped = []
for r in all_results:
    if r['url'] not in seen:
        seen.add(r['url'])
        deduped.append(r)

with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/bytedance-scan.json', 'w') as f:
    json.dump(deduped, f, ensure_ascii=False, indent=2)
print(f"\nTotal ByteDance candidates: {len(deduped)}")
for r in deduped[:20]:
    print(f"  📌 {r['title']} @ {r['company']} | {r['location']} | {r['url']}")
if len(deduped) > 20:
    print(f"  ... and {len(deduped)-20} more")
