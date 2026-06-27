#!/usr/bin/env python3
"""Career OS Cron — Deep analysis for strategy update."""
import json
import os
from collections import Counter, defaultdict

BASE = "/Users/iancolrick/.openclaw/workspace/career-os"
DB_PATH = os.path.join(BASE, "OKComputer_职位搜索清单/jobs-all.json")

def load_db():
    with open(DB_PATH) as f:
        data = json.load(f)
    if isinstance(data, dict):
        for key in ["jobs", "results", "data", "listings"]:
            if key in data and isinstance(data[key], list):
                return data[key]
        if all(isinstance(v, dict) for v in list(data.values())[:3]):
            return list(data.values())
        return []
    return data if isinstance(data, list) else []

def analyze(jobs):
    # Track companies with score-80+ roles
    company_high_scores = defaultdict(list)
    # Track cross-border roles specifically
    cross_border_roles = []
    # Track AI product roles
    ai_roles = []
    # Track strategy roles
    strategy_roles = []
    # Track roles in target cities
    target_cities = {"Singapore", "Hong Kong", "Shenzhen", "Shanghai"}
    
    for j in jobs:
        company = j.get("company", "unknown")
        score = j.get("quality_score", 0)
        city = j.get("location_norm", j.get("city", j.get("location", "")))
        cat = j.get("category", "")
        title = j.get("title", j.get("en_title", ""))
        url = j.get("url", "")
        status = j.get("status", "not_applied")
        english = j.get("english_friendly", False)
        direct = j.get("has_direct_link", False)
        
        if score and score >= 80:
            company_high_scores[company].append({
                "score": score,
                "title": title,
                "city": city,
                "category": cat,
                "url": url,
                "status": status,
                "english": english,
                "direct": direct
            })
        
        if cat == "cross_border" or "cross-border" in title.lower() or "跨境" in title:
            cross_border_roles.append({"score": score, "company": company, "title": title, "city": city, "url": url})
        
        if cat == "ai_product" or (title and ("ai" in title.lower() or "ml" in title.lower())):
            ai_roles.append({"score": score or 0, "company": company, "title": title, "city": city, "url": url})
        
        if cat == "strategy":
            strategy_roles.append({"score": score or 0, "company": company, "title": title, "city": city, "url": url})
    
    print("=== DEEP ANALYSIS: NEW OPPORTUNITIES ===\n")
    
    # 1. Companies with most high-score roles
    print("--- Company Opportunity Density (Score 80+) ---")
    sorted_companies = sorted(company_high_scores.items(), key=lambda x: -len(x[1]))
    for company, roles in sorted_companies[:25]:
        scores = [r["score"] for r in roles]
        cities = set(r["city"] for r in roles)
        english_roles = sum(1 for r in roles if r["english"])
        direct_roles = sum(1 for r in roles if r["direct"])
        print(f"  {company}: {len(roles)} roles (max {max(scores)}, avg {sum(scores)/len(scores):.0f}) | Cities: {', '.join(cities)} | English: {english_roles} | Direct: {direct_roles}")
        for r in sorted(roles, key=lambda x: -x["score"])[:3]:
            print(f"    [{r['score']}] {r['title'][:70]} ({r['city']})")
    
    # 2. Cross-border roles (Ian's differentiator)
    print(f"\n--- Cross-Border Roles ({len(cross_border_roles)} found) ---")
    cb_sorted = sorted(cross_border_roles, key=lambda x: -x.get("score", 0))
    for r in cb_sorted[:20]:
        print(f"  [{r.get('score', 0)}] {r['company']}: {r['title'][:60]} ({r['city']})")
    
    # 3. AI Product roles
    print(f"\n--- AI Product Roles ({len(ai_roles)} found) ---")
    ai_sorted = sorted(ai_roles, key=lambda x: -x.get("score", 0))
    for r in ai_sorted[:15]:
        print(f"  [{r.get('score', 0)}] {r['company']}: {r['title'][:60]} ({r['city']})")
    
    # 4. Strategy roles
    print(f"\n--- Strategy Roles ({len(strategy_roles)} found) ---")
    strat_sorted = sorted(strategy_roles, key=lambda x: -x.get("score", 0))
    for r in strat_sorted[:15]:
        print(f"  [{r.get('score', 0)}] {r['company']}: {r['title'][:60]} ({r['city']})")
    
    # 5. Direct-apply score-80+ roles (easiest to submit)
    print(f"\n--- Direct-Apply Score-80+ Roles (QUICK WINS) ---")
    direct_high = []
    for j in jobs:
        if j.get("quality_score", 0) >= 80 and j.get("has_direct_link"):
            direct_high.append(j)
    direct_high.sort(key=lambda x: -x.get("quality_score", 0))
    for j in direct_high[:30]:
        print(f"  [{j.get('quality_score', 0)}] {j.get('company', '')}: {j.get('title', '')[:60]} ({j.get('location_norm', j.get('location', ''))})")
    
    # 6. English + score 80+ roles not yet applied
    print(f"\n--- English Score-80+ UNAPPLIED (TOP 30) ---")
    english_high = [j for j in jobs if j.get("quality_score", 0) >= 80 and j.get("english_friendly") and j.get("status") != "applied"]
    english_high.sort(key=lambda x: -x.get("quality_score", 0))
    for j in english_high[:30]:
        print(f"  [{j.get('quality_score', 0)}] {j.get('company', '')}: {j.get('title', '')[:60]} ({j.get('location_norm', j.get('location', ''))})")
    
    # 7. NEW companies not in strategy doc
    print(f"\n--- Companies with 2+ Score-80+ Roles (potential new targets) ---")
    for company, roles in sorted_companies:
        if len(roles) >= 2:
            avg_score = sum(r["score"] for r in roles) / len(roles)
            if avg_score >= 80:
                print(f"  {company}: {len(roles)} roles, avg {avg_score:.0f}")

if __name__ == "__main__":
    jobs = load_db()
    if jobs:
        analyze(jobs)
    else:
        print("ERROR: No jobs found")
