#!/usr/bin/env python3
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOBS_FILE = ROOT / "OKComputer_职位搜索清单" / "jobs-all.json"
OUT_FILE = ROOT / "docs" / "data" / "dashboard.json"

def normalize_loc(loc):
    if not loc:
        return "Unknown"
    loc = str(loc).strip().lower()
    if "shenzhen" in loc or "深圳" in loc:
        return "SZ"
    if "hong kong" in loc or "hk" in loc or "香港" in loc:
        return "HK"
    if "guangzhou" in loc or "广州" in loc:
        return "GZ"
    if "shanghai" in loc or "上海" in loc:
        return "SH"
    if "singapore" in loc or "sg" in loc or "新加坡" in loc:
        return "SG"
    if "remote" in loc:
        return "Remote"
    return "Other"

def category_bucket(cat, role_type=None):
    cat = str(cat or "").lower()
    role_type = str(role_type or "").lower()
    if cat in ("product", "product_management", "general_pm", "ai_product", "senior_pm", "fintech", "other") or "product" in cat or "product" in role_type:
        return "PM"
    if cat in ("strategy", "ops", "gm", "cross_border") or "strategy" in cat or "strategy" in role_type:
        return "Strategy"
    if cat in ("growth",) or "growth" in cat or "growth" in role_type:
        return "Growth"
    return "Other"

def main():
    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    total = len(jobs)
    loc_counts = Counter(normalize_loc(j.get("location_norm") or j.get("location", "")) for j in jobs)
    cat_counts = Counter(category_bucket(j.get("category"), j.get("role_type")) for j in jobs)

    def score(j):
        s = j.get("quality_score")
        return int(s) if s is not None and str(s).isdigit() else 0

    top_jobs = sorted(jobs, key=score, reverse=True)[:5]
    top5 = []
    for j in top_jobs:
        top5.append({
            "job_id": j.get("job_id", ""),
            "title": j.get("title", ""),
            "company": j.get("company", ""),
            "location": j.get("location_norm") or j.get("location", ""),
            "category": j.get("category", ""),
            "quality_score": score(j),
            "url": j.get("url", ""),
            "status": j.get("status", ""),
        })

    dashboard = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "total_jobs": total,
            "jobs_by_location": {
                "SZ": loc_counts.get("SZ", 0),
                "HK": loc_counts.get("HK", 0),
                "GZ": loc_counts.get("GZ", 0),
                "SH": loc_counts.get("SH", 0),
                "SG": loc_counts.get("SG", 0),
                "Remote": loc_counts.get("Remote", 0),
                "Other": loc_counts.get("Other", 0),
                "Unknown": loc_counts.get("Unknown", 0),
            },
            "jobs_by_category": {
                "PM": cat_counts.get("PM", 0),
                "Strategy": cat_counts.get("Strategy", 0),
                "Growth": cat_counts.get("Growth", 0),
                "Other": cat_counts.get("Other", 0),
            },
        },
        "top_5_jobs": top5,
        "category_counts": dict(cat_counts.most_common()),
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, ensure_ascii=False, indent=2)

    print(f"Wrote {OUT_FILE}")
    print(f"Total jobs: {total}")
    print(f"Top score: {top5[0]['quality_score'] if top5 else 'N/A'}")

if __name__ == "__main__":
    main()
