#!/usr/bin/env python3
"""Scan 51job API for PM/strategy roles in Shenzhen and HK."""
import json
import urllib.request
import sys
from datetime import datetime

def fetch_51job(keyword, location_code):
    """Fetch jobs from 51job API."""
    # 51job uses a different API structure
    url = f"https://api.51job.com/api/job/search-pc?keyword={keyword}&searchType=2&jobArea={location_code}&keywordType=&function=&industryType=&salary=&workYear=&degree=&companyType=&companySize=&jobType=&issueDate=&sortType=0&pageNum=1&pageSize=30"
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Accept': 'application/json',
            'Referer': 'https://we.51job.com/'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"Error fetching 51job ({keyword}, {location_code}): {e}", file=sys.stderr)
        return None

def main():
    today = datetime.now().strftime('%Y-%m-%d')
    all_jobs = []
    
    # Location codes: 040090 = Shenzhen, 040020 = HK
    searches = [
        ('产品经理', '040090'),  # PM in Shenzhen
        ('商业策略', '040090'),  # Biz Strategy in Shenzhen
        ('Growth', '040090'),    # Growth in Shenzhen
        ('产品经理', '040020'),  # PM in HK
        ('商业策略', '040020'),  # Biz Strategy in HK
    ]
    
    for keyword, location_code in searches:
        print(f"\nSearching 51job: {keyword} in {location_code}...")
        data = fetch_51job(keyword, location_code)
        if not data:
            continue
        
        # Parse the response
        result = data.get('resultbody', {}).get('job', {}).get('items', [])
        print(f"  Found {len(result)} jobs")
        
        for j in result:
            title = j.get('jobName', '')
            company = j.get('companyName', '')
            loc = j.get('jobAreaString', '')
            salary = j.get('jobSalary', '')
            job_url = j.get('jobHref', '')
            job_id = j.get('jobId', '')
            
            all_jobs.append({
                'company': company,
                'title': title,
                'location': loc,
                'salary': salary,
                'url': job_url,
                'job_id': job_id,
                'source': '51job',
                'scanned_date': today,
                'keyword_search': keyword,
                'location_code': location_code,
            })
    
    # Deduplicate
    seen = set()
    unique = []
    for j in all_jobs:
        jid = j.get('job_id', j.get('url', ''))
        if jid and jid not in seen:
            seen.add(jid)
            unique.append(j)
    
    # Save
    output_path = '/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/51job-scan-latest.json'
    with open(output_path, 'w') as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    
    print(f"\nTotal unique 51job results: {len(unique)}")
    for j in unique[:15]:
        print(f"  {j['title']} @ {j['company']} | {j['location']} | {j.get('salary','')}")

if __name__ == '__main__':
    main()
