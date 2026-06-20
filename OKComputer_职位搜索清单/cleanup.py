#!/usr/bin/env python3
"""Job cleanup script: remove stale, irrelevant, wrong-city, and experience-mismatch jobs.

Usage:
  python3 cleanup.py              # dry-run (default, safe)
  python3 cleanup.py --apply      # actually modify jobs-all.json
  python3 cleanup.py --backup     # create backup before applying
"""

import json
import re
import os
import shutil
import sys
from datetime import datetime, timedelta

# ── Valid cities (expanded to cover Chinese variants & APAC) ──────────
VALID_CITIES = [
    # English
    "shenzhen", "hong kong", "guangzhou", "shanghai", "singapore",
    "beijing", "taipei", "hangzhou", "tokyo", "seoul", "bangkok",
    "jakarta", "kuala lumpur", "sydney", "melbourne", "australia",
    "remote", "hybrid", "worldwide", "global", "anywhere",
    # Chinese
    "深圳", "广州", "上海", "北京", "杭州",
]

# Irrelevant title keywords (case-insensitive, whole-word)
# These are standalone junior/entry-level roles — NOT when preceded by senior/staff
IRRELEVANT_KEYWORDS = [
    "intern", "junior", "assistant",
    "marketing coordinator",
]

# Keywords that are only irrelevant when NOT preceded by senior/staff/director/head/principal/group
CONDITIONAL_KEYWORDS = [
    "analyst", "support", "data scientist",
]

# Experience mismatch patterns
EXPERIENCE_PATTERNS = [
    r"15\+?\s*years",
    r"20\+?\s*years",
    r"15 years",
    r"20 years",
]


def is_valid_city(location):
    """Check if location contains any valid city (English or Chinese).
    
    Returns True if location is empty (we don't remove jobs with missing location data).
    """
    if not location or not location.strip():
        return True  # Empty location = don't remove
    loc_lower = location.lower()
    return any(city in loc_lower for city in VALID_CITIES)


def is_irrelevant_title(title):
    """Check if title contains irrelevant keywords (whole-word match).
    
    Returns list of matched keywords. Conditional keywords (analyst, engineer, etc.)
    are only matched if the title does NOT also contain senior/staff/director/head/principal.
    """
    title_lower = title.lower()
    matched = []
    
    # Seniority modifiers that exempt conditional keywords
    SENIORITY = ["senior", "staff", "director", "head ", "principal", "lead ", "vp "]
    hasSeniority = any(s in title_lower for s in SENIORITY)
    
    for kw in IRRELEVANT_KEYWORDS:
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, title_lower):
            matched.append(kw)
    
    if not hasSeniority:
        for kw in CONDITIONAL_KEYWORDS:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, title_lower):
                matched.append(kw)
    
    return matched


def has_experience_mismatch(job):
    """Check if any field mentions 15+ or 20+ years experience required."""
    text = " ".join(str(v) for v in job.values() if isinstance(v, str)).lower()
    for pattern in EXPERIENCE_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def is_stale(job, max_days=30):
    """Check if job is stale based on stale_days field or scanned_date age."""
    # Prefer the explicit stale_days field if present
    if "stale_days" in job:
        try:
            sd = int(job["stale_days"])
            if sd > max_days:
                return True
        except (ValueError, TypeError):
            pass

    # Fallback: check scanned_date
    scanned = job.get("scanned_date", "")
    if scanned:
        try:
            d = datetime.fromisoformat(scanned.replace("Z", ""))
            if (datetime.now() - d).days > max_days:
                return True
        except (ValueError, TypeError):
            pass

    # Fallback: old year mentions in key fields (only 2023/2024, not URLs)
    check_fields = [job.get("title", ""), job.get("company", ""),
                    job.get("role_type", ""), job.get("salary", "")]
    check_fields = [str(f) if f else "" for f in check_fields]
    check_text = " ".join(check_fields)
    for year in ["2023", "2024"]:
        if year in check_text:
            return True
    return False


def analyze_job(job):
    """Return list of removal reasons for a job, or empty list if OK."""
    reasons = []

    if not is_valid_city(job.get("location", "")):
        reasons.append("wrong_city")

    matched_kw = is_irrelevant_title(job.get("title", ""))
    if matched_kw:
        reasons.append(f"irrelevant_title:{','.join(matched_kw)}")

    if has_experience_mismatch(job):
        reasons.append("experience_mismatch")

    if is_stale(job):
        reasons.append("stale")

    return reasons


def main():
    dry_run = "--apply" not in sys.argv
    do_backup = "--backup" in sys.argv or dry_run  # always backup in dry-run info

    data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs-all.json")

    with open(data_file, "r") as f:
        jobs = json.load(f)

    original_count = len(jobs)
    removals = {}  # reason -> list of job descriptions
    cleaned = []

    for job in jobs:
        reasons = analyze_job(job)
        if reasons:
            label = f"{job.get('title', '?')} ({job.get('company', '?')})"
            for r in reasons:
                base = r.split(":")[0]
                removals.setdefault(base, []).append(label)
        else:
            cleaned.append(job)

    # Report
    total_removed = original_count - len(cleaned)
    mode = "DRY RUN" if dry_run else "APPLIED"

    print(f"=== JOB CLEANUP REPORT ({mode}) ===")
    print(f"Original count: {original_count}")
    print(f"After cleanup:  {len(cleaned)}")
    print(f"Total removed:  {total_removed}")
    print()

    for reason, items in removals.items():
        print(f"--- {reason.upper()} ({len(items)} removed) ---")
        for item in items[:10]:
            print(f"  • {item}")
        if len(items) > 10:
            print(f"  ... and {len(items) - 10} more")
        print()

    if dry_run:
        print("⚠️  DRY RUN — no changes written. Use --apply to modify jobs-all.json")
    else:
        if do_backup:
            backup = data_file + f".bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(data_file, backup)
            print(f"📦 Backup saved: {os.path.basename(backup)}")

        with open(data_file, "w") as f:
            json.dump(cleaned, f, indent=2, ensure_ascii=False)
        print(f"✅ Written {len(cleaned)} jobs to jobs-all.json")


if __name__ == "__main__":
    main()
