#!/usr/bin/env python3
"""Filter new jobs and merge into database."""
import json
import os

DB_PATH = os.path.expanduser("~/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json")
NEW_PATH = os.path.expanduser("~/.openclaw/workspace/new_jobs_temp.json")

with open(DB_PATH) as f:
    existing = json.load(f)
with open(NEW_PATH) as f:
    new_raw = json.load(f)

print(f"Raw new jobs: {len(new_raw)}")

# Filter rules:
# 1. Skip Director roles (but keep "Manager/Senior Manager")
# 2. Skip purely Korean/non-English titles
# 3. Skip non-relevant roles (compliance, legal, security, payroll, etc.)
# 4. Focus on target locations: Shenzhen, HK, SG, Shanghai, Guangzhou, Taipei
# 5. Skip engineering-only roles

SKIP_TITLE_KEYWORDS = [
    'director', 'vp ', 'vice president', 'chief',
    'compliance', 'legal', 'counsel', 'audit', 'security',
    'payroll', 'compensation', 'employee relation',
    'real estate', 'procurement', 'logistics', 'loss prevention',
    'information security', 'infrastructure procurement',
    'customer service', 'contact center',
    'data security', 'privacy',
    'staff engineer', 'backend engineer', 'frontend engineer', 'blockchain engineer',
    'test development', 'sre ', 'techops', 'hrbp',
    'linehaul', 'robotics', 'computer vision',
]

TARGET_LOCATIONS = ['hong kong', 'shenzhen', 'singapore', 'shanghai', 'guangzhou', 'taipei', 'apac']

filtered = []
for j in new_raw:
    title_lower = j['title'].lower()
    loc_lower = j['location'].lower()
    
    # Skip director/VP
    if any(k in title_lower for k in SKIP_TITLE_KEYWORDS):
        continue
    
    # Skip non-target locations
    if not any(k in loc_lower for k in TARGET_LOCATIONS):
        continue
    
    # Skip Korean-only titles (no English words)
    has_english = any(c.isascii() and c.isalpha() for c in j['title'])
    if not has_english:
        continue
    
    # Prefer Manager/Senior Manager/Lead/Principal level
    filtered.append(j)

print(f"After filtering: {len(filtered)}")

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
print("\n=== KEPT JOBS (relevant to profile) ===")
for j in filtered:
    print(f"\n📌 {j['title']} @ {j['company']}")
    print(f"📍 {j['location']}")
    print(f"🔗 {j['url']}")

# Clean up
os.remove(NEW_PATH)
