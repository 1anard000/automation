#!/usr/bin/env python3
"""Scan career sites via HTTP for new jobs."""
import json, urllib.request, re, ssl

ssl._create_default_https_context = ssl._create_unverified_context

def fetch_url(url, headers=None):
    """Fetch URL with error handling."""
    if headers is None:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode('utf-8', errors='ignore')

all_new = []

# === 1. Tencent Careers API ===
print("=== Tencent Careers ===")
try:
    # Tencent uses an API endpoint
    api_url = 'https://careers.tencent.com/tencentcareer/api/post/Query?timestamp=1&countryId=&cityId=&bgIds=&productId=&categoryId=&parentCategoryId=&attrId=&keyword=strategy&pageSize=20&start=0&language=en&area=chn'
    data = json.loads(fetch_url(api_url))
    posts = data.get('Data', {}).get('Posts', [])
    print(f"  Found {len(posts)} posts")
    for p in posts:
        title = p.get('RecruitPostName', '')
        loc = p.get('LocationName', '')
        dept = p.get('DepartmentName', '')
        post_id = p.get('PostId', '')
        url = f"https://careers.tencent.com/jobdesc.html?postId={post_id}"
        tl = title.lower()
        
        # Filter relevant roles
        if any(k in tl for k in ['product manager', 'strategy', 'growth', 'gm', 'head of', 'bizops', 'business operations', 'commercial', 'business development', 'cross-border', 'marketplace', 'fintech', 'product lead']):
            if any(k in loc.lower() for k in ['shenzhen', 'shanghai', 'guangzhou', 'hong kong', 'singapore', 'beijing']):
                # Skip director/VP level
                if not any(k in tl for k in ['director', 'vp ', 'vice president', 'svp', 'evp']):
                    all_new.append({
                        'company': 'Tencent',
                        'title': title,
                        'location': loc,
                        'url': url,
                        'source': 'tencent_careers',
                        'department': dept
                    })
                    print(f"  ✅ {title} | {loc}")
except Exception as e:
    print(f"  Error: {e}")

# === 2. ByteDance Careers API ===
print("\n=== ByteDance Careers ===")
try:
    # ByteDance has an API
    api_url = 'https://jobs.bytedance.com/api/v1/search/position?keyword=产品经理&limit=20&start=0&city=410100'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/json'
    }
    data = json.loads(fetch_url(api_url, headers))
    positions = data.get('data', {}).get('position_list', [])
    print(f"  Found {len(positions)} positions")
    for p in positions:
        title = p.get('name', '')
        loc = p.get('city_info', {}).get('name', '') if p.get('city_info') else ''
        post_id = p.get('id', '')
        url = f"https://jobs.bytedance.com/experienced/position/{post_id}/detail"
        tl = title.lower()
        
        if any(k in tl for k in ['product manager', 'strategy', 'growth', 'gm', 'head of', 'bizops', 'business operations', 'commercial', 'business development', 'cross-border', 'marketplace', 'fintech', 'product lead']):
            if any(k in loc.lower() for k in ['shenzhen', 'shanghai', 'guangzhou', 'hong kong', 'singapore', 'beijing', '深圳', '上海', '广州', '香港', '新加坡', '北京']):
                if not any(k in tl for k in ['director', 'vp ', 'vice president', 'svp', 'evp', '实习生', 'intern']):
                    all_new.append({
                        'company': 'ByteDance',
                        'title': title,
                        'location': loc,
                        'url': url,
                        'source': 'bytedance_careers'
                    })
                    print(f"  ✅ {title} | {loc}")
except Exception as e:
    print(f"  Error: {e}")

# === 3. Try 51job API ===
print("\n=== 51job ===")
try:
    # 51job has an API for search
    api_url = 'https://search.51job.com/list/040090,000000,0000,00,9,99,%25E4%25BA%25A7%25E5%2593%2581%25E7%25BB%258F%25E7%2590%2586,2,1.html'
    html = fetch_url(api_url)
    # Try to extract job listings from HTML
    # Pattern: job title, company, location, salary
    job_pattern = r'<span class="jname"[^>]*>(.*?)</span>.*?<span class="cname"[^>]*>(.*?)</span>'
    matches = re.findall(job_pattern, html, re.DOTALL)
    print(f"  Found {len(matches)} raw matches")
except Exception as e:
    print(f"  Error: {e}")

# === 4. Try Airwallex careers ===
print("\n=== Airwallex Careers ===")
try:
    api_url = 'https://www.airwallex.com/careers?location=shenzhen'
    html = fetch_url(api_url)
    # Look for job listings in HTML
    title_pattern = r'<h3[^>]*>(.*?)</h3>'
    titles = re.findall(title_pattern, html)
    print(f"  Found {len(titles)} potential titles in HTML")
except Exception as e:
    print(f"  Error: {e}")

print(f"\n=== TOTAL NEW JOBS FOUND: {len(all_new)} ===")
for j in all_new:
    print(f"  {j['company']} | {j['title']} | {j['location']}")

# Save results
with open('/tmp/careerscan_results.json', 'w') as f:
    json.dump(all_new, f, ensure_ascii=False, indent=2)
