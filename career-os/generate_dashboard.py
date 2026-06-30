#!/usr/bin/env python3
"""Generate dashboard.json from jobs-all.json"""
import json
from datetime import datetime, timezone
from pathlib import Path

# Load jobs
jobs_path = Path("OKComputer_职位搜索清单/jobs-all.json")
with open(jobs_path, 'r', encoding='utf-8') as f:
    jobs = json.load(f)

# Stats
total = len(jobs)

# Count by location
loc_counts = {}
for j in jobs:
    loc = j.get('location', '') or j.get('location_norm', '') or 'Unknown'
    loc_norm = loc.upper().replace(' ', '')
    if 'SHENZHEN' in loc_norm or '深圳' in loc:
        loc_key = 'SZ'
    elif 'HONGKONG' in loc_norm or '香港' in loc:
        loc_key = 'HK'
    elif 'GUANGZHOU' in loc_norm or '广州' in loc:
        loc_key = 'GZ'
    elif 'SHANGHAI' in loc_norm or '上海' in loc:
        loc_key = 'SH'
    elif 'SINGAPORE' in loc_norm or '新加坡' in loc:
        loc_key = 'SG'
    else:
        loc_key = loc[:20] if loc else 'Unknown'
    loc_counts[loc_key] = loc_counts.get(loc_key, 0) + 1

# Count by category
cat_counts = {}
for j in jobs:
    cat = j.get('category', 'Unknown')
    cat_counts[cat] = cat_counts.get(cat, 0) + 1

# Top 5 by quality_score
scored = []
for j in jobs:
    s = j.get('quality_score', 0) or 0
    try:
        s = float(s)
    except:
        s = 0
    scored.append((s, j))
scored.sort(key=lambda x: x[0], reverse=True)
top5 = []
for s, j in scored[:5]:
    top5.append({
        'title': j.get('title', 'N/A'),
        'company': j.get('company', 'N/A'),
        'location': j.get('location', 'N/A'),
        'quality_score': s,
        'quality_tier': j.get('quality_tier', ''),
        'role_type': j.get('role_type', ''),
        'url': j.get('url', '')
    })

dashboard = {
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'stats': {
        'total_jobs': total,
        'by_location': loc_counts,
        'by_category': cat_counts
    },
    'top_5_jobs': top5,
    'category_counts': cat_counts
}

# Write output
output_path = Path("docs/data/dashboard.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(dashboard, f, ensure_ascii=False, indent=2)

print(f"Dashboard generated: {output_path}")
print(f"Total jobs: {total}")
print(f"Locations: {loc_counts}")
print(f"Categories: {cat_counts}")
print(f"Top 5: {[t['title'] for t in top5]}")
