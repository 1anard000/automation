#!/usr/bin/env python3
"""Try alternative API endpoints"""
import urllib.request
import urllib.error
import urllib.parse
import json
from datetime import datetime, timezone

existing_path = "/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json"
with open(existing_path) as f:
    existing_jobs = json.load(f)

existing_urls = set(j.get("url", "") for j in existing_jobs)
new_jobs = []

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# Try Tencent careers with different API format
print("=== Trying Tencent Careers API ===")
try:
    # Try the newer Tencent career API
    url = "https://careers.tencent.com/tencentcareer/api/post/Query?keyword=strategy&locationId=&categoryId=&pageIndex=1&pageSize=20&language=en&area=cn"
    req = urllib.request.Request(url, headers={
        **headers,
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    print(f"  Tencent response keys: {list(data.keys())[:10]}")
    print(f"  Tencent Data type: {type(data.get('Data'))}")
except Exception as e:
    print(f"  ⚠ Tencent: {e}")

# Try ByteDance with proper encoding
print("\n=== Trying ByteDance Careers API ===")
try:
    kw = urllib.parse.quote("产品经理")
    url = f"https://jobs.bytedance.com/api/v1/search/position?keyword={kw}&limit=20&offset=0&type=2"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    print(f"  ByteDance response keys: {list(data.keys())[:10]}")
except Exception as e:
    print(f"  ⚠ ByteDance: {e}")

# Try getting job data from web pages
print("\n=== Trying Tencent Careers HTML ===")
try:
    url = "https://careers.tencent.com/en-us/search.html?keyword=strategy&location=Shenzhen"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode()
    print(f"  Tencent page length: {len(html)} chars")
    # Look for job data in HTML
    if '"postId"' in html or '"PostId"' in html:
        print("  Found job IDs in HTML!")
except Exception as e:
    print(f"  ⚠ Tencent HTML: {e}")

print("\n=== Trying 51job web page ===")
try:
    url = "https://we.51job.com/pc/search?keyword=产品经理&searchType=2&jobArea=040090"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode()
    print(f"  51job page length: {len(html)} chars")
except Exception as e:
    print(f"  ⚠ 51job: {e}")

print("\nDone scanning alternative sources")
