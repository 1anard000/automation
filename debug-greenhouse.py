#!/usr/bin/env python3
"""Debug Greenhouse API access."""
import subprocess, json

companies = {
    "okx": "OKX",
    "stripe": "Stripe",
    "airwallex": "Airwallex",
}

for slug, name in companies.items():
    url = f"https://boards-api.greenhouse.io/v1/jobs/{slug}?content=false"
    result = subprocess.run(
        ["curl", "-s", "-w", "\nHTTP_CODE:%{http_code}", "--max-time", "15", url],
        capture_output=True, text=True, timeout=20
    )
    lines = result.stdout.strip().split("\n")
    http_code = lines[-1] if lines else "unknown"
    body = "\n".join(lines[:-1])
    print(f"\n--- {name} ({slug}) ---")
    print(f"HTTP: {http_code}")
    print(f"Body (first 500 chars): {body[:500]}")
    print(f"stderr: {result.stderr[:200]}")
