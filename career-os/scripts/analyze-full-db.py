#!/usr/bin/env python3
"""Analyze the full job database (jobs-all.json) for actionable insights."""

import json
from collections import Counter, defaultdict

def safe_score(j):
    return j.get('quality_score') or 0

with open('OKComputer_职位搜索清单/jobs-all.json', 'r') as f:
    jobs = json.load(f)

print(f"Total jobs: {len(jobs)}")

# Score distribution
score_dist = Counter()
for j in jobs:
    s = safe_score(j)
    if s >= 90: score_dist['90-100'] += 1
    elif s >= 80: score_dist['80-89'] += 1
    elif s >= 70: score_dist['70-79'] += 1
    elif s >= 60: score_dist['60-69'] += 1
    else: score_dist['<60'] += 1

print(f"\n--- SCORE DISTRIBUTION ---")
for bucket in ['90-100', '80-89', '70-79', '60-69', '<60']:
    print(f"  {bucket}: {score_dist.get(bucket, 0)} jobs")

# Top companies by count
companies = Counter((j.get('company') or 'Unknown') for j in jobs)
print(f"\n--- TOP 25 COMPANIES ---")
for c, count in companies.most_common(25):
    high = sum(1 for j in jobs if (j.get('company') or '') == c and safe_score(j) >= 80)
    print(f"  {c}: {count} total, {high} score-80+")

# Cities
cities = Counter((j.get('location_norm') or j.get('location') or 'Unknown') for j in jobs)
print(f"\n--- CITIES ---")
for c, count in cities.most_common(20):
    print(f"  {c}: {count} jobs")

# English-friendly stats
eng = sum(1 for j in jobs if j.get('english_friendly'))
print(f"\n--- ENGLISH FRIENDLY ---")
print(f"  Total: {eng}/{len(jobs)} ({100*eng/len(jobs):.1f}%)")

# App platform
platforms = Counter((j.get('app_platform') or 'Unknown') for j in jobs)
print(f"\n--- APP PLATFORM ---")
for p, count in platforms.most_common(10):
    print(f"  {p}: {count}")

# Score 100 jobs
print(f"\n--- SCORE 100 JOBS ---")
for j in sorted(jobs, key=lambda x: safe_score(x), reverse=True):
    if safe_score(j) == 100:
        print(f"  {(j.get('company') or 'Unknown')} | {j.get('en_title') or j.get('title', 'Unknown')} | {j.get('location_norm') or j.get('location', 'Unknown')}")

# Score 80-99 jobs
print(f"\n--- SCORE 80-99 JOBS ---")
count_80_99 = 0
for j in sorted(jobs, key=lambda x: safe_score(x), reverse=True):
    score = safe_score(j)
    if 80 <= score < 100:
        count_80_99 += 1
        if count_80_99 <= 50:
            print(f"  {score} | {(j.get('company') or 'Unknown')} | {j.get('en_title') or j.get('title', 'Unknown')} | {j.get('location_norm') or j.get('location', 'Unknown')}")
print(f"  ... Total: {count_80_99} jobs")

# Category analysis
cats = Counter((j.get('category') or 'Unknown') for j in jobs)
print(f"\n--- CATEGORIES ---")
for c, count in cats.most_common(15):
    high = sum(1 for j in jobs if (j.get('category') or '') == c and safe_score(j) >= 80)
    print(f"  {c}: {count} total, {high} score-80+")

# Cross-border / marketplace / fintech / strategy roles
print(f"\n--- CROSS-BORDER / MARKETPLACE / FINTECH / STRATEGY ROLES (score 70+) ---")
cross_border = []
for j in jobs:
    title = ((j.get('en_title') or '') or (j.get('title') or '')).lower()
    score = safe_score(j)
    if score >= 70 and any(kw in title for kw in ['cross-border', 'cross border', 'marketplace', 'b2b', 'fintech', 'payment', 'commerce', 'e-commerce', 'ecommerce', 'growth', 'strategy', 'bizops', 'chief of staff']):
        cross_border.append(j)

cross_border.sort(key=lambda x: safe_score(x), reverse=True)
for j in cross_border[:30]:
    print(f"  {safe_score(j)} | {(j.get('company') or 'Unknown')} | {j.get('en_title') or j.get('title', 'Unknown')} | {j.get('location_norm') or j.get('location', 'Unknown')}")
print(f"  ... Total: {len(cross_border)} matching roles")

# Freshness
from datetime import datetime, timedelta
now = datetime(2026, 6, 27)
fresh = 0
stale = 0
unknown_date = 0
for j in jobs:
    scanned = j.get('scanned_date', '')
    if scanned:
        try:
            d = datetime.strptime(scanned, '%Y-%m-%d')
            if (now - d).days <= 7:
                fresh += 1
            else:
                stale += 1
        except:
            unknown_date += 1
    else:
        unknown_date += 1

print(f"\n--- FRESHNESS ---")
print(f"  Fresh (<=7 days): {fresh}")
print(f"  Stale (>7 days): {stale}")
print(f"  No date: {unknown_date}")

# Untapped high-value roles
print(f"\n--- UNTAPPED HIGH-VALUE ROLES (score 80+, not yet applied) ---")
untapped = []
for j in jobs:
    score = safe_score(j)
    status = j.get('status') or j.get('application_status') or ''
    if score >= 80 and not status:
        untapped.append(j)

untapped.sort(key=lambda x: safe_score(x), reverse=True)
print(f"  Total untapped score-80+: {len(untapped)}")
for j in untapped[:25]:
    print(f"  {safe_score(j)} | {(j.get('company') or 'Unknown')} | {j.get('en_title') or j.get('title', 'Unknown')} | {j.get('location_norm') or j.get('location', 'Unknown')}")

# Visa sponsorship signals
print(f"\n--- VISA / SPONSORSHIP SIGNALS ---")
visa_companies = ['Google', 'Microsoft', 'Airwallex', 'OKX', 'Stripe', 'Shopee', 'ByteDance', 'Agoda', 'Coupang', 'Mastercard']
for vc in visa_companies:
    count = sum(1 for j in jobs if (j.get('company') or '').lower() == vc.lower())
    high = sum(1 for j in jobs if (j.get('company') or '').lower() == vc.lower() and safe_score(j) >= 80)
    if count > 0:
        print(f"  {vc}: {count} jobs, {high} score-80+")

# Quick wins: direct apply + score 80+ + English
print(f"\n--- QUICK WINS: DIRECT APPLY + SCORE 80+ + ENGLISH ---")
quick_wins = []
for j in jobs:
    score = safe_score(j)
    eng_friendly = j.get('english_friendly')
    platform = j.get('app_platform') or ''
    if score >= 80 and eng_friendly and platform in ['careers_site', 'linkedin_easy', 'direct']:
        quick_wins.append(j)

quick_wins.sort(key=lambda x: safe_score(x), reverse=True)
print(f"  Total quick wins: {len(quick_wins)}")
for j in quick_wins[:20]:
    print(f"  {safe_score(j)} | {(j.get('company') or 'Unknown')} | {j.get('en_title') or j.get('title', 'Unknown')} | {j.get('location_norm') or j.get('location', 'Unknown')} | {j.get('url', 'no url')[:80]}")

# NEW: Stale role analysis by company
print(f"\n--- STALE RISK BY COMPANY (score 80+, >7 days old) ---")
stale_risk = []
for j in jobs:
    score = safe_score(j)
    if score < 80:
        continue
    scanned = j.get('scanned_date', '')
    if scanned:
        try:
            d = datetime.strptime(scanned, '%Y-%m-%d')
            days_old = (now - d).days
            if days_old > 7:
                stale_risk.append((days_old, j))
        except:
            pass

stale_risk.sort(key=lambda x: x[0], reverse=True)
for days_old, j in stale_risk[:15]:
    print(f"  {days_old}d old | {safe_score(j)} | {(j.get('company') or 'Unknown')} | {j.get('en_title') or j.get('title', 'Unknown')} | {j.get('location_norm') or j.get('location', 'Unknown')}")

print(f"\n  Total stale high-score roles: {len(stale_risk)}")
