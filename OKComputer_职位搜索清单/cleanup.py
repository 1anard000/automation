#!/usr/bin/env python3
"""Job cleanup script: remove stale, irrelevant, wrong-city, and experience-mismatch jobs."""

import json
import re

# Valid cities (case-insensitive matching)
VALID_CITIES = ["shenzhen", "hong kong", "guangzhou", "shanghai", "singapore"]

# Irrelevant title keywords (case-insensitive)
IRRELEVANT_KEYWORDS = [
    "intern", "junior", "assistant", "analyst", "support",
    "developer", "engineer", "data scientist", "marketing coordinator"
]

# Experience mismatch patterns
EXPERIENCE_PATTERNS = [
    r"15\+?\s*years",
    r"20\+?\s*years",
    r"15 years",
    r"20 years",
]

def is_valid_city(location):
    """Check if location contains any valid city."""
    loc_lower = location.lower()
    return any(city in loc_lower for city in VALID_CITIES)

def is_irrelevant_title(title):
    """Check if title contains irrelevant keywords (whole-word match)."""
    title_lower = title.lower()
    matched = []
    for kw in IRRELEVANT_KEYWORDS:
        # Use word boundary regex to avoid matching 'intern' in 'international'
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, title_lower):
            matched.append(kw)
    return matched

def has_experience_mismatch(job):
    """Check if any field mentions 15+ or 20+ years experience required."""
    # Check all string fields
    text = " ".join(str(v) for v in job.values() if isinstance(v, str)).lower()
    for pattern in EXPERIENCE_PATTERNS:
        if re.search(pattern, text):
            return True
    return False

def is_stale(job):
    """Check for dates like 2024 or 2025 that indicate old postings."""
    # Check all string fields for old year references
    text = " ".join(str(v) for v in job.values() if isinstance(v, str))
    # Look for year patterns that suggest the job is from 2024 or earlier
    # We check for "2024" or "2023" in any field, but NOT in scanned_date or URL context
    # Also check for "2025" since current date is 2026-06
    # But we should be careful: URLs may contain years as IDs
    # Only check title, company, role_type, salary fields
    check_fields = [job.get("title", ""), job.get("company", ""), 
                    job.get("role_type", ""), job.get("salary", "")]
    check_text = " ".join(check_fields)
    
    # Look for explicit date mentions like "Posted in 2024" or "Starts 2025"
    for year in ["2023", "2024"]:
        if year in check_text:
            return True
    return False

def main():
    with open("jobs-all.json", "r") as f:
        jobs = json.load(f)
    
    original_count = len(jobs)
    removals = {
        "wrong_city": [],
        "irrelevant_title": [],
        "experience_mismatch": [],
        "stale": [],
    }
    
    cleaned = []
    
    for job in jobs:
        removed = False
        
        # Check wrong city
        if not is_valid_city(job.get("location", "")):
            removals["wrong_city"].append(f"{job['title']} ({job.get('company', '?')}) - location: {job.get('location', '?')}")
            removed = True
        
        # Check irrelevant title
        if not removed:
            matched_kw = is_irrelevant_title(job.get("title", ""))
            if matched_kw:
                removals["irrelevant_title"].append(f"{job['title']} ({job.get('company', '?')}) - keywords: {matched_kw}")
                removed = True
        
        # Check experience mismatch
        if not removed and has_experience_mismatch(job):
            removals["experience_mismatch"].append(f"{job['title']} ({job.get('company', '?')})")
            removed = True
        
        # Check stale
        if not removed and is_stale(job):
            removals["stale"].append(f"{job['title']} ({job.get('company', '?')})")
            removed = True
        
        if not removed:
            cleaned.append(job)
    
    # Write cleaned file
    with open("jobs-all.json", "w") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)
    
    # Print report
    print(f"=== JOB CLEANUP REPORT ===")
    print(f"Original count: {original_count}")
    print(f"After cleanup:  {len(cleaned)}")
    print(f"Total removed:  {original_count - len(cleaned)}")
    print()
    
    for reason, items in removals.items():
        print(f"--- {reason.upper()} ({len(items)} removed) ---")
        for item in items:
            print(f"  • {item}")
        print()

if __name__ == "__main__":
    main()
