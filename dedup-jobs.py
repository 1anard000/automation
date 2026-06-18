#!/usr/bin/env python3
"""Deduplicate jobs-all.json by title+company, keeping the entry with higher quality_score."""
import json

path = 'OKComputer_职位搜索清单/jobs-all.json'
jobs = json.load(open(path))
print(f'Before: {len(jobs)} jobs')

# Deduplicate by title+company (case-insensitive), keeping higher quality_score
seen = {}
for j in jobs:
    key = (j.get('title', '').strip().lower(), j.get('company', '').strip().lower())
    if key in seen:
        existing = seen[key]
        # Keep the one with higher quality_score
        if (j.get('quality_score', 0)) > (existing.get('quality_score', 0)):
            seen[key] = j
            print(f'  Replaced duplicate: "{j.get("title")}" at "{j.get("company")}" (score {j.get("quality_score")} > {existing.get("quality_score")})')
    else:
        seen[key] = j

deduped = list(seen.values())
print(f'After: {len(deduped)} jobs (removed {len(jobs) - len(deduped)} duplicates)')

# Also fix the known location mismatch
for j in deduped:
    if 'central singapore' in j.get('location', '').lower() and 'hong kong' in j.get('location_norm', '').lower():
        j['location_norm'] = 'Singapore'
        print(f'  Fixed location_norm: "{j.get("title")[:50]}" -> Singapore')

with open(path, 'w') as f:
    json.dump(deduped, f, ensure_ascii=False, indent=2)
print('Saved.')
