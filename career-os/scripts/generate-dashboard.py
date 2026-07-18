#!/usr/bin/env python3
"""
Generate dashboard.json from the real jobs database.
Reads jobs-all.json, computes stats, and writes docs/data/dashboard.json.
"""
import json, os, re
from datetime import datetime, timedelta

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOBS_FILE = os.path.join(WORKSPACE, "OKComputer_职位搜索清单", "jobs-all.json")
DASHBOARD_FILE = os.path.join(WORKSPACE, "docs", "data", "dashboard.json")

# Blocked sources (inaccessible from China)
BLOCKED_SOURCES = {"linkedin", "glassdoor", "google_careers", "meta_careers"}

# Location normalization
LOC_MAP = {
    "hong kong": "Hong Kong", "hong kong sar": "Hong Kong", "hk": "Hong Kong",
    "shenzhen": "Shenzhen", "sz": "Shenzhen", "深圳": "Shenzhen",
    "guangzhou": "Guangzhou", "gz": "Guangzhou", "广州": "Guangzhou",
    "shanghai": "Shanghai", "sh": "Shanghai", "上海": "Shanghai",
    "singapore": "Singapore", "sg": "Singapore",
    "beijing": "Beijing", "bj": "Beijing", "北京": "Beijing",
}

# Category classification
def classify(title):
    t = title.lower()
    if any(k in t for k in ["product manager", "product director", "head of product",
                             "principal product", "senior product", "staff product"]):
        return "PM"
    if any(k in t for k in ["strategy", "strategic", "business operations", "bizops",
                             "chief of staff", "corporate strategy"]):
        return "Strategy"
    if any(k in t for k in ["growth", "expansion", "general manager", "country manager",
                             "regional manager", "head of growth"]):
        return "Growth"
    if any(k in t for k in ["program manager", "project manager"]):
        return "Program"
    return "Other"


def normalize_location(loc):
    if not loc:
        return ""
    l = loc.lower().strip()
    for pattern, city in LOC_MAP.items():
        if pattern in l:
            return city
    return ""


def is_accessible(job):
    """Check if job is accessible from China."""
    source = job.get("source", "").lower()
    if source in BLOCKED_SOURCES:
        return False
    url = job.get("url", "").lower()
    if "linkedin.com" in url:
        return False
    return True


def main():
    if not os.path.exists(JOBS_FILE):
        print(f"ERROR: {JOBS_FILE} not found")
        return

    with open(JOBS_FILE) as f:
        all_jobs = json.load(f)

    # Filter to accessible jobs only
    jobs = [j for j in all_jobs if is_accessible(j)]
    print(f"Total jobs: {len(all_jobs)}, Accessible from China: {len(jobs)}")

    # Compute stats
    now = datetime.now()
    week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    day_ago = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    by_city = {}
    by_category = {}
    jobs_7d = 0
    jobs_24h = 0

    for j in jobs:
        # Location
        loc = normalize_location(j.get("location", ""))
        if loc:
            by_city[loc] = by_city.get(loc, 0) + 1

        # Category
        cat = classify(j.get("title", ""))
        by_category[cat] = by_category.get(cat, 0) + 1

        # Recency
        scanned = j.get("scanned_date", "")
        if scanned >= week_ago:
            jobs_7d += 1
        if scanned >= day_ago:
            jobs_24h += 1

    # Top 5 highest-scored jobs (by quality_score descending)
    def sort_key(j):
        score = j.get("quality_score") or 0
        return -score  # descending

    top_jobs = sorted(jobs, key=sort_key)[:5]
    top_5 = []
    for j in top_jobs:
        top_5.append({
            "title": j.get("title", ""),
            "company": j.get("company", ""),
            "location": normalize_location(j.get("location", "")),
            "grade": j.get("grade", ""),
            "quality_score": j.get("quality_score"),
            "url": j.get("url", ""),
            "source": j.get("source", ""),
        })

    # Count with direct apply links
    direct_links = sum(1 for j in jobs if j.get("url") and "linkedin.com" not in j.get("url", "").lower())

    dashboard = {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "stats": {
            "total": len(jobs),
            "total_all": len(all_jobs),
            "jobs_last_7d": jobs_7d,
            "jobs_last_24h": jobs_24h,
            "direct_links": direct_links,
        },
        "by_city": dict(sorted(by_city.items(), key=lambda x: -x[1])),
        "by_category": dict(sorted(by_category.items(), key=lambda x: -x[1])),
        "top_5": top_5,
        "category_counts": dict(sorted(by_category.items(), key=lambda x: -x[1])),
        "error": None,
    }

    os.makedirs(os.path.dirname(DASHBOARD_FILE), exist_ok=True)
    with open(DASHBOARD_FILE, "w") as f:
        json.dump(dashboard, f, indent=2, ensure_ascii=False)

    print(f"Dashboard generated: {DASHBOARD_FILE}")
    print(f"  Total: {len(jobs)} accessible jobs (of {len(all_jobs)} total)")
    print(f"  By city: {by_city}")
    print(f"  By category: {by_category}")
    print(f"  Direct links: {direct_links}")


if __name__ == "__main__":
    main()
