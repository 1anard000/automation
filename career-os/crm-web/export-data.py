#!/usr/bin/env python3
"""
Export Career OS CRM database to JSON for the web dashboard.

Usage:
    python3 export-data.py

Reads: ../crm/crm.db
Writes: crm-data.json (same directory as this script)

The generated JSON is loaded by crm-dashboard.html when opened in a browser.
Due to browser security restrictions (CORS/file://), the HTML expects
the JSON file to be served or loaded via a local server. Quick options:

    # Option A: Python HTTP server (recommended)
    cd career-os/crm-web
    python3 -m http.server 8080
    # Then open http://localhost:8080/crm-dashboard.html

    # Option B: Just open the HTML file — it will try fetch('crm-data.json')
    # This works in Chrome with --allow-file-access-from-files flag.
"""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "crm" / "crm.db"
OUTPUT_PATH = Path(__file__).resolve().parent / "crm-data.json"


def export():
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Fetch all contacts with joined data
    cur.execute("""
        SELECT
            c.id, c.name, c.email, c.phone, c.company, c.title,
            c.linkedin_url, c.location, c.how_we_met, c.notes,
            c.created_at, c.updated_at,
            r.health_score, r.last_contact_date, r.strength, r.priority,
            (SELECT COUNT(*) FROM interactions i WHERE i.contact_id = c.id) as interaction_count,
            (SELECT i.date FROM interactions i WHERE i.contact_id = c.id ORDER BY i.date DESC LIMIT 1) as last_interaction_date
        FROM contacts c
        LEFT JOIN relationships r ON r.contact_id = c.id
        ORDER BY c.name
    """)
    contacts = [dict(row) for row in cur.fetchall()]

    # Fetch interactions grouped by contact
    cur.execute("SELECT * FROM interactions ORDER BY date DESC")
    all_interactions = [dict(row) for row in cur.fetchall()]
    interactions_by_contact = {}
    for i in all_interactions:
        cid = i["contact_id"]
        if cid not in interactions_by_contact:
            interactions_by_contact[cid] = []
        interactions_by_contact[cid].append(i)

    # Fetch reminders
    cur.execute("SELECT * FROM reminders WHERE status != 'done' ORDER BY due_date")
    reminders = [dict(row) for row in cur.fetchall()]
    reminders_by_contact = {}
    for r in reminders:
        cid = r["contact_id"]
        if cid not in reminders_by_contact:
            reminders_by_contact[cid] = []
        reminders_by_contact[cid].append(r)

    # Attach sub-records to contacts
    for c in contacts:
        c["interactions"] = interactions_by_contact.get(c["id"], [])
        c["reminders"] = reminders_by_contact.get(c["id"], [])

    # Build summary stats
    companies = {}
    health_buckets = {"excellent": 0, "good": 0, "fair": 0, "poor": 0, "unknown": 0}
    priority_counts = {"high": 0, "medium": 0, "low": 0}
    strength_counts = {"strong": 0, "medium": 0, "weak": 0}

    for c in contacts:
        co = c.get("company") or "Unknown"
        companies[co] = companies.get(co, 0) + 1

        hs = c.get("health_score")
        if hs is None:
            health_buckets["unknown"] += 1
        elif hs >= 80:
            health_buckets["excellent"] += 1
        elif hs >= 60:
            health_buckets["good"] += 1
        elif hs >= 40:
            health_buckets["fair"] += 1
        else:
            health_buckets["poor"] += 1

        p = c.get("priority") or "medium"
        priority_counts[p] = priority_counts.get(p, 0) + 1

        s = c.get("strength") or "weak"
        strength_counts[s] = strength_counts.get(s, 0) + 1

    data = {
        "contacts": contacts,
        "summary": {
            "total_contacts": len(contacts),
            "by_company": dict(sorted(companies.items(), key=lambda x: -x[1])),
            "health_distribution": health_buckets,
            "priority_distribution": priority_counts,
            "strength_distribution": strength_counts,
            "upcoming_reminders": reminders[:20],
        },
    }

    OUTPUT_PATH.write_text(json.dumps(data, indent=2, default=str))
    print(f"Exported {len(contacts)} contacts to {OUTPUT_PATH}")
    conn.close()


if __name__ == "__main__":
    export()
