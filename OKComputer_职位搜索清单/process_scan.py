#!/usr/bin/env python3
"""
Process job scan results and update jobs-all.json
"""
import json
import hashlib
import os
from datetime import datetime

DB_PATH = os.path.expanduser("~/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json")

# Load existing jobs
with open(DB_PATH, 'r') as f:
    existing_jobs = json.load(f)

# Create lookup sets for dedup
existing_urls = set()
existing_titles = set()
for j in existing_jobs:
    url = j.get('url', '')
    if url:
        existing_urls.add(url.split('?')[0])  # normalize URL
    title_key = f"{j.get('company', '').lower()}|{j.get('title', '').lower()}"
    existing_titles.add(title_key)

print(f"Existing jobs: {len(existing_jobs)}")
print(f"Existing URLs: {len(existing_urls)}")

# ========== Tencent Jobs (from browser) ==========
tencent_new_jobs = [
    {
        "title": "Strategy Manager",
        "company": "Tencent",
        "location": "Shenzhen",
        "salary": "",
        "url": "https://careers.tencent.com/en-us/search.html?keyword=strategy&location=Shenzhen",
        "source": "tencent-careers",
        "description": "Strategy Manager at Level Infinite (Tencent's global gaming brand). Drive strategic development, monitor global gaming market, deliver BI reports to top executives. 5+ yrs strategy consulting/IB/gaming analysis. Fluent English+Chinese.",
        "role_type": "Strategy",
        "quality_score": 75,
        "quality_tier": "B"
    },
    {
        "title": "Senior Strategy Manager",
        "company": "Tencent",
        "location": "Shanghai",
        "salary": "",
        "url": "https://careers.tencent.com/en-us/search.html?keyword=strategy&location=Shenzhen",
        "source": "tencent-careers",
        "description": "Senior Strategy Manager at Tencent. Strategy & Investment role.",
        "role_type": "Strategy",
        "quality_score": 70,
        "quality_tier": "B"
    },
    {
        "title": "Business Strategy & Analysis Manager",
        "company": "Tencent",
        "location": "Amsterdam",
        "salary": "",
        "url": "https://careers.tencent.com/en-us/search.html?keyword=strategy&location=Shenzhen",
        "source": "tencent-careers",
        "description": "Business Strategy & Analysis Manager at Tencent Amsterdam.",
        "role_type": "Strategy",
        "quality_score": 60,
        "quality_tier": "C"
    }
]

# ========== Liepin Jobs (filtered for relevance) ==========
liepin_new_jobs = [
    {
        "title": "高级产品经理 Product Manager (Banking)",
        "company": "赞德科技",
        "location": "深圳-南山区",
        "salary": "20-40k",
        "url": "https://www.liepin.com/job/1981270935.shtml",
        "source": "liepin",
        "description": "高级产品经理 Product Manager (Banking) at 赞德科技 in Shenzhen Nanshan. 3+ yrs, Bachelor's degree. Banking/fintech focus.",
        "role_type": "Product Manager",
        "quality_score": 65,
        "quality_tier": "B"
    },
    {
        "title": "系统AI产品经理 (AI OS Product Manager)",
        "company": "深圳纳欣科技有限公司",
        "location": "深圳-福田区",
        "salary": "25-40k·14薪",
        "url": "https://www.liepin.com/job/1983950045.shtml",
        "source": "liepin",
        "description": "系统AI产品经理 at 深圳纳欣科技. 3+ yrs, Bachelor's. AI/smart hardware focus. 500-999 employees.",
        "role_type": "Product Manager",
        "quality_score": 60,
        "quality_tier": "B"
    },
    {
        "title": "高级产品经理（小家电/厨电类/环境类）",
        "company": "深圳市微智盛网络技术有限公司",
        "location": "深圳-龙岗区",
        "salary": "35-55k",
        "url": "https://www.liepin.com/job/1983545817.shtml",
        "source": "liepin",
        "description": "高级产品经理 at 深圳市微智盛. 5+ yrs, Bachelor's. E-commerce focus. 100-499 employees.",
        "role_type": "Product Manager",
        "quality_score": 55,
        "quality_tier": "C"
    },
    {
        "title": "PM资深产品经理（某深圳上市半导体公司）",
        "company": "猎头推荐-深圳上市半导体",
        "location": "深圳",
        "salary": "40-60k",
        "url": "https://www.liepin.com/a/74956919.shtml",
        "source": "liepin",
        "description": "资深产品经理 at listed semiconductor company in Shenzhen. 10+ yrs, Bachelor's. Via headhunter.",
        "role_type": "Product Manager",
        "quality_score": 50,
        "quality_tier": "C"
    },
    {
        "title": "资深产品经理（存储行业、信创）",
        "company": "猎头推荐-深圳上市半导体",
        "location": "深圳-福田区",
        "salary": "40-60k",
        "url": "https://www.liepin.com/a/75291301.shtml",
        "source": "liepin",
        "description": "资深产品经理 in storage/xinchuang sector. 10+ yrs, Bachelor's. Listed company. Via headhunter.",
        "role_type": "Product Manager",
        "quality_score": 50,
        "quality_tier": "C"
    },
    {
        "title": "PM/产品经理（化妆品）",
        "company": "猎头推荐-深圳制药",
        "location": "深圳",
        "salary": "30-50k",
        "url": "https://www.liepin.com/a/75886675.shtml",
        "source": "liepin",
        "description": "PM/产品经理 cosmetics sector. 5-10 yrs, Bachelor's. C-round company. Via headhunter.",
        "role_type": "Product Manager",
        "quality_score": 45,
        "quality_tier": "C"
    },
    {
        "title": "ASIA PM 产品经理（知名外企）",
        "company": "猎头推荐-知名外企",
        "location": "深圳-龙岗区",
        "salary": "30-60k·15薪",
        "url": "https://www.liepin.com/a/77389341.shtml",
        "source": "liepin",
        "description": "ASIA PM Product Manager at well-known foreign company. 8+ yrs, Bachelor's. Mechanical/equipment sector. Via headhunter.",
        "role_type": "Product Manager",
        "quality_score": 55,
        "quality_tier": "C"
    },
    {
        "title": "产品经理Product Manager",
        "company": "猎头推荐-通信设备",
        "location": "深圳",
        "salary": "25-35k·16薪",
        "url": "https://www.liepin.com/a/75352981.shtml",
        "source": "liepin",
        "description": "Product Manager at Chinese telecom equipment company. 3+ yrs, Bachelor's. 500-999 employees. Via headhunter.",
        "role_type": "Product Manager",
        "quality_score": 50,
        "quality_tier": "C"
    }
]

# Combine all new jobs
all_new = tencent_new_jobs + liepin_new_jobs

# Filter for quality and salary threshold
filtered_new = []
for job in all_new:
    # Skip if already exists
    url_base = job['url'].split('?')[0]
    title_key = f"{job.get('company', '').lower()}|{job.get('title', '').lower()}"
    
    if url_base in existing_urls:
        print(f"SKIP (duplicate URL): {job['title']} @ {job['company']}")
        continue
    if title_key in existing_titles:
        print(f"SKIP (duplicate title): {job['title']} @ {job['company']}")
        continue
    
    # Check salary minimum (≥15k RMB/mo)
    salary_str = job.get('salary', '')
    if salary_str and salary_str != '薪资面议':
        # Extract numeric salary
        import re
        nums = re.findall(r'(\d+)', salary_str)
        if nums:
            max_salary = max(int(n) for n in nums)
            if max_salary < 15 and '万' not in salary_str:  # Less than 15k
                print(f"SKIP (salary too low): {job['title']} @ {job['company']} - {salary_str}")
                continue
    
    # Skip Director/VP roles
    title_lower = job.get('title', '').lower()
    if any(kw in title_lower for kw in ['director', 'vp', 'vice president', 'managing director']):
        print(f"SKIP (senior level): {job['title']}")
        continue
    
    # Skip internships
    if 'intern' in title_lower or '实习' in job.get('title', ''):
        print(f"SKIP (internship): {job['title']}")
        continue
    
    # Add metadata
    job['posted'] = datetime.now().isoformat()
    job['scanned_date'] = datetime.now().strftime('%Y-%m-%d')
    job['status'] = 'not_applied'
    job['status_date'] = datetime.now().strftime('%Y-%m-%d')
    job['last_touch_date'] = datetime.now().strftime('%Y-%m-%d')
    
    # Generate job_id
    job['job_id'] = hashlib.md5(f"{job.get('company', '')}-{job.get('title', '')}-{job.get('url', '')}".encode()).hexdigest()[:12]
    
    filtered_new.append(job)
    print(f"NEW: {job['title']} @ {job['company']} - {job.get('salary', 'N/A')}")

print(f"\nTotal new jobs to add: {len(filtered_new)}")

# Add to database
existing_jobs.extend(filtered_new)

# Save
with open(DB_PATH, 'w') as f:
    json.dump(existing_jobs, f, indent=2, ensure_ascii=False)

print(f"Database updated: {len(existing_jobs)} total jobs")
