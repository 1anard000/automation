#!/usr/bin/env python3
"""Filter Greenhouse scan results and find new jobs not in database."""
import json
import re
from datetime import datetime

# Target locations
TARGET_LOCATIONS = [
    'singapore', 'hong kong', 'shenzhen', 'guangzhou', 'shanghai',
    'hong kong sar', 'hk', 'sz', 'gz', 'sg',
    'southeast asia', 'sea', 'apac', 'asia',
]

# Role keywords to include
ROLE_KEYWORDS = [
    'product manager', 'product lead', 'product lead',
    'strategy', 'strategic', 'bizops', 'biz ops',
    'growth', 'gm', 'general manager',
    'operations manager', 'operations lead',
    'business development', 'bd manager',
    'marketing manager', 'marketing lead',
    'program manager', 'project manager',
    'head of', 'director', 'vp',
    'commercial', 'partnerships',
]

# Role keywords to EXCLUDE
EXCLUDE_KEYWORDS = [
    'intern', 'internship', 'trainee', 'apprentice',
    'junior', 'assistant', 'coordinator',
    'engineer', 'developer', 'designer', 'analyst',
    'data scientist', 'ml engineer', 'software',
]

def matches_location(loc):
    """Check if location matches target locations."""
    loc_lower = loc.lower()
    for target in TARGET_LOCATIONS:
        if target in loc_lower:
            return True
    return False

def matches_role(title):
    """Check if title matches target roles."""
    title_lower = title.lower()
    
    # Exclude unwanted roles
    for keyword in EXCLUDE_KEYWORDS:
        if keyword in title_lower:
            return False
    
    # Include wanted roles
    for keyword in ROLE_KEYWORDS:
        if keyword in title_lower:
            return True
    
    return False

def main():
    # Load latest scan
    with open('greenhouse-scan-latest.json') as f:
        scan = json.load(f)
    
    # Load existing database
    with open('jobs-all.json') as f:
        existing = json.load(f)
    
    # Build set of existing URLs for dedup
    existing_urls = set()
    existing_titles = set()
    for j in existing:
        url = j.get('url', '')
        if url:
            existing_urls.add(url)
        # Also track company+title for fuzzy dedup
        key = f"{j.get('company','').lower()}|{j.get('title','').lower()}"
        existing_titles.add(key)
    
    print(f"Existing jobs: {len(existing)}")
    print(f"Existing URLs: {len(existing_urls)}")
    print(f"Scan results: {len(scan)}")
    
    # Filter for relevant roles
    relevant = []
    for j in scan:
        title = j.get('title', '')
        loc = j.get('location', '')
        url = j.get('url', '')
        
        if matches_location(loc) and matches_role(title):
            relevant.append(j)
    
    print(f"Relevant roles (location + title match): {len(relevant)}")
    
    # Find new jobs
    new_jobs = []
    for j in relevant:
        url = j.get('url', '')
        key = f"{j.get('company','').lower()}|{j.get('title','').lower()}"
        
        if url not in existing_urls and key not in existing_titles:
            new_jobs.append(j)
    
    print(f"NEW jobs not in database: {len(new_jobs)}")
    
    # Print new jobs
    for j in new_jobs:
        print(f"\n  📌 {j['title']} @ {j['company']}")
        print(f"     📍 {j['location']} | Posted: {j['posted']}")
        print(f"     🔗 {j['url']}")
        if j.get('desc_preview'):
            print(f"     📝 {j['desc_preview'][:150]}...")
    
    # Save new jobs
    output_path = 'new-greenhouse-jobs.json'
    with open(output_path, 'w') as f:
        json.dump(new_jobs, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved {len(new_jobs)} new jobs to {output_path}")

if __name__ == '__main__':
    main()
