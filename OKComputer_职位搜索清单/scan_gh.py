#!/usr/bin/env python3
import json
import urllib.request
import ssl
from datetime import datetime

# Known valid Greenhouse company slugs to try
COMPANIES = [
    'flexport', 'affirm', 'stripe', 'airwallex', 'databricks',
    'figma', 'discord', 'spotify', 'airbnb', 'dropbox', 
    'rippling', 'deel', 'ramp', 'brex', 'plaid', 'mercury',
    'wise', 'revolut', 'scale', 'notion', 'vercel', 'canva',
    'shopify', 'coinbase', 'kraken', 'checkoutcom', 'marqeta',
    'retool', 'block', 'snap', 'lyft', 'databricks', 'rippling',
    'robinhood', 'sofi', 'n26', 'monzo', 'qonto', 'alan',
    'swile', 'qonto', 'zettle', 'izettle', 'sumup',
    'nubank', 'stori', 'dlocal', 'ebanx', 'pagseguro',
    'meli', 'mercadopago', 'shopee', 'grab', 'gojek',
    'traveloka', 'sea', 'razer', 'carousell', 'propertyguru',
    'lalamove', 'sensetime', 'megvii', 'bytedance', 'shein',
    'temu', 'tiktok', 'pinduoduo', 'meituan', 'didi',
    'xiaomi', 'oppo', 'vivo', 'netease', 'baidu',
    'douyin', 'kuaishou', 'xiaohongshu', 'zhihu', 'tencent',
    'suning', 'vipshop', 'meitu', 'lufax', 'zhongan',
    'iflytek', 'cambricon', 'jd', 'alibaba', 'antgroup',
    'wechatpay', 'lazada', 'foodpanda', 'deliveroo',
]

ASIA_KEYWORDS = ['singapore', 'hong kong', 'shenzhen', 'guangzhou', 'shanghai', 
                 'beijing', 'taipei', 'tokyo', 'seoul', 'bangkok', 'kuala lumpur',
                 'jakarta', 'manila', 'ho chi minh', 'hanoi', 'mumbai', 'delhi',
                 'hyderabad', 'bangalore', 'pune', 'chengdu', 'hangzhou', 'nanjing',
                 'wuhan', 'suzhou', 'xiamen', 'dalian', 'zhuhai', 'dongguan', 
                 'foshan', 'china', 'asia', 'apac', 'hk', ' sz ', ' global']

TARGET_KEYWORDS = ['product manager', 'senior product', 'staff product', 'lead product',
                   'strategy', 'bizops', 'business operations', 'growth', 'general manager',
                   'commercial', 'monetization', 'marketplace', 'platform', 'payments', 
                   'fintech', 'cross-border', 'international', 'expansion', 'partnerships',
                   'business development', 'product marketing', 'operations manager']

SKIP_KEYWORDS = ['intern', 'internship', 'junior', 'entry level', 'associate', 
                 'coordinator', 'vp ', 'vice president', 'chief ', 'c-level',
                 'head of', 'director of', 'sr. director', 'senior director',
                 'staff engineer', 'software engineer', 'data engineer',
                 'frontend', 'backend', 'full stack', 'devops', 'sre',
                 'designer', 'recruiter', 'recruiting', 'legal counsel',
                 'accountant', 'controller', 'payroll', 'benefits']

def fetch_jobs(company):
    url = f"https://boards-api.greenhouse.io/v1/jobs/{company}"
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data.get('jobs', [])
    except Exception as e:
        return []

def is_asia(loc):
    if not loc:
        return False
    loc_lower = loc.lower()
    return any(kw in loc_lower for kw in ASIA_KEYWORDS)

def is_target(title):
    if not title:
        return False
    title_lower = title.lower()
    if any(skip in title_lower for skip in SKIP_KEYWORDS):
        return False
    return any(kw in title_lower for kw in TARGET_KEYWORDS)

def main():
    print("Scanning Greenhouse APIs...")
    all_jobs = []
    scanned = 0
    errors = 0
    
    for company in COMPANIES:
        jobs = fetch_jobs(company)
        scanned += 1
        if jobs is None or (isinstance(jobs, list) and len(jobs) == 0):
            errors += 1
            continue
        for j in jobs:
            title = j.get('title', '')
            loc = j.get('location', {}).get('name', '')
            if is_asia(loc) and is_target(title):
                all_jobs.append({
                    'company': company,
                    'title': title,
                    'location': loc,
                    'url': j.get('absolute_url', ''),
                    'posted': j.get('updated_at', ''),
                    'source': 'greenhouse'
                })
        if scanned % 10 == 0:
            print(f"  Scanned {scanned} companies, found {len(all_jobs)} Asia PM/Strategy jobs so far...")
    
    print(f"\nScanned {scanned} companies, {errors} 404/errors")
    print(f"Found {len(all_jobs)} matching jobs")
    
    for j in all_jobs[:30]:
        print(f"  [{j['company']}] {j['title']} | {j['location']}")
        print(f"    {j['url']}")
    
    return all_jobs

if __name__ == '__main__':
    main()
