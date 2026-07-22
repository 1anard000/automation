#!/usr/bin/env python3
import json
import urllib.request
import urllib.error
import ssl
from datetime import datetime, timezone

# Greenhouse companies to scan
GREENHOUSE_COMPANIES = {
    'okx': 'OKX',
    'stripe': 'Stripe', 
    'airwallex': 'Airwallex',
    'flexport': 'Flexport',
    'coupang': 'Coupang',
    'databricks': 'Databricks',
    'cloudflare': 'Cloudflare',
    'figma': 'Figma',
    'discord': 'Discord',
    'spotify': 'Spotify',
    'airbnb': 'Airbnb',
    'dropbox': 'Dropbox',
    'snap': 'Snap',
    'block': 'Block/Square',
    'rippling': 'Rippling',
    'deel': 'Deel',
    'ramp': 'Ramp',
    'brex': 'Brex',
    'mercury': 'Mercury',
    'wise': 'Wise',
    'n26': 'N26',
    'revolut': 'Revolut',
    'scale': 'Scale AI',
    'anthropic': 'Anthropic',
    'openai': 'OpenAI',
    'retool': 'Retool',
    'vercel': 'Vercel',
    'linear': 'Linear',
    'notion': 'Notion',
    'plaid': 'Plaid',
    'affirm': 'Affirm',
    'klarna': 'Klarna',
    'shopify': 'Shopify',
    'coinbase': 'Coinbase',
    'kraken': 'Kraken',
    'circle': 'Circle',
    'paypal': 'PayPal',
    'adyen': 'Adyen',
    'checkout.com': 'Checkout.com',
    'marqeta': 'Marqeta',
    'galileo': 'Galileo',
    'airtable': 'Airtable',
    'canva': 'Canva',
    'bytedance': 'ByteDance',
    'shein': 'SHEIN',
    'temu': 'Temu',
    'alibaba': 'Alibaba',
    'jd': 'JD.com',
    'pinduoduo': 'Pinduoduo',
    'meituan': 'Meituan',
    'didi': 'DiDi',
    'xiaomi': 'Xiaomi',
    'huawei': 'Huawei',
    'oppo': 'OPPO',
    'vivo': 'vivo',
    'tencent': 'Tencent',
    'netease': 'NetEase',
    'baidu': 'Baidu',
    'sogou': 'Sogou',
    'xiaohongshu': 'Xiaohongshu',
    'zhihu': 'Zhihu',
    'douyin': 'Douyin',
    'kuaishou': 'Kuaishou',
    'pinduoduo': 'Pinduoduo',
    'suning': 'Suning',
    'vipshop': 'Vipshop',
    'meitu': 'Meitu',
    'shopee': 'Shopee',
    'lazada': 'Lazada',
    'grab': 'Grab',
    'gojek': 'Gojek',
    'traveloka': 'Traveloka',
    'sea': 'Sea Limited',
    'razer': 'Razer',
    'coupang': 'Coupang',
    'carousell': 'Carousell',
    'propertyguru': 'PropertyGuru',
    'foodpanda': 'foodpanda',
    'deliveroo': 'Deliveroo',
    'lalamove': 'Lalamove',
    'wechatpay': 'WeChat Pay',
    'antgroup': 'Ant Group',
    'lufax': 'Lufax',
    'zhongAn': 'ZhongAn',
    'sensetime': 'SenseTime',
    'megvii': 'Megvii',
    'cambricon': 'Cambricon',
    'iflytek': 'iFlytek',
    '商汤': 'SenseTime',
    '旷视': 'Megvii',
    '寒武纪': 'Cambricon',
    '科大讯飞': 'iFlytek',
    '商汤科技': 'SenseTime',
    '旷视科技': 'Megvii',
    '寒武纪科技': 'Cambricon',
    '科大讯飞科技': 'iFlytek',
}

# Location filters for Asia
ASIA_KEYWORDS = ['singapore', 'hong kong', 'shenzhen', 'guangzhou', 'shanghai', 'beijing', 'taipei', 'tokyo', 'seoul', 'bangkok', 'kuala lumpur', 'jakarta', 'manila', 'ho chi minh', 'hanoi', 'mumbai', 'delhi', 'hyderabad', 'bangalore', 'pune', 'chengdu', 'hangzhou', 'nanjing', 'wuhan', 'suzhou', 'xiamen', 'dalian', 'zhuhai', 'dongguan', 'foshan', 'china', 'asia', 'apac', 'hk', 'sz']

# Keywords for target roles
TARGET_KEYWORDS = ['product manager', 'senior product', 'staff product', 'lead product', 'product lead', 
                   'strategy', 'bizops', 'business operations', 'growth', 'general manager',
                   'commercial', 'monetization', 'marketplace', 'platform', 'payments', 'fintech',
                   'cross-border', 'international', 'expansion', 'partnerships', 'business development']

# Skip keywords
SKIP_KEYWORDS = ['intern', 'internship', 'junior', 'entry level', 'associate', 'coordinator',
                 'vp ', 'vice president', 'chief ', 'c-level', 'head of', 'director of']

def is_asia_location(loc):
    if not loc:
        return False
    loc_lower = loc.lower()
    return any(kw in loc_lower for kw in ASIA_KEYWORDS)

def is_target_role(title):
    if not title:
        return False
    title_lower = title.lower()
    if any(skip in title_lower for skip in SKIP_KEYWORDS):
        return False
    return any(kw in title_lower for kw in TARGET_KEYWORDS)

def fetch_greenhouse_jobs(company_slug, company_name):
    url = f"https://boards-api.greenhouse.io/v1/jobs/{company_slug}?content=true"
    jobs = []
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for j in data.get('jobs', []):
                title = j.get('title', '')
                loc = j.get('location', {}).get('name', '')
                updated = j.get('updated_at', '')
                url_job = j.get('absolute_url', '')
                
                # Filter by location (Asia)
                if is_asia_location(loc) or not loc:  # Include if no location specified
                    # Filter by target role
                    if is_target_role(title):
                        jobs.append({
                            'company': company_name,
                            'title': title,
                            'location': loc,
                            'url': url_job,
                            'posted_date': updated,
                            'source': 'greenhouse_api',
                            'role_type': 'greenhouse'
                        })
    except Exception as e:
        print(f"  Error fetching {company_slug}: {e}")
    return jobs

def main():
    print("Starting Greenhouse API scan...")
    all_new_jobs = []
    
    # Load existing jobs
    try:
        with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json', 'r') as f:
            existing_jobs = json.load(f)
        existing_urls = {j.get('url', '') for j in existing_jobs}
        print(f"Loaded {len(existing_jobs)} existing jobs")
    except Exception as e:
        print(f"Error loading existing jobs: {e}")
        existing_jobs = []
        existing_urls = set()
    
    # Scan Greenhouse companies
    for slug, name in GREENHOUSE_COMPANIES.items():
        print(f"\nScanning {name}...")
        jobs = fetch_greenhouse_jobs(slug, name)
        new_count = 0
        for job in jobs:
            if job['url'] not in existing_urls:
                existing_jobs.append(job)
                existing_urls.add(job['url'])
                all_new_jobs.append(job)
                new_count += 1
        if new_count > 0:
            print(f"  Found {new_count} new jobs")
        else:
            print(f"  No new jobs")
    
    # Save updated jobs
    with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json', 'w') as f:
        json.dump(existing_jobs, f, indent=2, ensure_ascii=False)
    
    print(f"\nTotal new jobs found: {len(all_new_jobs)}")
    
    # Print summary of new jobs
    if all_new_jobs:
        print("\nNew Jobs:")
        for job in all_new_jobs[:20]:  # Limit to 20 for output
            print(f"  {job['company']} - {job['title']} @ {job['location']}")
            print(f"    URL: {job['url']}")
    
    return all_new_jobs

if __name__ == '__main__':
    main()
