#!/usr/bin/env python3
"""Market Intelligence Refresh — Full Analysis
Analyzes the main job database for market intelligence update.
"""
import json
import os
from collections import Counter, defaultdict

# Try the main workspace database first (newer, bigger)
DB_PATH = os.path.expanduser("~/.openclaw/workspace/jobs-all.json")
with open(DB_PATH, 'r') as f:
    jobs = json.load(f)

print(f"=== MARKET INTELLIGENCE REFRESH — DATABASE ANALYSIS ===")
print(f"Database: {DB_PATH}")
print(f"Total jobs: {len(jobs)}")

# Inspect first job to understand schema
if jobs:
    sample = jobs[0]
    print(f"\nSchema fields: {list(sample.keys())[:20]}")
    print(f"Sample job: company={sample.get('company', 'N/A')}, title={sample.get('title', 'N/A')[:60]}, city={sample.get('city', sample.get('location', 'N/A'))}")

# Scored jobs
scored = [j for j in jobs if j.get('score') is not None and j.get('score') != '' and j.get('score') != 0]
print(f"\nScored jobs: {len(scored)}")

# Score breakdown
scores = [j['score'] for j in scored if isinstance(j.get('score'), (int, float))]
print(f"Score range: {min(scores) if scores else 'N/A'} to {max(scores) if scores else 'N/A'}")

high_score = [j for j in scored if isinstance(j.get('score'), (int, float)) and j['score'] >= 80]
score_100 = [j for j in scored if isinstance(j.get('score'), (int, float)) and j['score'] == 100]
score_90 = [j for j in scored if isinstance(j.get('score'), (int, float)) and 90 <= j['score'] < 100]

print(f"Score 100: {len(score_100)}")
print(f"Score 90-99: {len(score_90)}")
print(f"Score 80+: {len(high_score)}")

# Company breakdown
companies = Counter(j.get('company', 'Unknown') for j in jobs)
print(f"\nUnique companies: {len(companies)}")
print(f"\nTop 20 companies by volume:")
for c, n in companies.most_common(20):
    hs = len([j for j in high_score if j.get('company') == c])
    print(f"  {c}: {n} total, {hs} score-80+")

# City breakdown
cities = Counter()
for j in jobs:
    city = j.get('city', j.get('location', 'Unknown'))
    if not city or city == '':
        city = 'Unknown'
    cities[city] += 1
print(f"\nBy city:")
for city, count in cities.most_common(15):
    print(f"  {city}: {count}")

# Direct apply
direct = [j for j in jobs if j.get('direct_apply') == True or str(j.get('method', '')).lower() == 'direct']
print(f"\nDirect apply: {len(direct)}")
direct_hs = [j for j in direct if isinstance(j.get('score'), (int, float)) and j['score'] >= 80]
print(f"Direct apply score-80+: {len(direct_hs)}")

# English friendly
english = [j for j in jobs if j.get('english_friendly') == True or str(j.get('language', '')).lower() == 'english']
print(f"English-friendly: {len(english)}")

# Cross-border
cross_border = [j for j in jobs if 'cross' in str(j.get('title', '')).lower() or 'cross-border' in str(j.get('description', '')).lower() or '跨境' in str(j.get('title', ''))]
print(f"Cross-border roles: {len(cross_border)}")
for j in cross_border[:8]:
    sc = j.get('score', '?')
    print(f"  [{sc}] {j.get('company', '?')} — {j.get('title', '?')[:55]} ({j.get('city', '?')})")

# High-score by company
company_high = defaultdict(list)
for j in high_score:
    c = j.get('company', 'Unknown')
    company_high[c].append(j)

print(f"\n=== HIGH-SCORE (80+) BY COMPANY ===")
for c, roles in sorted(company_high.items(), key=lambda x: -len(x[1])):
    scores_list = [int(r['score']) for r in roles]
    cities_list = [r.get('city', r.get('location', '?')) for r in roles]
    print(f"\n{c} ({len(roles)} roles):")
    for r in sorted(roles, key=lambda x: -x.get('score', 0)):
        print(f"  [{int(r['score'])}] {r.get('title', '?')[:60]} ({r.get('city', r.get('location', '?'))})")

# Top direct-apply quick wins
print(f"\n=== TOP DIRECT-APPLY QUICK WINS (Score 80+, Direct) ===")
quick_wins = sorted(direct_hs, key=lambda x: -x.get('score', 0))
for i, j in enumerate(quick_wins[:25], 1):
    print(f"  {i}. [{int(j['score'])}] {j.get('company', '?')} — {j.get('title', '?')[:55]} ({j.get('city', '?')})")
    if j.get('url'):
        print(f"     URL: {j['url'][:80]}")

# Salary data
salary_jobs = [j for j in jobs if j.get('salary') or j.get('salary_min') or j.get('compensation')]
print(f"\nJobs with salary data: {len(salary_jobs)}")

# Analysis summary
print(f"\n=== ANALYSIS SUMMARY ===")
print(f"Total: {len(jobs)} jobs")
print(f"Score 80+: {len(high_score)} ({100*len(high_score)/len(jobs):.1f}%)")
print(f"Score 100: {len(score_100)}")
print(f"Direct apply: {len(direct)}")
print(f"Direct + 80+: {len(direct_hs)}")
print(f"English: {len(english)} ({100*len(english)/len(jobs):.1f}%)")
print(f"Cross-border: {len(cross_border)}")
