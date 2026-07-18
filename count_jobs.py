#!/usr/bin/env python3
import json
with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json') as f:
    jobs = json.load(f)
print(f'Total jobs: {len(jobs)}')
urls = set(j.get('url', '') for j in jobs)
print(f'Unique URLs: {len(urls)}')
# Show last 5 jobs by discovered/posted date
dated = [(j.get('discovered', j.get('posted_date', j.get('scanned_date', ''))), j.get('company', '?'), j.get('en_title', j.get('title', '?'))) for j in jobs]
dated.sort(key=lambda x: str(x[0]), reverse=True)
for d, c, t in dated[:10]:
    print(f'  {d} | {c} | {t}')
