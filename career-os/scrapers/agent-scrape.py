#!/usr/bin/env python3
"""
Career OS Agent Scraper — 2026-07-22
Scrapes Greenhouse API boards for APAC PM/Strategy/Growth roles.
Deduplicates against existing jobs.
"""
import json, os, sys, time, hashlib
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────────────
WORKSPACE = "/Users/iancolrick/.openclaw/workspace/career-os"
SCRAPER_DIR = os.path.join(WORKSPACE, "scrapers")
EXISTING_JOBS_PATH = os.path.join(WORKSPACE, "OKComputer_职位搜索清单/jobs-all.json")
AGENT_DISCOVERED_PATH = os.path.join(SCRAPER_DIR, "agent-discovered-jobs.json")
GREENHOUSE_RESULTS_PATH = os.path.join(SCRAPER_DIR, "greenhouse-results.json")

# Greenhouse boards to scrape (verified productive from China)
GREENHOUSE_BOARDS = [
    # Tier 1 — always scrape
    "okx", "stripe", "coinbase", "twilio", "databricks", "anthropic",
    # Tier 2 — periodic
    "flexport", "postman", "figma", "cloudflare", "bitmex", "xendit",
    "bybit", "airbnb", "agoda", "coupang",
    # Additional verified boards
    "braze", "sendbird", "payoneer", "gemini",
    # Newly added (may have APAC PM roles)
    "rippling", "deel", "notion", "canva", "atlassian", "wise",
    "ramp", "linear", "posthog", "retool", "mercury", "vercel",
    "openai", "samsara", "toast", "duolingo", "gitlab",
]

# APAC location keywords
APAC_LOCATIONS = [
    "singapore", "hong kong", "shenzhen", "guangzhou", "shanghai",
    "beijing", "taipei", "tokyo", "seoul", "bangkok", "apac",
    "asia pacific", "china", "hong kong sar", "malaysia", "kuala lumpur",
]

# Title keywords matching candidate profile
TITLE_KEYWORDS = [
    "product manager", "product lead", "strategy", "growth",
    "program manager", "bizops", "business operations",
    "general manager", "marketing strategy", "strategic",
    "product operations", "go-to-market", "gtm", "partnerships",
    "product specialist", "product marketing", "cross-border",
    "e-commerce", "ecommerce", "marketplace", "business strategy",
    "corporate strategy", "product analyst",
]

# Exclude keywords (too senior or wrong function)
EXCLUDE_KEYWORDS = [
    "director", "vp", "vice president", "chief", "head of",
    "intern", "internship", "staff+", "distinguished",
    "engineer", "data scientist", "designer", "ux designer",
    "recruiter", "talent", "coordinator", "analyst",
    "research", "scientist", "architect", "developer",
]

TODAY = datetime.now().strftime("%Y-%m-%d")


def fetch_json(url, timeout=20, retries=2):
    """Fetch JSON from URL with retry."""
    import random
    for attempt in range(retries + 1):
        try:
            req = Request(url, headers={"User-Agent": "CareerOS/2.0"})
            with urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (URLError, HTTPError, json.JSONDecodeError, OSError) as e:
            if attempt < retries:
                time.sleep(2 + random.uniform(0, 1))
            else:
                print(f"  [WARN] Failed: {url} — {e}", file=sys.stderr)
                return None


def location_matches(loc_name):
    loc = loc_name.lower()
    return any(kw in loc for kw in APAC_LOCATIONS)


def title_matches(title):
    t = title.lower()
    return any(kw in t for kw in TITLE_KEYWORDS)


def title_excluded(title):
    t = title.lower()
    return any(kw in t for kw in EXCLUDE_KEYWORDS)


def classify_role_type(title):
    t = title.lower()
    if "strategy" in t or "strategic" in t:
        return "Strategy/Ops"
    if "program" in t:
        return "Program Management"
    if "growth" in t:
        return "Growth"
    if "product" in t:
        return "Product Management"
    return "General"


def make_job_id(url, title):
    """Create deterministic job ID from URL + title."""
    raw = f"{url}|{title}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def scrape_greenhouse(board):
    """Scrape a single Greenhouse board."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
    data = fetch_json(url)
    if not data or "jobs" not in data:
        return []

    jobs = []
    for job in data["jobs"]:
        loc = job.get("location", {}).get("name", "")
        title = job.get("title", "")

        if not location_matches(loc):
            continue
        if not title_matches(title):
            continue
        if title_excluded(title):
            continue

        abs_url = job.get("absolute_url", f"https://job-boards.greenhouse.io/{board}/jobs/{job['id']}")

        jobs.append({
            "title": title,
            "company": board.replace("-", " ").title(),
            "location": loc,
            "url": abs_url,
            "salary": "",
            "source": "greenhouse-api",
            "scanned_date": TODAY,
            "job_id": make_job_id(abs_url, title),
            "status": "not_applied",
            "status_date": TODAY,
            "last_touch_date": TODAY,
            "role_type": classify_role_type(title),
            "english_friendly": True,
            "has_direct_link": True,
            "url_type": "direct",
            "quality_score": None,
            "quality_tier": "",
            "low_quality": False,
        })
    return jobs


def load_existing_urls(jobs_path):
    """Load existing job URLs and titles for dedup."""
    urls = set()
    titles = set()
    if os.path.exists(jobs_path):
        try:
            with open(jobs_path) as f:
                data = json.load(f)
            for job in data:
                urls.add(job.get("url", ""))
                titles.add(job.get("title", "").lower().strip())
        except Exception as e:
            print(f"  [WARN] Could not load {jobs_path}: {e}", file=sys.stderr)
    return urls, titles


def main():
    print(f"=== Career OS Agent Scraper — {TODAY} ===")
    print(f"Scanning {len(GREENHOUSE_BOARDS)} Greenhouse boards...\n")

    # Load existing jobs for dedup
    existing_urls, existing_titles = load_existing_urls(EXISTING_JOBS_PATH)
    agent_urls, agent_titles = load_existing_urls(AGENT_DISCOVERED_PATH)
    all_urls = existing_urls | agent_urls
    all_titles = existing_titles | agent_titles

    print(f"Existing jobs: {len(existing_urls)} URLs, {len(agent_urls)} agent-discovered")
    print(f"Total dedup set: {len(all_urls)} URLs\n")

    # Scrape all boards
    all_new_jobs = []
    boards_with_jobs = []
    boards_failed = []

    for i, board in enumerate(GREENHOUSE_BOARDS, 1):
        print(f"[{i}/{len(GREENHOUSE_BOARDS)}] {board}...", end=" ", flush=True)
        jobs = scrape_greenhouse(board)
        new_jobs = []
        for job in jobs:
            if job["url"] not in all_urls:
                new_jobs.append(job)
                all_urls.add(job["url"])

        if new_jobs:
            all_new_jobs.extend(new_jobs)
            boards_with_jobs.append(f"{board}({len(new_jobs)})")
            print(f"✓ {len(new_jobs)} new")
        elif jobs:
            print(f"— {len(jobs)} found, all dupes")
        else:
            boards_failed.append(board)
            print("✗ no matches")

        time.sleep(0.5)  # Rate limit

    # Save results
    print(f"\n{'='*60}")
    print(f"NEW JOBS FOUND: {len(all_new_jobs)}")
    print(f"Boards with new jobs: {', '.join(boards_with_jobs) if boards_with_jobs else 'none'}")
    print(f"Boards with no matches: {len(boards_failed)}")

    # Load existing agent-discovered jobs
    existing_agent = []
    if os.path.exists(AGENT_DISCOVERED_PATH):
        try:
            with open(AGENT_DISCOVERED_PATH) as f:
                existing_agent = json.load(f)
        except:
            pass

    # Merge new jobs with existing agent-discovered
    combined = existing_agent + all_new_jobs
    # Final dedup by URL
    seen = set()
    deduped = []
    for job in combined:
        if job["url"] not in seen:
            seen.add(job["url"])
            deduped.append(job)

    os.makedirs(SCRAPER_DIR, exist_ok=True)
    with open(AGENT_DISCOVERED_PATH, "w") as f:
        json.dump(deduped, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(deduped)} total jobs to {AGENT_DISCOVERED_PATH}")

    # Also update greenhouse-results.json with latest raw results
    with open(GREENHOUSE_RESULTS_PATH, "w") as f:
        json.dump(all_new_jobs, f, indent=2, ensure_ascii=False)
    print(f"Saved raw results to {GREENHOUSE_RESULTS_PATH}")

    # Print top new jobs summary
    if all_new_jobs:
        print(f"\n{'='*60}")
        print("TOP NEW JOBS:")
        for job in all_new_jobs[:20]:
            print(f"  • {job['title']} @ {job['company']} — {job['location']}")
            print(f"    {job['url']}")

    return all_new_jobs


if __name__ == "__main__":
    main()
