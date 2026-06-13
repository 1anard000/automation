#!/usr/bin/env python3
"""Merge *-jobs.json source files into jobs-all.json with deduplication by (title, company, location)."""
import json
import os
import sys
import glob
from datetime import datetime

DIR = os.path.dirname(os.path.abspath(__file__))
ALL_FILE = os.path.join(DIR, "jobs-all.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main(source_files=None):
    # Load existing jobs
    if os.path.exists(ALL_FILE):
        existing = load_json(ALL_FILE)
    else:
        existing = []

    # Build dedup index from existing
    seen = set()
    for j in existing:
        key = (j.get("title", "").strip(), j.get("company", "").strip(), j.get("location", "").strip())
        seen.add(key)

    # Find source files
    if source_files:
        sources = source_files
    else:
        sources = sorted(glob.glob(os.path.join(DIR, "*-jobs.json")))

    if not sources:
        print("No source files found (*-jobs.json)")
        return

    new_count = 0
    dup_count = 0

    for src in sources:
        if not os.path.exists(src):
            print(f"  Skipping missing file: {src}")
            continue
        try:
            jobs = load_json(src)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  Error reading {src}: {e}")
            continue

        basename = os.path.basename(src)
        added_from_file = 0
        for j in jobs:
            key = (j.get("title", "").strip(), j.get("company", "").strip(), j.get("location", "").strip())
            if key in seen:
                dup_count += 1
            else:
                seen.add(key)
                existing.append(j)
                new_count += 1
                added_from_file += 1

        print(f"  {basename}: {added_from_file} new / {len(jobs)} total")

    # Sort by grade priority then company
    grade_order = {"A-1": 0, "A-2": 1, "B": 2, "C": 3}
    existing.sort(key=lambda j: (grade_order.get(j.get("grade", ""), 9), j.get("company", "")))

    save_json(ALL_FILE, existing)

    print(f"\nMerge complete:")
    print(f"  New jobs added:  {new_count}")
    print(f"  Duplicates skipped: {dup_count}")
    print(f"  Total in jobs-all.json: {len(existing)}")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args if args else None)
