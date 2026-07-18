#!/usr/bin/env python3
"""Build dashboard.json from jobs-all.json"""
import json
from datetime import datetime, timezone
from collections import Counter

JOBS_PATH = "OKComputer_职位搜索清单/jobs-all.json"
OUT_PATH = "docs/data/dashboard.json"

with open(JOBS_PATH, "r", encoding="utf-8") as f:
    jobs = json.load(f)

total = len(jobs)

# Location normalization
def norm_location(loc):
    if not loc:
        return "Unknown"
    l = loc.lower()
    if any(x in l for x in ["shenzhen", "深圳"]):
        return "SZ"
    if any(x in l for x in ["hong kong", "hk", "香港"]):
        return "HK"
    if any(x in l for x in ["guangzhou", "广州", "gz"]):
        return "GZ"
    if any(x in l for x in ["shanghai", "上海", "sh"]):
        return "SH"
    if any(x in l for x in ["singapore", "sg"]):
        return "SG"
    if any(x in l for x in ["bangkok"]):
        return "BKK"
    if any(x in l for x in ["remote"]):
        return "Remote"
    return "Other"

# Category normalization
def norm_category(cat, role_type):
    if cat:
        c = cat.lower()
        if "product" in c:
            return "PM"
        if "strategy" in c:
            return "Strategy"
        if "growth" in c:
            return "Growth"
        if "fintech" in c:
            return "Fintech"
        if "general_pm" in c:
            return "PM"
    if role_type:
        r = role_type.lower()
        if "product" in r:
            return "PM"
        if "strategy" in r:
            return "Strategy"
        if "growth" in r:
            return "Growth"
    return "Other"

loc_counter = Counter()
cat_counter = Counter()
scored_jobs = []

for j in jobs:
    loc = norm_location(j.get("location_norm", "") or j.get("location", ""))
    loc_counter[loc] += 1
    
    cat = norm_category(j.get("category", ""), j.get("role_type", ""))
    cat_counter[cat] += 1
    
    score = j.get("quality_score")
    if score is not None:
        scored_jobs.append({
            "title": j.get("title", ""),
            "company": j.get("company", ""),
            "location": j.get("location", ""),
            "score": score,
            "quality_tier": j.get("quality_tier", ""),
            "category": cat,
            "job_id": j.get("job_id", ""),
            "url": j.get("url", ""),
        })

# Top 5 by score
scored_jobs.sort(key=lambda x: x["score"], reverse=True)
top5 = scored_jobs[:5]

dashboard = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "stats": {
        "total_jobs": total,
        "jobs_by_location": dict(loc_counter.most_common()),
        "jobs_by_category": dict(cat_counter.most_common()),
    },
    "top_5_scored_jobs": top5,
    "category_counts": dict(cat_counter.most_common()),
}

import os
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(dashboard, f, indent=2, ensure_ascii=False)

print(f"Dashboard built: {OUT_PATH}")
print(f"  Total jobs: {total}")
print(f"  By location: {dict(loc_counter.most_common())}")
print(f"  By category: {dict(cat_counter.most_common())}")
titles = [t["title"][:50] + " (" + str(t["score"]) + ")" for t in top5]
print(f"  Top 5 scored: {titles}")
