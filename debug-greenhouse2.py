#!/usr/bin/env python3
"""Debug Greenhouse API with redirect following."""
import subprocess, json

companies = {
    "okx": "OKX",
    "stripe": "Stripe",
    "airwallex": "Airwallex",
}

for slug, name in companies.items():
    url = f"https://boards-api.greenhouse.io/v1/jobs/{slug}?content=false"
    result = subprocess.run(
        ["curl", "-s", "-L", "-w", "\nHTTP_CODE:%{http_code}", "--max-time", "15", url],
        capture_output=True, text=True, timeout=20
    )
    lines = result.stdout.strip().split("\n")
    http_code = lines[-1] if lines else "unknown"
    body = "\n".join(lines[:-1])
    print(f"\n--- {name} ({slug}) ---")
    print(f"HTTP: {http_code}")
    if body:
        try:
            data = json.loads(body)
            jobs = data.get("jobs", [])
            print(f"Jobs count: {len(jobs)}")
            if jobs:
                print(f"First: {jobs[0].get('title')} @ {jobs[0].get('location',{}).get('name')}")
        except:
            print(f"Body (first 300 chars): {body[:300]}")
    else:
        print(f"Empty response. stderr: {result.stderr[:200]}")
