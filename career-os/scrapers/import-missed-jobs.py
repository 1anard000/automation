#!/usr/bin/env python3
"""
Import Boss直聘 zhaopin records + Indeed/JobsDB individual jobs.
Targeted import for records that are NOT already in master.
"""
from __future__ import annotations
import json, re, hashlib
from pathlib import Path

BASE = Path("/Users/iancolrick/.openclaw/workspace/career-os")
MASTER = BASE / "OKComputer_职位搜索清单" / "jobs-all.json"
AGENT = BASE / "scrapers" / "agent-discovered-jobs.json"
BOSS_RESULTS = BASE / "scrapers" / "boss-zhilian-discovery-results.json"
INDEED_RESULTS = BASE / "scrapers" / "indeed-jobsdb-results.json"
TODAY = "2026-10-21"

def sha1_12(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:12]

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

def normalize_location(loc: str) -> str:
    if not loc:
        return ""
    loc_l = loc.lower().strip()
    targets = [
        ("shenzhen", "Shenzhen"), ("hong kong", "Hong Kong"), ("guangzhou", "Guangzhou"),
        ("shanghai", "Shanghai"), ("singapore", "Singapore"), ("beijing", "Beijing"),
        ("tokyo", "Tokyo"), ("seoul", "Seoul"), ("bangkok", "Bangkok"),
        ("taipei", "Taipei"), ("jakarta", "Jakarta"), ("manila", "Manila"),
        ("kuala lumpur", "Kuala Lumpur"), ("sydney", "Sydney"), ("melbourne", "Melbourne")
    ]
    for key, val in targets:
        if key in loc_l:
            return val
    return loc_l

def build_schema(job: dict) -> dict:
    url = job.get("url", "")
    title = job.get("title", "")
    loc = job.get("location", "")
    loc_norm = job.get("location_norm") or normalize_location(loc)
    job_id = job.get("job_id") or sha1_12(url + title)
    return {
        "title": title,
        "company": job.get("company", ""),
        "location": loc,
        "location_norm": loc_norm,
        "url": url,
        "salary": job.get("salary", ""),
        "source": job.get("source", ""),
        "scanned_date": job.get("scanned_date", TODAY),
        "role_type": job.get("role_type", "Product Management"),
        "english_friendly": job.get("english_friendly", True),
        "has_direct_link": job.get("has_direct_link", True),
        "url_type": job.get("url_type", "direct"),
        "job_id": job_id,
        "status": job.get("status", "not_applied"),
        "status_date": job.get("status_date", TODAY),
        "last_touch_date": job.get("last_touch_date", TODAY),
        "quality_score": job.get("quality_score", None),
        "quality_tier": job.get("quality_tier", ""),
        "low_quality": job.get("low_quality", False),
        "category": job.get("category", "other"),
    }

def main():
    with open(MASTER) as f:
        master = json.load(f)
    with open(AGENT) as f:
        agent = json.load(f)
    master_urls = {norm_url(j.get("url", "")) for j in master}
    agent_urls = {norm_url(j.get("url", "")) for j in agent}

    new_records = []

    # === Boss直聘 zhaopin records ===
    with open(BOSS_RESULTS) as f:
        boss_data = json.load(f)
    for rec in boss_data:
        url = rec.get("url", "")
        if not url:
            continue
        nurl = norm_url(url)
        if nurl in master_urls or nurl in agent_urls:
            continue
        # Only import records with salary data
        salary = rec.get("salary", "")
        if not salary:
            continue
        salary_high = parse_salary_high(salary)
        loc = (rec.get("location") or "").lower()
        if "hong kong" in loc:
            floor = 60
        elif "singapore" in loc:
            floor = 10
        else:
            floor = 90
        if salary_high is not None and salary_high < floor:
            continue
        rec["source"] = "boss-zhilian-websearch"
        rec["scanned_date"] = TODAY
        new_records.append(build_schema(rec))

    # === Indeed/JobsDB individual jobs ===
    with open(INDEED_RESULTS) as f:
        indeed_data = json.load(f)
    for rec in indeed_data:
        url = rec.get("url", "")
        if not url:
            continue
        nurl = norm_url(url)
        if nurl in master_urls or nurl in agent_urls:
            continue
        # Skip listing pages
        if "/viewjob" not in url and "/job/" not in url:
            continue
        rec["source"] = "indeed-jobsdb-websearch"
        rec["scanned_date"] = TODAY
        rec["role_type"] = "Product Management"
        new_records.append(build_schema(rec))

    print(f"New records to import: {len(new_records)}")
    for r in new_records:
        print(f"  [{r['source']}] {r['title']} | {r['company']} | {r['location']} | {r['salary']}")

    if new_records:
        agent.extend(new_records)
        with open(AGENT, "w") as f:
            json.dump(agent, f, ensure_ascii=False, indent=2)
        print(f"Agent file updated: {len(agent)} total records")

if __name__ == "__main__":
    main()
