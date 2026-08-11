#!/usr/bin/env python3
"""Scan job sources - fix API calls."""
import json
import urllib.request
import urllib.parse
import os
from datetime import datetime, timezone

def try_greenhouse(slug):
    """Try various greenhouse board IDs."""
    urls_to_try = [
        f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=false",
        f"https://boards-api.greenhouse.io/v1/jobs/{slug}",
    ]
    for url in urls_to_try:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                jobs = data.get("jobs", [])
                print(f"  SUCCESS: {url} -> {len(jobs)} jobs")
                return data
        except Exception as e:
            pass
    return None

# Test various greenhouse slugs
test_companies = ["okx", "okxcom", "airwallex", "stripe", "agoda", "coupang"]
for company in test_companies:
    print(f"\nTrying {company}...")
    result = try_greenhouse(company)
    if result:
        jobs = result.get("jobs", [])
        for j in jobs[:5]:
            print(f"    {j.get('title', 'N/A')} | {j.get('location', {}).get('name', 'N/A')}")
