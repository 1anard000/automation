#!/usr/bin/env python3
"""Scan career sites - robust version with encoding fixes."""
import json, urllib.request, urllib.parse, re, ssl

ssl._create_default_https_context = ssl._create_unverified_context

def fetch_url(url, headers=None, data=None):
    if headers is None:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    req = urllib.request.Request(url, headers=headers, data=data)
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read()
        # Try multiple encodings
        for enc in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
            try:
                return raw.decode(enc)
            except:
                continue
        return raw.decode('utf-8', errors='ignore')

all_new = []

# === 1. Tencent Careers - try different API endpoint ===
print("=== Tencent Careers ===")
try:
    # Try the job search API
    api_url = 'https://careers.tencent.com/tencentcareer/api/post/Query?timestamp=1&countryId=&cityId=&bgIds=&productId=&categoryId=&parentCategoryId=&attrId=&keyword=product+manager&pageSize=30&start=0&language=en&area=chn'
    text = fetch_url(api_url)
    data = json.loads(text)
    posts = data.get('Data', {}).get('Posts', [])
    print(f"  Found {len(posts)} posts")
    for p in posts:
        title = p.get('RecruitPostName', '')
        loc = p.get('LocationName', '')
        post_id = p.get('PostId', '')
        url = f"https://careers.tencent.com/jobdesc.html?postId={post_id}"
        tl = title.lower()
        
        if any(k in tl for k in ['product manager', 'strategy', 'growth', 'head of', 'bizops', 'business operations', 'commercial', 'business development', 'cross-border', 'marketplace', 'fintech', 'product lead', 'product owner']):
            loc_l = loc.lower()
            if any(k in loc_l for k in ['shenzhen', 'shanghai', 'guangzhou', 'hong kong', 'singapore', 'beijing', '深圳', '上海', '广州', '香港', '新加坡', '北京']):
                if not any(k in tl for k in ['director', 'vp ', 'vice president', 'svp', 'evp', 'intern']):
                    all_new.append({
                        'company': 'Tencent',
                        'title': title,
                        'location': loc,
                        'url': url,
                        'source': 'tencent_careers'
                    })
                    print(f"  ✅ {title} | {loc}")
except Exception as e:
    print(f"  Error: {e}")

# === 2. ByteDance - use proper URL encoding ===
print("\n=== ByteDance Careers ===")
try:
    # ByteDance search API
    search_url = 'https://jobs.bytedance.com/api/v1/search/position'
    params = json.dumps({
        'keyword': 'product manager',
        'limit': 30,
        'start': 0,
        'city': ''
    }).encode('utf-8')
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/json'
    }
    text = fetch_url(search_url, headers=headers, data=params)
    data = json.loads(text)
    positions = data.get('data', {}).get('position_list', [])
    print(f"  Found {len(positions)} positions")
    for p in positions:
        title = p.get('name', '')
        loc = p.get('city_info', {}).get('name', '') if p.get('city_info') else ''
        post_id = p.get('id', '')
        url = f"https://jobs.bytedance.com/experienced/position/{post_id}/detail"
        tl = title.lower()
        
        if any(k in tl for k in ['product manager', 'strategy', 'growth', 'head of', 'bizops', 'business operations', 'commercial', 'business development', 'cross-border', 'marketplace', 'fintech', 'product lead']):
            loc_l = loc.lower()
            if any(k in loc_l for k in ['shenzhen', 'shanghai', 'guangzhou', 'hong kong', 'singapore', 'beijing', '深圳', '上海', '广州', '香港', '新加坡', '北京']):
                if not any(k in tl for k in ['director', 'vp ', 'vice president', 'svp', 'evp', 'intern']):
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

# === 3. Try fetching 51job via their API ===
print("\n=== 51job ===")
try:
    # 51job API search
    api_url = 'https://api.51job.com/job/search.php'
    params = urllib.parse.urlencode({
        'keyword': '产品经理',
        'jobArea': '040090',  # Shenzhen
        'salary': '15001,99999',
        'jobType': '0',
        'sortType': '0'
    })
    text = fetch_url(f"{api_url}?{params}")
    # Try to parse as JSON
    try:
        data = json.loads(text)
        print(f"  Got JSON response: {json.dumps(data)[:200]}")
    except:
        print(f"  Got HTML/text: {text[:300]}")
except Exception as e:
    print(f"  Error: {e}")

# === 4. Try fetching Liepin search results ===
print("\n=== Liepin ===")
try:
    api_url = 'https://www.liepin.com/zhaopin/?key=%E5%95%86%E4%B8%9A%E7%AD%96%E7%95%A5&dqs=050090'
    text = fetch_url(api_url)
    # Look for job cards in HTML
    # Pattern: job-title, company, location, salary
    title_pattern = r'class="job-title"[^>]*>(.*?)</a>'
    titles = re.findall(title_pattern, text)
    print(f"  Found {len(titles)} job titles")
    for t in titles[:5]:
        print(f"    {t}")
except Exception as e:
    print(f"  Error: {e}")

# === 5. Try Shopee/Lazada careers ===
print("\n=== Shopee/Lazada ===")
try:
    # Shopee careers API
    api_url = 'https://careers.shopee.com/api/v1/position?keyword=product+manager&limit=20&offset=0'
    text = fetch_url(api_url)
    data = json.loads(text)
    positions = data.get('data', {}).get('list', [])
    print(f"  Found {len(positions)} positions")
    for p in positions:
        title = p.get('name', '')
        loc = p.get('city', '')
        post_id = p.get('id', '')
        url = f"https://careers.shopee.com/position/{post_id}/detail"
        tl = title.lower()
        
        if any(k in tl for k in ['product manager', 'strategy', 'growth', 'head of', 'bizops', 'business operations', 'commercial', 'business development', 'cross-border', 'marketplace', 'fintech', 'product lead']):
            loc_l = loc.lower()
            if any(k in loc_l for k in ['shenzhen', 'shanghai', 'guangzhou', 'hong kong', 'singapore', 'beijing']):
                if not any(k in tl for k in ['director', 'vp ', 'vice president', 'svp', 'evp', 'intern']):
                    all_new.append({
                        'company': 'Shopee',
                        'title': title,
                        'location': loc,
                        'url': url,
                        'source': 'shopee_careers'
                    })
                    print(f"  ✅ {title} | {loc}")
except Exception as e:
    print(f"  Error: {e}")

print(f"\n=== TOTAL NEW JOBS FOUND: {len(all_new)} ===")
for j in all_new:
    print(f"  {j['company']} | {j['title']} | {j['location']}")

# Save results
with open('/tmp/careerscan_results.json', 'w') as f:
    json.dump(all_new, f, ensure_ascii=False, indent=2)
