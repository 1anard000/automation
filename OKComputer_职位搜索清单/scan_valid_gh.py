#!/usr/bin/env python3
import json
import urllib.request
import ssl
from datetime import datetime

ASIA_KEYWORDS = ['singapore', 'hong kong', 'shenzhen', 'guangzhou', 'shanghai', 
                 'beijing', 'taipei', 'tokyo', 'seoul', 'bangkok', 'kuala lumpur',
                 'jakarta', 'manila', 'ho chi minh', 'hanoi', 'mumbai', 'delhi',
                 'hyderabad', 'bangalore', 'pune', 'chengdu', 'hangzhou', 'nanjing',
                 'wuhan', 'suzhou', 'xiamen', 'dalian', 'zhuhai', 'dongguan', 
                 'foshan', 'china', 'asia', 'apac', ' global', 'remote']

TARGET_KEYWORDS = ['product manager', 'senior product', 'staff product', 'lead product',
                   'product lead', 'product director', 'strategy', 'bizops', 'business operations', 
                   'growth', 'general manager', 'commercial', 'monetization', 'marketplace', 
                   'platform', 'payments', 'fintech', 'cross-border', 'international', 
                   'expansion', 'partnerships', 'business development', 'product marketing', 
                   'operations manager', 'head of product']

SKIP_KEYWORDS = ['intern', 'internship', 'junior', 'entry level', 'associate', 
                 'coordinator', 'vp ', 'vice president', 'chief ', 'c-level',
                 'staff engineer', 'software engineer', 'data engineer',
                 'frontend', 'backend', 'full stack', 'devops', 'sre',
                 'designer', 'recruiter', 'recruiting', 'legal counsel',
                 'accountant', 'controller', 'payroll', 'benefits', 
                 'data scientist', 'ml engineer', 'security engineer',
                 'sales engineer', 'solutions architect', 'customer success',
                 'customer support', 'technical support']

VALID_SLUGS = ['adyen', 'affirm', 'agoda', 'airbnb', 'anthropic', 'bybit', 'chime', 
               'cloudflare', 'coinbase', 'coupang', 'figma', 'flexport', 'gitlab', 
               'mercury', 'newrelic', 'okx', 'reddit', 'stripe', 'tripadvisor', 
               'twilio', 'vercel', 'xendit', 'canva', 'notion', 'rippling',
               'brex', 'plaid', 'wise', 'revolut', 'deel', 'ramp', 'scale',
               'spotify', 'dropbox', 'snap', 'block', 'shopify', 'checkoutcom',
               'databricks', 'marqeta', 'retool', 'nubank', 'dlocal',
               'lalamove', 'shopee', 'grab', 'gojek', 'sea']

def fetch_jobs(slug):
    url = f"https://boards-api.greenhouse.io/v1/jobs/{slug}"
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
            return json.loads(resp.read().decode('utf-8')).get('jobs', [])
    except Exception as e:
        return []

def is_asia(loc):
    if not loc:
        return False
    return any(kw in loc.lower() for kw in ASIA_KEYWORDS)

def is_target(title):
    if not title:
        return False
    t = title.lower()
    if any(skip in t for skip in SKIP_KEYWORDS):
        return False
    return any(kw in t for kw in TARGET_KEYWORDS)

# Load existing URLs
with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json') as f:
    existing = json.load(f)
existing_urls = {j.get('url', '') for j in existing}

new_jobs = []
for slug in VALID_SLUGS:
    jobs = fetch_jobs(slug)
    for j in jobs:
        title = j.get('title', '')
        loc = j.get('location', {}).get('name', '')
        url = j.get('absolute_url', '')
        if url not in existing_urls and is_asia(loc) and is_target(title):
            new_jobs.append({
                'company': slug,
                'title': title,
                'location': loc,
                'url': url,
                'posted': j.get('updated_at', ''),
                'source': 'greenhouse_api'
            })

print(f"NEW JOBS FOUND: {len(new_jobs)}")
for j in new_jobs:
    print(f"  [{j['company'].upper()}] {j['title']} | {j['location']}")
    print(f"    {j['url']}")
