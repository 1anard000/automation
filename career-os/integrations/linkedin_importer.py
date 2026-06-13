#!/usr/bin/env python3
"""
LinkedIn Contact Sync for Career OS CRM
Parses LinkedIn connections export (JSON from Google Takeout or LinkedIn export)
"""

import os
import sys
import re
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


class LinkedInImporter:
    def __init__(self, db_path: str, dry_run: bool = False):
        self.db_path = db_path
        self.dry_run = dry_run
        self.contacts_imported = 0
        self.contacts_updated = 0
        self.duplicates_merged = 0
        self.connections_processed = 0
        self.connections_skipped = 0
        self.interactions_logged = 0
        
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
    
    def parse_linkedin_export(self, export_path: str) -> List[Dict]:
        """Parse LinkedIn connections export JSON"""
        if not os.path.exists(export_path):
            raise FileNotFoundError(f"LinkedIn export not found: {export_path}")
        
        with open(export_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different export formats
        connections = []
        
        # Format 1: LinkedIn's direct export (Connections.json)
        if isinstance(data, dict) and 'connections' in data:
            connections = data['connections']
        
        # Format 2: Simple array
        elif isinstance(data, list):
            connections = data
        
        # Format 3: Google Takeout format
        elif isinstance(data, dict) and 'Connected At' in data:
            connections = [data]
        
        print(f"Found {len(connections)} connections in export")
        return connections
    
    def extract_linkedin_url(self, profile_url: str, first_name: str, last_name: str) -> Optional[str]:
        """Extract or construct LinkedIn URL"""
        if profile_url:
            # Clean up URL
            url = profile_url.strip()
            if url.startswith('http'):
                return url
            else:
                return f"https://www.linkedin.com/{url}"
        
        # Try to construct from name (fallback)
        if first_name and last_name:
            # This is a guess, not reliable
            return None
        
        return None
    
    def parse_connection_date(self, date_str: str) -> Optional[str]:
        """Parse connection date from various formats"""
        if not date_str:
            return None
        
        # Try various formats
        formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%b %d, %Y',
            '%B %d, %Y',
            '%Y-%m-%dT%H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).isoformat()
            except:
                continue
        
        # If all else fails, return as-is
        return date_str
    
    def match_contact_by_name(self, conn, first_name: str, last_name: str) -> Optional[int]:
        """Try to match contact by name"""
        cursor = conn.cursor()
        
        # Try full name match
        full_name = f"{first_name} {last_name}"
        cursor.execute('SELECT id FROM contacts WHERE name = ?', (full_name,))
        row = cursor.fetchone()
        
        if row:
            return row['id']
        
        # Try partial name match
        cursor.execute('''
            SELECT id FROM contacts 
            WHERE name LIKE ? OR name LIKE ?
        ''', (f"%{first_name}%", f"%{last_name}%"))
        
        rows = cursor.fetchall()
        if rows:
            # Return first match (could be improved with better matching logic)
            return rows[0]['id']
        
        return None
    
    def get_or_create_contact(self, conn, name: str, email: str = None,
                              title: str = None, company: str = None,
                              linkedin_url: str = None, 
                              connection_date: str = None) -> int:
        """Get existing contact or create new one"""
        cursor = conn.cursor()
        
        # Try to find by email first
        if email:
            cursor.execute('SELECT id FROM contacts WHERE email = ?', (email,))
            row = cursor.fetchone()
            
            if row:
                self.duplicates_merged += 1
                contact_id = row['id']
                
                # Update with LinkedIn info
                updates = []
                params = []
                
                if linkedin_url:
                    updates.append('linkedin_url = ?')
                    params.append(linkedin_url)
                if connection_date:
                    updates.append('connection_date = ?')
                    params.append(connection_date)
                if name and not cursor.execute('SELECT name FROM contacts WHERE id = ?', (contact_id,)).fetchone()['name']:
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
                    params.append(contact_id)
                    cursor.execute(f'''
                        UPDATE contacts 
                        SET {', '.join(updates)}
                        WHERE id = ?
                    ''', params)
                    conn.commit()
                
                return contact_id
        
        # Try to find by name
        if name:
            cursor.execute('SELECT id FROM contacts WHERE name = ?', (name,))
            row = cursor.fetchone()
            
            if row:
                self.duplicates_merged += 1
                contact_id = row['id']
                
                # Update with LinkedIn info
                updates = []
                params = []
                
                if email:
                    updates.append('email = ?')
                    params.append(email)
                if linkedin_url:
                    updates.append('linkedin_url = ?')
                    params.append(linkedin_url)
                if connection_date:
                    updates.append('connection_date = ?')
                    params.append(connection_date)
                if title:
                    updates.append('title = ?')
                    params.append(title)
                if company:
                    updates.append('company = ?')
                    params.append(company)
                
                if updates:
                    updates.append('updated_at = CURRENT_TIMESTAMP')
                    params.append(contact_id)
                    cursor.execute(f'''
                        UPDATE contacts 
                        SET {', '.join(updates)}
                        WHERE id = ?
                    ''', params)
                    conn.commit()
                
                return contact_id
        
        # Create new contact
        cursor.execute('''
            INSERT INTO contacts (name, email, title, company, linkedin_url, connection_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, email, title, company, linkedin_url, connection_date))
        conn.commit()
        self.contacts_imported += 1
        
        return cursor.lastrowid
    
    def log_connection_interaction(self, conn, contact_id: int, connection_date: str):
        """Log LinkedIn connection as interaction"""
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO interactions 
            (contact_id, type, date, subject, sentiment, topics, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            contact_id,
            'linkedin_connection',
            connection_date or datetime.now().isoformat(),
            'LinkedIn Connection',
            'neutral',
            json.dumps(['networking']),
            json.dumps({'source': 'linkedin', 'type': 'connection'})
        ))
        
        conn.commit()
        self.interactions_logged += 1
    
    def import_connections(self, export_path: str, limit: int = None):
        """Import LinkedIn connections from export"""
        print(f"💼 Importing LinkedIn connections from: {export_path}")
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No data will be imported")
            return
        
        connections = self.parse_linkedin_export(export_path)
        
        if limit:
            connections = connections[:limit]
            print(f"Processing first {limit} connections...")
        
        conn = self.connect_db()
        self.init_schema(conn)
        
        # Process connections
        iterator = tqdm(connections) if tqdm else connections
        for connection in iterator:
            try:
                # Extract connection info based on export format
                first_name = connection.get('firstName', '')
                last_name = connection.get('lastName', '')
                name = f"{first_name} {last_name}".strip()
                
                # Handle format where name is a single field
                if not name and connection.get('name'):
                    name = connection.get('name')
                
                email = connection.get('emailAddress', connection.get('email', ''))
                title = connection.get('position', connection.get('title', ''))
                company = connection.get('companyName', connection.get('company', ''))
                profile_url = connection.get('profileUrl', connection.get('profile_url', ''))
                connected_at = connection.get('connectedAt', connection.get('Connected At', ''))
                
                # Parse connection date
                connection_date = self.parse_connection_date(connected_at)
                
                # Extract LinkedIn URL
                linkedin_url = self.extract_linkedin_url(profile_url, first_name, last_name)
                
                # Get or create contact
                contact_id = self.get_or_create_contact(
                    conn, name, email, title, company,
                    linkedin_url, connection_date
                )
                
                # Log connection interaction
                self.log_connection_interaction(conn, contact_id, connection_date)
                
                self.connections_processed += 1
                
                if tqdm and self.connections_processed % 50 == 0:
                    iterator.set_postfix({
                        'contacts': self.contacts_imported,
                        'updated': self.contacts_updated,
                        'merged': self.duplicates_merged
                    })
                    
            except Exception as e:
                self.connections_skipped += 1
                if self.connections_skipped < 10:
                    print(f"⚠️  Error processing connection: {e}")
        
        conn.close()
    
    def get_summary(self) -> Dict:
        """Get import summary"""
        return {
            'connections_processed': self.connections_processed,
            'connections_skipped': self.connections_skipped,
            'contacts_imported': self.contacts_imported,
            'contacts_updated': self.contacts_updated,
            'duplicates_merged': self.duplicates_merged
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Importer for Career OS CRM')
    parser.add_argument('--db', required=True, help='Path to CRM database')
    parser.add_argument('--export', required=True, help='Path to LinkedIn connections export JSON')
    parser.add_argument('--limit', type=int, help='Limit number of connections to process')
    parser.add_argument('--dry-run', action='store_true', help='Preview without importing')
    
    args = parser.parse_args()
    
    importer = LinkedInImporter(args.db, dry_run=args.dry_run)
    
    try:
        importer.import_connections(args.export, args.limit)
        
        summary = importer.get_summary()
        print("\n✅ Import Complete!")
        print(f"   Connections processed: {summary['connections_processed']}")
        print(f"   Connections skipped: {summary['connections_skipped']}")
        print(f"   Contacts imported: {summary['contacts_imported']}")
        print(f"   Contacts updated: {summary['contacts_updated']}")
        print(f"   Duplicates merged: {summary['duplicates_merged']}")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
