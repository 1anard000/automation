#!/usr/bin/env python3
"""Scan Tencent careers API for strategy/PM roles."""
import json
import urllib.request
import sys
from datetime import datetime

def fetch_tencent_jobs(keyword, location):
    """Fetch jobs from Tencent careers API."""
    url = f"https://careers.tencent.com/tencentcareer/api/post/Query?timestamp={int(datetime.now().timestamp())}&countryId=&cityId=&jobIds=&keyword={keyword}&languageCode=en&area={location}&type=0&subType=0&pageIndex=1&pageSize=30"
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Accept': 'application/json',
            'Referer': 'https://careers.tencent.com/en-us/search.html'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"Error fetching Tencent ({keyword}, {location}): {e}", file=sys.stderr)
        return None

def main():
    today = datetime.now().strftime('%Y-%m-%d')
    all_jobs = []
    
    # Search terms
    searches = [
        ('strategy', 'Shenzhen'),
        ('product manager', 'Shenzhen'),
        ('business development', 'Shenzhen'),
        ('growth', 'Shenzhen'),
        ('strategy', 'Hong Kong'),
        ('product manager', 'Hong Kong'),
    ]
    
    for keyword, location in searches:
        print(f"\nSearching: {keyword} in {location}...")
        data = fetch_tencent_jobs(keyword, location)
        if not data:
            continue
        
        posts = data.get('Data', {}).get('Posts', [])
        print(f"  Found {len(posts)} jobs")
        
        for p in posts:
            title = p.get('RecruitPostName', '')
            loc = p.get('LocationName', '')
            category = p.get('CategoryName', '')
            dept = p.get('DepartmentName', '')
            post_id = p.get('PostId', '')
            url = f"https://careers.tencent.com/en-us/position/{post_id}.html" if post_id else ''
            
            all_jobs.append({
                'company': 'Tencent',
                'title': title,
                'location': loc,
                'url': url,
                'source': 'tencent_careers',
                'scanned_date': today,
                'category': category,
                'department': dept,
                'keyword_search': keyword,
                'location_search': location,
            })
    
    # Deduplicate by PostId
    seen = set()
    unique = []
    for j in all_jobs:
        pid = j.get('url', '')
        if pid not in seen:
            seen.add(pid)
            unique.append(j)
    
    # Save
    output_path = '/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/tencent-scan-latest.json'
    with open(output_path, 'w') as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    
    print(f"\nTotal unique Tencent jobs: {len(unique)}")
    for j in unique[:10]:
        print(f"  {j['title']} | {j['location']} | {j['url'][:60]}")

if __name__ == '__main__':
    main()
