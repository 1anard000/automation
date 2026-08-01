#!/usr/bin/env python3
"""Scan Greenhouse API boards for new jobs."""
import json, urllib.request, sys

# Companies with Greenhouse boards to scan
COMPANIES = {
    'okx': 'https://boards-api.greenhouse.io/v1/jobs/okx?content=false',
    'stripe': 'https://boards-api.greenhouse.io/v1/jobs/stripe?content=false',
    'airwallex': 'https://boards-api.greenhouse.io/v1/jobs/airwallex?content=false',
    'coupang': 'https://boards-api.greenhouse.io/v1/jobs/coupang?content=false',
    'agoda': 'https://boards-api.greenhouse.io/v1/jobs/agoda?content=false',
}

# Target keywords for role matching
TITLE_KEYWORDS = [
    'product manager', 'strategy', 'growth', 'general manager', 'gm ',
    'head of', 'bizops', 'business operations', 'business development',
    'cross-border', 'marketplace', 'fintech', 'payments', 'platform',
    'director', 'lead', 'chief of staff', 'go-to-market', 'gtm',
    'commercial', 'expansion', 'partnerships'
]

# Target locations
LOC_KEYWORDS = [
    'shenzhen', 'hong kong', 'singapore', 'shanghai', 'guangzhou',
    'asia', 'apac', 'greater china', 'china', 'sea', 'southeast'
]

# Title keywords to SKIP
SKIP_KEYWORDS = [
    'intern', 'internship', 'staff engineer', 'software engineer',
    'data scientist', 'devops', 'sre', 'ux designer', 'designer',
    'recruiter', 'recruiting', 'talent acquisition', 'accountant',
    'legal counsel', 'paralegal', 'receptionist', 'admin assistant'
]

# Seniority filters - skip very senior
SKIP_SENIORITY = ['vice president', 'svp', 'evp', 'chief ', 'cfo', 'cto', 'ceo', 'coo']

all_new = []

for company, api_url in COMPANIES.items():
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        
        jobs = data.get('jobs', [])
        print(f'\n=== {company.upper()} === ({len(jobs)} total jobs)')
        
        matches = 0
        for j in jobs:
            title = j.get('title', '')
            loc = j.get('location', {}).get('name', '')
            tl = title.lower()
            ll = loc.lower()
            posted = j.get('updated_at', j.get('created_at', ''))
            
            # Skip unwanted roles
            if any(k in tl for k in SKIP_KEYWORDS):
                continue
            if any(k in tl for k in SKIP_SENIORITY):
                continue
            
            # Check title relevance
            title_match = any(k in tl for k in TITLE_KEYWORDS)
            # Check location relevance
            loc_match = any(k in ll for k in LOC_KEYWORDS)
            
            if title_match and loc_match:
                # Get URL
                url = j.get('absolute_url', '')
                
                all_new.append({
                    'company': company.title() if company != 'okx' else 'OKX',
                    'title': title,
                    'location': loc,
                    'url': url,
                    'posted': posted,
                    'source': 'greenhouse_api'
                })
                matches += 1
                print(f'  ✅ {title} | {loc}')
        
        print(f'  Matches: {matches}/{len(jobs)}')
        
    except Exception as e:
        print(f'Error scanning {company}: {e}')

print(f'\n=== SUMMARY: {len(all_new)} potential new jobs from Greenhouse ===')
# Save results
with open('/tmp/greenhouse_results.json', 'w') as f:
    json.dump(all_new, f, ensure_ascii=False, indent=2)
print('Saved to /tmp/greenhouse_results.json')
