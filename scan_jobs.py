#!/usr/bin/env python3
import json

with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json') as f:
    jobs = json.load(f)
print(f'Total jobs: {len(jobs)}')
urls = set(j.get('url','') for j in jobs)
print(f'Unique URLs: {len(urls)}')
# Print all URLs for dedup checking
for u in sorted(urls):
    print(u)
