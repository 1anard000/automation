#!/usr/bin/env python3
"""Scrape 51job for PM/Strategy roles in Shenzhen and HK"""
import urllib.request
import urllib.error
import urllib.parse
import json
from datetime import datetime, timezone

existing_path = "/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json"
with open(existing_path) as f:
    existing_jobs = json.load(f)

existing_urls = set(j.get("url", "") for j in existing_jobs)
new_jobs = []

searches = [
    {"keyword": "产品经理", "area": "040090", "area_name": "深圳"},
    {"keyword": "商业策略", "area": "040090", "area_name": "深圳"},
    {"keyword": "产品经理", "area": "040020", "area_name": "香港"},
    {"keyword": "Growth", "area": "040090", "area_name": "深圳"},
    {"keyword": "商业策略", "area": "040020", "area_name": "香港"},
]

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://we.51job.com/",
}

for search in searches:
    keyword = search["keyword"]
    area = search["area"]
    area_name = search["area_name"]
    
    encoded_kw = urllib.parse.quote(keyword)
    url = f"https://we.51job.com/api/job/search-pc?api_key=51job&keyword={encoded_kw}&searchType=2&jobArea={area}&page=1&pageSize=20&source=1&timestamp={int(datetime.now(timezone.utc).timestamp())}"
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        
        result = data.get("resultbody", {}).get("job", {}).get("items", [])
        print(f"  📋 51job {keyword} in {area_name}: {len(result)} results")
        
        for item in result:
            title = item.get("jobName", "")
            company = item.get("companyName", "")
            salary = item.get("jobSalary", "")
            city = item.get("jobArea", area_name)
            job_url = item.get("jobHref", "")
            job_id = item.get("jobId", "")
            
            if not job_url and job_id:
                job_url = f"https://jobs.51job.com/{area_name}/{job_id}.html"
            
            if not job_url or job_url in existing_urls:
                continue
                
            salary_lower = salary.lower()
            min_salary = 0
            try:
                parts = salary.replace("万", "").replace("千", "").replace("/月", "").split("-")
                if len(parts) == 2:
                    num1 = float(parts[0].strip())
                    if "千" in salary:
                        min_salary = num1 * 1000
                    else:
                        min_salary = num1 * 1000 if num1 < 100 else num1 * 10000
            except:
                pass
            
            if min_salary > 0 and min_salary < 15000:
                continue
                
            new_jobs.append({
                "title": title,
                "company": company,
                "location": f"{city}, China",
                "url": job_url,
                "source": "51job",
                "salary": salary,
                "scanned_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "posted_date": "",
                "quality_score": 60,
                "quality_tier": "C",
                "grade": "C",
                "english_friendly": False,
                "platform": "51job",
                "low_quality": False,
            })
            
    except Exception as e:
        print(f"  ⚠ Failed to fetch 51job {keyword} in {area_name}: {e}")

print(f"\n=== 51job: Found {len(new_jobs)} new jobs ===")
for j in new_jobs[:15]:
    print(f"  📌 {j['title']} @ {j['company']} | {j['location']} | {j['salary']}")

if new_jobs:
    existing_jobs.extend(new_jobs)
    with open(existing_path, 'w', encoding='utf-8') as f:
        json.dump(existing_jobs, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved {len(new_jobs)} new jobs to database (total: {len(existing_jobs)})")
