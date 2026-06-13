#!/usr/bin/env python3
"""Remove duplicate jobs from jobs-all.json, keeping the entry with the more specific URL."""
import json
import os
import re

DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DIR, "jobs-all.json")

LINKEDIN_SEARCH_RE = re.compile(
    r"^https?://(?:www\.)?linkedin\.com/jobs/search/", re.IGNORECASE
)


def is_generic_url(url):
    """Return True if URL is a generic LinkedIn search URL (not a direct job link)."""
    if not url:
        return True  # empty URL is "generic"
    return bool(LINKEDIN_SEARCH_RE.match(url))


def url_specificity(url):
    """Higher score = more specific/better URL."""
    if not url:
        return 0
    if is_generic_url(url):
        return 1
    return 2  # direct link


def main():
    if not os.path.exists(DATA_FILE):
        print(f"File not found: {DATA_FILE}")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    # Group by (title, company)
    groups = {}
    for j in jobs:
        key = (j.get("title", "").strip(), j.get("company", "").strip())
        groups.setdefault(key, []).append(j)

    cleaned = []
    removed = 0

    for key, group in groups.items():
        if len(group) == 1:
            cleaned.append(group[0])
            continue

        # Keep the one with the best URL, then most recent scanned_date
        best = max(group, key=lambda j: (
            url_specificity(j.get("url", "")),
            j.get("scanned_date", ""),
        ))
        cleaned.append(best)
        removed += len(group) - 1

    # Sort by grade then company
    grade_order = {"A-1": 0, "A-2": 1, "B": 2, "C": 3}
    cleaned.sort(key=lambda j: (grade_order.get(j.get("grade", ""), 9), j.get("company", "")))

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Dedup complete:")
    print(f"  Removed: {removed} duplicates")
    print(f"  Remaining: {len(cleaned)} jobs")


if __name__ == "__main__":
    main()
