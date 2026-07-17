#!/usr/bin/env python3
"""Scan 51job API for APAC PM/Strategy/Growth roles."""
import json, urllib.request, urllib.parse, sys
from datetime import datetime

keywords = ['产品经理', '商业策略', 'product manager', 'strategy', '增长']
all_results = []
target_cities = {'040090': '深圳', '040020': '香港', '040030': '广州', '040080': '上海'}

for kw in keywords:
    for city, city_name in target_cities.items():
        encoded_kw = urllib.parse.quote(kw)
        url = f"https://we.51job.com/api/job/search-pc?api_key=51job&keyword={encoded_kw}&searchType=2&jobArea={city}&page=1&pageSize=20&sortType=0"
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': 'https://we.51job.com/'
            })
            resp = urllib.request.urlopen(req, timeout=15)
            raw = resp.read()
            data = json.loads(raw)
            jobs = data.get('resultbody', {}).get('job', {}).get('items', [])
            print(f"51job '{kw}' @ {city_name}: {len(jobs)} results")
            for j in jobs:
                title = j.get('jobName', '')
                company = j.get('companyName', '')
                job_url = j.get('jobHref', '')
                salary = j.get('provideSalaryString', '')
                loc = j.get('jobAreaString', '') or city_name
                tl = title.lower()
                if any(k in tl for k in ['intern', '实习', 'director', 'vp']):
                    continue
                all_results.append({
                    'title': title,
                    'company': company,
                    'location': loc,
                    'url': job_url,
                    'source': '51job',
                    'salary': salary,
                    'scanned_date': datetime.now().strftime('%Y-%m-%d'),
                    'role_type': 'unknown',
                    'quality_score': 70,
                    'quality_tier': 'B'
                })
        except Exception as e:
            print(f"51job '{kw}' @ {city_name}: {e}", file=sys.stderr)

# Dedup by URL
seen = set()
deduped = []
for r in all_results:
    if r['url'] not in seen:
        seen.add(r['url'])
        deduped.append(r)

with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/51job-scan.json', 'w') as f:
    json.dump(deduped, f, ensure_ascii=False, indent=2)
print(f"\nTotal 51job candidates: {len(deduped)}")
for r in deduped[:30]:
    print(f"  📌 {r['title']} @ {r['company']} | {r['location']} | {r['url']}")
if len(deduped) > 30:
    print(f"  ... and {len(deduped)-30} more")
