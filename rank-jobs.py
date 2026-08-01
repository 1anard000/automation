#!/usr/bin/env python3
"""Extract top target-profile jobs from the new batch."""
import json

db = json.load(open("/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json"))
scanned = "2026-08-02"
new_jobs = [j for j in db if j.get("scanned_date") == scanned]

# Priority: HK/SZ/SG > other Asia
# PM/Strategy/Growth > Ops/Eng
PRIORITY_LOCATIONS = ["shenzhen", "hong kong", "singapore"]
PRIORITY_KEYWORDS = ["product manager", "strategy", "growth", "bizops", "operations manager", "commercial", "analytics"]
SKIP_KEYWORDS = ["security", "compliance", "aml", "cft", "due diligence", "treasury", "finance operations", "engineering", "data scientist", "data engineer"]

def priority_score(j):
    score = 0
    loc = j.get("location", "").lower()
    title = j.get("title", "").lower()
    if any(k in loc for k in ["shenzhen", "hong kong"]):
        score += 10
    elif "singapore" in loc:
        score += 8
    elif "tokyo" in loc or "taipei" in loc:
        score += 5
    elif "bangkok" in loc:
        score += 3
    
    for kw in PRIORITY_KEYWORDS:
        if kw in title:
            score += 5
    for kw in SKIP_KEYWORDS:
        if kw in title:
            score -= 3
    
    return score

scored = [(priority_score(j), j) for j in new_jobs]
scored.sort(key=lambda x: -x[0])

print(f"Total new jobs: {len(new_jobs)}")
print()
print("=== TOP TARGET-PROFILE JOBS ===")
for score, j in scored[:15]:
    print(f"[{score:2d}] {j['title']} @ {j['company']}")
    print(f"     📍 {j['location']}")
    print(f"     🔗 {j['url']}")
    print()
