#!/usr/bin/env python3
"""Analyze job database for actionable insights."""

import json
import sys
from collections import Counter, defaultdict

# Load the main database
with open('scrapers/final-results.json', 'r') as f:
    data = json.load(f)

jobs = data if isinstance(data, list) else data.get('jobs', data.get('results', []))
print(f"Total jobs: {len(jobs)}")

if len(jobs) == 0:
    print("No jobs found")
    sys.exit(1)

# Print sample keys
print(f"Job keys: {list(jobs[0].keys())}")
print(f"\nSample job:\n{json.dumps(jobs[0], indent=2, ensure_ascii=False)[:600]}")

# Analyze companies
companies = Counter()
for j in jobs:
    company = j.get('company', j.get('company_name', 'Unknown'))
    companies[company] += 1

print(f"\n--- TOP 20 COMPANIES ---")
for c, count in companies.most_common(20):
    print(f"  {c}: {count} jobs")

# Analyze cities
cities = Counter()
for j in jobs:
    city = j.get('city', j.get('location', 'Unknown'))
    cities[city] += 1

print(f"\n--- TOP 15 CITIES ---")
for c, count in cities.most_common(15):
    print(f"  {c}: {count} jobs")

# Analyze scores
scores = []
score_dist = Counter()
for j in jobs:
    score = j.get('score', j.get('priority_score', None))
    if score is not None:
        scores.append(score)
        bucket = f"{(score // 10) * 10}-{(score // 10) * 10 + 9}"
        score_dist[bucket] += 1

print(f"\n--- SCORE DISTRIBUTION ---")
for bucket in sorted(score_dist.keys()):
    print(f"  {bucket}: {score_dist[bucket]} jobs")

# Find score-100 jobs
print(f"\n--- SCORE 100 JOBS ---")
for j in jobs:
    score = j.get('score', j.get('priority_score', None))
    if score == 100:
        company = j.get('company', j.get('company_name', 'Unknown'))
        title = j.get('title', j.get('job_title', 'Unknown'))
        city = j.get('city', j.get('location', 'Unknown'))
        print(f"  {company} | {title} | {city}")

# Find score 80-99 jobs
print(f"\n--- SCORE 80-99 JOBS (count: {sum(1 for s in scores if 80 <= s < 100)}) ---")
high_score_jobs = []
for j in jobs:
    score = j.get('score', j.get('priority_score', None))
    if score is not None and 80 <= score < 100:
        company = j.get('company', j.get('company_name', 'Unknown'))
        title = j.get('title', j.get('job_title', 'Unknown'))
        city = j.get('city', j.get('location', 'Unknown'))
        high_score_jobs.append((score, company, title, city))

high_score_jobs.sort(reverse=True)
for score, company, title, city in high_score_jobs[:30]:
    print(f"  {score} | {company} | {title} | {city}")

# Find direct apply roles
print(f"\n--- DIRECT APPLY JOBS ---")
direct_apply = 0
for j in jobs:
    url = j.get('url', j.get('apply_url', j.get('link', '')))
    if url and ('apply' in str(url).lower() or 'careers' in str(url).lower()):
        direct_apply += 1
print(f"  Total with apply URLs: {direct_apply}")

# Check for cross-border roles
print(f"\n--- CROSS-BORDER / MARKETPLACE ROLES ---")
for j in jobs:
    title = j.get('title', j.get('job_title', '')).lower()
    desc = j.get('description', j.get('desc', '')).lower()
    company = j.get('company', j.get('company_name', 'Unknown'))
    city = j.get('city', j.get('location', 'Unknown'))
    score = j.get('score', j.get('priority_score', 0))
    if any(kw in title for kw in ['cross-border', 'cross border', 'marketplace', 'b2b', 'fintech', 'payment']):
        print(f"  {score} | {company} | {j.get('title', j.get('job_title', 'Unknown'))} | {city}")
