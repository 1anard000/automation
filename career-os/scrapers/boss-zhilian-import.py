#!/usr/bin/env python3
"""
Boss/Zhilian Discovery Import Script

Takes boss-zhilian-discovery-results.json and merges new jobs into jobs-all.json.
Deduplicates by title+company and URL.
"""
import json, os, sys
from datetime import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOBS_FILE = os.path.join(WORKSPACE, "OKComputer_职位搜索清单", "jobs-all.json")
SCRAPERS_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FILE = os.path.join(SCRAPERS_DIR, "boss-zhilian-discovery-results.json")

def dedup_key(job):
    """Generate dedup key from title + company (normalized)."""
    title = job.get("title", "").strip().lower()
    company = job.get("company", "").strip().lower()
    title = " ".join(title.split())
    company = " ".join(company.split())
    return f"{title}||{company}"

def url_key(job):
    """Use URL as secondary dedup key."""
    return job.get("url", "").strip().rstrip("/").lower()

def main():
    # Load discovery results
    if not os.path.exists(RESULTS_FILE):
        print(f"ERROR: {RESULTS_FILE} not found. Run boss-zhilian-discovery.py first.")
        sys.exit(1)
    
    with open(RESULTS_FILE, "r") as f:
        new_jobs = json.load(f)
    
    print(f"Loaded {len(new_jobs)} jobs from discovery results")
    
    # Load existing jobs
    existing_jobs = []
    if os.path.exists(JOBS_FILE):
        with open(JOBS_FILE, "r") as f:
            existing_jobs = json.load(f)
    
    print(f"Existing jobs: {len(existing_jobs)}")
    
    # Build dedup sets from existing jobs
    existing_title_company = set()
    existing_urls = set()
    for job in existing_jobs:
        existing_title_company.add(dedup_key(job))
        u = url_key(job)
        if u:
            existing_urls.add(u)
    
    # Filter new jobs
    truly_new = []
    for job in new_jobs:
        # Dedup by title+company
        tc_key = dedup_key(job)
        if tc_key in existing_title_company:
            continue
        
        # Dedup by URL
        u = url_key(job)
        if u and u in existing_urls:
            continue
        
        existing_title_company.add(tc_key)
        if u:
            existing_urls.add(u)
        truly_new.append(job)
    
    print(f"New unique jobs after dedup: {len(truly_new)}")
    
    if truly_new:
        existing_jobs.extend(truly_new)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(JOBS_FILE), exist_ok=True)
        
        with open(JOBS_FILE, "w") as f:
            json.dump(existing_jobs, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Appended {len(truly_new)} new jobs to {JOBS_FILE}")
        
        # Show new jobs by location
        location_counts = {}
        for j in truly_new:
            loc = j.get("location", "Unknown") or "Unknown"
            location_counts[loc] = location_counts.get(loc, 0) + 1
        print(f"\nNew jobs by location:")
        for loc, count in sorted(location_counts.items(), key=lambda x: -x[1]):
            print(f"  {loc:20s}: {count}")
        
        # Show new jobs by grade
        grade_counts = {}
        for j in truly_new:
            g = j.get("grade", "A-2")
            grade_counts[g] = grade_counts.get(g, 0) + 1
        print(f"\nNew jobs by grade:")
        for g, count in sorted(grade_counts.items()):
            print(f"  {g:20s}: {count}")
    else:
        print("\n⚠️  No new jobs to import")
    
    print(f"\nTotal jobs now: {len(existing_jobs)}")
    return len(truly_new)

if __name__ == "__main__":
    main()
