#!/usr/bin/env python3
"""Parse Tencent API response."""
import json, urllib.request, ssl

ssl._create_default_https_context = ssl._create_unverified_context

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json'
}

# Try strategy keyword
url = 'https://careers.tencent.com/tencentcareer/api/post/Query?timestamp=1&keyword=strategy&pageSize=20&start=0&language=en'
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read())
    print(json.dumps(data, indent=2)[:2000])
