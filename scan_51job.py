#!/usr/bin/env python3
"""Scan 51job for PM/Strategy roles in Shenzhen and Hong Kong."""
import json
import urllib.request
import urllib.parse
from datetime import datetime

def search_51job(keyword, area_code, area_name):
    """Search 51job for jobs."""
    jobs = []
    params = {
        'keyword': keyword,
        'searchType': '2',
        'jobArea': area_code,
        'curr_page': '1'
    }
    url = f"https://we.51job.com/api/job/search-pc?api_key=51job&timestamp={int(datetime.now().timestamp())}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://we.51job.com/pc/search'
    }
    
    try:
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            job_list = result.get('resultbody', {}).get('job', {}).get('items', [])
            print(f"[51job] {area_name}: {len(job_list)} jobs found")
            for j in job_list:
                jobs.append({
                    'title': j.get('jobName', ''),
                    'company': j.get('companyName', ''),
                    'location': area_name,
                    'salary': j.get('jobSalary', ''),
                    'url': j.get('jobHref', ''),
                    'source': '51job',
                    'scanned_date': datetime.now().strftime('%Y-%m-%d'),
                    'english_friendly': False,  # 51job is primarily Chinese
                    'quality_score': 70
                })
    except Exception as e:
        print(f"[51job] Error searching {area_name}: {e}")
    
    return jobs

def main():
    # Load existing jobs
    existing = json.load(open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json'))
    existing_urls = {j.get('url') for j in existing}
    
    # Search keywords
    keywords = ['产品经理', '商业策略', '增长', '运营']
    
    # Area codes: 040090 = Shenzhen, 040020 = Hong Kong
    areas = [
        ('040090', 'Shenzhen'),
        ('040020', 'Hong Kong')
    ]
    
    new_jobs = []
    
    for keyword in keywords:
        for area_code, area_name in areas:
            print(f"\nSearching: {keyword} in {area_name}")
            jobs = search_51job(keyword, area_code, area_name)
            
            for j in jobs:
                if j['url'] not in existing_urls:
                    new_jobs.append(j)
                    existing_urls.add(j['url'])  # Avoid duplicates
    
    print(f"\nTotal new 51job jobs: {len(new_jobs)}")
    
    # Save results
    if new_jobs:
        with open('/Users/iancolrick/.openclaw/workspace/new_51job_jobs.json', 'w') as f:
            json.dump(new_jobs, f, indent=2, ensure_ascii=False)
        print(f"Saved to new_51job_jobs.json")
        
        # Show top 5
        for j in new_jobs[:5]:
            print(f"  {j['title']} @ {j['company']} | {j['salary']} | {j['url'][:80]}...")
    
    return new_jobs

if __name__ == "__main__":
    main()
