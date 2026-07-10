#!/usr/bin/env python3
"""Market Intelligence Refresh — June 27, 2026
Analyzes current job database for freshness, new opportunities, and stale roles.
Focus: What changed since last scan? What's the current state?
"""
import json
import os
from datetime import datetime, timedelta
from collections import Counter, defaultdict

DB_PATH = os.path.expanduser("~/OKComputer_职位搜索清单/jobs-all.json")
if not os.path.exists(DB_PATH):
    DB_PATH = os.path.expanduser("~/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json")

with open(DB_PATH, 'r') as f:
    jobs = json.load(f)

print(f"=== MARKET INTELLIGENCE REFRESH — {datetime.now().strftime('%Y-%m-%d')} ===")
print(f"\nTotal jobs in database: {len(jobs)}")

# Basic stats
scored = [j for j in jobs if j.get('score') is not None and j.get('score') != '']
high_score = [j for j in scored if isinstance(j.get('score'), (int, float)) and j['score'] >= 80]
score_100 = [j for j in scored if isinstance(j.get('score'), (int, float)) and j['score'] == 100]
direct_apply = [j for j in jobs if j.get('direct_apply') == True or j.get('method', '').lower() == 'direct']

print(f"Scored jobs: {len(scored)}")
print(f"Score 80+: {len(high_score)}")
print(f"Score 100: {len(score_100)}")
print(f"Direct apply: {len(direct_apply)}")

# Company breakdown
companies = Counter(j.get('company', 'Unknown') for j in jobs)
print(f"\nUnique companies: {len(companies)}")

# City breakdown
cities = Counter(j.get('city', j.get('location', 'Unknown')) for j in jobs)
print(f"\nBy city:")
for city, count in cities.most_common(10):
    print(f"  {city}: {count}")

# Score distribution
score_vals = [j['score'] for j in scored if isinstance(j.get('score'), (int, float))]
if score_vals:
    print(f"\nScore distribution:")
    print(f"  Min: {min(score_vals)}, Max: {max(score_vals)}, Avg: {sum(score_vals)/len(score_vals):.1f}")
    tiers = Counter()
    for s in score_vals:
        if s >= 100: tiers['100'] += 1
        elif s >= 90: tiers['90-99'] += 1
        elif s >= 80: tiers['80-89'] += 1
        elif s >= 70: tiers['70-79'] += 1
        else: tiers['<70'] += 1
    for tier in ['100', '90-99', '80-89', '70-79', '<70']:
        print(f"  {tier}: {tiers.get(tier, 0)}")

# Freshness analysis — check for date_posted fields
dated_jobs = [j for j in jobs if j.get('date_posted') or j.get('posted_date') or j.get('scraped_date')]
print(f"\nJobs with date info: {len(dated_jobs)}")

# High-score by company
company_high = defaultdict(list)
for j in high_score:
    c = j.get('company', 'Unknown')
    company_high[c].append(j)

print(f"\n=== HIGH-SCORE (80+) BY COMPANY ===")
for c, roles in sorted(company_high.items(), key=lambda x: -len(x[1])):
    scores = [r['score'] for r in roles]
    print(f"{c}: {len(roles)} roles (scores: {', '.join(str(int(s)) for s in sorted(scores, reverse=True))})")

# Cross-border specific
cross_border = [j for j in jobs if 'cross' in str(j.get('title', '')).lower() or 'cross' in str(j.get('description', '')).lower()]
print(f"\nCross-border related roles: {len(cross_border)}")
for j in cross_border[:5]:
    print(f"  {j.get('company', '?')} — {j.get('title', '?')} ({j.get('city', '?')}) score={j.get('score', '?')}")

# English-friendly analysis
english = [j for j in jobs if j.get('english_friendly') == True or j.get('language', '').lower() == 'english']
print(f"\nEnglish-friendly roles: {len(english)}")

# Visa sponsorship signals
visa = [j for j in jobs if j.get('visa_sponsorship') == True or 'visa' in str(j.get('description', '')).lower()][:10]
print(f"Visa sponsorship roles (sample): {len(visa)}")

# Stale analysis — roles that might be old
# Check if there are any freshness indicators
print(f"\n=== KEY ACTIONS FOR THIS RUN ===")
print(f"1. Total database: {len(jobs)} jobs across {len(companies)} companies")
print(f"2. High-score pool: {len(high_score)} jobs score-80+, {len(score_100)} at 100")
print(f"3. Direct-apply high-score: {len([j for j in high_score if j.get('direct_apply') or j.get('method', '').lower() == 'direct'])}")
print(f"4. Top opportunity companies: {', '.join(c for c, _ in sorted(company_high.items(), key=lambda x: -len(x[1]))[:5])}")
