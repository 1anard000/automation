#!/usr/bin/env python3
"""Debug 51job API response."""
import urllib.request, urllib.parse

url = "https://we.51job.com/api/job/search-pc?api_key=51job&keyword=" + urllib.parse.quote("产品经理") + "&searchType=2&jobArea=040090&page=1&pageSize=5&sortType=0"
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Referer': 'https://we.51job.com/',
    'Accept': 'application/json'
})
resp = urllib.request.urlopen(req, timeout=15)
print(f"Status: {resp.status}")
print(f"Headers: {dict(resp.headers)}")
raw = resp.read()
print(f"Body length: {len(raw)}")
print(f"Body preview: {raw[:500]}")
