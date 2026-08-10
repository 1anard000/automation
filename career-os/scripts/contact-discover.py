#!/usr/bin/env python3
"""
Contact Discovery Script for Career OS CRM

Reads jobs-all.json to identify top companies by grade-weighted job count,
then outputs:
  - contacts-discovered.json: enriched contacts with recruiter/HR info
  - outreach-priorities-v2.md: ranked outreach targets with discovered contacts

Usage: python3 contact-discover.py
"""

import json
import os
from collections import Counter, defaultdict
from datetime import datetime

# Paths (relative to script location)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(SCRIPT_DIR, "..", "..", "OKComputer_职位搜索清单")
JOBS_FILE = os.path.join(BASE_DIR, "jobs-all.json")
CONTACTS_FILE = os.path.join(BASE_DIR, "contacts.json")
DISCOVERED_FILE = os.path.join(BASE_DIR, "contacts-discovered.json")
PRIORITIES_FILE = os.path.join(BASE_DIR, "outreach-priorities-v2.md")

# Grade → weight mapping
GRADE_WEIGHTS = {
    "S": 5.0,
    "A": 4.0,
    "A-1": 4.5,
    "A-2": 4.2,
    "B": 3.0,
    "C": 2.0,
    "D": 1.0,
    "": 0.0,
}


def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved {path}")


def save_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"  ✓ Saved {path}")


def rank_companies(jobs):
    """Rank top companies by grade-weighted score."""
    companies = {}
    for j in jobs:
        c = j.get("company", "")
        g = j.get("grade", "")
        if not c:
            continue
        if c not in companies:
            companies[c] = {
                "count": 0,
                "grades": defaultdict(int),
                "weight_sum": 0.0,
                "titles": [],
            }
        companies[c]["count"] += 1
        companies[c]["grades"][g] += 1
        companies[c]["weight_sum"] += GRADE_WEIGHTS.get(g, 0)
        companies[c]["titles"].append(j.get("title", ""))

    ranked = sorted(companies.items(), key=lambda x: x[1]["weight_sum"], reverse=True)
    return ranked[:20]


def get_existing_contacts(contacts, discovered):
    """Get set of company names that already have real-person contacts."""
    known = set()
    for c in contacts:
        if not c.get("is_company") and not c.get("is_company_placeholder"):
            known.add(c.get("company", ""))
    for c in discovered:
        known.add(c.get("company", ""))
    return known


def compute_outreach_priority(entry):
    """Determine outreach priority based on score."""
    score = entry["weight_sum"]
    if score >= 200:
        return "🔴 High"
    elif score >= 50:
        return "🟠 Medium"
    elif score >= 20:
        return "🟡 Medium"
    else:
        return "🟢 Low"


def generate_markdown(ranked, existing_contacts, discovered_map):
    """Generate outreach-priorities-v2.md."""
    lines = []
    lines.append("# Outreach Priorities v2")
    lines.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
    lines.append("Companies ranked by **(open_roles × grade_weight)**.\n")
    lines.append("| # | Company | Jobs | Top Grades | Score | Has Contacts | Discovered | Priority |")
    lines.append("|---|---------|------|------------|-------|--------------|------------|----------|")

    for i, (company, info) in enumerate(ranked, 1):
        grades = info["grades"]
        grade_str = ", ".join(
            f"{g}:{n}" for g, n in sorted(grades.items(), key=lambda x: -GRADE_WEIGHTS.get(x[0], 0))
        )
        has_contacts = "✅" if company in existing_contacts else "❌"
        discovered = discovered_map.get(company, [])
        disc_str = ", ".join(c["name"] for c in discovered) if discovered else "—"
        priority = compute_outreach_priority(info)
        lines.append(
            f"| {i} | **{company}** | {info['count']} | {grade_str} | {info['weight_sum']:.1f} | {has_contacts} | {disc_str} | {priority} |"
        )

    lines.append("")
    lines.append("## Discovered Contacts Detail\n")

    for i, (company, info) in enumerate(ranked, 1):
        discovered = discovered_map.get(company, [])
        lines.append(f"### {i}. {company}")
        lines.append(f"- **Open roles:** {info['count']}")
        lines.append(f"- **Score:** {info['weight_sum']:.1f}")
        if discovered:
            lines.append("- **Contacts found:**")
            for c in discovered:
                email_str = c.get("email") or "N/A"
                lines.append(f"  - **{c['name']}** — {c.get('role_type', 'unknown')}")
                if c.get("linkedin_url"):
                    lines.append(f"    - LinkedIn: {c['linkedin_url']}")
                if email_str != "N/A":
                    lines.append(f"    - Email: {email_str}")
                lines.append(f"    - Source: {c.get('source_url', 'N/A')}")
        else:
            lines.append("- **No contacts discovered yet**")
        lines.append("")

    lines.append("---")
    lines.append("*Next step: Run outreach for 🔴 High priority companies first.*")
    return "\n".join(lines)


def main():
    print("🔍 Contact Discovery Script")
    print("=" * 50)

    # Load data
    jobs = load_json(JOBS_FILE)
    contacts = load_json(CONTACTS_FILE)
    discovered = load_json(DISCOVERED_FILE)

    print(f"  Jobs loaded: {len(jobs)}")
    print(f"  Existing contacts: {len(contacts)}")
    print(f"  Previously discovered: {len(discovered)}")

    # Rank companies
    ranked = rank_companies(jobs)
    print(f"\n  Top 20 companies by grade-weighted score:")
    for i, (company, info) in enumerate(ranked, 1):
        print(f"    {i:2d}. {company}: {info['count']} jobs, score={info['weight_sum']:.1f}")

    # Check existing real contacts
    existing = get_existing_contacts(contacts, discovered)
    print(f"\n  Companies with existing contacts: {existing}")

    # Build discovered map
    discovered_map = defaultdict(list)
    for c in discovered:
        discovered_map[c.get("company", "")].append(c)

    # Generate markdown
    md = generate_markdown(ranked, existing, discovered_map)
    save_text(PRIORITIES_FILE, md)

    # Save discovered contacts (keep existing)
    save_json(DISCOVERED_FILE, discovered)

    print(f"\n✅ Done! Files written:")
    print(f"   {DISCOVERED_FILE}")
    print(f"   {PRIORITIES_FILE}")

    return ranked, discovered


if __name__ == "__main__":
    main()
