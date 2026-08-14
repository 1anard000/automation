#!/usr/bin/env python3
"""Debug: test Greenhouse API endpoints."""
import urllib.request
import json
import sys

urls = [
    "https://boards-api.greenhouse.io/v1/jobs/okx",
    "https://boards-api.greenhouse.io/v1/boards/okx/jobs",
    "https://boards-api.greenhouse.io/v1/boards/okx",
]

for url in urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            parsed = json.loads(data)
            if isinstance(parsed, dict):
                print(f"OK: {url} -> keys: {list(parsed.keys())[:10]}")
                if "jobs" in parsed:
                    print(f"  Jobs count: {len(parsed['jobs'])}")
            elif isinstance(parsed, list):
                print(f"OK: {url} -> list of {len(parsed)} items")
            else:
                print(f"OK: {url} -> type: {type(parsed)}")
    except Exception as e:
        print(f"ERR: {url} -> {e}")
