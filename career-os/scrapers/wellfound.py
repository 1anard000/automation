#!/usr/bin/env python3
"""
Wellfound (AngelList) job scraper via web_search.

This script processes pre-fetched web_search results into structured job listings.

Usage (agent-driven):
  1. Run web_search queries via Hermes Agent (defined in QUERIES below)
  2. Feed results into process_results() or save to wellfound-websearch.json
  3. Run this script to generate wellfound-results.json
"""
import json, os, re, sys
from datetime import datetime

OUTPUT = os.path.join(os.path.dirname(__file__), "wellfound-results.json")

QUERIES = [
    'site:wellfound.com "product manager" Singapore OR "Hong Kong"',
    'site:wellfound.com "senior product manager" Asia',
    'site:wellfound.com "director of product" Singapore',
    'site:wellfound.com "head of product" Singapore OR "Hong Kong"',
    'site:wellfound.com "product lead" Singapore',
]

TITLE_KEYWORDS = [
    "product manager", "program manager", "strategy",
    "head of product", "director", "vp product",
    "product lead", "principal", "senior",
    "cross-border", "e-commerce", "ecommerce", "growth",
]

WEB_SEARCH_RESULTS = []

def is_relevant(title, snippet):
    text = f"{title} {snippet}".lower()
    has_pm = any(kw in text for kw in TITLE_KEYWORDS)
    has_senior = any(kw in text for kw in ["senior", "director", "head", "vp", "principal", "lead", "manager"])
    return has_pm and has_senior

def extract_location(title, snippet):
    text = f"{title} {snippet}".lower()
    if "singapore" in text:
        return "Singapore"
    if "hong kong" in text or "hongkong" in text:
        return "Hong Kong"
    if "shenzhen" in text:
        return "Shenzhen"
    if "remote" in text:
        return "Remote"
    return ""

def classify_role_type(title):
    t = title.lower()
    if "strategy" in t:
        return "Strategy/Ops"
    if "program" in t:
        return "Program Management"
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
        if "wellfound.com" not in url.lower():
            continue
        if url in seen_urls:
            continue
        if not is_relevant(title, snippet):
            continue
        
        seen_urls.add(url)
        
        # Clean title
        clean_title = re.sub(r'\s*(?:at|@)\s+[^-|–]+$', '', title).strip()
        
        # Extract company from URL pattern: wellfound.com/company/name
        company = ""
        company_match = re.search(r'wellfound\.com/company/([^/]+)', url)
        if company_match:
            company = company_match.group(1).replace("-", " ").title()
        
        formatted.append({
            "title": clean_title,
            "company": company,
            "location": extract_location(title, snippet),
            "grade": "A-1" if any(k in clean_title.lower() for k in ["director", "vp", "head"]) else "A-2",
            "url": url,
            "role_type": classify_role_type(clean_title),
            "salary": "",
            "scanned_date": datetime.now().strftime("%Y-%m-%d"),
            "source": "wellfound",
        })
    
    return formatted

def main():
    standalone_path = os.path.join(os.path.dirname(__file__), "wellfound-websearch.json")
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
    print(f"\nWellfound: {len(jobs)} jobs extracted")
    
    with open(OUTPUT, 'w') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    print(f"Saved to {OUTPUT}")
    return jobs

if __name__ == "__main__":
    main()
