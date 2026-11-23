#!/usr/bin/env python3
"""Generate docs/data/dashboard.json from OKComputer_职位搜索清单/jobs-all.json."""
import json
from datetime import datetime, timezone
from collections import Counter

JOBS_PATH = "OKComputer_职位搜索清单/jobs-all.json"
OUT_PATH = "docs/data/dashboard.json"

# Location normalization mapping to canonical buckets
LOCATION_MAP = {
    "SZ": ["shenzhen", "深圳", "sz"],
    "HK": ["hong kong", "香港", "hk"],
    "GZ": ["guangzhou", "广州", "gz"],
    "SH": ["shanghai", "上海", "sh"],
    "SG": ["singapore", "新加坡", "sg"],
}

# Category mapping: PM / Strategy / Growth
PM_KEYWORDS = ["product", "pm", "产品", "product manager", "product management", "product lead", "product owner", "product director"]
STRATEGY_KEYWORDS = ["strategy", "strategic", "战略", "corporate development", "bizops", "business operations", "strategy/ops"]
GROWTH_KEYWORDS = ["growth", "增长", "growth manager", "growth lead", "growth hacker", "marketing", "seo", "performance marketing"]


def norm_location(loc):
    if not loc:
        return "Other"
    loc_l = loc.lower()
    for canon, aliases in LOCATION_MAP.items():
        for alias in aliases:
            if alias in loc_l:
                return canon
    return "Other"


def norm_category(job):
    # Prefer existing category field if it is one of the three
    cat = (job.get("category") or "").lower()
    role = (job.get("role_type") or "").lower()
    title = (job.get("title") or "").lower()
    text = f"{cat} {role} {title}"

    if any(k in text for k in GROWTH_KEYWORDS):
        return "Growth"
    if any(k in text for k in STRATEGY_KEYWORDS):
        return "Strategy"
    if any(k in text for k in PM_KEYWORDS) or cat == "pm":
        return "PM"
    return "Other"


def main():
    with open(JOBS_PATH) as f:
        jobs = json.load(f)

    loc_counter = Counter()
    cat_counter = Counter()
    for j in jobs:
        loc_counter[norm_location(j.get("location") or j.get("location_norm") or "")] += 1
        cat_counter[norm_category(j)] += 1

    # Top 5 by quality_score
    def score(j):
        s = j.get("quality_score")
        return s if isinstance(s, (int, float)) else 0

    top5 = sorted(jobs, key=score, reverse=True)[:5]
    top5_out = [
        {
            "title": j.get("title", ""),
            "company": j.get("company", ""),
            "location": j.get("location", ""),
            "quality_score": j.get("quality_score"),
            "quality_tier": j.get("quality_tier", ""),
            "role_type": j.get("role_type", ""),
            "url": j.get("url", ""),
        }
        for j in top5
    ]

    dashboard = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "total_jobs": len(jobs),
            "jobs_by_location": {
                "SZ": loc_counter.get("SZ", 0),
                "HK": loc_counter.get("HK", 0),
                "GZ": loc_counter.get("GZ", 0),
                "SH": loc_counter.get("SH", 0),
                "SG": loc_counter.get("SG", 0),
            },
            "jobs_by_category": {
                "PM": cat_counter.get("PM", 0),
                "Strategy": cat_counter.get("Strategy", 0),
                "Growth": cat_counter.get("Growth", 0),
            },
        },
        "top_5_jobs": top5_out,
        "category_counts": {
            "PM": cat_counter.get("PM", 0),
            "Strategy": cat_counter.get("Strategy", 0),
            "Growth": cat_counter.get("Growth", 0),
            "Other": cat_counter.get("Other", 0),
        },
    }

    with open(OUT_PATH, "w") as f:
        json.dump(dashboard, f, ensure_ascii=False, indent=2)

    print(f"Wrote {OUT_PATH}")
    print(json.dumps(dashboard["stats"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
