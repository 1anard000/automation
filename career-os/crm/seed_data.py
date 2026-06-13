#!/usr/bin/env python3
"""
Seed example data for testing the Personal CRM.
Creates sample contacts, interactions, and reminders.
"""

import sys
from pathlib import Path
from datetime import date, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from database import (
    init_db, create_contact, create_interaction, create_reminder,
    update_relationship, DB_PATH
)


def seed_database():
    """Seed database with example data."""
    
    print("🌱 Seeding example data...\n")
    
    # Initialize database
    init_db()
    
    # Sample contacts
    contacts = [
        {
            'name': 'Sarah Chen',
            'email': 'sarah.chen@nvidia.com',
            'phone': '+1-415-555-0101',
            'company': 'NVIDIA',
            'title': 'VP of AI Research',
            'linkedin_url': 'https://linkedin.com/in/sarahchen',
            'location': 'San Francisco, CA',
            'how_we_met': 'Met at NeurIPS 2025 conference',
            'notes': 'Key contact for AI partnerships. Very responsive to emails.',
            'priority': 'high',
            'last_contact': (date.today() - timedelta(days=15)).isoformat(),
        },
        {
            'name': 'Michael Zhang',
            'email': 'm.zhang@openai.com',
            'phone': '+1-415-555-0102',
            'company': 'OpenAI',
            'title': 'Senior Research Scientist',
            'linkedin_url': 'https://linkedin.com/in/michaelzhang',
            'location': 'San Francisco, CA',
            'how_we_met': 'Introduced by Sarah Chen',
            'notes': 'Expert in LLM alignment. Interested in collaboration.',
            'priority': 'high',
            'last_contact': (date.today() - timedelta(days=45)).isoformat(),
        },
        {
            'name': 'Emily Watson',
            'email': 'emily.w@airwallex.com',
            'phone': '+86-10-5555-0103',
            'company': 'Airwallex',
            'title': 'Head of Product',
            'linkedin_url': 'https://linkedin.com/in/emilywatson',
            'location': 'Beijing, China',
            'how_we_met': 'AWS Summit Beijing 2025',
            'notes': 'Looking for ML engineers for payments team.',
            'priority': 'medium',
            'last_contact': (date.today() - timedelta(days=120)).isoformat(),
        },
        {
            'name': 'David Liu',
            'email': 'david.liu@bytedance.com',
            'phone': '+86-10-5555-0104',
            'company': 'ByteDance',
            'title': 'Engineering Director',
            'linkedin_url': 'https://linkedin.com/in/davidliu',
            'location': 'Beijing, China',
            'how_we_met': 'Tech conference in Shanghai',
            'notes': 'Hiring for AI infra roles. Prefers WeChat communication.',
            'priority': 'medium',
            'last_contact': (date.today() - timedelta(days=200)).isoformat(),
        },
        {
            'name': 'Jessica Park',
            'email': 'jessica.park@tesla.com',
            'phone': '+1-510-555-0105',
            'company': 'Tesla',
            'title': 'Autopilot ML Lead',
            'linkedin_url': 'https://linkedin.com/in/jessicapark',
            'location': 'Palo Alto, CA',
            'how_we_met': 'Stanford AI Seminar',
            'notes': 'PhD from Stanford. Interested in computer vision.',
            'priority': 'high',
            'last_contact': (date.today() - timedelta(days=5)).isoformat(),
        },
        {
            'name': 'Robert Kim',
            'email': 'r.kim@anthropic.com',
            'phone': '+1-415-555-0106',
            'company': 'Anthropic',
            'title': 'Research Engineer',
            'linkedin_url': 'https://linkedin.com/in/robertkim',
            'location': 'San Francisco, CA',
            'how_we_met': 'Met at ML meetup',
            'notes': 'Works on Claude. Good source of industry insights.',
            'priority': 'medium',
            'last_contact': (date.today() - timedelta(days=8)).isoformat(),
        },
        {
            'name': 'Amanda Foster',
            'email': 'amanda@google.com',
            'phone': '+1-650-555-0107',
            'company': 'Google',
            'title': 'Staff Software Engineer',
            'linkedin_url': 'https://linkedin.com/in/amandafoster',
            'location': 'Mountain View, CA',
            'how_we_met': 'Google I/O 2025',
            'notes': 'Works on Gemini team. Open to referrals.',
            'priority': 'medium',
            'last_contact': (date.today() - timedelta(days=60)).isoformat(),
        },
        {
            'name': 'Thomas Anderson',
            'email': 't.anderson@meta.com',
            'phone': '+1-650-555-0108',
            'company': 'Meta',
            'title': 'Research Scientist',
            'linkedin_url': 'https://linkedin.com/in/thomasanderson',
            'location': 'Menlo Park, CA',
            'how_we_met': 'FAIR seminar',
            'notes': 'Expert in reinforcement learning.',
            'priority': 'low',
            'last_contact': (date.today() - timedelta(days=250)).isoformat(),
        },
        {
            'name': 'Lisa Wang',
            'email': 'lisa.wang@sequoiacap.com',
            'phone': '+1-415-555-0109',
            'company': 'Sequoia Capital',
            'title': 'Partner',
            'linkedin_url': 'https://linkedin.com/in/lisawang',
            'location': 'San Francisco, CA',
            'how_we_met': 'Startup demo day',
            'notes': 'Interested in AI startups. Good connection for fundraising.',
            'priority': 'high',
            'last_contact': (date.today() - timedelta(days=30)).isoformat(),
        },
        {
            'name': 'James Miller',
            'email': 'james.m@ycombinator.com',
            'phone': '+1-415-555-0110',
            'company': 'Y Combinator',
            'title': 'Group Partner',
            'linkedin_url': 'https://linkedin.com/in/jamesmiller',
            'location': 'San Francisco, CA',
            'how_we_met': 'YC office hours',
            'notes': 'Can provide intros to portfolio companies.',
            'priority': 'medium',
            'last_contact': (date.today() - timedelta(days=95)).isoformat(),
        },
    ]
    
    print("Creating contacts...")
    contact_ids = {}
    
    for contact_data in contacts:
        priority = contact_data.pop('priority')
        last_contact = contact_data.pop('last_contact')
        
        contact_id = create_contact(**contact_data)
        contact_ids[contact_data['email']] = contact_id
        
        # Update relationship with priority and last contact
        update_relationship(
            contact_id,
            priority=priority,
            last_contact_date=last_contact,
            strength='strong' if priority == 'high' else 'medium'
        )
        
        print(f"  ✓ {contact_data['name']} ({contact_data['company']})")
    
    print(f"\nCreated {len(contacts)} contacts\n")
    
    # Create interactions
    print("Creating interactions...")
    
    interactions = [
        {
            'email': 'sarah.chen@nvidia.com',
            'type': 'meeting',
            'date': (date.today() - timedelta(days=15)).isoformat(),
            'summary': 'Discussed AI partnership opportunities at NVIDIA',
            'sentiment': 'positive',
            'follow_up_needed': True,
            'follow_up_date': (date.today() + timedelta(days=7)).isoformat(),
        },
        {
            'email': 'jessica.park@tesla.com',
            'type': 'call',
            'date': (date.today() - timedelta(days=5)).isoformat(),
            'summary': 'Catch-up call about Autopilot progress',
            'sentiment': 'positive',
            'follow_up_needed': False,
        },
        {
            'email': 'robert.kim@anthropic.com',
            'type': 'email',
            'date': (date.today() - timedelta(days=8)).isoformat(),
            'summary': 'Shared paper on RLHF improvements',
            'sentiment': 'neutral',
            'follow_up_needed': False,
        },
        {
            'email': 'm.zhang@openai.com',
            'type': 'linkedin',
            'date': (date.today() - timedelta(days=45)).isoformat(),
            'summary': 'Connected on LinkedIn, commented on his post',
            'sentiment': 'positive',
            'follow_up_needed': True,
            'follow_up_date': (date.today() + timedelta(days=3)).isoformat(),
        },
        {
            'email': 'lisa.wang@sequoiacap.com',
            'type': 'meeting',
            'date': (date.today() - timedelta(days=30)).isoformat(),
            'summary': 'Coffee chat about AI investment trends',
            'sentiment': 'positive',
            'follow_up_needed': True,
            'follow_up_date': (date.today() + timedelta(days=14)).isoformat(),
        },
        {
            'email': 'emily.w@airwallex.com',
            'type': 'email',
            'date': (date.today() - timedelta(days=120)).isoformat(),
            'summary': 'Initial discussion about ML engineer roles',
            'sentiment': 'neutral',
            'follow_up_needed': False,
        },
        {
            'email': 'amanda@google.com',
            'type': 'meeting',
            'date': (date.today() - timedelta(days=60)).isoformat(),
            'summary': 'Google I/O meetup, discussed Gemini capabilities',
            'sentiment': 'positive',
            'follow_up_needed': False,
        },
        {
            'email': 'david.liu@bytedance.com',
            'type': 'call',
            'date': (date.today() - timedelta(days=200)).isoformat(),
            'summary': 'Discussed AI infra challenges at ByteDance',
            'sentiment': 'neutral',
            'follow_up_needed': False,
        },
    ]
    
    for interaction_data in interactions:
        email = interaction_data.pop('email')
        contact_id = contact_ids.get(email)
        if contact_id:
            # Rename parameters to match function signature
            interaction_type = interaction_data.pop('type')
            date_str = interaction_data.pop('date')
            create_interaction(
                contact_id=contact_id,
                interaction_type=interaction_type,
                date_str=date_str,
                **interaction_data
            )
    
    print(f"  Created {len(interactions)} interactions\n")
    
    # Create reminders
    print("Creating reminders...")
    
    reminders = [
        {
            'email': 'sarah.chen@nvidia.com',
            'task': 'Follow up on NVIDIA partnership proposal',
            'due_date': (date.today() + timedelta(days=7)).isoformat(),
        },
        {
            'email': 'm.zhang@openai.com',
            'task': 'Send Michael the alignment paper he requested',
            'due_date': (date.today() + timedelta(days=3)).isoformat(),
        },
        {
            'email': 'lisa.wang@sequoiacap.com',
            'task': 'Share Q2 metrics with Lisa for potential intro',
            'due_date': (date.today() + timedelta(days=14)).isoformat(),
        },
        {
            'email': 'david.liu@bytedance.com',
            'task': 'Reconnect - haven\'t talked in 6+ months',
            'due_date': (date.today() + timedelta(days=1)).isoformat(),
        },
        {
            'email': 'emily.w@airwallex.com',
            'task': 'Check if Airwallex still hiring ML engineers',
            'due_date': (date.today() + timedelta(days=5)).isoformat(),
        },
        {
            'email': 't.anderson@meta.com',
            'task': 'Reach out - been 8+ months since last contact',
            'due_date': (date.today() + timedelta(days=10)).isoformat(),
        },
    ]
    
    for reminder_data in reminders:
        email = reminder_data.pop('email')
        contact_id = contact_ids.get(email)
        if contact_id:
            create_reminder(contact_id, **reminder_data)
    
    print(f"  Created {len(reminders)} reminders\n")
    
    print("✅ Database seeded successfully!")
    print(f"\n📊 Summary:")
    print(f"   Contacts: {len(contacts)}")
    print(f"   Interactions: {len(interactions)}")
    print(f"   Reminders: {len(reminders)}")
    print(f"\n📁 Database location: {DB_PATH}")
    print(f"\nTry these commands:")
    print(f"   python3 cli.py health")
    print(f"   python3 cli.py search 'who do I know at NVIDIA?'")
    print(f"   python3 cli.py stale --months 3")
    print(f"   python3 cli.py remind --list")


if __name__ == '__main__':
    seed_database()
