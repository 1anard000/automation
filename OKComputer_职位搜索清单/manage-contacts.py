#!/usr/bin/env python3
"""Manage CRM contacts. Usage:
  python3 manage-contacts.py add --company X --name Y --role Z --email E
  python3 manage-contacts.py list [--company X]
  python3 manage-contacts.py update --company X --status interviewed
  python3 manage-contacts.py stats
"""
import json, os, sys, argparse
from datetime import datetime

DIR = os.path.dirname(os.path.abspath(__file__))
CONTACTS_FILE = os.path.join(DIR, "contacts.json")

def load_contacts():
    if os.path.exists(CONTACTS_FILE):
        with open(CONTACTS_FILE) as f:
            return json.load(f)
    return {"contacts": [], "schema_version": 1, "created": datetime.now().isoformat()}

def save_contacts(data):
    with open(CONTACTS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def add_contact(args):
    data = load_contacts()
    contact = {
        "company": args.company,
        "name": args.name,
        "role": args.role or "",
        "email": args.email or "",
        "linkedin": args.linkedin or "",
        "phone": args.phone or "",
        "last_contact": datetime.now().strftime("%Y-%m-%d"),
        "status": args.status or "initial",
        "notes": args.notes or ""
    }
    data["contacts"].append(contact)
    save_contacts(data)
    print(f"✅ Added contact: {args.name} at {args.company}")

def list_contacts(args):
    data = load_contacts()
    contacts = data["contacts"]
    if args.company:
        contacts = [c for c in contacts if args.company.lower() in c.get("company","").lower()]
    if not contacts:
        print("No contacts found.")
        return
    for c in contacts:
        print(f"  {c['company']} | {c.get('name','?')} | {c.get('status','?')} | {c.get('last_contact','?')}")
    print(f"\nTotal: {len(contacts)} contacts")

def update_contact(args):
    data = load_contacts()
    updated = 0
    for c in data["contacts"]:
        if args.company and args.company.lower() in c.get("company","").lower():
            if args.status:
                c["status"] = args.status
            if args.notes:
                c["notes"] = args.notes
            c["last_contact"] = datetime.now().strftime("%Y-%m-%d")
            updated += 1
    save_contacts(data)
    print(f"✅ Updated {updated} contact(s)")

def stats(args):
    data = load_contacts()
    contacts = data["contacts"]
    statuses = {}
    for c in contacts:
        s = c.get("status", "unknown")
        statuses[s] = statuses.get(s, 0) + 1
    companies = set(c.get("company","") for c in contacts)
    print(f"📊 Contact Stats:")
    print(f"  Total: {len(contacts)}")
    print(f"  Companies: {len(companies)}")
    for s, count in sorted(statuses.items(), key=lambda x: -x[1]):
        print(f"  {s}: {count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CRM Contact Manager")
    sub = parser.add_subparsers(dest="command")
    
    add_p = sub.add_parser("add")
    add_p.add_argument("--company", required=True)
    add_p.add_argument("--name", required=True)
    add_p.add_argument("--role")
    add_p.add_argument("--email")
    add_p.add_argument("--linkedin")
    add_p.add_argument("--phone")
    add_p.add_argument("--status", choices=["initial","responded","interviewing","ghosted","declined"])
    add_p.add_argument("--notes")
    
    list_p = sub.add_parser("list")
    list_p.add_argument("--company")
    
    update_p = sub.add_parser("update")
    update_p.add_argument("--company")
    update_p.add_argument("--status", choices=["initial","responded","interviewing","ghosted","declined"])
    update_p.add_argument("--notes")
    
    sub.add_parser("stats")
    
    args = parser.parse_args()
    if args.command == "add": add_contact(args)
    elif args.command == "list": list_contacts(args)
    elif args.command == "update": update_contact(args)
    elif args.command == "stats": stats(args)
    else: parser.print_help()
