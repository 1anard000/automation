#!/usr/bin/env python3
"""Sanity check: did any of today's 11 Greenhouse new jobs get dropped?"""
import json
from datetime import date
from collections import Counter

AGENT = "/Users/iancolrick/.openclaw/workspace/career-os/scrapers/agent-discovered-jobs.json"
SUMMARY = "/Users/iancolrick/.openclaw/workspace/career-os/scrapers/agent-discovered-jobs-summary.json"

with open(AGENT) as f:
    agent = json.load(f)

today = date.today().isoformat()
todays = [j for j in agent if j.get('scanned_date')==today]
print(f"Today's records in agent: {len(todays)}")
for j in todays:
    print(f"  [{j.get('role_type','?')}] {j.get('title','')[:70]} | {j.get('company','')} | {j.get('location_norm') or j.get('location','')}")

# Read summary to see what was discovered
try:
    with open(SUMMARY) as f:
        s = json.load(f)
    print(f"\nSummary keys: {list(s.keys()) if isinstance(s,dict) else 'list'}")
    if isinstance(s, dict):
        print(json.dumps(s, indent=2)[:2000])
except Exception as e:
    print(f"no summary: {e}")
