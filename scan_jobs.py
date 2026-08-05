#!/usr/bin/env python3
"""Full job scan - Greenhouse APIs + other sources."""
import json
import urllib.request
import urllib.parse
import os
from datetime import datetime, timezone

JOBS_FILE = os.path.expanduser("~/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json")

KEYWORDS = ['product manager', 'product management', 'product lead', 'product strategy',
            '产品经理', 'strategy', 'business strategy', 'bizops', 'biz ops',
            'business operations', 'growth', 'growth manager', 'commercial',
            'partnerships', 'business development', 'general manager',
            'senior product', 'lead product', 'strategic', 'head of product',
            'director of product', 'platform manager', 'marketplace',
            'cross-border', 'cross border', 'fintech', 'ai product']

TARGET_LOCATIONS = ['shenzhen', 'hong kong', 'hk', 'guangzhou', 'shanghai', 'singapore',
                    '深圳', '香港', '广州', '上海', '新加坡', 'seoul', 'bangkok',
                    'taipei', 'tokyo', 'china', 'asia', 'apac', 'southeast asia',
                    'remote', 'hybrid', 'singapore', 'sydney', 'melbourne',
                    'new york', 'nyc', 'san francisco', 'sf', 'london']

SKIP_WORDS = ['intern', 'internship', 'coordinator', 'analyst', 'junior', 'entry level',
              'security', 'data engineer', 'backend', 'frontend', 'devops',
              'sre', 'software engineer', 'software developer', 'qa',
              'quality assurance', 'test engineer', 'designer', 'design',
              'recruiter', 'recruiting', 'hr ', 'human resources',
              'legal', 'finance', 'accounting', 'accountant', 'auditor',
              'operations analyst', 'operations specialist', 'customer success',
              'implementation', 'project manager', 'program manager',
              'graphic', 'content', 'marketing specialist', 'copywriter',
              'administrative', 'office manager', 'executive assistant',
              'receptionist', 'procurement', 'logistics', 'warehouse']

def is_relevant(title, location=""):
    title_lower = title.lower()
    title_match = any(kw in title_lower for kw in KEYWORDS)
    skip_match = any(skip in title_lower for skip in SKIP_WORDS)
    return title_match and not skip_match

def fetch_greenhouse(slug):
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=false"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  Error fetching {slug}: {e}")
        return None

def process_greenhouse(slug, display_name=None):
    data = fetch_greenhouse(slug)
    if not data:
        return []
    display_name = display_name or slug.title()
    jobs = data.get("jobs", [])
    results = []
    for j in jobs:
        title = j.get("title", "")
        location = j.get("location", {}).get("name", "")
        job_id = j.get("id", "")
        url = j.get("absolute_url", "") or f"https://job-boards.greenhouse.io/{slug}/jobs/{job_id}"
        posted = j.get("updated_at") or j.get("created_at") or datetime.now(timezone.utc).isoformat()

        if is_relevant(title, location):
            results.append({
                "title": title.strip(),
                "company": display_name,
                "location": location,
                "salary": "Not listed",
                "url": url,
                "source": f"greenhouse_{slug}",
                "role_type": "target_profile",
                "description": "",
                "posted_date": posted,
                "scanned_date": datetime.now().strftime("%Y-%m-%d"),
                "grade": "B"
            })
    return results

def main():
    with open(JOBS_FILE) as f:
        existing = json.load(f)
    existing_urls = set(j["url"] for j in existing)
    existing_tc = set((j["title"].lower().strip(), j["company"].lower().strip()) for j in existing)

    print(f"Existing jobs: {len(existing)}")

    all_new = []

    # Greenhouse scans
    greenhouse_companies = [
        ("okx", "OKX"),
        ("stripe", "Stripe"),
        ("agoda", "Agoda"),
        ("coupang", "Coupang"),
    ]
    for slug, name in greenhouse_companies:
        print(f"\nScanning {name} ({slug})...")
        jobs = process_greenhouse(slug, name)
        new = []
        for j in jobs:
            tc = (j["title"].lower().strip(), j["company"].lower().strip())
            if j["url"] not in existing_urls and tc not in existing_tc:
                new.append(j)
        print(f"  {len(jobs)} relevant, {len(new)} new")
        all_new.extend(new)

    # Try Tencent careers (they may have a job API)
    print("\nScanning Tencent careers...")
    try:
        # Tencent career search API
        tencent_url = "https://careers.tencent.com/v3/schema/search?keyword=strategy&limit=50&offset=0"
        req = urllib.request.Request(tencent_url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Accept": "application/json, text/plain, */*"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            data = json.loads(raw)
            posts = data.get("data", {}).get("posts", [])
            print(f"  Got {len(posts)} posts from Tencent API")
            tencent_new = []
            for j in posts:
                title = j.get("RecruitmentPostName", "")
                loc = j.get("LocationName", "")
                url = f"https://careers.tencent.com/en-us/search.html?keyword=strategy"
                if is_relevant(title, loc):
                    tc = (title.lower().strip(), "tencent")
                    if url not in existing_urls and tc not in existing_tc:
                        tencent_new.append({
                            "title": title.strip(),
                            "company": "Tencent",
                            "location": loc,
                            "salary": "Not listed",
                            "url": url,
                            "source": "tencent_careers",
                            "role_type": "target_profile",
                            "description": "",
                            "scanned_date": datetime.now().strftime("%Y-%m-%d"),
                            "grade": "B"
                        })
            print(f"  {len(tencent_new)} new from Tencent")
            all_new.extend(tencent_new)
    except Exception as e:
        print(f"  Error: {e}")

    # Try ByteDance careers API
    print("\nScanning ByteDance careers...")
    try:
        # Try multiple API endpoints
        bd_endpoints = [
            "https://jobs.bytedance.com/api/v1/search/position?keyword=%E4%BA%A7%E5%93%81%E7%BB%8F%E7%90%86&limit=50&offset=0",
            "https://jobs.bytedance.com/experienced/position?keywords=%E4%BA%A7%E5%93%81%E7%BB%8F%E7%90%86&location=",
        ]
        for bd_url in bd_endpoints:
            try:
                req = urllib.request.Request(bd_url, headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                    "Accept": "application/json"
                })
                with urllib.request.urlopen(req, timeout=15) as resp:
                    raw = resp.read()
                    data = json.loads(raw)
                    bd_jobs = data.get("data", {}).get("job_post_list", [])
                    if not bd_jobs:
                        bd_jobs = data.get("data", {}).get("positions", [])
                    print(f"  ByteDance: Got {len(bd_jobs)} jobs from {bd_url.split('?')[0]}")
                    for j in bd_jobs:
                        title = j.get("name", j.get("title", ""))
                        location = j.get("city", "") or j.get("city_name", "")
                        job_id = j.get("id", "")
                        url = f"https://jobs.bytedance.com/experienced/position/{job_id}"
                        if is_relevant(title, location):
                            tc = (title.lower().strip(), "bytedance")
                            if tc not in existing_tc:
                                all_new.append({
                                    "title": title.strip(),
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
                    break  # Success, don't try other endpoints
            except Exception as e:
                continue
    except Exception as e:
        print(f"  Error: {e}")

    # Save results
    if all_new:
        print(f"\n{'='*50}")
        print(f"NEW JOBS FOUND: {len(all_new)}")
        print(f"{'='*50}")
        for j in all_new:
            print(f"  + {j['title']} @ {j['company']} | {j['location']}")
            existing.append(j)
            existing_urls.add(j["url"])
            existing_tc.add((j["title"].lower().strip(), j["company"].lower().strip()))

        with open(JOBS_FILE, "w") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        print(f"\nSaved. Total: {len(existing)}")
    else:
        print("\nNo new jobs found.")

    # Write summary
    summary = {
        "new_count": len(all_new),
        "new_jobs": all_new,
        "total_jobs": len(existing),
        "scan_time": datetime.now().isoformat()
    }
    with open(os.path.expanduser("~/.openclaw/workspace/last_scan_summary.json"), "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
