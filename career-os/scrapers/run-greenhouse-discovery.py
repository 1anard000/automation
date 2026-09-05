#!/usr/bin/env python3
"""Greenhouse API job discovery for Career OS."""
import json, os, re, hashlib, sys
from datetime import date
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from collections import Counter

MASTER_PATH = "/Users/iancolrick/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json"
AGENT_PATH = "/Users/iancolrick/.openclaw/workspace/career-os/scrapers/agent-discovered-jobs.json"

TARGET_LOCATIONS = [
    "shenzhen", "hong kong", "hongkong", "guangzhou", "shanghai", "singapore",
    "apac", "asia pacific", "asia-pacific", "southeast asia", "south-east asia",
    "greater china", "bangkok", "kuala lumpur", "tokyo", "seoul", "taipei",
    "jakarta", "manila", "sydney", "melbourne", "remote"
]

ROLE_KEYWORDS = [
    "product manager", "product management", "product owner", "product lead",
    "product director", "head of product", "chief product",
    "strategy", "strategic", "bizops", "business operations", "business strategy",
    "growth", "growth manager", "expansion", "gm ", "general manager",
    "program manager", "program management", "project manager", "project management",
    "产品经理", "产品总监", "产品负责人", "产品主管", "增长", "战略", "策略",
    "总经理", "项目管理", "项目经理"
]

EXCLUDE_TITLE_RE = re.compile(
    r"\b(vp|vice president|svp|evp|chief|cto|cfo|ceo|coo|cmo|president)\b",
    re.IGNORECASE
)

# Exclude non-target functional roles (sales, engineering, design, finance, HR, legal, etc.)
EXCLUDE_FUNCTIONAL_RE = re.compile(
    r"\b(account executive|sales executive|business development|enterprise sales|sdr|bdr|solution architect|software engineer|data engineer|machine learning engineer|frontend|backend|fullstack|ux designer|ui designer|graphic designer|financial analyst|accountant|recruiter|talent acquisition|legal counsel|paralegal|copywriter|content writer|customer success|support specialist|operations analyst)\b",
    re.IGNORECASE
)

EXCLUDE_COMPANY_RE = re.compile(r"\bamazon\b", re.IGNORECASE)

BOARD_SLUGS = [
    # Tier 1
    "okx", "stripe", "coinbase", "twilio", "coupang", "agoda", "databricks", "anthropic",
    # Tier 2
    "flexport", "postman", "figma", "cloudflare", "bitmex", "xendit", "bybit",
    "airbnb", "payoneer", "braze", "gemini", "sendbird", "vercel",
    # APAC / China
    "nium", "tron", "canva", "atlassian", "grab", "gojek", "sea-limited", "shopee",
    "tiktok", "bytedance", "xiaohongshu", "lalamove",
    # Finance / Fintech
    "axa", "hsbc", "standardchartered", "jpmorgan", "goldmansachs", "morganstanley",
    "dbsbank", "ocbc", "uob", "salesforce", "servicenow", "workday", "adobe",
    "autodesk", "intuit", "square", "block", "plaid", "wise", "remitly",
    "airwallex", "rapyd", "checkout", "marqeta", "adyen",
    # Travel / E-commerce
    "booking", "expedia", "trip-com", "trip", "kkday", "klook", "lazada", "zalora",
    "tokopedia", "miniso", "popmart", "skechers", "lululemon", "nike", "adidas", "puma",
    # Legacy industrial / healthcare
    "siemens", "bosch", "philips", "ge", "honeywell", "johnson-controls", "nestle",
    "pepsico", "cocacola", "unilever", "gsk", "pfizer", "roche", "novartis",
    "sanofi", "astrazeneca", "merck",
    # Additional tech
    "gitlab", "github", "shopify", "snowflake", "datadog", "mongodb", "confluent",
    "elastic", "hashicorp", "newrelic", "pagerduty", "sumologic", "splunk",
    "zoom", "slack", "asana", "notion", "linear", "miro", "mural", "lucid",
    "rippling", "gusto", "lever", "greenhouse", "workday", "oracle", "sap",
    "dell", "hp", "cisco", "ibm", "intel", "amd", "nvidia", "qualcomm",
    "mediaTek", "tencent", "alibaba", "antgroup", "meituan", "pinduoduo", "jd",
    "netease", "bilibili", "kuaishou", "oppo", "vivo", "xiaomi", "huawei", "byd",
    "djI", "senseTime", "megvii", "yitu", "cloudwalk"
]


def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_location(loc):
    if not loc:
        return ""
    l = loc.lower()
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
    if "apac" in l or "asia pacific" in l or "asia-pacific" in l:
        return "APAC"
    if "southeast asia" in l or "south-east asia" in l:
        return "Southeast Asia"
    if "greater china" in l:
        return "Greater China"
    if "remote" in l:
        return "Remote"
    return loc


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
    if any(k in t for k in ["strategy", "strategic", "bizops", "business operations", "business strategy", "战略", "策略"]):
        return "Strategy/Ops"
    if any(k in t for k in ["general manager", "gm ", "总经理"]):
        return "General Manager"
    if any(k in t for k in ["program manager", "program management", "project manager", "project management", "项目管理", "项目经理"]):
        return "Program/Project Management"
    return "Other"


def fetch_board(slug):
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    req = Request(url, headers={"User-Agent": "CareerOS-Greenhouse-Scraper/1.0"})
    try:
        with urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("jobs", [])
    except HTTPError as e:
        if e.code == 404:
            print(f"  {slug}: board not found (404)")
        else:
            print(f"  {slug}: HTTP {e.code}")
    except URLError as e:
        print(f"  {slug}: URL error {e.reason}")
    except Exception as e:
        print(f"  {slug}: error {e}")
    return []


def matches_role(title):
    t = title.lower()
    return any(kw.lower() in t for kw in ROLE_KEYWORDS)


def should_exclude(job_title, company_name):
    if EXCLUDE_TITLE_RE.search(job_title):
        return True, "overly senior title"
    if EXCLUDE_FUNCTIONAL_RE.search(job_title):
        return True, "non-target functional role"
    text_to_check = f"{job_title} {company_name}"
    if EXCLUDE_COMPANY_RE.search(text_to_check):
        return True, "amazon"
    return False, ""


def make_record(job, source_slug):
    title = job.get("title", "").strip()
    loc_raw = job.get("location", {})
    if isinstance(loc_raw, dict):
        loc = loc_raw.get("name", "")
    else:
        loc = str(loc_raw)
    url = job.get("absolute_url", "")
    if not url:
        url = f"https://job-boards.greenhouse.io/{source_slug}/jobs/{job.get('id', '')}"
    return {
        "title": title,
        "company": source_slug.capitalize(),
        "location": loc,
        "location_norm": normalize_location(loc),
        "url": url,
        "salary": "",
        "source": f"greenhouse-api-{source_slug}",
        "scanned_date": date.today().isoformat(),
        "role_type": role_type_for(title),
        "english_friendly": True,
        "has_direct_link": True,
        "url_type": "direct",
        "job_id": hashlib.sha1(f"{url}{title}".encode("utf-8")).hexdigest()[:12],
        "status": "not_applied",
        "status_date": date.today().isoformat(),
        "last_touch_date": date.today().isoformat(),
        "quality_score": None,
        "quality_tier": "",
        "low_quality": False,
        "category": "other"
    }


def main():
    master = load_json(MASTER_PATH)
    agent = load_json(AGENT_PATH)

    master_urls = {j.get("url", "") for j in master}
    master_ids = {j.get("job_id", "") for j in master}
    agent_urls = {j.get("url", "") for j in agent}
    agent_ids = {j.get("job_id", "") for j in agent}

    print(f"Loaded master: {len(master)} jobs, agent: {len(agent)} jobs")

    new_jobs = []
    source_counts = Counter()
    skipped_counts = Counter()

    for slug in BOARD_SLUGS:
        jobs = fetch_board(slug)
        if not jobs:
            continue
        print(f"{slug}: {len(jobs)} total jobs")
        for job in jobs:
            title = job.get("title", "")
            if not matches_role(title):
                continue
            loc = job.get("location", {}).get("name", "") if isinstance(job.get("location"), dict) else job.get("location", "")
            if not is_target_location(loc):
                continue
            excl, reason = should_exclude(title, slug)
            if excl:
                skipped_counts[reason] += 1
                continue
            rec = make_record(job, slug)
            if rec["url"] in master_urls or rec["url"] in agent_urls:
                skipped_counts["duplicate_url"] += 1
                continue
            if rec["job_id"] in master_ids or rec["job_id"] in agent_ids:
                skipped_counts["duplicate_id"] += 1
                continue
            new_jobs.append(rec)
            source_counts[slug] += 1
            master_urls.add(rec["url"])
            master_ids.add(rec["job_id"])

    if new_jobs:
        agent.extend(new_jobs)
        save_json(AGENT_PATH, agent)

    print(f"\nNew jobs discovered: {len(new_jobs)}")
    print("By source:", dict(source_counts))
    print("Skipped reasons:", dict(skipped_counts))
    print("Role type distribution:", Counter(j["role_type"] for j in new_jobs))
    print("Location distribution:", Counter(j["location_norm"] for j in new_jobs))

    # Also write a summary JSON for easy reporting
    summary = {
        "date": date.today().isoformat(),
        "new_jobs": len(new_jobs),
        "by_source": dict(source_counts),
        "by_role_type": dict(Counter(j["role_type"] for j in new_jobs)),
        "by_location": dict(Counter(j["location_norm"] for j in new_jobs)),
        "skipped": dict(skipped_counts)
    }
    summary_path = AGENT_PATH.replace(".json", "-summary.json")
    save_json(summary_path, summary)
    print(f"Summary written to {summary_path}")


if __name__ == "__main__":
    main()
