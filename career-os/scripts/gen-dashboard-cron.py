#!/usr/bin/env python3
"""Generate docs/data/dashboard.json from jobs-all.json."""
import json
from datetime import datetime, timezone
from collections import Counter

BASE = "/Users/iancolrick/.openclaw/workspace/career-os"

with open(f"{BASE}/OKComputer_职位搜索清单/jobs-all.json") as f:
    jobs = json.load(f)

def loc_bucket(loc):
    l = (loc or "").lower()
    if "shenzhen" in l or "深圳" in l:
        return "SZ"
    if "hong kong" in l or "香港" in l:
        return "HK"
    if "guangzhou" in l or "广州" in l:
        return "GZ"
    if "shanghai" in l or "上海" in l:
        return "SH"
    if "singapore" in l or "新加坡" in l:
        return "SG"
    return "Other"

def cat_bucket(cat, role_type=""):
    c = (cat or "").lower()
    r = (role_type or "").lower()
    if c in ("general_pm", "product", "product_management", "senior_pm", "ai_product", "platform") or "product" in r:
        return "PM"
    if c in ("strategy", "vc_pe") or "strategy" in r:
        return "Strategy"
    if c in ("growth",) or "growth" in r:
        return "Growth"
    return "Other"

loc_counts = Counter(loc_bucket(j.get("location_norm") or j.get("location")) for j in jobs)
cat_counts = Counter(cat_bucket(j.get("category"), j.get("role_type")) for j in jobs)

# Top 5 by quality_score (fallback to 0)
def score(j):
    try:
        return int(j.get("quality_score") or 0)
    except (ValueError, TypeError):
        return 0

top5 = sorted(jobs, key=score, reverse=True)[:5]
top5_out = [
    {
        "title": j.get("title", ""),
        "company": j.get("company", ""),
        "location": j.get("location_norm") or j.get("location", ""),
        "category": j.get("category", ""),
        "quality_score": score(j),
        "quality_tier": j.get("quality_tier", ""),
        "url": j.get("url", ""),
        "job_id": j.get("job_id", ""),
        "status": j.get("status", ""),
    }
    for j in top5
]

dashboard = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "stats": {
        "total_jobs": len(jobs),
        "jobs_by_location": {k: loc_counts.get(k, 0) for k in ["SZ", "HK", "GZ", "SH", "SG", "Other"]},
        "jobs_by_category": {k: cat_counts.get(k, 0) for k in ["PM", "Strategy", "Growth", "Other"]},
    },
    "top_5_highest_scored": top5_out,
    "category_counts": dict(Counter(j.get("category") or "unknown" for j in jobs)),
}

import os
os.makedirs(f"{BASE}/docs/data", exist_ok=True)
with open(f"{BASE}/docs/data/dashboard.json", "w") as f:
    json.dump(dashboard, f, indent=2, ensure_ascii=False)

print(json.dumps(dashboard["stats"], indent=2))
print("top5:", [t["title"][:40] for t in top5_out])
print("Wrote docs/data/dashboard.json")
