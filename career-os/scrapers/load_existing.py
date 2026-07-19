#!/usr/bin/env python3
import json

existing = json.load(open('/Users/iancolrick/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json'))
discovered = json.load(open('/Users/iancolrick/.openclaw/workspace/career-os/scrapers/agent-discovered-jobs.json'))
existing_urls = set(j.get('url','') for j in existing)
existing_titles = set(j.get('title','').lower().strip() for j in existing if j.get('url'))
discovered_urls = set(j.get('url','') for j in discovered)
discovered_titles = set(j.get('title','').lower().strip() for j in discovered if j.get('url'))
all_urls = existing_urls | discovered_urls
all_titles = existing_titles | discovered_titles
print(f'Existing jobs: {len(existing)}, Discovered: {len(discovered)}')
print(f'Unique URLs: {len(all_urls)}, Unique titles: {len(all_titles)}')
# Output the sets as JSON for later use
json.dump(list(all_urls), open('/tmp/all_urls.json', 'w'))
json.dump(list(all_titles), open('/tmp/all_titles.json', 'w'))
