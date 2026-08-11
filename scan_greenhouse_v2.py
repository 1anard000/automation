#!/usr/bin/env python3
"""Comprehensive Greenhouse API scan for all known boards."""
import json
import os
import subprocess
from datetime import datetime

WORKSPACE = "/Users/iancolrick/.openclaw/workspace"
DB_PATH = os.path.join(WORKSPACE, "OKComputer_职位搜索清单", "jobs-all.json")

# Load existing jobs
existing = json.load(open(DB_PATH))
existing_urls = set(j.get("url", "") for j in existing)
existing_keys = set(
    (j.get("title", "").lower().strip(), j.get("company", "").lower().strip())
    for j in existing
)

# Filters
TARGET_KEYWORDS = [
    "product manager", "strategy", "bizops", "business operations", "growth",
    "gm", "general manager", "lead", "senior manager", "commercial",
    "cross-border", "marketplace", "fintech", "ai product", "payments",
    "partnership", "business development", "operations manager",
    "senior", "principal", "head of", "director"
]
SKIP_KEYWORDS = [
    "director", "vp ", "vice president", "managing director", "intern",
    "internship", "administration", "marketing", "hr ", "legal", "design",
    "engineer", "developer", "recruiter", "accounting", "finance manager",
    "sales manager", "account executive", "data scientist", "consultant",
    "researcher", "analyst", "content", "copywriter", "social media",
    "graphic designer", "ux designer", "frontend", "backend", "devops",
    "sre", "security engineer", "technical writer", "qa", "quality assurance"
]
ASIA_KEYWORDS = [
    "shenzhen", "hong kong", "singapore", "guangzhou", "shanghai",
    "taipei", "tokyo", "asia", "apac", "remote"
]
MIN_SALARY_RMB = 15000

# Greenhouse boards to scan
BOARDS = {
    "okx": "OKX",
    "stripe": "Stripe",
    "coupang": "Coupang",
    "bybit": "Bybit",
    "figma": "Figma",
}

all_new = []
scan_stats = {}

for slug, company_name in BOARDS.items():
    json_file = f"/tmp/gh_{slug}.json"
    try:
        with open(json_file) as f:
            data = json.load(f)
        jobs = data.get("jobs", [])
        scan_stats[company_name] = {"total": len(jobs), "new": 0}
        
        for job in jobs:
            title = job.get("title", "")
            title_lower = title.lower()
            location = job.get("location", {}).get("name", "")
            job_url = job.get("absolute_url", "")
            
            # Skip if already exists
            if job_url in existing_urls:
                continue
            key = (title_lower.strip(), company_name.lower().strip())
            if key in existing_keys:
                continue
            
            # Filter: must be in Asia
            if not any(k in location.lower() for k in ASIA_KEYWORDS):
                continue
            
            # Filter: skip Director/VP/Intern and unrelated roles
            if any(k in title_lower for k in SKIP_KEYWORDS):
                continue
            
            # Filter: must match target profile
            if not any(k in title_lower for k in TARGET_KEYWORDS):
                continue
            
            # Add new job
            new_job = {
                "title": title,
                "company": company_name,
                "location": location,
                "salary": "Not listed",
                "url": job_url,
                "source": f"greenhouse_{slug}",
                "role_type": "target_profile",
                "description": f"Greenhouse listing for {company_name} in {location}",
                "scanned_date": datetime.now().strftime("%Y-%m-%d"),
                "posted_date": job.get("updated_at", ""),
                "english_friendly": True,
                "quality_tier": "A" if any(k in title_lower for k in ["senior", "principal", "lead", "manager"]) else "B"
            }
            all_new.append(new_job)
            existing_urls.add(job_url)
            existing_keys.add(key)
            scan_stats[company_name]["new"] += 1
            
    except Exception as e:
        scan_stats[company_name] = {"error": str(e)}

# Add new jobs to database
if all_new:
    existing.extend(all_new)
    with open(DB_PATH, "w") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

# Print results
print(f"\n=== Scan Complete: {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
print(f"New jobs found: {len(all_new)}")
for company, stats in scan_stats.items():
    if "error" in stats:
        print(f"  {company}: ERROR - {stats['error']}")
    else:
        print(f"  {company}: {stats['total']} total, {stats['new']} new")

print(f"\n=== New Jobs ===")
for j in all_new[:20]:  # Show first 20
    print(f"  📌 {j['title']} @ {j['company']} ({j['location']})")
    print(f"     {j['url']}")

print(f"\n=== Database ===")
print(f"Total jobs now: {len(existing)}")
