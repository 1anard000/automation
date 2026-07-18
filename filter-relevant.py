#!/usr/bin/env python3
"""Filter new jobs to most relevant for WeChat update."""
import json, re

with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/new-jobs-this-scan.json') as f:
    jobs = json.load(f)

# Target profile filters
GOOD_KEYWORDS = ['product manager', 'strategy', 'growth', 'bizops', 'biz ops', 'business operations',
                 'gm', 'general manager', 'head of', 'lead', 'program manager', 'operations manager',
                 'commercial', 'marketplace', 'platform', 'go-to-market', 'gtm']
BAD_KEYWORDS = ['engineer', 'designer', 'recruiter', 'accountant', 'legal', 'hr operations',
                'data engineer', 'software', 'architect', 'quant developer', 'frontend', 'backend',
                'full stack', 'staff engineer', 'senior staff engineer']
TARGET_LOCS = ['hong kong', 'singapore', 'shenzhen', 'shanghai', 'guangzhou', 'tokyo', 'taipei', 'seoul']

relevant = []
for j in jobs:
    tl = j.get('title', '').lower()
    ll = j.get('location', '').lower()
    
    # Must be in target location
    if not any(k in ll for k in TARGET_LOCS):
        continue
    
    # Must have good keywords
    if not any(k in tl for k in GOOD_KEYWORDS):
        continue
    
    # Must NOT have bad keywords
    if any(k in tl for k in BAD_KEYWORDS):
        continue
    
    # Skip Director/VP
    if any(k in tl for k in ['director', 'vp ', 'vice president']):
        continue
    
    relevant.append(j)

print(f"Relevant new jobs: {len(relevant)}")
for j in relevant:
    print(f"  📌 {j['title']} @ {j['company']} | {j.get('location', '')} | {j.get('url', '')}")
