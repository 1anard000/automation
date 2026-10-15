#!/usr/bin/env python3
"""
Post-import salary-floor cleanup for jobs-all.json (master DB).

Drop today's records whose salary range top is below the user's floor:
  - Mainland China (Shenzhen / Shanghai / Guangzhou / Beijing / Hangzhou): high < 30K RMB/mo
  - Hong Kong: high < 60K HKD/mo
  - Singapore: high < 10K SGD/mo

Key gotchas (learned from real runs):
  1. Strip the ·Nsalary-months suffix (e.g. "14-28K·14薪") before regex.
  2. Fall back to `location` when `location_norm` is empty/None (Boss直聘 imports
     often leave location_norm unset).
  3. Boss直聘-import writes go directly to jobs-all.json, NOT agent-discovered-jobs.json,
     so this script targets the master DB filtered by scanned_date == today.

Records with empty salary are kept (Greenhouse rarely includes salary).
Non-"today" records are never touched — historical data stays as-is.

Usage: python3 enforce-salary-floor.py [--dry-run]
"""
import json, os, re, sys
from datetime import date

MASTER_PATH = "/Users/iancolrick/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json"

# (city_substring_in_location, min_top_of_range_K, currency_label)
FLOORS = [
    ("shenzhen", 30, "RMB"),
    ("shanghai", 30, "RMB"),
    ("guangzhou", 30, "RMB"),
    ("beijing", 30, "RMB"),
    ("hangzhou", 30, "RMB"),
    ("hong kong", 60, "HKD"),
    ("singapore", 10, "SGD"),
]

SALARY_RE = re.compile(r"(\d+)[-–](\d+)K")
SUFFIX_RE = re.compile(r"[·.]\d+薪")


def load(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"warn reading {path}: {e}")
            return []


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def below_floor(job):
    sal = job.get("salary", "") or ""
    if not sal:
        return False, ""  # no data -> keep
    sal_clean = SUFFIX_RE.sub("", sal)
    m = SALARY_RE.search(sal_clean)
    if not m:
        return False, ""
    high = int(m.group(2))
    loc = (job.get("location_norm") or job.get("location") or "").lower()
    for city, floor_k, cur in FLOORS:
        if city in loc and high < floor_k:
            return True, f"{loc.strip()} top-of-range {high}K < floor {floor_k}K {cur}"
    return False, ""


def main():
    dry_run = "--dry-run" in sys.argv
    today = date.today().isoformat()
    master = load(MASTER_PATH)
    kept, removed = [], []
    for j in master:
        if j.get("scanned_date") != today:
            kept.append(j)
            continue
        bad, reason = below_floor(j)
        if bad:
            removed.append((j, reason))
        else:
            kept.append(j)

    today_count = sum(1 for j in master if j.get("scanned_date") == today)
    print(f"today ({today}): scanned {today_count}")
    print(f"below-floor removed: {len(removed)}")
    for j, reason in removed:
        print(f"  - {j.get('title', '')[:50]} | {j.get('location', '')} | {j.get('salary', '')}  ({reason})")

    if removed and not dry_run:
        save(MASTER_PATH, kept)
        print(f"saved: {len(master)} -> {len(kept)}")
    elif dry_run:
        print("(dry-run, no changes written)")
    else:
        print("no changes needed")


if __name__ == "__main__":
    main()
