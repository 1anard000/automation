#!/usr/bin/env python3
"""Add filtered new jobs to database and rebuild dashboard."""
import json, shutil
from datetime import datetime

# Load new jobs from scan
new_jobs = json.load(open('/tmp/new_jobs_to_add.json'))

# Load existing jobs
jobs = json.load(open('OKComputer_职位搜索清单/jobs-all.json'))

# Filter new jobs more carefully based on target profile:
# - Locations: Shenzhen > Hong Kong > Guangzhou > Shanghai > Singapore
# - Roles: Senior PM / Strategy / BizOps / Growth / GM
# - Skip: Director/VP, internships
# - Prefer: Cross-border, marketplace, fintech, AI
# - Skip: Crypto exchanges (already in rules)

TARGET_LOCS = ['shenzhen', 'hong kong', 'shanghai', 'guangzhou', 'singapore']
SECONDARY_LOCS = ['bangkok', 'taipei', 'tokyo', 'manila', 'jakarta', 'kuala lumpur']

# Title keywords that are strong matches
STRONG_TITLE = [
    'product manager', 'strategy', 'growth', 'head of', 'gm',
    'bizops', 'business operations', 'commercial', 'business development',
    'cross-border', 'marketplace', 'fintech', 'payments', 'platform',
    'lead', 'chief of staff', 'go-to-market', 'gtm',
    'expansion', 'partnerships'
]

# Title keywords that are weak matches (still acceptable)
WEAK_TITLE = [
    'marketing manager', 'marketing specialist', 'abm', 'lead generation',
    'finance manager', 'finance analyst', 'data platform', 'cloud solutions',
    'counsel', 'privacy', 'insights analyst'
]

# Seniority to skip
SKIP_SENIORITY = [
    'director', 'vp ', 'vice president', 'svp', 'evp', 'chief ',
    'cfo', 'cto', 'ceo', 'coo', 'intern', 'internship'
]

filtered = []
today = datetime.now().strftime('%Y-%m-%d')

for j in new_jobs:
    title = j.get('title', '')
    company = j.get('company', '')
    loc = j.get('location', '')
    tl = title.lower()
    ll = loc.lower()
    
    # Skip Director/VP level
    if any(k in tl for k in SKIP_SENIORITY):
        continue
    
    # Check if location is in target locations
    is_target_loc = any(k in ll for k in TARGET_LOCS)
    is_secondary_loc = any(k in ll for k in SECONDARY_LOCS)
    
    # Check title match strength
    is_strong_title = any(k in tl for k in STRONG_TITLE)
    is_weak_title = any(k in tl for k in WEAK_TITLE)
    
    # Decision logic:
    # 1. Strong title + any location -> include
    # 2. Weak title + target location -> include
    # 3. Weak title + secondary location -> skip
    # 4. No title match -> skip (shouldn't happen based on earlier filter)
    
    if is_strong_title:
        filtered.append(j)
        print(f"  ✅ STRONG: {company} | {title} | {loc}")
    elif is_weak_title and is_target_loc:
        filtered.append(j)
        print(f"  ✅ WEAK+TARGET: {company} | {title} | {loc}")
    elif is_weak_title and is_secondary_loc:
        # Skip weak matches in secondary locations
        print(f"  ⚠️ SKIP (weak+secondary): {company} | {title} | {loc}")
    else:
        # Check if it's a marketing/finance role in secondary location
        print(f"  ⚠️ SKIP (no match): {company} | {title} | {loc}")

print(f"\n=== FILTERED: {len(filtered)} jobs to add (from {len(new_jobs)} total) ===")

# Add to database
jobs.extend(filtered)

# Save updated database
with open('OKComputer_职位搜索清单/jobs-all.json', 'w', encoding='utf-8') as f:
    json.dump(jobs, f, ensure_ascii=False, indent=2)

print(f"\nDatabase updated: {len(jobs)} total jobs (added {len(filtered)} new)")
print("Saved to OKComputer_职位搜索清单/jobs-all.json")
