#!/usr/bin/env python3
"""Enrich CRM contacts with application statuses and follow-up tracking."""
import json
import os
from datetime import datetime

DIR = os.path.dirname(os.path.abspath(__file__))

def load(fn):
    p = os.path.join(DIR, fn)
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return None

def save(fn, data):
    p = os.path.join(DIR, fn)
    with open(p, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    contacts_raw = load("contacts.json")
    apps_data = load("applications-tracker.json")
    
    if not contacts_raw or not apps_data:
        print("Missing contacts.json or applications-tracker.json")
        return
    
    contacts = contacts_raw.get("contacts", []) if isinstance(contacts_raw, dict) else contacts_raw
    applications = apps_data.get("applications", [])
    
    # Build lookup: company -> applications
    company_apps = {}
    for app in applications:
        co = app.get("company", "").lower().strip()
        if co not in company_apps:
            company_apps[co] = []
        company_apps[co].append(app)
    
    enriched = 0
    followups_set = 0
    
    for contact in contacts:
        co = (contact.get("company") or "").lower().strip()
        
        # Skip if already has a real status
        if contact.get("status") and contact["status"] != "none":
            continue
        
        # Check if this contact's company has applications
        if co in company_apps:
            apps_for_co = company_apps[co]
            # Set application status based on most recent app
            latest = max(apps_for_co, key=lambda a: a.get("applied_date") or "")
            contact["application_status"] = latest.get("status", "not_applied")
            contact["applied_date"] = latest.get("applied_date", "")
            contact["status"] = latest.get("status", "not_applied")
            
            # Set follow-up date if not already set
            if not contact.get("follow_up_date") and latest.get("follow_up_date"):
                contact["follow_up_date"] = latest["follow_up_date"]
                followups_set += 1
            
            # Add matching job count
            contact["matching_jobs"] = len(apps_for_co)
            
            enriched += 1
        else:
            # No application for this company — mark as prospect
            contact["application_status"] = "prospect"
            contact["status"] = "prospect"
    
    # Save enriched contacts
    save("contacts.json", contacts_raw)
    
    # Regenerate CRM dashboard
    import subprocess
    result = subprocess.run(
        ["python3", os.path.join(DIR, "build-crm.py")],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("CRM dashboard regenerated")
    else:
        print(f"Dashboard rebuild failed: {result.stderr[:200]}")
    
    # Summary
    status_counts = {}
    for c in contacts:
        s = c.get("status", "none")
        status_counts[s] = status_counts.get(s, 0) + 1
    
    print(f"\nEnriched {enriched} contacts with application data")
    print(f"Set {followups_set} follow-up dates")
    print(f"\nContact status breakdown:")
    for s, count in sorted(status_counts.items(), key=lambda x: -x[1]):
        print(f"  {s}: {count}")

if __name__ == "__main__":
    main()
