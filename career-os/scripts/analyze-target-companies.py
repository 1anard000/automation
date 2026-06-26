#!/usr/bin/env python3
"""Analyze local job database for contact mapping insights."""
import json, os, collections

workspace = os.path.expanduser("~/.openclaw/workspace")

# Load job database
db_files = ["apac_jobs.json", "jobs-all.json", "verified-career-jobs.json"]
jobs = []
for f in db_files:
    path = os.path.join(workspace, f)
    if os.path.exists(path):
        with open(path) as fh:
            data = json.load(fh)
            if isinstance(data, list):
                jobs.extend(data)
                print(f"Loaded {len(data)} from {f}")

# Deduplicate by URL
seen = set()
unique = []
for j in jobs:
    url = j.get("url", j.get("apply_url", j.get("link", "")))
    if url and url not in seen:
        seen.add(url)
        unique.append(j)
    elif not url:
        unique.append(j)

print(f"\nTotal unique jobs: {len(unique)}")

# Analyze by company for target companies
targets = ["Wellington", "Mastercard", "BlackRock", "BNY", "DBS", "UOB", "OKX", "Airwallex", "ByteDance", "Crypto.com", "Binance", "Coupang", "Thunes", "SymphonyAI", "Visa"]

# Find jobs at target companies
company_jobs = collections.defaultdict(list)
for j in unique:
    company = j.get("company", j.get("employer", ""))
    for t in targets:
        if t.lower() in company.lower():
            company_jobs[t].append(j)
            break

print("\n=== Target Company Job Counts ===")
for t in targets:
    count = len(company_jobs.get(t, []))
    if count > 0:
        titles = [j.get("title", j.get("position", "unknown"))[:50] for j in company_jobs[t][:3]]
        print(f"  {t}: {count} jobs — {', '.join(titles)}")

# Check for salary data
salary_count = 0
for j in unique:
    sal = j.get("salary", j.get("compensation", ""))
    if sal:
        salary_count += 1
print(f"\nJobs with salary data: {salary_count}/{len(unique)}")

# Check for direct apply
direct_count = 0
for j in unique:
    url = j.get("url", j.get("apply_url", j.get("link", "")))
    if url and ("greenhouse" in url or "lever" in url or "workday" in url or "ashby" in url or "apply" in url.lower()):
        direct_count += 1
print(f"Jobs with direct apply links: {direct_count}/{len(unique)}")

# Print a sample of Wellington jobs (highest priority research queue company)
if "Wellington" in company_jobs:
    print(f"\n=== Wellington Management Jobs ({len(company_jobs['Wellington'])}) ===")
    for j in company_jobs["Wellington"][:5]:
        print(f"  Title: {j.get('title', 'N/A')}")
        print(f"  City: {j.get('city', j.get('location', 'N/A'))}")
        print(f"  URL: {j.get('url', j.get('apply_url', j.get('link', 'N/A')))}")
        print()

# Print Mastercard jobs
if "Mastercard" in company_jobs:
    print(f"\n=== Mastercard Jobs ({len(company_jobs['Mastercard'])}) ===")
    for j in company_jobs["Mastercard"][:5]:
        print(f"  Title: {j.get('title', 'N/A')}")
        print(f"  City: {j.get('city', j.get('location', 'N/A'))}")
        print(f"  URL: {j.get('url', j.get('apply_url', j.get('link', 'N/A')))}")
        print()

# Print BlackRock jobs
if "BlackRock" in company_jobs:
    print(f"\n=== BlackRock Jobs ({len(company_jobs['BlackRock'])}) ===")
    for j in company_jobs["BlackRock"][:5]:
        print(f"  Title: {j.get('title', 'N/A')}")
        print(f"  City: {j.get('city', j.get('location', 'N/A'))}")
        print(f"  URL: {j.get('url', j.get('apply_url', j.get('link', 'N/A')))}")
        print()

# Print BNY jobs
if "BNY" in company_jobs:
    print(f"\n=== BNY Jobs ({len(company_jobs['BNY'])}) ===")
    for j in company_jobs["BNY"][:5]:
        print(f"  Title: {j.get('title', 'N/A')}")
        print(f"  City: {j.get('city', j.get('location', 'N/A'))}")
        print(f"  URL: {j.get('url', j.get('apply_url', j.get('link', 'N/A')))}")
        print()

# Count by city
city_counts = collections.Counter()
for j in unique:
    city = j.get("city", j.get("location", "unknown"))
    city_counts[city] += 1

print("\n=== Top Cities ===")
for city, count in city_counts.most_common(15):
    print(f"  {city}: {count}")
