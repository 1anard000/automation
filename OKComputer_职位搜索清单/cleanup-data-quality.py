#!/usr/bin/env python3
"""Nightly data quality cleanup: remove generic search pages, flag missing companies."""
import json
import os

jobs_path = os.path.join(os.path.dirname(__file__), 'jobs-all.json')
with open(jobs_path) as f:
    jobs = json.load(f)

original_count = len(jobs)

# Identify generic search pages (not real job postings)
generic_patterns = [
    'zhaopin/', 'zhaopin?',  # generic search pages
    'zhipin.com/zhaopin/',   # Boss直聘 search pages
    'liepin.com/zhaopin/',   # Liepin search pages
    'linkedin.com/jobs/search',  # LinkedIn search pages (not specific)
]

def is_generic_search(job):
    url = job.get('url', '')
    title = job.get('title', '')
    # Check if URL is a search page (not a specific job)
    for p in generic_patterns:
        if p in url.lower():
            return True
    # Check if title ends with "招聘" and no company name
    if title.endswith('招聘') and not job.get('company', '').strip():
        return True
    return False

# Separate generic from real jobs
generic = []
real = []
for j in jobs:
    if is_generic_search(j):
        generic.append(j)
    else:
        real.append(j)

print(f"Original: {original_count}")
print(f"Generic search pages found: {len(generic)}")
print(f"Real job postings remaining: {len(real)}")

# Save cleaned jobs
with open(jobs_path, 'w') as f:
    json.dump(real, f, indent=2, ensure_ascii=False)

# Log what was removed
print("\nRemoved generic entries:")
for j in generic[:10]:
    print(f"  - {j.get('title','?')} ({j.get('url','')[:50]})")

if len(generic) > 10:
    print(f"  ... and {len(generic)-10} more")
