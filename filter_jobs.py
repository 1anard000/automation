#!/usr/bin/env python3
"""Filter and add new jobs from Greenhouse scan to database."""
import json
from datetime import datetime

# Load new jobs
with open('/Users/iancolrick/.openclaw/workspace/new_greenhouse_jobs.json') as f:
    all_new = json.load(f)

# Filter for target profile
priority_locations = ['shenzhen', 'hong kong', 'singapore', 'guangzhou', 'shanghai', 'tokyo', 'bangkok', 'asia', 'apac', 'greater china']
target_keywords = ['product manager', 'senior product', 'strategy', 'strategic', 'bizops', 'business operations', 'growth', 'senior manager', 'head of product', 'head of growth', 'head of strategy', 'commercial manager', 'gm ']

# Score and rank
scored = []
for j in all_new:
    title_lower = j['title'].lower()
    loc_lower = j['location'].lower()
    
    # Score location
    loc_score = 0
    for i, loc in enumerate(priority_locations):
        if loc in loc_lower:
            loc_score = max(loc_score, 10 - i)
    
    # Score role type
    role_score = 0
    for kw in target_keywords:
        if kw in title_lower:
            role_score = max(role_score, 8)
    
    # Bonus for fintech/crypto/marketplace
    if any(w in title_lower for w in ['fintech', 'crypto', 'defi', 'web3', 'marketplace', 'commerce', 'payments']):
        role_score += 2
    
    # Penalty for non-PM roles (designers, engineers)
    if any(w in title_lower for w in ['designer', 'engineer', 'scientist', 'analyst']):
        role_score -= 3
    
    total = loc_score + role_score
    
    if total >= 5:  # Only top matches
        scored.append({**j, 'score': total, 'loc_score': loc_score, 'role_score': role_score})

scored.sort(key=lambda x: x['score'], reverse=True)

# Take top 20 most relevant
top_jobs = scored[:20]

print(f"=== TOP {len(top_jobs)} MOST RELEVANT NEW JOBS ===\n")
for j in top_jobs:
    print(f"📌 {j['title']} @ {j['company']}")
    print(f"   📍 {j['location']} | Score: {j['score']} (loc:{j['loc_score']} role:{j['role_score']})")
    print(f"   🔗 {j['url']}")
    print(f"   📅 Posted: {j['posted'][:10] if j.get('posted') else 'unknown'}")
    print()

# Save filtered jobs
with open('/Users/iancolrick/.openclaw/workspace/top_new_jobs.json', 'w') as f:
    json.dump(top_jobs, f, indent=2)

print(f"\nSaved {len(top_jobs)} top jobs to top_new_jobs.json")
print(f"Total from scan: {len(all_new)}")
print(f"Scored ≥5: {len(scored)}")
