#!/usr/bin/env python3
"""Try various Greenhouse company slugs."""
import subprocess, json

# Try some known slugs — Greenhouse API recently changed
slugs_to_try = [
    "okx", "OKX", "okx-1", "okxglobal",
    "stripe", "stripeinc",
    "airwallex", "airwallex-global",
    "coupang", "coupang-global",
]

for slug in slugs_to_try:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    result = subprocess.run(
        ["curl", "-s", "-L", "-w", "\nHTTP:%{http_code}", "--max-time", "10", url],
        capture_output=True, text=True, timeout=15
    )
    lines = result.stdout.strip().split("\n")
    http_code = [l for l in lines if l.startswith("HTTP:")]
    http_code = http_code[-1] if http_code else "?"
    body = "\n".join(l for l in lines if not l.startswith("HTTP:"))
    
    if "200" in http_code:
        try:
            data = json.loads(body)
            count = len(data.get("jobs", []))
            print(f"✅ {slug}: {count} jobs — http={http_code}")
        except:
            print(f"⚠️  {slug}: 200 but parse failed — http={http_code}")
    elif "404" in http_code:
        print(f"❌ {slug}: not found — http={http_code}")
    elif "403" in http_code:
        print(f"🚫 {slug}: forbidden — http={http_code}")
    else:
        print(f"❓ {slug}: http={http_code} body={body[:100]}")
