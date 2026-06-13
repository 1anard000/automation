#!/usr/bin/env python3
"""
Gmail Importer for Career OS CRM
Extracts contacts and interactions from Gmail (IMAP or Google Takeout)
"""

import os
import sys
import re
import sqlite3
import email
import imaplib
import json
from email.header import decode_header
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import hashlib

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

# Noise patterns to filter out
NOISE_PATTERNS = [
    r'^no-reply@',
    r'^noreply@',
    r'^marketing@',
    r'^newsletter@',
    r'^notifications@',
    r'^auto-confirm@',
    r'^receipts@',
    r'^orders@',
    r'^shipping@',
    r'^support@.*\.com$',
    r'^.*-bounce@',
    r'^.*-notifications@',
]

# Common spam/automated senders
NOISE_DOMAINS = [
    'linkedin.com',  # Will be handled by LinkedIn importer
    'facebook.com',
    'twitter.com',
    'instagram.com',
    'amazon.com',
    'ebay.com',
    'paypal.com',
    'receipts',
    'orders',
    'notifications',
]

class GmailImporter:
    def __init__(self, db_path: str, dry_run: bool = False):
        self.db_path = db_path
        self.dry_run = dry_run
        self.contacts_imported = 0
        self.interactions_logged = 0
        self.duplicates_merged = 0
        self.emails_processed = 0
        self.emails_skipped = 0
        
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
    
    def decode_header_value(self, header_value):
        """Decode email header values with encoding"""
        if not header_value:
            return ""
        
        decoded_parts = []
        for part, encoding in decode_header(header_value):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
                except:
                    decoded_parts.append(part.decode('utf-8', errors='ignore'))
            else:
                decoded_parts.append(part)
        
        return ''.join(decoded_parts)
    
    def is_noise_email(self, email_address: str) -> bool:
        """Check if email is from automated/noise source"""
        if not email_address:
            return True
        
        email_lower = email_address.lower()
        
        # Check patterns
        for pattern in NOISE_PATTERNS:
            if re.match(pattern, email_lower):
                return True
        
        # Check domains
        for domain in NOISE_DOMAINS:
            if domain in email_lower:
                return True
        
        return False
    
    def extract_email_addresses(self, header_value: str) -> List[str]:
        """Extract email addresses from header field"""
        if not header_value:
            return []
        
        emails = []
        # Match email addresses in various formats
        pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        matches = re.findall(pattern, header_value)
        emails.extend(matches)
        
        return emails
    
    def parse_email_signature(self, body: str) -> Optional[Dict]:
        """Extract contact info from email signature"""
        signature_info = {}
        
        # Common signature patterns
        patterns = [
            # Name and title
            r'^[-_]*\s*([A-Z][a-z]+\s+[A-Z][a-z]+)\s*$',
            # Title at company
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*\n?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*(?:at|@)\s*([A-Za-z\s]+)',
            # Phone number
            r'(\+?[\d\s\-\(\)]{10,})',
            # LinkedIn URL
            r'(linkedin\.com/in/[\w\-]+)',
        ]
        
        # Look for signature block (usually at end)
        lines = body.split('\n')
        signature_start = -1
        
        for i, line in enumerate(lines[-10:]):  # Check last 10 lines
            if '--' in line or 'Regards' in line or 'Best' in line or 'Thanks' in line:
                signature_start = len(lines) - 10 + i
                break
        
        if signature_start >= 0:
            signature_text = '\n'.join(lines[signature_start:])
            
            # Extract phone
            phone_match = re.search(r'(\+?[\d\s\-\(\)]{10,})', signature_text)
            if phone_match:
                signature_info['phone'] = phone_match.group(1).strip()
            
            # Extract LinkedIn
            linkedin_match = re.search(r'(linkedin\.com/in/[\w\-]+)', signature_text)
            if linkedin_match:
                signature_info['linkedin_url'] = f"https://{linkedin_match.group(1)}"
        
        return signature_info if signature_info else None
    
    def analyze_sentiment(self, subject: str, body: str) -> str:
        """Simple sentiment analysis (positive/neutral/negative)"""
        text = (subject + ' ' + body).lower()
        
        positive_words = [
            'great', 'excellent', 'wonderful', 'fantastic', 'awesome',
            'thanks', 'thank you', 'appreciate', 'pleasure', 'happy',
            'excited', 'looking forward', 'congratulations', 'congrats',
            'success', 'successful', 'achieved', 'completed'
        ]
        
        negative_words = [
            'unfortunately', 'sorry', 'problem', 'issue', 'concern',
            'disappointed', 'frustrated', 'angry', 'upset', 'delay',
            'cancel', 'rejected', 'declined', 'failed', 'error'
        ]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count + 2:
            return 'positive'
        elif negative_count > positive_count + 2:
            return 'negative'
        else:
            return 'neutral'
    
    def extract_topics(self, subject: str, body: str) -> List[str]:
        """Extract topics from email content"""
        text = (subject + ' ' + body).lower()
        
        topics = []
        topic_keywords = {
            'job search': ['job', 'position', 'role', 'opportunity', 'hiring', 'interview'],
            'project': ['project', 'deliverable', 'milestone', 'deadline', 'sprint'],
            'introduction': ['intro', 'introduce', 'meet', 'connect', 'referral'],
            'meeting': ['meeting', 'call', 'zoom', 'teams', 'schedule', 'calendar'],
            'follow-up': ['follow up', 'followup', 'checking in', 'touch base'],
            'networking': ['networking', 'event', 'conference', 'meetup'],
            'partnership': ['partnership', 'collaboration', 'collaborate', 'partner'],
            'sales': ['sales', 'purchase', 'buy', 'pricing', 'quote', 'proposal'],
            'support': ['support', 'help', 'issue', 'bug', 'problem'],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def get_or_create_contact(self, conn, email: str, name: str = None, 
                              title: str = None, company: str = None,
                              phone: str = None, linkedin_url: str = None) -> int:
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
            if phone:
                updates.append('phone = ?')
                params.append(phone)
            if linkedin_url:
                updates.append('linkedin_url = ?')
                params.append(linkedin_url)
            
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
                INSERT INTO contacts (name, email, title, company, phone, linkedin_url)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, email, title, company, phone, linkedin_url))
            conn.commit()
            contact_id = cursor.lastrowid
            self.contacts_imported += 1
        
        return contact_id
    
    def log_interaction(self, conn, contact_id: int, email_date: str,
                       subject: str, body: str, direction: str):
        """Log an email interaction"""
        cursor = conn.cursor()
        
        sentiment = self.analyze_sentiment(subject, body)
        topics = self.extract_topics(subject, body)
        
        cursor.execute('''
            INSERT INTO interactions 
            (contact_id, type, date, subject, sentiment, topics, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            contact_id,
            f'email_{direction}',
            email_date,
            subject[:500] if subject else '',
            sentiment,
            json.dumps(topics),
            json.dumps({
                'subject': subject,
                'direction': direction,
                'snippet': body[:1000] if body else ''
            })
        ))
        
        conn.commit()
        self.interactions_logged += 1
    
    def process_email_message(self, conn, msg: email.message.Message) -> List[int]:
        """Process a single email message and extract contacts"""
        contact_ids = []
        
        # Get headers
        from_header = self.decode_header_value(msg.get('From', ''))
        to_header = self.decode_header_value(msg.get('To', ''))
        cc_header = self.decode_header_value(msg.get('CC', ''))
        bcc_header = self.decode_header_value(msg.get('BCC', ''))
        subject = self.decode_header_value(msg.get('Subject', ''))
        date_header = msg.get('Date', '')
        
        # Parse date
        try:
            email_date = datetime.strptime(date_header[:25], '%a, %d %b %Y %H:%M:%S').isoformat()
        except:
            email_date = datetime.now().isoformat()
        
        # Get body
        body = ''
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                pass
        
        # Extract contacts from headers
        all_emails = []
        all_emails.extend(self.extract_email_addresses(from_header))
        all_emails.extend(self.extract_email_addresses(to_header))
        all_emails.extend(self.extract_email_addresses(cc_header))
        all_emails.extend(self.extract_email_addresses(bcc_header))
        
        # Process each email address
        for email_addr in all_emails:
            if self.is_noise_email(email_addr):
                continue
            
            # Try to extract name from header
            name = None
            name_match = re.search(r'([A-Z][a-z]+\s+[A-Z][a-z]+)', from_header)
            if name_match:
                name = name_match.group(1)
            
            # Extract signature info
            sig_info = self.parse_email_signature(body) or {}
            
            # Get or create contact
            contact_id = self.get_or_create_contact(
                conn, email_addr, name,
                sig_info.get('title'),
                sig_info.get('company'),
                sig_info.get('phone'),
                sig_info.get('linkedin_url')
            )
            
            contact_ids.append(contact_id)
            
            # Log interaction for sender
            if email_addr in from_header:
                direction = 'received' if 'To' in msg else 'sent'
                self.log_interaction(conn, contact_id, email_date, subject, body, direction)
        
        return contact_ids
    
    def import_from_imap(self, gmail_user: str, gmail_password: str, 
                        months: int = 12, limit: int = None):
        """Import emails via IMAP"""
        print(f"📧 Connecting to Gmail via IMAP...")
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No data will be imported")
            return
        
        try:
            # Connect to Gmail IMAP
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(gmail_user, gmail_password)
            mail.select('inbox')
            
            # Calculate date threshold
            date_threshold = (datetime.now() - timedelta(days=months*30)).strftime('%d-%b-%Y')
            
            # Search for emails since threshold
            status, messages = mail.search(None, f'(SINCE {date_threshold})')
            email_ids = messages[0].split()
            
            total_emails = len(email_ids)
            print(f"Found {total_emails} emails from last {months} months")
            
            if limit:
                email_ids = email_ids[:limit]
                print(f"Processing first {limit} emails...")
            
            conn = self.connect_db()
            self.init_schema(conn)
            
            # Process emails
            iterator = tqdm(email_ids) if tqdm else email_ids
            for email_id in iterator:
                try:
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    msg = email.message_from_bytes(msg_data[0][1])
                    self.process_email_message(conn, msg)
                    self.emails_processed += 1
                    
                    if tqdm and self.emails_processed % 100 == 0:
                        iterator.set_postfix({
                            'contacts': self.contacts_imported,
                            'interactions': self.interactions_logged
                        })
                except Exception as e:
                    self.emails_skipped += 1
                    if self.emails_skipped < 10:  # Show first 10 errors
                        print(f"⚠️  Error processing email {email_id}: {e}")
            
            conn.close()
            mail.close()
            mail.logout()
            
        except Exception as e:
            print(f"❌ IMAP Error: {e}")
            print("\n💡 Tip: For Gmail, you may need to:")
            print("   1. Enable IMAP in Gmail settings")
            print("   2. Use an App Password instead of regular password")
            print("   3. Or use Google Takeout export instead (see README)")
            raise
    
    def import_from_takeout(self, takeout_path: str, limit: int = None):
        """Import emails from Google Takeout MBOX export"""
        print(f"📦 Importing from Google Takeout: {takeout_path}")
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No data will be imported")
            return
        
        if not os.path.exists(takeout_path):
            raise FileNotFoundError(f"Takeout file not found: {takeout_path}")
        
        conn = self.connect_db()
        self.init_schema(conn)
        
        # Parse MBOX file
        with open(takeout_path, 'rb') as f:
            mbox_content = f.read()
        
        # Split into individual messages
        messages = []
        current_msg = []
        
        for line in mbox_content.split(b'\n'):
            if line.startswith(b'From '):
                if current_msg:
                    messages.append(b'\n'.join(current_msg))
                current_msg = [line]
            else:
                current_msg.append(line)
        
        if current_msg:
            messages.append(b'\n'.join(current_msg))
        
        total_msgs = len(messages)
        print(f"Found {total_msgs} emails in Takeout export")
        
        if limit:
            messages = messages[:limit]
            print(f"Processing first {limit} emails...")
        
        # Process messages
        iterator = tqdm(messages) if tqdm else messages
        for msg_bytes in iterator:
            try:
                msg = email.message_from_bytes(msg_bytes)
                self.process_email_message(conn, msg)
                self.emails_processed += 1
                
                if tqdm and self.emails_processed % 100 == 0:
                    iterator.set_postfix({
                        'contacts': self.contacts_imported,
                        'interactions': self.interactions_logged
                    })
            except Exception as e:
                self.emails_skipped += 1
                if self.emails_skipped < 10:
                    print(f"⚠️  Error processing email: {e}")
        
        conn.close()
    
    def get_summary(self) -> Dict:
        """Get import summary"""
        return {
            'emails_processed': self.emails_processed,
            'emails_skipped': self.emails_skipped,
            'contacts_imported': self.contacts_imported,
            'interactions_logged': self.interactions_logged,
            'duplicates_merged': self.duplicates_merged
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Gmail Importer for Career OS CRM')
    parser.add_argument('--db', required=True, help='Path to CRM database')
    parser.add_argument('--imap', action='store_true', help='Import via IMAP')
    parser.add_argument('--takeout', help='Import from Google Takeout MBOX file')
    parser.add_argument('--email', help='Gmail email address (for IMAP)')
    parser.add_argument('--password', help='Gmail password/App Password (for IMAP)')
    parser.add_argument('--months', type=int, default=12, help='Months to import (default: 12)')
    parser.add_argument('--limit', type=int, help='Limit number of emails to process')
    parser.add_argument('--dry-run', action='store_true', help='Preview without importing')
    
    args = parser.parse_args()
    
    importer = GmailImporter(args.db, dry_run=args.dry_run)
    
    try:
        if args.imap:
            if not args.email or not args.password:
                print("❌ Email and password required for IMAP import")
                sys.exit(1)
            importer.import_from_imap(args.email, args.password, args.months, args.limit)
        elif args.takeout:
            importer.import_from_takeout(args.takeout, args.limit)
        else:
            print("❌ Specify --imap or --takeout")
            sys.exit(1)
        
        summary = importer.get_summary()
        print("\n✅ Import Complete!")
        print(f"   Emails processed: {summary['emails_processed']}")
        print(f"   Emails skipped: {summary['emails_skipped']}")
        print(f"   Contacts imported: {summary['contacts_imported']}")
        print(f"   Interactions logged: {summary['interactions_logged']}")
        print(f"   Duplicates merged: {summary['duplicates_merged']}")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
