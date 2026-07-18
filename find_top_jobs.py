#!/usr/bin/env python3
"""Find the most relevant APAC jobs from today's scan"""
import json
from datetime import datetime

existing_path = "/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json"
with open(existing_path) as f:
    jobs = json.load(f)

# Get jobs scanned today (July 18 or 19)
today_jobs = [j for j in jobs if j.get("scanned_date", "").startswith("2026-07-1")]
print(f"Jobs scanned recently (Jul 18-19): {len(today_jobs)}")

# Filter for top-tier APAC roles
apac_tier1 = ["shenzhen", "hong kong", "hk", "singapore", "shanghai", "guangzhou"]
apac_tier2 = ["bangkok", "tokyo", "seoul", "taipei", "malaysia", "indonesia"]

top_jobs = []
for j in today_jobs:
    loc = j.get("location", "").lower()
    title = j.get("title", "").lower()
    
    # Skip Director/VP roles
    if "director" in title and "product director" not in title:
        continue
    if "vp " in title or "vice president" in title:
        continue
    if "intern" in title:
        continue
    if "compliance" in title:
        continue
    if "legal" in title:
        continue
    if "counsel" in title:
        continue
    
    # Score by location
    score = 0
    for kw in apac_tier1:
        if kw in loc:
            score += 3
    for kw in apac_tier2:
        if kw in loc:
            score += 2
    
    # Score by title relevance
    pm_keywords = ["product manager", "senior product", "principal product", 
                   "strategy", "growth", "bizops", "business operations",
                   "commercial", "partnerships", "marketplace", "fintech",
                   "senior manager", "lead", "head of", "monetization",
                   "data scientist", "analytics"]
    for kw in pm_keywords:
        if kw in title:
            score += 1
    
    if score >= 3:  # At least tier1 location + one keyword, or tier2 + multiple
        j["_score"] = score
        top_jobs.append(j)

# Sort by score, deduplicate by title+company
top_jobs.sort(key=lambda x: x.get("_score", 0), reverse=True)
seen = set()
unique_top = []
for j in top_jobs:
    key = (j.get("company", ""), j.get("title", ""))
    if key not in seen:
        seen.add(key)
        unique_top.append(j)

print(f"Unique top APAC jobs: {len(unique_top)}")

# Show top 25
for j in unique_top[:25]:
    loc = j.get("location", "")
    company = j.get("company", "")
    title = j.get("title", "")
    url = j.get("url", "")
    print(f"\n[{j.get('_score', 0)}] {company} | {title}")
    print(f"    📍 {loc}")
    print(f"    🔗 {url}")
