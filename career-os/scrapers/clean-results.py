#!/usr/bin/env python3
"""
Filter and clean the newly discovered jobs.
Remove junior roles, sales roles, non-English positions, and Bangkok-only roles.
"""
import json, os

AGENT_PATH = "/Users/iancolrick/.openclaw/workspace/career-os/scrapers/agent-discovered-jobs.json"
RESULTS_PATH = "/Users/iancolrick/.openclaw/workspace/career-os/scrapers/greenhouse-results.json"

# Load raw new jobs from greenhouse-results.json (this run's output)
with open(RESULTS_PATH) as f:
    raw_jobs = json.load(f)

print(f"Raw new jobs from this run: {len(raw_jobs)}")

# Filter criteria
EXCLUDE_TITLE_PATTERNS = [
    "junior", "intern", "coordinator", "associate",
    "area manager",  # Agoda sales
    "strategic account manager",  # Agoda sales
    "가격 매핑",  # Korean-only title
]

EXCLUDE_LOCATION_PATTERNS = [
    "bangkok",  # Not a target geo per user preference
]

def should_exclude(job):
    title_lower = job["title"].lower()
    loc_lower = job["location"].lower()
    
    for pat in EXCLUDE_TITLE_PATTERNS:
        if pat in title_lower:
            return True, f"excluded: title contains '{pat}'"
    
    # Check if location is ONLY Bangkok (not multi-location)
    if "bangkok" in loc_lower and "hong kong" not in loc_lower and "singapore" not in loc_lower and "shenzhen" not in loc_lower:
        return True, "excluded: Bangkok-only location"
    
    return False, None

kept = []
filtered_out = []

for job in raw_jobs:
    exclude, reason = should_exclude(job)
    if exclude:
        filtered_out.append((job["title"], job["company"], reason))
    else:
        kept.append(job)

print(f"Kept: {len(kept)}")
print(f"Filtered out: {len(filtered_out)}")

for title, company, reason in filtered_out:
    print(f"  ✗ {title} @ {company} — {reason}")

print(f"\n{'='*60}")
print(f"FINAL NEW JOBS ({len(kept)}):")
print(f"{'='*60}")

for job in kept:
    print(f"\n  📌 {job['title']}")
    print(f"     Company: {job['company']}")
    print(f"     Location: {job['location']}")
    print(f"     Role: {job['role_type']}")
    print(f"     URL: {job['url']}")
    print(f"     Source: {job['source']}")

# Update greenhouse-results.json with cleaned version
with open(RESULTS_PATH, "w") as f:
    json.dump(kept, f, indent=2, ensure_ascii=False)

# Also update agent-discovered-jobs.json — remove filtered jobs from this run
with open(AGENT_PATH) as f:
    agent_jobs = json.load(f)

# Rebuild: keep only jobs that passed the filter
kept_urls = {j["url"] for j in kept}
# Keep all existing agent jobs, but only if they were from previous runs
# (jobs from this run that were filtered out should be removed)
updated_agent = []
for j in agent_jobs:
    if j["url"] in kept_urls:
        updated_agent.append(j)
    elif j.get("scanned_date") != kept[0]["scanned_date"] if kept else True:
        # Keep jobs from previous runs
        updated_agent.append(j)

# Add the new kept jobs
existing_urls = {j["url"] for j in updated_agent}
for j in kept:
    if j["url"] not in existing_urls:
        updated_agent.append(j)

with open(AGENT_PATH, "w") as f:
    json.dump(updated_agent, f, indent=2, ensure_ascii=False)

print(f"\nUpdated agent-discovered-jobs.json: {len(updated_agent)} total jobs")
print(f"Updated greenhouse-results.json: {len(kept)} clean jobs")
