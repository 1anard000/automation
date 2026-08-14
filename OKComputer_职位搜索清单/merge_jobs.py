#!/usr/bin/env python3
"""Merge new Greenhouse jobs into the database."""
import json
import sys

DB_PATH = "/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json"

# Load existing
with open(DB_PATH) as f:
    existing = json.load(f)

existing_urls = {j.get("url", "") for j in existing}
existing_gids = set()
for j in existing:
    gid = j.get("greenhouse_id")
    if gid:
        existing_gids.add(gid)

# Also build title-based dedup set for similar roles
existing_titles = set()
for j in existing:
    key = f"{j.get('company','').lower()}|{j.get('title','').lower().strip()}|{j.get('location','').lower().strip()}"
    existing_titles.add(key)

print(f"Existing jobs: {len(existing)}", file=sys.stderr)
print(f"Existing URLs: {len(existing_urls)}", file=sys.stderr)
print(f"Existing greenhouse IDs: {len(existing_gids)}", file=sys.stderr)

# New jobs from scan (hardcoded from the filtered scan output)
new_jobs = json.loads(sys.stdin.read())

# Filter rules
EXCLUDE_LOCATIONS = ["pakistan", "germany", "netherlands", "australia", "uk ", "united kingdom", "brazil", "india", "japan"]
SKIP_TITLES = ["director", "vp ", "vice president", "managing director", "chief", "intern"]

added = 0
skipped_existing = 0
skipped_location = 0
skipped_title = 0

for job in new_jobs:
    gid = job.get("greenhouse_id")
    url = job.get("url", "")
    title = job.get("title", "")
    location = job.get("location", "").lower()
    
    # Skip if already in DB
    if gid in existing_gids:
        skipped_existing += 1
        continue
    if url in existing_urls:
        skipped_existing += 1
        continue
    
    # Check title-based dedup
    title_key = f"{job.get('company','').lower()}|{title.lower().strip()}|{location.strip()}"
    if title_key in existing_titles:
        skipped_existing += 1
        continue
    
    # Skip Director/VP roles (per rules)
    title_lower = title.lower()
    if any(skip in title_lower for skip in SKIP_TITLES):
        skipped_title += 1
        continue
    
    # Skip non-target locations
    if any(loc in location for loc in EXCLUDE_LOCATIONS):
        skipped_location += 1
        continue
    
    # Skip "Pakistan" specifically
    if "pakistan" in location:
        skipped_location += 1
        continue
    
    # Add to database
    existing.append(job)
    existing_gids.add(gid)
    existing_urls.add(url)
    existing_titles.add(title_key)
    added += 1

print(f"\nResults:", file=sys.stderr)
print(f"  Added: {added}", file=sys.stderr)
print(f"  Skipped (existing): {skipped_existing}", file=sys.stderr)
print(f"  Skipped (location): {skipped_location}", file=sys.stderr)
print(f"  Skipped (title): {skipped_title}", file=sys.stderr)
print(f"  Total now: {len(existing)}", file=sys.stderr)

# Write updated database
with open(DB_PATH, 'w', encoding='utf-8') as f:
    json.dump(existing, f, indent=2, ensure_ascii=False)

print(f"\nDatabase updated: {DB_PATH}", file=sys.stderr)

# Also output summary of what was added
for job in existing[-added:]:
    print(f"  + {job.get('company')} | {job.get('title')} | {job.get('location')} | {job.get('url','')[:80]}")
