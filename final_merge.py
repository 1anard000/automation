#!/usr/bin/env python3
"""Final filter and merge new jobs into database."""
import json
import os

DB_PATH = os.path.expanduser("~/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json")
NEW_PATH = os.path.expanduser("~/.openclaw/workspace/new_jobs_final.json")

with open(DB_PATH) as f:
    existing = json.load(f)
with open(NEW_PATH) as f:
    new_raw = json.load(f)

print(f"Raw new jobs: {len(new_raw)}")

# Strict filter for target profile
# Keep: PM, Strategy, Growth, BizOps, BD, GM, Lead (non-engineering)
# Skip: Engineering, compliance, legal, audit, HR, finance ops, etc.
STRICT_SKIP = [
    'engineer', 'developer', 'architect', 'devops', 'sre',
    'compliance', 'legal', 'counsel', 'audit', 'security',
    'payroll', 'compensation', 'employee relation',
    'accountant', 'recruiter', 'recruiting', 'interpreter',
    'customer service', '客服', 'ux researcher',
    'admin specialist', 'executive assistant',
    'supply chain', 'logistics', '運輸',
    'data scientist', 'data engineer', 'algorithm',
    'mobile engineer', 'android engineer', 'ios engineer',
    'front-end', 'back-end', 'backend', 'frontend',
    'staff engineer', 'software engineer',
    'brand management', 'catalog operation', 'instock',
    'line haul', 'linehaul', 'middle mile',
]

# Keep roles matching target
KEEP_KEYWORDS = ['product', 'strategy', 'growth', 'business', 'operations', 'gm', 'lead', 'manager', 'bd', 'partnership', 'commercial', 'marketing']

filtered = []
for j in new_raw:
    title_lower = j['title'].lower()
    
    # Strict skip
    if any(k in title_lower for k in STRICT_SKIP):
        continue
    
    # Must match at least one keep keyword
    if not any(k in title_lower for k in KEEP_KEYWORDS):
        continue
    
    filtered.append(j)

print(f"After strict filtering: {len(filtered)}")

# Add to database
for j in filtered:
    j['scanned_date'] = '2026-08-11'
    j['date'] = '2026-08-11'
    j['date_source'] = 'scanned_today'
    existing.append(j)

print(f"Total jobs after merge: {len(existing)}")

# Save
with open(DB_PATH, 'w') as f:
    json.dump(existing, f, indent=2, ensure_ascii=False)

# Print the keepers
print("\n=== FINAL NEW JOBS (target profile) ===")
for j in filtered:
    print(f"\n📌 {j['title']} @ {j['company']}")
    print(f"📍 {j['location']}")
    print(f"🔗 {j['url']}")

# Clean up
os.remove(NEW_PATH)
