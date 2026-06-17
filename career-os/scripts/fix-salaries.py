#!/usr/bin/env python3
"""Fix remaining quality issues after quality-improver.py run."""
import json, os, re
from datetime import datetime

WORKSPACE = '/Users/iancolrick/.openclaw/workspace'
DB_PATH = os.path.join(WORKSPACE, 'OKComputer_职位搜索清单', 'jobs-all.json')

# Salary estimate tables
SALARY_MAP = {
    'Hong Kong': {
        'director': '80-120K HKD/mo',
        'head': '80-120K HKD/mo',
        'vp': '80-120K HKD/mo',
        'senior': '50-80K HKD/mo',
        'sr.': '50-80K HKD/mo',
        'product manager': '40-65K HKD/mo',
        'default': '50-80K HKD/mo',
    },
    'Shenzhen': {
        'director': '80-150K RMB/yr',
        'head': '100-180K RMB/yr',
        'senior': '60-120K RMB/yr',
        'product manager': '40-80K RMB/yr',
        'default': '60-120K RMB/yr',
    },
    'Shanghai': {
        'director': '80-150K RMB/yr',
        'head': '100-180K RMB/yr',
        'senior': '60-120K RMB/yr',
        'product manager': '40-80K RMB/yr',
        'default': '60-120K RMB/yr',
    },
    'Singapore': {
        'director': '15-25K SGD/mo',
        'head': '18-30K SGD/mo',
        'vp': '20-35K SGD/mo',
        'senior': '12-20K SGD/mo',
        'product manager': '10-18K SGD/mo',
        'default': '12-20K SGD/mo',
    },
}

def estimate_salary(job):
    """Add salary estimate for jobs with empty or 'Not listed' salary."""
    salary = job.get('salary', '').strip()
    if salary and salary != 'Not listed':
        return False
    
    title = job.get('title', '').lower()
    loc = job.get('location_norm', job.get('location', ''))
    
    # Determine level
    if any(kw in title for kw in ['director', 'head of', 'vp', 'chief', 'svp', 'evp']):
        level = 'director'
        if 'head' in title:
            level = 'head'
        if 'vp' in title:
            level = 'vp'
    elif any(kw in title for kw in ['senior', 'sr.', 'principal', 'lead']):
        level = 'senior'
    elif 'product manager' in title or 'product owner' in title:
        level = 'product manager'
    else:
        level = 'default'
    
    # Match location
    for city, levels in SALARY_MAP.items():
        if city.lower() in loc.lower():
            est = levels.get(level, levels.get('default', ''))
            if est:
                job['salary'] = f"(est) {est}"
                return True
    
    return False

def main():
    with open(DB_PATH) as f:
        all_jobs = json.load(f)
    
    print(f"Loaded {len(all_jobs)} jobs")
    
    # Fix salaries
    salary_fixes = 0
    for job in all_jobs:
        if job.get('quality_bar_reject'):
            continue
        if estimate_salary(job):
            salary_fixes += 1
    
    print(f"Salary fixes: {salary_fixes}")
    
    # Write back
    with open(DB_PATH, 'w') as f:
        json.dump(all_jobs, f, indent=2, ensure_ascii=False)
    
    # Verify
    with open(DB_PATH) as f:
        verify = json.load(f)
    print(f"Verified: {len(verify)} jobs written")
    
    # Check remaining issues
    still_missing = [j for j in verify if not j.get('salary','').strip() or j.get('salary') == 'Not listed']
    print(f"Still missing salary: {len(still_missing)}")

if __name__ == '__main__':
    main()
