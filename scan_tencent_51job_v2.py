import json
import urllib.request
import urllib.parse

# Try Tencent Workday API
print("=== TENCENT WORKDAY API ===")
try:
    workday_url = "https://tencent.wd1.myworkdayjobs.com/wday/cxs/tencent/Tencent_Careers/jobs"
    payload = json.dumps({
        "appliedFacets": {},
        "limit": 20,
        "offset": 0,
        "searchText": "strategy product Shenzhen"
    }).encode('utf-8')
    
    req = urllib.request.Request(workday_url, data=payload, headers={
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    })
    resp = urllib.request.urlopen(req, timeout=15)
    data = json.loads(resp.read())
    jobs = data.get('jobPostings', [])
    print(f"Tencent Workday: {len(jobs)} jobs")
    for j in jobs[:10]:
        ext_path = j.get('externalPath', '')
        title = j.get('title', '')
        loc = j.get('locationsText', '') or j.get('bulletFields', [''])[0] if j.get('bulletFields') else ''
        posted = j.get('postedOn', '')
        print(f"  {title} | {loc} | {posted}")
        if ext_path:
            print(f"    https://tencent.wd1.myworkdayjobs.com/en-us/Tencent_Careers{ext_path}")
except Exception as e:
    print(f"Error: {e}")

# Try 51job with proper encoding
print("\n=== 51JOB ===")
try:
    keyword = urllib.parse.quote('产品经理')
    area = '040090'  # Shenzhen
    search_url = f"https://we.51job.com/api/job/search-pc?api_key=51job&keyword={keyword}&searchType=2&jobArea={area}&keywordType=2&pageNum=1&pageSize=20&source=1"
    req = urllib.request.Request(search_url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json'
    })
    resp = urllib.request.urlopen(req, timeout=15)
    data = json.loads(resp.read())
    print(f"51job response keys: {list(data.keys())}")
    if 'resultbody' in data:
        jobs = data['resultbody'].get('job', {}).get('items', [])
        print(f"51job: {len(jobs)} jobs")
        for j in jobs[:10]:
            print(f"  {j.get('jobName', '')} | {j.get('companyName', '')} | {j.get('provideSalaryString', '')}")
except Exception as e:
    print(f"51job error: {e}")
