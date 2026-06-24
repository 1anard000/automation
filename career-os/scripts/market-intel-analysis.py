#!/usr/bin/env python3
"""Deep market intelligence from job database — salary analysis, hiring signals, company patterns."""
import json, re
from collections import defaultdict, Counter

with open("/Users/iancolrick/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json") as f:
    data = json.load(f)

jobs = data if isinstance(data, list) else data.get("jobs", data.get("results", []))

# Parse salary strings into monthly RMB/HKD/SGD ranges
def parse_salary(s):
    """Extract min/max from salary string."""
    if not s:
        return None
    # Find numbers
    nums = re.findall(r'[\d,]+(?:\.\d+)?', s.replace(',', ''))
    nums = [float(n) for n in nums if float(n) > 10]  # filter noise
    if len(nums) >= 2:
        return {"min": min(nums), "max": max(nums), "raw": s}
    elif len(nums) == 1:
        return {"min": nums[0], "max": nums[0], "raw": s}
    return None

# Company hiring analysis
company_data = defaultdict(lambda: {
    "roles": 0, "scores": [], "cities": Counter(), "categories": Counter(),
    "salaries": [], "direct_apply": 0, "high_score": 0, "director_level": 0,
    "titles": []
})

for j in jobs:
    co = j.get("company", "Unknown")
    if not co or co == "Unknown":
        continue
    score = j.get("quality_score", j.get("score", 0))
    city = j.get("location_norm", j.get("city", "Unknown"))
    cat = j.get("category", "unclassified")
    title = j.get("title", "")
    sal = j.get("salary_normalized", j.get("salary", ""))
    
    company_data[co]["roles"] += 1
    company_data[co]["scores"].append(score)
    company_data[co]["cities"][city] += 1
    company_data[co]["categories"][cat] += 1
    company_data[co]["titles"].append(title)
    
    if j.get("direct_apply"):
        company_data[co]["direct_apply"] += 1
    if score >= 80:
        company_data[co]["high_score"] += 1
    
    # Director-level detection
    if any(kw in title.lower() for kw in ["director", "head of", "vp ", "vice president", "principal"]):
        company_data[co]["director_level"] += 1
    
    if sal:
        parsed = parse_salary(sal)
        if parsed:
            company_data[co]["salaries"].append(parsed)

# === OUTPUT ===
print("=" * 80)
print("MARKET INTELLIGENCE BRIEF — APAC Career Landscape (June 2026)")
print("=" * 80)

# Top companies by hiring activity
print("\n## TOP COMPANIES BY HIRING ACTIVITY (Role Count = Hiring Urgency Signal)")
print(f"{'Company':<25} {'Roles':>5} {'Avg Score':>9} {'80+':>4} {'Dir+':>4} {'DA':>3} {'Cities'}")
print("-" * 80)

sorted_cos = sorted(company_data.items(), key=lambda x: x[1]["roles"], reverse=True)
for co, d in sorted_cos[:25]:
    avg = sum(d["scores"]) / len(d["scores"])
    cities = ", ".join(c + "(" + str(n) + ")" for c, n in d["cities"].most_common(3) if c != "Unknown")
    print(f"{co:<25} {d['roles']:>5} {avg:>9.0f} {d['high_score']:>4} {d['director_level']:>4} {d['direct_apply']:>3} {cities}")

# Salary intelligence
print("\n## SALARY INTELLIGENCE BY CITY")
for city in ["Singapore", "Hong Kong", "Shenzhen", "Shanghai"]:
    city_jobs = [j for j in jobs if j.get("location_norm") == city]
    city_salaries = []
    for j in city_jobs:
        sal = j.get("salary_normalized", j.get("salary", ""))
        if sal:
            p = parse_salary(sal)
            if p:
                city_salaries.append({"company": j.get("company", "?"), "min": p["min"], "max": p["max"], "raw": p["raw"]})
    
    if city_salaries:
        print(f"\n### {city} ({len(city_salaries)} roles with salary data)")
        all_mins = [s["min"] for s in city_salaries]
        all_maxs = [s["max"] for s in city_salaries]
        print(f"  Range: {min(all_mins):.0f} — {max(all_maxs):.0f}")
        print(f"  Median floor: {sorted(all_mins)[len(all_mins)//2]:.0f}")
        print(f"  Median ceiling: {sorted(all_maxs)[len(all_maxs)//2]:.0f}")
        print(f"  Top-paying roles:")
        city_salaries.sort(key=lambda x: x["max"], reverse=True)
        for s in city_salaries[:5]:
            print(f"    {s['company']}: {s['raw']}")

# High-score clusters
print("\n## HIGH-SCORE CLUSTERS (Companies with 3+ score-80+ roles)")
for co, d in sorted_cos:
    if d["high_score"] >= 3:
        print(f"\n### {co} ({d['high_score']} high-score roles)")
        high_jobs = [(j.get("title", "?"), j.get("location_norm", "?"), j.get("quality_score", j.get("score", 0)))
                     for j in jobs if j.get("company") == co and j.get("quality_score", j.get("score", 0)) >= 80]
        high_jobs.sort(key=lambda x: x[2], reverse=True)
        for title, city, score in high_jobs[:8]:
            print(f"  [{score}] {title} — {city}")

# Director-level opportunities
print("\n## DIRECTOR-LEVEL OPPORTUNITIES (Score 80+, Director/VP/Head titles)")
director_jobs = []
for j in jobs:
    title = j.get("title", "")
    score = j.get("quality_score", j.get("score", 0))
    if score >= 80 and any(kw in title.lower() for kw in ["director", "head of", "vp ", "vice president", "principal"]):
        director_jobs.append({
            "company": j.get("company", "?"),
            "title": title,
            "city": j.get("location_norm", "?"),
            "score": score,
            "salary": j.get("salary_normalized", j.get("salary", "")),
            "direct_apply": j.get("direct_apply", False)
        })

director_jobs.sort(key=lambda x: x["score"], reverse=True)
for d in director_jobs[:15]:
    da = "DA" if d["direct_apply"] else "  "
    sal = f" | {d['salary']}" if d["salary"] else ""
    print(f"  {da} [{d['score']:>3}] {d['company']}: {d['title']} — {d['city']}{sal}")

# Geographic heatmap
print("\n## GEOGRAPHIC HEATMAP (Jobs by City × Category)")
geo = defaultdict(lambda: Counter())
for j in jobs:
    city = j.get("location_norm", "Unknown")
    cat = j.get("category", "unclassified")
    if city != "Unknown":
        geo[city][cat] += 1

for city in ["Singapore", "Hong Kong", "Shenzhen", "Shanghai"]:
    cats = geo[city]
    total = sum(cats.values())
    if total > 0:
        top_cats = cats.most_common(5)
        print(f"\n### {city} ({total} total)")
        for cat, count in top_cats:
            pct = count / total * 100
            print(f"  {cat}: {count} ({pct:.0f}%)")

# Actionable insight: companies hiring across multiple cities
print("\n## MULTI-CITY COMPANIES (Hiring in 2+ APAC cities)")
for co, d in sorted_cos:
    apac_cities = {c for c in d["cities"] if c in ("Singapore", "Hong Kong", "Shenzhen", "Shanghai")}
    if len(apac_cities) >= 2:
        city_str = ", ".join(c + "(" + str(d["cities"][c]) + ")" for c in apac_cities)
        print(f"  {co}: {city_str}")

# Visa sponsorship signals
print("\n## VISA SPONSORSHIP LIKELIHOOD (Companies with Director+ APAC roles)")
visa_companies = ["Google", "Meta", "Mastercard", "Visa", "Airwallex", "OKX", "ByteDance", 
                  "Wellington Management", "BlackRock", "BNY", "Manulife", "Stripe", "Databricks"]
for co in visa_companies:
    if co in company_data:
        d = company_data[co]
        if d["high_score"] > 0:
            print(f"  ✅ {co}: {d['roles']} roles, {d['high_score']} high-score, {d['director_level']} Director+")

print("\n" + "=" * 80)
print("Generated: June 23, 2026 by Career OS Market Intel")
print("Data: 699 jobs in OKComputer_职位搜索清单/jobs-all.json")
print("=" * 80)
