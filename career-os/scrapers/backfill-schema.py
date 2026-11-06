#!/usr/bin/env python3
"""
Backfill missing schema fields on jobs-all.json records.

scan-all.py appends new records with a minimal schema (title, company, location,
grade, url, role_type, salary, scanned_date, source, yoe_note). This script
backfills the standard schema fields that older pipeline scripts produce:
status, status_date, last_touch_date, location_norm, quality_score, quality_tier,
low_quality, category, english_friendly, has_direct_link, url_type, job_id.

Usage:
    python3 backfill-schema.py                # backfill records missing 'status'
    python3 backfill-schema.py --today-only   # only records with scanned_date == today
    python3 backfill-schema.py --dry-run      # print what would change, don't write

Idempotent: safe to run multiple times. Only fills fields that are missing
or empty; never overwrites existing non-empty values.
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "OKComputer_职位搜索清单" / "jobs-all.json"

APAC_CITY_MAP = {
    "shenzhen": "Shenzhen",
    "hong kong": "Hong Kong",
    "hongkong": "Hong Kong",
    "guangzhou": "Guangzhou",
    "shanghai": "Shanghai",
    "singapore": "Singapore",
    "beijing": "Beijing",
    "hangzhou": "Hangzhou",
    "taipei": "Taipei",
    "taiwan": "Taiwan",
    "tokyo": "Tokyo",
    "seoul": "Seoul",
    "bangkok": "Bangkok",
    "kuala lumpur": "Kuala Lumpur",
    "jakarta": "Jakarta",
    "manila": "Manila",
    "sydney": "Sydney",
    "melbourne": "Melbourne",
}


def normalize_location(raw: str) -> str:
    """Map a raw Greenhouse/Ashby location string to a canonical city name.

    Handles:
      - "Hong Kong, Hong Kong SAR"         → "Hong Kong"
      - "Singapore, Singapore"             → "Singapore"
      - "Beijing, China; Shanghai, China"  → "Beijing"  (first APAC match wins)
      - "Taiwan (Remote)"                  → "Taiwan"
      - "Shenzhen"                         → "Shenzhen"
      - "US-Remote" / "Remote - US"        → ""        (non-APAC → empty)
    """
    if not raw:
        return ""
    # Split multi-location strings on ';' or '/'
    segments = re.split(r"[;/]", raw)
    for seg in segments:
        seg_l = seg.strip().lower()
        # Try to match APAC city names as substrings
        for kw, canonical in APAC_CITY_MAP.items():
            if kw in seg_l:
                return canonical
    return ""


def make_job_id(url: str, title: str) -> str:
    return hashlib.sha1((url + title).encode()).hexdigest()[:12]


def backfill(jobs: list, today_only: bool = False, today: str = None) -> tuple:
    """Return (modified_count, total_missing_status)."""
    today = today or date.today().isoformat()
    modified = 0
    missing_status = 0

    for j in jobs:
        if today_only and j.get("scanned_date") != today:
            continue
        if "status" not in j:
            missing_status += 1

        changed = False

        # Status fields
        for field, default in [
            ("status", "not_applied"),
            ("status_date", j.get("scanned_date", today)),
            ("last_touch_date", j.get("scanned_date", today)),
        ]:
            if not j.get(field):
                j[field] = default
                changed = True

        # location_norm
        if not j.get("location_norm"):
            norm = normalize_location(j.get("location", ""))
            if norm:
                j["location_norm"] = norm
                changed = True

        # Quality fields
        for field, default in [
            ("quality_score", None),
            ("quality_tier", ""),
            ("low_quality", False),
            ("category", "other"),
            ("english_friendly", True),
            ("has_direct_link", True),
            ("url_type", "direct"),
        ]:
            if field not in j:
                j[field] = default
                changed = True

        # job_id
        if not j.get("job_id"):
            url = j.get("url", "")
            title = j.get("title", "")
            if url or title:
                j["job_id"] = make_job_id(url, title)
                changed = True

        if changed:
            modified += 1

    return modified, missing_status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB), help="Path to jobs-all.json")
    ap.add_argument("--today-only", action="store_true",
                    help="Only backfill records with scanned_date == today")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print stats without writing")
    args = ap.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"ERROR: {db_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(db_path) as f:
        jobs = json.load(f)

    modified, missing_status = backfill(jobs, today_only=args.today_only)

    print(f"Total records:     {len(jobs)}")
    print(f"Modified records:  {modified}")
    print(f"Missing status:    {missing_status}")

    if args.dry_run:
        print("DRY RUN — no changes written.")
        return

    with open(db_path, "w") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"Wrote {db_path}")


if __name__ == "__main__":
    main()
