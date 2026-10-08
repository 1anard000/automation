#!/usr/bin/env python3
"""Pre-import gate for Boss直聘 pre-fetched results.
Dedup against master + agent, apply salary floor, filter to /job_detail/ URLs.
Exit 0 = zero survivors (skip import). Exit 1 = survivors exist.
"""
import json
import re
import sys
from pathlib import Path

TODAY = "2026-10-07"
MASTER = Path("/Users/iancolrick/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json")
AGENT = Path("/Users/iancolrick/.openclaw/workspace/career-os/scrapers/agent-discovered-jobs.json")
PREFETCH = Path("/Users/iancolrick/.openclaw/workspace/career-os/scrapers/boss-zhilian-discovery-results.json")

# Salary floor: top of range >= 30K RMB (mainland), >= 60K HKD, >= 10K SGD
# For zhipin/zhaopin we only have RMB ranges; HK jobs on zhipin still quote RMB sometimes
FLOOR_RMB_K = 30

def parse_salary_high(salary: str) -> float | None:
    """Extract top of K-range from strings like '30-55K·15薪' or '50-70K' or '80-110K·15薪'."""
    if not salary:
        return None
    # Strip the 薪 suffix first
    cleaned = re.sub(r'[·.]\d+薪', '', salary)
    # Match N-MK pattern
    m = re.search(r'(\d+)\s*[-–]\s*(\d+)\s*K', cleaned, re.IGNORECASE)
    if m:
        return float(m.group(2))
    # Match single value like '50K'
    m = re.search(r'(\d+)\s*K', cleaned, re.IGNORECASE)
    if m:
        return float(m.group(1))
    return None

def normalize_url(url: str) -> str:
    """Strip mobile prefix and trailing slash variations."""
    if not url:
        return ""
    u = url.strip().lower()
    u = u.replace("m.zhipin.com", "www.zhipin.com")
    u = u.replace("m.zhaopin.com", "www.zhaopin.com")
    u = u.rstrip("/")
    return u

def main():
    with open(MASTER) as f:
        master = json.load(f)
    with open(AGENT) as f:
        agent = json.load(f)
    with open(PREFETCH) as f:
        prefetch = json.load(f)

    master_urls = {normalize_url(j.get("url", "")) for j in master}
    agent_urls = {normalize_url(j.get("url", "")) for j in agent}

    # Target locations (case-insensitive substring)
    TARGET_LOCS = ["shenzhen", "hong kong", "guangzhou", "shanghai", "singapore", "beijing", "hangzhou"]

    survivors = []
    dropped = {"dup": 0, "listing_page": 0, "salary_below_floor": 0, "non_target_loc": 0, "no_salary_no_loc": 0}

    for j in prefetch:
        url = j.get("url", "")
        # Only keep individual job detail pages
        if "/job_detail/" not in url and "/jobdetail/" not in url:
            dropped["listing_page"] += 1
            continue

        norm = normalize_url(url)
        if norm in master_urls or norm in agent_urls:
            dropped["dup"] += 1
            continue

        loc = (j.get("location") or "").lower()
        if not any(t in loc for t in TARGET_LOCS):
            # Only drop if location is non-empty AND not target
            if loc:
                dropped["non_target_loc"] += 1
                continue

        salary_high = parse_salary_high(j.get("salary", ""))
        if salary_high is not None and salary_high < FLOOR_RMB_K:
            dropped["salary_below_floor"] += 1
            continue

        survivors.append(j)

    print(f"Prefetched: {len(prefetch)}")
    print(f"Dropped dups: {dropped['dup']}")
    print(f"Dropped listing pages: {dropped['listing_page']}")
    print(f"Dropped salary below floor ({FLOOR_RMB_K}K): {dropped['salary_below_floor']}")
    print(f"Dropped non-target location: {dropped['non_target_loc']}")
    print(f"Survivors passing all gates: {len(survivors)}")
    print()
    if survivors:
        print("Survivors:")
        for s in survivors:
            sal = s.get('salary', '')
            print(f"  - [{s.get('location','?')}] {s.get('title','?')[:60]} | {s.get('company','?')} | {sal} | {s.get('url','')[:80]}")
        sys.exit(1)
    else:
        print("Zero survivors — skipping import.")
        sys.exit(0)

if __name__ == "__main__":
    main()
