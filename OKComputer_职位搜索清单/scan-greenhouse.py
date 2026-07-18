#!/usr/bin/env python3
"""Scan Greenhouse boards for APAC senior roles."""
import json, urllib.request, sys, re
from datetime import datetime

# Target companies with APAC presence
BOARDS = [
    "adyen", "stripe", "agoda", "airtable", "rippling", "brex",
    "ramp", "plaid", "checkout", "checkoutdotcom", "dLocal",
    "nuvei", "marqeta", "synapse", "galileo", "dianrong",
    "simplify", "lever", "ashbyhq", "rappi", "grab",
    "sea", "shopee", "bytedance", "bytedanc", "meituan",
    "pinduoduo", "alibaba", "tencent", "jd", "baidu",
    "didi", "xiaomi", "huawei", "temu", "shein",
    "xai", "anthropic", "openai", "deepmind", "moonshot",
    "minimax", "zhipu", "baichuan", "01.ai", "stepfun",
    "sensetime", "megvii", "cambricon",
    "revolut", "nubank", "wise", "monzo", "starling",
    "coinbase", "binance", "okx", "huobi", "bybit",
    "okx", "kraken", "bitstamp",
]

# APAC cities
APAC_CITIES = [
    "shenzhen", "shenzhen", "hong kong", "hongkong", "hk",
    "guangzhou", "guangzhou", "shanghai", "singapore",
    "bangkok", "taipei", "tokyo", "seoul", "jakarta",
    "kuala lumpur", "manila", "ho chi minh", "hcmc",
    "mumbai", "delhi", "bangalore", "bengaluru",
    "sydney", "melbourne"
]

# Senior title patterns
SENIOR_PATTERNS = [
    "director", "head of", "vp", "vice president", "chief",
    "senior product", "senior manager", "senior director",
    "principal", "general manager", "gm", "partner",
    "associate director", "senior advisor", "operating",
    "lead product", "product lead", "strategy lead",
    "expansion lead", "market lead", "business lead"
]

# Exclude patterns
EXCLUDE = [
    "intern", "junior", "associate (non-senior)", "analyst",
    "assistant", "graduate", "trainee", "entry level",
    "software engineer", "data engineer", "devops",
    "backend", "frontend", "full stack", "ml engineer",
    "sre", "qa", "tester", "support", "customer success",
    "account executive", "sales representative", "recruiter",
    "hr ", "human resources", "finance ", "legal "
]

def is_apac(loc):
    if not loc:
        return False
    loc_lower = loc.lower()
    return any(c in loc_lower for c in APAC_CITIES)

def is_senior(title):
    if not title:
        return False
    t = title.lower()
    # Must NOT be in exclude list
    for ex in EXCLUDE:
        if ex in t:
            return False
    # Must match senior pattern
    return any(p in t for p in SENIOR_PATTERNS)

def fetch_board(board):
    url = f"https://api.greenhouse.io/v1/boards/{board}/jobs"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return None

def scan():
    results = []
    scanned = 0
    for board in BOARDS:
        data = fetch_board(board)
        if not data or "jobs" not in data:
            continue
        scanned += 1
        for job in data["jobs"]:
            title = job.get("title", "")
            loc = job.get("location", {}).get("name", "")
            if is_apac(loc) and is_senior(title):
                results.append({
                    "title": title.strip(),
                    "company": job.get("company_name", board),
                    "location": loc,
                    "salary": "",
                    "url": job.get("absolute_url", ""),
                    "source": "greenhouse",
                    "role_type": categorize_role(title),
                    "description": f"Greenhouse posting. Location: {loc}.",
                    "grade": "",
                    "posted": job.get("first_published", "")[:10]
                })
    
    print(f"Scanned {scanned} boards, found {len(results)} APAC senior roles")
    
    # Write output
    with open("/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/scan-latest.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Print summary
    for r in results:
        print(f"  {r['title']} | {r['company']} | {r['location']}")
    
    return results

def categorize_role(title):
    t = title.lower()
    if any(w in t for w in ["product manager", "product lead", "head of product"]):
        return "product"
    elif any(w in t for w in ["strategy", "strategic", "strategy lead"]):
        return "strategy"
    elif any(w in t for w in ["expansion", "market entry", "cross-border"]):
        return "expansion"
    elif any(w in t for w in ["business development", "partnership", "bd"]):
        return "bd"
    elif any(w in t for w in ["general manager", "gm", "country manager", "head of"]):
        return "gm"
    elif any(w in t for w in ["operations", "ops", "operating"]):
        return "ops"
    else:
        return "other"

if __name__ == "__main__":
    scan()
