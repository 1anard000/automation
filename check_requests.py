#!/usr/bin/env python3
"""Check if requests is available and try career site APIs."""
try:
    import requests
    print("requests is available")
    HAS_REQUESTS = True
except ImportError:
    print("requests not available")
    HAS_REQUESTS = False

import json, urllib.request, ssl

ssl._create_default_https_context = ssl._create_unverified_context

if HAS_REQUESTS:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    
    # Try ByteDance with requests
    print("\n=== ByteDance with requests ===")
    try:
        resp = session.get('https://jobs.bytedance.com/experienced/position?keywords=product%20manager&location=Shenzhen', timeout=15)
        print(f"Status: {resp.status_code}")
        # Check if it's a SPA that needs JS
        if '<div id="app">' in resp.text or 'window.__INITIAL_STATE__' in resp.text:
            print("  SPA detected - needs JavaScript rendering")
        # Try to find job data in page source
        import re
        job_matches = re.findall(r'"positionName"\s*:\s*"([^"]+)"', resp.text)
        print(f"  Found {len(job_matches)} position names in HTML")
        for m in job_matches[:5]:
            print(f"    {m}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Try Tencent with requests
    print("\n=== Tencent with requests ===")
    try:
        resp = session.get('https://careers.tencent.com/search.html?keyword=strategy&location=Shenzhen', timeout=15)
        print(f"Status: {resp.status_code}")
        if '<div id="app">' in resp.text or 'window.__INITIAL_STATE__' in resp.text:
            print("  SPA detected - needs JavaScript rendering")
        job_matches = re.findall(r'"RecruitPostName"\s*:\s*"([^"]+)"', resp.text)
        print(f"  Found {len(job_matches)} position names in HTML")
        for m in job_matches[:5]:
            print(f"    {m}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Try 51job with requests
    print("\n=== 51job with requests ===")
    try:
        resp = session.get('https://we.51job.com/pc/search?keyword=产品经理&searchType=2&jobArea=040090', timeout=15)
        print(f"Status: {resp.status_code}")
        if '<div id="app">' in resp.text:
            print("  SPA detected - needs JavaScript rendering")
        # Try to find job data
        job_matches = re.findall(r'"jobName"\s*:\s*"([^"]+)"', resp.text)
        print(f"  Found {len(job_matches)} job names in HTML")
        for m in job_matches[:5]:
            print(f"    {m}")
    except Exception as e:
        print(f"  Error: {e}")
else:
    print("\nCannot test with requests - not available")
    print("All career sites appear to require JavaScript rendering")
    print("Consider using a headless browser tool for future scans")
