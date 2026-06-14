#!/usr/bin/env python3
"""
Built In job scraper via web_search.

This script processes pre-fetched web_search results into structured job listings.

Usage (agent-driven):
  1. Run web_search queries via Hermes Agent (defined in QUERIES below)
  2. Feed results into process_results() or save to builtin-websearch.json
  3. Run this script to generate builtin-results.json
"""
import json, os, re, sys
from datetime import datetime

OUTPUT = os.path.join(os.path.dirname(__file__), "builtin-results.json")

QUERIES = [
    'site:builtin.com "senior product manager" "Hong Kong"',
    'site:builtin.com "senior product manager" Singapore',
    'site:builtin.com "product director" "Hong Kong" OR Singapore',
    'site:builtin.com "head of product" Singapore OR "Hong Kong"',
    'site:builtin.com "product manager" remote Asia',
]

TITLE_KEYWORDS = [
    "product manager", "program manager", "strategy",
    "head of product", "director", "vp product",
    "product lead", "principal", "senior", "staff",
    "cross-border", "e-commerce", "ecommerce", "growth",
]

WEB_SEARCH_RESULTS = []

def is_relevant(title, snippet):
    text = f"{title} {snippet}".lower()
    has_role = any(kw in text for kw in TITLE_KEYWORDS)
    return has_role

def extract_location(title, snippet):
    text = f"{title} {snippet}".lower()
    if "hong kong" in text:
        return "Hong Kong"
    if "singapore" in text:
        return "Singapore"
    if "remote" in text:
        return "Remote"
    return ""

def classify_role_type(title):
    t = title.lower()
    if "strategy" in t:
        return "Strategy/Ops"
    if "program" in t:
        return "Program Management"
    if "product" in t:
        return "Product Management"
    return "Product Management"

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
        if "builtin.com" not in url.lower():
            continue
        if url in seen_urls:
            continue
        if not is_relevant(title, snippet):
            continue
        
        seen_urls.add(url)
        
        # Clean title
        clean_title = title.strip()
        # Remove " | Built In" suffix
        clean_title = re.sub(r'\s*\|\s*Built\s*In.*$', '', clean_title)
        clean_title = re.sub(r'\s*-\s*Built\s*In.*$', '', clean_title)
        
        # Extract company from title (often "Company - Title | Built In")
        company = ""
        if " - " in clean_title:
            parts = clean_title.split(" - ", 1)
            if len(parts) == 2 and len(parts[0]) < 60:
                # Check if first part looks like a company
                candidate = parts[0].strip()
                if not any(kw in candidate.lower() for kw in ["senior", "junior", "lead", "director", "head", "vp"]):
                    company = candidate
                    clean_title = parts[1].strip()
        
        formatted.append({
            "title": clean_title,
            "company": company,
            "location": extract_location(title, snippet),
            "grade": "A-1" if any(k in clean_title.lower() for k in ["director", "vp", "head"]) else "A-2",
            "url": url,
            "role_type": classify_role_type(clean_title),
            "salary": "",
            "scanned_date": datetime.now().strftime("%Y-%m-%d"),
            "source": "builtin",
        })
    
    return formatted

def main():
    standalone_path = os.path.join(os.path.dirname(__file__), "builtin-websearch.json")
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
    print(f"\nBuilt In: {len(jobs)} jobs extracted")
    
    with open(OUTPUT, 'w') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    print(f"Saved to {OUTPUT}")
    return jobs

if __name__ == "__main__":
    main()
