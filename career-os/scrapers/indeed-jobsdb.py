#!/usr/bin/env python3
"""
Indeed & JobsDB job scraper via web_search.

This script processes pre-fetched web_search results into structured job listings.

Usage (agent-driven):
  1. Run web_search queries via Hermes Agent (defined in QUERIES below)
  2. Feed results into process_results() or save to indeed-jobsdb-websearch.json
  3. Run this script to generate indeed-jobsdb-results.json
"""
import json, os, re, sys
from datetime import datetime

OUTPUT = os.path.join(os.path.dirname(__file__), "indeed-jobsdb-results.json")

QUERIES = [
    'site:indeed.com "senior product manager" Singapore',
    'site:indeed.com "product director" Singapore',
    'site:indeed.com "head of product" Singapore',
    'site:indeed.com "senior product manager" "Hong Kong"',
    'site:indeed.com "product director" "Hong Kong"',
    'site:indeed.com "product manager" Shenzhen cross-border',
    'site:indeed.com "program manager" Singapore fintech',
    'site:jobsdb.com "senior product manager" "Hong Kong"',
    'site:jobsdb.com "product director" "Hong Kong"',
    'site:jobsdb.com "head of product" "Hong Kong"',
    'site:jobsdb.com "senior product manager" Singapore',
    'site:jobsdb.com "product director" Singapore',
    'site:jobsdb.com "strategy director" Singapore OR "Hong Kong"',
    'site:jobsdb.com "product manager" Shenzhen OR Guangzhou cross-border',
]

TITLE_KEYWORDS = [
    "product manager", "program manager", "strategy",
    "head of product", "director of product", "vp product",
    "product lead", "principal product", "senior product",
    "cross-border", "e-commerce", "ecommerce", "growth",
]

SENIORITY_KEYWORDS = [
    "senior", "sr.", "director", "head", "vp", "vice president",
    "lead", "principal", "staff", "manager", "chief",
]

WEB_SEARCH_RESULTS = []

def extract_source(url):
    u = url.lower()
    if "indeed.com" in u:
        return "indeed"
    if "jobsdb.com" in u:
        return "jobsdb"
    return "web_search"

def extract_company(title, url, snippet=""):
    # Try "at Company" pattern
    at_match = re.search(r'\s+(?:at|@)\s+([^|–\-]+?)(?:\s*[-|–]|\s*$)', title, re.IGNORECASE)
    if at_match:
        return at_match.group(1).strip()
    # Try "Title - Company" pattern
    dash_match = re.search(r'[-|–]\s*([^-|–]+?)$', title)
    if dash_match:
        c = dash_match.group(1).strip()
        if len(c) < 50 and not any(kw in c.lower() for kw in ["singapore", "hong kong", "remote", "shenzhen", "guangzhou", "shanghai"]):
            return c
    # Try from snippet "Company is hiring"
    hiring_match = re.search(r'^(.+?)\s+is\s+hiring', snippet, re.IGNORECASE)
    if hiring_match:
        return hiring_match.group(1).strip()
    return ""

def extract_location(title, snippet):
    text = f"{title} {snippet}".lower()
    locations = {
        "Singapore": ["singapore"],
        "Hong Kong": ["hong kong", "hongkong"],
        "Shenzhen": ["shenzhen"],
        "Guangzhou": ["guangzhou"],
        "Shanghai": ["shanghai"],
        "Remote": ["remote"],
    }
    for loc, kws in locations.items():
        if any(kw in text for kw in kws):
            return loc
    return ""

def is_relevant(title, snippet):
    text = f"{title} {snippet}".lower()
    has_role = any(kw in text for kw in TITLE_KEYWORDS)
    has_seniority = any(kw in text for kw in SENIORITY_KEYWORDS)
    return has_role and has_seniority

def classify_role_type(title):
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

def classify_grade(title):
    t = title.lower()
    if any(k in t for k in ["vp", "vice president", "c-level", "chief"]):
        return "S-1"
    if any(k in t for k in ["director", "head of"]):
        return "A-1"
    if any(k in t for k in ["principal", "staff"]):
        return "A-1"
    if "senior" in t or "sr." in t:
        return "A-2"
    return "A-2"

def process_results(results):
    """Process web_search results into structured job listings."""
    seen_urls = set()
    formatted = []
    
    for r in results:
        url = r.get("url", "")
        title = r.get("title", "")
        snippet = r.get("description", r.get("snippet", ""))
        
        if not url or not title:
            continue
        if url in seen_urls:
            continue
        
        # Filter: must be indeed.com or jobsdb.com
        source = extract_source(url)
        if source == "web_search":
            continue
        
        if not is_relevant(title, snippet):
            continue
        
        seen_urls.add(url)
        location = extract_location(title, snippet)
        company = extract_company(title, url, snippet)
        clean_title = re.sub(r'\s*(?:at|@)\s+[^-|–]+$', '', title).strip()
        clean_title = re.sub(r'\s*[-|–]\s*[^-|–]+$', '', clean_title).strip()
        
        formatted.append({
            "title": clean_title,
            "company": company,
            "location": location,
            "grade": classify_grade(clean_title),
            "url": url,
            "role_type": classify_role_type(clean_title),
            "salary": "",
            "scanned_date": datetime.now().strftime("%Y-%m-%d"),
            "source": source,
        })
    
    return formatted

def main():
    standalone_path = os.path.join(os.path.dirname(__file__), "indeed-jobsdb-websearch.json")
    results = []
    
    if os.path.exists(standalone_path):
        with open(standalone_path) as f:
            results = json.load(f)
        print(f"Loaded {len(results)} results from {standalone_path}")
    elif WEB_SEARCH_RESULTS:
        results = WEB_SEARCH_RESULTS
        print(f"Using {len(results)} embedded results")
    else:
        print("No web_search results found. Run web_search queries first.")
        print("Queries to run:")
        for q in QUERIES:
            print(f"  - {q}")
        print(f"\nSave results to {standalone_path} and re-run.")
        return []
    
    jobs = process_results(results)
    print(f"\nIndeed/JobsDB: {len(jobs)} jobs extracted")
    
    with open(OUTPUT, 'w') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    print(f"Saved to {OUTPUT}")
    return jobs

if __name__ == "__main__":
    main()
