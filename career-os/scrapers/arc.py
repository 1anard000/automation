#!/usr/bin/env python3
"""
Arc.dev job scraper via web_search.

Scrapes remote dev and PM jobs from Arc.dev.

Usage (agent-driven):
  1. Run web_search queries (QUERIES below)
  2. Save results to arc-websearch.json
  3. Run this script to generate arc-results.json
"""
import json, os, re, sys
from datetime import datetime

OUTPUT = os.path.join(os.path.dirname(__file__), "arc-results.json")

QUERIES = [
    'site:arc.dev "senior product manager" remote',
    'site:arc.dev "head of product" remote',
    'site:arc.dev "product director" remote',
    'site:arc.dev "VP product" remote',
    'arc.dev senior product manager remote jobs',
    'arc.dev product director APAC remote',
    'arc.dev "product manager" Singapore OR "Hong Kong"',
    'arc remote senior product leadership roles',
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
    if "hong kong" in text:
        return "Hong Kong"
    if "remote" in text:
        return "Remote"
    if "shanghai" in text:
        return "Shanghai"
    if "shenzhen" in text:
        return "Shenzhen"
    return "Remote"


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
        if "arc.dev" not in url.lower():
            continue
        if url in seen_urls:
            continue
        if not is_relevant(title, snippet):
            continue

        seen_urls.add(url)

        # Clean title
        clean_title = re.sub(r'\s*\|\s*Arc\.dev.*$', '', title).strip()
        clean_title = re.sub(r'\s*-\s*Arc\.dev.*$', '', clean_title).strip()

        company = ""
        if " at " in clean_title.lower():
            parts = re.split(r'\s+at\s+', clean_title, maxsplit=1)
            if len(parts) == 2:
                company = parts[1].strip()
                clean_title = parts[0].strip()

        jobs.append({
            "title": clean_title,
            "company": company,
            "location": extract_location(title, snippet),
            "grade": classify_grade(clean_title),
            "url": url,
            "role_type": classify_role_type(clean_title),
            "salary": "",
            "scanned_date": datetime.now().strftime("%Y-%m-%d"),
            "source": "arc",
        })

    return jobs


def main():
    standalone_path = os.path.join(os.path.dirname(__file__), "arc-websearch.json")
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
    print(f"\nArc.dev: {len(jobs)} jobs extracted")

    with open(OUTPUT, 'w') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    print(f"Saved to {OUTPUT}")
    return jobs


if __name__ == "__main__":
    main()
