#!/usr/bin/env python3
"""Scan Greenhouse APIs for new jobs."""
import json
import urllib.request
import sys
from datetime import datetime

def fetch_greenhouse_jobs(board_token):
    """Fetch all jobs from a Greenhouse board."""
    url = f"https://boards-api.greenhouse.io/v1/{board_token}/jobs?content=true"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            return data.get('jobs', [])
    except Exception as e:
        print(f"Error fetching {board_token}: {e}")
        return []

def filter_relevant_jobs(jobs, board_token):
    """Filter for relevant PM/Strategy/Growth roles in target locations."""
    relevant = []
    target_locations = ['shenzhen', 'hong kong', 'singapore', 'shanghai', 'guangzhou', 'remote']
    target_keywords = ['product manager', 'strategy', 'growth', 'bizops', 'gm', 'general manager',
                      'head of', 'principal product', 'senior manager', 'program manager']
    
    for j in jobs:
        title = j.get('title', '')
        loc = j.get('location', {}).get('name', '')
        lower_t = title.lower()
        
        # Check if title matches target keywords
        if any(k in lower_t for k in target_keywords):
            # Check if location matches
            if any(l in loc.lower() for l in target_locations):
                relevant.append({
                    'id': j['id'],
                    'title': title,
                    'location': loc,
                    'url': j.get('absolute_url', ''),
                    'company': board_token.upper(),
                    'source': 'greenhouse_api'
                })
    
    return relevant

def main():
    # Load existing jobs
    jobs_file = '/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json'
    try:
        with open(jobs_file) as f:
            existing_jobs = json.load(f)
        existing_urls = {j.get('url') for j in existing_jobs}
        print(f"Existing jobs: {len(existing_jobs)}")
        print(f"Existing URLs count: {len(existing_urls)}")
    except Exception as e:
        print(f"Error loading existing jobs: {e}")
        existing_urls = set()
    
    # Companies to scan
    companies = ['okx', 'stripe', 'airwallex', 'coupang']
    new_jobs = []
    
    for company in companies:
        print(f"\nScanning {company}...")
        jobs = fetch_greenhouse_jobs(company)
        print(f"  Total jobs: {len(jobs)}")
        
        relevant = filter_relevant_jobs(jobs, company)
        print(f"  Relevant: {len(relevant)}")
        
        for j in relevant:
            if j['url'] not in existing_urls:
                new_jobs.append(j)
                print(f"    NEW: {j['title']} | {j['location']} | {j['url']}")
            else:
                print(f"    EXISTS: {j['title']}")
    
    print(f"\nTotal new jobs found: {len(new_jobs)}")
    
    # Save new jobs to a temporary file for review
    if new_jobs:
        output_file = '/Users/iancolrick/.openclaw/workspace/new_greenhouse_jobs.json'
        with open(output_file, 'w') as f:
            json.dump(new_jobs, f, indent=2)
        print(f"New jobs saved to: {output_file}")
    
    return new_jobs

if __name__ == "__main__":
    new_jobs = main()
    sys.exit(0 if new_jobs else 1)
