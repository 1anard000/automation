#!/usr/bin/env python3
"""Analyze job database for market intelligence."""

import json
import sys
from collections import Counter, defaultdict

# Load data
with open('/Users/iancolrick/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json', 'r') as f:
    data = json.load(f)

print(f"Total jobs: {len(data)}")

# Count by company
companies = Counter()
for job in data:
    company = job.get('company', 'Unknown')
    if company:
        companies[company] += 1

print("\nTop 20 companies by job count:")
for company, count in companies.most_common(20):
    print(f"  {company}: {count}")

# Count by location
locations = Counter()
for job in data:
    loc = job.get('location_norm', job.get('location', 'Unknown'))
    locations[loc] += 1

print("\nJobs by location:")
for loc, count in locations.most_common(10):
    print(f"  {loc}: {count}")

# Count by score tier
scores = Counter()
for job in data:
    score = job.get('quality_score') or 0
    if score >= 90:
        scores['90+'] += 1
    elif score >= 80:
        scores['80-89'] += 1
    elif score >= 70:
        scores['70-79'] += 1
    else:
        scores['<70'] += 1

print("\nScore distribution:")
for tier, count in sorted(scores.items()):
    print(f"  {tier}: {count}")

# Count by category
categories = Counter()
for job in data:
    cat = job.get('category', 'unclassified')
    categories[cat] += 1

print("\nCategories:")
for cat, count in categories.most_common(10):
    print(f"  {cat}: {count}")

# Find direct apply jobs
direct_apply = [job for job in data if job.get('has_direct_link') or job.get('url_type') == 'direct']
print(f"\nDirect apply jobs: {len(direct_apply)}")

# Find high-score jobs
high_score = [job for job in data if (job.get('quality_score') or 0) >= 80]
print(f"High-score (80+) jobs: {len(high_score)}")

# Find English-friendly jobs
english = [job for job in data if job.get('english_friendly')]
print(f"English-friendly jobs: {len(english)}")

# Salary ranges
salary_jobs = [job for job in data if job.get('salary')]
print(f"\nJobs with salary data: {len(salary_jobs)}")

# Top companies with high-score roles
print("\nTop companies with high-score (80+) roles:")
company_high_score = defaultdict(int)
for job in high_score:
    company = job.get('company', 'Unknown')
    if company:
        company_high_score[company] += 1

for company, count in sorted(company_high_score.items(), key=lambda x: -x[1])[:15]:
    print(f"  {company}: {count}")

# Stale analysis
stale = [job for job in data if job.get('low_quality')]
print(f"\nLow quality/stale jobs: {len(stale)}")

# Jobs by city with scores
print("\nHigh-score jobs by city:")
city_scores = defaultdict(list)
for job in high_score:
    loc = job.get('location_norm', job.get('location', 'Unknown'))
    city_scores[loc].append(job.get('quality_score') or 0)

for city, score_list in sorted(city_scores.items(), key=lambda x: -len(x[1])):
    avg_score = sum(score_list) / len(score_list) if score_list else 0
    print(f"  {city}: {len(score_list)} jobs, avg score: {avg_score:.1f}")
