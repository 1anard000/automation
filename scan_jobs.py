#!/usr/bin/env python3
"""Scan Greenhouse APIs and other job sources for new jobs."""
import json
import urllib.request
import os
import sys
from datetime import datetime, timezone

JOBS_FILE = os.path.expanduser("~/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json")

def load_existing_jobs():
    with open(JOBS_FILE, "r") as f:
        return json.load(f)

def save_jobs(jobs):
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

def fetch_greenhouse(company):
    url = f"https://boards-api.greenhouse.io/v1/jobs/{company}?content=false"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  Error fetching {company}: {e}")
        return None

KEYWORDS_PRODUCT = ['product manager', 'product management', 'product lead', 'product strategy',
                     '商业策略', '产品经理', 'strategy', 'business strategy', 'bizops', 'biz ops',
                     'business operations', 'growth', 'growth manager', 'gm role', 'commercial',
                     'partnerships', 'business development', 'bd lead', 'general manager']

TARGET_LOCATIONS = ['shenzhen', 'hong kong', 'hk', 'guangzhou', 'shanghai', 'singapore',
                    '深圳', '香港', '广州', '上海', '新加坡', 'seoul', 'bangkok', 'taipei', 'tokyo']

def is_relevant(title, location=""):
    title_lower = title.lower()
    loc_lower = location.lower()

    # Check if title matches
    title_match = any(kw in title_lower for kw in KEYWORDS_PRODUCT)

    # Check if location matches
    loc_match = any(loc in loc_lower for loc in TARGET_LOCATIONS) if location else True

    # Skip unwanted roles
    skip_words = ['intern', 'internship', 'director', 'vp', 'vice president',
                  'internship', 'coordinator', 'analyst', 'junior', 'entry level',
                  'security', 'data engineer', 'backend', 'frontend', 'devops',
                  'sre', 'software engineer', 'software developer', 'qa',
                  'quality assurance', 'test engineer', 'designer', 'design',
                  'recruiter', 'recruiting', 'hr ', 'human resources',
                  'legal', 'finance', 'accounting', 'accountant', 'auditor',
                  'operations analyst', 'operations specialist']
    skip_match = any(skip in title_lower for skip in skip_words)

    return title_match and loc_match and not skip_match

def get_salary_range(job):
    """Extract salary from Greenhouse job if available."""
    salary = job.get("salary", None)
    if salary:
        return salary
    return None

def process_greenhouse(source_name, company_key):
    data = fetch_greenhouse(company_key)
    if not data:
        return []

    jobs = data.get("jobs", [])
    results = []
    for j in jobs:
        title = j.get("title", "")
        location = j.get("location", {}).get("name", "")
        job_id = j.get("id", "")
        absolute_url = j.get("absolute_url", "")

        if is_relevant(title, location):
            url = absolute_url or f"https://job-boards.greenhouse.io/{company_key}/jobs/{job_id}"
            salary = get_salary_range(j)
            results.append({
                "title": title,
                "company": company_key.title(),
                "location": location,
                "salary": salary or "Not listed",
                "url": url,
                "source": source_name,
                "role_type": "greenhouse_scan",
                "description": "",
                "posted_date": j.get("updated_at") or j.get("created_at") or datetime.now(timezone.utc).isoformat(),
                "scanned_date": datetime.now().strftime("%Y-%m-%d"),
                "grade": "B"
            })
    return results

def main():
    existing = load_existing_jobs()
    existing_urls = set(j["url"] for j in existing)
    existing_titles = set((j["title"].lower().strip(), j["company"].lower().strip()) for j in existing)

    print(f"Existing jobs: {len(existing)}")
    print(f"Existing unique URLs: {len(existing_urls)}")

    all_new = []

    # Scan Greenhouse APIs
    companies = [
        ("greenhouse_okx", "okx"),
        ("greenhouse_airwallex", "airwallex"),
        ("greenhouse_stripe", "stripe"),
        ("greenhouse_agoda", "agoda"),
        ("greenhouse_coupang", "coupang"),
    ]

    for source_name, company_key in companies:
        print(f"\nScanning {company_key}...")
        new_jobs = process_greenhouse(source_name, company_key)
        truly_new = []
        for j in new_jobs:
            title_company = (j["title"].lower().strip(), j["company"].lower().strip())
            if j["url"] not in existing_urls and title_company not in existing_titles:
                truly_new.append(j)
        print(f"  Found {len(new_jobs)} relevant, {len(truly_new)} new")
        all_new.extend(truly_new)

    # Try Tencent careers API
    print("\nScanning Tencent careers...")
    try:
        tencent_url = "https://careers.tencent.com/v3/schema/search?keyword=strategy&limit=50&offset=0"
        req = urllib.request.Request(tencent_url, headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            tencent_jobs = data.get("data", {}).get("posts", [])
            if not tencent_jobs and isinstance(data, dict):
                # Try alternative response structure
                tencent_jobs = data.get("jobs", []) or data.get("results", [])
            tencent_new = []
            for j in tencent_jobs:
                title = j.get("RecruitmentPostName", j.get("title", ""))
                location = j.get("LocationName", j.get("location", ""))
                city = j.get("City", "")
                location = location or city
                job_id = j.get("PostId", j.get("id", ""))
                url = j.get("Url", f"https://careers.tencent.com/en-us/search.html?keyword=strategy")

                if is_relevant(title, location):
                    title_company = (title.lower().strip(), "tencent")
                    if url not in existing_urls and title_company not in existing_titles:
                        tencent_new.append({
                            "title": title,
                            "company": "Tencent",
                            "location": location,
                            "salary": "Not listed",
                            "url": url,
                            "source": "tencent_careers",
                            "role_type": "target_profile",
                            "description": "",
                            "scanned_date": datetime.now().strftime("%Y-%m-%d"),
                            "grade": "B"
                        })
            print(f"  Found {len(tencent_new)} new from Tencent")
            all_new.extend(tencent_new)
    except Exception as e:
        print(f"  Error: {e}")

    # Try ByteDance careers API
    print("\nScanning ByteDance careers...")
    try:
        bd_url = "https://jobs.bytedance.com/api/v1/search/position?keyword=产品经理&limit=50&offset=0&city_name=深圳"
        req = urllib.request.Request(bd_url, headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            bd_jobs = data.get("data", {}).get("job_post_list", [])
            if not bd_jobs:
                bd_jobs = data.get("data", {}).get("positions", [])
            bd_new = []
            for j in bd_jobs:
                title = j.get("name", j.get("title", ""))
                location = j.get("city", "")
                if not location:
                    loc_parts = [j.get("city_name", ""), j.get("area_name", "")]
                    location = ", ".join(p for p in loc_parts if p)
                job_id = j.get("id", "")
                url = j.get("url", f"https://jobs.bytedance.com/experienced/position/{job_id}")

                if is_relevant(title, location):
                    title_company = (title.lower().strip(), "bytedance")
                    if url not in existing_urls and title_company not in existing_titles:
                        bd_new.append({
                            "title": title,
                            "company": "ByteDance",
                            "location": location,
                            "salary": "Not listed",
                            "url": url,
                            "source": "bytedance_careers",
                            "role_type": "target_profile",
                            "description": "",
                            "scanned_date": datetime.now().strftime("%Y-%m-%d"),
                            "grade": "B"
                        })
            print(f"  Found {len(bd_new)} new from ByteDance")
            all_new.extend(bd_new)
    except Exception as e:
        print(f"  Error: {e}")

    # Try 51job API
    print("\nScanning 51job...")
    try:
        job51_url = "https://search.51job.com/list/040090,000000,0000,00,9,99,产品经理,2,1.html"
        # 51job doesn't have a clean API, skip for now
        print("  51job: Skipped (no clean API available)")
    except Exception as e:
        print(f"  Error: {e}")

    # Add new jobs to database
    if all_new:
        print(f"\n=== Adding {len(all_new)} new jobs ===")
        for j in all_new:
            print(f"  + {j['title']} @ {j['company']} | {j['location']}")
            # Add to existing
            existing.append(j)
            # Also add a minimal entry to existing_urls to prevent duplicates within this batch
            existing_urls.add(j["url"])
            existing_titles.add((j["title"].lower().strip(), j["company"].lower().strip()))

        save_jobs(existing)
        print(f"\nSaved. Total jobs now: {len(existing)}")
    else:
        print("\nNo new jobs found.")

    # Output summary for the caller
    summary = {
        "new_count": len(all_new),
        "new_jobs": all_new,
        "total_jobs": len(existing),
        "scan_time": datetime.now().isoformat()
    }
    with open(os.path.expanduser("~/.openclaw/workspace/last_scan_summary.json"), "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return all_new

if __name__ == "__main__":
    new = main()
    print(f"\nDone. {len(new)} new jobs added.")
