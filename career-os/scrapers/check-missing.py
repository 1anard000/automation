#!/usr/bin/env python3
"""Check what happened to the 5 Remote jobs from today's discovery."""
import json
from datetime import date

AGENT = "/Users/iancolrick/.openclaw/workspace/career-os/scrapers/agent-discovered-jobs.json"

with open(AGENT) as f:
    agent = json.load(f)

# Find all records that might be from today but have Remote location
today = date.today().isoformat()

# Check if there are any records with scanned_date == today that have Remote in location
remote_today = [j for j in agent if j.get('scanned_date')==today and 'remote' in (j.get('location_norm') or j.get('location','')).lower()]
print(f"Today's records with Remote location: {len(remote_today)}")

# Let's also check all records with scanned_date == today
all_today = [j for j in agent if j.get('scanned_date')==today]
print(f"All today's records: {len(all_today)}")

# Check if the 5 missing ones are perhaps in the file but with different dates
# Let's look at the most recent 20 records by scanned_date
recent = sorted(agent, key=lambda x: x.get('scanned_date',''), reverse=True)[:20]
print("\nMost recent 20 records by scanned_date:")
for j in recent:
    print(f"  {j.get('scanned_date')} | {j.get('source','?')[:30]:30} | {j.get('location_norm') or j.get('location','?')[:30]:30} | {j.get('title','')[:50]}")
