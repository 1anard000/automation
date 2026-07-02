#!/usr/bin/env python3
"""Comprehensive job scanner - fetch from Greenhouse, Ashby, Lever boards and filter for APAC senior roles."""
import json
import os
import urllib.request
import re
import sys
from datetime import datetime, timedelta
import html

# ── Config ──────────────────────────────────────────────────────────────
APAC_LOCATIONS = [
    "singapore", "hong kong", "shenzhen", "guangzhou", "shanghai",
    "tokyo", "seoul", "bangkok", "jakarta", "kuala lumpur",
    "australia", "sydney", "melbourne", "apac", "asia",
    "china", "taipei", "vietnam", "philippines",
    # Also accept "remote" as potentially APAC-friendly
    "remote", "hybrid", "worldwide", "global", "anywhere",
]

SENIOR_TITLES = [
    "director", "vp ", "vice president", "head of", "senior",
    "lead ", "principal", "chief", "general manager", "gm ",
    "总监", "总经理", "资深", "专家", "head ",
]

EXCLUDE_TITLES = [
    "associate", "assistant", "junior", "graduate", "intern",
    "entry", "trainee", "analyst", "support", "specialist",
    "engineer", "developer", "designer", "researcher",
    "account executive", "sales representative", "sdr", "bdr",
]

PRODUCT_KEYWORDS = [
    "product manager", "product lead", "product director",
    "product strategy", "strategy", "operations", "biz ops",
    "business operations", "program manager", "programme manager",
    "business development", "partnerships", "expansion",
    "market entry", "growth", "cross-border", "international",
    "gtm", "go-to-market", "fintech", "platform", "api",
    "developer relations", "ai product", "ai strategy",
    "regulatory", "compliance", "legal", "policy",
    "general manager", "country manager", "regional",
]

# Greenhouse boards to scan
GH_BOARDS = [
    "stripe", "airbnb", "figma", "notion", "shopify", "doordash",
    "pinterest", "lyft", "brex", "chime", "affirm", "duolingo",
    "webflow", "vercel", "mercury", "checkr", "gitlab", "baidu",
    "plaid", "rippling", "discourse", "elastic", "twilio",
    "cloudflare", "datadog", "snowflake", "databricks",
    "coinbase", "block", "paypal", "adyen", "nubank",
    "grab", "sea", "shopee", "lazada",
]

def fetch_json(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return None

def is_apac(loc):
    loc_l = loc.lower()
    return any(kw in loc_l for kw in APAC_LOCATIONS)

def is_senior(title):
    t = title.lower()
    return any(kw in t for kw in SENIOR_TITLES)

def is_excluded(title):
    t = title.lower()
    return any(kw in t for kw in EXCLUDE_TITLES)

def is_product_strategy(title):
    t = title.lower()
    return any(kw in t for kw in PRODUCT_KEYWORDS)

def classify_role(title):
    t = title.lower()
    if any(kw in t for kw in ["product manager", "product lead", "product director"]):
        return "product"
    if any(kw in t for kw in ["strategy", "strategic"]):
        return "strategy"
    if any(kw in t for kw in ["operations", "biz ops", "business operations"]):
        return "ops"
    if any(kw in t for kw in ["business development", "partnerships", "bd "]):
        return "bd"
    if any(kw in t for kw in ["expansion", "market entry", "international", "cross-border", "regional"]):
        return "expansion"
    if any(kw in t for kw in ["general manager", "country manager", "gm "]):
        return "gm"
    if any(kw in t for kw in ["program manager", "programme manager"]):
        return "program"
    if any(kw in t for kw in ["gtm", "go-to-market"]):
        return "gtm"
    return "other"

def main():
    results = []
    
    for board in GH_BOARDS:
        data = fetch_json(f"https://api.greenhouse.io/v1/boards/{board}/jobs")
        if not data or "jobs" not in data:
            continue
        
        jobs = data["jobs"]
        board_matches = 0
        
        for job in jobs:
            title = job.get("title", "").strip()
            loc = job.get("location", {}).get("name", "").strip()
            url = job.get("absolute_url", "")
            published = job.get("first_published", "")
            
            # Skip old postings (>30 days)
            if published:
                try:
                    pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    if datetime.now(pub_dt.tzinfo) - pub_dt > timedelta(days=30):
                        continue
                except:
                    pass
            
            # Filter
            if not is_apac(loc):
                continue
            if is_excluded(title):
                continue
            if not is_senior(title):
                continue
            # Must be product/strategy/ops related OR senior enough to matter
            if not is_product_strategy(title):
                # Still keep if title is very senior (director/VP/head)
                title_l = title.lower()
                if not any(kw in title_l for kw in ["director", "vp", "vice president", "head of", "general manager", "chief"]):
                    continue
            
            board_matches += 1
            results.append({
                "title": title,
                "company": board.replace("_", " ").title(),
                "location": loc,
                "salary": "",
                "url": url,
                "source": "greenhouse",
                "role_type": classify_role(title),
                "description": f"Senior role at {board.title()} in {loc}.",
                "grade": "",
                "posted": published,
            })
        
        if board_matches > 0:
            print(f"  ✓ {board}: {board_matches} matches / {len(jobs)} total")
        else:
            print(f"  {board}: 0 matches / {len(jobs)} total")
    
    # Also check existing scan-latest.json and merge
    existing_path = "/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/scan-latest.json"
    try:
        with open(existing_path) as f:
            existing = json.load(f)
        # Add any existing jobs not already in results
        existing_keys = {(j["title"], j["company"]) for j in results}
        for j in existing:
            key = (j["title"], j["company"])
            if key not in existing_keys:
                results.append(j)
                existing_keys.add(key)
    except:
        pass
    
    # Save as scan-jobs.json (merge-jobs.py auto-picks up *-jobs.json)
    scan_jobs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan-jobs.json")
    with open(scan_jobs_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Also keep scan-latest.json for backward compat
    latest_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan-latest.json")
    with open(latest_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"Total: {len(results)} jobs found")
    print(f"{'='*60}")
    
    # Print summary
    by_type = {}
    for j in results:
        rt = j.get("role_type", "other")
        by_type[rt] = by_type.get(rt, 0) + 1
    
    print(f"\nBy role type:")
    for rt, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {rt}: {count}")
    
    print(f"\nTop picks:")
    for j in results[:10]:
        print(f"  [{j.get('role_type','?')}] {j['title']} — {j['company']} ({j['location']})")

if __name__ == "__main__":
    main()
