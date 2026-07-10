#!/usr/bin/env python3
"""Market Intelligence Refresh — Full Analysis v2
Handles both schema types (grade vs score).
"""
import json
import os
from collections import Counter, defaultdict

DB_PATH = os.path.expanduser("~/.openclaw/workspace/jobs-all.json")
with open(DB_PATH, 'r') as f:
    jobs = json.load(f)

print(f"=== MARKET INTELLIGENCE REFRESH — {len(jobs)} JOBS ===\n")

# Normalize — check both 'score' and 'grade' fields
for j in jobs:
    if j.get('score') is None and j.get('grade') is not None:
        j['score'] = j['grade']

# Score/grade stats
scored = [j for j in jobs if j.get('score') is not None and j.get('score') != '' and j.get('score') != 0]
scores = []
for j in scored:
    try:
        s = float(j['score'])
        scores.append(s)
    except:
        pass

print(f"Total jobs: {len(jobs)}")
print(f"With grade/score: {len(scored)}")

if scores:
    print(f"Score range: {min(scores)} to {max(scores)}")
    print(f"Average: {sum(scores)/len(scores):.1f}")
    
    tiers = Counter()
    for s in scores:
        if s >= 100: tiers['100'] += 1
        elif s >= 90: tiers['90-99'] += 1
        elif s >= 80: tiers['80-89'] += 1
        elif s >= 70: tiers['70-79'] += 1
        elif s >= 60: tiers['60-69'] += 1
        else: tiers['<60'] += 1
    print(f"\nScore distribution:")
    for tier in ['100', '90-99', '80-89', '70-79', '60-69', '<60']:
        if tiers.get(tier, 0) > 0:
            print(f"  {tier}: {tiers[tier]}")
else:
    print("No numeric scores found")

# Company breakdown
companies = Counter(j.get('company', 'Unknown') for j in jobs if j.get('company'))
print(f"\nUnique companies (with name): {len(companies)}")
print(f"\nTop 20 companies by volume:")
for c, n in companies.most_common(20):
    hs = len([j for j in scored if j.get('company') == c and isinstance(j.get('score'), (int, float)) and j['score'] >= 80])
    print(f"  {c}: {n} total, {hs} high-score")

# City breakdown (normalize)
city_counter = Counter()
for j in jobs:
    city = j.get('city_normalized', j.get('city', j.get('location', 'Unknown')))
    if not city or city == '':
        city = 'Unknown'
    # Normalize common variations
    city_map = {
        'Singapore, Singapore': 'Singapore',
        'Singapore, SG': 'Singapore',
        'Hong Kong, Hong Kong SAR': 'Hong Kong',
        'Hong Kong, HK': 'Hong Kong',
        'Shenzhen, Guangdong, China': 'Shenzhen',
        '深圳': 'Shenzhen',
        'Shanghai, China': 'Shanghai',
        'Seoul, South Korea': 'Seoul',
        'Bangkok, Thailand': 'Bangkok',
        'Remote - USA': 'Remote (US)',
        'United States - Remote': 'Remote (US)',
    }
    city = city_map.get(city, city)
    city_counter[city] += 1

print(f"\nBy city (normalized):")
for city, count in city_counter.most_common(15):
    print(f"  {city}: {count}")

# English-friendly
english = [j for j in jobs if j.get('english_friendly') == True]
print(f"\nEnglish-friendly: {len(english)} ({100*len(english)/len(jobs):.1f}%)")

# Salary data
salary_jobs = [j for j in jobs if j.get('salary') and j['salary'] != '']
print(f"Jobs with salary data: {len(salary_jobs)}")

# High-score by company
high_score = [j for j in scored if isinstance(j.get('score'), (int, float)) and j['score'] >= 80]
company_high = defaultdict(list)
for j in high_score:
    c = j.get('company', 'Unknown')
    company_high[c].append(j)

print(f"\n=== HIGH-SCORE (80+) BY COMPANY ({len(high_score)} total) ===")
for c, roles in sorted(company_high.items(), key=lambda x: -len(x[1])):
    print(f"\n{c} ({len(roles)} roles):")
    for r in sorted(roles, key=lambda x: -x.get('score', 0))[:5]:
        sc = int(r['score'])
        print(f"  [{sc}] {r.get('title', '?')[:65]} ({r.get('city_normalized', r.get('city', r.get('location', '?')))})")
    if len(roles) > 5:
        print(f"  ... and {len(roles)-5} more")

# Cross-border specific
cross_border = [j for j in jobs if 'cross' in str(j.get('title', '')).lower() or '跨境' in str(j.get('title', ''))]
print(f"\n=== CROSS-BORDER ROLES ({len(cross_border)}) ===")
for j in cross_border[:10]:
    sc = j.get('score', '?')
    if isinstance(sc, (int, float)):
        sc = int(sc)
    print(f"  [{sc}] {j.get('company', '?')} — {j.get('title', '?')[:60]} ({j.get('city_normalized', j.get('city', '?'))})")

# Freshness — check scanned_date
dated = [j for j in jobs if j.get('scanned_date')]
if dated:
    dates = sorted([j['scanned_date'] for j in dated])
    print(f"\nDate range: {dates[0]} to {dates[-1]}")
    recent = [j for j in dated if j['scanned_date'] >= '2026-06-20']
    print(f"Jobs scanned since Jun 20: {len(recent)}")

# Top quick wins — high score + English + target cities
target_cities = ['Hong Kong', 'Singapore', 'Shanghai', 'Shenzhen', 'Tokyo']
quick_wins = [j for j in high_score 
              if j.get('english_friendly') 
              and j.get('city_normalized', j.get('city', j.get('location', ''))) in target_cities]
quick_wins.sort(key=lambda x: -x.get('score', 0))

print(f"\n=== TOP QUICK WINS (Score 80+, English, Target Cities) ===")
print(f"Total: {len(quick_wins)}")
for i, j in enumerate(quick_wins[:20], 1):
    sc = int(j['score'])
    city = j.get('city_normalized', j.get('city', j.get('location', '?')))
    url = j.get('url', '')[:70] if j.get('url') else 'no URL'
    print(f"  {i}. [{sc}] {j.get('company', '?')} — {j.get('title', '?')[:55]} ({city})")
    if url != 'no URL':
        print(f"     {url}")

# Role type breakdown
role_types = Counter(j.get('role_type', 'Unknown') for j in jobs if j.get('role_type'))
if role_types:
    print(f"\nRole types:")
    for rt, count in role_types.most_common(10):
        print(f"  {rt}: {count}")

# Source breakdown
sources = Counter(j.get('source', 'Unknown') for j in jobs if j.get('source'))
if sources:
    print(f"\nSources:")
    for src, count in sources.most_common(10):
        print(f"  {src}: {count}")
