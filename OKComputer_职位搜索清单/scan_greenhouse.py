#!/usr/bin/env python3
"""Scan Greenhouse API for OKX, Stripe, Airwallex, Coupang jobs."""
import json
import urllib.request
import sys

companies = {
    'okx': 'https://boards-api.greenhouse.io/v1/jobs/okx?content=true',
    'stripe': 'https://boards-api.greenhouse.io/v1/jobs/stripe?content=true',
    'airwallex': 'https://boards-api.greenhouse.io/v1/jobs/airwallex?content=true',
    'coupang': 'https://boards-api.greenhouse.io/v1/jobs/coupang?content=true',
}

keywords = ['strategy', 'product', 'growth', 'gm', 'bizops', 'operations',
            'general manager', 'lead', 'senior manager', 'manager', 'head']
location_keywords = ['shenzhen', 'hong kong', 'shanghai', 'singapore',
                     'guangzhou', 'remote', 'asia', 'apac', 'china', 'hk']

results = []

for company, url in companies.items():
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        jobs = data.get('jobs', [])
        for j in jobs:
            title = j.get('title', '')
            loc = j.get('location', {}).get('name', '')
            absolute_url = j.get('absolute_url', '')
            updated = j.get('updated_at', '')
            title_lower = title.lower()
            loc_lower = loc.lower()
            has_keyword = any(k in title_lower for k in keywords)
            has_location = any(l in loc_lower for l in location_keywords)
            if has_keyword and has_location:
                results.append({
                    'company': company,
                    'title': title,
                    'location': loc,
                    'url': absolute_url,
                    'updated': updated,
                })
        print(f"[OK] {company}: {len(jobs)} total jobs, {sum(1 for r in results if r['company']==company)} matches", file=sys.stderr)
    except Exception as e:
        print(f"[ERR] {company}: {e}", file=sys.stderr)

print(json.dumps(results, indent=2))
