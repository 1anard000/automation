#!/usr/bin/env python3
"""
Post-filter agent-discovered-jobs.json to match the user's exact target profile:
- Locations: Shenzhen, Hong Kong, Guangzhou, Shanghai, Singapore, APAC/Greater China/Southeast Asia regional
- Exclude Remote-USA/Remote-EMEA roles
- Exclude non-target functional roles (finance, accounting, HR, sales, etc.)
- Exclude Amazon
- Exclude overly senior titles (Director/VP/Chief/Head of) per 9-yr profile
- Keep only target role types: PM, Strategy/Ops, Growth, GM, Program/Project Management
"""
import json
import os
import re
from collections import Counter

AGENT_PATH = "/Users/iancolrick/.openclaw/workspace/career-os/scrapers/agent-discovered-jobs.json"

TARGET_LOCATIONS = [
    "shenzhen", "hong kong", "hongkong", "guangzhou", "shanghai", "singapore",
    "apac", "asia pacific", "asia-pacific", "southeast asia", "south-east asia",
    "greater china",
    "seoul", "tokyo", "bangkok", "kuala lumpur", "taipei", "jakarta", "manila",
    "sydney", "melbourne", "auckland"
]

EXCLUDED_FUNCTIONAL = [
    "finance", "accountant", "accounting", "fp&a", "financial", "tax", "audit",
    "payroll", "treasury", "controller", "hr ", "human resources", "people ",
    "talent ", "recruiter", "recruiting", "sales ", "account executive",
    "account manager", "business development", "bd ", "marketing ", "content ",
    "copywriter", "translator", "localisation", "localization", "legal ",
    "counsel", "compliance", "risk ", "operations manager", "customer success",
    "support specialist", "coordinator", "analyst", "data scientist",
    "engineer", "engineering", "developer", "designer", "ux ", "qa ",
    "devops", "sre ", "security ", "it manager", "data engineer", "machine learning",
    "ml ", "ai researcher", "research scientist", "scientist"
]

EXCLUDED_SENIOR = [
    "vp", "vice president", "svp", "evp", "chief", "president",
    "cfo", "cto", "coo", "ceo", "head of", "director"
]

AMAZON_RE = re.compile(r"\bamazon\b", re.IGNORECASE)


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_target_location(loc):
    if not loc:
        return False
    l = loc.lower()
    # Reject Remote-USA/EMEA/UK-only roles
    if "remote" in l:
        us_emea_indicators = ["usa", "us", "emea", "europe", "uk", "united kingdom", "america",
                              "san francisco", "seattle", "new york", "california", "poland",
                              "bangalore", "india"]
        if any(x in l for x in us_emea_indicators):
            return False
        # Accept if it's truly global/APAC remote (no specific non-target geo)
        return True
    for kw in TARGET_LOCATIONS:
        if kw.lower() in l:
            return True
    return False


def is_target_role(title):
    t = title.lower()
    # Must be one of the target role families
    pm = any(k in t for k in ["product manager", "product management", "product owner", "product lead", "产品经理", "产品总监", "产品负责人", "产品主管"])
    strategy = any(k in t for k in ["strategy", "strategic", "bizops", "business operations", "business strategy", "战略", "策略"])
    growth = any(k in t for k in ["growth", "expansion", "增长"])
    gm = any(k in t for k in ["general manager", "country manager", "总经理"])
    program = any(k in t for k in ["program manager", "program management", "project manager", "project management", "项目管理", "项目经理"])
    if not (pm or strategy or growth or gm or program):
        return False, "not_target_role_type"
    # Exclude non-target functional roles
    if any(ex in t for ex in EXCLUDED_FUNCTIONAL):
        return False, "functional_role"
    # Exclude overly senior
    if any(ex in t for ex in EXCLUDED_SENIOR):
        return False, "overly_senior"
    return True, ""


def main():
    jobs = load(AGENT_PATH)
    keep = []
    rejected = Counter()
    for j in jobs:
        title = j.get("title", "")
        company = j.get("company", "")
        loc = j.get("location", "")
        if AMAZON_RE.search(title) or AMAZON_RE.search(company):
            rejected["amazon"] += 1
            continue
        if not is_target_location(loc):
            rejected["non_target_location"] += 1
            continue
        ok, reason = is_target_role(title)
        if not ok:
            rejected[reason] += 1
            continue
        keep.append(j)

    removed = len(jobs) - len(keep)
    if removed:
        save(AGENT_PATH, keep)

    print(f"agent-discovered: {len(jobs)} -> {len(keep)} (removed {removed})")
    print("Rejected reasons:", dict(rejected))

    today = max((j.get("scanned_date", "") for j in keep), default="")
    today_jobs = [j for j in keep if j.get("scanned_date") == today]
    print(f"Latest scan date: {today}, records: {len(today_jobs)}")
    if today_jobs:
        print("By source:")
        for src, cnt in Counter(j.get("source", "unknown") for j in today_jobs).most_common():
            print(f"  {src}: {cnt}")
        print("By location_norm:")
        for loc, cnt in Counter(j.get("location_norm", "") for j in today_jobs).most_common():
            print(f"  {loc}: {cnt}")
        print("By role_type:")
        for rt, cnt in Counter(j.get("role_type", "") for j in today_jobs).most_common():
            print(f"  {rt}: {cnt}")


if __name__ == "__main__":
    main()
