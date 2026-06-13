#!/usr/bin/env python3
"""
CLI Interface for Personal CRM.
Commands: search, stale, add, remind, health, import, score, list
"""

import argparse
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from database import (
    init_db, create_contact, get_contact_by_email, update_contact,
    delete_contact, search_contacts as db_search_contacts, list_contacts,
    create_interaction, create_reminder, get_reminders, update_reminder,
    delete_reminder, DB_PATH
)
from vector_search import VectorSearch, search_contacts, find_stale_contacts
from scorer import (
    calculate_health_score, update_all_health_scores, get_stale_contacts,
    get_health_dashboard, print_health_report, get_health_status
)
from discovery import import_contacts


def cmd_search(args):
    """Search contacts by query."""
    query = args.query
    
    # Check if it's a company-specific query
    company_keywords = ['at ', '@', 'company', 'work', 'works']
    is_company_query = any(kw in query.lower() for kw in company_keywords)
    
    searcher = VectorSearch()
    
    if is_company_query:
        # Extract company name
        import re
        match = re.search(r'(?:at |@ )?([A-Z][a-zA-Z0-9]+)', query)
        if match:
            company = match.group(1)
            print(f"🔍 Searching for contacts at {company}...\n")
            results = searcher.search_by_company(company)
        else:
            results = searcher.search(query, top_k=args.top)
    else:
        results = searcher.search(query, top_k=args.top)
    
    if not results:
        print("No contacts found.")
        return
    
    print(f"Found {len(results)} contact(s):\n")
    for contact, score in results:
        company = contact.get('company', 'N/A')
        title = contact.get('title', '')
        title_str = f" - {title}" if title else ''
        print(f"  👤 {contact['name']} ({company}){title_str}")
        print(f"     📧 {contact.get('email', 'N/A')}")
        if contact.get('linkedin_url'):
            print(f"     🔗 {contact['linkedin_url']}")
        print(f"     🎯 Match Score: {score:.3f}")
        print()


def cmd_stale(args):
    """Show relationships needing outreach."""
    months = args.months
    print(f"🕰️  Contacts not contacted in {months}+ months:\n")
    
    stale = find_stale_contacts(months)
    
    if not stale:
        print("✅ No stale contacts found!")
        return
    
    for contact in stale:
        days = contact.get('last_contact_date')
        status_emoji, status_label = get_health_status(contact.get('health_score', 50))
        
        print(f"  {status_emoji} {contact['name']}")
        print(f"     📧 {contact.get('email', 'N/A')}")
        if contact.get('company'):
            print(f"     🏢 {contact['company']}")
        print(f"     📅 Last Contact: {contact.get('last_contact_date', 'Never')}")
        print(f"     💪 Strength: {contact.get('strength', 'N/A').title()}")
        print(f"     🎯 Priority: {contact.get('priority', 'N/A').title()}")
        print()
    
    print(f"Total: {len(stale)} stale contact(s)")


def cmd_add(args):
    """Add a new contact."""
    # Parse input: "John Doe, john@example.com, Head of Product, met at AWS Summit"
    parts = [p.strip() for p in args.contact.split(',')]
    
    if len(parts) < 2:
        print("❌ Invalid format. Use: 'Name, email, title, how we met'")
        return
    
    name = parts[0]
    email = parts[1] if len(parts) > 1 else None
    title = parts[2] if len(parts) > 2 else None
    how_we_met = parts[3] if len(parts) > 3 else None
    
    # Check if contact already exists
    existing = get_contact_by_email(email)
    if existing:
        print(f"⚠️  Contact already exists: {existing['name']}")
        print(f"   Email: {existing['email']}")
        print(f"   Company: {existing.get('company', 'N/A')}")
        
        # Offer to update
        if args.update or input("\nUpdate existing contact? (y/n): ").lower() == 'y':
            update_data = {}
            if name and name != existing['name']:
                update_data['name'] = name
            if title and title != existing.get('title'):
                update_data['title'] = title
            if how_we_met and how_we_met != existing.get('how_we_met'):
                update_data['how_we_met'] = how_we_met
            
            if update_data:
                update_contact(existing['id'], **update_data)
                print("✅ Contact updated!")
            else:
                print("ℹ️  No changes made.")
        return
    
    # Create new contact
    contact_id = create_contact(
        name=name,
        email=email,
        title=title,
        how_we_met=how_we_met
    )
    
    print("✅ Contact added!")
    print(f"   ID: {contact_id}")
    print(f"   Name: {name}")
    print(f"   Email: {email}")
    if title:
        print(f"   Title: {title}")
    if how_we_met:
        print(f"   Met: {how_we_met}")


def cmd_remind(args):
    """Create or manage reminders."""
    if args.delete:
        # Delete reminder by ID
        if delete_reminder(args.delete):
            print(f"✅ Reminder {args.delete} deleted.")
        else:
            print(f"❌ Reminder {args.delete} not found.")
        return
    
    if args.done:
        # Mark reminder as done
        if update_reminder(args.done, status='done'):
            print(f"✅ Reminder {args.done} marked as done.")
        else:
            print(f"❌ Reminder {args.done} not found.")
        return
    
    if args.list:
        # List reminders
        status = args.status
        reminders = get_reminders(status)
        
        if not reminders:
            print(f"No {status} reminders found.")
            return
        
        print(f"📋 {status.title()} Reminders:\n")
        for reminder in reminders:
            contact_name = reminder.get('contact_name', 'General')
            print(f"  [{reminder['id']}] {reminder['task']}")
            print(f"     👤 {contact_name}")
            print(f"     📅 Due: {reminder['due_date']}")
            if reminder.get('snooze_until'):
                print(f"     ⏰ Snoozed until: {reminder['snooze_until']}")
            print()
        return
    
    # Create new reminder
    task = args.task
    due_date = args.date or date.today().isoformat()
    
    # Try to find contact
    contact_id = None
    if args.contact:
        contact = get_contact_by_email(args.contact)
        if contact:
            contact_id = contact['id']
        else:
            # Search by name
            contacts = db_search_contacts(args.contact)
            if contacts:
                contact_id = contacts[0]['id']
    
    reminder_id = create_reminder(
        contact_id=contact_id,
        task=task,
        due_date=due_date
    )
    
    print("✅ Reminder created!")
    print(f"   ID: {reminder_id}")
    print(f"   Task: {task}")
    print(f"   Due: {due_date}")
    if contact_id:
        print(f"   Contact ID: {contact_id}")


def cmd_health(args):
    """Show relationship health dashboard."""
    if args.contact:
        # Show health for specific contact
        contact = get_contact_by_email(args.contact)
        if not contact:
            contacts = db_search_contacts(args.contact)
            if contacts:
                contact = contacts[0]
        
        if not contact:
            print(f"❌ Contact '{args.contact}' not found.")
            return
        
        result = calculate_health_score(contact['id'])
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return
        
        print_health_report(result)
        return
    
    # Show dashboard
    print("📊 Relationship Health Dashboard\n")
    print("=" * 60)
    
    dashboard = get_health_dashboard()
    
    print(f"\n📈 Summary")
    print(f"   Total Contacts: {dashboard['total_contacts']}")
    print(f"   Average Health Score: {dashboard['summary']['average_score']}/100")
    print(f"   Needing Outreach (90+ days): {dashboard['summary']['needs_outreach']}")
    
    print(f"\n🟢 Healthy ({dashboard['summary']['healthy_count']})")
    for contact in dashboard['healthy'][:5]:
        print(f"   • {contact['name']} - Score: {contact['health_score']}")
    if len(dashboard['healthy']) > 5:
        print(f"   ... and {len(dashboard['healthy']) - 5} more")
    
    print(f"\n🟡 Warming ({dashboard['summary']['warming_count']})")
    for contact in dashboard['warming'][:5]:
        print(f"   • {contact['name']} - Score: {contact['health_score']}")
    if len(dashboard['warming']) > 5:
        print(f"   ... and {len(dashboard['warming']) - 5} more")
    
    print(f"\n🟠 Stale ({dashboard['summary']['stale_count']})")
    for contact in dashboard['stale'][:5]:
        print(f"   • {contact['name']} - Score: {contact['health_score']}")
    if len(dashboard['stale']) > 5:
        print(f"   ... and {len(dashboard['stale']) - 5} more")
    
    print(f"\n🔴 Cold ({dashboard['summary']['cold_count']})")
    for contact in dashboard['cold'][:5]:
        print(f"   • {contact['name']} - Score: {contact['health_score']}")
    if len(dashboard['cold']) > 5:
        print(f"   ... and {len(dashboard['cold']) - 5} more")
    
    print("\n" + "=" * 60)


def cmd_import(args):
    """Import contacts from Gmail/Calendar exports."""
    gmail_path = Path(args.gmail) if args.gmail else None
    calendar_path = Path(args.calendar) if args.calendar else None
    
    if not gmail_path and not calendar_path:
        print("❌ Please specify --gmail or --calendar path.")
        return
    
    result = import_contacts(
        gmail_path=gmail_path,
        calendar_path=calendar_path,
        dry_run=args.dry_run
    )
    
    print(f"\n✅ Import complete!")
    print(f"   Total unique contacts: {result['total']}")


def cmd_score(args):
    """Recalculate health scores."""
    print("🔄 Recalculating health scores...\n")
    
    results = update_all_health_scores()
    
    print(f"✅ Updated {len(results)} contact(s)")
    
    if args.show_changes:
        print("\nScore Changes:")
        for result in results:
            if result['score_change'] != 0:
                change = result['score_change']
                sign = '+' if change > 0 else ''
                print(f"   {result['name']}: {result['previous_score']} → {result['health_score']} ({sign}{change})")


def cmd_list(args):
    """List all contacts."""
    contacts = list_contacts()
    
    if not contacts:
        print("No contacts found.")
        return
    
    print(f"📇 All Contacts ({len(contacts)}):\n")
    
    for contact in contacts:
        company = contact.get('company', 'N/A')
        email = contact.get('email', 'N/A')
        print(f"  👤 {contact['name']}")
        print(f"     📧 {email}")
        if company != 'N/A':
            print(f"     🏢 {company}")
        print()


def cmd_interact(args):
    """Log an interaction with a contact."""
    contact = get_contact_by_email(args.contact)
    if not contact:
        contacts = db_search_contacts(args.contact)
        if contacts:
            contact = contacts[0]
    
    if not contact:
        print(f"❌ Contact '{args.contact}' not found.")
        return
    
    interaction_id = create_interaction(
        contact_id=contact['id'],
        interaction_type=args.type,
        date_str=args.date or date.today().isoformat(),
        summary=args.summary,
        sentiment=args.sentiment,
        follow_up_needed=args.follow_up,
        follow_up_date=args.follow_up_date
    )
    
    print("✅ Interaction logged!")
    print(f"   ID: {interaction_id}")
    print(f"   Contact: {contact['name']}")
    print(f"   Type: {args.type}")
    print(f"   Date: {args.date or date.today().isoformat()}")
    if args.summary:
        print(f"   Summary: {args.summary}")
    if args.follow_up:
        print(f"   ⚠️  Follow-up needed: {args.follow_up_date or 'Not set'}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Personal CRM - Manage your professional relationships',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 cli.py search "who do I know at NVIDIA?"
  python3 cli.py stale --months 6
  python3 cli.py add "John Doe, john@nvidia.com, VP Engineering, met at tech conference"
  python3 cli.py remind "Follow up with Sarah" --date 2026-06-15 --contact sarah@company.com
  python3 cli.py health
  python3 cli.py import --gmail ~/Downloads/gmail-export.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search contacts')
    search_parser.add_argument('query', help='Search query (e.g., "who do I know at NVIDIA?")')
    search_parser.add_argument('--top', type=int, default=10, help='Number of results')
    search_parser.set_defaults(func=cmd_search)
    
    # Stale command
    stale_parser = subparsers.add_parser('stale', help='Show stale relationships')
    stale_parser.add_argument('--months', type=int, default=6, help='Months threshold')
    stale_parser.set_defaults(func=cmd_stale)
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new contact')
    add_parser.add_argument('contact', help='Contact info: "Name, email, title, how we met"')
    add_parser.add_argument('--update', action='store_true', help='Auto-update if exists')
    add_parser.set_defaults(func=cmd_add)
    
    # Remind command
    remind_parser = subparsers.add_parser('remind', help='Manage reminders')
    remind_parser.add_argument('task', nargs='?', help='Reminder task')
    remind_parser.add_argument('--date', help='Due date (YYYY-MM-DD)')
    remind_parser.add_argument('--contact', help='Related contact (email or name)')
    remind_parser.add_argument('--list', action='store_true', help='List reminders')
    remind_parser.add_argument('--status', default='pending', help='Filter by status')
    remind_parser.add_argument('--done', type=int, help='Mark reminder as done')
    remind_parser.add_argument('--delete', type=int, help='Delete reminder by ID')
    remind_parser.set_defaults(func=cmd_remind)
    
    # Health command
    health_parser = subparsers.add_parser('health', help='Show health dashboard')
    health_parser.add_argument('--contact', help='Show health for specific contact')
    health_parser.set_defaults(func=cmd_health)
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import contacts')
    import_parser.add_argument('--gmail', help='Path to Gmail export (MBOX/JSON)')
    import_parser.add_argument('--calendar', help='Path to Calendar export (ICS/JSON)')
    import_parser.add_argument('--dry-run', action='store_true', help='Don\'t write to DB')
    import_parser.set_defaults(func=cmd_import)
    
    # Score command
    score_parser = subparsers.add_parser('score', help='Recalculate health scores')
    score_parser.add_argument('--show-changes', action='store_true', help='Show score changes')
    score_parser.set_defaults(func=cmd_score)
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all contacts')
    list_parser.set_defaults(func=cmd_list)
    
    # Interact command
    interact_parser = subparsers.add_parser('interact', help='Log an interaction')
    interact_parser.add_argument('contact', help='Contact email or name')
    interact_parser.add_argument('--type', choices=['email', 'meeting', 'call', 'linkedin', 'other'],
                                default='other', help='Interaction type')
    interact_parser.add_argument('--date', help='Interaction date (YYYY-MM-DD)')
    interact_parser.add_argument('--summary', help='Interaction summary')
    interact_parser.add_argument('--sentiment', choices=['positive', 'neutral', 'negative'],
                                default='neutral', help='Interaction sentiment')
    interact_parser.add_argument('--follow-up', action='store_true', help='Follow-up needed')
    interact_parser.add_argument('--follow-up-date', help='Follow-up date')
    interact_parser.set_defaults(func=cmd_interact)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize database
    init_db()
    
    # Execute command
    args.func(args)


if __name__ == '__main__':
    main()
