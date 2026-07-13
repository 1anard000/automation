#!/usr/bin/env python3
import json, sys
from datetime import datetime, timedelta
from collections import Counter

with open("/Users/iancolrick/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json") as f:
    jobs = json.load(f)

today = datetime.now().strftime("%Y-%m-%d")
last_24h = datetime.now() - timedelta(hours=24)

# Filter out Amazon
jobs = [j for j in jobs if "amazon" not in j.get("company", "").lower() and "amazon" not in j.get("title", "").lower()]

total = len(jobs)

# Jobs by location
loc_counter = Counter()
for j in jobs:
    loc = j.get("location_norm", "") or j.get("location", "") or "Unknown"
    if not loc.strip():
        loc = "Unknown"
    loc_counter[loc.strip()] += 1

# Jobs by category
cat_counter = Counter()
for j in jobs:
    cat = j.get("category", "") or j.get("role_type", "") or "Other"
    if not cat.strip():
        cat = "Other"
    cat_counter[cat.strip()] += 1

# New jobs in last 24h
new_jobs = []
for j in jobs:
    sd = j.get("scanned_date", "")
    try:
        d = datetime.strptime(sd, "%Y-%m-%d")
        if d >= last_24h:
            new_jobs.append(j)
    except:
        pass

# Jobs with direct apply links
direct_link_count = sum(1 for j in jobs if j.get("has_direct_link") or j.get("has_direct_apply"))

# Status counts
status_counter = Counter(j.get("status", "unknown") for j in jobs)

# Score and rank
def score_job(j):
    score = j.get("quality_score", 0) or 0
    
    loc = (j.get("location_norm", "") or j.get("location", "")).lower()
    if "shenzhen" in loc: score += 20
    elif "hong kong" in loc: score += 15
    elif "guangzhou" in loc: score += 12
    elif "shanghai" in loc: score += 10
    elif "singapore" in loc: score += 8
    
    cat = (j.get("category", "") or j.get("role_type", "")).lower()
    if any(k in cat for k in ["product", "strategy", "growth", "bizops"]): score += 15
    elif any(k in cat for k in ["general_pm", "gm"]): score += 12
    
    if j.get("english_friendly"): score += 5
    if j.get("has_direct_link") or j.get("has_direct_apply"): score += 5
    if j.get("salary"): score += 5
    
    return score

# Rank all jobs
ranked = sorted(jobs, key=lambda j: (score_job(j), j.get("scanned_date", "")), reverse=True)

# Top 10
top10 = ranked[:10]

# Shenzhen picks
sz_picks = [j for j in ranked if "shenzhen" in (j.get("location_norm", "") or j.get("location", "")).lower()][:5]

# HK picks
hk_picks = [j for j in ranked if "hong kong" in (j.get("location_norm", "") or j.get("location", "")).lower()][:3]

# Applied jobs
applied = [j for j in jobs if j.get("status") in ("applied", "interviewing", "offer")]
applied_count = len(applied)

print(f"DATE:{today}")
print(f"TOTAL:{total}")
print(f"NEW_24H:{len(new_jobs)}")
print(f"DIRECT_LINKS:{direct_link_count}")
print(f"APPLIED:{applied_count}")

print("---LOCATIONS---")
for loc, cnt in loc_counter.most_common(15):
    print(f"{loc}|{cnt}")

print("---CATEGORIES---")
for cat, cnt in cat_counter.most_common(15):
    print(f"{cat}|{cnt}")

print("---STATUS---")
for st, cnt in status_counter.items():
    print(f"{st}|{cnt}")

print("---TOP10---")
for j in top10:
    title = j.get("en_title") or j.get("title", "?")
    company = j.get("company", "—")
    loc = j.get("location_norm", "") or j.get("location", "?")
    url = j.get("url", "")
    score = score_job(j)
    has_link = j.get("has_direct_link") or j.get("has_direct_apply")
    salary = j.get("salary", "")
    print(json.dumps({"t": title, "c": company, "l": loc, "u": url, "s": score, "dl": has_link, "sal": salary}))

print("---SHENZHEN---")
for j in sz_picks:
    title = j.get("en_title") or j.get("title", "?")
    company = j.get("company", "—")
    url = j.get("url", "")
    score = score_job(j)
    has_link = j.get("has_direct_link") or j.get("has_direct_apply")
    salary = j.get("salary", "")
    print(json.dumps({"t": title, "c": company, "u": url, "s": score, "dl": has_link, "sal": salary}))

print("---HONGKONG---")
for j in hk_picks:
    title = j.get("en_title") or j.get("title", "?")
    company = j.get("company", "—")
    url = j.get("url", "")
    score = score_job(j)
    salary = j.get("salary", "")
    print(json.dumps({"t": title, "c": company, "u": url, "s": score, "sal": salary}))

print("---NEW24H---")
for j in new_jobs[:10]:
    title = j.get("en_title") or j.get("title", "?")
    company = j.get("company", "—")
    loc = j.get("location_norm", "") or j.get("location", "?")
    url = j.get("url", "")
    score = score_job(j)
    print(json.dumps({"t": title, "c": company, "l": loc, "u": url, "s": score}))
