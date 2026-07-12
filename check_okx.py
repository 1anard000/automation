#!/usr/bin/env python3
"""Check Greenhouse API for OKX jobs"""
import json
import urllib.request

url = "https://boards-api.greenhouse.io/v1/jobs/okx?content=false"
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as response:
        data = json.loads(response.read().decode())
        jobs = data.get('jobs', [])
        
        print(f"OKX total jobs: {len(jobs)}")
        
        # Filter for relevant locations
        relevant = []
        for j in jobs:
            loc = j.get('location', {}).get('name', '')
            title = j.get('title', '')
            if any(c in loc for c in ['Shenzhen', 'Hong Kong', 'Singapore', 'Shanghai', 'Guangzhou']):
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
                    'company': 'OKX'
                })
        
        print(f"Relevant APAC jobs (excl Director/VP): {len(relevant)}")
        for j in relevant:
            print(f"- {j['title']} @ {j['location']}")
            print(f"  {j['url']}")
            
except Exception as e:
    print(f"Error: {e}")
