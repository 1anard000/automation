#!/usr/bin/env python3
"""
Post-discovery cleanup for Career OS job pipeline.

Runs deterministic post-processing on jobs-all.json and agent-discovered-jobs.json:
1. Salary-floor cleanup on master's today's records (Boss直-imported RMB/HKD/SGD ranges).
2. Cross-file dedup (agent vs master by URL and job_id).
3. US/non-APAC-remote filter using the RAW `location` field (not just `location_norm`).
4. Target-location filter for non-Remote records.
5. Verifies: no internal dups, no Amazon leaks, prints today's new counts by source/role/location.

Usage:
  python3 post-discovery-cleanup.py            # dry-run-ish, writes both files
  python3 post-discovery-cleanup.py --check    # only print, do not write

Designed to be called from cron after run-greenhouse-discovery.py and
boss-zhilian-import.py. Idempotent — running twice produces the same result.

IMPORTANT: this script is the FINAL authority on what stays in agent-discovered-jobs.json.
Do NOT re-run the greenhouse scraper to "recover" records this script dropped —
the scraper's filters are intentionally looser. If this script drops too much,
fix the filter here and re-run only this script (ideally against a backup).
"""
import json, re, sys
from datetime import date
from collections import Counter

MASTER = "/Users/iancolrick/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json"
AGENT = "/Users/iancolrick/.openclaw/workspace/career-os/scrapers/agent-discovered-jobs.json"

TARGET_LOCS = [
    "shenzhen", "hong kong", "hongkong", "guangzhou", "shanghai", "singapore",
    "apac", "asia pacific", "asia-pacific", "southeast asia", "greater china",
    "bangkok", "kuala lumpur", "tokyo", "seoul", "taipei", "jakarta", "manila",
    "sydney", "melbourne"
]

def salary_high(sal):
    """Top of salary range in K (RMB/HKD/SGD). Returns None if no range found."""
    if not sal:
        return None
    s = re.sub(r'[·.]\d+薪', '', sal)
    m = re.search(r'(\d+)\s*[-–]\s*(\d+)\s*K', s, re.I)
    if m:
        return int(m.group(2))
    m = re.search(r'(\d+)\s*[-–]\s*(\d+)', s)
    if m:
        return int(m.group(2))
    return None

def is_hk(loc): return 'hong kong' in loc or 'hongkong' in loc
def is_mainland(loc):
    return any(c in loc for c in ['shenzhen','guangzhou','shanghai','beijing','hangzhou','chengdu','suzhou'])
def is_sg(loc): return 'singapore' in loc

def is_us_remote(loc):
    """True if the location is US-remote or non-APAC remote (Europe, India, LATAM)."""
    l = loc.lower()
    us_direct = [
        'remote - us', 'remote - usa', 'remote, us', 'remote, united states',
        'united states', 'usa', 'us-', 'us;', ' us ', 'u.s.', 'americas',
        'atlanta', 'chicago', 'seattle', 'san francisco', 'new york', 'boston',
        'california', 'colorado', 'nevada', 'arizona', 'washington', 'oregon',
        'texas', 'florida', 'georgia', 'denver', 'nyc', 'portland', 'austin',
        'remote - california', 'remote - colorado', 'remote - canada', 'canada'
    ]
    non_apac = [
        'remote - india', 'remote - united kingdom', 'remote, united kingdom',
        'remote, poland', 'remote - emea', 'germany', 'france', 'netherlands',
        'lisbon', 'portugal', 'latam', 'mexico', 'spain', 'italy', 'sweden',
        'norway', 'denmark', 'finland', 'belgium', 'switzerland', 'austria',
        'ireland', 'israel', 'turkey', 'dubai', 'uae', 'saudi', 'boston, ma',
        'san francisco', 'new york'
    ]
    return any(s in l for s in us_direct) or any(s in l for s in non_apac)

def is_apac_remote(loc):
    """True if the location is APAC or global remote."""
    l = loc.lower()
    apac = [
        'apac', 'asia pacific', 'asia-pacific', 'global remote', 'worldwide',
        'anywhere', 'seoul', 'tokyo', 'singapore', 'hong kong', 'taipei',
        'bangkok', 'jakarta', 'sydney', 'melbourne', 'manila', 'kuala lumpur',
        'remote - apac', 'remote apac', 'remote asia', 'remote - seoul',
        'remote - tokyo', 'remote - singapore', 'remote - hong kong',
        'remote - taipei', 'remote - bangkok', 'remote - jakarta',
        'remote - sydney', 'remote - melbourne'
    ]
    return any(s in l for s in apac)

def main():
    check_only = '--check' in sys.argv

    with open(MASTER) as f:
        master = json.load(f)
    with open(AGENT) as f:
        agent = json.load(f)

    today = date.today().isoformat()
    print(f"today={today}")
    print(f"master total={len(master)}, agent total={len(agent)}")

    # --- 1. Salary-floor cleanup on master today's records ---
    removed = []
    kept = []
    for j in master:
        if j.get('scanned_date') != today:
            kept.append(j)
            continue
        sal = j.get('salary','') or ''
        loc = (j.get('location_norm') or j.get('location') or '').lower()
        high = salary_high(sal)
        if high is None:
            kept.append(j)
            continue
        if is_hk(loc) and high < 60:
            removed.append((j['title'][:40], sal, loc))
        elif is_mainland(loc) and high < 30:
            removed.append((j['title'][:40], sal, loc))
        elif is_sg(loc) and high < 10:
            removed.append((j['title'][:40], sal, loc))
        else:
            kept.append(j)

    print(f"\n[Salary cleanup] removed {len(removed)}, kept today {sum(1 for j in kept if j.get('scanned_date')==today)}")
    for r in removed:
        print("  REMOVED:", r)

    if not check_only:
        with open(MASTER,'w') as f:
            json.dump(kept, f, ensure_ascii=False, indent=2)

    # --- 2-4. Agent cleanup: dedup, remote filter, target loc filter ---
    master_urls = {j.get('url','').strip().rstrip('/').lower() for j in kept if j.get('url')}
    master_ids = {j.get('job_id') for j in kept if j.get('job_id')}

    cleaned = []
    dropped_url, dropped_loc, dropped_remote, kept_remote = 0, 0, 0, 0
    for j in agent:
        u = (j.get('url') or '').strip().rstrip('/').lower()
        if u and u in master_urls:
            dropped_url += 1
            continue
        if j.get('job_id') and j['job_id'] in master_ids:
            dropped_url += 1
            continue
        loc_norm = (j.get('location_norm') or '').lower()
        raw_loc = (j.get('location') or '').lower()
        combined = raw_loc + ' ' + loc_norm

        if 'remote' in combined:
            if is_apac_remote(raw_loc) or is_apac_remote(loc_norm):
                kept_remote += 1
                cleaned.append(j)
                continue
            dropped_remote += 1
            continue

        if not any(t in combined for t in TARGET_LOCS):
            dropped_loc += 1
            continue
        cleaned.append(j)

    print(f"\n[Agent cleanup] dropped {dropped_url} cross-dups, {dropped_remote} US/non-APAC remote, {dropped_loc} non-target loc, kept {kept_remote} APAC remote")
    print(f"Agent file now: {len(cleaned)} records")

    if not check_only:
        with open(AGENT,'w') as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=2)

    # --- 5. Verification ---
    urls = [(j.get('url') or '').lower() for j in cleaned]
    ids = [j.get('job_id') for j in cleaned]
    dup_urls = [u for u,c in Counter(urls).items() if c > 1 and u]
    dup_ids = [i for i,c in Counter(ids).items() if c > 1 and i]
    print(f"Internal agent dups: urls={len(dup_urls)}, ids={len(dup_ids)}")

    todays = [j for j in cleaned if j.get('scanned_date') == today]
    print(f"\nToday's new agent records: {len(todays)}")
    print("By source:", Counter(j['source'] for j in todays))
    print("By role_type:", Counter(j.get('role_type','?') for j in todays))
    print("By location:", Counter(j.get('location_norm') or j.get('location','?') for j in todays))

    amz = [j for j in cleaned if 'amazon' in ((j.get('company','') + ' ' + j.get('title','')).lower())]
    print(f"Amazon leaks: {len(amz)}")

    juniors = [j['title'] for j in todays if '助理' in j.get('title','') or '实习' in j.get('title','')]
    print(f"Junior-title flags: {juniors}")

    print("\n--- Today's jobs ---")
    for j in todays:
        print(f"  [{j.get('role_type','?')}] {j.get('title','')[:60]} | {j.get('company','')} | {j.get('location_norm') or j.get('location','')}")

if __name__ == '__main__':
    main()
