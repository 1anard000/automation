#!/usr/bin/env python3
"""Try various career site APIs with proper headers."""
import json, urllib.request, urllib.parse, ssl, re

ssl._create_default_https_context = ssl._create_unverified_context

all_new = []

def try_api(name, url, headers=None, data=None, method='GET'):
    try:
        if headers is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                'Referer': 'https://careers.tencent.com/',
                'Origin': 'https://careers.tencent.com'
            }
        req = urllib.request.Request(url, headers=headers, data=data, method=method)
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            for enc in ['utf-8', 'gbk', 'latin-1']:
                try:
                    return raw.decode(enc)
                except:
                    continue
            return raw.decode('utf-8', errors='ignore')
    except Exception as e:
        return f"ERROR: {e}"

# === ByteDance API ===
print("=== ByteDance API ===")
# ByteDance uses an internal API
bd_url = 'https://jobs.bytedance.com/api/v1/search/position'
bd_data = json.dumps({
    'keyword': 'product manager',
    'limit': 30,
    'start': 0,
    'search_type': 2,
    'job_category_id_list': [],
    'city_code_list': ['410100']  # Shenzhen
}).encode('utf-8')
bd_headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Referer': 'https://jobs.bytedance.com/experienced/position'
}
result = try_api('ByteDance', bd_url, headers=bd_headers, data=bd_data, method='POST')
print(f"Response: {result[:500]}")

# === Try fetching 51job search page ===
print("\n=== 51job Search ===")
job51_url = 'https://we.51job.com/api/job/search-pc?api_key=51job&keyword=产品经理&searchType=2&jobArea=040090&salary=15001%2C99999&pageNum=1&pageSize=20'
result = try_api('51job', job51_url)
print(f"Response: {result[:500]}")

# === Try fetching Liepin API ===
print("\n=== Liepin API ===")
liepin_url = 'https://api-c.liepin.com/api/com.liepin.searchfront4c.pc-search-job?key=%E5%95%86%E4%B8%9A%E7%AD%96%E7%95%A5&dq=050090&curPage=0&pageSize=20'
liepin_headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.liepin.com/',
    'Origin': 'https://www.liepin.com'
}
result = try_api('Liepin', liepin_url, headers=liepin_headers)
print(f"Response: {result[:500]}")

# === Try fetching Shopee careers ===
print("\n=== Shopee Careers ===")
shopee_url = 'https://careers.shopee.com/api/v1/search?keyword=product+manager&limit=20&offset=0'
result = try_api('Shopee', shopee_url)
print(f"Response: {result[:500]}")

# === Try fetching OKX careers ===
print("\n=== OKX Careers ===")
okx_url = 'https://www.okx.com/careers/api/v1/jobs?keyword=product+manager&limit=20&offset=0'
result = try_api('OKX', okx_url)
print(f"Response: {result[:500]}")

# === Try fetching Grab careers ===
print("\n=== Grab Careers ===")
grab_url = 'https://grab.careers/ext/api/v1/search?keyword=product+manager&limit=20&offset=0'
result = try_api('Grab', grab_url)
print(f"Response: {result[:500]}")
