"""Pre-import gate for Boss直聘 pre-fetched results.

Diffs `boss-zhilian-discovery-results.json` against master + agent by normalized
URL, filters to `/job_detail/` or `/jobdetail/` URLs only (drops `/zhaopin/`
listing pages), applies the salary-floor regex, and exits:

  0  when zero survivors  -> caller should SKIP the import
  1  when >=1 survivor    -> caller should PROCEED with boss-zhilian-import.py

Usage:
    python3 check-boss-prefetch.py [--verbose]

Compatibility: works on Python 3.8+. Avoids PEP 604 (`X | None`) type-hint
syntax so it runs under older cron Pythons. See SKILL.md Filtering Pitfall #24.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Optional

BASE = "/Users/iancolrick/.openclaw/workspace/career-os"
MASTER = os.path.join(BASE, "OKComputer_职位搜索清单", "jobs-all.json")
AGENT = os.path.join(BASE, "scrapers", "agent-discovered-jobs.json")
PREFETCH = os.path.join(BASE, "scrapers", "boss-zhilian-discovery-results.json")

JOB_DETAIL_RE = re.compile(r"/(job_detail|jobdetail)/", re.IGNORECASE)
SALARY_MONTHS_RE = re.compile(r"[·.]\d+薪")
SALARY_RANGE_RE = re.compile(r"(\d+)\s*[-–]\s*(\d+)\s*[Kk]")


def parse_salary_high(salary):
    # type: (str) -> Optional[float]
    """Return the top of the salary range in K, or None if unparseable."""
    if not salary:
        return None
    s = SALARY_MONTHS_RE.sub("", salary)
    m = SALARY_RANGE_RE.search(s)
    if not m:
        return None
    try:
        return float(m.group(2))
    except ValueError:
        return None


def normalize_url(url):
    # type: (str) -> str
    if not url:
        return ""
    url = url.strip().lower()
    url = url.split("?")[0].split("#")[0]
    url = url.rstrip("/")
    return url


def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return []
    if isinstance(data, dict):
        for key in ("jobs", "results", "items", "data"):
            if key in data and isinstance(data[key], list):
                return data[key]
        return [data]
    return data if isinstance(data, list) else []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    master = load_json(MASTER)
    agent = load_json(AGENT)
    prefetch = load_json(PREFETCH)

    existing_urls = {normalize_url(j.get("url", "")) for j in master}
    existing_urls |= {normalize_url(j.get("url", "")) for j in agent}
    existing_urls.discard("")

    survivors = []
    skipped_dup = 0
    skipped_listing = 0
    skipped_floor = 0

    for j in prefetch:
        url = j.get("url", "") or j.get("link", "") or ""
        if not JOB_DETAIL_RE.search(url):
            skipped_listing += 1
            continue
        norm = normalize_url(url)
        if norm in existing_urls:
            skipped_dup += 1
            continue
        high = parse_salary_high(j.get("salary", "") or "")
        if high is not None and high < 30:
            skipped_floor += 1
            continue
        survivors.append(j)

    print(f"prefetched={len(prefetch)} listing_pages={skipped_listing} "
          f"dups={skipped_dup} below_floor={skipped_floor} survivors={len(survivors)}")

    if args.verbose:
        for s in survivors:
            title = (s.get("title") or "")[:50]
            sal = (s.get("salary") or "")
            print(f"  SURVIVOR: {title} | {sal} | {s.get('url', '')[:80]}")

    sys.exit(1 if survivors else 0)


if __name__ == "__main__":
    main()
