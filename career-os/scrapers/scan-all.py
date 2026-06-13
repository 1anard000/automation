#!/usr/bin/env python3
"""
Master job scanner.
Runs all scrapers, merges results, deduplicates against existing jobs,
and appends new jobs to jobs-all.json.
"""
import json, sys, os, subprocess, importlib.util
from datetime import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOBS_FILE = os.path.join(WORKSPACE, "OKComputer_职位搜索清单", "jobs-all.json")
SCRAPERS_DIR = os.path.dirname(os.path.abspath(__file__))

SCRAPERS = [
    ("greenhouse", "greenhouse.py"),
    ("builtin", "builtin.py"),
    ("wellfound", "wellfound.py"),
    ("websearch", "websearch.py"),
    ("company_careers", "company_careers.py"),
]

def load_existing_jobs():
    """Load existing jobs from jobs-all.json."""
    if not os.path.exists(JOBS_FILE):
        return []
    with open(JOBS_FILE, "r") as f:
        return json.load(f)

def load_scraper_results(scraper_name):
    """Load results from a scraper's output JSON file."""
    results_file = os.path.join(SCRAPERS_DIR, f"{scraper_name}-results.json")
    if not os.path.exists(results_file):
        return []
    with open(results_file, "r") as f:
        return json.load(f)

def dedup_key(job):
    """Generate dedup key from title + company (normalized)."""
    title = job.get("title", "").strip().lower()
    company = job.get("company", "").strip().lower()
    # Normalize
    title = " ".join(title.split())
    company = " ".join(company.split())
    return f"{title}||{company}"

def url_key(job):
    """Use URL as secondary dedup key."""
    return job.get("url", "").strip().rstrip("/").lower()

def classify_grade(title):
    """Assign grade based on seniority signals."""
    t = title.lower()
    if any(k in t for k in ["vp", "vice president", "c-level", "chief"]):
        return "S-1"
    if any(k in t for k in ["director", "head of"]):
        return "A-1"
    if any(k in t for k in ["principal", "staff"]):
        return "A-1"
    if "senior" in t or "sr." in t:
        return "A-2"
    return "A-2"

def run_scraper(name, script_file):
    """Run a scraper script and return its results."""
    script_path = os.path.join(SCRAPERS_DIR, script_file)
    if not os.path.exists(script_path):
        print(f"  [SKIP] {script_file} not found")
        return []
    
    print(f"\n{'='*60}")
    print(f"Running: {name}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True, text=True, timeout=120,
            cwd=SCRAPERS_DIR,
        )
        print(result.stdout)
        if result.stderr:
            print(f"  [STDERR] {result.stderr[:500]}", file=sys.stderr)
        
        if result.returncode != 0:
            print(f"  [WARN] {name} exited with code {result.returncode}")
        
        return load_scraper_results(name)
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] {name} exceeded 120s")
        return []
    except Exception as e:
        print(f"  [ERROR] {name}: {e}")
        return []

def main():
    print("=" * 60)
    print("Career OS - Master Job Scanner")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Load existing jobs
    existing_jobs = load_existing_jobs()
    print(f"\nExisting jobs: {len(existing_jobs)}")
    
    # Build dedup sets from existing jobs
    existing_title_company = set()
    existing_urls = set()
    for job in existing_jobs:
        existing_title_company.add(dedup_key(job))
        u = url_key(job)
        if u:
            existing_urls.add(u)
    
    # Run all scrapers
    all_new_jobs = []
    scraper_stats = {}
    
    for name, script in SCRAPERS:
        results = run_scraper(name, script)
        scraper_stats[name] = len(results)
        all_new_jobs.extend(results)
    
    print(f"\n{'='*60}")
    print(f"Total raw results from all scrapers: {len(all_new_jobs)}")
    
    # Deduplicate: against existing + within new results
    truly_new = []
    seen_title_company = set(existing_title_company)
    seen_urls = set(existing_urls)
    
    for job in all_new_jobs:
        # Fix grade if missing
        if not job.get("grade"):
            job["grade"] = classify_grade(job.get("title", ""))
        
        # Ensure scanned_date
        if not job.get("scanned_date"):
            job["scanned_date"] = datetime.now().strftime("%Y-%m-%d")
        
        # Dedup by title+company
        tc_key = dedup_key(job)
        if tc_key in seen_title_company:
            continue
        
        # Dedup by URL
        u = url_key(job)
        if u and u in seen_urls:
            continue
        
        seen_title_company.add(tc_key)
        if u:
            seen_urls.add(u)
        truly_new.append(job)
    
    print(f"New unique jobs after dedup: {len(truly_new)}")
    
    # Append to jobs-all.json
    if truly_new:
        existing_jobs.extend(truly_new)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(JOBS_FILE), exist_ok=True)
        
        with open(JOBS_FILE, "w") as f:
            json.dump(existing_jobs, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Appended {len(truly_new)} new jobs to {JOBS_FILE}")
    else:
        print("\n⚠️  No new jobs found")
    
    # Summary
    print(f"\n{'='*60}")
    print("SCAN SUMMARY")
    print(f"{'='*60}")
    print(f"Existing jobs:       {len(existing_jobs) - len(truly_new)}")
    print(f"New jobs found:      {len(truly_new)}")
    print(f"Total jobs now:      {len(existing_jobs)}")
    print(f"\nBy scraper source:")
    for name, count in sorted(scraper_stats.items(), key=lambda x: -x[1]):
        print(f"  {name:20s}: {count} results")
    
    # Count new by source
    if truly_new:
        source_counts = {}
        for j in truly_new:
            s = j.get("source", "unknown")
            source_counts[s] = source_counts.get(s, 0) + 1
        print(f"\nNew jobs by source:")
        for s, c in sorted(source_counts.items(), key=lambda x: -x[1]):
            print(f"  {s:20s}: {c}")
    
    return len(truly_new)

if __name__ == "__main__":
    main()
