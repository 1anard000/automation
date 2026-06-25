#!/usr/bin/env python3
"""Analyze job database with correct field names."""
import json

with open('/Users/iancolrick/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json', 'r') as f:
    jobs = json.load(f)

print(f'Total jobs: {len(jobs)}')

# Check quality_score values
scores = [j.get('quality_score', 0) or 0 for j in jobs]
print(f'quality_score range: {min(scores)} - {max(scores)}')
print(f'quality_score distribution:')
for threshold in [100, 90, 80, 70, 60, 50]:
    count = sum(1 for s in scores if s >= threshold)
    print(f'  score >= {threshold}: {count}')

# Check location field
locations = set()
for j in jobs:
    loc = j.get('location_norm', j.get('location', ''))
    locations.add(loc)
print(f'\nUnique locations: {len(locations)}')
for loc in sorted(locations)[:20]:
    print(f'  {loc}')

# Focus on score-80+ jobs
high_score = [j for j in jobs if (j.get('quality_score', 0) or 0) >= 80]
print(f'\n--- Score-80+ jobs: {len(high_score)} ---')

# Count by company
companies = {}
for j in high_score:
    co = j.get('company', 'unknown')
    if co not in companies:
        companies[co] = {'count': 0, 'roles': []}
    companies[co]['count'] += 1
    companies[co]['roles'].append(j)

print('\n--- Top score-80+ companies (contact mapping priorities) ---')
for co, data in sorted(companies.items(), key=lambda x: -x[1]['count'])[:15]:
    print(f'\n  {co}: {data["count"]} score-80+ roles')
    for r in data['roles'][:3]:
        title = r.get('title', 'unknown')
        loc = r.get('location_norm', r.get('location', ''))
        score = r.get('quality_score', 0) or 0
        has_direct = r.get('has_direct_link', False)
        print(f'    [{score}] {title} ({loc}) direct={has_direct}')
    if data['count'] > 3:
        print(f'    ... +{data["count"]-3} more')

# Companies with score-100
score100 = [j for j in jobs if (j.get('quality_score', 0) or 0) >= 100]
print(f'\n--- Score-100 jobs: {len(score100)} ---')
for j in score100:
    co = j.get('company', 'unknown')
    title = j.get('title', 'unknown')
    loc = j.get('location_norm', j.get('location', ''))
    has_direct = j.get('has_direct_link', False)
    print(f'  {co}: {title} ({loc}) direct={has_direct}')
