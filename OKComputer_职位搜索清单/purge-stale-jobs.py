#!/usr/bin/env python3
"""Remove stale jobs (>30 days old) and jobs with empty company/title from jobs-all.json."""
import json
import os
import datetime

jobs_path = os.path.join(os.path.dirname(__file__), 'jobs-all.json')
backup_path = jobs_path + '.bak'

with open(jobs_path) as f:
    jobs = json.load(f)

original_count = len(jobs)
today = datetime.date(2026, 7, 4)
removed = []
kept = []

for j in jobs:
    # Check for empty title or company
    title = (j.get('title') or '').strip()
    company = (j.get('company') or '').strip()
    if not title or not company:
        removed.append(('empty_fields', j))
        continue

    # Check staleness
    date_str = j.get('date_posted') or j.get('posted_date') or j.get('created_at') or j.get('first_seen')
    if date_str:
        try:
            dt = datetime.date.fromisoformat(str(date_str)[:10])
            if (today - dt).days > 30:
                removed.append(('stale', j))
                continue
        except (ValueError, TypeError):
            pass  # unparseable date, keep it

    kept.append(j)

print(f"Original: {original_count}")
print(f"Removed: {len(removed)} ({len([r for r in removed if r[0]=='stale'])} stale, {len([r for r in removed if r[0]=='empty_fields'])} empty)")
print(f"Remaining: {len(kept)}")

# Backup original
import shutil
shutil.copy2(jobs_path, backup_path)

# Save cleaned
with open(jobs_path, 'w') as f:
    json.dump(kept, f, indent=2, ensure_ascii=False)

print(f"\nBackup saved to: {backup_path}")
print("\nSample removed (stale):")
for reason, j in removed[:5]:
    print(f"  [{reason}] {j.get('title','?')} @ {j.get('company','?')} (date: {j.get('date_posted') or j.get('posted_date') or j.get('created_at') or j.get('first_seen', 'N/A')})")
