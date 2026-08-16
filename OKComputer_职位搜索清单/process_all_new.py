#!/usr/bin/env python3
"""Process all new jobs and add to database."""
import json
import sys
from datetime import datetime
from urllib.parse import quote

# Target locations
TARGET_LOCATIONS_CN = ['深圳', '上海', '广州', '杭州']
TARGET_LOCATIONS_EN = ['shenzhen', 'hong kong', 'guangzhou', 'shanghai', 'singapore', 'hk', 'sz']

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
    '产品经理', '策略', '增长', '运营',
]

# Role keywords to EXCLUDE
EXCLUDE_KEYWORDS = [
    'intern', 'internship', 'trainee', 'apprentice',
    'junior', 'assistant', 'coordinator',
    'engineer', 'developer', 'designer', 'analyst',
    'data scientist', 'ml engineer', 'software',
    'sr. director', 'senior director', 'vice president',
]

def matches_location(loc):
    """Check if location matches target locations."""
    loc_lower = loc.lower()
    for target in TARGET_LOCATIONS_EN + TARGET_LOCATIONS_CN:
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
    # Load existing database
    with open('jobs-all.json') as f:
        existing = json.load(f)
    
    # Build dedup sets
    existing_urls = set()
    existing_titles = set()
    for j in existing:
        url = j.get('url', '')
        if url:
            existing_urls.add(url)
        key = f"{j.get('company','').lower()}|{j.get('title','').lower()}"
        existing_titles.add(key)
    
    print(f"Existing jobs: {len(existing)}")
    
    # Process Greenhouse scan
    new_jobs = []
    try:
        with open('greenhouse-scan-latest.json') as f:
            scan = json.load(f)
        
        for j in scan:
            title = j.get('title', '')
            loc = j.get('location', '')
            url = j.get('url', '')
            
            # Check if relevant
            if matches_location(loc) and matches_role(title):
                # Check if new
                key = f"{j.get('company','').lower()}|{title.lower()}"
                if url not in existing_urls and key not in existing_titles:
                    # Clean up description
                    desc = j.get('desc_preview', '')
                    # Remove HTML tags
                    import re
                    desc = re.sub(r'<[^>]+>', ' ', desc)
                    desc = re.sub(r'\s+', ' ', desc).strip()
                    
                    new_job = {
                        'company': j.get('company', ''),
                        'title': title,
                        'location': loc,
                        'url': url,
                        'greenhouse_id': j.get('greenhouse_id'),
                        'posted': j.get('posted', ''),
                        'source': 'greenhouse_api',
                        'scanned_date': datetime.now().strftime('%Y-%m-%d'),
                        'description': desc[:300] if desc else '',
                        'grade': 'A-1',
                        'english_friendly': True,
                        'category': 'product',
                        'city_normalized': loc.split(',')[0] if ',' in loc else loc,
                    }
                    new_jobs.append(new_job)
    except Exception as e:
        print(f"Error processing greenhouse scan: {e}")
    
    # Process Tencent scan
    try:
        with open('tencent-scan-latest.json') as f:
            tencent = json.load(f)
        
        for j in tencent:
            title = j.get('title', '')
            loc = j.get('location', '')
            url = j.get('url', '')
            
            # Check if relevant
            if matches_location(loc) and matches_role(title):
                # Check if new
                key = f"tencent|{title.lower()}"
                if url not in existing_urls and key not in existing_titles:
                    new_job = {
                        'company': 'Tencent',
                        'title': title,
                        'location': loc,
                        'url': url,
                        'source': 'tencent_careers',
                        'scanned_date': datetime.now().strftime('%Y-%m-%d'),
                        'category': j.get('category', ''),
                        'grade': 'A-1',
                        'english_friendly': True,
                        'city_normalized': loc.split('-')[0] if '-' in loc else loc,
                    }
                    new_jobs.append(new_job)
    except Exception as e:
        print(f"Error processing Tencent scan: {e}")
    
    print(f"\nNEW relevant jobs found: {len(new_jobs)}")
    
    # Print new jobs
    for j in new_jobs:
        print(f"\n  📌 {j['title']} @ {j['company']}")
        print(f"     📍 {j['location']}")
        print(f"     🔗 {j['url']}")
    
    # Add to database
    if new_jobs:
        existing.extend(new_jobs)
        with open('jobs-all.json', 'w') as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Added {len(new_jobs)} new jobs to database")
        print(f"Total jobs now: {len(existing)}")
    else:
        print("\nNo new jobs to add")
    
    # Save new jobs list
    with open('new-jobs-this-scan.json', 'w') as f:
        json.dump(new_jobs, f, indent=2, ensure_ascii=False)
    
    return new_jobs

if __name__ == '__main__':
    new = main()
