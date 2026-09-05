#!/usr/bin/env python3
"""
Consolidate discovery sources into agent-discovered-jobs.json.
- Greenhouse API jobs are already appended by run-greenhouse-discovery.py.
- This script imports normalized jobs from boss-zhilian-discovery-results.json,
  indeed-jobsdb-results.json, and liepin-results.json, deduplicates against
  jobs-all.json and existing agent-discovered-jobs.json, applies filters, and
  appends only net-new records.
"""
import json
import os
import re
import hashlib
from datetime import date
from collections import Counter

MASTER_PATH = "/Users/iancolrick/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json"
AGENT_PATH = "/Users/iancolrick/.openclaw/workspace/career-os/scrapers/agent-discovered-jobs.json"

SOURCE_FILES = [
    "/Users/iancolrick/.openclaw/workspace/career-os/scrapers/boss-zhilian-discovery-results.json",
    "/Users/iancolrick/.openclaw/workspace/career-os/scrapers/indeed-jobsdb-results.json",
    "/Users/iancolrick/.openclaw/workspace/career-os/scrapers/liepin-results.json",
]

TARGET_LOCATIONS = [
    "shenzhen", "hong kong", "hongkong", "guangzhou", "shanghai", "singapore",
    "apac", "asia pacific", "asia-pacific", "southeast asia", "south-east asia",
    "greater china", "bangkok", "kuala lumpur", "tokyo", "seoul", "taipei",
    "jakarta", "manila", "sydney", "melbourne", "remote"
]

SALARY_FLOOR_RMB = 90_000  # per month
SALARY_FLOOR_HKD = 60_000
SALARY_FLOOR_SGD = 10_000

AMAZON_RE = re.compile(r"\bamazon\b", re.IGNORECASE)


def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"warn: failed to load {path}: {e}")
            return []


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_location(loc):
    if not loc:
        return ""
    l = loc.lower().replace(",", " ").replace("  ", " ")
    if "hong kong" in l or "hongkong" in l:
        return "Hong Kong"
    if "singapore" in l:
        return "Singapore"
    if "shenzhen" in l:
        return "Shenzhen"
    if "shanghai" in l:
        return "Shanghai"
    if "guangzhou" in l:
        return "Guangzhou"
    if "beijing" in l:
        return "Beijing"
    if "hangzhou" in l:
        return "Hangzhou"
    if "apac" in l or "asia pacific" in l or "asia-pacific" in l:
        return "APAC"
    if "southeast asia" in l or "south-east asia" in l:
        return "Southeast Asia"
    if "greater china" in l:
        return "Greater China"
    if "remote" in l:
        return "Remote"
    return loc.strip()


def is_target_location(loc):
    if not loc:
        return False
    l = loc.lower()
    for kw in TARGET_LOCATIONS:
        if kw.lower() in l:
            return True
    return False


def role_type_for(title):
    t = title.lower()
    if any(k in t for k in ["product manager", "product management", "product owner", "product lead", "产品经理", "产品总监", "产品负责人", "产品主管"]):
        return "Product Management"
    if any(k in t for k in ["growth", "expansion", "增长"]):
        return "Growth/Expansion"
    if any(k in t for k in ["strategy", "strategic", "bizops", "business operations", "business strategy", "战略", "策略", "商业化"]):
        return "Strategy/Ops"
    if any(k in t for k in ["general manager", "gm ", "总经理", "country manager"]):
        return "General Manager"
    if any(k in t for k in ["program manager", "program management", "project manager", "project management", "项目管理", "项目经理"]):
        return "Program/Project Management"
    return "Other"


def parse_salary(salary):
    """Return (min_monthly, currency_hint) or (None, None)."""
    if not salary:
        return None, None
    s = salary.lower().replace(",", "")
    # Match patterns like 30-60K, 80-110K·15薪, 45-75K·15薪, 100-200K, 2-3万, 4-8万
    # K = thousand per month (RMB default on zhipin)
    m = re.search(r"(\d+(?:\.\d+)?)\s*[\-~]\s*(\d+(?:\.\d+)?)\s*(k|万|萬|w)?", s)
    if not m:
        return None, None
    low = float(m.group(1))
    high = float(m.group(2))
    unit = m.group(3) or "k"
    if unit in ("万", "萬"):
        # x万 per month in Chinese listings
        return low * 10_000, "RMB"
    # K default: RMB on zhipin, but could be HKD/SGD on other sites if location HK/SG
    return low * 1_000, "unknown"


def salary_meets_floor(salary, location_norm):
    """For Chinese listings, require visible salary >=90k RMB/mo.
    For HK/SG listings, require >=60k HKD / >=10k SGD.
    Returns (meets_floor, reason).
    """
    amount, currency = parse_salary(salary)
    if amount is None:
        return None, "no_salary"
    loc = location_norm.lower()
    if "hong kong" in loc:
        return amount >= SALARY_FLOOR_HKD, f"{amount} HKD"
    if "singapore" in loc:
        return amount >= SALARY_FLOOR_SGD, f"{amount} SGD"
    # Default RMB for mainland/unknown
    return amount >= SALARY_FLOOR_RMB, f"{amount} RMB"


def is_senior_title(title):
    t = title.lower()
    senior_keywords = [
        "senior", "sr.", "sr ", "staff", "principal", "lead", "head of",
        "director", "总监", "负责人", "资深", "高级", "专家", "chief",
        "vp", "vice president", "general manager", "总经理"
    ]
    return any(kw in t for kw in senior_keywords)


def should_keep_fallback(record):
    """Filter fallback search-result jobs.
    - Must have target location.
    - Must not be Amazon.
    - If salary visible, must meet floor.
    - If salary not visible, must have a senior-sounding title.
    - Must not be a category page.
    """
    title = record.get("title", "")
    url = record.get("url", "")
    loc = record.get("location", "")
    salary = record.get("salary", "")
    company = record.get("company", "")

    if AMAZON_RE.search(title) or AMAZON_RE.search(company):
        return False, "amazon"

    if not is_target_location(loc):
        return False, "non_target_location"

    # Skip category/search pages
    if "/zhaopin/" in url and not any(c.isdigit() for c in url.split("/")[-1]):
        return False, "category_page"
    if url.endswith("-jobs") or "/career/" in url or "/city-" in url:
        return False, "category_page"

    meets = salary_meets_floor(salary, normalize_location(loc))
    if meets is None:
        # No salary visible: keep only if senior title
        if not is_senior_title(title):
            return False, "no_salary_not_senior"
        return True, "no_salary_senior"
    return meets[0], f"salary_{meets[1]}"


def build_record(raw, source_label):
    title = raw.get("title", "").strip()
    url = raw.get("url", "").strip()
    loc = raw.get("location", "")
    loc_norm = normalize_location(loc)
    salary = raw.get("salary", "")
    company = raw.get("company", "").strip() or raw.get("source", "")
    today = date.today().isoformat()
    return {
        "title": title,
        "company": company,
        "location": loc,
        "location_norm": loc_norm,
        "url": url,
        "salary": salary,
        "source": source_label,
        "scanned_date": today,
        "role_type": role_type_for(title),
        "english_friendly": True,
        "has_direct_link": "zhipin.com" in url or "liepin.com" in url or "indeed.com" in url or "jobsdb.com" in url,
        "url_type": "direct" if ("zhipin.com/job_detail" in url or "liepin.com/job/" in url or "indeed.com/viewjob" in url or "jobsdb.com/job/" in url) else "search",
        "job_id": hashlib.sha1(f"{url}{title}".encode("utf-8")).hexdigest()[:12],
        "status": "not_applied",
        "status_date": today,
        "last_touch_date": today,
        "quality_score": None,
        "quality_tier": "",
        "low_quality": False,
        "category": "other"
    }


def main():
    master = load_json(MASTER_PATH)
    agent = load_json(AGENT_PATH)

    existing_keys = set()
    for j in master + agent:
        if j.get("url"):
            existing_keys.add(j["url"].strip())
        if j.get("job_id"):
            existing_keys.add(j["job_id"])

    new_jobs = []
    rejected_counts = Counter()
    source_counts = Counter()

    for path in SOURCE_FILES:
        label = os.path.basename(path).replace("-results.json", "").replace("-", "_")
        for raw in load_json(path):
            rec = build_record(raw, label)
            keep, reason = should_keep_fallback(rec)
            if not keep:
                rejected_counts[reason] += 1
                continue
            if rec["url"] in existing_keys or rec["job_id"] in existing_keys:
                rejected_counts["duplicate"] += 1
                continue
            new_jobs.append(rec)
            existing_keys.add(rec["url"])
            existing_keys.add(rec["job_id"])
            source_counts[label] += 1

    if new_jobs:
        agent.extend(new_jobs)
        save_json(AGENT_PATH, agent)

    print(f"Net-new fallback jobs appended: {len(new_jobs)}")
    print("By source:", dict(source_counts))
    print("Rejected reasons:", dict(rejected_counts))
    print("Role type distribution:", Counter(j["role_type"] for j in new_jobs))
    print("Location distribution:", Counter(j["location_norm"] for j in new_jobs))


if __name__ == "__main__":
    main()
