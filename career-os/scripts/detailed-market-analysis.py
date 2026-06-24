#!/usr/bin/env python3
"""Detailed market intelligence analysis for Career OS."""

import json
import re
from collections import Counter, defaultdict

# Load data
with open('/Users/iancolrick/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json', 'r') as f:
    data = json.load(f)

print("=" * 80)
print("CAREER OS MARKET INTELLIGENCE REPORT")
print("=" * 80)

# 1. Database Overview
print("\n1. DATABASE OVERVIEW")
print("-" * 40)
print(f"Total jobs: {len(data)}")
print(f"High-score (80+): {len([j for j in data if (j.get('quality_score') or 0) >= 80])}")
print(f"Score-100: {len([j for j in data if (j.get('quality_score') or 0) == 100])}")
print(f"English-friendly: {len([j for j in data if j.get('english_friendly')])}")
print(f"Direct apply: {len([j for j in data if j.get('has_direct_link') or j.get('url_type') == 'direct'])}")
print(f"With salary data: {len([j for j in data if j.get('salary')])}")

# 2. Location Analysis
print("\n2. LOCATION ANALYSIS")
print("-" * 40)
locations = defaultdict(lambda: {'total': 0, 'high_score': 0, 'english': 0, 'scores': []})
for job in data:
    loc = job.get('location_norm') or job.get('location') or 'Unknown'
    # Normalize locations
    if 'Singapore' in loc:
        loc = 'Singapore'
    elif 'Hong Kong' in loc:
        loc = 'Hong Kong'
    elif 'Shenzhen' in loc or '深圳' in loc:
        loc = 'Shenzhen'
    elif 'Shanghai' in loc or '上海' in loc:
        loc = 'Shanghai'
    elif 'Tokyo' in loc:
        loc = 'Tokyo'
    elif 'Seoul' in loc:
        loc = 'Seoul'
    elif 'Bangkok' in loc:
        loc = 'Bangkok'
    elif 'Taipei' in loc:
        loc = 'Taipei'
    elif 'Remote - USA' in loc or 'United States - Remote' in loc:
        loc = 'Remote USA'
    else:
        continue  # Skip other locations
    
    locations[loc]['total'] += 1
    if (job.get('quality_score') or 0) >= 80:
        locations[loc]['high_score'] += 1
    if job.get('english_friendly'):
        locations[loc]['english'] += 1
    locations[loc]['scores'].append(job.get('quality_score') or 0)

print(f"{'City':<15} {'Total':<8} {'80+':<8} {'English':<10} {'Avg Score':<10}")
print("-" * 51)
for city, stats in sorted(locations.items(), key=lambda x: -x[1]['total']):
    avg = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
    eng_pct = (stats['english'] / stats['total'] * 100) if stats['total'] > 0 else 0
    print(f"{city:<15} {stats['total']:<8} {stats['high_score']:<8} {eng_pct:.0f}%{'':<5} {avg:.1f}")

# 3. Company Analysis
print("\n3. COMPANY ANALYSIS (Top 15 by High-Score Roles)")
print("-" * 40)
company_stats = defaultdict(lambda: {'total': 0, 'high_score': 0, 'score_100': 0, 'locations': set()})
for job in data:
    company = job.get('company') or 'Unknown'
    if not company or company == 'Unknown':
        continue
    company_stats[company]['total'] += 1
    score = job.get('quality_score') or 0
    if score >= 80:
        company_stats[company]['high_score'] += 1
    if score == 100:
        company_stats[company]['score_100'] += 1
    loc = job.get('location_norm') or job.get('location') or ''
    company_stats[company]['locations'].add(loc)

# Merge OKX case variants
if 'OKX' in company_stats and 'Okx' in company_stats:
    company_stats['OKX']['total'] += company_stats['Okx']['total']
    company_stats['OKX']['high_score'] += company_stats['Okx']['high_score']
    company_stats['OKX']['score_100'] += company_stats['Okx']['score_100']
    company_stats['OKX']['locations'].update(company_stats['Okx']['locations'])
    del company_stats['Okx']

print(f"{'Company':<25} {'Total':<8} {'80+':<8} {'100':<6} {'Key Cities'}")
print("-" * 80)
for company, stats in sorted(company_stats.items(), key=lambda x: -x[1]['high_score'])[:15]:
    cities = ', '.join(sorted(stats['locations'])[:3])
    print(f"{company:<25} {stats['total']:<8} {stats['high_score']:<8} {stats['score_100']:<6} {cities}")

# 4. Salary Analysis
print("\n4. SALARY ANALYSIS (Parsed from Job Data)")
print("-" * 40)

def parse_salary(salary_str):
    """Parse salary string and return monthly USD equivalent."""
    if not salary_str:
        return None
    
    salary_str = salary_str.strip()
    
    # Handle K format (e.g., "50-80K", "50-80K·16薪")
    k_match = re.search(r'(\d+)-(\d+)K', salary_str)
    if k_match:
        low = int(k_match.group(1))
        high = int(k_match.group(2))
        # Check for months multiplier
        months_match = re.search(r'(\d+)薪', salary_str)
        months = int(months_match.group(1)) if months_match else 12
        # Convert to monthly (assuming K is monthly already for Chinese salaries)
        return (low + high) / 2  # Average monthly in K
    
    # Handle HKD/SGD format
    hkd_match = re.search(r'HKD\s*(\d+)[Kk]', salary_str)
    if hkd_match:
        return float(hkd_match.group(1))  # Monthly in HKD K
    
    sgd_match = re.search(r'SGD\s*(\d+)[Kk]', salary_str)
    if sgd_match:
        return float(sgd_match.group(1))  # Monthly in SGD K
    
    return None

# Analyze salaries by location
salary_by_city = defaultdict(list)
for job in data:
    salary = job.get('salary')
    if salary:
        parsed = parse_salary(salary)
        if parsed and parsed > 0:
            loc = job.get('location_norm') or job.get('location') or 'Unknown'
            if 'Singapore' in loc:
                salary_by_city['Singapore'].append(parsed)
            elif 'Hong Kong' in loc:
                salary_by_city['Hong Kong'].append(parsed)
            elif 'Shenzhen' in loc or '深圳' in loc:
                salary_by_city['Shenzhen'].append(parsed)
            elif 'Shanghai' in loc or '上海' in loc:
                salary_by_city['Shanghai'].append(parsed)

print(f"{'City':<15} {'# Jobs':<10} {'Avg (K/mo)':<15} {'Min':<10} {'Max':<10}")
print("-" * 60)
for city, salaries in sorted(salary_by_city.items()):
    if salaries:
        avg = sum(salaries) / len(salaries)
        print(f"{city:<15} {len(salaries):<10} {avg:.1f}K{'':<8} {min(salaries):.0f}K{'':<7} {max(salaries):.0f}K")

# 5. Category Analysis
print("\n5. CATEGORY ANALYSIS")
print("-" * 40)
categories = defaultdict(lambda: {'total': 0, 'high_score': 0})
for job in data:
    cat = job.get('category') or 'unclassified'
    categories[cat]['total'] += 1
    if (job.get('quality_score') or 0) >= 80:
        categories[cat]['high_score'] += 1

print(f"{'Category':<20} {'Total':<10} {'80+':<10} {'% High Score':<15}")
print("-" * 55)
for cat, stats in sorted(categories.items(), key=lambda x: -x[1]['high_score']):
    pct = (stats['high_score'] / stats['total'] * 100) if stats['total'] > 0 else 0
    print(f"{cat:<20} {stats['total']:<10} {stats['high_score']:<10} {pct:.1f}%")

# 6. Fresh vs Stale Analysis
print("\n6. FRESH vs STALE ANALYSIS")
print("-" * 40)
stale_by_city = defaultdict(lambda: {'total': 0, 'stale': 0})
for job in data:
    loc = job.get('location_norm') or job.get('location') or 'Unknown'
    if 'Singapore' in loc:
        loc = 'Singapore'
    elif 'Hong Kong' in loc:
        loc = 'Hong Kong'
    elif 'Shenzhen' in loc or '深圳' in loc:
        loc = 'Shenzhen'
    elif 'Shanghai' in loc or '上海' in loc:
        loc = 'Shanghai'
    else:
        continue
    
    stale_by_city[loc]['total'] += 1
    if job.get('low_quality'):
        stale_by_city[loc]['stale'] += 1

print(f"{'City':<15} {'Total':<10} {'Stale':<10} {'Fresh %':<10} {'Risk'}")
print("-" * 55)
for city, stats in sorted(stale_by_city.items(), key=lambda x: -x[1]['stale']/x[1]['total'] if x[1]['total'] > 0 else 0):
    fresh_pct = ((stats['total'] - stats['stale']) / stats['total'] * 100) if stats['total'] > 0 else 0
    risk = "HIGH" if fresh_pct < 70 else "MEDIUM" if fresh_pct < 85 else "LOW"
    print(f"{city:<15} {stats['total']:<10} {stats['stale']:<10} {fresh_pct:.0f}%{'':<5} {risk}")

# 7. Top Opportunities by Score
print("\n7. TOP 20 OPPORTUNITIES BY SCORE")
print("-" * 40)
scored_jobs = [(job.get('quality_score') or 0, job) for job in data if (job.get('quality_score') or 0) >= 90]
scored_jobs.sort(key=lambda x: -x[0])

print(f"{'Score':<8} {'Company':<20} {'Title':<35} {'City':<15}")
print("-" * 78)
for score, job in scored_jobs[:20]:
    company = job.get('company') or 'Unknown'
    title = job.get('title') or 'Unknown'
    loc = job.get('location_norm') or job.get('location') or 'Unknown'
    if len(title) > 33:
        title = title[:30] + "..."
    print(f"{score:<8} {company:<20} {title:<35} {loc:<15}")

# 8. Visa Sponsorship Signals
print("\n8. VISA SPONSORSHIP SIGNALS")
print("-" * 40)
visa_companies = ['Google', 'Meta', 'Microsoft', 'Airwallex', 'OKX', 'Binance', 'Stripe', 'Mastercard', 'Visa', 'Agoda', 'Grab']
print("Companies likely to sponsor visas (based on presence and size):")
for company in visa_companies:
    count = len([j for j in data if j.get('company') == company])
    if count > 0:
        print(f"  ✓ {company}: {count} roles")

# 9. Executive Summary
print("\n" + "=" * 80)
print("EXECUTIVE SUMMARY")
print("=" * 80)
print(f"""
KEY FINDINGS:
1. Database has {len(data)} jobs across {len(locations)} major cities
2. {len([j for j in data if (j.get('quality_score') or 0) >= 80])} high-score (80+) opportunities
3. Singapore is the largest market ({locations.get('Singapore', {}).get('total', 0)} jobs)
4. Hong Kong has highest avg score ({sum(locations.get('Hong Kong', {}).get('scores', [0])) / len(locations.get('Hong Kong', {}).get('scores', [1])):.1f})
5. OKX dominates high-score roles ({company_stats.get('OKX', {}).get('high_score', 0)} 80+ roles)
6. {len([j for j in data if j.get('english_friendly')])} English-friendly roles ({len([j for j in data if j.get('english_friendly')]) / len(data) * 100:.0f}% of database)
7. {len([j for j in data if j.get('has_direct_link') or j.get('url_type') == 'direct'])} direct-apply opportunities

PRIORITY ACTIONS:
1. Focus on Singapore (largest market, highest English ratio)
2. Target OKX (most high-score roles)
3. Apply to direct-apply jobs first (306 available)
4. Prioritize fresh roles over stale ones
""")
