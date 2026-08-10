#!/usr/bin/env python3
"""Scan Tencent careers for PM/Strategy roles in Shenzhen."""
import json
import urllib.request
from datetime import datetime

def search_tencent_careers():
    """Search Tencent careers API."""
    jobs = []
    
    # Tencent careers API endpoint
    url = "https://careers.tencent.com/tencentcareer/api/post/Query?timestamp={}&countryId=&cityId=&bgIds=&pageSize=10&industryId=&functionId=&level=&keyword=strategy&scenes=1"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://careers.tencent.com/search.html'
    }
    
    try:
        formatted_url = url.format(int(datetime.now().timestamp()))
        req = urllib.request.Request(formatted_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            job_list = result.get('Data', {}).get('Posts', [])
            print(f"[Tencent] Found {len(job_list)} jobs")
            
            for j in job_list:
                loc = j.get('LocationName', '')
                if '深圳' in loc or 'Shenzhen' in loc.lower():
                    jobs.append({
                        'title': j.get('RecruitPostName', ''),
                        'company': 'Tencent',
                        'location': 'Shenzhen',
                        'salary': j.get('Salary', ''),
                        'url': f"https://careers.tencent.com/jobdesc.html?postId={j.get('PostId', '')}",
                        'source': 'tencent_api',
                        'scanned_date': datetime.now().strftime('%Y-%m-%d'),
                        'english_friendly': False,  # Tencent is primarily Chinese
                        'quality_score': 75
                    })
    except Exception as e:
        print(f"[Tencent] Error: {e}")
    
    return jobs

def main():
    # Load existing jobs
    existing = json.load(open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json'))
    existing_urls = {j.get('url') for j in existing}
    
    print("Scanning Tencent careers...")
    jobs = search_tencent_careers()
    
    new_jobs = [j for j in jobs if j['url'] not in existing_urls]
    
    print(f"\nTotal new Tencent jobs: {len(new_jobs)}")
    
    # Save results
    if new_jobs:
        with open('/Users/iancolrick/.openclaw/workspace/new_tencent_jobs.json', 'w') as f:
            json.dump(new_jobs, f, indent=2, ensure_ascii=False)
        print(f"Saved to new_tencent_jobs.json")
        
        for j in new_jobs:
            print(f"  {j['title']} @ {j['company']} | {j['url'][:80]}...")
    
    return new_jobs

if __name__ == "__main__":
    main()
