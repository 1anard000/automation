#!/usr/bin/env python3
"""Scan ByteDance careers for PM/Strategy roles in Shenzhen."""
import json
import urllib.request
from datetime import datetime

def search_bytedance_careers():
    """Search ByteDance careers API."""
    jobs = []
    
    # ByteDance careers API
    url = "https://jobs.bytedance.com/api/v1/search/position"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Referer': 'https://jobs.bytedance.com/experienced/position'
    }
    
    # Search params
    params = {
        "keyword": "产品经理",
        "limit": 20,
        "offset": 0,
        "position_status": 1,  # Open positions
        "job_category_id_list": [],
        "city_code_list": ["765"],  # Shenzhen
        "recruit_type": 2  # Experienced
    }
    
    try:
        data = json.dumps(params).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            job_list = result.get('data', {}).get('job_post_list', [])
            print(f"[ByteDance] Found {len(job_list)} jobs")
            
            for j in job_list:
                title = j.get('name', '')
                # Filter for PM/Strategy roles
                if any(k in title.lower() for k in ['product manager', '产品经理', 'strategy', '策略', 'growth', '增长']):
                    jobs.append({
                        'title': title,
                        'company': 'ByteDance',
                        'location': 'Shenzhen',
                        'salary': '',
                        'url': f"https://jobs.bytedance.com/experienced/position/{j.get('id', '')}/detail",
                        'source': 'bytedance',
                        'scanned_date': datetime.now().strftime('%Y-%m-%d'),
                        'english_friendly': False,  # ByteDance is primarily Chinese
                        'quality_score': 75
                    })
    except Exception as e:
        print(f"[ByteDance] Error: {e}")
    
    return jobs

def main():
    # Load existing jobs
    existing = json.load(open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json'))
    existing_urls = {j.get('url') for j in existing}
    
    print("Scanning ByteDance careers...")
    jobs = search_bytedance_careers()
    
    new_jobs = [j for j in jobs if j['url'] not in existing_urls]
    
    print(f"\nTotal new ByteDance jobs: {len(new_jobs)}")
    
    # Save results
    if new_jobs:
        with open('/Users/iancolrick/.openclaw/workspace/new_bytedance_jobs.json', 'w') as f:
            json.dump(new_jobs, f, indent=2, ensure_ascii=False)
        print(f"Saved to new_bytedance_jobs.json")
        
        for j in new_jobs:
            print(f"  {j['title']} @ {j['company']} | {j['url'][:80]}...")
    
    return new_jobs

if __name__ == "__main__":
    main()
