#!/usr/bin/env python3
"""Check existing Greenhouse URLs in DB and try to find working boards."""
import json, urllib.request

# Load existing jobs to find Greenhouse patterns
jobs = json.load(open('OKComputer_职位搜索清单/jobs-all.json'))

# Find all greenhouse URLs
gh_urls = set()
for j in jobs:
    url = j.get('url', '')
    if 'greenhouse' in url:
        # Extract board name from URL
        # e.g. https://boards.greenhouse.io/affirm/jobs/7752003003
        parts = url.split('/')
        if len(parts) >= 5:
            board = parts[4] if len(parts) > 4 else 'unknown'
            gh_urls.add(board)

print("Greenhouse boards found in DB:")
for b in sorted(gh_urls):
    print(f"  - {b}")

# Try to fetch a few known boards via API
test_boards = ['affirm', 'okx', 'stripe', 'airwallex', 'agoda', 'bytedance', 'shopee', 'grab']
print("\nTesting API access:")
for board in test_boards:
    try:
        url = f'https://boards-api.greenhouse.io/v1/jobs/{board}?content=false'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            count = len(data.get('jobs', []))
            print(f"  ✅ {board}: {count} jobs")
    except Exception as e:
        print(f"  ❌ {board}: {e}")
