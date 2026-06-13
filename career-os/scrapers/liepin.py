#!/usr/bin/env python3
"""Scan Liepin for senior roles in target cities."""
import json
import urllib.request
import urllib.parse
import os
import datetime
import re

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
OUTPUT = os.path.join(WORKSPACE, "OKComputer_职位搜索清单/liepin-latest.json")

# Target search URLs
SEARCHES = [
    # Shenzhen
    "https://www.liepin.com/zhaopin/?key=product+manager&dqs=050090&curPage=0",
    # Shanghai
    "https://www.liepin.com/zhaopin/?key=product+manager&dqs=020090&curPage=0",
    # Guangzhou
    "https://www.liepin.com/zhaopin/?key=product+manager&dqs=050020&curPage=0",
    # Hong Kong
    "https://www.liepin.com/zhaopin/?key=product+manager&dqs=070020&curPage=0",
    # Cross-border
    "https://www.liepin.com/zhaopin/?key=cross+border+ecommerce&dqs=050090&curPage=0",
    # Strategy
    "https://www.liepin.com/zhaopin/?key=strategy+director&dqs=020090&curPage=0",
    # AI
    "https://www.liepin.com/zhaopin/?key=AI+product+manager&dqs=050090&curPage=0",
]

def scrape():
    """Attempt to scrape Liepin search results."""
    jobs = []
    
    # Note: Liepin has anti-scraping. We'll use web_search as fallback.
    # This script is called by the agent which uses web_search tool.
    
    for url in SEARCHES:
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            })
            resp = urllib.request.urlopen(req, timeout=10)
            html = resp.read().decode('utf-8', errors='ignore')
            
            # Extract job cards (simplified parsing)
            # Liepin uses React/Next.js, so we look for JSON data
            data_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html)
            if data_match:
                data = json.loads(data_match.group(1))
                # Extract jobs from the data structure
                job_list = data.get('job', {}).get('data', {}).get('list', [])
                for j in job_list:
                    jobs.append({
                        'title': j.get('job', {}).get('title', ''),
                        'company': j.get('comp', {}).get('compName', ''),
                        'location': j.get('job', {}).get('dq', ''),
                        'salary': j.get('job', {}).get('salary', ''),
                        'url': f"https://www.liepin.com/job/{j.get('job', {}).get('jobId', '')}",
                        'source': 'liepin',
                        'role_type': '',
                        'description': j.get('job', {}).get('requirement', '')[:200],
                    })
        except Exception as e:
            print(f"Liepin scrape error: {e}")
    
    if jobs:
        with open(OUTPUT, 'w') as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
        print(f"Liepin: {len(jobs)} jobs saved to {OUTPUT}")
    else:
        print("Liepin: No jobs extracted (anti-scraping likely)")
        # Save empty to indicate we tried
        with open(OUTPUT, 'w') as f:
            json.dump([], f)
    
    return jobs

if __name__ == "__main__":
    scrape()
