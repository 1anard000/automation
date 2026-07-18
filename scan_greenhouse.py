#!/usr/bin/env python3
"""Scan Greenhouse boards for OKX, Stripe, Airwallex, Coupang, Agoda"""
import json
import urllib.request
import urllib.error
import sys
from datetime import datetime, timezone

COMPANIES = {
    "okx": "OKX",
    "stripe": "Stripe",
    "airwallex": "Airwallex",
    "coupang": "Coupang",
    "agoda": "Agoda",
    "affirm": "Affirm",
    "airbnb": "Airbnb",
    "anthropic": "Anthropic",
    "rippling": "Rippling",
    "ramp": "Ramp",
}

# Load existing URLs
existing_path = "/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json"
with open(existing_path) as f:
    existing_jobs = json.load(f)

existing_urls = set(j.get("url", "") for j in existing_jobs)
existing_titles = set()
for j in existing_jobs:
    key = (j.get("company", ""), j.get("title", ""), j.get("url", ""))
    existing_titles.add(key)

new_jobs = []
keywords_pm = ["product manager", "product", "strategy", "bizops", "business operations",
               "growth", "general manager", "commercial", "partnerships", "GM",
               "head of", "senior manager", "lead", "director of product"]
keywords_skip = ["intern", "internship", "interns", "vice president", "managing director",
                 "vp of", "c-level", "chief ", "staff engineer", "distinguished"]

for company_slug, company_name in COMPANIES.items():
    url = f"https://boards-api.greenhouse.io/v1/jobs/{company_slug}?content=true"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ⚠ Failed to fetch {company_name}: {e}")
        continue

    jobs = data.get("jobs", [])
    print(f"  📋 {company_name}: {len(jobs)} total jobs")
    found = 0

    for job in jobs:
        title = job.get("title", "")
        location = job.get("location", {}).get("name", "")
        job_id = job.get("id", "")
        job_url = f"https://boards-api.greenhouse.io/{company_slug}/jobs/{job_id}#app"
        posted_at = job.get("updated_at", job.get("created_at", ""))

        title_lower = title.lower()

        # Skip irrelevant roles
        if any(skip in title_lower for skip in keywords_skip):
            continue

        # Check if matches PM/Strategy profile
        is_match = any(kw in title_lower for kw in keywords_pm)

        # Focus on APAC locations
        location_lower = location.lower()
        apac_keywords = ["shenzhen", "hong kong", "hk", "guangzhou", "shanghai",
                         "singapore", "bangkok", "tokyo", "seoul", "asia",
                         "taipei", "malaysia", "indonesia", "philippines"]
        is_apac = any(kw in location_lower for kw in apac_keywords)

        # For APAC matches or strategy roles anywhere
        if not is_match:
            continue

        # Check if new
        if job_url in existing_urls:
            continue
        if (company_name, title, job_url) in existing_titles:
            continue

        found += 1
        new_jobs.append({
            "title": title,
            "company": company_name,
            "location": location,
            "url": job_url,
            "source": "greenhouse_api",
            "salary": "Not listed",
            "scanned_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "posted_date": posted_at,
            "quality_score": 75 if is_apac else 65,
            "quality_tier": "B",
            "grade": "B",
            "english_friendly": True,
            "platform": "Greenhouse",
            "low_quality": False,
        })

    print(f"     → {found} new matching jobs")

# Save new jobs
print(f"\n=== Total new jobs found: {len(new_jobs)} ===")
for j in new_jobs:
    print(f"  📌 {j['title']} @ {j['company']} | {j['location']}")

# Append to existing
if new_jobs:
    existing_jobs.extend(new_jobs)
    with open(existing_path, 'w', encoding='utf-8') as f:
        json.dump(existing_jobs, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved {len(new_jobs)} new jobs to database (total: {len(existing_jobs)})")
else:
    print("\nℹ️  No new jobs to add")
