#!/usr/bin/env python3
"""Better filter for target profile roles from greenhouse scan."""
import json
import os
from datetime import datetime

# Load existing jobs
db_path = '/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json'
with open(db_path, 'r') as f:
    existing_jobs = json.load(f)

# Create set of existing job URLs for dedup
existing_urls = set(j.get('url', '') for j in existing_jobs)

# Load scan results
scan_path = '/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/scan-latest.json'
with open(scan_path, 'r') as f:
    scan_results = json.load(f)

print(f"Existing jobs: {len(existing_jobs)}")
print(f"Scan results: {len(scan_results)}")

# Target locations (priority order)
TARGET_LOCATIONS = ['shenzhen', 'hong kong', 'hk', 'guangzhou', 'shanghai', 'singapore']

# Target role patterns (more specific)
TARGET_ROLE_PATTERNS = [
    'product manager', 'product lead', 'head of product',
    'strategy', 'strategic', 'bizops', 'business operations',
    'general manager', 'gm', 'country manager',
    'growth', 'expansion', 'marketplace',
    'cross-border', 'international',
    'fintech', 'payments', 'financial',
    'ai product', 'ai strategy'
]

# Exclude patterns
EXCLUDE_PATTERNS = [
    'director', 'vp ', 'vice president', 'chief', 'c-level',
    'intern', 'junior', 'associate', 'analyst', 'assistant',
    'engineer', 'developer', 'designer', 'architect',
    'sales', 'marketing', 'hr', 'recruiting', 'finance',
    'legal', 'admin', 'operations manager', 'supply chain',
    'accounting', 'compliance', 'risk', 'audit'
]

def is_target_location(loc):
    if not loc:
        return False
    loc_lower = loc.lower()
    return any(t in loc_lower for t in TARGET_LOCATIONS)

def is_target_role(title):
    if not title:
        return False
    title_lower = title.lower()
    
    # Must NOT be in exclude list
    for ex in EXCLUDE_PATTERNS:
        if ex in title_lower:
            return False
    
    # Must match target role pattern
    return any(p in title_lower for p in TARGET_ROLE_PATTERNS)

def categorize_role(title):
    t = title.lower()
    if any(w in t for w in ['product manager', 'product lead', 'head of product']):
        return 'product'
    elif any(w in t for w in ['strategy', 'strategic', 'strategy lead', 'bizops', 'business operations']):
        return 'strategy'
    elif any(w in t for w in ['expansion', 'market entry', 'cross-border']):
        return 'expansion'
    elif any(w in t for w in ['business development', 'partnership', 'bd']):
        return 'bd'
    elif any(w in t for w in ['general manager', 'gm', 'country manager', 'head of']):
        return 'gm'
    elif any(w in t for w in ['operations', 'ops', 'operating']):
        return 'ops'
    else:
        return 'other'

def infer_category(title):
    t = title.lower()
    if any(k in t for k in ['strategy', 'chief of staff', 'bizops', 'business operations',
                             'strategic', 'commercial strategy']):
        return 'strategy'
    if any(k in t for k in ['ai ', ' ai', 'data strategy', 'machine learning',
                             'artificial intelligence']):
        return 'ai_product'
    if any(k in t for k in ['cross-border', 'cross border', 'international',
                             'global', 'regional', 'apac', 'sea ', 'southeast asia']):
        return 'cross_border'
    if any(k in t for k in ['fintech', 'banking', 'financial', 'payments',
                             'lending', 'credit']):
        return 'fintech'
    if any(k in t for k in ['growth', 'expansion', 'marketplace']):
        return 'growth'
    if any(k in t for k in ['senior', 'principal', 'director', 'head of',
                             'vp ', 'vice president']):
        return 'senior_pm'
    return 'general_pm'

# Process scan results
new_jobs = []
for job in scan_results:
    title = job.get('title', '')
    location = job.get('location', '')
    url = job.get('url', '')
    
    # Skip if already exists
    if url in existing_urls:
        continue
    
    # Skip if not target location
    if not is_target_location(location):
        continue
    
    # Skip if not target role
    if not is_target_role(title):
        continue
    
    # Create job entry
    new_job = {
        'title': title,
        'company': job.get('company', ''),
        'location': location,
        'salary': '',
        'url': url,
        'source': 'greenhouse',
        'role_type': categorize_role(title),
        'description': job.get('description', ''),
        'grade': '',
        'posted': job.get('posted', ''),
        'scanned_date': datetime.now().strftime('%Y-%m-%d'),
        'en_title': title if not any('\u4e00' <= c <= '\u9fff' for c in title) else '',
        'category': infer_category(title),
        'quality_tier': 'B',
        'quality_score': 70,
        'english_friendly': True
    }
    new_jobs.append(new_job)
    existing_urls.add(url)

print(f"\nNew jobs to add: {len(new_jobs)}")
for job in new_jobs:
    print(f"  + {job['title']} | {job['company']} | {job['location']}")

# Add new jobs to database
if new_jobs:
    existing_jobs.extend(new_jobs)
    with open(db_path, 'w') as f:
        json.dump(existing_jobs, f, indent=2, ensure_ascii=False)
    print(f"\nDatabase updated: {len(existing_jobs)} total jobs")
else:
    print("\nNo new jobs to add")
