#!/usr/bin/env python3
"""Generate dashboard.json from jobs-all.json"""
import json
import os
from datetime import datetime, timezone
from collections import Counter

# Paths
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOBS_FILE = os.path.join(BASE, "OKComputer_职位搜索清单", "jobs-all.json")
OUT_FILE = os.path.join(BASE, "docs", "data", "dashboard.json")

# Load jobs
with open(JOBS_FILE, "r", encoding="utf-8") as f:
    jobs = json.load(f)

total = len(jobs)

# Location mapping
LOCATION_MAP = {
    "Shenzhen": "SZ",
    "Hong Kong": "HK",
    "Guangzhou": "GZ",
    "Shanghai": "SH",
    "Singapore": "SG",
}

def norm_location(loc):
    if not loc:
        return "Other"
    loc_lower = loc.lower()
    for key, short in LOCATION_MAP.items():
        if key.lower() in loc_lower:
            return short
    if "remote" in loc_lower:
        return "Remote"
    return "Other"

# Category mapping
CATEGORY_MAP = {
    "product": "PM",
    "product_management": "PM",
    "general_pm": "PM",
    "senior_pm": "PM",
    "ai_product": "PM",
    "strategy": "Strategy",
    "growth": "Growth",
    "operations": "Ops",
    "ops": "Ops",
    "cross_border": "Cross-border",
    "fintech": "Fintech",
    "gm": "GM",
    "platform": "Platform",
    "program": "Program",
    "general_manager": "GM",
    "vc_pe": "VC/PE",
    "other": "Other",
}

def norm_category(cat):
    if not cat:
        return "Other"
    cat_lower = cat.lower()
    if cat_lower in CATEGORY_MAP:
        return CATEGORY_MAP[cat_lower]
    # Try case-insensitive lookup
    for key, val in CATEGORY_MAP.items():
        if key.lower() == cat_lower:
            return val
    return cat

# Compute stats
location_counts = Counter()
category_counts = Counter()
scored_jobs = []

for job in jobs:
    loc = norm_location(job.get("location_norm") or job.get("location", ""))
    location_counts[loc] += 1
    
    cat = norm_category(job.get("category", ""))
    category_counts[cat] += 1
    
    score = job.get("quality_score")
    if score is not None:
        scored_jobs.append((score, job))

# Top 5 by score
scored_jobs.sort(key=lambda x: x[0], reverse=True)
top5 = []
for score, job in scored_jobs[:5]:
    top5.append({
        "title": job.get("title", ""),
        "company": job.get("company", ""),
        "location": job.get("location", ""),
        "category": job.get("category", ""),
        "quality_score": score,
        "url": job.get("url", ""),
    })

# Build dashboard
dashboard = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "stats": {
        "total_jobs": total,
        "by_location": dict(location_counts.most_common()),
        "by_category": dict(category_counts.most_common()),
    },
    "top_5_jobs": top5,
    "category_counts": dict(category_counts.most_common()),
}

# Ensure output dir
os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)

# Write
with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(dashboard, f, ensure_ascii=False, indent=2)

print(f"Dashboard written to {OUT_FILE}")
print(f"Total jobs: {total}")
print(f"Locations: {dict(location_counts.most_common())}")
print(f"Categories: {dict(category_counts.most_common())}")
