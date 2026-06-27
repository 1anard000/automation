#!/usr/bin/env python3
"""Career OS Cron — Focus analysis: find new opportunities, case-variant companies, and cross-border fits."""
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
        return []
    return data if isinstance(data, list) else []

def analyze(jobs):
    # 1. Case-variant company detection
    company_variants = defaultdict(list)
    for j in jobs:
        c = j.get("company", "")
        if c:
            company_variants[c.lower().strip()].append(c)
    
    print("=== CASE-VARIANT COMPANIES ===")
    for normalized, variants in company_variants.items():
        unique_variants = set(variants)
        if len(unique_variants) > 1:
            print(f"  '{normalized}': {unique_variants}")
    
    # 2. Companies with score-80+ (using normalized names)
    company_high = defaultdict(list)
    for j in jobs:
        score = j.get("quality_score") or 0
        if score >= 80:
            c = j.get("company", "unknown")
            company_high[c].append({
                "score": score,
                "title": j.get("title", ""),
                "city": j.get("location_norm", j.get("location", "")),
                "direct": j.get("has_direct_link", False),
                "english": j.get("english_friendly", False),
                "status": j.get("status", "not_applied")
            })
    
    # Merge case variants
    merged = defaultdict(list)
    variant_map = {}
    for normalized, variants in company_variants.items():
        canonical = max(set(variants), key=variants.count)
        for v in set(variants):
            variant_map[v] = canonical
    
    for company, roles in company_high.items():
        canonical = variant_map.get(company, company)
        merged[canonical].extend(roles)
    
    print("\n=== TOP COMPANIES BY SCORE-80+ (MERGED) ===")
    sorted_merged = sorted(merged.items(), key=lambda x: -len(x[1]))
    for company, roles in sorted_merged[:30]:
        scores = [r["score"] for r in roles]
        direct = sum(1 for r in roles if r["direct"])
        english = sum(1 for r in roles if r["english"])
        cities = set(r["city"] for r in roles)
        applied = sum(1 for r in roles if r["status"] == "applied")
        print(f"  {company}: {len(roles)} roles (max {max(scores)}, avg {sum(scores)//len(scores)}) | Direct: {direct} | English: {english} | Applied: {applied} | Cities: {', '.join(cities)}")
        for r in sorted(roles, key=lambda x: -x["score"])[:3]:
            print(f"    [{r['score']}] {r['title'][:65]} ({r['city']}) {'✅APPLIED' if r['status']=='applied' else ''}")
    
    # 3. Cross-border roles in target cities
    print("\n=== CROSS-BORDER ROLES IN TARGET CITIES ===")
    target = {"Singapore", "Hong Kong", "Shenzhen", "Shanghai", "HK", "SG", "SZ", "SH"}
    for j in jobs:
        score = j.get("quality_score") or 0
        cat = j.get("category", "")
        title = j.get("title", "")
        city = j.get("location_norm", j.get("location", ""))
        
        is_cb = cat == "cross_border" or "cross-border" in title.lower() or "跨境" in title
        in_target = any(t in city for t in ["Singapore", "Hong Kong", "Shenzhen", "Shanghai", "HK", "SG", "SZ", "SH", "深圳", "上海", "香港"])
        
        if is_cb and in_target and score >= 70:
            print(f"  [{score}] {j.get('company', '')}: {title[:65]} ({city})")
    
    # 4. Direct-apply score 80+ (actual check for None)
    print("\n=== DIRECT-APPLY SCORE-80+ (QUICK WINS) ===")
    count = 0
    for j in jobs:
        score = j.get("quality_score") or 0
        if score >= 80 and j.get("has_direct_link"):
            count += 1
            if count <= 30:
                print(f"  [{score}] {j.get('company', '')}: {j.get('title', '')[:65]} ({j.get('location_norm', j.get('location', ''))})")
    print(f"  Total: {count}")

if __name__ == "__main__":
    jobs = load_db()
    analyze(jobs)
