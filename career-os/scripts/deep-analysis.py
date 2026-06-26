#!/usr/bin/env python3
"""Deep analysis: OKX case variants, direct-apply URLs, and actionable quick wins."""

import json
from collections import Counter

with open('OKComputer_职位搜索清单/jobs-all.json', 'r') as f:
    jobs = json.load(f)

def safe_score(j):
    return j.get('quality_score') or 0

# 1. OKX case variant analysis
print("--- OKX CASE VARIANT ANALYSIS ---")
okx_both = []
for j in jobs:
    company = (j.get('company') or '').lower()
    if 'okx' in company:
        okx_both.append(j)

print(f"Total OKX/Okx jobs: {len(okx_both)}")
okx_high = [j for j in okx_both if safe_score(j) >= 80]
print(f"Score 80+: {len(okx_high)}")
for j in sorted(okx_high, key=lambda x: safe_score(x), reverse=True):
    url = j.get('url', '')[:80]
    print(f"  {safe_score(j)} | {(j.get('company'))} | {j.get('en_title') or j.get('title', 'Unknown')} | {j.get('location_norm') or j.get('location', 'Unknown')} | {url}")

# 2. Direct apply analysis - check URL patterns
print("\n--- DIRECT APPLY URL PATTERNS ---")
patterns = Counter()
for j in jobs:
    url = j.get('url', '') or ''
    if 'greenhouse' in url: patterns['greenhouse'] += 1
    elif 'lever' in url: patterns['lever'] += 1
    elif 'workday' in url: patterns['workday'] += 1
    elif 'linkedin.com' in url: patterns['linkedin'] += 1
    elif 'jobsdb' in url: patterns['jobsdb'] += 1
    elif 'zhipin' in url: patterns['zhipin'] += 1
    elif 'liepin' in url: patterns['liepin'] += 1
    else: patterns['other/none'] += 1

for p, count in patterns.most_common():
    print(f"  {p}: {count}")

# 3. Score 80+ with working URLs
print("\n--- SCORE 80+ WITH URLs (potential quick wins) ---")
quick = []
for j in jobs:
    score = safe_score(j)
    url = j.get('url', '') or ''
    if score >= 80 and url:
        quick.append(j)

quick.sort(key=lambda x: safe_score(x), reverse=True)
print(f"Total: {len(quick)}")
for j in quick[:30]:
    print(f"  {safe_score(j)} | {(j.get('company') or 'Unknown')} | {j.get('en_title') or j.get('title', 'Unknown')} | {j.get('location_norm') or j.get('location', 'Unknown')} | {(j.get('url') or '')[:90]}")

# 4. Untapped score-100 roles
print("\n--- SCORE 100 UNTAPPED ---")
for j in jobs:
    if safe_score(j) == 100:
        print(f"  {(j.get('company') or 'Unknown')} | {j.get('en_title') or j.get('title', 'Unknown')} | {j.get('location_norm') or j.get('location', 'Unknown')} | {(j.get('url') or '')[:80]}")

# 5. Company growth: which companies have the most NEW roles?
print("\n--- LARGEST COMPANY OPPORTUNITIES ---")
company_stats = {}
for j in jobs:
    company = j.get('company') or 'Unknown'
    if company not in company_stats:
        company_stats[company] = {'total': 0, 'high': 0, 'cities': set(), 'categories': set()}
    company_stats[company]['total'] += 1
    if safe_score(j) >= 80:
        company_stats[company]['high'] += 1
    company_stats[company]['cities'].add(j.get('location_norm') or j.get('location') or 'Unknown')
    company_stats[company]['categories'].add(j.get('category') or 'Unknown')

sorted_companies = sorted(company_stats.items(), key=lambda x: x[1]['high'], reverse=True)
for company, stats in sorted_companies[:15]:
    if stats['high'] > 0:
        cities = ', '.join(sorted(stats['cities'])[:3])
        cats = ', '.join(sorted(stats['categories'])[:3])
        print(f"  {company}: {stats['total']} jobs, {stats['high']} high-score | Cities: {cities} | Cats: {cats}")

# 6. Cross-border specific roles
print("\n--- CROSS-BORDER SPECIFIC (score 75+, title contains cross-border/cross border) ---")
for j in jobs:
    title = ((j.get('en_title') or '') or (j.get('title') or '')).lower()
    score = safe_score(j)
    if score >= 75 and ('cross-border' in title or 'cross border' in title):
        print(f"  {score} | {(j.get('company') or 'Unknown')} | {j.get('en_title') or j.get('title', 'Unknown')} | {j.get('location_norm') or j.get('location', 'Unknown')}")
