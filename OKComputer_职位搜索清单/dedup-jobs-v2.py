#!/usr/bin/env python3
"""Remove duplicate jobs from jobs-all.json with smarter matching.
Handles:
- Case-insensitive company names
- Greenhouse job ID matching (boards.greenhouse.io vs job-boards.greenhouse.io)
- LinkedIn duplicate job IDs
- Normalized title matching
"""
import json
import os
import re

DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DIR, "jobs-all.json")

LINKEDIN_ID_RE = re.compile(r"/view/(\d+)")
GREENHOUSE_ID_RE = re.compile(r"/jobs/(\d+)")
GH_ID_RE = re.compile(r"/(\d{10,})")  # 10+ digit IDs in greenhouse URLs

def extract_job_id(url):
    """Extract unique job identifier from URL."""
    if not url:
        return None
    # LinkedIn job ID
    m = LINKEDIN_ID_RE.search(url)
    if m:
        return f"li-{m.group(1)}"
    # Greenhouse job ID
    m = GREENHOUSE_ID_RE.search(url)
    if m:
        return f"gh-{m.group(1)}"
    # Generic 10+ digit ID (other boards)
    m = GH_ID_RE.search(url)
    if m:
        return f"other-{m.group(1)}"
    return None

def normalize_title(title):
    """Normalize title for comparison."""
    if not title:
        return ""
    t = title.lower().strip()
    # Remove common prefixes/suffixes
    t = re.sub(r'\s*[\(\[][^\)\]]*[\)\]]\s*', ' ', t)  # Remove bracketed text
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def normalize_company(company):
    """Normalize company name for comparison."""
    if not company:
        return ""
    c = company.lower().strip()
    # Remove common suffixes
    for suffix in [' inc', ' inc.', ' llc', ' ltd', ' ltd.', ' co', ' corp', ' corporation']:
        if c.endswith(suffix):
            c = c[:-len(suffix)]
    return c

def main():
    if not os.path.exists(DATA_FILE):
        print(f"File not found: {DATA_FILE}")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    print(f"Starting with {len(jobs)} jobs")

    # Group by extracted job ID first (strongest match)
    id_groups = {}
    no_id = []
    for j in jobs:
        url = j.get("url", "")
        jid = extract_job_id(url)
        if jid:
            id_groups.setdefault(jid, []).append(j)
        else:
            no_id.append(j)

    # Deduplicate ID groups, keeping the best entry
    deduped_by_id = []
    removed_by_id = 0
    for jid, group in id_groups.items():
        if len(group) == 1:
            deduped_by_id.append(group[0])
        else:
            # Keep: most fields filled, prefer greenhouse_api source, longest URL
            best = max(group, key=lambda j: (
                sum(1 for v in j.values() if v),  # field count
                1 if 'greenhouse_api' in str(j.get('source','')) else 0,
                len(j.get('url','')),
            ))
            deduped_by_id.append(best)
            removed_by_id += len(group) - 1

    # Now deduplicate remaining by (normalized_title, normalized_company)
    all_jobs = deduped_by_id + no_id
    title_groups = {}
    for j in all_jobs:
        key = (normalize_title(j.get("title","")), normalize_company(j.get("company","")))
        title_groups.setdefault(key, []).append(j)

    cleaned = []
    removed_by_title = 0
    for key, group in title_groups.items():
        if len(group) == 1:
            cleaned.append(group[0])
        else:
            # Same strategy: keep best
            best = max(group, key=lambda j: (
                sum(1 for v in j.values() if v),
                1 if 'greenhouse_api' in str(j.get('source','')) else 0,
                len(j.get('url','')),
            ))
            cleaned.append(best)
            removed_by_title += len(group) - 1

    total_removed = removed_by_id + removed_by_title
    print(f"Removed {removed_by_id} by URL ID match")
    print(f"Removed {removed_by_title} by title+company match")
    print(f"Total removed: {total_removed}")
    print(f"Remaining: {len(cleaned)}")

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    print("Done!")

if __name__ == "__main__":
    main()
