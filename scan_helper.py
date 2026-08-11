#!/usr/bin/env python3
"""Job scan helper: count existing jobs and build dedup sets."""
import json, sys

jobs = json.load(open('OKComputer_职位搜索清单/jobs-all.json'))
print(f'Total jobs in DB: {len(jobs)}')

urls = set(j.get('url','').lower().strip() for j in jobs)
titles_companies = set((j.get('title','').lower().strip(), j.get('company','').lower().strip()) for j in jobs)
print(f'Unique URLs: {len(urls)}')
print(f'Unique title+company combos: {len(titles_companies)}')

dates = sorted(set(j.get('scanned_date','') for j in jobs if j.get('scanned_date')))
print(f'Last scan dates: {dates[-5:]}')

recent = sorted([j for j in jobs if j.get('scanned_date')], key=lambda x: x['scanned_date'], reverse=True)[:5]
for j in recent:
    print(f'  Recent: {j.get("company")} | {j.get("title")} | scanned: {j.get("scanned_date")}')

# Save dedup data for reference
dedup_data = {
    'urls': list(urls),
    'title_company': [(t, c) for t, c in titles_companies]
}
with open('/tmp/job_dedup.json', 'w') as f:
    json.dump(dedup_data, f)
print('Dedup data saved to /tmp/job_dedup.json')
