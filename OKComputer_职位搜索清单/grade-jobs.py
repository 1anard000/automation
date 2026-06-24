#!/usr/bin/env python3
"""Grade ungraded jobs based on role relevance, seniority, company, and location."""
import json

SENIOR_KEYWORDS = ['vp', 'vice president', 'director', 'head of', 'principal', 'chief', 'c-level', 'cxo']
MID_KEYWORDS = ['senior', 'lead', 'staff', 'principal', 'distinguished']
ENTRY_KEYWORDS = ['associate', 'junior', 'intern', 'assistant', 'coordinator']

# Top-tier companies for PM/fintech
TOP_COMPANIES = {
    'anthropic', 'openai', 'google', 'meta', 'bytedance', 'tiktok', 'alibaba',
    'tencent', 'airbnb', 'stripe', 'coinbase', 'binance', 'okx', 'huobi',
    'grab', 'shopee', 'lazada', 'gojek', 'sea group', 'sea limited',
    'databricks', 'snowflake', 'figma', 'notion', 'vercel', 'supabase',
    'toptal', 'airwallex', 'xendit', 'grab', 'revolut', 'n26', 'monzo',
    'plaid', 'ramp', 'brex', 'chime', 'nubank', 'mercado pago',
    'agoda', 'booking', 'expedia', 'klook', 'trip.com',
    'bytedance', 'samsung', 'lg', 'sony',
}

# Preferred locations
TIER1_LOCATIONS = {'singapore', 'hong kong', 'remote', 'shanghai', 'beijing', 'shenzhen'}
TIER2_LOCATIONS = {'tokyo', 'seoul', 'taipei', 'bangkok', 'jakarta', 'kuala lumpur', 'manila'}

def classify_role(title):
    t = title.lower()
    # PM-specific roles
    if any(k in t for k in ['product manager', 'product director', 'product lead', 'product owner', 'head of product']):
        return 'pm'
    if any(k in t for k in ['product strategy', 'product operations', 'product analyst']):
        return 'pm'
    # Strategy/ops roles that are PM-adjacent
    if any(k in t for k in ['strategy', 'operations', 'gtm', 'go-to-market']):
        return 'adjacent'
    # Engineering/tech
    if any(k in t for k in ['engineer', 'developer', 'architect', 'sre', 'devops']):
        return 'tech'
    # Design
    if any(k in t for k in ['designer', 'design lead', 'ux', 'ui']):
        return 'design'
    # Marketing/sales
    if any(k in t for k in ['marketing', 'sales', 'account executive', 'business development', 'partnerships']):
        return 'business'
    # Finance
    if any(k in t for k in ['finance', 'accounting', 'financial', 'controller']):
        return 'finance'
    # Compliance/legal
    if any(k in t for k in ['compliance', 'legal', 'regulatory', 'risk']):
        return 'compliance'
    return 'other'

def get_seniority(title):
    t = title.lower()
    if any(k in t for k in SENIOR_KEYWORDS):
        return 'senior'
    if any(k in t for k in MID_KEYWORDS):
        return 'mid'
    if any(k in t for k in ENTRY_KEYWORDS):
        return 'entry'
    return 'mid'  # default

def grade_job(j):
    title = j.get('title', '')
    company = j.get('company', '').lower()
    location = j.get('location', '').lower()
    
    role = classify_role(title)
    seniority = get_seniority(title)
    
    # Base grade
    if role == 'pm':
        base = 'A-2'
    elif role == 'adjacent':
        base = 'B'
    elif role in ('tech', 'design'):
        base = 'C'
    else:
        base = 'C'
    
    # Seniority modifier
    if seniority == 'senior':
        if base == 'A-2':
            base = 'A-1'
        elif base == 'B':
            base = 'A-2'
    elif seniority == 'entry':
        if base == 'A-2':
            base = 'B'
        elif base == 'A-1':
            base = 'A-2'
    
    # Company boost
    if company in TOP_COMPANIES:
        if base == 'A-2':
            base = 'A-1'
        elif base == 'B':
            base = 'A-2'
    
    # Location modifier
    if any(location.startswith(t) for t in TIER1_LOCATIONS):
        pass  # no change, already good
    elif any(location.startswith(t) for t in TIER2_LOCATIONS):
        pass  # acceptable
    elif location and 'remote' in location:
        if base in ('A-2', 'B'):
            # Remote is good for accessibility
            pass
    
    # Non-PM roles that are VP/Director -> still relevant if at top company
    if role not in ('pm', 'adjacent') and seniority == 'senior':
        if company in TOP_COMPANIES:
            base = 'B'
        else:
            base = 'C'
    
    return base

def main():
    with open('jobs-all.json') as f:
        jobs = json.load(f)
    
    graded_count = 0
    for j in jobs:
        if not j.get('grade'):
            j['grade'] = grade_job(j)
            graded_count += 1
    
    with open('jobs-all.json', 'w') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=1)
    
    # Show new distribution
    from collections import Counter
    grades = Counter(j.get('grade', '?') for j in jobs)
    print(f'Graded {graded_count} jobs')
    print(f'Grade distribution: {dict(sorted(grades.items()))}')

if __name__ == '__main__':
    main()
