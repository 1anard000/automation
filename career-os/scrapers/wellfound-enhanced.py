#!/usr/bin/env python3
"""
Wellfound (AngelList) enhanced job scraper via web_search.

Improved version of wellfound.py with broader query coverage,
better dedup, salary extraction, and more role types.

Usage (agent-driven):
  1. Run web_search queries (QUERIES below)
  2. Save results to wellfound-enhanced-websearch.json
  3. Run this script to generate wellfound-enhanced-results.json
"""
import json, os, re, sys
from datetime import datetime

OUTPUT = os.path.join(os.path.dirname(__file__), "wellfound-enhanced-results.json")

QUERIES = [
    'site:wellfound.com "senior product manager" Singapore OR "Hong Kong"',
    'site:wellfound.com "head of product" Singapore OR "Hong Kong"',
    'site:wellfound.com "director of product" Singapore OR "Hong Kong"',
    'site:wellfound.com "VP product" Singapore OR "Hong Kong"',
    'site:wellfound.com "product lead" Singapore OR "Hong Kong"',
    'site:wellfound.com "chief product officer" Asia',
    'site:wellfound.com "product manager" remote Asia',
    'site:wellfound.com "general manager" product Asia',
    'wellfound.com senior product manager Singapore startup jobs',
    'wellfound.com product director Hong Kong startup',
    'wellfound.com "head of product" Asia remote',
    'wellfound.com "VP product" Asia startup',
    'wellfound.com "product" senior APAC',
]

TITLE_KEYWORDS = [
    "product manager", "program manager", "strategy",
    "head of product", "director", "vp product", "chief product",
    "product lead", "principal", "senior", "staff",
    "cross-border", "e-commerce", "ecommerce", "growth",
    "general manager", "gm",
]

WEB_SEARCH_RESULTS = []


def is_relevant(title, snippet):
    text = f"{title} {snippet}".lower()
    has_role = any(kw in text for kw in TITLE_KEYWORDS)
    has_senior = any(kw in text for kw in [
        "senior", "director", "head", "vp", "principal", "lead",
        "chief", "general manager", "gm", "staff"
    ])
    return has_role and has_senior


def extract_location(title, snippet):
    text = f"{title} {snippet}".lower()
    if "singapore" in text:
        return "Singapore"
    if "hong kong" in text or "hongkong" in text:
        return "Hong Kong"
    if "shanghai" in text:
        return "Shanghai"
    if "shenzhen" in text:
        return "Shenzhen"
    if "remote" in text:
        return "Remote"
    if "asia" in text or "apac" in text:
        return "APAC"
    return ""


def extract_salary(title, snippet):
    """Try to extract salary from snippet."""
    text = f"{title} {snippet}"
    # Patterns: "$150K-$200K", "$150k - $200k", "150K-200K USD"
    m = re.search(r'\$?(\d{2,3}K?)\s*[-–~to]+\s*\$?(\d{2,3}K?)\s*(?:USD|SGD|HKD)?', text, re.I)
    if m:
        return f"${m.group(1)}-{m.group(2)}"
    return ""


def classify_grade(title):
    t = title.lower()
    if any(k in t for k in ["vp", "vice president", "c-level", "chief"]):
        return "S-1"
    if any(k in t for k in ["director", "head of"]):
        return "A-1"
    if any(k in t for k in ["principal", "staff"]):
        return "A-1"
    return "A-2"


def classify_role_type(title):
    t = title.lower()
    if "strategy" in t:
        return "Strategy/Ops"
    if "program" in t:
        return "Program Management"
    if "growth" in t:
        return "Growth"
    if "general manager" in t or " gm " in t:
        return "General Management"
    return "Product Management"


def process_results(results):
    """Process web_search results into structured job listings."""
    seen_urls = set()
    jobs = []

    for r in results:
        url = r.get("url", "")
        title = r.get("title", "")
        snippet = r.get("description", r.get("snippet", ""))

        if not url or not title:
            continue
        if "wellfound.com" not in url.lower():
            continue
        if url in seen_urls:
            continue
        if not is_relevant(title, snippet):
            continue

        seen_urls.add(url)

        # Clean title
        clean_title = re.sub(r'\s*(?:at|@)\s+[^-|–]+$', '', title).strip()
        clean_title = re.sub(r'\s*\|\s*Wellfound.*$', '', clean_title).strip()
        clean_title = re.sub(r'\s*-\s*Wellfound.*$', '', clean_title).strip()

        # Extract company from URL pattern: wellfound.com/company/name
        company = ""
        company_match = re.search(r'wellfound\.com/company/([^/]+)', url)
        if company_match:
            company = company_match.group(1).replace("-", " ").title()

        # Also try "Company is hiring" or "Company | Wellfound"
        if not company:
            co_match = re.match(r'^(.+?)(?:\s+(?:is hiring|jobs|careers))', title, re.I)
            if co_match:
                company = co_match.group(1).strip()

        salary = extract_salary(title, snippet)

        jobs.append({
            "title": clean_title,
            "company": company,
            "location": extract_location(title, snippet),
            "grade": classify_grade(clean_title),
            "url": url,
            "role_type": classify_role_type(clean_title),
            "salary": salary,
            "scanned_date": datetime.now().strftime("%Y-%m-%d"),
            "source": "wellfound-enhanced",
        })

    return jobs


def main():
    standalone_path = os.path.join(os.path.dirname(__file__), "wellfound-enhanced-websearch.json")
    results = []

    if os.path.exists(standalone_path):
        with open(standalone_path) as f:
            results = json.load(f)
        print(f"Loaded {len(results)} results from {standalone_path}")
    elif WEB_SEARCH_RESULTS:
        results = WEB_SEARCH_RESULTS
        print(f"Using {len(results)} embedded results")
    else:
        print("No web_search results found.")
        print("Queries to run:")
        for q in QUERIES:
            print(f"  - {q}")
        print(f"\nSave results to {standalone_path} and re-run.")
        return []

    jobs = process_results(results)
    print(f"\nWellfound Enhanced: {len(jobs)} jobs extracted")

    with open(OUTPUT, 'w') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    print(f"Saved to {OUTPUT}")
    return jobs


if __name__ == "__main__":
    main()
