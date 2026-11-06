#!/usr/bin/env python3
"""master-location-cleanup.py — drop today's non-APAC records from jobs-all.json.

Why this exists (Pitfall #35, #41):
  `scan-all.py` has NO location gate. Its quality gate checks domain keywords
  and salary floor, but when salary is empty (most Greenhouse records), the
  location check is skipped entirely. The result: US-Remote / Canada-Remote /
  EMEA-remote records leak into master, and the operator reports them as "new
  jobs" until manual inspection catches them.

  This script is the deterministic post-scan cleanup. Run it AFTER
  `scan-all.py` and AFTER `backfill-schema.py` (so `location_norm` is filled)
  and BEFORE `rewrite-summary.py` (so the summary reflects the cleaned state).

What it does:
  1. Loads `jobs-all.json`.
  2. For every record with `scanned_date == today`:
       - Drop if raw `location` is non-APAC (US-remote, Canada-remote,
         EMEA cities, LATAM, etc.) and not explicitly APAC-remote.
       - Drop if `title` contains seniority leaks ('head of', VP, chief,
         c-level) — these should have been caught upstream but sometimes
         slip through.
  3. Writes the cleaned list back to `jobs-all.json`.
  4. Prints a per-record drop log so the operator can audit.

Idempotent: dropping an already-dropped record is a no-op.

Usage (from cron):
  python3 scrapers/master-location-cleanup.py            # uses today's date
  python3 scrapers/master-location-cleanup.py 2026-11-04 # explicit date

Exit codes:
  0 — clean (no drops needed, or drops applied successfully)
  1 — jobs-all.json missing or unreadable
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import date

# --- Config -----------------------------------------------------------------

DEFAULT_MASTER = os.path.join(
    os.path.expanduser("~"),
    ".openclaw", "workspace", "career-os",
    "OKComputer_职位搜索清单", "jobs-all.json",
)

# APAC substrings — case-insensitive match against raw `location`.
APAC_KEYWORDS = [
    "shenzhen", "hong kong", "guangzhou", "shanghai", "singapore",
    "beijing", "hangzhou", "chengdu", "nanjing", "suzhou",
    "tokyo", "seoul", "taipei", "bangkok", "jakarta", "manila",
    "kuala lumpur", "sydney", "melbourne", "ho chi minh", "hanoi",
    "apac", "asia pacific", "southeast asia", "sea region",
    "japan", "korea", "taiwan", "thailand", "vietnam", "indonesia",
    "malaysia", "philippines", "australia", "new zealand", "india",
]

# Explicit APAC-remote markers — keep these even if the location string
# also mentions "Remote".
APAC_REMOTE_MARKERS = [
    "remote - apac", "remote apac", "apac remote", "apac (remote)",
    "asia pacific remote", "remote - asia", "remote asia",
    "global remote", "remote - global",
]

# Seniority leaks — drop today's records with these in the title.
SENIORITY_LEAK_RE = re.compile(
    r"\b(head of|vp|vice president|svp|evp|chief|cto|cfo|ceo|coo|cmo|president)\b",
    re.IGNORECASE,
)


# --- Helpers ----------------------------------------------------------------

def is_apac_location(loc: str) -> bool:
    """Return True if the raw location string mentions APAC."""
    if not loc:
        return False  # empty location is NOT auto-APAC — flag for review
    loc_l = loc.lower()
    if any(m in loc_l for m in APAC_REMOTE_MARKERS):
        return True
    return any(k in loc_l for k in APAC_KEYWORDS)


def is_seniority_leak(title: str) -> bool:
    if not title:
        return False
    return bool(SENIORITY_LEAK_RE.search(title))


# --- Main -------------------------------------------------------------------

def main() -> int:
    today = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    path = DEFAULT_MASTER
    if not os.path.exists(path):
        print(f"[ERROR] master not found: {path}", file=sys.stderr)
        return 1

    with open(path, "r", encoding="utf-8") as f:
        master = json.load(f)

    kept, dropped = [], []
    for j in master:
        if j.get("scanned_date") != today:
            kept.append(j)
            continue

        loc_raw = j.get("location") or ""
        loc_norm = j.get("location_norm") or ""
        loc = (loc_raw or loc_norm or "").strip()
        title = j.get("title") or ""

        reasons = []
        if not is_apac_location(loc):
            reasons.append(f"non-apac-loc:{loc[:50]}")
        if is_seniority_leak(title):
            reasons.append(f"seniority-leak:{title[:50]}")

        if reasons:
            dropped.append((j, reasons))
        else:
            kept.append(j)

    if dropped:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(kept, f, ensure_ascii=False, indent=2)

    print(f"date filter: scanned_date == {today}")
    print(f"master before: {len(master)}")
    print(f"dropped:       {len(dropped)}")
    print(f"master after:  {len(kept)}")
    print()
    if dropped:
        print("--- dropped records ---")
        for j, reasons in dropped:
            print(f"  - {j.get('title','?')[:60]} | {j.get('company','?')} | "
                  f"{(j.get('location') or '')[:40]} | reasons: {', '.join(reasons)}")
    else:
        print("[OK] no non-APAC or seniority-leak records in today's batch")
    return 0


if __name__ == "__main__":
    sys.exit(main())
