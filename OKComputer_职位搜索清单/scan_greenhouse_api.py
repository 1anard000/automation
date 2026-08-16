#!/usr/bin/env python3
"""Scan Greenhouse boards API for new jobs from target companies."""
import json
import urllib.request
import sys
from datetime import datetime

COMPANIES = {
    'okx': 'OKX',
    'stripe': 'Stripe',
    'coupang': 'Coupang',
    'bybit': 'Bybit',
    'flexport': 'Flexport',
    'airbnb': 'Airbnb',
    'pinterest': 'Pinterest',
}

def fetch_greenhouse(slug):
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"Error fetching {slug}: {e}", file=sys.stderr)
        return None

def main():
    today = datetime.now().strftime('%Y-%m-%d')
    all_new = []
    
    for slug, company_name in COMPANIES.items():
        data = fetch_greenhouse(slug)
        if not data:
            continue
        jobs = data.get('jobs', [])
        print(f"{company_name}: {len(jobs)} total jobs")
        
        for j in jobs:
            title = j.get('title', '')
            loc = j.get('location', {}).get('name', '')
            url = j.get('absolute_url', '')
            updated = j.get('updated_at', '')[:10]
            content = j.get('content', '')[:500] if j.get('content') else ''
            gh_id = j.get('id', '')
            
            all_new.append({
                'company': company_name,
                'title': title,
                'location': loc,
                'url': url,
                'greenhouse_id': gh_id,
                'posted': updated,
                'source': 'greenhouse_api',
                'scanned_date': today,
                'desc_preview': content
            })
    
    # Save raw scan
    output_path = '/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/greenhouse-scan-latest.json'
    with open(output_path, 'w') as f:
        json.dump(all_new, f, indent=2, ensure_ascii=False)
    
    print(f"\nTotal jobs scanned: {len(all_new)}")
    print(f"Saved to: {output_path}")

if __name__ == '__main__':
    main()
