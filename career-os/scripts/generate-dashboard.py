#!/usr/bin/env python3
"""Generate docs/data/dashboard.json from jobs-all.json."""

import json
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

BASE = Path(__file__).resolve().parents[1]
JOBS_FILE = BASE / "OKComputer_职位搜索清单" / "jobs-all.json"
OUT_FILE = BASE / "docs" / "data" / "dashboard.json"


def normalize_location(loc):
    loc = (loc or "").lower()
    if "shenzhen" in loc or "深圳" in loc or "sz" in loc:
        return "SZ"
    if "hong kong" in loc or "hk" in loc or "香港" in loc:
        return "HK"
    if "guangzhou" in loc or "广州" in loc or "gz" in loc:
        return "GZ"
    if "shanghai" in loc or "上海" in loc or "sh" in loc:
        return "SH"
    if "singapore" in loc or "sg" in loc or "新加坡" in loc:
        return "SG"
    return "Other"


def categorize(job):
    title = (job.get("title") or "").lower()
    role = (job.get("role_type") or "").lower()
    text = f"{title} {role}"
    if "product" in text or "产品" in text or "pm" in text:
        return "PM"
    if "strategy" in text or "战略" in text or "strategic" in text:
        return "Strategy"
    if "growth" in text or "增长" in text:
        return "Growth"
    return "Other"


def main():
    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    total = len(jobs)
    locations = Counter(normalize_location(j.get("location_norm") or j.get("location", "")) for j in jobs)
    categories = Counter(categorize(j) for j in jobs)

    def _score(j):
        s = j.get("quality_score")
        return s if isinstance(s, (int, float)) else 0

    top_jobs = sorted(jobs, key=_score, reverse=True)[:5]

    top5 = [
        {
            "job_id": j.get("job_id"),
            "title": j.get("title"),
            "company": j.get("company"),
            "location": j.get("location_norm") or j.get("location"),
            "category": categorize(j),
            "quality_score": j.get("quality_score"),
            "quality_tier": j.get("quality_tier"),
            "url": j.get("url"),
            "status": j.get("status"),
        }
        for j in top_jobs
    ]

    dashboard = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "total_jobs": total,
            "by_location": {
                "SZ": locations.get("SZ", 0),
                "HK": locations.get("HK", 0),
                "GZ": locations.get("GZ", 0),
                "SH": locations.get("SH", 0),
                "SG": locations.get("SG", 0),
                "Other": locations.get("Other", 0),
            },
            "by_category": {
                "PM": categories.get("PM", 0),
                "Strategy": categories.get("Strategy", 0),
                "Growth": categories.get("Growth", 0),
                "Other": categories.get("Other", 0),
            },
        },
        "category_counts": dict(categories),
        "top_jobs": top5,
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, ensure_ascii=False, indent=2)

    print(f"Wrote {OUT_FILE} with {total} jobs")


if __name__ == "__main__":
    main()
