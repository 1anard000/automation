import json
import urllib.request

companies = ['okx', 'stripe', 'coupang', 'flexport']
existing_urls = set()

# Load existing jobs
with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json', 'r') as f:
    existing = json.load(f)
    for j in existing:
        existing_urls.add(j.get('url', ''))

print(f"Existing jobs: {len(existing)}")

new_jobs = []

for company in companies:
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=20)
        data = json.loads(resp.read())
        jobs = data.get('jobs', [])
        print(f"\n{company}: {len(jobs)} total jobs")
        
        company_new = 0
        for j in jobs:
            title = j.get('title', '')
            location = j.get('location', {}).get('name', '')
            updated = j.get('updated_at', '')
            job_id = j.get('id', '')
            job_url = f"https://boards.greenhouse.io/{company}/jobs/{job_id}"
            
            # Check alternate URL formats in existing
            alt_url = j.get('absolute_url', '')
            if job_url in existing_urls or alt_url in existing_urls:
                continue
            
            # Also check by job ID pattern
            id_found = False
            for eu in existing_urls:
                if str(job_id) in eu:
                    id_found = True
                    break
            if id_found:
                continue
            
            # Filter by location
            loc_lower = location.lower()
            is_target_loc = any(k in loc_lower for k in [
                'shenzhen', 'hong kong', 'guangzhou', 'shanghai', 'singapore', 
                'remote', 'asia', 'apac', 'china', 'hk', 'sg'
            ])
            
            # Filter by title (PM, strategy, bizops, growth, GM)
            title_lower = title.lower()
            is_target_role = any(k in title_lower for k in [
                'product manager', 'product director', 'product management',
                'strategy', 'bizops', 'growth', 'general manager',
                'business development', 'head of product', 'lead product',
                'staff product', 'principal product', 'senior product',
                'commercial', 'partnership', 'business operations'
            ])
            
            # Skip Director/VP/Managing Director
            skip_titles = ['vice president', 'managing director']
            is_skip = any(k in title_lower for k in skip_titles)
            
            if is_target_loc and is_target_role and not is_skip:
                company_new += 1
                new_jobs.append({
                    'title': title,
                    'company': company.capitalize(),
                    'location': location,
                    'salary': 'Not listed',
                    'url': job_url,
                    'source': 'greenhouse_api',
                    'role_type': 'Product Management',
                    'scanned_date': '2026-07-23',
                    'posted_date': updated
                })
                print(f"  NEW: {title} | {location} | {updated[:10] if updated else 'N/A'}")
        
        print(f"  ({company_new} new from {company})")
                
    except Exception as e:
        print(f"  ERROR fetching {company}: {e}")

print(f"\n--- TOTAL NEW JOBS FOUND: {len(new_jobs)} ---")
for j in new_jobs:
    print(f"  {j['company']} | {j['title']} | {j['location']} | {j['url']}")

# Save to temp file
with open('/Users/iancolrick/.openclaw/workspace/new_jobs_greenhouse.json', 'w') as f:
    json.dump(new_jobs, f, indent=2, ensure_ascii=False)
