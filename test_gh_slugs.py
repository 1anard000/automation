#!/usr/bin/env python3
"""Test Greenhouse API slugs"""
import urllib.request
import json

# Try different slug formats
slugs = [
    "okx", "okx-com", "okx-global", "okx1",
    "stripe", "stripe-inc", "stripe-hk",
    "airwallex", "airwallex-inc",
    "agoda", "agoda-com", "agoda-co-ltd",
    "affirm", "affirm-inc",
    "coupang",
    "anthropic", "anthropic-pbc",
]

for slug in slugs:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            name = data.get("name", "?")
            jobs_url = data.get("jobs_url", "?")
            print(f"  ✅ {slug} → {name} ({jobs_url})")
    except Exception as e:
        print(f"  ❌ {slug} → {e}")
