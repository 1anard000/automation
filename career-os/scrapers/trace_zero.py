#!/usr/bin/env python3
"""Replay scan-all.py's exact dedup + quality gate against current result files
to determine whether 0-new-jobs is 'pipeline healthy' or a bug."""
import json, re, os, sys
from collections import Counter
from datetime import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOBS_FILE = os.path.join(WORKSPACE, "OKComputer_职位搜索清单", "jobs-all.json")
SCRAPERS_DIR = os.path.dirname(os.path.abspath(__file__))

SCRAPERS = [
    ("greenhouse", "greenhouse.py"),
    ("ashby", "ashby.py"),
    ("builtin", "builtin.py"),
    ("indeed-jobsdb", "indeed-jobsdb.py"),
    ("liepin", "liepin.py"),
    ("boss-zhilian-discovery", "boss-zhilian-discovery.py"),
    ("boss-zhilian-import", "boss-zhilian-import.py"),
    ("wellfound", "wellfound.py"),
    ("websearch", "websearch.py"),
    ("company_careers", "company_careers.py"),
    ("wellfound-enhanced", "wellfound-enhanced.py"),
]
EXTRA_RESULTS = ["diversified"]

_USER_MIN_YOE = 8
_USER_MAX_YOE = 15

def dedup_key(job):
    title = job.get("title", "").strip().lower()
    company = job.get("company", "").strip().lower()
    title = " ".join(title.split())
    company = " ".join(company.split())
    return f"{title}||{company}"

def url_key(job):
    return job.get("url", "").strip().rstrip("/").lower()

def text_for_job(job):
    return " ".join([
        str(job.get("title", "")),
        str(job.get("company", "")),
        str(job.get("location", "")),
        str(job.get("role_type", "")),
        str(job.get("notes", "")),
        str(job.get("category", "")),
        str(job.get("source", "")),
    ]).lower()

_NEGATIVE = [
    "sales", "marketing", "hr", "human resources", "finance", "accounting",
    "software engineer", "swe ", "frontend", "backend", "design", "ux", "ui",
    "graphic", "data scientist", "data engineer", "recruiter",
]
_SALARY_FLOOR = {
    "hong kong": 60000, "hong kong sar": 60000, "hk": 60000,
    "singapore": 10000, "sg": 10000,
    "shenzhen": 90000, "guangzhou": 90000, "shanghai": 90000,
}
_PURE_CRYPTO_PATTERNS = [
    "bitcoin", "btc", "ethereum", "eth", "solana", "defi", "dex",
    "token economics", "tokenomics", "crypto exchange", "on-chain", "layer2",
    "layer 2", "web3 trading", "crypto trading", "trading bot", "market maker crypto",
    "airdrop", "ico", "ido", "nft", "wallet product", "blockchain protocol",
]
_FINTECH_KEEP_PATTERNS = [
    "payments", "payment", "neobank", "banking", "cards", "treasury", "kyc", "aml",
    "capital markets", "equities", "lending", "remittance", "fx", "forex",
    "cross-border payments", "billing", "merchant", "issuing", "stablecoin payments",
    "digital asset custody", "digital payments", "ledger", "settlement", "compliance",
]

def _salary_value(job):
    try:
        salary = job.get("salary")
        if not salary:
            return None
        m = re.search(r"([\d,]+)", str(salary).replace(",", ""))
        return int(m.group(1)) if m else None
    except Exception:
        return None

def _quality_block_reason(job):
    text = text_for_job(job)
    for kw in _NEGATIVE:
        if kw in text:
            return f"wrong-domain:{kw}"
    salary = _salary_value(job)
    if salary is not None:
        loc = (job.get("location", "") or "").lower()
        floor = next((v for k, v in _SALARY_FLOOR.items() if k in loc), None)
        if floor is not None and salary < floor:
            return f"below-floor:{salary}<{floor}"
    has_crypto = any(p in text for p in _PURE_CRYPTO_PATTERNS)
    has_keep = any(p in text for p in _FINTECH_KEEP_PATTERNS)
    if has_crypto and not has_keep:
        return "purely-crypto"
    return None

def _parse_yoe(title, notes=''):
    text = f"{title} {notes}".lower()
    m = re.search(r"(\d+)\s*[-–—]\s*(\d+)\s*(?:年|years?|yoe)", text)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"(\d+)\s*\+\s*(?:年|years?|yoe)", text)
    if m:
        return int(m.group(1)), int(m.group(1)) + 5
    if any(k in text for k in ["senior", "sr.", "sr "]):
        return (5, 12)
    if any(k in text for k in ["staff", "principal"]):
        return (8, 15)
    if "lead" in text:
        return (7, 12)
    return None

def load_results(name):
    p = os.path.join(SCRAPERS_DIR, f"{name}-results.json")
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return json.load(f)

# Load master
with open(JOBS_FILE) as f:
    existing = json.load(f)
existing_tc = set()
existing_urls = set()
for j in existing:
    existing_tc.add(dedup_key(j))
    u = url_key(j)
    if u:
        existing_urls.add(u)
print(f"Master: {len(existing)} jobs")

# Concat all results in scan-all order
all_new = []
for name, _ in SCRAPERS:
    rs = load_results(name)
    for j in rs:
        j['_scraper'] = name
    all_new.extend(rs)
    if rs:
        print(f"  {name}: {len(rs)}")
for name in EXTRA_RESULTS:
    rs = load_results(name)
    for j in rs:
        j['_scraper'] = name
    all_new.extend(rs)
    if rs:
        print(f"  {name}: {len(rs)}")

print(f"\nTotal raw: {len(all_new)}")

# Replay
counts = Counter()
new_survivors = []
seen_tc = set(existing_tc)
seen_urls = set(existing_urls)

for job in all_new:
    tc = dedup_key(job)
    if tc in seen_tc:
        counts['tc_dup'] += 1
        continue
    u = url_key(job)
    if u and u in seen_urls:
        counts['url_dup'] += 1
        continue
    reason = _quality_block_reason(job)
    if reason:
        counts[f'quality:{reason.split(":")[0]}'] += 1
        # Print specific false-positive-prone blocks
        if reason.startswith('wrong-domain:'):
            kw = reason.split(':', 1)[1]
            title = job.get('title', '')
            if kw in title.lower():
                print(f"    [FP-CHECK] title contains '{kw}': {title[:80]} | company={job.get('company','')[:30]}")
        continue
    seen_tc.add(tc)
    if u:
        seen_urls.add(u)
    rng = _parse_yoe(job.get('title', ''), job.get('notes', ''))
    if rng is not None:
        lo, hi = rng
        if lo > _USER_MAX_YOE:
            counts['yoe_too_senior'] += 1
            continue
    counts['NEW'] += 1
    new_survivors.append(job)

print(f"\n=== Replay Results ===")
for k, v in counts.most_common(30):
    print(f"  {k}: {v}")

# Check APAC among survivors
apac_kw = ['shenzhen', 'hong kong', 'guangzhou', 'shanghai', 'singapore', 'apac', 'asia pacific', 'bangkok', 'tokyo', 'seoul', 'taipei', 'jakarta', 'kuala lumpur', 'manila']
apac = [j for j in new_survivors if any(k in (j.get('location','') or '').lower() for k in apac_kw)]
print(f"\nAPAC survivors: {len(apac)}")
for j in apac[:30]:
    print(f"  [{j['_scraper']}] {j.get('title','')[:60]} | {j.get('company','')[:25]} | {j.get('location','')[:30]}")

# Sample of quality blocks to identify false positives
print(f"\n=== Sample quality-blocked (first 10) ===")
blocked = [j for j in all_new if not _quality_block_reason(j) is None]
for j in all_new[:500]:
    r = _quality_block_reason(j)
    if r:
        print(f"  [{j['_scraper']}] {r}: {j.get('title','')[:60]} | {j.get('company','')[:25]}")
