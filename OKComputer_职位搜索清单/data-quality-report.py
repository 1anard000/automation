#!/usr/bin/env python3
"""Data Quality Report — scans jobs-all.json and outputs a quality scorecard.

Usage: python3 data-quality-report.py [--json]
"""
import json
import sys
from collections import Counter
from datetime import datetime, timedelta

def main():
    json_mode = "--json" in sys.argv
    with open("jobs-all.json") as f:
        jobs = json.load(f)

    report = {}
    report["total_jobs"] = len(jobs)

    # Field completeness
    fields = ["title", "company", "location", "salary", "url", "source", "scanned_date"]
    field_stats = {}
    for field in fields:
        filled = sum(1 for j in jobs if j.get(field))
        pct = round(100 * filled / len(jobs), 1) if jobs else 0
        field_stats[field] = {"filled": filled, "missing": len(jobs) - filled, "pct": pct}
    report["field_completeness"] = field_stats

    # Source distribution
    sources = Counter(j.get("source", "unknown") for j in jobs)
    report["sources"] = dict(sources.most_common(20))
    report["source_count"] = len(sources)

    # Duplicate check
    seen = set()
    dupes = []
    for j in jobs:
        key = (j.get("title", "").strip().lower(), j.get("company", "").strip().lower())
        if key in seen:
            dupes.append(key)
        seen.add(key)
    report["duplicates"] = len(dupes)

    # Freshness
    has_date = 0
    stale_30d = 0
    stale_60d = 0
    now = datetime.now()
    for j in jobs:
        ds = j.get("date") or j.get("posted") or j.get("scan_date") or ""
        if ds:
            has_date += 1
            try:
                d = datetime.fromisoformat(ds.replace("Z", "").replace("+00:00", "").split(" ")[0])
                if d < now - timedelta(days=30):
                    stale_30d += 1
                if d < now - timedelta(days=60):
                    stale_60d += 1
            except Exception:
                pass
    report["freshness"] = {
        "with_date": has_date,
        "without_date": len(jobs) - has_date,
        "stale_30d": stale_30d,
        "stale_60d": stale_60d,
    }

    # Grade distribution
    grades = Counter(j.get("grade", "ungraded") for j in jobs)
    report["grade_distribution"] = dict(grades.most_common())

    # Company concentration
    companies = Counter(j.get("company", "unknown") for j in jobs)
    top5 = companies.most_common(5)
    report["top_companies"] = {c: n for c, n in top5}
    report["unique_companies"] = len(companies)

    # Quality score (0-10)
    score = 10
    for f in ["title", "company", "salary", "url", "source"]:
        pct = field_stats[f]["pct"]
        if pct < 50:
            score -= 2
        elif pct < 80:
            score -= 1
    if report["duplicates"] > 0:
        score -= 1
    if has_date < len(jobs) * 0.3:
        score -= 1
    report["quality_score"] = max(0, score)

    # Top issues
    issues = []
    if field_stats["salary"]["pct"] < 50:
        issues.append(f"Salary missing for {field_stats['salary']['missing']} jobs ({field_stats['salary']['pct']}% filled)")
    if field_stats["scanned_date"]["pct"] < 50:
        issues.append(f"Date missing for {field_stats['scanned_date']['missing']} jobs ({field_stats['scanned_date']['pct']}% filled)")
    if field_stats["company"]["pct"] < 90:
        issues.append(f"Company missing for {field_stats['company']['missing']} jobs")
    if report["duplicates"] > 0:
        issues.append(f"{report['duplicates']} duplicate jobs found")
    report["top_issues"] = issues

    if json_mode:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("=" * 50)
        print("  DATA QUALITY REPORT")
        print("=" * 50)
        print(f"\n  Total Jobs: {report['total_jobs']}")
        print(f"  Quality Score: {report['quality_score']}/10")
        print(f"  Sources: {report['source_count']}")
        print(f"  Companies: {report['unique_companies']}")
        print(f"  Duplicates: {report['duplicates']}")
        print(f"\n  Field Completeness:")
        for f in fields:
            s = field_stats[f]
            bar = "█" * int(s["pct"] / 5) + "░" * (20 - int(s["pct"] / 5))
            print(f"    {f:10s} {bar} {s['pct']}% ({s['missing']} missing)")
        print(f"\n  Grade Distribution:")
        for g, c in sorted(grades.items()):
            print(f"    {g:12s} {c}")
        print(f"\n  Top Issues:")
        for issue in issues:
            print(f"    ⚠  {issue}")
        print()

if __name__ == "__main__":
    main()
