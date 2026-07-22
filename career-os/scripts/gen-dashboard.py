#!/usr/bin/env python3
"""Generate docs/data/dashboard.json from jobs-all.json"""
import json
import os
from collections import Counter
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOBS_PATH = os.path.join(BASE, 'OKComputer_职位搜索清单', 'jobs-all.json')
OUT_DIR = os.path.join(BASE, 'docs', 'data')
OUT_PATH = os.path.join(OUT_DIR, 'dashboard.json')

with open(JOBS_PATH) as f:
    jobs = json.load(f)

total = len(jobs)

# Location normalization
loc_counter = Counter()
for j in jobs:
    loc = j.get('location_norm', '') or j.get('location', '') or ''
    loc_lower = loc.strip().lower()
    if 'shenzhen' in loc_lower or '深圳' in loc_lower:
        loc_norm = 'Shenzhen (SZ)'
    elif 'hong kong' in loc_lower or '香港' in loc_lower:
        loc_norm = 'Hong Kong (HK)'
    elif 'guangzhou' in loc_lower or '广州' in loc_lower:
        loc_norm = 'Guangzhou (GZ)'
    elif 'shanghai' in loc_lower or '上海' in loc_lower:
        loc_norm = 'Shanghai (SH)'
    elif 'singapore' in loc_lower:
        loc_norm = 'Singapore (SG)'
    elif 'remote' in loc_lower:
        loc_norm = 'Remote'
    elif loc.strip() == '':
        loc_norm = 'Unknown'
    else:
        loc_norm = loc.strip()
    loc_counter[loc_norm] += 1

# Category normalization
cat_counter = Counter()
for j in jobs:
    cat = j.get('category', '') or j.get('role_type', '') or 'unknown'
    cat_lower = cat.strip().lower()
    if 'product' in cat_lower or 'pm' in cat_lower or cat_lower == 'general_pm':
        cat_norm = 'Product Management'
    elif 'strategy' in cat_lower or 'ops' in cat_lower:
        cat_norm = 'Strategy'
    elif 'growth' in cat_lower:
        cat_norm = 'Growth'
    elif 'fintech' in cat_lower:
        cat_norm = 'Fintech'
    else:
        cat_norm = cat.strip()
    cat_counter[cat_norm] += 1

# Top 5 by quality_score (descending)
scored = [j for j in jobs if j.get('quality_score') is not None]
scored.sort(key=lambda x: x['quality_score'], reverse=True)
top5 = []
for j in scored[:5]:
    top5.append({
        'title': j.get('en_title') or j.get('title', ''),
        'company': j.get('company', ''),
        'location': j.get('location_norm') or j.get('location', ''),
        'quality_score': j['quality_score'],
        'category': j.get('category', ''),
        'job_id': j.get('job_id', ''),
        'url': j.get('url', '')
    })

dashboard = {
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'stats': {
        'total_jobs': total,
        'jobs_by_location': dict(loc_counter.most_common()),
        'jobs_by_category': dict(cat_counter.most_common())
    },
    'top_5_scored_jobs': top5,
    'category_counts': dict(cat_counter.most_common())
}

os.makedirs(OUT_DIR, exist_ok=True)
with open(OUT_PATH, 'w') as f:
    json.dump(dashboard, f, indent=2, ensure_ascii=False)

print(f"Dashboard written to {OUT_PATH}")
print(f"Total jobs: {total}")
print(f"Locations: {dict(loc_counter.most_common())}")
print(f"Categories: {dict(cat_counter.most_common())}")
print(f"Top 5 scored:")
for t in top5:
    print(f"  [{t['quality_score']}] {t['title']} @ {t['company']}")
