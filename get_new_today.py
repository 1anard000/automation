#!/usr/bin/env python3
"""Get new jobs scanned today for summary."""
import json
jobs = json.load(open('OKComputer_职位搜索清单/jobs-all.json'))
today = '2026-08-01'
new_today = [j for j in jobs if j.get('scanned_date') == today]
print(f"Jobs scanned today: {len(new_today)}")
for j in new_today:
    company = j.get('company', '')
    title = j.get('title', '')
    loc = j.get('location', '')
    salary = j.get('salary', 'Not listed')
    url = j.get('url', '')
    src = j.get('source', '')
    print(f"  {company} | {title} | {loc} | {salary} | {src}")
    print(f"    URL: {url}")
