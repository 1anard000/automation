#!/usr/bin/env python3
import json

with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json') as f:
    jobs = json.load(f)

# Extract all URLs, titles+companies for dedup
urls = set(j.get('url','').rstrip('/') for j in jobs)
title_company = set()
for j in jobs:
    t = j.get('title','').strip().lower()
    c = j.get('company','').strip().lower()
    title_company.add((t, c))

# Save for quick dedup
with open('/Users/iancolrick/.openclaw/workspace/existing_urls.json', 'w') as f:
    json.dump(list(urls), f)
with open('/Users/iancolrick/.openclaw/workspace/existing_titles.json', 'w') as f:
    json.dump([list(x) for x in title_company], f)

print(f'Saved {len(urls)} URLs and {len(title_company)} title+company pairs')
