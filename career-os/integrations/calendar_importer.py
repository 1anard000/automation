#!/usr/bin/env python3
"""
Calendar Importer for Career OS CRM
Extracts contacts and interactions from Google Calendar (API or ICS export)
"""

import os
import sys
import re
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import hashlib

try:
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

try:
    import icalendar
    ICAL_AVAILABLE = True
except ImportError:
    ICAL_AVAILABLE = False


class CalendarImporter:
    def __init__(self, db_path: str, dry_run: bool = False):
        self.db_path = db_path
        self.dry_run = dry_run
        self.contacts_imported = 0
        self.interactions_logged = 0
        self.duplicates_merged = 0
        self.events_processed = 0
        self.events_skipped = 0
        
    def connect_db(self):
        """Connect to CRM database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_schema(self, conn):
        """Initialize database schema if not exists"""
        cursor = conn.cursor()
        
        # Contacts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT UNIQUE,
                title TEXT,
                company TEXT,
                phone TEXT,
                linkedin_url TEXT,
                connection_date TEXT,
                relationship_score REAL DEFAULT 0.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Interactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                type TEXT,
                date TEXT,
                subject TEXT,
                sentiment TEXT,
                topics TEXT,
                raw_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts(id)
            )
        ''')
        
        conn.commit()
    
    def categorize_meeting(self, title: str, description: str, attendees: List[str]) -> str:
        """Categorize meeting type"""
        text = (title + ' ' + description).lower()
        
        # Check attendee count
        attendee_count = len([a for a in attendees if '@' in a])
        
        # Interview indicators
        if any(word in text for word in ['interview', 'technical interview', 'screening', 'phone screen']):
            return 'interview'
        
        # Conference indicators
        if any(word in text for word in ['conference', 'summit', 'meetup', 'event', 'talk']):
            return 'conference'
        
        # Networking indicators
        if any(word in text for word in ['coffee', 'lunch', 'meet', 'networking', 'intro']):
            return 'networking'
        
        # 1:1 vs group
        if attendee_count <= 2:
            return '1:1'
        else:
            return 'group'
    
    def extract_email_from_attendee(self, attendee: str) -> Optional[str]:
        """Extract email from attendee string"""
        if not attendee:
            return None
        
        # Try to extract email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', attendee)
        if email_match:
            return email_match.group(0)
        
        # If it looks like an email already
        if '@' in attendee and '.' in attendee:
            return attendee
        
        return None
    
    def extract_name_from_attendee(self, attendee: str) -> Optional[str]:
        """Extract name from attendee string"""
        if not attendee:
            return None
        
        # Format: "Name <email>" or "Name (email)"
        name_match = re.search(r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*[<(]', attendee)
        if name_match:
            return name_match.group(1)
        
        # Just return None if we can't extract a clean name
        return None
    
    def extract_topics(self, title: str, description: str) -> List[str]:
        """Extract topics from meeting"""
        text = (title + ' ' + description).lower()
        
        topics = []
        topic_keywords = {
            'job search': ['job', 'position', 'role', 'opportunity', 'hiring', 'interview'],
            'project': ['project', 'deliverable', 'milestone', 'deadline', 'sprint', 'planning'],
            'introduction': ['intro', 'introduce', 'meet', 'connect', 'referral'],
            'meeting': ['meeting', 'call', 'zoom', 'teams', 'schedule', 'sync'],
            'follow-up': ['follow up', 'followup', 'checking in', 'touch base'],
            'networking': ['networking', 'event', 'conference', 'meetup'],
            'partnership': ['partnership', 'collaboration', 'collaborate', 'partner'],
            'sales': ['sales', 'purchase', 'buy', 'pricing', 'quote', 'proposal', 'demo'],
            'support': ['support', 'help', 'issue', 'bug', 'problem'],
            'recruiting': ['recruiter', 'recruiting', 'talent', 'candidate', 'hiring'],
            'mentoring': ['mentor', 'mentoring', 'coaching', 'advice', 'guidance'],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def get_or_create_contact(self, conn, email: str, name: str = None,
                              title: str = None, company: str = None) -> int:
        """Get existing contact or create new one"""
        cursor = conn.cursor()
        
        # Try to find by email
        cursor.execute('SELECT id FROM contacts WHERE email = ?', (email,))
        row = cursor.fetchone()
        
        if row:
            self.duplicates_merged += 1
            contact_id = row['id']
            
            # Update if we have better info
            updates = []
            params = []
            
            if name:
                updates.append('name = ?')
                params.append(name)
            if title:
                updates.append('title = ?')
                params.append(title)
            if company:
                updates.append('company = ?')
                params.append(company)
            
            if updates:
                updates.append('updated_at = CURRENT_TIMESTAMP')
                params.append(email)
                cursor.execute(f'''
                    UPDATE contacts 
                    SET {', '.join(updates)}
                    WHERE email = ?
                ''', params)
                conn.commit()
        else:
            # Create new contact
            cursor.execute('''
                INSERT INTO contacts (name, email, title, company)
                VALUES (?, ?, ?, ?)
            ''', (name, email, title, company))
            conn.commit()
            contact_id = cursor.lastrowid
            self.contacts_imported += 1
        
        return contact_id
    
    def log_interaction(self, conn, contact_id: int, event_date: str,
                       title: str, description: str, meeting_type: str,
                       location: str = None, attendees: List[str] = None):
        """Log a meeting interaction"""
        cursor = conn.cursor()
        
        topics = self.extract_topics(title, description)
        
        cursor.execute('''
            INSERT INTO interactions 
            (contact_id, type, date, subject, sentiment, topics, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            contact_id,
            f'meeting_{meeting_type}',
            event_date,
            title[:500] if title else '',
            'neutral',  # Meetings are generally neutral
            json.dumps(topics),
            json.dumps({
                'title': title,
                'description': description[:500] if description else '',
                'location': location,
                'attendees': attendees or [],
                'meeting_type': meeting_type
            })
        ))
        
        conn.commit()
        self.interactions_logged += 1
    
    def process_calendar_event(self, conn, event: dict):
        """Process a single calendar event"""
        try:
            # Extract event details
            summary = event.get('summary', '')
            description = event.get('description', '')
            location = event.get('location', '')
            
            # Parse start time
            start = event.get('start', {})
            if 'dateTime' in start:
                event_date = start['dateTime']
            elif 'date' in start:
                event_date = start['date']
            else:
                event_date = datetime.now().isoformat()
            
            # Extract attendees
            attendees = event.get('attendees', [])
            attendee_emails = []
            
            for attendee in attendees:
                email = attendee.get('email')
                if email:
                    attendee_emails.append(email)
                    
                    # Extract name if available
                    name = attendee.get('displayName')
                    
                    # Get or create contact
                    contact_id = self.get_or_create_contact(conn, email, name)
                    
                    # Log interaction for this attendee
                    meeting_type = self.categorize_meeting(
                        summary, description, attendee_emails
                    )
                    
                    self.log_interaction(
                        conn, contact_id, event_date, summary, description,
                        meeting_type, location, attendee_emails
                    )
            
            self.events_processed += 1
            
        except Exception as e:
            self.events_skipped += 1
            if self.events_skipped < 10:
                print(f"⚠️  Error processing event: {e}")
    
    def import_from_api(self, credentials_path: str = None, 
                       token_path: str = 'token.json',
                       months: int = 12, limit: int = None):
        """Import from Google Calendar API"""
        print(f"📅 Connecting to Google Calendar API...")
        
        if not GOOGLE_API_AVAILABLE:
            print("❌ Google API libraries not installed. Run: pip3 install -r requirements.txt")
            sys.exit(1)
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No data will be imported")
            return
        
        SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        creds = None
        
        # Load or refresh credentials
        if token_path and os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not credentials_path:
                    print("❌ Credentials file required for first-time auth")
                    print("   Download from: https://console.developers.google.com/")
                    sys.exit(1)
                
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open(token_path, 'w') as f:
                f.write(creds.to_json())
        
        # Build service
        service = build('calendar', 'v3', credentials=creds)
        
        # Calculate time range
        time_min = (datetime.now() - timedelta(days=months*30)).isoformat() + 'Z'
        time_max = datetime.now().isoformat() + 'Z'
        
        print(f"Fetching events from {time_min[:10]} to {time_max[:10]}...")
        
        conn = self.connect_db()
        self.init_schema(conn)
        
        # Fetch events
        page_token = None
        total_events = 0
        
        while True:
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime',
                pageToken=page_token
            ).execute()
            
            events = events_result.get('items', [])
            total_events += len(events)
            
            if limit and total_events > limit:
                events = events[:limit - (total_events - len(events))]
            
            # Process events
            iterator = tqdm(events) if tqdm else events
            for event in iterator:
                self.process_calendar_event(conn, event)
                
                if tqdm and self.events_processed % 50 == 0:
                    iterator.set_postfix({
                        'contacts': self.contacts_imported,
                        'interactions': self.interactions_logged
                    })
            
            page_token = events_result.get('nextPageToken')
            if not page_token or (limit and total_events >= limit):
                break
        
        conn.close()
        print(f"Processed {total_events} events")
    
    def import_from_ics(self, ics_path: str, limit: int = None):
        """Import from ICS file export"""
        print(f"📅 Importing from ICS file: {ics_path}")
        
        if not ICAL_AVAILABLE:
            print("❌ icalendar library not installed. Run: pip3 install icalendar")
            sys.exit(1)
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No data will be imported")
            return
        
        if not os.path.exists(ics_path):
            raise FileNotFoundError(f"ICS file not found: {ics_path}")
        
        conn = self.connect_db()
        self.init_schema(conn)
        
        # Parse ICS file
        with open(ics_path, 'rb') as f:
            cal = icalendar.Calendar.from_ical(f.read())
        
        # Extract events
        events = []
        for component in cal.walk('VEVENT'):
            events.append(component)
        
        total_events = len(events)
        print(f"Found {total_events} events in ICS file")
        
        if limit:
            events = events[:limit]
            print(f"Processing first {limit} events...")
        
        # Process events
        iterator = tqdm(events) if tqdm else events
        for event in iterator:
            try:
                # Convert to dict-like structure
                event_dict = {
                    'summary': str(event.get('SUMMARY', '')),
                    'description': str(event.get('DESCRIPTION', '')),
                    'location': str(event.get('LOCATION', '')),
                    'start': {
                        'dateTime': event.get('DTSTART').to_ical().decode() if event.get('DTSTART') else None,
                        'date': None
                    },
                    'attendees': []
                }
                
                # Parse attendees
                attendees = event.get('ATTENDEE')
                if attendees:
                    if not isinstance(attendees, list):
                        attendees = [attendees]
                    
                    for attendee in attendees:
                        attendee_str = str(attendee)
                        email = self.extract_email_from_attendee(attendee_str)
                        if email:
                            event_dict['attendees'].append({
                                'email': email,
                                'displayName': self.extract_name_from_attendee(attendee_str)
                            })
                
                self.process_calendar_event(conn, event_dict)
                
                if tqdm and self.events_processed % 50 == 0:
                    iterator.set_postfix({
                        'contacts': self.contacts_imported,
                        'interactions': self.interactions_logged
                    })
                    
            except Exception as e:
                self.events_skipped += 1
                if self.events_skipped < 10:
                    print(f"⚠️  Error processing event: {e}")
        
        conn.close()
    
    def get_summary(self) -> Dict:
        """Get import summary"""
        return {
            'events_processed': self.events_processed,
            'events_skipped': self.events_skipped,
            'contacts_imported': self.contacts_imported,
            'interactions_logged': self.interactions_logged,
            'duplicates_merged': self.duplicates_merged
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Calendar Importer for Career OS CRM')
    parser.add_argument('--db', required=True, help='Path to CRM database')
    parser.add_argument('--api', action='store_true', help='Import via Google Calendar API')
    parser.add_argument('--ics', help='Import from ICS file export')
    parser.add_argument('--credentials', help='Google API credentials file (for API import)')
    parser.add_argument('--token', default='token.json', help='OAuth token file (default: token.json)')
    parser.add_argument('--months', type=int, default=12, help='Months to import (default: 12)')
    parser.add_argument('--limit', type=int, help='Limit number of events to process')
    parser.add_argument('--dry-run', action='store_true', help='Preview without importing')
    
    args = parser.parse_args()
    
    importer = CalendarImporter(args.db, dry_run=args.dry_run)
    
    try:
        if args.api:
            importer.import_from_api(args.credentials, args.token, args.months, args.limit)
        elif args.ics:
            importer.import_from_ics(args.ics, args.limit)
        else:
            print("❌ Specify --api or --ics")
            sys.exit(1)
        
        summary = importer.get_summary()
        print("\n✅ Import Complete!")
        print(f"   Events processed: {summary['events_processed']}")
        print(f"   Events skipped: {summary['events_skipped']}")
        print(f"   Contacts imported: {summary['contacts_imported']}")
        print(f"   Interactions logged: {summary['interactions_logged']}")
        print(f"   Duplicates merged: {summary['duplicates_merged']}")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
