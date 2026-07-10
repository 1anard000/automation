#!/usr/bin/env python3
"""
Ashby job board scraper.
Uses curl (not urllib) since Ashby API can be slow/unreliable via Python urllib in China.
"""
import json, sys, os, re, subprocess, time
from datetime import datetime

# Companies with Ashby boards
COMPANIES = [
    "flexport", "notion", "ramp", "vercel", "linear", "retool",
    "mercury", "rippling", "deel", "snyk", "posthog",
]

LOCATIONS = ["hong kong", "singapore", "shenzhen", "guangzhou", "shanghai",
             "beijing", "remote", "tokyo", "taipei"]

TITLE_KEYWORDS = [
    "product manager", "program manager", "strategy",
    "head of product", "director of product", "vp product",
    "product lead", "product director", "principal product",
    "senior product", "staff product", "group product",
    "cross-border", "e-commerce", "ecommerce", "marketplace",
    "business strategy", "corporate strategy", "growth",
    "business operations", "bizops", "chief of staff",
    "general manager", "country manager",
]


def fetch_json_curl(url, timeout=30):
    """Fetch JSON using curl with file-based output (avoids pipe buffer issues with large responses)."""
    import tempfile
    tmpfile = tempfile.mktemp(suffix='.json')
    try:
        result = subprocess.run(
            ["curl", "-s", "--connect-timeout", "8", "--max-time", str(timeout),
             url, "-o", tmpfile],
            capture_output=True, text=True, timeout=timeout + 10
        )
        if not os.path.exists(tmpfile) or os.path.getsize(tmpfile) == 0:
            return None
        with open(tmpfile) as f:
            return json.load(f)
    except (json.JSONDecodeError, subprocess.TimeoutExpired, Exception) as e:
        return None
    finally:
        try:
            os.unlink(tmpfile)
        except OSError:
            pass


def location_matches(loc_name):
    loc = loc_name.lower()
    return any(kw in loc for kw in LOCATIONS)


def title_matches(title):
    t = title.lower()
    return any(kw in t for kw in TITLE_KEYWORDS)


def classify_role_type(title):
    t = title.lower()
    if "chief of staff" in t: return "Chief of Staff"
    if "business operations" in t or "bizops" in t: return "Business Operations"
    if "strategy" in t or "strategic" in t: return "Strategy/Ops"
    if "general manager" in t or "country manager" in t: return "General Manager"
    if "growth" in t: return "Growth"
    if "product" in t: return "Product Management"
    if "program" in t: return "Program Management"
    return "Other"


def scrape_company(company):
    """Scrape jobs from a single Ashby company board using curl."""
    url = f"https://api.ashbyhq.com/posting-api/job-board/{company}"
    data = fetch_json_curl(url)
    if not data:
        return []

    jobs_list = data if isinstance(data, list) else data.get("jobs", [])
    jobs = []
    for job in jobs_list:
        loc = ""
        if isinstance(job.get("location"), str):
            loc = job["location"]
        elif isinstance(job.get("location"), dict):
            loc = job["location"].get("name", "")
        elif "primaryLocation" in job:
            loc = str(job["primaryLocation"])

        title = job.get("title", "")
        if not location_matches(loc):
            continue
        if not title_matches(title):
            continue

        apply_url = job.get("applyUrl") or job.get("absolute_url") or ""
        if not apply_url:
            job_id = job.get("id", "")
            apply_url = f"https://jobs.ashbyhq.com/{company}/{job_id}"

        jobs.append({
            "title": title,
            "company": company.replace("-", " ").title(),
            "location": loc,
            "grade": "A-1" if any(k in title.lower()
                                  for k in ["director", "vp", "head", "principal"])
                     else "A-2",
            "url": apply_url,
            "role_type": classify_role_type(title),
            "salary": "",
            "scanned_date": datetime.now().strftime("%Y-%m-%d"),
            "source": "ashby",
        })
    return jobs


def main():
    print(f"Ashby scraper: scanning {len(COMPANIES)} companies...")
    all_jobs = []
    for company in COMPANIES:
        print(f"  Scanning {company}...")
        jobs = scrape_company(company)
        all_jobs.extend(jobs)
        print(f"    Found {len(jobs)} matching jobs")
        time.sleep(0.5)

    print(f"\nAshby total: {len(all_jobs)} jobs")

    output_path = os.path.join(os.path.dirname(__file__), "ashby-results.json")
    with open(output_path, "w") as f:
        json.dump(all_jobs, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")
    return all_jobs


if __name__ == "__main__":
    main()
