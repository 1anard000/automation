#!/usr/bin/env python3
"""Inspect the 48 Remote jobs: which are US-remote vs global/APAC-remote."""
import json
from datetime import date
from collections import Counter

AGENT = "/Users/iancolrick/.openclaw/workspace/career-os/scrapers/agent-discovered-jobs.json"
with open(AGENT) as f:
    agent = json.load(f)

today = date.today().isoformat()
todays = [j for j in agent if j.get('scanned_date')==today]
print(f"Today's records: {len(todays)}")

remote_jobs = [j for j in todays if 'remote' in (j.get('location_norm') or j.get('location','')).lower()]
print(f"Remote jobs today: {len(remote_jobs)}")

# Bucket them
apac_signal = ['apac','asia','seoul','tokyo','singapore','hong kong','taipei','bangkok','jakarta','sydney','melbourne','global']
us_signal = ['us','usa','americas','emea','europe','united states','uk','london','toronto','canada']

apac_remote = []
us_remote = []
unclear = []
for j in remote_jobs:
    loc = (j.get('location') or '').lower()
    title = (j.get('title') or '').lower()
    combined = loc + ' ' + title
    if any(s in loc for s in us_signal) and not any(s in loc for s in apac_signal):
        us_remote.append(j)
    elif any(s in combined for s in apac_signal):
        apac_remote.append(j)
    else:
        unclear.append(j)

print(f"\n  US-remote (drop): {len(us_remote)}")
print(f"  APAC/global-remote (keep): {len(apac_remote)}")
print(f"  Unclear: {len(unclear)}")

print("\n--- US-remote (to drop) ---")
for j in us_remote:
    print(f"  [{j.get('source','?')}] {j.get('location','?')[:40]:40} | {j.get('title','')[:60]}")

print("\n--- APAC/global-remote (to keep) ---")
for j in apac_remote:
    print(f"  [{j.get('source','?')}] {j.get('location','?')[:40]:40} | {j.get('title','')[:60]}")

print("\n--- Unclear ---")
for j in unclear:
    print(f"  [{j.get('source','?')}] {j.get('location','?')[:40]:40} | {j.get('title','')[:60]}")
