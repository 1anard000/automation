#!/usr/bin/env python3
import json
import re

with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json') as f:
    data = json.load(f)

# Find greenhouse URLs to extract valid slugs
gh_urls = set()
for j in data:
    url = j.get('url', '')
    if 'greenhouse' in url.lower():
        gh_urls.add(url)
        # Also check source
    if 'greenhouse' in j.get('source', '').lower():
        gh_urls.add(url)

print(f"Found {len(gh_urls)} greenhouse URLs in existing database")
for u in sorted(gh_urls)[:30]:
    print(f"  {u}")

# Extract company slugs from URLs
slugs = set()
for u in gh_urls:
    m = re.search(r'boards?(?:-api)?\.greenhouse\.io/(?:v1/jobs/)?(\w+)', u)
    if m:
        slugs.add(m.group(1))

print(f"\nValid greenhouse slugs found: {sorted(slugs)}")
