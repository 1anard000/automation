#!/usr/bin/env python3
"""
Outreach Tracker - Analytics for Career OS CRM.

Reads crm.db and generates outreach analytics:
- Contacts by stage (prospect → contacted → responded → interview → offer)
- Response rates
- Follow-up overdue
- Pipeline funnel data

Outputs JSON summary for the dashboard.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

DB_PATH = Path(__file__).resolve().parent.parent / "crm" / "crm.db"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "crm-web" / "outreach-analytics.json"

TODAY = datetime.now().date()
TODAY_STR = TODAY.isoformat()


def get_outreach_stage(cur, contact_id):
    """Determine outreach stage for a contact based on interactions."""
    cur.execute("""
        SELECT type, sentiment, follow_up_needed, date
        FROM interactions WHERE contact_id = ?
        ORDER BY date DESC
    """, (contact_id,))
    interactions = cur.fetchall()

    if not interactions:
        return "prospect"

    # Check for interview signals
    for i in interactions:
        summary = i[3] if len(i) > 3 else ""
        if "interview" in str(i).lower() or "onsite" in str(i).lower():
            return "interview"

    # Check for response signals
    positive_count = sum(1 for i in interactions if i[1] == "positive")
    if positive_count > 0:
        return "responded"

    # Has outreach
    return "contacted"


def compute_analytics():
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        return None

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Get all contacts with relationships
    cur.execute("""
        SELECT
            c.id, c.name, c.company, c.title, c.email, c.location,
            r.health_score, r.last_contact_date, r.strength, r.priority,
            r.contact_id as rel_id
        FROM contacts c
        LEFT JOIN relationships r ON r.contact_id = c.id
        ORDER BY c.name
    """)
    contacts = [dict(row) for row in cur.fetchall()]

    # Get all interactions
    cur.execute("SELECT * FROM interactions ORDER BY date DESC")
    all_interactions = [dict(row) for row in cur.fetchall()]

    # Get all reminders
    cur.execute("SELECT * FROM reminders ORDER BY due_date")
    all_reminders = [dict(row) for row in cur.fetchall()]

    # ── Outreach Pipeline ──
    stage_counts = defaultdict(int)
    stage_contacts = defaultdict(list)

    for c in contacts:
        stage = get_outreach_stage(cur, c["id"])
        c["outreach_stage"] = stage
        stage_counts[stage] += 1
        stage_contacts[stage].append({
            "id": c["id"],
            "name": c["name"],
            "company": c["company"],
            "health_score": c.get("health_score"),
        })

    # ── Response Rate ──
    total_contacted = sum(1 for c in contacts if c["outreach_stage"] != "prospect")
    responded = sum(1 for c in contacts if c["outreach_stage"] in ("responded", "interview"))
    response_rate = (responded / total_contacted * 100) if total_contacted > 0 else 0

    # ── Follow-up Analysis ──
    overdue_followups = []
    upcoming_followups = []
    today = datetime.now().date()

    for c in contacts:
        cur.execute("""
            SELECT follow_up_needed, follow_up_date
            FROM interactions WHERE contact_id = ? AND follow_up_needed = 1
            ORDER BY follow_up_date DESC LIMIT 1
        """, (c["id"],))
        fu = cur.fetchone()
        if fu and fu["follow_up_date"]:
            fu_date = datetime.strptime(fu["follow_up_date"], "%Y-%m-%d").date()
            days = (today - fu_date).days
            entry = {
                "contact_id": c["id"],
                "contact_name": c["name"],
                "company": c["company"],
                "follow_up_date": fu["follow_up_date"],
                "days_overdue": max(0, days),
                "health_score": c.get("health_score"),
            }
            if days > 0:
                overdue_followups.append(entry)
            else:
                upcoming_followups.append(entry)

    # Sort overdue by severity
    overdue_followups.sort(key=lambda x: x["days_overdue"], reverse=True)

    # ── Reminder Analysis ──
    pending_reminders = [r for r in all_reminders if r["status"] == "pending"]
    overdue_reminders = []
    for r in pending_reminders:
        if r["due_date"]:
            due = datetime.strptime(r["due_date"], "%Y-%m-%d").date()
            if due < today:
                r["days_overdue"] = (today - due).days
                overdue_reminders.append(dict(r))
    overdue_reminders.sort(key=lambda x: x.get("days_overdue", 0), reverse=True)

    # ── Interaction Timeline ──
    recent_interactions = []
    for i in all_interactions[:20]:
        contact = next((c for c in contacts if c["id"] == i["contact_id"]), None)
        recent_interactions.append({
            "id": i["id"],
            "contact_name": contact["name"] if contact else "Unknown",
            "company": contact["company"] if contact else "Unknown",
            "type": i["type"],
            "date": i["date"],
            "summary": i["summary"],
            "sentiment": i["sentiment"],
            "follow_up_needed": i["follow_up_needed"],
            "follow_up_date": i.get("follow_up_date"),
        })

    # ── Company Outreach Summary ──
    company_outreach = defaultdict(lambda: {
        "contacts": 0, "contacted": 0, "responded": 0, "interactions": 0
    })
    for c in contacts:
        co = c["company"] or "Unknown"
        company_outreach[co]["contacts"] += 1
        if c["outreach_stage"] != "prospect":
            company_outreach[co]["contacted"] += 1
        if c["outreach_stage"] in ("responded", "interview"):
            company_outreach[co]["responded"] += 1
    for i in all_interactions:
        contact = next((c for c in contacts if c["id"] == i["contact_id"]), None)
        if contact:
            co = contact["company"] or "Unknown"
            company_outreach[co]["interactions"] += 1

    # ── Build Output ──
    analytics = {
        "generated_at": datetime.now().isoformat(),
        "pipeline": {
            "stages": {
                "prospect": {
                    "count": stage_counts.get("prospect", 0),
                    "contacts": stage_contacts.get("prospect", []),
                    "description": "Not yet contacted"
                },
                "contacted": {
                    "count": stage_counts.get("contacted", 0),
                    "contacts": stage_contacts.get("contacted", []),
                    "description": "Outreach sent, awaiting response"
                },
                "responded": {
                    "count": stage_counts.get("responded", 0),
                    "contacts": stage_contacts.get("responded", []),
                    "description": "Positive response received"
                },
                "interview": {
                    "count": stage_counts.get("interview", 0),
                    "contacts": stage_contacts.get("interview", []),
                    "description": "Interview stage"
                },
            },
            "funnel": [
                {"stage": "Prospect", "count": stage_counts.get("prospect", 0)},
                {"stage": "Contacted", "count": stage_counts.get("contacted", 0)},
                {"stage": "Responded", "count": stage_counts.get("responded", 0)},
                {"stage": "Interview", "count": stage_counts.get("interview", 0)},
            ]
        },
        "metrics": {
            "total_contacts": len(contacts),
            "total_interactions": len(all_interactions),
            "total_outreach": total_contacted,
            "response_rate": round(response_rate, 1),
            "avg_interactions_per_contact": round(len(all_interactions) / len(contacts), 1) if contacts else 0,
        },
        "follow_ups": {
            "overdue": overdue_followups,
            "upcoming": upcoming_followups[:10],
            "overdue_count": len(overdue_followups),
        },
        "reminders": {
            "pending_count": len(pending_reminders),
            "overdue": overdue_reminders[:15],
            "overdue_count": len(overdue_reminders),
        },
        "recent_interactions": recent_interactions,
        "company_outreach": dict(sorted(company_outreach.items(), key=lambda x: -x[1]["interactions"])),
    }

    # Write output
    OUTPUT_PATH.write_text(json.dumps(analytics, indent=2, default=str))
    print(f"Outreach analytics written to {OUTPUT_PATH}")
    print(f"\n=== Outreach Pipeline ===")
    print(f"  Prospect:   {stage_counts.get('prospect', 0)}")
    print(f"  Contacted:  {stage_counts.get('contacted', 0)}")
    print(f"  Responded:  {stage_counts.get('responded', 0)}")
    print(f"  Interview:  {stage_counts.get('interview', 0)}")
    print(f"\n  Response Rate: {response_rate:.1f}%")
    print(f"  Overdue Follow-ups: {len(overdue_followups)}")
    print(f"  Pending Reminders: {len(pending_reminders)}")
    print(f"  Total Interactions: {len(all_interactions)}")

    conn.close()
    return analytics


if __name__ == "__main__":
    compute_analytics()
