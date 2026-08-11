#!/usr/bin/env python3
"""Career OS Daily Brief Generator - v3 aligned with user preferences."""
import json
from datetime import datetime, timedelta
from collections import Counter

DB_PATH = "/Users/iancolrick/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json"
TODAY = datetime.now().strftime("%Y-%m-%d")
YESTERDAY = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

with open(DB_PATH, "r", encoding="utf-8") as f:
    jobs = json.load(f)

# Exclude Amazon per user preference
jobs = [j for j in jobs if "amazon" not in (j.get("company", "") + " " + j.get("title", "")).lower()]

TOTAL = len(jobs)
NEW_24H = sum(1 for j in jobs if j.get("scanned_date", "") >= YESTERDAY)
DIRECT_LINKS = sum(1 for j in jobs if j.get("has_direct_link") or j.get("has_direct_apply"))

# Location normalization and priority
LOC_PRIORITY = {"Shenzhen": 100, "Hong Kong": 90, "Guangzhou": 70, "Shanghai": 60, "Singapore": 50, "Remote": 40, "Unknown": 30}

def normalize_loc(loc):
    if not loc: return "Unknown"
    loc = loc.strip().split(",")[0].strip().lower()
    if loc in {"hk", "hongkong", "hong kong sar"}: return "Hong Kong"
    if loc in {"sz"}: return "Shenzhen"
    if loc in {"gz"}: return "Guangzhou"
    if loc in {"sh"}: return "Shanghai"
    if loc in {"sg", "sgp"}: return "Singapore"
    for k in ["shenzhen", "hong kong", "guangzhou", "shanghai", "singapore"]:
        if k in loc: return k.title().replace("Hong Kong", "Hong Kong")
    if "remote" in loc: return "Remote"
    return "Unknown"

for j in jobs:
    j["_loc"] = normalize_loc(j.get("location_norm", "") or j.get("location", ""))

loc_counts = Counter(j["_loc"] for j in jobs)
cat_counts = Counter(j.get("category", "") or j.get("role_type", "") or "other" for j in jobs)

# Target-profile filter
# Senior PM / Strategy / BizOps / Growth / GM, preferred locations, no Amazon.
# Per user preference #3, remove Director/VP/Head of/Chief from suggestions (too senior).
SENIOR_KW = ["senior", "gm", "general manager", "strategy", "strategic", "bizops", "business operations", "growth", "principal", "lead", "staff"]
EXCLUDE_TITLES = ["director", "head of", "vp", "vice president", "chief", "vice-president"]

def keep(j):
    title = (j.get("title") or "").lower()
    company = (j.get("company") or "").lower()
    if "amazon" in title or "amazon" in company: return False
    if j["_loc"] not in LOC_PRIORITY: return False
    if any(k in title for k in EXCLUDE_TITLES): return False
    role = (j.get("role_type") or "").lower()
    combined = title + " " + role
    return any(k in combined for k in SENIOR_KW)

filtered = [j for j in jobs if keep(j)]

def score(j):
    s = 0
    s += LOC_PRIORITY.get(j["_loc"], 30)
    title = (j.get("title") or "").lower()
    if "gm" in title or "general manager" in title: s += 45
    if "strategy" in title or "strategic" in title or "bizops" in title or "business operations" in title: s += 30
    if "growth" in title: s += 25
    if "senior product" in title or "senior pm" in title or "principal" in title or "staff" in title: s += 20
    if j.get("salary") and j.get("salary") not in ("", "Not listed"): s += 10
    if j.get("has_direct_link") or j.get("has_direct_apply"): s += 15
    qs = j.get("quality_score")
    if isinstance(qs, (int, float)): s += min(qs, 30)
    if j.get("scanned_date", "") >= YESTERDAY: s += 10
    return s

for j in filtered:
    j["_score"] = score(j)

filtered.sort(key=lambda x: x["_score"], reverse=True)

new_jobs = [j for j in filtered if j.get("scanned_date", "") >= YESTERDAY]
new_jobs.sort(key=lambda x: x["_score"], reverse=True)

# Use new 24h jobs if any fit; otherwise best overall target-profile matches.
if new_jobs:
    top10 = new_jobs[:10]
else:
    top10 = filtered[:10]

top_sz = [j for j in filtered if j["_loc"] == "Shenzhen"][:5]

status_updates = [j for j in jobs if j.get("status") and j.get("status") not in ("", "not_applied", "unknown")]

def link(j):
    url = j.get("url", "")
    if not url: return "(no link)"
    return url if url.startswith("http") else url

def fmt(j):
    comp = j.get("company") or "Unknown"
    title = j.get("title", "Untitled")
    direct = "✅" if (j.get("has_direct_link") or j.get("has_direct_apply")) else ""
    return f"{title} @ {comp} — {j['_loc']} {direct} — {link(j)}"

print(f"🎯 Career OS Daily Brief — {TODAY}")
print()
print(f"📊 Pipeline: {TOTAL} total | {NEW_24H} new (24h) | {DIRECT_LINKS} direct apply links")
print(f"- Location split: Shenzhen {loc_counts.get('Shenzhen',0)}, Hong Kong {loc_counts.get('Hong Kong',0)}, Singapore {loc_counts.get('Singapore',0)}, Shanghai {loc_counts.get('Shanghai',0)}, Guangzhou {loc_counts.get('Guangzhou',0)}, Remote {loc_counts.get('Remote',0)}, Unknown {loc_counts.get('Unknown',0)}")
print(f"- Category split: strategy {cat_counts.get('strategy',0)}, general_pm {cat_counts.get('general_pm',0)}, growth {cat_counts.get('growth',0)}, ops {cat_counts.get('ops',0)}, ai_product {cat_counts.get('ai_product',0)}, fintech {cat_counts.get('fintech',0)}, gm {cat_counts.get('gm',0)}")
print()
print("🏆 Top picks today:")
if not top10:
    print("No target-profile matches currently in pipeline.")
for i, j in enumerate(top10, 1):
    print(f"{i}. {fmt(j)}")
print()
print("📍 Best in Shenzhen:")
if not top_sz:
    print("No Shenzhen matches currently.")
for i, j in enumerate(top_sz, 1):
    print(f"{i}. {fmt(j)}")
print()
if status_updates:
    print(f"📝 Status updates: {len(status_updates)} tracked applications with non-default status.")
print()
print("📋 What to do today:")
if NEW_24H == 0:
    print("- Pipeline is stale: no jobs scanned in last 24h. Trigger a full scan (python3 scrapers/scan-all.py).")
else:
    direct_picks = [j for j in top10 if (j.get("has_direct_link") or j.get("has_direct_apply"))]
    if direct_picks:
        for j in direct_picks[:3]:
            comp = j.get("company") or "Unknown"
            print(f"- Apply to {j.get('title','')} @ {comp} ({j['_loc']}).")
    else:
        print("- Review top 3 picks and source direct apply URLs via LinkedIn/company careers page.")
if not top_sz:
    print("- Shenzhen pipeline is empty: run BOSS/Zhilian scan with Chinese PM keywords.")
if not status_updates:
    print("- No application status updates to review today.")
