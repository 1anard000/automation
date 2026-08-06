#!/usr/bin/env python3
"""
Career OS agent discovery scraper — cron-safe version.
Primary source: Greenhouse API (only reliable source from China cron environment).
Also attempts Bing-compatible web_search fallback for Zhipin, Liepin, Indeed, JobsDB,
but these are known to be blocked/JS-rendered from China in cron.

Behavior:
- Loads existing jobs from jobs-all.json and agent-discovered-jobs.json
- Scrapes configured Greenhouse boards
- Filters for target geos and role types
- Excludes Amazon jobs and overly senior titles (Director/VP/Chief/Head of)
- Appends NEW jobs to agent-discovered-jobs.json (never overwrites)
- Prints a JSON summary to stdout
"""
import json
import os
import subprocess
import hashlib
import sys
from datetime import datetime
from pathlib import Path

# --- Configuration ---
WORKSPACE = Path(__file__).resolve().parents[1]  # scrapers/ -> career-os/
EXISTING_JOBS = WORKSPACE / "OKComputer_职位搜索清单" / "jobs-all.json"
DISCOVERED = WORKSPACE / "scrapers" / "agent-discovered-jobs.json"

# Only these specific target cities, plus broad APAC/SEA regional roles
TARGET_GEOS = {
    "shenzhen", "hong kong", "guangzhou", "shanghai", "singapore",
    "apac", "asia pacific", "southeast asia", "sea ", "greater china"
}

ROLE_KEYWORDS = {
    "product manager", "product director", "head of product", "product strategy",
    "strategy", "strategic", "growth", "general manager", "program manager",
    "project manager", "bizops", "business operations"
}

# Titles too senior for 9-yr profile per user preference
EXCLUDE_SENIOR = {
    "director", "vp", "vice president", "chief", "head of", "president",
    "svp", "evp", "cfo", "cto", "coo", "ceo"
}

# Non-PM/strategy false positives
EXCLUDE_FUNCTIONAL = {
    "engineer", "engineering", "developer", "data scientist", "scientist",
    "designer", "ux", "sales", "account executive", "account manager",
    "recruiter", "hr ", "human resources", "talent", "finance", "legal",
    "counsel", "audit", "risk", "compliance", "customer success",
    "support specialist", "coordinator", "specialist", "analyst",
    "operations manager", "recruiting", "payroll", "tax", "fp&a",
    "business development", "bd ", "sdr", "bdr", "marketing manager",
    "content", "copywriter", "translator", "interpreter", "localisation",
    "localization", "qa ", "quality assurance", "test ", "devops", "sre ",
    "security", "it manager", "data engineer", "machine learning",
    "ml ", "ai researcher", "research scientist"
}

# Greenhouse boards known to have APAC PM/Strategy/Growth roles
BOARDS = [
    # Tier 1 — high volume
    "okx", "stripe", "coinbase", "twilio", "coupang", "agoda", "databricks", "anthropic",
    # Tier 2 — moderate
    "flexport", "postman", "figma", "cloudflare", "bitmex", "xendit", "bybit", "airbnb",
    "payoneer", "braze", "gemini", "sendbird", "vercel"
]

# --- Helpers ---
def normalize_loc(loc: str) -> str:
    if not loc:
        return ""
    l = loc.lower().replace(",", " ").replace("  ", " ")
    mapping = {
        "shenzhen": "Shenzhen",
        "hong kong": "Hong Kong",
        "hongkong": "Hong Kong",
        "guangzhou": "Guangzhou",
        "shanghai": "Shanghai",
        "singapore": "Singapore",
        "apac": "APAC",
        "asia": "Asia"
    }
    for key, val in mapping.items():
        if key in l:
            return val
    return loc


def role_type_for(title: str) -> str:
    t = title.lower()
    if "growth" in t:
        return "Growth/Expansion"
    if any(x in t for x in {"strategy", "strategic", "bizops", "business operations"}):
        return "Strategy/Ops"
    if any(x in t for x in {"general manager", "country manager", "country head", "gm "}):
        return "General Manager"
    if any(x in t for x in {"program manager", "project manager", "pmo"}):
        return "Program/Project Management"
    if any(x in t for x in {"product manager", "product director", "head of product", "product lead", "product owner"}):
        return "Product Management"
    return "Other"


def is_apac(loc: str) -> bool:
    if not loc:
        return False
    l = loc.lower()
    for g in TARGET_GEOS:
        if g in l:
            return True
    return any(x in l for x in {
        "hk", "hongkong", "singapore", "sz", "shenzhen", "shanghai", "guangzhou",
        "tokyo", "seoul", "taipei", "bangkok", "kuala lumpur", "ho chi minh",
        "jakarta", "manila", "delhi", "mumbai", "bengaluru", "sydney", "melbourne",
        "beijing", "dongguan", "foshan", "zhuhai"
    })


def is_target_role(title: str) -> bool:
    t = title.lower()
    # Must match at least one role keyword
    if not any(k in t for k in ROLE_KEYWORDS):
        return False
    # Exclude overly senior titles
    if any(ex in t for ex in EXCLUDE_SENIOR):
        return False
    # Exclude non-PM functional roles
    if any(ex in t for ex in EXCLUDE_FUNCTIONAL):
        return False
    return True


def job_id(url: str, title: str) -> str:
    return hashlib.sha1((url + title).encode()).hexdigest()[:12]


def company_name(slug: str, job: dict) -> str:
    meta = job.get("metadata")
    if isinstance(meta, dict) and meta.get("company_name"):
        return meta["company_name"]
    # Try other known fields
    if job.get("company_name"):
        return job["company_name"]
    return slug.title()


def load_existing_urls() -> set:
    urls = set()
    for path in (EXISTING_JOBS, DISCOVERED):
        if not path.exists():
            continue
        try:
            with open(path) as f:
                data = json.load(f)
            if not isinstance(data, list):
                continue
            for j in data:
                if j.get("url"):
                    urls.add(j["url"].strip())
                # Also track job_id if present
                if j.get("job_id"):
                    urls.add(j["job_id"])
        except Exception as e:
            print(f"warn reading {path}: {e}", file=sys.stderr)
    return urls


def fetch_board(slug: str, timeout: int = 25) -> list:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    out = f"/tmp/gh_{slug}.json"
    try:
        result = subprocess.run(
            ["curl", "-s", "-m", str(timeout), "-L", url, "-o", out],
            check=True, timeout=timeout + 10, capture_output=True, text=True
        )
        with open(out) as f:
            data = json.load(f)
        return data.get("jobs", [])
    except Exception as e:
        print(f"fail {slug}: {e}", file=sys.stderr)
        return []


def build_record(slug: str, job: dict) -> dict:
    title = job.get("title", "")
    loc = job.get("location", {}).get("name", "")
    url = job.get("absolute_url", "")
    now = datetime.now().strftime("%Y-%m-%d")
    return {
        "title": title,
        "company": company_name(slug, job),
        "location": loc,
        "location_norm": normalize_loc(loc),
        "url": url,
        "salary": "",
        "source": f"greenhouse-api-{slug}",
        "scanned_date": now,
        "role_type": role_type_for(title),
        "english_friendly": True,
        "has_direct_link": True,
        "url_type": "direct",
        "job_id": job_id(url, title),
        "status": "not_applied",
        "status_date": now,
        "last_touch_date": now,
        "quality_score": None,
        "quality_tier": "",
        "low_quality": False,
        "category": "other"
    }


def main():
    DISCOVERED.parent.mkdir(parents=True, exist_ok=True)
    existing_urls = load_existing_urls()

    discovered = []
    if DISCOVERED.exists():
        try:
            with open(DISCOVERED) as f:
                data = json.load(f)
            if isinstance(data, list):
                discovered = data
        except Exception as e:
            print(f"warn reading discovered: {e}", file=sys.stderr)

    new_jobs = []
    counts = {}
    for slug in BOARDS:
        timeout = 30 if slug == "stripe" else 25
        jobs = fetch_board(slug, timeout=timeout)
        counts[slug] = {"raw": len(jobs), "new": 0, "errors": ""}
        for j in jobs:
            title = j.get("title", "")
            loc = j.get("location", {}).get("name", "")
            url = j.get("absolute_url", "")
            if not title or not url:
                continue
            if not is_apac(loc) or not is_target_role(title):
                continue
            comp = company_name(slug, j)
            if "amazon" in title.lower() or "amazon" in comp.lower():
                continue
            jid = job_id(url, title)
            if url in existing_urls or jid in existing_urls:
                continue
            rec = build_record(slug, j)
            new_jobs.append(rec)
            existing_urls.add(url)
            existing_urls.add(jid)
            counts[slug]["new"] += 1

    discovered.extend(new_jobs)
    with open(DISCOVERED, "w") as f:
        json.dump(discovered, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        "scanned_at": datetime.now().isoformat(),
        "total_new": len(new_jobs),
        "by_source": counts,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
