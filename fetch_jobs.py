#!/usr/bin/env python3
"""Fetch jobs from Greenhouse APIs and output as JSON."""
import json
import urllib.request
import sys
from datetime import datetime

COMPANIES = {
    'okx': 'OKX',
    'stripe': 'Stripe',
    'airwallex': 'Airwallex',
    'coupang': 'Coupang',
}

TARGET_LOCS = ['shenzhen', 'hong kong', 'hong kong sar', 'guangzhou', 'shanghai', 'singapore']
KEYWORDS_PM = ['product manager', 'product lead', 'product director', 'head of product',
               'strategy', 'bizops', 'business operations', 'general manager',
               'growth', 'expansion', 'chief of staff', 'program manager',
               'go-to-market', 'gtm', 'commercial', 'cross-border']
REJECT = ['intern', 'internship', 'director', 'vp ', 'vice president', 'senior director',
          'managing director', 'data scientist', 'software engineer', 'developer',
          'sales manager', 'hr ', 'recruiting', 'legal', 'accountant', 'designer',
          'devops', 'sre', 'ux ', 'ui ', 'frontend', 'backend']

all_jobs = []

for board, company_name in COMPANIES.items():
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=false"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read().decode())
        jobs = data.get('jobs', [])
        print(f"[{company_name}] {len(jobs)} total jobs on Greenhouse", file=sys.stderr)
        
        for j in jobs:
            title = j.get('title', '')
            loc = j.get('location', {}).get('name', '')
            loc_lower = loc.lower()
            title_lower = title.lower()
            posted = j.get('updated_at', '')
            job_url = j.get('absolute_url', '')
            job_id = j.get('id', '')
            
            # Filter: must be in target location
            if not any(t in loc_lower for t in TARGET_LOCS):
                continue
            
            # Filter: must match PM/strategy keywords
            if not any(k in title_lower for k in KEYWORDS_PM):
                continue
            
            # Filter: reject unwanted roles
            if any(r in title_lower for r in REJECT):
                continue
            
            all_jobs.append({
                'title': title,
                'company': company_name,
                'location': loc,
                'salary': '',
                'url': job_url,
                'source': 'greenhouse_api',
                'role_type': 'product' if 'product' in title_lower else 'strategy',
                'grade': 'A',
                'quality_tier': 'A',
                'quality_score': 80,
                'scanned_date': datetime.now().strftime('%Y-%m-%d'),
                'en_title': title,
                'summary': f"{title} at {company_name} in {loc}",
                'english_friendly': True,
                'posted_date': posted[:10] if posted else '',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'date_source': 'backfilled_from_scanned_date',
                'platform': 'Greenhouse',
                'low_quality': False,
                'is_director': any(d in title_lower for d in ['director', 'vp', 'vice president']),
                'category': 'strategy' if 'strategy' in title_lower else 'product',
                'company_type': 'crypto_exchange' if board == 'okx' else 'fintech' if board in ['stripe', 'airwallex'] else 'ecommerce',
            })
    except Exception as e:
        print(f"[{company_name}] Error: {e}", file=sys.stderr)

print(json.dumps(all_jobs, ensure_ascii=False, indent=2))
