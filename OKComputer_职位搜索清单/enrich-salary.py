#!/usr/bin/env python3
"""Estimate missing salaries based on title seniority + location + existing data patterns."""
import json, re

SALARY_RANGES = {
    # Monthly estimates in local currency
    # Singapore SGD
    "singapore": {"junior": (5000, 8000), "mid": (8000, 14000), "senior": (14000, 25000), "director": (22000, 40000), "currency": "SGD"},
    # Hong Kong HKD
    "hong kong": {"junior": (25000, 40000), "mid": (40000, 65000), "senior": (65000, 100000), "director": (90000, 150000), "currency": "HKD"},
    # China RMB
    "china": {"junior": (15000, 25000), "mid": (25000, 45000), "senior": (45000, 75000), "director": (70000, 120000), "currency": "RMB"},
    # US/Remote USD
    "us": {"junior": (8000, 13000), "mid": (13000, 20000), "senior": (20000, 30000), "director": (28000, 45000), "currency": "USD"},
    # Default USD
    "default": {"junior": (6000, 10000), "mid": (10000, 18000), "senior": (18000, 28000), "director": (25000, 40000), "currency": "USD"},
}

TITLE_LEVELS = {
    "director": ["director", "head of", "vp ", "vice president", "chief"],
    "senior": ["senior", "sr.", "sr ", "staff", "principal", "lead"],
    "mid": ["product manager", "pm ", "产品经理"],
    "junior": ["junior", "jr.", "associate", "assistant", "intern"],
}

def classify_location(loc):
    loc = (loc or "").lower()
    if any(k in loc for k in ["singapore", "sg"]):
        return "singapore"
    if any(k in loc for k in ["hong kong", "hk"]):
        return "hong kong"
    if any(k in loc for k in ["china", "beijing", "shanghai", "深圳", "杭州", "广州", "cn"]):
        return "china"
    if any(k in loc for k in ["us", "united states", "san francisco", "new york", "seattle", "remote us"]):
        return "us"
    return "default"

def classify_seniority(title):
    title = (title or "").lower()
    for level, keywords in TITLE_LEVELS.items():
        if any(kw in title for kw in keywords):
            return level
    return "mid"

def estimate_salary(title, location):
    region = classify_location(location)
    level = classify_seniority(title)
    band = SALARY_RANGES[region]
    low, high = band[level]
    currency = band["currency"]
    return f"(est) {currency} {low:,}-{high:,}/mo"

def main():
    with open("jobs-all.json") as f:
        jobs = json.load(f)
    
    enriched = 0
    for j in jobs:
        has_salary = j.get("salary_range") or j.get("salary")
        if has_salary:
            continue
        title = j.get("title", "")
        location = j.get("location", "")
        if not title:
            continue
        j["salary"] = estimate_salary(title, location)
        j["salary_source"] = "estimation"
        enriched += 1
    
    with open("jobs-all.json", "w") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    
    # Stats
    with_sal = sum(1 for j in jobs if j.get("salary_range") or j.get("salary"))
    print(f"Enriched {enriched} jobs with salary estimates")
    print(f"Total jobs with salary: {with_sal}/{len(jobs)} ({with_sal*100//len(jobs)}%)")

if __name__ == "__main__":
    main()
