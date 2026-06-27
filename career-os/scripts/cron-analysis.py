#!/usr/bin/env python3
"""Career OS Cron Analysis — Full database scan for strategy update."""
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta

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
    print(f"=== DATABASE ANALYSIS ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===")
    print(f"Total jobs: {len(jobs)}")
    
    # Company distribution
    companies = Counter()
    cities = Counter()
    categories = Counter()
    sources = Counter()
    scores = []
    english_count = 0
    direct_apply_count = 0
    applied_count = 0
    stale_count = 0
    high_score_jobs = []
    
    for j in jobs:
        company = j.get("company", j.get("company_name", "unknown"))
        companies[company] += 1
        
        city = j.get("location_norm", j.get("city", j.get("location", "unknown")))
        cities[city] += 1
        
        cat = j.get("category", j.get("type", "unknown"))
        categories[cat] += 1
        
        source = j.get("source", "unknown")
        sources[source] += 1
        
        score = j.get("quality_score", j.get("score", 0))
        if score:
            scores.append((score, company, j.get("title", j.get("en_title", "")), city, j.get("url", "")))
            if score >= 80:
                high_score_jobs.append((score, company, j.get("title", j.get("en_title", "")), city, j.get("url", ""), j.get("status", "")))
        
        if j.get("english_friendly"):
            english_count += 1
        
        if j.get("has_direct_link") or j.get("direct_apply"):
            direct_apply_count += 1
        
        if j.get("status") in ["applied", "submitted"]:
            applied_count += 1
        
        # Check staleness
        scanned = j.get("scanned_date", j.get("posted_date", ""))
        if scanned:
            try:
                d = datetime.strptime(scanned[:10], "%Y-%m-%d")
                if datetime.now() - d > timedelta(days=30):
                    stale_count += 1
            except:
                pass
    
    # Top companies
    print(f"\n--- Top 30 Companies by Job Count ---")
    for company, count in companies.most_common(30):
        if company and company != "unknown" and company != "":
            print(f"  {company}: {count}")
    
    # City distribution
    print(f"\n--- City Distribution ---")
    for city, count in cities.most_common(20):
        print(f"  {city}: {count}")
    
    # Category distribution
    print(f"\n--- Category Distribution ---")
    for cat, count in categories.most_common(15):
        print(f"  {cat}: {count}")
    
    # Source distribution
    print(f"\n--- Source Distribution ---")
    for src, count in sources.most_common(15):
        print(f"  {src}: {count}")
    
    # Score analysis
    if scores:
        scores.sort(key=lambda x: -x[0])
        print(f"\n--- Score Analysis ---")
        print(f"Jobs with scores: {len(scores)}")
        print(f"Score 80+: {len([s for s in scores if s[0] >= 80])}")
        print(f"Score 90+: {len([s for s in scores if s[0] >= 90])}")
        print(f"Score 100: {len([s for s in scores if s[0] >= 100])}")
        
        print(f"\n--- Top 20 Scored Roles ---")
        for score, company, title, city, url in scores[:20]:
            short_title = title[:60] if title else "N/A"
            print(f"  [{score}] {company}: {short_title} ({city})")
        
        # Score by city
        city_scores = defaultdict(list)
        for score, company, title, city, url in scores:
            city_scores[city].append(score)
        print(f"\n--- Average Score by City ---")
        for city, city_s in sorted(city_scores.items(), key=lambda x: -sum(x[1])/len(x[1])):
            print(f"  {city}: avg {sum(city_s)/len(city_s):.1f} ({len(city_s)} jobs)")
        
        # Score by category
        cat_scores = defaultdict(list)
        for score, company, title, city, url in scores:
            cat_scores[company].append(score)
        print(f"\n--- Average Score by Company (Top 15) ---")
        company_avg = [(c, sum(s)/len(s), len(s)) for c, s in cat_scores.items() if len(s) >= 2]
        company_avg.sort(key=lambda x: -x[1])
        for company, avg, count in company_avg[:15]:
            print(f"  {company}: avg {avg:.1f} ({count} jobs)")
    
    # High-score jobs by status
    if high_score_jobs:
        print(f"\n--- High-Score (80+) Jobs by Status ---")
        status_counts = Counter()
        for s, c, t, city, url, status in high_score_jobs:
            status_counts[status] += 1
        for status, count in status_counts.most_common():
            print(f"  {status}: {count}")
        
        # High-score jobs not applied
        unapplied = [h for h in high_score_jobs if h[5] in ["not_applied", ""]]
        print(f"\n--- HIGH-SCORE UNAPPLIED ({len(unapplied)} roles) ---")
        for score, company, title, city, url, status in sorted(unapplied, key=lambda x: -x[0])[:25]:
            short_title = title[:55] if title else "N/A"
            print(f"  [{score}] {company}: {short_title} ({city})")
    
    # Summary
    print(f"\n--- Summary ---")
    print(f"Total jobs: {len(jobs)}")
    print(f"English-tagged: {english_count} ({english_count*100//max(len(jobs),1)}%)")
    print(f"Direct apply: {direct_apply_count}")
    print(f"Applied: {applied_count}")
    print(f"Stale (30+ days): {stale_count}")
    print(f"Companies with jobs: {len(companies)}")
    print(f"Score 80+: {len([s for s in scores if s[0] >= 80])}")
    print(f"Score 100: {len([s for s in scores if s[0] >= 100])}")

if __name__ == "__main__":
    jobs = load_db()
    if jobs:
        analyze(jobs)
    else:
        print("ERROR: No jobs found in database")
