#!/usr/bin/env python3
import json
import urllib.request
import urllib.error
import ssl
import sys

def fetch_jobs(company):
    url = f"https://boards-api.greenhouse.io/v1/jobs/{company}"
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

# Test with just one company
result = fetch_jobs('okx')
print(json.dumps(result, indent=2)[:2000])
