#!/usr/bin/env python3
"""
Greenhouse job board scraper.
Scrapes public Greenhouse API for Senior PM/Strategy roles in target locations.
"""
import json, sys, os, re, time
from urllib.request import urlopen, Request
from urllib.error import URLError
from datetime import datetime

# Companies with Greenhouse boards — verified to have APAC roles
COMPANIES = [
    # === APAC HQ / Major APAC presence ===
    "agoda",                    # Travel, SG/BKK — 12 APAC roles
    "okx",                      # Crypto exchange, HK — 225 APAC roles
    "flexport",                 # Logistics, SZ/SG — 16 APAC roles
    "coupang",                  # E-commerce, SH/Seoul — 20 APAC roles
    "bitmex",                   # Crypto, HK — 4 APAC roles

    # === Global with strong APAC offices ===
    "stripe",                   # Payments, SG/JP — 117 APAC roles
    "coinbase",                 # Crypto, SG — 117 APAC roles
    "databricks",               # Data/AI, SG — 81 APAC roles
    "twilio",                   # Comms, SG — 159 APAC roles
    "anthropic",                # AI, SG — 41 APAC roles
    "vercel",                   # Dev tools — 20 APAC roles
    "postman",                  # API tools, SG — 12 APAC roles
    "figma",                    # Design, SG — 6 APAC roles
    "cloudflare",               # Infra, SG — 3 APAC roles
]

# Location filters
LOCATIONS = ["hong kong", "singapore", "shenzhen", "guangzhou", "shanghai", "beijing", "remote"]

# Title keywords that match [CANDIDATE]'s profile
TITLE_KEYWORDS = [
    "product manager", "program manager", "strategy",
    "head of product", "director of product", "vp product",
    "product lead", "product director", "principal product",
    "senior product", "staff product", "group product",
    "cross-border", "e-commerce", "ecommerce", "marketplace",
    "business strategy", "corporate strategy", "growth",
]

def fetch_json(url, timeout=15, retries=2):
    """Fetch JSON from URL with retry."""
    import random
    for attempt in range(retries + 1):
        try:
            req = Request(url, headers={"User-Agent": "CareerOS/1.0"})
            with urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (URLError, json.JSONDecodeError, OSError) as e:
            if attempt < retries:
                time.sleep(2 + random.uniform(0, 1))
            else:
                print(f"  [WARN] Failed to fetch {url}: {e}", file=sys.stderr)
                return None

def location_matches(loc_name):
    """Check if location matches target regions."""
    loc = loc_name.lower()
    return any(kw in loc for kw in LOCATIONS)

def title_matches(title):
    """Check if title matches target roles."""
    t = title.lower()
    return any(kw in t for kw in TITLE_KEYWORDS)

def classify_role_type(title):
    """Classify role type from title."""
    t = title.lower()
    if "strategy" in t or "strategic" in t:
        return "Strategy/Ops"
    if "program" in t:
        return "Program Management"
    if "product" in t:
        return "Product Management"
    if "growth" in t:
        return "Growth"
    return "Product Management"

def scrape_company(company):
    """Scrape jobs from a single Greenhouse company board."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"
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

        jobs.append({
            "title": title,
            "company": job.get("company_name", company.title()),
            "location": loc,
            "grade": "A-1" if any(k in title.lower() for k in ["director", "vp", "head", "principal"]) else "A-2",
            "url": job.get("absolute_url", ""),
            "role_type": classify_role_type(title),
            "salary": "",
            "scanned_date": datetime.now().strftime("%Y-%m-%d"),
            "source": "greenhouse",
        })
    return jobs

def main():
    print(f"Greenhouse scraper: scanning {len(COMPANIES)} companies...")
    all_jobs = []
    for company in COMPANIES:
        print(f"  Scanning {company}...")
        jobs = scrape_company(company)
        all_jobs.extend(jobs)
        print(f"    Found {len(jobs)} matching jobs")

    print(f"\nGreenhouse total: {len(all_jobs)} jobs")

    output_path = os.path.join(os.path.dirname(__file__), "greenhouse-results.json")
    with open(output_path, "w") as f:
        json.dump(all_jobs, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")
    return all_jobs

if __name__ == "__main__":
    main()
