import json
import urllib.request

# Try different Greenhouse API formats
test_urls = [
    "https://boards-api.greenhouse.io/v1/boards/okx/jobs?content=true",
    "https://boards-api.greenhouse.io/v1/boards/stripe/jobs?content=true",
    "https://boards-api.greenhouse.io/v1/boards/airwallex/jobs?content=true",
    "https://boards-api.greenhouse.io/v1/boards/coupang/jobs?content=true",
    "https://boards-api.greenhouse.io/v1/boards/flexport/jobs?content=true",
]

for url in test_urls:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        jobs = data.get('jobs', [])
        print(f"OK: {url.split('/')[-2]} - {len(jobs)} jobs")
    except Exception as e:
        print(f"FAIL: {url.split('/')[-2]} - {e}")
