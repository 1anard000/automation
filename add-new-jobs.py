#!/usr/bin/env python3
"""Add new jobs found in this scan to the database."""
import json
from datetime import datetime

# Load existing
with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json') as f:
    existing = json.load(f)

existing_urls = {j.get('url', '') for j in existing}

# New jobs from this scan (only the 4 from Greenhouse APIs)
new_jobs = [
    {
        "title": "Administration Expert, Global Strategic & Digitalization COE",
        "company": "OKX",
        "location": "Hong Kong, Hong Kong SAR",
        "salary": "Not listed",
        "url": "https://job-boards.greenhouse.io/okx/jobs/5949501003",
        "source": "greenhouse_api",
        "role_type": "Operations",
        "scanned_date": datetime.now().strftime('%Y-%m-%d'),
        "date": datetime.now().strftime('%Y-%m-%d'),
        "posted": datetime.now().strftime('%Y-%m-%d'),
        "english_friendly": True,
        "category": "operations",
        "quality_tier": "B",
        "grade": "B",
        "description": "Administration Expert in Global Strategic & Digitalization COE at OKX Hong Kong. Operations/admin focus."
    },
    {
        "title": "Account Executive - SEA, Platforms (Grower)",
        "company": "Stripe",
        "location": "Singapore",
        "salary": "Not listed",
        "url": "https://stripe.com/jobs/search?gh_jid=8108891",
        "source": "greenhouse_api",
        "role_type": "Sales",
        "scanned_date": datetime.now().strftime('%Y-%m-%d'),
        "date": datetime.now().strftime('%Y-%m-%d'),
        "posted": datetime.now().strftime('%Y-%m-%d'),
        "english_friendly": True,
        "category": "sales",
        "quality_tier": "B",
        "grade": "B",
        "description": "Account Executive for SEA Platforms at Stripe Singapore. Sales role, not PM."
    },
    {
        "title": "Program Manager, GTM Strategic Programs",
        "company": "Stripe",
        "location": "US-Remote",
        "salary": "Not listed",
        "url": "https://stripe.com/jobs/search?gh_jid=8042309",
        "source": "greenhouse_api",
        "role_type": "Strategy",
        "scanned_date": datetime.now().strftime('%Y-%m-%d'),
        "date": datetime.now().strftime('%Y-%m-%d'),
        "posted": datetime.now().strftime('%Y-%m-%d'),
        "english_friendly": True,
        "category": "strategy",
        "quality_tier": "B",
        "grade": "B",
        "description": "Program Manager for GTM Strategic Programs at Stripe. Strategy focus but US-Remote."
    },
    {
        "title": "Senior Manager, Real Estate Development and Investment",
        "company": "Coupang",
        "location": "Taipei, Taiwan",
        "salary": "Not listed",
        "url": "https://www.coupang.jobs/en/jobs/?gh_jid=8120875",
        "source": "greenhouse_api",
        "role_type": "Management",
        "scanned_date": datetime.now().strftime('%Y-%m-%d'),
        "date": datetime.now().strftime('%Y-%m-%d'),
        "posted": datetime.now().strftime('%Y-%m-%d'),
        "english_friendly": True,
        "category": "real_estate",
        "quality_tier": "B",
        "grade": "B",
        "description": "Senior Manager for Real Estate Development at Coupang Taipei. Not PM/Strategy focused."
    }
]

# Filter out already existing
added = 0
for job in new_jobs:
    if job['url'] not in existing_urls:
        existing.append(job)
        added += 1
        print(f"ADDED: {job['title']} @ {job['company']}")
    else:
        print(f"SKIP (exists): {job['title']} @ {job['company']}")

# Save
with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json', 'w') as f:
    json.dump(existing, f, indent=2, ensure_ascii=False)

print(f"\nAdded {added} new jobs. Total: {len(existing)}")
