"""Inspect today's boss-zhilian imports to see if pipeline already ran today."""
import json
from collections import Counter

BASE = "/Users/iancolrick/.openclaw/workspace/career-os"
MASTER = f"{BASE}/OKComputer_职位搜索清单/jobs-all.json"

with open(MASTER) as f:
    master = json.load(f)

today_jobs = [j for j in master if j.get('scanned_date') == '2026-10-09']
print(f"Today's master jobs: {len(today_jobs)}")
print()
for j in today_jobs[:30]:
    title = (j.get('title') or '')[:60]
    comp = (j.get('company') or '')[:20]
    loc = (j.get('location') or j.get('location_norm') or '')[:30]
    sal = (j.get('salary') or '')[:25]
    print(f"  {comp:<20} | {title:<60} | {loc:<30} | {sal}")

# Check schema completeness
schema_missing = sum(1 for j in today_jobs if not j.get('status'))
print(f"\nRecords missing 'status' field: {schema_missing}")
