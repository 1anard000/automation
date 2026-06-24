#!/usr/bin/env python3
"""Analyze job database for market intelligence."""
import json
from collections import Counter

with open("/Users/iancolrick/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json") as f:
    data = json.load(f)

jobs = data if isinstance(data, list) else data.get("jobs", data.get("results", []))

companies = Counter()
cities = Counter()
scores = {}
statuses = Counter()
categories = Counter()
salary_data = []

for j in jobs:
    co = j.get("company", "Unknown")
    city = j.get("location_norm", j.get("city", "Unknown"))
    score = j.get("quality_score", j.get("score", 0))
    status = j.get("status", "unknown")
    cat = j.get("category", "unclassified")

    companies[co] += 1
    cities[city] += 1
    statuses[status] += 1
    categories[cat] += 1

    if co not in scores:
        scores[co] = []
    scores[co].append(score)

    salary = j.get("salary_normalized", j.get("salary", None))
    if salary:
        salary_data.append({"company": co, "city": city, "score": score, "salary": salary})

print("=== TOP COMPANIES BY ROLE COUNT ===")
for co, count in companies.most_common(25):
    avg = sum(scores[co]) / len(scores[co])
    high = sum(1 for s in scores[co] if s >= 80)
    perfect = sum(1 for s in scores[co] if s >= 100)
    print(f"{co}: {count} roles, avg={avg:.0f}, 80+={high}, 100={perfect}")

print("\n=== CITIES ===")
for city, count in cities.most_common(10):
    print(f"{city}: {count}")

print("\n=== CATEGORIES ===")
for cat, count in categories.most_common():
    print(f"{cat}: {count}")

print("\n=== STATUSES ===")
for st, count in statuses.most_common():
    print(f"{st}: {count}")

print("\n=== HIGH-SCORE DIRECT-APPLY (score>=80) ===")
direct_apply = [j for j in jobs if j.get("quality_score", j.get("score", 0)) >= 80]
for j in sorted(direct_apply, key=lambda x: x.get("quality_score", x.get("score", 0)), reverse=True)[:25]:
    co = j.get("company", "?")
    title = j.get("title", "?")
    city = j.get("location_norm", j.get("city", "?"))
    score = j.get("quality_score", j.get("score", "?"))
    da = "DA" if j.get("direct_apply") else "  "
    sal = j.get("salary_normalized", "")
    print(f"  {da} {co}: {title} [{city}] score={score} {sal}")

print(f"\n=== APPLIED COUNT ===")
applied = [j for j in jobs if j.get("status") in ("applied", "Applied", "submitted")]
not_applied = [j for j in jobs if j.get("status") not in ("applied", "Applied", "submitted")]
print(f"Applied: {len(applied)}")
print(f"Not applied: {len(not_applied)}")

print(f"\n=== SALARY DATA SAMPLE (first 15) ===")
for s in salary_data[:15]:
    print(f"  {s['company']}: {s['city']} score={s['score']} salary={s['salary']}")

print(f"\n=== TOTAL JOBS: {len(jobs)} ===")
