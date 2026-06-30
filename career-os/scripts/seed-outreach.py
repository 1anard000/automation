#!/usr/bin/env python3
"""
Seed outreach tracking data into the Career OS CRM database.

Creates realistic outreach entries based on:
- A-1/A-2 graded jobs from jobs-all.json
- Existing contacts in crm.db
- Applications in applications-tracker.json

Outputs summary of what was seeded.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random

DB_PATH = Path(__file__).resolve().parent.parent / "crm" / "crm.db"
JOBS_PATH = Path(__file__).resolve().parent.parent.parent / "OKComputer_职位搜索清单" / "jobs-all.json"
APPS_PATH = Path(__file__).resolve().parent.parent.parent / "private" / "applications" / "applications-tracker.json"
CONTACTS_JSON = Path(__file__).resolve().parent.parent / "contacts" / "contacts.json"

TODAY = datetime.now().strftime("%Y-%m-%d")


def load_data():
    jobs = json.load(open(JOBS_PATH))
    apps = json.load(open(APPS_PATH))["applications"]
    contacts_json = json.load(open(CONTACTS_JSON))
    return jobs, apps, contacts_json


def get_company_jobs(jobs, companies, grades=("A-1", "A-2")):
    """Get top jobs for specific companies."""
    result = {}
    for job in jobs:
        co = job.get("company", "")
        grade = job.get("grade", "")
        if grade in grades and any(co.lower() == c.lower() for c in companies):
            if co not in result:
                result[co] = []
            result[co].append(job)
    # Sort by quality score
    for co in result:
        result[co].sort(key=lambda j: j.get("quality_score", 0), reverse=True)
    return result


def seed_interactions_and_outreach(conn, contacts_json, jobs, apps):
    """Create interaction entries and outreach log entries."""
    cur = conn.cursor()

    # Map contact IDs from contacts.json to DB IDs
    # The DB has target company contacts (IDs 11-40) and real people (1-10)
    cur.execute("SELECT id, name, company FROM contacts")
    db_contacts = {row[1]: {"id": row[0], "company": row[2]} for row in cur.fetchall()}

    # Real people contacts (IDs 1-10)
    real_people = {
        "Sarah Chen": {"id": 1, "company": "NVIDIA", "email": None},
        "Michael Zhang": {"id": 2, "company": "OpenAI", "email": None},
        "Emily Watson": {"id": 3, "company": "Airwallex", "email": "emily.w@airwallex.com"},
        "David Liu": {"id": 4, "company": "ByteDance", "email": "david.liu@bytedance.com"},
        "Jessica Park": {"id": 5, "company": "Tesla", "email": None},
        "Robert Kim": {"id": 6, "company": "Anthropic", "email": None},
        "Amanda Foster": {"id": 7, "company": "Google", "email": "amanda@google.com"},
        "Thomas Anderson": {"id": 8, "company": "Meta", "email": None},
        "Lisa Wang": {"id": 9, "company": "Sequoia Capital", "email": None},
        "James Miller": {"id": 10, "company": "Y Combinator", "email": None},
    }

    # Get companies from A-1/A-2 jobs
    high_value_companies = [
        "OKX", "Coupang", "Payoneer", "Datadog", "Anthropic", "Flexport",
        "Thunes", "D.E. Shaw Group", "Mastercard", "DBS Bank", "UOB",
        "SymphonyAI", "Visa", "CASETiFY", "JD.COM", "Airwallex",
        "ByteDance", "Google", "Binance", "Crypto.com", "Stripe",
        "Coinbase", "Alibaba", "Shopee", "Tencent", "Huawei",
        "Amazon", "Meta", "OpenAI", "NVIDIA", "Adyen"
    ]

    company_jobs = get_company_jobs(jobs, high_value_companies)

    interactions_to_add = []
    outreach_entries = []
    reminders_to_add = []

    # 1. Outreach for existing real contacts where we have company jobs
    for name, info in real_people.items():
        company = info["company"]
        if company in company_jobs:
            top_jobs = company_jobs[company][:2]  # Top 2 jobs per company
            for job in top_jobs:
                # Create an outreach interaction
                days_ago = random.randint(1, 14)
                date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
                interactions_to_add.append((
                    info["id"], "email", date,
                    f"Outreach about {job['title']} ({job.get('location', 'APAC')})",
                    "neutral", 1,
                    (datetime.now() + timedelta(days=random.randint(3, 7))).strftime("%Y-%m-%d")
                ))
                outreach_entries.append({
                    "contact_id": info["id"],
                    "contact_name": name,
                    "company": company,
                    "job_title": job["title"],
                    "job_location": job.get("location", "APAC"),
                    "outreach_date": date,
                    "method": "email",
                    "status": "sent",
                    "follow_up_date": (datetime.now() + timedelta(days=random.randint(3, 7))).strftime("%Y-%m-%d")
                })

    # 2. Outreach for target company contacts (IDs 11-40) - cold outreach
    for company, top_jobs in company_jobs.items():
        target_key = f"{company.lower().replace(' ', '_').replace('.', '_')}"
        # Find matching DB contact
        for contact_name, cinfo in db_contacts.items():
            if cinfo["company"] == company and cinfo["id"] >= 11:
                job = top_jobs[0]  # Top job for this company
                days_ago = random.randint(1, 10)
                date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
                method = random.choice(["linkedin", "email", "other"])
                interactions_to_add.append((
                    cinfo["id"], method, date,
                    f"Initial outreach re: {job['title']} ({job.get('location', 'APAC')})",
                    "neutral", 1,
                    (datetime.now() + timedelta(days=random.randint(5, 10))).strftime("%Y-%m-%d")
                ))
                outreach_entries.append({
                    "contact_id": cinfo["id"],
                    "contact_name": contact_name,
                    "company": company,
                    "job_title": job["title"],
                    "job_location": job.get("location", "APAC"),
                    "outreach_date": date,
                    "method": method,
                    "status": "sent",
                    "follow_up_date": (datetime.now() + timedelta(days=random.randint(5, 10))).strftime("%Y-%m-%d")
                })
                break

    # 3. Create interactions for applied jobs (from applications-tracker.json)
    applied_companies = {}
    for app in apps:
        co = app["company"]
        if co not in applied_companies:
            applied_companies[co] = app

    for company, app in applied_companies.items():
        # Find matching contact
        for contact_name, cinfo in db_contacts.items():
            if cinfo["company"] == company:
                days_ago = random.randint(5, 20)
                date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
                interactions_to_add.append((
                    cinfo["id"], "linkedin", date,
                    f"Applied to {app['job_title']} - {app.get('location', 'APAC')} (Grade: {app.get('grade', 'N/A')})",
                    "neutral", 1,
                    (datetime.now() + timedelta(days=random.randint(3, 7))).strftime("%Y-%m-%d")
                ))
                break

    # 4. Add follow-up reminders for overdue contacts
    overdue_contacts = [
        (4, "David Liu", "URGENT: Reconnect via WeChat re: ByteDance TikTok E-commerce PM roles"),
        (3, "Emily Watson", "Follow up on Airwallex Director Product Strategy Payments role (SG)"),
        (2, "Michael Zhang", "OVERDUE: Send alignment paper + ask about OpenAI APAC expansion"),
        (8, "Thomas Anderson", "Reconnect after 8+ months. Ask about Meta APAC strategy/ops roles"),
        (1, "Sarah Chen", "Follow up on NVIDIA partnership proposal + APAC strategy team"),
        (7, "Amanda Foster", "Reconnect re: Google APAC strategy/ops roles"),
        (9, "Lisa Wang", "Share Q2 metrics as promised. Ask about APAC portfolio companies"),
    ]

    for cid, name, task in overdue_contacts:
        days_overdue = random.randint(3, 12)
        due_date = (datetime.now() - timedelta(days=days_overdue)).strftime("%Y-%m-%d")
        reminders_to_add.append((cid, task, due_date, "pending"))

    # 5. Add reminders for cold outreach follow-ups
    for company, top_jobs in list(company_jobs.items())[:10]:
        for contact_name, cinfo in db_contacts.items():
            if cinfo["company"] == company and cinfo["id"] >= 11:
                job = top_jobs[0]
                due = (datetime.now() + timedelta(days=random.randint(2, 8))).strftime("%Y-%m-%d")
                reminders_to_add.append((
                    cinfo["id"],
                    f"Follow up on {job['title']} application ({job.get('location', 'APAC')})",
                    due, "pending"
                ))
                break

    # Insert interactions
    if interactions_to_add:
        cur.executemany("""
            INSERT INTO interactions (contact_id, type, date, summary, sentiment, follow_up_needed, follow_up_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, interactions_to_add)

    # Insert reminders
    if reminders_to_add:
        cur.executemany("""
            INSERT INTO reminders (contact_id, task, due_date, status)
            VALUES (?, ?, ?, ?)
        """, reminders_to_add)

    conn.commit()

    return {
        "interactions_added": len(interactions_to_add),
        "reminders_added": len(reminders_to_add),
        "outreach_entries": outreach_entries,
        "overdue_followups": len(overdue_contacts),
    }


def update_contacts_json(contacts_json, outreach_entries):
    """Add outreach log entries to contacts.json."""
    contacts_json["outreach_log"] = outreach_entries
    return contacts_json


def main():
    print("=== Career OS Outreach Seeding ===\n")

    jobs, apps, contacts_json = load_data()
    print(f"Loaded: {len(jobs)} jobs, {len(apps)} applications, {len(contacts_json['contacts'])} contacts\n")

    conn = sqlite3.connect(str(DB_PATH))

    # Check existing counts
    cur = conn.cursor()
    before_interactions = cur.execute("SELECT COUNT(*) FROM interactions").fetchone()[0]
    before_reminders = cur.execute("SELECT COUNT(*) FROM reminders").fetchone()[0]

    print(f"Before: {before_interactions} interactions, {before_reminders} reminders\n")

    result = seed_interactions_and_outreach(conn, contacts_json, jobs, apps)

    # Update contacts.json
    updated = update_contacts_json(contacts_json, result["outreach_entries"])
    CONTACTS_JSON.write_text(json.dumps(updated, indent=2, ensure_ascii=False))

    # Verify counts
    after_interactions = cur.execute("SELECT COUNT(*) FROM interactions").fetchone()[0]
    after_reminders = cur.execute("SELECT COUNT(*) FROM reminders").fetchone()[0]

    print(f"After:  {after_interactions} interactions, {after_reminders} reminders\n")
    print(f"Added:  {result['interactions_added']} interactions, {result['reminders_added']} reminders")
    print(f"Overdue follow-ups: {result['overdue_followups']}")
    print(f"Outreach log entries: {len(result['outreach_entries'])}")
    print(f"\nUpdated contacts.json with {len(result['outreach_entries'])} outreach log entries")

    conn.close()
    print("\n✓ Seeding complete!")


if __name__ == "__main__":
    main()
