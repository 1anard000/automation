#!/usr/bin/env python3
"""Extract greenhouse board names from existing URLs and try the API."""
import json, urllib.request, re

jobs = json.load(open('OKComputer_职位搜索清单/jobs-all.json'))

# Extract greenhouse board names from URLs
boards = set()
for j in jobs:
    url = j.get('url', '')
    # Match patterns like greenhouse.io/BOARD/jobs/ID or job-boards.greenhouse.io/BOARD/jobs/ID
    m = re.search(r'greenhouse\.io/([^/]+)/jobs/', url)
    if m:
        boards.add(m.group(1))

print("Greenhouse boards from existing URLs:")
for b in sorted(boards):
    print(f"  - {b}")

# Try each via API
print("\nTesting API:")
for board in sorted(boards):
    try:
        url = f'https://boards-api.greenhouse.io/v1/jobs/{board}?content=false'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            count = len(data.get('jobs', []))
            print(f"  ✅ {board}: {count} jobs")
    except Exception as e:
        print(f"  ❌ {board}: {e}")
