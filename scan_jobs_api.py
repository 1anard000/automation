#!/usr/bin/env python3
"""Scan job sites via API/scraping for relevant positions."""
import json
import urllib.request
import urllib.parse
import re
import ssl
from datetime import datetime

TODAY = datetime.now().strftime('%Y-%m-%d')

# Load existing jobs
with open('OKComputer_职位搜索清单/jobs-all.json') as f:
    existing_jobs = json.load(f)

existing_urls = set()
existing_titles = set()
for j in existing_jobs:
    existing_urls.add(j.get('url', ''))
    key = (j.get('title', '').lower().strip(), j.get('company', '').lower().strip())
    existing_titles.add(key)

print(f"Existing jobs: {len(existing_jobs)}")

# Create SSL context that doesn't verify (for some APIs)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

new_jobs = []

# --- 1. Try Greenhouse API with different slugs ---
GH_COMPANIES = [
    'okx', 'stripe', 'airwallex', 'coupang',
    'okx-global', 'okx-hk',
]

print("\n=== Greenhouse API ===")
for slug in GH_COMPANIES:
    url = f"https://boards-api.greenhouse.io/v1/jobs/{slug}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = json.loads(resp.read())
        jobs_list = data.get('jobs', [])
        print(f"  {slug}: {len(jobs_list)} jobs")
        if jobs_list:
            for j in jobs_list[:5]:
                print(f"    Sample: {j.get('title','')} @ {j.get('location',{}).get('name','')}")
    except Exception as e:
        print(f"  {slug}: {e}")

# --- 2. Try Tencent Careers API ---
print("\n=== Tencent Careers ===")
try:
    tencent_url = "https://careers.tencent.com/search.html?keyword=strategy&location=Shenzhen"
    req = urllib.request.Request(tencent_url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml',
    })
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    # Try to find job data in the HTML
    job_data_match = re.findall(r'\"RecruitPostId\":(\d+).*?\"RecruitTitle\":\"(.*?)\".*?\"ResponsibilityLocation\":\"(.*?)\"', html)
    if job_data_match:
        print(f"  Found {len(job_data_match)} jobs in HTML")
        for rid, title, loc in job_data_match[:5]:
            print(f"    {title} @ {loc}")
    else:
        print(f"  HTML length: {len(html)}, no structured data found")
        # Check if there's an API endpoint
        api_match = re.findall(r'/api/[^\s"]+', html)
        if api_match:
            print(f"  API endpoints found: {api_match[:3]}")
except Exception as e:
    print(f"  Tencent error: {e}")

# --- 3. Try 51job API ---
print("\n=== 51job ===")
try:
    # 51job has a search API
    params = urllib.parse.urlencode({
        'keyword': '产品经理',
        'searchType': 2,
        'jobArea': '040090',  # Shenzhen
    })
    url51 = f"https://we.51job.com/pc/search?{params}"
    req = urllib.request.Request(url51, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml',
    })
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    print(f"  51job HTML length: {len(html)}")
    # Look for job data patterns
    job_json_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?})\s*;', html, re.DOTALL)
    if job_json_match:
        try:
            state = json.loads(job_json_match.group(1))
            print(f"  Found initial state with keys: {list(state.keys())[:5]}")
        except:
            print(f"  Initial state found but couldn't parse")
    else:
        # Try another pattern
        job_items = re.findall(r'class="j_joblist".*?href="(.*?)".*?title="(.*?)"', html, re.DOTALL)
        if job_items:
            print(f"  Found {len(job_items)} job items")
            for href, title in job_items[:5]:
                print(f"    {title}: {href}")
        else:
            print(f"  No job data patterns found")
except Exception as e:
    print(f"  51job error: {e}")

# --- 4. Try Liepin API ---
print("\n=== Liepin ===")
try:
    liepin_params = urllib.parse.urlencode({
        'key': '商业策略',
        'dq': '050090',  # Shenzhen
    })
    url_lp = f"https://www.liepin.com/zhaopin/?{liepin_params}"
    req = urllib.request.Request(url_lp, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml',
    })
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    print(f"  Liepin HTML length: {len(html)}")
    job_items = re.findall(r'data-title="(.*?)"', html)
    if job_items:
        print(f"  Found {len(job_items)} job items")
        for t in job_items[:5]:
            print(f"    {t}")
    else:
        # Try other patterns
        job_items2 = re.findall(r'class="job-title".*?>(.*?)<', html)
        if job_items2:
            print(f"  Found {len(job_items2)} job titles")
            for t in job_items2[:5]:
                print(f"    {t}")
        else:
            print(f"  No job patterns found")
except Exception as e:
    print(f"  Liepin error: {e}")

# --- 5. Try additional Greenhouse boards ---
print("\n=== Additional Greenhouse boards ===")
extra_gh = ['airbnb', 'agoda', 'shopee', 'grab', 'gojek', 'klook', 'lalamove']
for slug in extra_gh:
    url = f"https://boards-api.greenhouse.io/v1/jobs/{slug}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read())
        jobs_list = data.get('jobs', [])
        relevant = []
        for j in jobs_list:
            title = j.get('title', '')
            loc = j.get('location', {}).get('name', '')
            tl = title.lower() + ' ' + loc.lower()
            skip_kw = ['director', 'vp ', 'intern', 'software', 'frontend', 'backend',
                       'data scientist', 'designer', 'recruiter', 'analyst']
            if any(k in tl for k in skip_kw):
                continue
            match_kw = ['product manager', 'strategy', 'bizops', 'growth', 'head of']
            if any(k in tl for k in match_kw):
                target_loc = ['singapore', 'shenzhen', 'hong kong', 'shanghai', 'tokyo']
                if any(t in tl for t in target_loc):
                    gh_id = str(j.get('id', ''))
                    if gh_id not in existing_titles:
                        relevant.append(j)
        if relevant:
            print(f"  {slug}: {len(relevant)} relevant from {len(jobs_list)} total")
            for j in relevant[:3]:
                print(f"    {j['title']} @ {j.get('location',{}).get('name','')}")
        else:
            total_relevant = sum(1 for j in jobs_list if any(k in j.get('title','').lower() for k in ['product manager', 'strategy']))
            print(f"  {slug}: {len(jobs_list)} total, {total_relevant} PM/strategy (none matching criteria)")
    except Exception as e:
        print(f"  {slug}: {e}")

print("\n=== Scan complete ===")
