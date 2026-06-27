#!/usr/bin/env python3
"""Market Intelligence — Grade Distribution + Cross-DB Comparison
"""
import json
import os
from collections import Counter

# Main database (1358 jobs, letter grades)
DB1 = os.path.expanduser("~/.openclaw/workspace/jobs-all.json")
with open(DB1, 'r') as f:
    jobs1 = json.load(f)

# Career OS database (may have numeric scores)
DB2 = os.path.expanduser("~/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json")
with open(DB2, 'r') as f:
    jobs2 = json.load(f)

print(f"=== DATABASE COMPARISON ===")
print(f"Main DB (jobs-all.json): {len(jobs1)} jobs")
print(f"Career OS DB: {len(jobs2)} jobs")

# Grade distribution for main DB
grades = Counter(j.get('grade', 'None') for j in jobs1)
print(f"\n=== GRADE DISTRIBUTION (Main DB) ===")
for g, n in sorted(grades.items(), key=lambda x: -x[1]):
    print(f"  {g}: {n}")

# High-grade roles (A-1 is highest)
a1_roles = [j for j in jobs1 if j.get('grade') == 'A-1']
a2_roles = [j for j in jobs1 if j.get('grade') == 'A-2']
print(f"\nA-1 (top tier): {len(a1_roles)} roles")
print(f"A-2: {len(a2_roles)} roles")
print(f"A-1 + A-2 combined: {len(a1_roles) + len(a2_roles)} roles")

# A-1 roles by company
a1_companies = Counter(j.get('company', 'Unknown') for j in a1_roles)
print(f"\nA-1 roles by company:")
for c, n in a1_companies.most_common(15):
    print(f"  {c}: {n}")

# A-1 roles by city
a1_cities = Counter()
for j in a1_roles:
    city = j.get('city_normalized', j.get('city', j.get('location', 'Unknown')))
    a1_cities[city] += 1
print(f"\nA-1 roles by city:")
for city, n in a1_cities.most_common(10):
    print(f"  {city}: {n}")

# Cross-border A-1 roles
cross_a1 = [j for j in a1_roles if 'cross' in str(j.get('title', '')).lower() or '跨境' in str(j.get('title', ''))]
print(f"\n=== CROSS-BORDER A-1 ROLES ({len(cross_a1)}) ===")
for j in cross_a1:
    print(f"  {j.get('company', '?')} — {j.get('title', '?')} ({j.get('city_normalized', j.get('city', '?'))})")
    if j.get('url'):
        print(f"    URL: {j['url'][:80]}")

# Career OS DB — check for numeric scores
scored2 = [j for j in jobs2 if j.get('score') is not None and j.get('score') != '']
print(f"\n=== CAREER OS DB ===")
print(f"Total: {len(jobs2)}")
print(f"With score: {len(scored2)}")
if scored2:
    scores2 = [j['score'] for j in scored2 if isinstance(j.get('score'), (int, float))]
    if scores2:
        print(f"Score range: {min(scores2)} to {max(scores2)}")
        print(f"Score 80+: {len([s for s in scores2 if s >= 80])}")
        print(f"Score 100: {len([s for s in scores2 if s == 100])}")

# Top A-1 roles in target cities
target_cities = ['Hong Kong', 'Singapore', 'Shanghai', 'Shenzhen', 'Tokyo']
a1_target = [j for j in a1_roles if j.get('city_normalized', j.get('city', j.get('location', ''))) in target_cities]
print(f"\n=== A-1 ROLES IN TARGET CITIES ({len(a1_target)}) ===")
for j in sorted(a1_target, key=lambda x: x.get('company', '')):
    city = j.get('city_normalized', j.get('city', j.get('location', '?')))
    eng = "✓EN" if j.get('english_friendly') else ""
    salary = j.get('salary', '')
    print(f"  {j.get('company', '?')} — {j.get('title', '?')[:55]} ({city}) {eng}")
    if salary:
        print(f"    Salary: {salary}")

# New companies not in previous analysis
prev_companies = {'OKX', 'Coupang', 'Agoda', 'Stripe', 'Binance', 'Airwallex', 'Coins.ph', 
                  'ByteDance', 'Shopee', 'Databricks', 'Datadog', 'Flexport', 'Payoneer',
                  'Anthropic', 'Adyen', 'Grab', 'MongoDB', 'Xendit', 'Twilio', 'Coinbase'}
current_companies = set(j.get('company', '') for j in jobs1 if j.get('company'))
new_companies = current_companies - prev_companies
print(f"\n=== NEW COMPANIES NOT PREVIOUSLY TRACKED ===")
for c in sorted(new_companies):
    count = len([j for j in jobs1 if j.get('company') == c])
    if count >= 3:
        a1_count = len([j for j in a1_roles if j.get('company') == c])
        print(f"  {c}: {count} roles ({a1_count} A-1)")
