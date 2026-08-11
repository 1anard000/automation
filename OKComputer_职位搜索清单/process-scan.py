#!/usr/bin/env python3
"""Process scan results and add new jobs to database."""
import json
import urllib.request
from datetime import datetime
from hashlib import md5

# Target cities
TARGET_CITIES = ['shenzhen', 'hong kong', 'hk', 'guangzhou', 'shanghai', 'singapore',
                 'bangkok', 'taipei', 'tokyo', 'seoul', 'kuala lumpur', 'jakarta']

# Senior title patterns
SENIOR_PATTERNS = ['manager', 'lead', 'head of', 'director', 'principal',
                   'senior', 'gm', 'general manager', 'product']

# Exclude patterns
EXCLUDE = ['intern', 'junior', 'associate (non-senior)', 'analyst', 'assistant',
           'graduate', 'trainee', 'entry level', 'software engineer', 'data engineer',
           'devops', 'backend', 'frontend', 'full stack', 'ml engineer', 'sre',
           'designer', 'recruiter', 'art director', 'legal counsel', 'accountant',
           'controller', 'payroll', 'benefits', 'data scientist', 'compliance']

# Target keywords for role type
TARGET_KEYWORDS = ['product', 'strategy', 'bizops', 'business operations', 'growth',
                   'general manager', 'commercial', 'monetization', 'marketplace',
                   'platform', 'payments', 'fintech', 'cross-border', 'international',
                   'expansion', 'partnerships', 'business development', 'operations']

def is_target_city(loc):
    if not loc:
        return False
    loc_lower = loc.lower()
    return any(c in loc_lower for c in TARGET_CITIES)

def is_relevant_title(title):
    if not title:
        return False
    t = title.lower()
    # Skip excluded roles
    for ex in EXCLUDE:
        if ex in t:
            return False
    # Must match target keywords
    return any(kw in t for kw in TARGET_KEYWORDS)

def normalize_location(loc):
    if not loc:
        return 'Unknown'
    # Simplify location string
    if 'shenzhen' in loc.lower():
        return 'Shenzhen'
    elif 'hong kong' in loc.lower() or 'hk' in loc.lower():
        return 'Hong Kong'
    elif 'singapore' in loc.lower():
        return 'Singapore'
    elif 'shanghai' in loc.lower():
        return 'Shanghai'
    elif 'bangkok' in loc.lower():
        return 'Bangkok'
    elif 'taipei' in loc.lower():
        return 'Taipei'
    elif 'tokyo' in loc.lower():
        return 'Tokyo'
    elif 'seoul' in loc.lower():
        return 'Seoul'
    elif 'kuala lumpur' in loc.lower():
        return 'Kuala Lumpur'
    elif 'jakarta' in loc.lower():
        return 'Jakarta'
    elif 'guangzhou' in loc.lower():
        return 'Guangzhou'
    elif 'india' in loc.lower() or 'bangalore' in loc.lower() or 'bengaluru' in loc.lower() or 'mumbai' in loc.lower():
        return None  # Skip India for now
    elif 'australia' in loc.lower() or 'sydney' in loc.lower() or 'melbourne' in loc.lower():
        return None  # Skip Australia for now
    elif 'abu dhabi' in loc.lower() or 'uae' in loc.lower():
        return None  # Skip UAE for now
    return loc.split(',')[0].strip()

def create_job_id(company, title, location):
    """Create unique ID for dedup."""
    return md5(f"{company}:{title}:{location}".encode()).hexdigest()[:12]

# Load existing database
with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json') as f:
    existing_jobs = json.load(f)

# Create sets for dedup
existing_urls = {j.get('url', '') for j in existing_jobs}
existing_titles = {(j.get('company', ''), j.get('title', '')) for j in existing_jobs}

print(f"Loaded {len(existing_jobs)} existing jobs")

new_jobs = []

# Process Greenhouse scan results
BOARDS = ["adyen", "stripe", "okx", "anthropic", "bybit", "flexport", "xendit",
          "airbnb", "gitlab", "cloudflare", "coinbase", "figma", "block",
          "datadog", "elastic", "mercury", "spotify", "dropbox", "snap",
          "shopify", "rippling", "brex", "plaid", "wise", "revolut", "deel",
          "ramp", "scale", "notion", "vercel", "canva", "databricks",
          "marqeta", "retool", "nubank", "dlocal", "lalamove", "shopee",
          "grab", "gojek", "sea", "adyen"]

for slug in BOARDS:
    url = f"https://api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        continue

    if "jobs" not in data:
        continue

    for job in data["jobs"]:
        title = job.get("title", "")
        loc = job.get("location", {}).get("name", "")
        job_url = job.get("absolute_url", "")

        if not is_target_city(loc):
            continue
        if not is_relevant_title(title):
            continue
        if job_url in existing_urls:
            continue

        norm_loc = normalize_location(loc)
        if norm_loc is None:
            continue

        # Check if similar job already exists
        if (slug, title) in existing_titles:
            continue

        new_jobs.append({
            "company": slug.title(),
            "title": title,
            "location": norm_loc,
            "salary": "",
            "url": job_url,
            "source": "greenhouse_api",
            "scanned_date": datetime.now().strftime("%Y-%m-%d"),
            "quality_score": 70,
            "quality_tier": "B",
            "en_title": title,
            "english_friendly": True,
            "category": "product_management"
        })
        existing_urls.add(job_url)
        existing_titles.add((slug, title))

print(f"\nNEW JOBS FOUND: {len(new_jobs)}")

# Add to database
if new_jobs:
    existing_jobs.extend(new_jobs)
    with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json', 'w') as f:
        json.dump(existing_jobs, f, indent=2, ensure_ascii=False)
    print(f"Added {len(new_jobs)} new jobs to database")

# Print summary of new jobs
for j in new_jobs:
    print(f"  📌 {j['title']} @ {j['company']}")
    print(f"     📍 {j['location']} | 🔗 {j['url']}")
