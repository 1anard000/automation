#!/usr/bin/env python3
"""Post-discovery cleanup: salary floor + location filter + cross-dedup."""
import json, re
from datetime import date
from collections import Counter

MASTER = "/Users/iancolrick/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json"
AGENT = "/Users/iancolrick/.openclaw/workspace/career-os/scrapers/agent-discovered-jobs.json"

with open(MASTER) as f:
    master = json.load(f)
with open(AGENT) as f:
    agent = json.load(f)

today = date.today().isoformat()
print(f"today={today}")
print(f"master total={len(master)}, agent total={len(agent)}")

def salary_high(sal):
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

def is_hk(loc):
    return 'hong kong' in loc or 'hongkong' in loc

def is_mainland(loc):
    return any(c in loc for c in ['shenzhen','guangzhou','shanghai','beijing','hangzhou','chengdu','suzhou'])

def is_sg(loc):
    return 'singapore' in loc

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

with open(MASTER,'w') as f:
    json.dump(kept, f, ensure_ascii=False, indent=2)

TARGET_LOCS = ["shenzhen","hong kong","hongkong","guangzhou","shanghai","singapore","apac","asia pacific","asia-pacific","southeast asia","greater china","bangkok","kuala lumpur","tokyo","seoul","taipei","jakarta","manila","sydney","melbourne"]

master_urls = {j.get('url','').strip().rstrip('/').lower() for j in kept if j.get('url')}
master_ids = {j.get('job_id') for j in kept if j.get('job_id')}

def is_us_remote(loc):
    """Check if location is US-remote or non-APAC remote."""
    l = loc.lower()
    # Direct US indicators
    us_direct = ['remote - us', 'remote - usa', 'remote, us', 'remote, united states',
                 'united states', 'usa', 'us-', 'us;', ' us ', 'u.s.', 'americas',
                 'atlanta', 'chicago', 'seattle', 'san francisco', 'new york', 'boston',
                 'california', 'colorado', 'nevada', 'arizona', 'washington', 'oregon',
                 'texas', 'florida', 'georgia', 'denver', 'nyc', 'portland', 'austin',
                 'remote - california', 'remote - colorado', 'remote - canada']
    # Non-APAC remote indicators
    non_apac = ['remote - india', 'remote - united kingdom', 'remote, united kingdom',
                'remote, poland', 'remote - emea', 'germany', 'france', 'netherlands',
                'lisbon', 'portugal', 'latam', 'mexico', 'spain', 'italy', 'sweden',
                'norway', 'denmark', 'finland', 'belgium', 'switzerland', 'austria',
                'ireland', 'israel', 'turkey', 'dubai', 'uae', 'saudi']
    return any(s in l for s in us_direct) or any(s in l for s in non_apac)

def is_apac_remote(loc):
    """Check if location is APAC or global remote."""
    l = loc.lower()
    apac = ['apac', 'asia pacific', 'asia-pacific', 'global remote', 'worldwide',
            'anywhere', 'seoul', 'tokyo', 'singapore', 'hong kong', 'taipei',
            'bangkok', 'jakarta', 'sydney', 'melbourne', 'manila', 'kuala lumpur',
            'remote - apac', 'remote apac', 'remote asia', 'remote - seoul',
            'remote - tokyo', 'remote - singapore', 'remote - hong kong',
            'remote - taipei', 'remote - bangkok', 'remote - jakarta',
            'remote - sydney', 'remote - melbourne']
    return any(s in l for s in apac)

cleaned = []
dropped_url, dropped_loc, dropped_remote_us, kept_remote = 0,0,0,0
for j in agent:
    u = (j.get('url') or '').strip().rstrip('/').lower()
    if u and u in master_urls:
        dropped_url += 1
        continue
    if j.get('job_id') and j['job_id'] in master_ids:
        dropped_url += 1
        continue
    loc = (j.get('location_norm') or j.get('location') or '').lower()
    raw_loc = (j.get('location') or '').lower()
    # Handle Remote jobs
    if 'remote' in loc or 'remote' in raw_loc:
        if is_apac_remote(raw_loc) or is_apac_remote(loc):
            kept_remote += 1
            cleaned.append(j)
            continue
        # Default: drop all remote jobs that are not clearly APAC
        dropped_remote_us += 1
        continue
    if not any(t in loc for t in TARGET_LOCS):
        dropped_loc += 1
        continue
    cleaned.append(j)

print(f"\n[Agent cleanup] dropped {dropped_url} cross-dups, {dropped_remote_us} US/non-APAC remote, {dropped_loc} non-target loc, kept {kept_remote} APAC remote")
print(f"Agent file now: {len(cleaned)} records")

with open(AGENT,'w') as f:
    json.dump(cleaned, f, ensure_ascii=False, indent=2)

urls = [(j.get('url') or '').lower() for j in cleaned]
dup_urls = [u for u,c in Counter(urls).items() if c>1 and u]
ids = [j.get('job_id') for j in cleaned]
dup_ids = [i for i,c in Counter(ids).items() if c>1 and i]
print(f"Internal agent dups: urls={len(dup_urls)}, ids={len(dup_ids)}")

todays = [j for j in cleaned if j.get('scanned_date')==today]
print(f"\nToday's new agent records: {len(todays)}")
print("By source:", Counter(j['source'] for j in todays))
print("By role_type:", Counter(j.get('role_type','?') for j in todays))
print("By location:", Counter(j.get('location_norm') or j.get('location','?') for j in todays))

amz = [j for j in cleaned if 'amazon' in ((j.get('company','')+' '+j.get('title','')).lower())]
print(f"Amazon leaks: {len(amz)}")

juniors = [j['title'] for j in todays if '助理' in j.get('title','') or '实习' in j.get('title','')]
print(f"Junior-title flags: {juniors}")

print("\n--- Sample of today's jobs ---")
for j in todays[:15]:
    print(f"  [{j.get('role_type','?')}] {j.get('title','')[:60]} | {j.get('company','')} | {j.get('location_norm') or j.get('location','')}")
