#!/usr/bin/env python3
"""
Clean agent-discovered-jobs.json:
- Remove duplicate records within the file.
- Remove records whose URL or job_id already exists in jobs-all.json (master is source of truth).
Prints a concise summary.
"""
import json
import os
from collections import Counter

AGENT_PATH = "/Users/iancolrick/.openclaw/workspace/career-os/scrapers/agent-discovered-jobs.json"
MASTER_PATH = "/Users/iancolrick/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json"


def load(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"warn reading {path}: {e}")
            return []


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    agent = load(AGENT_PATH)
    master = load(MASTER_PATH)
    master_keys = set()
    for j in master:
        if j.get("url"):
            master_keys.add(j["url"].strip())
        if j.get("job_id"):
            master_keys.add(j["job_id"])

    seen = set()
    unique = []
    dupes_within = 0
    cross_dupes = 0
    for j in agent:
        url = j.get("url", "").strip()
        jid = j.get("job_id", "")
        key = (url, jid)
        if key in seen:
            dupes_within += 1
            continue
        if url in master_keys or jid in master_keys:
            cross_dupes += 1
            continue
        seen.add(key)
        unique.append(j)

    if dupes_within or cross_dupes:
        save(AGENT_PATH, unique)

    print(
        f"agent-discovered: {len(agent)} -> {len(unique)} "
        f"(removed {dupes_within} internal dupes, {cross_dupes} master dupes)"
    )

    today = max((j.get("scanned_date", "") for j in unique), default="")
    today_jobs = [j for j in unique if j.get("scanned_date") == today]
    print(f"Latest scan date: {today}, records: {len(today_jobs)}")
    if today_jobs:
        print("By source:")
        for src, cnt in Counter(j.get("source", "unknown") for j in today_jobs).most_common():
            print(f"  {src}: {cnt}")


if __name__ == "__main__":
    main()
