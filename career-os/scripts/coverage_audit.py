#!/usr/bin/env python3
"""
Coverage audit for the career job database.
Reads OKComputer_职位搜索清单/jobs-all.json and writes
OKComputer_职位搜索清单/coverage-report.json with company/source/distribution stats.
Outputs a concise coverage score estimate to stdout when run from CLI.
"""

import json
import os
import collections
import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2] / "OKComputer_职位搜索清单"
JOBS_PATH = BASE_DIR / "jobs-all.json"
REPORT_PATH = BASE_DIR / "coverage-report.json"


def load_jobs():
    if not JOBS_PATH.exists():
        raise SystemExit(f"Missing {JOBS_PATH}")
    with JOBS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def clean_value(value):
    return (value or "").strip().lower() or "empty"


def build_report(jobs):
    total = len(jobs)
    source_counter = collections.Counter(clean_value(job.get("source")) for job in jobs)
    company_counter = collections.Counter(
        (job.get("company") or "").strip() for job in jobs
    )
    location_counter = collections.Counter(
        (job.get("location") or "").strip() or "Unspecified" for job in jobs
    )
    role_counter = collections.Counter(
        (job.get("role_type") or "").strip().lower() or "unspecified" for job in jobs
    )
    grade_counter = collections.Counter(
        (job.get("grade") or "").strip().upper() or "Unspecified" for job in jobs
    )

    unique_companies = len(company_counter)
    top_companies = company_counter.most_common(15)
    concentrated = sum(c for _, c in top_companies) / max(total, 1)

    new_source_names = {
        "linkedin",
        "company_site",
        "ashby",
        "greenhouse",
        "linkedin_search",
        "linkedin_posting",
        "indeed",
        "jobsdb",
        "glassdoor",
        "wellfound",
        "builtin",
        "cryptojobslist",
        "jobs-radar",
    }
    new_sources_present = sum(1 for source, count in source_counter.items() if source in new_source_names)

    source_coverage_penalty = 0
    if not source_counter:
        source_coverage_penalty = 4
    else:
        if sum(source_counter.get(name, 0) for name in ["indeed", "glassdoor", "jobsdb"]) < 10:
            source_coverage_penalty += 2
        if source_counter.get("linkedin_search", 0) < 10:
            source_coverage_penalty += 1
        if source_counter.get("builtin", 0) < 5:
            source_coverage_penalty += 1
        if source_counter.get("wellfound", 0) < 5:
            source_coverage_penalty += 1

    score = 10 - source_coverage_penalty
    score = max(0, min(10, score))

    report = {
        "report_date": datetime.date.today().isoformat(),
        "total_jobs": total,
        "unique_companies": unique_companies,
        "source_breakdown": dict(source_counter.most_common()),
        "top_companies": top_companies,
        "location_breakdown": dict(location_counter.most_common()),
        "role_breakdown": dict(role_counter.most_common()),
        "grade_breakdown": dict(grade_counter.most_common()),
        "concentration_in_top_companies": concentrated,
        "new_source_count": new_sources_present,
        "coverage_score": score,
    }

    return report


def write_report(report):
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return REPORT_PATH


def main():
    jobs = load_jobs()
    report = build_report(jobs)
    report_path = write_report(report)

    print(f"Coverage audit complete: total_jobs={report['total_jobs']}")
    print(f"Unique companies: {report['unique_companies']}")
    print(f"Top companies: {[name for name, _ in report['top_companies']]}")
    print(f"Source breakdown: {report['source_breakdown']}")
    print(f"Coverage score estimate: {report['coverage_score']}/10")
    print(f"Report written: {report_path}")


if __name__ == "__main__":
    main()
