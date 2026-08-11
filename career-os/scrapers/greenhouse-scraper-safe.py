#!/usr/bin/env python3
"""
Safe Greenhouse + optional Ashby API scraper for Career OS.
- Appends new records to agent-discovered-jobs.json (never overwrites it).
- Deduplicates against both jobs-all.json and agent-discovered-jobs.json by URL.
- Type-checks Greenhouse metadata before extracting company name.
- Targets APAC PM/Strategy/Growth/Program/GM roles.
- Skips known false-positive titles (engineering, design, sales, HR, legal, etc.).
- Excludes overly senior titles (Director, VP, Chief, Head of, etc.) per target profile.
- Excludes Amazon jobs.
- Handles Greenhouse EU-domain boards (e.g. Bybit) and an optional Ashby fallback.

Usage:
    python3 greenhouse-scraper-safe.py

Outputs:
    - Appends to ../scrapers/agent-discovered-jobs.json
    - Prints JSON summary with per-board counts

If agent-discovered-jobs.json is missing or corrupted, the script starts fresh.
"""
import json, subprocess, hashlib, sys, time
from datetime import datetime
from pathlib import Path

# --- Configuration ---
WORKSPACE = Path("/Users/iancolrick/.openclaw/workspace/career-os")
EXISTING_JOBS = WORKSPACE / "OKComputer_职位搜索清单" / "jobs-all.json"
DISCOVERED = WORKSPACE / "scrapers" / "agent-discovered-jobs.json"

# Target cities per user preference. The scraper can optionally allow broad regional
# markers ("apac", "asia pacific", "southeast asia") for roles that cover the region.
TARGET_GEOS = {
    "shenzhen", "hong kong", "guangzhou", "shanghai", "singapore",
    "apac", "asia pacific", "southeast asia", "sea ", "greater china"
}

ROLE_KEYWORDS = {
    "product manager", "product director", "head of product", "product strategy",
    "strategy", "strategic", "growth", "general manager", "program manager",
    "project manager", "bizops", "business operations"
}

# Titles too senior for the target profile (9yr exp → Manager/Sr Manager, not exec).
EXCLUDE_SENIOR = {
    "director", "vp", "vice president", "chief", "head of", "president",
    "svp", "evp", "cfo", "cto", "coo", "ceo"
}

# Non-PM/strategy functional false positives that pass the keyword filter.
EXCLUDE_TITLES = {
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
    "ml ", "ai researcher", "research scientist", "commercial counsel",
    "partner manager", "channel manager", "vendor manager", "procurement",
    "administrative", "office manager", "facilities", "receptionist",
    "paralegal", "lawyer", "solicitor", "barrister", "accountant",
    "bookkeeper", "investment banker", "trader", "portfolio manager"
}

# Standard Greenhouse boards. Add new productive boards here; remove dead 404s.
BOARDS = [
    "okx", "stripe", "coinbase", "twilio", "coupang", "agoda", "databricks", "anthropic",
    "flexport", "postman", "figma", "cloudflare", "xendit", "airbnb",
    "payoneer", "braze", "gemini", "sendbird", "vercel", "gitlab", "turing", "lyft",
    "didi", "remote"
]

# Boards hosted on Greenhouse EU domain (not boards-api.greenhouse.io).
# Format: {board_slug: company_name_override}
EU_BOARDS = {
    "bybit": "Bybit"
}

# Optional Ashby fallback — historically low yield for APAC PM but cheap to check.
ASHBY_BOARDS = ["notion", "posthog"]

# --- Helpers ---
def normalize_loc(loc: str) -> str:
    if not loc:
        return ""
    l = loc.lower().replace(",", " ")
    for g in TARGET_GEOS:
        if g in l:
            return g.title()
    if "hk" in l or "hongkong" in l:
        return "Hong Kong"
    return loc

def role_type_for(title: str) -> str:
    t = title.lower()
    if "growth" in t:
        return "Growth/Expansion"
    if any(x in t for x in {"strategy", "strategic", "bizops", "business operations"}):
        return "Strategy/Ops"
    if any(x in t for x in {"general manager", "country manager", "country head"}):
        return "General Manager"
    if any(x in t for x in {"program manager", "project manager", "pmo"}):
        return "Program/Project Management"
    if any(x in t for x in {"product manager", "product director", "head of product"}):
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
        "jakarta", "manila", "delhi", "mumbai", "bengaluru", "sydney", "melbourne"
    })

def is_target_role(title: str) -> bool:
    t = title.lower()
    if any(ex in t for ex in EXCLUDE_TITLES):
        return False
    if any(ex in t for ex in EXCLUDE_SENIOR):
        return False
    return any(k in t for k in ROLE_KEYWORDS)

def job_id(url: str, title: str) -> str:
    return hashlib.sha1((url + title).encode()).hexdigest()[:12]

def company_name(slug: str, job: dict, override: str = "") -> str:
    if override:
        return override
    meta = job.get("metadata")
    if isinstance(meta, dict) and meta.get("company_name"):
        return meta["company_name"]
    return slug.title()

def load_existing_urls() -> set:
    urls = set()
    for path in (EXISTING_JOBS, DISCOVERED):
        if not path.exists():
            continue
        try:
            data = json.load(open(path))
            if not isinstance(data, list):
                continue
            for j in data:
                if j.get("url"):
                    urls.add(j["url"])
        except Exception as e:
            print(f"warn reading {path}: {e}", file=sys.stderr)
    return urls

def fetch_greenhouse(slug: str, eu: bool = False, timeout: int = 20) -> list:
    if eu:
        url = f"https://job-boards.eu.greenhouse.io/{slug}/jobs"
    else:
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    out = f"/tmp/gh_{slug}.json"
    try:
        subprocess.run(["curl", "-s", "-m", str(timeout), url, "-o", out], check=True, timeout=timeout + 10)
        with open(out) as f:
            data = json.load(f)
        return data.get("jobs", []) if isinstance(data, dict) else []
    except Exception as e:
        print(f"fail greenhouse {slug}: {e}", file=sys.stderr)
        return []

def fetch_ashby(slug: str, timeout: int = 30) -> list:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    out = f"/tmp/ashby_{slug}.json"
    try:
        subprocess.run(["curl", "-s", "-m", str(timeout), url, "-o", out], check=True, timeout=timeout + 15)
        with open(out) as f:
            data = json.load(f)
        return data.get("jobs", []) if isinstance(data, dict) else []
    except Exception as e:
        print(f"fail ashby {slug}: {e}", file=sys.stderr)
        return []

def build_record(source_prefix: str, company: str, title: str, loc: str, url: str, board: str = "") -> dict:
    now = datetime.now().strftime("%Y-%m-%d")
    return {
        "title": title,
        "company": company,
        "location": loc,
        "location_norm": normalize_loc(loc),
        "url": url,
        "salary": "",
        "source": f"{source_prefix}-{board}" if board else source_prefix,
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
            data = json.load(open(DISCOVERED))
            if isinstance(data, list):
                discovered = data
        except Exception as e:
            print(f"warn reading discovered: {e}", file=sys.stderr)

    new_jobs = []
    counts = {}

    # Standard Greenhouse boards
    for slug in BOARDS:
        timeout = 30 if slug == "stripe" else 20
        jobs = fetch_greenhouse(slug, timeout=timeout)
        time.sleep(0.3)
        counts[f"greenhouse:{slug}"] = {"raw": len(jobs), "new": 0}
        for j in jobs:
            title = j.get("title", "")
            loc = j.get("location", {}).get("name", "") if isinstance(j.get("location"), dict) else ""
            url = j.get("absolute_url", "")
            if not title or not url:
                continue
            if not is_apac(loc) or not is_target_role(title):
                continue
            if "amazon" in title.lower() or "amazon" in company_name(slug, j).lower():
                continue
            if url in existing_urls:
                continue
            rec = build_record("greenhouse-api", company_name(slug, j), title, loc, url, board=slug)
            new_jobs.append(rec)
            existing_urls.add(url)
            counts[f"greenhouse:{slug}"]["new"] += 1

    # Greenhouse EU-domain boards (e.g. Bybit)
    for slug, company_override in EU_BOARDS.items():
        jobs = fetch_greenhouse(slug, eu=True, timeout=20)
        time.sleep(0.3)
        counts[f"greenhouse-eu:{slug}"] = {"raw": len(jobs), "new": 0}
        for j in jobs:
            title = j.get("title", "")
            loc = j.get("location", {}).get("name", "") if isinstance(j.get("location"), dict) else ""
            url = j.get("absolute_url", "")
            if not title or not url:
                continue
            if not is_apac(loc) or not is_target_role(title):
                continue
            if url in existing_urls:
                continue
            rec = build_record("greenhouse-api", company_override, title, loc, url, board=slug)
            new_jobs.append(rec)
            existing_urls.add(url)
            counts[f"greenhouse-eu:{slug}"]["new"] += 1

    # Ashby fallback
    for slug in ASHBY_BOARDS:
        jobs = fetch_ashby(slug, timeout=30)
        time.sleep(0.3)
        counts[f"ashby:{slug}"] = {"raw": len(jobs), "new": 0}
        for j in jobs:
            title = j.get("title", "")
            loc = j.get("location", "")
            url = j.get("jobUrl", "")
            if not title or not url:
                continue
            if not is_apac(loc) or not is_target_role(title):
                continue
            if url in existing_urls:
                continue
            rec = build_record("ashby-api", company_name(slug, j), title, loc, url, board=slug)
            new_jobs.append(rec)
            existing_urls.add(url)
            counts[f"ashby:{slug}"]["new"] += 1

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
