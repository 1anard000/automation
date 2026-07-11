#!/usr/bin/env python3
"""Scan Greenhouse job boards for new relevant jobs."""
import json
import urllib.request
import sys

def fetch_gh_jobs(company):
    url = f'https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true'
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
        return data.get('jobs', [])
    except Exception as e:
        print(f'ERROR fetching {company}: {e}', file=sys.stderr)
        return []

def main():
    # Load existing URLs
    with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json') as f:
        existing = json.load(f)
    existing_urls = {j.get('url', '') for j in existing}
    existing_titles = {(j.get('title', ''), j.get('company', '')) for j in existing}
    print(f'Existing jobs: {len(existing)}, URLs: {len(existing_urls)}')

    locations_kw = ['shenzhen', 'hong kong', 'singapore', 'shanghai', 'guangzhou', 'greater bay', 'hk', 'apac', 'asia pacific']
    role_kw = ['product', 'strategy', 'growth', 'bizops', 'business operation', 'partnerships', 'gm', 'lead', 'expansion', 'marketplace']
    skip_kw = ['intern', 'internship', 'director', 'vp ', 'vice president']

    new_jobs = []

    companies = ['okx', 'stripe', 'airwallex', 'coupang']
    for company in companies:
        print(f'\n--- {company.upper()} ---')
        jobs = fetch_gh_jobs(company)
        print(f'Total jobs: {len(jobs)}')
        found = 0
        for j in jobs:
            title = j.get('title', '')
            title_lower = title.lower()
            location = j.get('location', {}).get('name', '')
            loc_lower = location.lower()

            # Location filter
            loc_match = any(lk in loc_lower for lk in locations_kw)
            if not loc_match:
                continue

            # Role filter
            role_match = any(kw in title_lower for kw in role_kw)
            if not role_match:
                continue

            # Skip low-level / too senior
            if any(kw in title_lower for kw in skip_kw):
                continue

            url = j.get('absolute_url', '')
            if not url:
                url = f"https://job-boards.greenhouse.io/{company}/jobs/{j.get('id', '')}"

            # Check dedup
            if url in existing_urls:
                continue
            if (title, company.title()) in existing_titles:
                continue

            desc_raw = j.get('content', '')
            desc = ''
            if desc_raw:
                # Strip HTML
                import re
                desc = re.sub('<[^<]+?>', '', desc_raw)[:300]

            new_jobs.append({
                'title': title,
                'company': company.title(),
                'location': location,
                'salary': 'Not listed',
                'url': url,
                'source': 'greenhouse_api',
                'role_type': title,
                'description': desc,
                'grade': '',
                'quality_tier': '',
                'english_friendly': True,
                'scanned_date': '2026-07-12',
                'en_title': title,
                'summary': f'{title} at {company.title()} in {location}',
            })
            print(f'  NEW: {title} | {location} | {url}')
            found += 1

        if found == 0:
            print(f'  No new matching jobs')

    print(f'\n=== TOTAL NEW JOBS FOUND: {len(new_jobs)} ===')
    # Output as JSON for further processing
    with open('/tmp/new_greenhouse_jobs.json', 'w') as f:
        json.dump(new_jobs, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    main()
