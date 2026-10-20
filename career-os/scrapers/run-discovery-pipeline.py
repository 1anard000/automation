#!/usr/bin/env python3
"""
Career OS Job Discovery Pipeline — 2026-10-21
1. Load master + agent dedupe sets
2. Check boss-zhilian pre-fetched results for survivors
3. Run Greenhouse API sweep
4. Post-cleanup (salary floor, location, dedup)
5. Backfill schema
6. Rewrite summary
"""
from __future__ import annotations
import json, re, os, sys, hashlib, subprocess, datetime
from pathlib import Path

BASE = Path("/Users/iancolrick/.openclaw/workspace/career-os")
MASTER = BASE / "OKComputer_职位搜索清单" / "jobs-all.json"
AGENT = BASE / "scrapers" / "agent-discovered-jobs.json"
SUMMARY = BASE / "scrapers" / "agent-discovered-jobs-summary.json"
BOSS_RESULTS = BASE / "scrapers" / "boss-zhilian-discovery-results.json"
TODAY = "2026-10-21"

# Salary floors
FLOORS = {"rmb": 90, "hkd": 60, "sgd": 10}

TARGET_LOCS = [
    "shenzhen", "hong kong", "guangzhou", "shanghai", "singapore",
    "apac", "asia pacific", "southeast asia", "bangkok", "kuala lumpur",
    "tokyo", "seoul", "taipei", "jakarta", "manila"
]

APAC_RAW = [
    "shenzhen", "hong kong", "guangzhou", "shanghai", "singapore",
    "apac", "asia pacific", "southeast asia", "bangkok", "kuala lumpur",
    "tokyo", "seoul", "taipei", "jakarta", "manila", "sydney", "melbourne"
]

US_REMOTE_PATTERNS = [
    "remote - us", "remote - usa", "remote, united states", "remote, us",
    "remote - united states", "remote - america", "us-remote", "usa-remote"
]

def sha1_12(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:12]

def load_json(path: Path):
    with open(path) as f:
        return json.load(f)

def save_json(path: Path, data):
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def norm_url(url: str) -> str:
    return (url or "").strip().rstrip("/").lower()

def parse_salary_high(salary: str) -> float | None:
    if not salary:
        return None
    s = str(salary)
    s = re.sub(r"[·.]\d+薪", "", s)
    m = re.search(r"(\d+)[-–](\d+)\s*K", s, re.IGNORECASE)
    if m:
        return float(m.group(2))
    m = re.search(r"(\d+)[-–](\d+)", s)
    if m:
        high = float(m.group(2))
        if high < 1000:
            return high
        return high / 1000.0
    m = re.search(r"(\d+)\s*K", s, re.IGNORECASE)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+)", s)
    if m:
        val = float(m.group(1))
        if val >= 1000:
            return val / 1000.0
        return val
    return None

def is_target_location(loc: str) -> bool:
    if not loc:
        return False
    loc_l = loc.lower()
    for t in TARGET_LOCS:
        if t in loc_l:
            return True
    return False

def is_apac_remote(loc: str) -> bool:
    if not loc:
        return False
    loc_l = loc.lower()
    for p in US_REMOTE_PATTERNS:
        if p in loc_l:
            return False
    for t in APAC_RAW:
        if t in loc_l:
            return True
    return False

def is_us_remote(loc: str) -> bool:
    if not loc:
        return False
    loc_l = loc.lower()
    for p in US_REMOTE_PATTERNS:
        if p in loc_l:
            return True
    if "remote" in loc_l and not is_apac_remote(loc):
        return True
    return False

EXCLUDE_COMPANY_RE = re.compile(r"\bamazon\b", re.IGNORECASE)
EXCLUDE_TITLE_RE = re.compile(
    r"\b(vp|vice president|svp|evp|chief|cto|cfo|ceo|coo|cmo|president|head of)\b",
    re.IGNORECASE
)
EXCLUDE_NON_PM_DIRECTOR_RE = re.compile(
    r"\bdirector\b(?![^|]*\b(product|pm|programme?|project)\b)",
    re.IGNORECASE
)
PM_KEYWORDS_RE = re.compile(r"\b(product|programme?|project)\b", re.IGNORECASE)

PURE_CRYPTO_PATTERNS = [
    "defi", "dex", "trading bot", "copy trading", "web3", "nft", "dao",
    "blockchain protocol", "smart contract", "on-chain", "chainlink"
]
FINTECH_KEEP_PATTERNS = [
    "payment", "fintech", "bank", "tradingview", "portfolio", "wealth",
    "asset management", "risk", "compliance", "kyc", "aml", "fiat"
]

def should_exclude(title: str, company: str) -> tuple[bool, str]:
    text = f"{title} {company}".lower()
    if EXCLUDE_COMPANY_RE.search(text):
        return True, "amazon"
    if EXCLUDE_TITLE_RE.search(title):
        return True, "seniority"
    if "director" in title.lower() and EXCLUDE_NON_PM_DIRECTOR_RE.search(title):
        if not PM_KEYWORDS_RE.search(title):
            return True, "non-pm-director"
    t_l = title.lower()
    is_crypto = any(p in t_l for p in PURE_CRYPTO_PATTERNS)
    is_fintech = any(p in t_l for p in FINTECH_KEEP_PATTERNS)
    if is_crypto and not is_fintech:
        return True, "pure-crypto"
    return False, ""

def normalize_location(loc: str) -> str:
    if not loc:
        return ""
    loc_l = loc.lower().strip()
    for t in TARGET_LOCS:
        if t in loc_l:
            return t.title()
    for t in APAC_RAW:
        if t in loc_l:
            return t.title()
    return loc_l

def build_schema(job: dict) -> dict:
    url = job.get("url", "")
    title = job.get("title", "")
    loc = job.get("location", "")
    loc_norm = job.get("location_norm") or normalize_location(loc)
    job_id = job.get("job_id") or sha1_12(url + title)
    now = TODAY
    return {
        "title": title,
        "company": job.get("company", ""),
        "location": loc,
        "location_norm": loc_norm,
        "url": url,
        "salary": job.get("salary", ""),
        "source": job.get("source", ""),
        "scanned_date": job.get("scanned_date", now),
        "role_type": job.get("role_type", "Product Management"),
        "english_friendly": job.get("english_friendly", True),
        "has_direct_link": job.get("has_direct_link", True),
        "url_type": job.get("url_type", "direct"),
        "job_id": job_id,
        "status": job.get("status", "not_applied"),
        "status_date": job.get("status_date", now),
        "last_touch_date": job.get("last_touch_date", now),
        "quality_score": job.get("quality_score", None),
        "quality_tier": job.get("quality_tier", ""),
        "low_quality": job.get("low_quality", False),
        "category": job.get("category", "other"),
    }

def main():
    report = {"date": TODAY, "steps": []}

    # 1. Load context
    master = load_json(MASTER)
    agent = load_json(AGENT)
    master_urls = {norm_url(j.get("url", "")) for j in master}
    master_ids = {j.get("job_id", "") for j in master}
    agent_urls = {norm_url(j.get("url", "")) for j in agent}
    agent_ids = {j.get("job_id", "") for j in agent}
    report["steps"].append({
        "step": "load_context",
        "master_total": len(master),
        "agent_total": len(agent),
        "master_today": len([j for j in master if j.get("scanned_date") == TODAY]),
        "agent_today": len([j for j in agent if j.get("scanned_date") == TODAY]),
    })

    # 2. Boss直聘 pre-check
    boss_data = load_json(BOSS_RESULTS)
    boss_candidates = []
    for rec in boss_data:
        url = rec.get("url", "")
        if not url:
            continue
        nurl = norm_url(url)
        if nurl in master_urls or nurl in agent_urls:
            continue
        if "/job_detail/" not in url and "/jobdetail/" not in url:
            continue
        salary_high = parse_salary_high(rec.get("salary", ""))
        loc = (rec.get("location") or "").lower()
        if "hong kong" in loc:
            floor = FLOORS["hkd"]
        elif "singapore" in loc:
            floor = FLOORS["sgd"]
        else:
            floor = FLOORS["rmb"]
        if salary_high is not None and salary_high < floor:
            continue
        boss_candidates.append(rec)
    boss_survivors = len(boss_candidates)
    report["steps"].append({
        "step": "boss_prefetch_check",
        "raw": len(boss_data),
        "survivors": boss_survivors,
        "action": "import" if boss_survivors > 0 else "skip",
    })

    # 3. Run Greenhouse API sweep (background)
    greenhouse_script = BASE / "scrapers" / "run-greenhouse-discovery.py"
    gh_result = subprocess.run(
        ["python3", str(greenhouse_script)],
        capture_output=True, text=True, timeout=300
    )
    report["steps"].append({
        "step": "greenhouse_api",
        "returncode": gh_result.returncode,
        "stdout_tail": gh_result.stdout[-500:] if gh_result.stdout else "",
        "stderr_tail": gh_result.stderr[-500:] if gh_result.stderr else "",
    })

    # 4. Post-cleanup
    post_script = BASE / "scrapers" / "post-discovery-cleanup.py"
    if post_script.exists():
        post_result = subprocess.run(
            ["python3", str(post_script)],
            capture_output=True, text=True, timeout=120
        )
        report["steps"].append({
            "step": "post_cleanup",
            "returncode": post_result.returncode,
            "stdout_tail": post_result.stdout[-500:] if post_result.stdout else "",
            "stderr_tail": post_result.stderr[-500:] if post_result.stderr else "",
        })
    else:
        report["steps"].append({"step": "post_cleanup", "status": "script_missing"})

    # 5. Backfill schema
    backfill_script = BASE / "scrapers" / "backfill-schema.py"
    if backfill_script.exists():
        backfill_result = subprocess.run(
            ["python3", str(backfill_script)],
            capture_output=True, text=True, timeout=120
        )
        report["steps"].append({
            "step": "backfill_schema",
            "returncode": backfill_result.returncode,
            "stdout_tail": backfill_result.stdout[-500:] if backfill_result.stdout else "",
            "stderr_tail": backfill_result.stderr[-500:] if backfill_result.stderr else "",
        })
    else:
        report["steps"].append({"step": "backfill_schema", "status": "script_missing"})

    # 6. Rewrite summary
    summary_script = BASE / "scrapers" / "rewrite-summary.py"
    if summary_script.exists():
        summary_result = subprocess.run(
            ["python3", str(summary_script)],
            capture_output=True, text=True, timeout=120
        )
        report["steps"].append({
            "step": "rewrite_summary",
            "returncode": summary_result.returncode,
            "stdout_tail": summary_result.stdout[-500:] if summary_result.stdout else "",
            "stderr_tail": summary_result.stderr[-500:] if summary_result.stderr else "",
        })
    else:
        report["steps"].append({"step": "rewrite_summary", "status": "script_missing"})

    # 7. Final verification
    master_final = load_json(MASTER)
    agent_final = load_json(AGENT)
    master_today = [j for j in master_final if j.get("scanned_date") == TODAY]
    agent_today = [j for j in agent_final if j.get("scanned_date") == TODAY]
    all_today = master_today + agent_today

    # Dedup check
    seen_urls = set()
    dup_urls = []
    for j in all_today:
        nurl = norm_url(j.get("url", ""))
        if nurl in seen_urls:
            dup_urls.append(nurl)
        seen_urls.add(nurl)

    # Quality checks
    quality_issues = []
    for j in all_today:
        title = j.get("title", "")
        company = j.get("company", "")
        loc = j.get("location", "")
        excl, reason = should_exclude(title, company)
        if excl:
            quality_issues.append({"title": title, "company": company, "reason": reason})
        if is_us_remote(loc):
            quality_issues.append({"title": title, "company": company, "reason": "us-remote"})

    # Location check
    loc_ok = []
    loc_bad = []
    for j in all_today:
        loc = (j.get("location_norm") or "").strip() or (j.get("location") or "")
        if is_target_location(loc) or is_apac_remote(j.get("location", "")):
            loc_ok.append(j)
        else:
            loc_bad.append(j)

    report["final"] = {
        "master_today": len(master_today),
        "agent_today": len(agent_today),
        "total_today": len(all_today),
        "unique_urls_today": len(seen_urls),
        "dup_urls_today": dup_urls,
        "quality_issues": quality_issues,
        "loc_ok": len(loc_ok),
        "loc_bad": len(loc_bad),
        "by_source": {},
        "by_role_type": {},
        "by_location": {},
    }

    for j in all_today:
        src = j.get("source", "unknown")
        rt = j.get("role_type", "unknown")
        loc = (j.get("location_norm") or "").strip() or (j.get("location") or "")
        report["final"]["by_source"][src] = report["final"]["by_source"].get(src, 0) + 1
        report["final"]["by_role_type"][rt] = report["final"]["by_role_type"].get(rt, 0) + 1
        report["final"]["by_location"][loc] = report["final"]["by_location"].get(loc, 0) + 1

    save_json(BASE / "scrapers" / f"discovery-report-{TODAY}.json", report)
    print(json.dumps(report["final"], ensure_ascii=False, indent=2))
    print("---")
    print(f"Report saved to discovery-report-{TODAY}.json")

if __name__ == "__main__":
    main()
