#!/usr/bin/env python3
"""Deduplicate, grade, and write final scan results."""
import json

with open("/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/scan-latest.json") as f:
    jobs = json.load(f)

# Deduplicate by (title, company, location)
seen = set()
unique = []
for j in jobs:
    key = (j["title"].strip().lower(), j["company"].strip().lower(), j["location"].strip().lower())
    if key not in seen:
        seen.add(key)
        unique.append(j)

# Target cities
TARGET = {"shenzhen", "shenzhen", "hong kong", "hongkong", "hk", "guangzhou", 
          "guangzhou", "shanghai", "singapore", "bangkok", "taipei", "tokyo", 
          "seoul", "jakarta", "kuala lumpur", "manila", "ho chi minh", "hcmc",
          "mumbai", "delhi", "bangalore", "bengaluru", "sydney", "melbourne"}

def in_target_city(loc):
    loc_l = loc.lower()
    return any(c in loc_l for c in TARGET)

def grade_job(j):
    title = j["title"].lower()
    loc = j["location"].lower()
    
    # Must be in target city
    if not in_target_city(loc):
        return None
    
    # Exclude pure engineering/HR/legal
    skip = ["engineer", "architect", "sre", "devops", "recruiter", "talent acquisition",
            "hr ", "human resources", "legal ", "counsel", "compliance ", "privacy",
            "data science", "data engineer", "security operation", "devrel"]
    if any(s in title for s in skip):
        return None
    
    # Score
    score = 0
    role_match = j.get("role_type", "") in ["product", "strategy", "expansion", "bd", "gm", "ops"]
    if role_match:
        score += 3
    
    ai_related = any(w in title for w in ["ai", "agent", "machine learning", "intelligence"])
    if ai_related:
        score += 2
    
    senior_title = any(w in title for w in ["director", "head of", "vp", "vice president", 
                                              "senior product", "senior manager", "principal",
                                              "general manager", "gm", "chief", "managing director"])
    if senior_title:
        score += 2
    
    crypto_fintech = any(w in title for w in ["trading", "payment", "fintech", "crypto", 
                                                "defi", "web3", "wallet", "institutional"])
    if crypto_fintech:
        score += 1
    
    # Target cities bonus
    core_city = any(c in loc for c in ["singapore", "shenzhen", "hong kong", "shanghai", "guangzhou"])
    if core_city:
        score += 2
    
    if score >= 7:
        return "A-1"
    elif score >= 5:
        return "A-2"
    elif score >= 3:
        return "B"
    else:
        return "C"

# Grade and filter
graded = []
for j in unique:
    g = grade_job(j)
    if g:
        j["grade"] = g
        graded.append(j)

# Sort by grade
grade_order = {"A-1": 0, "A-2": 1, "B": 2, "C": 3}
graded.sort(key=lambda x: (grade_order.get(x["grade"], 9), x["company"]))

# Stats
from collections import Counter
grade_counts = Counter(j["grade"] for j in graded)
city_counts = Counter()
for j in graded:
    for c in ["Singapore", "Hong Kong", "Shenzhen", "Shanghai", "Guangzhou", 
              "Bangkok", "Tokyo", "Seoul", "Sydney", "Mumbai", "Kuala Lumpur"]:
        if c.lower() in j["location"].lower():
            city_counts[c] += 1

company_counts = Counter(j["company"] for j in graded)

print(f"\n=== SCAN RESULTS ===")
print(f"Total unique APAC roles: {len(unique)}")
print(f"After grading/filtering: {len(graded)}")
print(f"\nBy Grade:")
for g in ["A-1", "A-2", "B", "C"]:
    print(f"  {g}: {grade_counts.get(g, 0)}")
print(f"\nBy City:")
for c, n in city_counts.most_common():
    print(f"  {c}: {n}")
print(f"\nBy Company:")
for c, n in company_counts.most_common(10):
    print(f"  {c}: {n}")

print(f"\n=== TOP PICKS ===")
for j in graded[:15]:
    print(f"  [{j['grade']}] {j['title']} | {j['company']} | {j['location']}")

# Save
with open("/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/scan-latest.json", "w") as f:
    json.dump(graded, f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(graded)} graded jobs to scan-latest.json")
