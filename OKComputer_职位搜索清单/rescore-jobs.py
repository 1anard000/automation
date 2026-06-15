#!/usr/bin/env python3
"""Re-score all jobs with quality_score=0 (or missing) based on field completeness and grade."""
import json

def score_job(j):
    s = 0
    # Core fields
    if j.get("title"): s += 15
    if j.get("company"): s += 15
    if j.get("location"): s += 10
    if j.get("salary"): s += 10
    if j.get("url"): s += 10
    if j.get("source"): s += 5
    # Grade bonus
    grade = j.get("grade", "")
    if grade == "A": s += 20
    elif grade == "B": s += 15
    elif grade == "C": s += 10
    elif grade == "D": s += 5
    # Tier bonus
    tier = j.get("quality_tier", "")
    if tier == "A": s += 10
    elif tier == "B": s += 5
    # Other enrichments
    if j.get("salary") and "$" in str(j.get("salary", "")): s += 5
    if j.get("en_title"): s += 3
    if j.get("english_friendly"): s += 2
    return min(s, 100)

def tier_from_score(s):
    if s >= 75: return "A"
    if s >= 55: return "B"
    if s >= 35: return "C"
    return "D"

def main():
    with open("jobs-all.json") as f:
        jobs = json.load(f)
    changed = 0
    for j in jobs:
        if j.get("quality_score", 0) == 0:
            j["quality_score"] = score_job(j)
            j["quality_tier"] = tier_from_score(j["quality_score"])
            changed += 1
    with open("jobs-all.json", "w") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=1)
    print(f"Re-scored {changed} jobs (was score 0)")
    # Show new distribution
    from collections import Counter
    tiers = Counter(j.get("quality_tier", "?") for j in jobs)
    scores = [j.get("quality_score", 0) for j in jobs]
    print(f"Tier distribution: {dict(tiers)}")
    print(f"Score range: {min(scores)}-{max(scores)}, avg: {sum(scores)/len(scores):.1f}")

if __name__ == "__main__":
    main()
