#!/usr/bin/env python3
"""Rewrite agent-discovered-jobs-summary.json post-cleanup with accurate counts."""
import json
from collections import Counter
from pathlib import Path
from datetime import date

TODAY = date.today().isoformat()
AGENT = Path("/Users/iancolrick/.openclaw/workspace/career-os/scrapers/agent-discovered-jobs.json")
MASTER = Path("/Users/iancolrick/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json")
SUMMARY = Path("/Users/iancolrick/.openclaw/workspace/career-os/scrapers/agent-discovered-jobs-summary.json")

def main():
    with open(AGENT) as f:
        agent = json.load(f)
    with open(MASTER) as f:
        master = json.load(f)

    today_agent = [j for j in agent if j.get("scanned_date") == TODAY]
    today_master = [j for j in master if j.get("scanned_date") == TODAY]

    # Merge for unified summary
    all_new = today_agent + today_master

    summary = {
        "date": TODAY,
        "total_new_jobs": len(all_new),
        "agent_discovered": len(today_agent),
        "master_imported": len(today_master),
        "by_source": dict(Counter(j.get("source", "unknown") for j in all_new)),
        "by_location": dict(Counter(j.get("location", "unknown") for j in all_new)),
        "by_role_type": dict(Counter(j.get("role_type", "unknown") for j in all_new)),
        "cleanup_notes": {
            "us_remote_dropped_from_master": 3,
            "salary_floor_dropped_from_master": 5,
            "us_remote_dropped_from_agent": 44,
            "agent_cross_file_dups": 0,
            "junior_title_flags": [],
            "skipped_sources": [
                "liepin (0 actionable - junk aggregator rows only)",
                "indeed-jobsdb (0 actionable - listing pages only, no individual jobs)",
                "websearch (0 results)"
            ]
        }
    }

    with open(SUMMARY, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"Summary written: {SUMMARY}")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
