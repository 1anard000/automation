#!/usr/bin/env python3
"""Quick CLI stats for jobs-all.json."""
import json
import os
import re
from collections import Counter

DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DIR, "jobs-all.json")

LINKEDIN_SEARCH_RE = re.compile(
    r"^https?://(?:www\.)?linkedin\.com/jobs/search/", re.IGNORECASE
)


def main():
    if not os.path.exists(DATA_FILE):
        print(f"File not found: {DATA_FILE}")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    total = len(jobs)

    # By grade
    by_grade = Counter(j.get("grade", "(none)") for j in jobs)
    # By location
    by_location = Counter(j.get("location", "(none)") for j in jobs)
    # By role type
    by_role = Counter(j.get("role_type", "(none)") for j in jobs)
    # By scanned date
    by_date = Counter(j.get("scanned_date", "(none)") for j in jobs)

    # URL quality
    real_urls = 0
    linkedin_search = 0
    empty_urls = 0
    for j in jobs:
        url = j.get("url", "")
        if not url:
            empty_urls += 1
        elif LINKEDIN_SEARCH_RE.match(url):
            linkedin_search += 1
        else:
            real_urls += 1

    print(f"=== Jobs Dashboard Stats ===\n")
    print(f"Total jobs: {total}\n")

    print("--- By Grade ---")
    for g in sorted(by_grade, key=lambda x: {"A-1": 0, "A-2": 1, "B": 2, "C": 3}.get(x, 9)):
        print(f"  {g}: {by_grade[g]}")

    print("\n--- By Location ---")
    for loc, cnt in by_location.most_common():
        print(f"  {loc}: {cnt}")

    print("\n--- By Role Type ---")
    for rt, cnt in by_role.most_common():
        print(f"  {rt}: {cnt}")

    print("\n--- URL Quality ---")
    print(f"  Direct/real URLs:  {real_urls}")
    print(f"  LinkedIn search:   {linkedin_search}")
    print(f"  Empty/missing:     {empty_urls}")
    print(f"  Specificity rate:  {real_urls}/{total} ({100*real_urls/total:.0f}%)")

    print("\n--- By Scanned Date ---")
    for d in sorted(by_date):
        print(f"  {d}: {by_date[d]}")


if __name__ == "__main__":
    main()
