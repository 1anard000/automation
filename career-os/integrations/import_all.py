#!/usr/bin/env python3
"""
Unified Import Pipeline for Career OS CRM
Runs all importers in sequence with deduplication and merging
"""

import os
import sys
import sqlite3
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

# Import local modules
from gmail_importer import GmailImporter
from calendar_importer import CalendarImporter
from linkedin_importer import LinkedInImporter


class UnifiedImporter:
    def __init__(self, db_path: str, dry_run: bool = False):
        self.db_path = db_path
        self.dry_run = dry_run
        self.start_time = datetime.now()
        
        # Importer instances
        self.gmail_importer = None
        self.calendar_importer = None
        self.linkedin_importer = None
        
        # Summary stats
        self.summary = {
            'gmail': None,
            'calendar': None,
            'linkedin': None,
            'total_contacts': 0,
            'total_interactions': 0,
            'total_duplicates_merged': 0,
            'deduplication_stats': {}
        }
    
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
        
        # Import log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS import_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                import_date TEXT DEFAULT CURRENT_TIMESTAMP,
                source TEXT,
                records_imported INTEGER,
                records_skipped INTEGER,
                details TEXT
            )
        ''')
        
        conn.commit()
    
    def log_import(self, conn, source: str, imported: int, skipped: int, details: Dict = None):
        """Log import operation"""
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO import_log (source, records_imported, records_skipped, details)
            VALUES (?, ?, ?, ?)
        ''', (source, imported, skipped, json.dumps(details or {})))
        conn.commit()
    
    def deduplicate_contacts(self, conn):
        """Deduplicate contacts across all sources"""
        print("\n🔄 Deduplicating contacts...")
        
        cursor = conn.cursor()
        
        # Find duplicate emails
        cursor.execute('''
            SELECT email, COUNT(*) as count, GROUP_CONCAT(id) as ids
            FROM contacts
            WHERE email IS NOT NULL AND email != ''
            GROUP BY email
            HAVING count > 1
        ''')
        
        email_duplicates = cursor.fetchall()
        email_dedup_count = 0
        
        for dup in email_duplicates:
            ids = [int(id.strip()) for id in dup['ids'].split(',')]
            
            # Keep the first ID, merge others into it
            keep_id = ids[0]
            merge_ids = ids[1:]
            
            # Merge interactions
            for merge_id in merge_ids:
                cursor.execute('''
                    UPDATE interactions SET contact_id = ? WHERE contact_id = ?
                ''', (keep_id, merge_id))
                
                # Delete the duplicate contact
                cursor.execute('DELETE FROM contacts WHERE id = ?', (merge_id,))
                email_dedup_count += 1
        
        # Find duplicate names (fuzzy matching)
        cursor.execute('''
            SELECT name, COUNT(*) as count, GROUP_CONCAT(id) as ids
            FROM contacts
            WHERE name IS NOT NULL AND name != '' AND email IS NULL
            GROUP BY LOWER(name)
            HAVING count > 1
        ''')
        
        name_duplicates = cursor.fetchall()
        name_dedup_count = 0
        
        for dup in name_duplicates:
            ids = [int(id.strip()) for id in dup['ids'].split(',')]
            
            # Keep the first ID, merge others
            keep_id = ids[0]
            merge_ids = ids[1:]
            
            for merge_id in merge_ids:
                cursor.execute('''
                    UPDATE interactions SET contact_id = ? WHERE contact_id = ?
                ''', (keep_id, merge_id))
                
                cursor.execute('DELETE FROM contacts WHERE id = ?', (merge_id,))
                name_dedup_count += 1
        
        conn.commit()
        
        total_dedup = email_dedup_count + name_dedup_count
        print(f"   Removed {total_dedup} duplicate contacts")
        print(f"   - Email duplicates: {email_dedup_count}")
        print(f"   - Name duplicates: {name_dedup_count}")
        
        self.summary['deduplication_stats'] = {
            'email_duplicates': email_dedup_count,
            'name_duplicates': name_dedup_count,
            'total_removed': total_dedup
        }
    
    def calculate_relationship_scores(self, conn):
        """Calculate relationship health scores for all contacts"""
        print("\n📊 Calculating relationship scores...")
        
        cursor = conn.cursor()
        
        # Get all contacts with interactions
        cursor.execute('''
            SELECT c.id, c.name, c.email,
                   COUNT(i.id) as interaction_count,
                   SUM(CASE WHEN i.sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
                   SUM(CASE WHEN i.sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count,
                   MAX(i.date) as last_interaction
            FROM contacts c
            LEFT JOIN interactions i ON c.id = i.contact_id
            GROUP BY c.id
        ''')
        
        contacts = cursor.fetchall()
        
        for contact in contacts:
            interaction_count = contact['interaction_count'] or 0
            positive_count = contact['positive_count'] or 0
            negative_count = contact['negative_count'] or 0
            
            # Calculate score (-100 to 100)
            if interaction_count == 0:
                score = 0
            else:
                # Base score from sentiment ratio
                sentiment_ratio = (positive_count - negative_count) / interaction_count
                base_score = sentiment_ratio * 50
                
                # Bonus for interaction frequency
                frequency_bonus = min(interaction_count * 2, 30)
                
                # Recency bonus (more recent = higher)
                recency_bonus = 0
                if contact['last_interaction']:
                    try:
                        last_date = datetime.fromisoformat(contact['last_interaction'])
                        days_since = (datetime.now() - last_date).days
                        if days_since < 30:
                            recency_bonus = 20
                        elif days_since < 90:
                            recency_bonus = 10
                        elif days_since < 180:
                            recency_bonus = 5
                    except:
                        pass
                
                score = base_score + frequency_bonus + recency_bonus
                score = max(-100, min(100, score))  # Clamp to -100 to 100
            
            # Update contact score
            cursor.execute('''
                UPDATE contacts SET relationship_score = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (score, contact['id']))
        
        conn.commit()
        print(f"   Updated scores for {len(contacts)} contacts")
    
    def run_gmail_import(self, email: str = None, password: str = None,
                        takeout_path: str = None, months: int = 12,
                        limit: int = None):
        """Run Gmail importer"""
        print("\n" + "="*60)
        print("📧 GMAIL IMPORT")
        print("="*60)
        
        if not takeout_path and not (email and password):
            print("⚠️  Skipping Gmail import (no credentials or takeout path)")
            return
        
        self.gmail_importer = GmailImporter(self.db_path, dry_run=self.dry_run)
        
        try:
            if takeout_path:
                self.gmail_importer.import_from_takeout(takeout_path, limit)
            else:
                self.gmail_importer.import_from_imap(email, password, months, limit)
            
            self.summary['gmail'] = self.gmail_importer.get_summary()
            
            # Log import
            if not self.dry_run:
                conn = self.connect_db()
                self.log_import(conn, 'gmail', 
                              self.summary['gmail']['contacts_imported'],
                              self.summary['gmail']['emails_skipped'],
                              self.summary['gmail'])
                conn.close()
        
        except Exception as e:
            print(f"❌ Gmail import failed: {e}")
            self.summary['gmail'] = {'error': str(e)}
    
    def run_calendar_import(self, credentials_path: str = None,
                           ics_path: str = None, months: int = 12,
                           limit: int = None):
        """Run Calendar importer"""
        print("\n" + "="*60)
        print("📅 CALENDAR IMPORT")
        print("="*60)
        
        if not ics_path and not credentials_path:
            print("⚠️  Skipping Calendar import (no credentials or ICS path)")
            return
        
        self.calendar_importer = CalendarImporter(self.db_path, dry_run=self.dry_run)
        
        try:
            if ics_path:
                self.calendar_importer.import_from_ics(ics_path, limit)
            else:
                self.calendar_importer.import_from_api(credentials_path, months=months, limit=limit)
            
            self.summary['calendar'] = self.calendar_importer.get_summary()
            
            # Log import
            if not self.dry_run:
                conn = self.connect_db()
                self.log_import(conn, 'calendar',
                              self.summary['calendar']['contacts_imported'],
                              self.summary['calendar']['events_skipped'],
                              self.summary['calendar'])
                conn.close()
        
        except Exception as e:
            print(f"❌ Calendar import failed: {e}")
            self.summary['calendar'] = {'error': str(e)}
    
    def run_linkedin_import(self, export_path: str, limit: int = None):
        """Run LinkedIn importer"""
        print("\n" + "="*60)
        print("💼 LINKEDIN IMPORT")
        print("="*60)
        
        if not export_path:
            print("⚠️  Skipping LinkedIn import (no export path)")
            return
        
        self.linkedin_importer = LinkedInImporter(self.db_path, dry_run=self.dry_run)
        
        try:
            self.linkedin_importer.import_connections(export_path, limit)
            
            self.summary['linkedin'] = self.linkedin_importer.get_summary()
            
            # Log import
            if not self.dry_run:
                conn = self.connect_db()
                self.log_import(conn, 'linkedin',
                              self.summary['linkedin']['contacts_imported'],
                              self.summary['linkedin']['connections_skipped'],
                              self.summary['linkedin'])
                conn.close()
        
        except Exception as e:
            print(f"❌ LinkedIn import failed: {e}")
            self.summary['linkedin'] = {'error': str(e)}
    
    def run_all(self, gmail_takeout: str = None, gmail_email: str = None,
                gmail_password: str = None, calendar_ics: str = None,
                calendar_credentials: str = None, linkedin_export: str = None,
                months: int = 12, limit: int = None):
        """Run all importers in sequence"""
        print("🚀 Starting Unified Import Pipeline")
        print(f"   Database: {self.db_path}")
        print(f"   Dry Run: {self.dry_run}")
        print(f"   Time Range: Last {months} months")
        
        # Initialize database
        if not self.dry_run:
            conn = self.connect_db()
            self.init_schema(conn)
            conn.close()
        
        # Run importers
        self.run_gmail_import(gmail_email, gmail_password, gmail_takeout, months, limit)
        self.run_calendar_import(calendar_credentials, calendar_ics, months, limit)
        self.run_linkedin_import(linkedin_export, limit)
        
        # Post-processing
        if not self.dry_run:
            conn = self.connect_db()
            self.deduplicate_contacts(conn)
            self.calculate_relationship_scores(conn)
            
            # Calculate totals
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM contacts')
            self.summary['total_contacts'] = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM interactions')
            self.summary['total_interactions'] = cursor.fetchone()['count']
            
            conn.close()
        
        # Print summary
        self.print_summary()
        
        return self.summary
    
    def print_summary(self):
        """Print import summary"""
        print("\n" + "="*60)
        print("✅ IMPORT COMPLETE")
        print("="*60)
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"   Total time: {elapsed:.1f} seconds")
        
        print("\n📊 Summary:")
        
        if self.summary['gmail']:
            if 'error' not in self.summary['gmail']:
                print(f"\n   Gmail:")
                print(f"      Emails processed: {self.summary['gmail']['emails_processed']}")
                print(f"      Contacts imported: {self.summary['gmail']['contacts_imported']}")
                print(f"      Interactions logged: {self.summary['gmail']['interactions_logged']}")
        
        if self.summary['calendar']:
            if 'error' not in self.summary['calendar']:
                print(f"\n   Calendar:")
                print(f"      Events processed: {self.summary['calendar']['events_processed']}")
                print(f"      Contacts imported: {self.summary['calendar']['contacts_imported']}")
                print(f"      Interactions logged: {self.summary['calendar']['interactions_logged']}")
        
        if self.summary['linkedin']:
            if 'error' not in self.summary['linkedin']:
                print(f"\n   LinkedIn:")
                print(f"      Connections processed: {self.summary['linkedin']['connections_processed']}")
                print(f"      Contacts imported: {self.summary['linkedin']['contacts_imported']}")
        
        if self.summary['deduplication_stats']:
            print(f"\n   Deduplication:")
            print(f"      Duplicates merged: {self.summary['deduplication_stats']['total_removed']}")
        
        print(f"\n   Totals:")
        print(f"      Total contacts: {self.summary['total_contacts']}")
        print(f"      Total interactions: {self.summary['total_interactions']}")
        
        print("\n💾 Data stored in:", self.db_path)
        print("\n✨ Next steps:")
        print("   - Review contacts in CRM")
        print("   - Check relationship scores")
        print("   - Explore interaction history")


def main():
    parser = argparse.ArgumentParser(
        description='Unified Import Pipeline for Career OS CRM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Import from all sources
  python3 import_all.py --gmail-takeout ~/Downloads/gmail.mbox \\
                        --calendar-ics ~/Downloads/calendar.ics \\
                        --linkedin-export ~/Downloads/linkedin.json \\
                        --output ../crm/crm.db

  # Gmail via IMAP (requires app password)
  python3 import_all.py --gmail-email user@gmail.com \\
                        --gmail-password "app-password" \\
                        --output ../crm/crm.db

  # Calendar via Google API
  python3 import_all.py --calendar-credentials credentials.json \\
                        --output ../crm/crm.db

  # Dry run (preview only)
  python3 import_all.py --gmail-takeout ~/Downloads/gmail.mbox \\
                        --dry-run --output ../crm/crm.db
        '''
    )
    
    # Output
    parser.add_argument('--output', required=True, help='Output database path')
    
    # Gmail options
    parser.add_argument('--gmail', action='store_true', help='Enable Gmail import')
    parser.add_argument('--gmail-takeout', help='Gmail Takeout MBOX file path')
    parser.add_argument('--gmail-email', help='Gmail email address (for IMAP)')
    parser.add_argument('--gmail-password', help='Gmail password/App Password (for IMAP)')
    
    # Calendar options
    parser.add_argument('--calendar', action='store_true', help='Enable Calendar import')
    parser.add_argument('--calendar-ics', help='Calendar ICS export file path')
    parser.add_argument('--calendar-credentials', help='Google API credentials file (for API)')
    
    # LinkedIn options
    parser.add_argument('--linkedin', action='store_true', help='Enable LinkedIn import')
    parser.add_argument('--linkedin-export', help='LinkedIn connections export JSON path')
    
    # Common options
    parser.add_argument('--months', type=int, default=12, help='Months to import (default: 12)')
    parser.add_argument('--limit', type=int, help='Limit records per source')
    parser.add_argument('--dry-run', action='store_true', help='Preview without importing')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not any([args.gmail, args.calendar, args.linkedin]):
        if not any([args.gmail_takeout, args.gmail_email, args.calendar_ics, 
                   args.calendar_credentials, args.linkedin_export]):
            print("❌ No import sources specified. Use --gmail, --calendar, --linkedin")
            print("   or provide specific file paths.")
            sys.exit(1)
    
    # Create importer and run
    importer = UnifiedImporter(args.output, dry_run=args.dry_run)
    
    try:
        importer.run_all(
            gmail_takeout=args.gmail_takeout,
            gmail_email=args.gmail_email,
            gmail_password=args.gmail_password,
            calendar_ics=args.calendar_ics,
            calendar_credentials=args.calendar_credentials,
            linkedin_export=args.linkedin_export,
            months=args.months,
            limit=args.limit
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Import interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
