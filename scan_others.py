#!/usr/bin/env python3
"""Scan Liepin and Tencent/ByteDance career sites"""
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

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# Liepin search
print("=== Scanning Liepin ===")
liepin_searches = [
    {"keyword": "产品经理", "city": "050090", "city_name": "深圳"},
    {"keyword": "商业策略", "city": "050090", "city_name": "深圳"},
]

for search in liepin_searches:
    keyword = search["keyword"]
    city = search["city"]
    city_name = search["city_name"]
    
    encoded_kw = urllib.parse.quote(keyword)
    url = f"https://api-c.liepin.com/api/com.liepin.searchfront4c.pc-search-job?key={encoded_kw}&dq={city}&curPage=0&pageSize=20&scene=company"
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        
        jobs_data = data.get("data", {}).get("data", {})
        items = jobs_data.get("jobCardList", []) if isinstance(jobs_data, dict) else []
        print(f"  📋 Liepin {keyword} in {city_name}: {len(items)} results")
        
        for item in items:
            job = item.get("job", {}) if isinstance(item, dict) else {}
            if not job:
                continue
            title = job.get("title", "")
            company = job.get("compName", "")
            salary = job.get("salary", "")
            city_label = job.get("dq", city_name)
            job_id = job.get("jobId", "")
            job_url = f"https://www.liepin.com/job/{job_id}" if job_id else ""
            
            if not job_url or job_url in existing_urls:
                continue
            
            # Parse salary
            salary_lower = salary.lower() if salary else ""
            min_salary = 0
            try:
                parts = salary.replace("万", "").replace("千", "").replace("/月", "").replace("·", "-").split("-")
                if len(parts) >= 2:
                    num1 = float(parts[0].strip())
                    if "万" in salary:
                        min_salary = num1 * 10000
                    elif "千" in salary:
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
                "location": f"{city_label}, China",
                "url": job_url,
                "source": "liepin",
                "salary": salary,
                "scanned_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "posted_date": "",
                "quality_score": 60,
                "quality_tier": "C",
                "grade": "C",
                "english_friendly": False,
                "platform": "Liepin",
                "low_quality": False,
            })
            
    except Exception as e:
        print(f"  ⚠ Failed to fetch Liepin {keyword} in {city_name}: {e}")

# Tencent careers
print("\n=== Scanning Tencent Careers ===")
try:
    url = "https://careers.tencent.com/tencentcareer/api/post/Query?keyword=strategy&locationId=&categoryId=&pageIndex=1&pageSize=20&language=en&area=cn"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    
    posts = data.get("Data", {}).get("Posts", []) if isinstance(data.get("Data"), dict) else []
    print(f"  📋 Tencent careers: {len(posts)} results")
    
    for post in posts:
        title = post.get("RecruitPostName", "")
        department = post.get("DepartmentName", "")
        location = post.get("LocationName", "Shenzhen")
        post_id = post.get("PostId", "")
        job_url = f"https://careers.tencent.com/jobdesc.html?postId={post_id}" if post_id else ""
        category = post.get("CategoryName", "")
        
        if not job_url or job_url in existing_urls:
            continue
        
        new_jobs.append({
            "title": title,
            "company": "Tencent",
            "location": f"{location}, China",
            "url": job_url,
            "source": "tencent_careers",
            "salary": "Not listed",
            "scanned_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "posted_date": "",
            "quality_score": 70,
            "quality_tier": "B",
            "grade": "B",
            "english_friendly": True,
            "platform": "Tencent Careers",
            "low_quality": False,
        })
        
except Exception as e:
    print(f"  ⚠ Failed to fetch Tencent careers: {e}")

# ByteDance careers
print("\n=== Scanning ByteDance Careers ===")
try:
    url = "https://jobs.bytedance.com/api/v1/search/position?keyword=产品经理&limit=20&offset=0&job_category_id=&location=&city_code=&recruit_type=&tag=&type=2"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    
    positions = data.get("data", {}).get("position_list", []) if isinstance(data.get("data"), dict) else []
    print(f"  📋 ByteDance careers: {len(positions)} results")
    
    for pos in positions:
        title = pos.get("name", "")
        city = pos.get("city_info", {}).get("name", "")
        job_id = pos.get("id", "")
        job_url = f"https://jobs.bytedance.com/experienced/position/{job_id}/detail" if job_id else ""
        
        if not job_url or job_url in existing_urls:
            continue
        
        new_jobs.append({
            "title": title,
            "company": "ByteDance",
            "location": f"{city}, China",
            "url": job_url,
            "source": "bytedance_careers",
            "salary": "Not listed",
            "scanned_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "posted_date": "",
            "quality_score": 70,
            "quality_tier": "B",
            "grade": "B",
            "english_friendly": True,
            "platform": "ByteDance Careers",
            "low_quality": False,
        })
        
except Exception as e:
    print(f"  ⚠ Failed to fetch ByteDance careers: {e}")

print(f"\n=== Total new jobs from other sources: {len(new_jobs)} ===")
for j in new_jobs[:20]:
    print(f"  📌 {j['title']} @ {j['company']} | {j['location']}")

if new_jobs:
    existing_jobs.extend(new_jobs)
    with open(existing_path, 'w', encoding='utf-8') as f:
        json.dump(existing_jobs, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved {len(new_jobs)} new jobs to database (total: {len(existing_jobs)})")
