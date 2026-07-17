#!/usr/bin/env python3
"""Scan Greenhouse API boards for new APAC PM/Strategy/Growth roles."""
import json, urllib.request, sys, re
from datetime import datetime

BOARDS = ['okx', 'stripe', 'airwallex', 'coupang', 'agoda', 'grab', 'shopee', 'lalamove', 'klook']
TARGET_LOCS = ['hong kong', 'singapore', 'shenzhen', 'shanghai', 'guangzhou', 'tokyo', 'taipei', 'seoul', 'korea', 'malaysia', 'bangkok']
GOOD_KEYWORDS = ['product manager', 'strategy', 'growth', 'bizops', 'biz ops', 'business operations',
                 'gm', 'general manager', 'head of', 'lead', 'program manager', 'operations manager',
                 'commercial', 'marketplace', 'platform', 'go-to-market', 'gtm']
BAD_KEYWORDS = ['director', 'vp ', 'vice president', 'intern', 'internship', 'jr.', 'junior',
                'data scientist', 'software engineer', 'designer', 'recruiter', 'accountant', 'legal']

results = []
for board in BOARDS:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        jobs = data.get('jobs', [])
        print(f"✅ {board}: {len(jobs)} total jobs")
        for j in jobs:
            title = j.get('title', '')
            loc = j.get('location', {}).get('name', '')
            tl = title.lower()
            ll = loc.lower()
            # Location filter
            if not any(k in ll for k in TARGET_LOCS):
                continue
            # Title filter
            if not any(k in tl for k in GOOD_KEYWORDS):
                continue
            if any(k in tl for k in BAD_KEYWORDS):
                continue
            # Extract salary if present in description
            desc = j.get('description', '') or ''
            salary = ''
            salary_match = re.search(r'(\d[\d,]+)\s*[-–to]+\s*(\d[\d,]+)\s*(USD|HKD|SGD|RMB|CNY)', desc, re.I)
            if salary_match:
                salary = salary_match.group(0)
            
            job_url = f"https://job-boards.greenhouse.io/{board}/jobs/{j['id']}"
            results.append({
                'title': title,
                'company': board.capitalize(),
                'location': loc,
                'url': job_url,
                'source': 'greenhouse_api',
                'salary': salary,
                'scanned_date': datetime.now().strftime('%Y-%m-%d'),
                'role_type': 'unknown',
                'quality_score': 75,
                'quality_tier': 'B'
            })
    except Exception as e:
        print(f"❌ {board}: {e}", file=sys.stderr)

with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/greenhouse-scan.json', 'w') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\nTotal new candidates: {len(results)}")
for r in results:
    print(f"  📌 {r['title']} @ {r['company']} | {r['location']} | {r['url']}")
