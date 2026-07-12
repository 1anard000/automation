#!/usr/bin/env python3
"""Check Greenhouse API for job listings"""
import json
import urllib.request
import sys

def check_company(company_name, board_id):
    url = f"https://boards-api.greenhouse.io/v1/jobs/{board_id}?content=false"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            jobs = data.get('jobs', [])
            
            # Filter for relevant locations
            relevant = []
            for j in jobs:
                loc = j.get('location', {}).get('name', '')
                title = j.get('title', '')
                if any(c in loc for c in ['Shenzhen', 'Hong Kong', 'Singapore', 'Shanghai', 'Guangzhou', 'Remote']):
                    # Skip Director/VP roles
                    if any(skip in title.lower() for skip in ['director', 'vp ', 'vice president', 'managing director']):
                        continue
                    # Skip internships
                    if 'intern' in title.lower():
                        continue
                    relevant.append({
                        'title': title,
                        'location': loc,
                        'url': j.get('absolute_url', ''),
                        'company': company_name
                    })
            return relevant
    except Exception as e:
        print(f"Error fetching {company_name}: {e}")
        return []

# Check multiple companies
companies = [
    ('Stripe', 'stripe'),
    ('Airwallex', 'airwallex'),
    ('Coupang', 'coupang'),
]

all_jobs = []
for name, board in companies:
    jobs = check_company(name, board)
    all_jobs.extend(jobs)
    print(f"\n{name}: {len(jobs)} relevant jobs")

# Print all jobs
print("\n=== All Relevant Jobs ===")
for j in all_jobs:
    print(f"- {j['title']} @ {j['company']} ({j['location']})")
    print(f"  {j['url']}")
