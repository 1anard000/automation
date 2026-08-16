#!/usr/bin/env python3
"""Scan 51job API for PM/Strategy roles in SZ and HK."""
import json, urllib.request, urllib.parse
from datetime import datetime

TODAY = datetime.now().strftime('%Y-%m-%d')

# Load existing
with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json') as f:
    existing = json.load(f)
existing_urls = {j.get('url', '') for j in existing}

# 51job API endpoint (new version)
BASE = 'https://we.51job.com/api/job/search-pc'

queries = [
    {'keyword': '产品经理', 'jobArea': '040090', 'area_name': '深圳'},  # Shenzhen
    {'keyword': '产品经理', 'jobArea': '040020', 'area_name': '香港'},  # Hong Kong
    {'keyword': '商业策略', 'jobArea': '040090', 'area_name': '深圳'},  # Shenzhen strategy
    {'keyword': 'product manager', 'jobArea': '040090', 'area_name': '深圳'},
    {'keyword': 'growth', 'jobArea': '040090', 'area_name': '深圳'},
]

new_jobs = []

for q in queries:
    params = {
        'keyword': q['keyword'],
        'searchType': '2',
        'jobArea': q['jobArea'],
        'keywordType': '0',
        'function': '',
        'industryType': '',
        'salary': '',
        'workYear': '05,06,07',  # 5-10+ years
        'degree': '',
        'companyType': '',
        'companySize': '',
        'jobType': '',
        'issueDate': '',
        'sortType': '0',
        'pageSize': '20',
        'pageNum': '1'
    }
    
    url = BASE + '?' + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://we.51job.com/',
            'Accept': 'application/json'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        
        jobs = data.get('resultbody', {}).get('job', {}).get('items', [])
        total = data.get('resultbody', {}).get('job', {}).get('totalCount', 0)
        print(f'51job [{q["keyword"]} in {q["area_name"]}]: {len(jobs)} results (total: {total})')
        
        for j in jobs:
            title = j.get('jobName', '')
            company = j.get('companyName', '')
            salary = j.get('jobSalary', '')
            city = j.get('jobArea', q['area_name'])
            job_url = j.get('jobHref', j.get('jobUrl', ''))
            job_id = j.get('jobId', '')
            
            if not job_url and job_id:
                job_url = f'https://jobs.51job.com/{city}/{job_id}.html'
            
            # Filter: skip low-level roles
            title_lower = title.lower()
            if any(s in title_lower for s in ['实习', 'intern', 'junior', '助理', '应届']):
                continue
            
            is_new = job_url not in existing_urls
            new_jobs.append({
                'company': company,
                'title': title,
                'location': city,
                'salary': salary,
                'url': job_url,
                'source': '51job',
                'scanned_date': TODAY,
                'is_new': is_new
            })
    except Exception as e:
        print(f'51job [{q["keyword"]}]: ERROR - {e}')

print(f'\n--- 51job Summary ---')
print(f'Total results: {len(new_jobs)}')
actual_new = [j for j in new_jobs if j['is_new']]
print(f'NEW (not in DB): {len(actual_new)}')
for j in actual_new[:20]:
    print(f'  NEW: {j["company"]} | {j["title"]} | {j["location"]} | {j["salary"]} | {j["url"][:80]}')

with open('/tmp/new_51job_jobs.json', 'w') as f:
    json.dump(new_jobs, f, ensure_ascii=False, indent=2)
