#!/usr/bin/env python3
"""Filter Greenhouse results against existing database and target profile."""
import json
import os

# Load existing database
DB_PATH = '/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json'
with open(DB_PATH, 'r') as f:
    existing_jobs = json.load(f)

# Create set of existing URLs
existing_urls = set(j.get('url', '') for j in existing_jobs)
existing_titles = set((j.get('title', '').lower(), j.get('company', '').lower()) for j in existing_jobs)

print(f"Existing jobs in database: {len(existing_jobs)}")
print(f"Unique URLs: {len(existing_urls)}")

# Load Greenhouse results
with open('/Users/iancolrick/.openclaw/workspace/tmp_greenhouse_results.json', 'r') as f:
    all_relevant = json.load(f)

print(f"\nGreenhouse relevant jobs: {len(all_relevant)}")

# Target locations (priority order)
TARGET_LOCATIONS = ['shenzhen', 'hong kong', 'guangzhou', 'shanghai', 'singapore', 
                    'beijing', 'bangkok', 'taipei', 'tokyo', 'seoul']

# Target keywords (stronger match)
STRONG_KEYWORDS = ['product manager', 'product lead', 'strategy manager', 'growth manager',
                   'bizops', 'business operations', 'general manager', 'head of product',
                   'head of growth', 'business development manager', 'partnerships manager']

# Location priority scores
LOCATION_SCORE = {
    'shenzhen': 10,
    'hong kong': 9,
    'guangzhou': 7,
    'shanghai': 8,
    'singapore': 8,
    'beijing': 7,
    'bangkok': 5,
    'taipei': 5,
    'tokyo': 4,
    'seoul': 4,
}

def get_location_score(location):
    loc_lower = location.lower()
    for city, score in LOCATION_SCORE.items():
        if city in loc_lower:
            return score
    return 0

def is_strong_match(title):
    title_lower = title.lower()
    return any(kw in title_lower for kw in STRONG_KEYWORDS)

def get_quality_score(job):
    """Calculate quality score based on location and title match."""
    score = 0
    
    # Location score (0-10)
    loc_score = get_location_score(job['location'])
    score += loc_score
    
    # Title match bonus (0-5)
    if is_strong_match(job['title']):
        score += 5
    
    # English-friendly bonus (companies known to be English-friendly)
    english_companies = ['Stripe', 'Agoda', 'Airwallex', 'OKX']
    if job['company'] in english_companies:
        score += 2
    
    return score

# Filter and deduplicate
new_jobs = []
for job in all_relevant:
    url = job['url']
    title_key = (job['title'].lower(), job['company'].lower())
    
    # Skip if already in database
    if url in existing_urls or title_key in existing_titles:
        continue
    
    # Calculate quality score
    quality = get_quality_score(job)
    
    # Only include if location is relevant (score > 0)
    if quality > 0:
        job['quality_score'] = quality
        job['location_score'] = get_location_score(job['location'])
        new_jobs.append(job)

# Sort by quality score
new_jobs.sort(key=lambda x: x['quality_score'], reverse=True)

print(f"\nNew jobs to add: {len(new_jobs)}")
print("\nTop 20 new jobs:")
for i, job in enumerate(new_jobs[:20], 1):
    print(f"{i}. [{job['quality_score']}] {job['title']} @ {job['company']}")
    print(f"   Location: {job['location']}")
    print(f"   URL: {job['url']}")
    print()

# Save filtered results
with open('/Users/iancolrick/.openclaw/workspace/tmp_new_jobs.json', 'w') as f:
    json.dump(new_jobs, f, indent=2)
print(f"\nSaved {len(new_jobs)} new jobs to tmp_new_jobs.json")
