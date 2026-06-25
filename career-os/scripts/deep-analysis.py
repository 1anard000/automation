#!/usr/bin/env python3
"""Deep analysis of job database for market intelligence update."""
import json

with open('/Users/iancolrick/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json', 'r') as f:
    jobs = json.load(f)

# Normalize company names (OKX vs Okx)
for j in jobs:
    co = j.get('company', '')
    if co.lower() in ['okx', 'osl (okx)']:
        j['company'] = 'OKX'
    elif co.lower() == 'binance':
        j['company'] = 'Binance'
    elif co.lower() == 'coins.ph':
        j['company'] = 'Coins.ph'

scores = [j.get('quality_score', 0) or 0 for j in jobs]
print(f'Total jobs: {len(jobs)}')
print(f'Score-80+: {sum(1 for s in scores if s >= 80)}')
print(f'Score-100: {sum(1 for s in scores if s >= 100)}')

# Direct-apply score-80+ English roles
direct_apply_80 = [j for j in jobs if (j.get('quality_score', 0) or 0) >= 80 
                   and j.get('has_direct_link', False)
                   and j.get('english_friendly', False)]
print(f'\nDirect-apply score-80+ English: {len(direct_apply_80)}')

# By company
companies_80 = {}
for j in direct_apply_80:
    co = j.get('company', 'unknown')
    if co not in companies_80:
        companies_80[co] = []
    companies_80[co].append(j)

print('\n--- Direct-apply score-80+ English roles by company ---')
for co, roles in sorted(companies_80.items(), key=lambda x: -len(x[1])):
    print(f'\n  {co}: {len(roles)} roles')
    for r in roles:
        title = r.get('title', 'unknown')
        loc = r.get('location_norm', r.get('location', ''))
        score = r.get('quality_score', 0) or 0
        print(f'    [{score}] {title} ({loc})')

# Salary analysis
print('\n--- Salary data ---')
with_salary = [j for j in jobs if j.get('salary')]
print(f'Jobs with salary data: {len(with_salary)}')

# By city
cities = {}
for j in jobs:
    loc = j.get('location_norm', j.get('location', 'unknown'))
    if loc not in cities:
        cities[loc] = {'total': 0, 'score_80plus': 0, 'english': 0}
    cities[loc]['total'] += 1
    if (j.get('quality_score', 0) or 0) >= 80:
        cities[loc]['score_80plus'] += 1
    if j.get('english_friendly'):
        cities[loc]['english'] += 1

print('\n--- City breakdown (top 15) ---')
for loc, data in sorted(cities.items(), key=lambda x: -x[1]['total'])[:15]:
    eng_pct = round(data['english'] / data['total'] * 100) if data['total'] > 0 else 0
    print(f'  {loc}: {data["total"]} total, {data["score_80plus"]} score-80+, {eng_pct}% English')

# Stale/low quality analysis
low_quality = [j for j in jobs if j.get('low_quality')]
print(f'\nLow quality/stale: {len(low_quality)} ({round(len(low_quality)/len(jobs)*100)}%)')

# OKX deep dive (combined OKX + Okx)
okx_roles = [j for j in jobs if j.get('company') == 'OKX']
okx_80 = [j for j in okx_roles if (j.get('quality_score', 0) or 0) >= 80]
print(f'\n--- OKX Deep Dive ---')
print(f'Total OKX roles: {len(okx_roles)}')
print(f'Score-80+: {len(okx_80)}')
for r in sorted(okx_80, key=lambda x: -(x.get('quality_score', 0) or 0)):
    title = r.get('title', 'unknown')
    loc = r.get('location_norm', r.get('location', ''))
    score = r.get('quality_score', 0) or 0
    direct = r.get('has_direct_link', False)
    print(f'  [{score}] {title} ({loc}) direct={direct}')
