import json
import urllib.request

# Scan Tencent careers
print("=== SCANNING TENCENT CAREERS ===")
tencent_url = "https://careers.tencent.com/en-us/search.html?keyword=strategy&location=Shenzhen"
# Try to scrape the careers page
try:
    req = urllib.request.Request(tencent_url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'})
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode('utf-8')
    print(f"Tencent page loaded: {len(html)} chars")
    
    # Look for job links and titles in the HTML
    import re
    # Find job URLs
    job_urls = re.findall(r'href="(/en-us/position/\d+)"', html)
    print(f"Found {len(job_urls)} job URLs")
    
    # Find job titles
    titles = re.findall(r'class="recruit-title[^"]*"[^>]*>([^<]+)<', html)
    print(f"Found {len(titles)} job titles")
    
    for url, title in zip(job_urls[:10], titles[:10]):
        print(f"  {title.strip()} | https://careers.tencent.com{url}")
        
except Exception as e:
    print(f"Error: {e}")

print("\n=== SCANNING 51JOB ===")
# 51job uses JavaScript rendering, harder to scrape
# Try their API or search page
try:
    search_url = "https://we.51job.com/api/job/search-pc?api_key=51job&keyword=产品经理&searchType=2&jobArea=040090&keywordType=2&function=&industryType=&salary=&workYear=&degree=&companyType=&companySize=&jobType=&issueDate=&sortType=0&pageNum=1&requestId=&pageSize=20&source=1&accountId=&contextId="
    req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=15)
    data = json.loads(resp.read())
    print(f"51job API response keys: {list(data.keys())}")
    if 'resultbody' in data:
        jobs = data['resultbody'].get('job', {}).get('items', [])
        print(f"51job: {len(jobs)} jobs found")
        for j in jobs[:10]:
            print(f"  {j.get('jobName', '')} | {j.get('companyName', '')} | {j.get('jobArea', '')} | {j.get('provideSalaryString', '')}")
except Exception as e:
    print(f"51job error: {e}")
