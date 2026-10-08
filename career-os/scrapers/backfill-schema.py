#!/usr/bin/env python3
"""Backfill missing schema fields on master + agent records scanned today.
Idempotent. Also drops US-remote records from master that leaked through scan-all.
"""
import json
import hashlib
from pathlib import Path
from datetime import date

TODAY = date.today().isoformat()
MASTER = Path("/Users/iancolrick/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json")
AGENT = Path("/Users/iancolrick/.openclaw/workspace/career-os/scrapers/agent-discovered-jobs.json")

def normalize_location(loc: str) -> str:
    if not loc:
        return ""
    loc_l = loc.lower().strip()
    mapping = {
        "shenzhen": "Shenzhen",
        "hong kong": "Hong Kong",
        "guangzhou": "Guangzhou",
        "shanghai": "Shanghai",
        "singapore": "Singapore",
        "beijing": "Beijing",
        "hangzhou": "Hangzhou",
        "bangkok": "Bangkok",
        "tokyo": "Tokyo",
        "seoul": "Seoul",
        "taipei": "Taipei",
        "jakarta": "Jakarta",
        "manila": "Manila",
        "kuala lumpur": "Kuala Lumpur",
        "sydney": "Sydney",
        "melbourne": "Melbourne",
    }
    for key, val in mapping.items():
        if key in loc_l:
            return val
    if "remote" in loc_l:
        return "Remote"
    return loc.strip()

def is_us_remote(loc: str) -> bool:
    if not loc:
        return False
    loc_l = loc.lower()
    us_signals = [
        "remote - us", "remote - usa", "remote, us", "remote, united states",
        "san francisco", "new york", "seattle", "los angeles", "chicago",
        "boston", "austin", "denver", "atlanta", "miami", "portland",
        "california", "washington", "texas", "new york", "florida",
        "colorado", "oregon", "massachusetts", "georgia", "illinois",
        "united states", "usa", "u.s.", "us-remote", "us remote"
    ]
    return any(s in loc_l for s in us_signals)

def backfill_record(j: dict) -> bool:
    """Backfill a single record. Returns True if any field was changed."""
    changed = False
    if not j.get("status"):
        j["status"] = "not_applied"
        changed = True
    if not j.get("status_date"):
        j["status_date"] = j.get("scanned_date", TODAY)
        changed = True
    if not j.get("last_touch_date"):
        j["last_touch_date"] = j.get("scanned_date", TODAY)
        changed = True
    if not j.get("location_norm"):
        j["location_norm"] = normalize_location(j.get("location", ""))
        changed = True
    if "quality_score" not in j:
        j["quality_score"] = None
        changed = True
    if "quality_tier" not in j:
        j["quality_tier"] = ""
        changed = True
    if "low_quality" not in j:
        j["low_quality"] = False
        changed = True
    if "category" not in j:
        j["category"] = "other"
        changed = True
    if not j.get("job_id"):
        key = (j.get("url", "") + j.get("title", "")).encode("utf-8")
        j["job_id"] = hashlib.sha1(key).hexdigest()[:12]
        changed = True
    if "english_friendly" not in j:
        j["english_friendly"] = True
        changed = True
    if "has_direct_link" not in j:
        url = j.get("url", "")
        j["has_direct_link"] = bool(url and "zhaopin" not in url and "zhipin.com/zhaopin" not in url)
        changed = True
    if "url_type" not in j:
        url = j.get("url", "")
        if "job_detail" in url or "jobdetail" in url or "greenhouse" in url or "ashby" in url:
            j["url_type"] = "direct"
        else:
            j["url_type"] = "search"
        changed = True
    return changed

def main():
    with open(MASTER) as f:
        master = json.load(f)
    with open(AGENT) as f:
        agent = json.load(f)

    # Drop US-remote from master today
    before = len(master)
    master = [j for j in master if not (j.get("scanned_date") == TODAY and is_us_remote(j.get("location", "")))]
    dropped_us = before - len(master)

    changed_master = 0
    for j in master:
        if j.get("scanned_date") == TODAY:
            if backfill_record(j):
                changed_master += 1

    changed_agent = 0
    for j in agent:
        if j.get("scanned_date") == TODAY:
            if backfill_record(j):
                changed_agent += 1

    with open(MASTER, "w") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)
    with open(AGENT, "w") as f:
        json.dump(agent, f, indent=2, ensure_ascii=False)

    print(f"Master: dropped {dropped_us} US-remote, backfilled {changed_master} records")
    print(f"Agent: backfilled {changed_agent} records")

if __name__ == "__main__":
    main()
