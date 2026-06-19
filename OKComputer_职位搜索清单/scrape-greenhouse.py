#!/usr/bin/env python3
"""Scrape Greenhouse API for product/strategy roles in APAC."""
import json
import urllib.request
import re
import sys
from datetime import datetime, timedelta

# Companies with Greenhouse boards to check
COMPANIES = [
    "stripe", "airbnb", "figma", "notion", "shopify", "doordash",
    "discord", "twitter", "snap", "pinterest", "lyft", "uber",
    "rippling", "brex", "ramp", "chime", "plaid", "affirm",
    "duolingo", "webflow", "linear", "vercel", "supabase",
    "mercury", "ramp", "ramp", "checkr", "zenefits", "lever",
    "ashby", "gitlab", "automattic", "zapier", "buffer",
    "grab", "gojek", "sea_group", "shopee", "lazada",
    "bytedance", "tiktok", "lark", "feishu", "dji",
    "xiaomi", "baidu", "alibaba", "tencent", "jd",
]

APAC_LOCATIONS = [
    "singapore", "hong kong", "shenzhen", "guangzhou", "shanghai",
    "tokyo", "seoul", "bangkok", "jakarta", "kuala lumpur",
    "australia", "sydney", "melbourne", "apac", "asia",
    "china", "remote", "hybrid",
]

SENIOR_KEYWORDS = [
    "director", "vp", "vice president", "head of", "senior",
    "lead", "principal", "chief", "general manager", "gm",
    "总监", "总经理", "资深", "专家",
]

PRODUCT_KEYWORDS = [
    "product manager", "product lead", "product director",
    "product strategy", "strategy", "operations", "biz ops",
    "program manager", "programme manager", "business development",
    "partnerships", "expansion", "market entry", "growth",
    "cross-border", "international", "gtm", "go-to-market",
    "fintech", "platform", "api", "developer relations",
    "ai product", "ai strategy", "ai ops",
]

def fetch_greenhouse(board, content=False):
    """Fetch jobs from Greenhouse API."""
    url = f"https://api.greenhouse.io/v1/boards/{board}/jobs"
    if content:
        url += "?content=true"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  Error fetching {board}: {e}")
        return None


def is_apac(location):
    """Check if location is APAC-friendly."""
    loc_lower = location.lower()
    return any(kw in loc_lower for kw in APAC_LOCATIONS)


def is_senior(title):
    """Check if title indicates senior+ level."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in SENIOR_KEYWORDS)


def is_product_strategy(title):
    """Check if role is product/strategy related."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in PRODUCT_KEYWORDS)


def main():
    results = []
    checked = 0
    matched = 0

    for company in COMPANIES:
        checked += 1
        data = fetch_greenhouse(company)
        if not data or "jobs" not in data:
            continue

        jobs = data["jobs"]
        print(f"  {company}: {len(jobs)} total jobs")

        for job in jobs:
            title = job.get("title", "")
            location = job.get("location", {}).get("name", "")
            url = job.get("absolute_url", "")

            if not is_apac(location):
                continue
            if not is_senior(title):
                continue
            if not is_product_strategy(title):
                continue

            # Check posting date
            published = job.get("first_published", "")
            if published:
                try:
                    pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    if datetime.now(pub_date.tzinfo) - pub_date > timedelta(days=30):
                        continue  # Skip old postings
                except:
                    pass

            matched += 1
            results.append({
                "title": title.strip(),
                "company": company.replace("_", " ").title(),
                "location": location.strip(),
                "salary": "",
                "url": url,
                "source": "greenhouse",
                "role_type": "unknown",
                "description": f"Senior role at {company.title()} in {location}. Posted via Greenhouse.",
                "grade": "",
                "posted": published,
            })

        if checked % 10 == 0:
            print(f"  Progress: checked {checked}/{len(COMPANIES)}")

    print(f"\nChecked {checked} companies, found {matched} matching jobs")
    
    # Save results
    with open("/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/scan-latest.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(results)} jobs to scan-latest.json")

if __name__ == "__main__":
    main()
