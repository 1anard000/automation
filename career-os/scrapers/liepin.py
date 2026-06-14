#!/usr/bin/env python3
"""
Liepin (猎聘) job scraper via web_search.

This script processes pre-fetched web_search results into structured job listings.

Usage (agent-driven):
  1. Run web_search queries via Hermes Agent (defined in QUERIES below)
  2. Feed results into process_results() or paste into WEB_SEARCH_RESULTS
  3. Run this script to generate liepin-results.json

Alternative: standalone mode reads from liepin-websearch.json if present.
"""
import json, os, re, sys
from datetime import datetime

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
OUTPUT = os.path.join(WORKSPACE, "career-os/scrapers/liepin-results.json")

# Search queries for Hermes Agent web_search tool
QUERIES = [
    'site:liepin.com "资深产品经理" 深圳',
    'site:liepin.com "资深产品经理" 上海',
    'site:liepin.com "产品总监" 深圳 OR 上海 OR 广州',
    'site:liepin.com "AI product manager" Shenzhen OR Shanghai',
    'site:liepin.com "跨境电商" 产品经理 深圳',
    'site:liepin.com "strategy director" Shanghai OR "Hong Kong"',
    'site:liepin.com "head of product" Singapore OR "Hong Kong"',
]

# Pre-fetched web_search results (populated by Hermes Agent)
WEB_SEARCH_RESULTS = []

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
        if url in seen_urls:
            continue
        
        # Filter: must be a liepin job listing
        if "liepin.com" not in url.lower():
            continue
        
        # Filter: must look like a job listing (not search/category pages)
        if "/zhaopin/" in url and not any(c.isdigit() for c in url.split("/")[-1]):
            continue  # category page, not a specific job
        
        seen_urls.add(url)
        
        # Extract company from title (Liepin format: "Title - Company")
        company = ""
        title_clean = title
        if " - " in title:
            parts = title.rsplit(" - ", 1)
            if len(parts) == 2 and len(parts[1]) < 50:
                company = parts[1].strip()
                title_clean = parts[0].strip()
        elif "｜" in title:
            parts = title.rsplit("｜", 1)
            if len(parts) == 2:
                company = parts[1].strip()
                title_clean = parts[0].strip()
        
        # Remove common prefixes
        title_clean = re.sub(r'^(招聘|最新)?[\s\-]*', '', title_clean).strip()
        
        # Extract location
        location = ""
        text = f"{title} {snippet}".lower()
        for city in ["Shanghai", "Beijing", "Shenzhen", "Guangzhou", "Hong Kong", "Singapore", "Hangzhou", "Remote"]:
            if city.lower() in text:
                location = city
                break
        
        # Extract salary from snippet
        salary = ""
        salary_match = re.search(r'(\d+[\-~]\d+K(?:·\d+薪)?)', snippet)
        if salary_match:
            salary = salary_match.group(1)
        
        # Classify grade
        t = title_clean.lower()
        if any(k in t for k in ["vp", "vice president", "c-level", "首席"]):
            grade = "S-1"
        elif any(k in t for k in ["director", "总监", "head of", "负责人"]):
            grade = "A-1"
        elif any(k in t for k in ["principal", "staff", "专家"]):
            grade = "A-1"
        elif any(k in t for k in ["senior", "sr.", "资深", "高级"]):
            grade = "A-2"
        else:
            grade = "A-2"
        
        # Classify role type
        role_type = "Product Management"
        if "strategy" in t or "战略" in t:
            role_type = "Strategy/Ops"
        elif "program" in t or "项目" in t:
            role_type = "Program Management"
        elif "growth" in t or "增长" in t:
            role_type = "Growth"
        
        jobs.append({
            "title": title_clean,
            "company": company,
            "location": location,
            "grade": grade,
            "url": url,
            "role_type": role_type,
            "salary": salary,
            "scanned_date": datetime.now().strftime("%Y-%m-%d"),
            "source": "liepin",
        })
    
    return jobs

def main():
    # Try loading from standalone file first
    standalone_path = os.path.join(os.path.dirname(__file__), "liepin-websearch.json")
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
    print(f"\nLiepin: {len(jobs)} jobs extracted")
    
    with open(OUTPUT, 'w') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    print(f"Saved to {OUTPUT}")
    return jobs

if __name__ == "__main__":
    main()
