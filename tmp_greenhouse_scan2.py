#!/usr/bin/env python3
"""Scan Greenhouse boards for relevant jobs - with correct API format."""
import json
import urllib.request
import sys

# Try different board slug formats
COMPANIES = [
    ('okx', 'OKX'),
    ('okx-labs', 'OKX Labs'),
    ('stripe', 'Stripe'),
    ('airwallex', 'Airwallex'),
    ('agoda', 'Agoda'),
    ('coupang', 'Coupang'),
    ('lazada', 'Lazada'),
    ('shopee', 'Shopee'),
    ('grab', 'Grab'),
    ('bytedance', 'ByteDance'),
    ('tencent', 'Tencent'),
    ('alibaba', 'Alibaba'),
    ('meituan', 'Meituan'),
    ('jd', 'JD'),
    ('xiaomi', 'Xiaomi'),
    ('huawei', 'Huawei'),
]

KEYWORDS = ['product', 'strategy', 'growth', 'bizops', 'business development', 
            'partnerships', 'operations', 'general manager']

def try_fetch(slug):
    """Try to fetch from Greenhouse API."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=false"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get('jobs', [])
    except Exception as e:
        return None

def main():
    found_companies = []
    
    for slug, name in COMPANIES:
        jobs = try_fetch(slug)
        if jobs is not None:
            print(f"✅ {name} ({slug}): {len(jobs)} jobs")
            found_companies.append((slug, name, jobs))
        else:
            print(f"❌ {name} ({slug}): not found")
    
    print(f"\n=== Companies with Greenhouse boards: {len(found_companies)} ===")
    
    all_relevant = []
    for slug, name, jobs in found_companies:
        relevant = []
        for j in jobs:
            title = j.get('title', '').lower()
            if any(kw in title for kw in KEYWORDS):
                skip = ['director', 'vp ', 'vice president', 'managing director', 'chief', 'intern']
                if not any(s in title for s in skip):
                    relevant.append({
                        'company': name,
                        'title': j['title'],
                        'location': j.get('location', {}).get('name', 'Unknown'),
                        'url': f"https://job-boards.greenhouse.io/{slug}/jobs/{j['id']}",
                        'source': 'greenhouse'
                    })
        if relevant:
            print(f"\n{name} - {len(relevant)} relevant jobs:")
            for r in relevant[:5]:
                print(f"  - {r['title']} | {r['location']}")
            all_relevant.extend(relevant)
    
    print(f"\nTotal relevant: {len(all_relevant)}")
    
    with open('/Users/iancolrick/.openclaw/workspace/tmp_greenhouse_results.json', 'w') as f:
        json.dump(all_relevant, f, indent=2)

if __name__ == '__main__':
    main()
