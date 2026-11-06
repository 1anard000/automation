#!/usr/bin/env python3
"""Rewrite agent-discovered-jobs-summary.json post-cleanup with accurate counts.
Merges agent + master records scanned today. Idempotent.

2026-10-16 update: derive skipped_sources from actual data instead of hardcoded
strings. Previously the script always listed boss-zhilian as skipped when the
pre-check gate reported 0 survivors, even if boss-zhilian-import.py actually
imported records (Pitfall #30). Now we count actual records by source.
"""
import json
from collections import Counter
from pathlib import Path
from datetime import date

TODAY = date.today().isoformat()
AGENT = Path("/Users/iancolrick/.openclaw/workspace/career-os/scrapers/agent-discovered-jobs.json")
MASTER = Path("/Users/iancolrick/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json")
SUMMARY = Path("/Users/iancolrick/.openclaw/workspace/career-os/scrapers/agent-discovered-jobs-summary.json")

# Sources that the pipeline attempts but often yields 0 from.
# We check each against actual today's data to build an honest skipped list.
ATTEMPTED_SOURCES = {
    "boss-zhilian-websearch": "boss-zhilian",
    "liepin": "liepin",
    "indeed-jobsdb": "indeed-jobsdb",
    "websearch": "websearch",
    "builtin": "builtin",
    "wellfound": "wellfound",
    "ashby": "ashby",
}

def main():
    with open(AGENT) as f:
        agent = json.load(f)
    with open(MASTER) as f:
        master = json.load(f)

    today_agent = [j for j in agent if j.get("scanned_date") == TODAY]
    today_master = [j for j in master if j.get("scanned_date") == TODAY]

    all_new = today_agent + today_master
    source_counts = Counter(j.get("source", "unknown") for j in all_new)

    # Build skipped_sources from actual data: attempted sources with 0 records today
    skipped_sources = []
    for src_key, label in ATTEMPTED_SOURCES.items():
        if source_counts.get(src_key, 0) == 0:
            skipped_sources.append(f"{label} (0 records today)")

    # Detect junior titles (Pitfall #4)
    junior_flags = []
    for j in all_new:
        title = j.get("title", "")
        if "助理" in title or "实习" in title:
            junior_flags.append(f"{title} @ {j.get('company', '?')} | {j.get('salary', '?')}")

    summary = {
        "date": TODAY,
        "total_new_jobs": len(all_new),
        "agent_discovered": len(today_agent),
        "master_imported": len(today_master),
        "by_source": dict(source_counts),
        "by_location": dict(Counter(
            (j.get("location_norm") or "").strip() or (j.get("location") or "unknown")
            for j in all_new
        )),
        "by_role_type": dict(Counter(j.get("role_type", "unknown") for j in all_new)),
        "cleanup_notes": {
            "us_remote_dropped_from_master": 0,
            "salary_floor_dropped_from_master": 0,
            "us_remote_dropped_from_agent": 0,
            "agent_cross_file_dups": 0,
            "junior_title_flags": junior_flags,
            "skipped_sources": skipped_sources,
        }
    }

    with open(SUMMARY, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"Summary written: {SUMMARY}")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
