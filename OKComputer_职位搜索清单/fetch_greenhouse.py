#!/usr/bin/env python3
"""Fetch relevant jobs from Greenhouse boards."""
import json
import urllib.request
import sys
import hashlib

COMPANIES = ["okx", "stripe", "airwallex", "coupang"]
KEYWORDS = ["product manager", "strategy", "bizops", "business operations", "growth", 
            "general manager", "gm", "product lead", "senior product", "senior strategy",
            "business development", "commercial", "head of product"]
SKIP_KEYWORDS = ["intern", "internship", "director", "vp", "vice president", "managing director", "chief"]

results = []
for company in COMPANIES:
    try:
        url = f"https://boards-api.greenhouse.io/v1/jobs/{company}?content=true"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        jobs = data.get("jobs", [])
        print(f"{company}: {len(jobs)} total jobs", file=sys.stderr)
        for j in jobs:
            title = j.get("title", "").lower()
            loc = j.get("location", {}).get("name", "")
            abs_url = j.get("absolute_url", "")
            desc = j.get("content", "")[:2000].lower() if j.get("content") else ""
            
            # Must match at least one keyword
            matched = any(kw in title for kw in KEYWORDS)
            if not matched:
                continue
            
            # Skip interns/directors/VPs
            if any(sk in title for sk in SKIP_KEYWORDS):
                continue
            
            # Skip non-Asia locations (unless remote)
            asia_locs = ["singapore", "hong kong", "shenzhen", "shanghai", "guangzhou", "beijing", "taipei", "tokyo", "seoul", "bangkok", "jakarta", "vietnam", "malaysia", "india"]
            is_remote = "remote" in loc.lower() or "anywhere" in loc.lower()
            is_asia = any(al in loc.lower() for al in asia_locs)
            
            if not is_asia and not is_remote:
                continue
            
            job_id = hashlib.md5(f"{company}-{abs_url}".encode()).hexdigest()[:12]
            
            results.append({
                "company": company.title(),
                "title": j.get("title", ""),
                "location": loc,
                "url": abs_url,
                "source": "greenhouse",
                "job_id": job_id
            })
    except Exception as e:
        print(f"Error fetching {company}: {e}", file=sys.stderr)

print(json.dumps(results, indent=2))
