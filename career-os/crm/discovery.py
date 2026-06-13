"""
Contact Discovery Parser for Personal CRM.
Parses Gmail exports (MBOX/JSON) and Google Calendar exports (ICS/JSON) to extract contacts.
Filters noise and deduplicates contacts.
"""

import re
import json
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Set, Tuple
from pathlib import Path
from collections import defaultdict
import email
from email.header import decode_header

try:
    from icalendar import Calendar
    ICAL_AVAILABLE = True
except ImportError:
    ICAL_AVAILABLE = False
    print("Warning: icalendar not installed. ICS parsing disabled.")
    print("Install with: pip install icalendar")

from database import create_contact, get_contact_by_email, update_contact


# Noise patterns to filter out
NOISE_EMAIL_PATTERNS = [
    r'^no[-_]?reply@',
    r'^noreply@',
    r'^do[-_]?not[-_]?reply@',
    r'^notifications@',
    r'^notification@',
    r'^auto[-_]?confirm@',
    r'^mailer[-_]?daemon@',
    r'^postmaster@',
    r'^bounce@',
    r'^marketing@',
    r'^newsletter@',
    r'^news@',
    r'^updates@',
    r'^alerts@',
    r'^support@.*\.zendesk\.com',
    r'^support@.*\.freshdesk\.com',
    r'^noreply@.*\.linkedin\.com',
    r'^noreply@.*\.twitter\.com',
    r'^noreply@.*\.facebook\.com',
    r'^noreply@.*\.google\.com',
    r'^calendar@.*\.google\.com',
]

# Compile patterns for performance
NOISE_REGEX = [re.compile(p, re.IGNORECASE) for p in NOISE_EMAIL_PATTERNS]

# Company domain mappings (common email domains)
COMPANY_DOMAINS = {
    'gmail.com': None,  # Personal
    'yahoo.com': None,
    'hotmail.com': None,
    'outlook.com': None,
    'icloud.com': None,
    'me.com': None,
    'mac.com': None,
    '163.com': None,
    '126.com': None,
    'qq.com': None,
}


def is_noise_email(email_addr: str) -> bool:
    """Check if email is from a noise source (marketing, auto-reply, etc.)."""
    for pattern in NOISE_REGEX:
        if pattern.match(email_addr):
            return True
    return False


def extract_name_from_email(email_addr: str) -> Optional[str]:
    """Extract probable name from email address."""
    # john.doe@company.com -> John Doe
    local_part = email_addr.split('@')[0]
    # Remove common prefixes
    local_part = re.sub(r'^(the|real|mr|ms|mrs|dr)\.?', '', local_part, flags=re.IGNORECASE)
    # Convert separators to spaces
    name = re.sub(r'[._-]', ' ', local_part)
    # Title case
    name = name.title()
    # Remove digits
    name = re.sub(r'\d+', '', name)
    # Clean up
    name = ' '.join(name.split())
    return name if len(name) > 1 else None


def extract_company_from_email(email_addr: str) -> Optional[str]:
    """Extract company name from email domain."""
    domain = email_addr.split('@')[-1].lower()
    
    # Skip personal email domains
    if domain in COMPANY_DOMAINS:
        return None
    
    # Remove TLD and common suffixes
    company = domain.replace('.com', '').replace('.cn', '').replace('.io', '')
    company = company.replace('.co', '').replace('.net', '').replace('.org', '')
    
    # Convert to title case
    company = re.sub(r'[._-]', ' ', company)
    company = company.title()
    
    return company if len(company) > 1 else None


def normalize_email(email_addr: str) -> str:
    """Normalize email address (lowercase, remove + aliases)."""
    email_addr = email_addr.lower().strip()
    
    # Remove + aliasing (john+tag@gmail.com -> john@gmail.com)
    if '+' in email_addr:
        local, domain = email_addr.split('@')
        local = local.split('+')[0]
        email_addr = f"{local}@{domain}"
    
    return email_addr


def parse_email_address(addr: str) -> Tuple[Optional[str], str]:
    """Parse email address string into (name, email)."""
    # Handle "Name <email@domain.com>" format
    match = re.match(r'["\']?([^"<\']+)["\']?\s*<([^>]+)>', addr)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    
    # Handle "email@domain.com" format
    if '@' in addr:
        addr = addr.strip()
        name = extract_name_from_email(addr)
        return name, addr
    
    return None, addr


class GmailParser:
    """Parse Gmail exports (MBOX or JSON format)."""
    
    def __init__(self):
        self.contacts = {}  # email -> contact data
        self.email_threads = defaultdict(list)  # email -> list of messages
    
    def parse_mbox(self, mbox_path: Path) -> List[Dict[str, Any]]:
        """Parse MBOX file and extract contacts."""
        if not mbox_path.exists():
            raise FileNotFoundError(f"MBOX file not found: {mbox_path}")
        
        with open(mbox_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Split by "From " line (MBOX delimiter)
        messages = re.split(r'^From ', content, flags=re.MULTILINE)
        
        for msg_str in messages[1:]:  # Skip first empty split
            try:
                msg = email.message_from_string(msg_str)
                self._process_email_message(msg)
            except Exception as e:
                continue
        
        return list(self.contacts.values())
    
    def parse_json(self, json_path: Path) -> List[Dict[str, Any]]:
        """Parse Gmail JSON export (Takeout format)."""
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        messages = []
        if isinstance(data, list):
            messages = data
        elif isinstance(data, dict):
            messages = data.get('messages', data.get('emails', []))
        
        for msg in messages:
            self._process_json_message(msg)
        
        return list(self.contacts.values())
    
    def _process_email_message(self, msg) -> None:
        """Process a single email message."""
        # Extract sender
        from_addr = msg.get('From', '')
        sender_name, sender_email = parse_email_address(from_addr)
        
        if not sender_email or '@' not in sender_email:
            return
        
        sender_email = normalize_email(sender_email)
        
        # Skip noise
        if is_noise_email(sender_email):
            return
        
        # Extract recipients
        to_addrs = msg.get('To', '')
        cc_addrs = msg.get('Cc', '')
        
        # Process sender
        self._add_contact(sender_name, sender_email)
        
        # Process recipients
        for addr in to_addrs.split(',') + cc_addrs.split(','):
            addr = addr.strip()
            if addr:
                name, email_addr = parse_email_address(addr)
                if email_addr and '@' in email_addr:
                    email_addr = normalize_email(email_addr)
                    if not is_noise_email(email_addr):
                        self._add_contact(name, email_addr)
        
        # Store thread info
        subject = msg.get('Subject', '')
        date_str = msg.get('Date', '')
        self.email_threads[sender_email].append({
            'subject': subject,
            'date': date_str,
            'from': sender_name or sender_email
        })
    
    def _process_json_message(self, msg: Dict[str, Any]) -> None:
        """Process a JSON email message."""
        # Handle Gmail Takeout JSON format
        header = msg.get('header', msg)
        
        from_addr = header.get('from', header.get('From', ''))
        to_addr = header.get('to', header.get('To', ''))
        subject = header.get('subject', header.get('Subject', ''))
        date_str = header.get('date', header.get('Date', ''))
        
        sender_name, sender_email = parse_email_address(from_addr)
        
        if not sender_email or '@' not in sender_email:
            return
        
        sender_email = normalize_email(sender_email)
        
        if is_noise_email(sender_email):
            return
        
        self._add_contact(sender_name, sender_email)
        
        # Process recipients
        for addr in to_addr.split(','):
            addr = addr.strip()
            if addr:
                name, email_addr = parse_email_address(addr)
                if email_addr and '@' in email_addr:
                    email_addr = normalize_email(email_addr)
                    if not is_noise_email(email_addr):
                        self._add_contact(name, email_addr)
    
    def _add_contact(self, name: Optional[str], email_addr: str) -> None:
        """Add or update contact in local cache."""
        email_addr = normalize_email(email_addr)
        
        if email_addr in self.contacts:
            # Update with better name if available
            existing = self.contacts[email_addr]
            if name and (not existing.get('name') or len(name) > len(existing['name'])):
                existing['name'] = name
        else:
            self.contacts[email_addr] = {
                'name': name or extract_name_from_email(email_addr),
                'email': email_addr,
                'company': extract_company_from_email(email_addr),
                'source': 'gmail'
            }


class CalendarParser:
    """Parse Google Calendar exports (ICS or JSON format)."""
    
    def __init__(self):
        self.contacts = {}  # email -> contact data
        self.meetings = []  # list of meeting data
    
    def parse_ics(self, ics_path: Path) -> List[Dict[str, Any]]:
        """Parse ICS calendar file and extract contacts."""
        if not ICAL_AVAILABLE:
            print("Warning: icalendar not available. Install with: pip install icalendar")
            return []
        
        if not ics_path.exists():
            raise FileNotFoundError(f"ICS file not found: {ics_path}")
        
        with open(ics_path, 'rb') as f:
            cal = Calendar.from_ical(f.read())
        
        for component in cal.walk():
            if component.name == "VEVENT":
                self._process_event(component)
        
        return list(self.contacts.values())
    
    def parse_json(self, json_path: Path) -> List[Dict[str, Any]]:
        """Parse Calendar JSON export."""
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        events = []
        if isinstance(data, list):
            events = data
        elif isinstance(data, dict):
            events = data.get('events', data.get('items', []))
        
        for event in events:
            self._process_json_event(event)
        
        return list(self.contacts.values())
    
    def _process_event(self, event) -> None:
        """Process an ICS VEVENT component."""
        summary = str(event.get('SUMMARY', ''))
        description = str(event.get('DESCRIPTION', ''))
        location = str(event.get('LOCATION', ''))
        
        # Extract attendees
        attendees = event.get('ATTENDEE', [])
        if not isinstance(attendees, list):
            attendees = [attendees]
        
        for attendee in attendees:
            email_addr = str(attendee).replace('mailto:', '').split('@')[0] + '@' + str(attendee).split('@')[-1]
            email_addr = normalize_email(email_addr)
            
            if is_noise_email(email_addr):
                continue
            
            # Try to get name from CN parameter
            name = attendee.params.get('CN', [None])[0] if hasattr(attendee, 'params') else None
            
            self._add_contact(name, email_addr, 'calendar')
        
        # Extract organizer
        organizer = event.get('ORGANIZER')
        if organizer:
            email_addr = str(organizer).replace('mailto:', '')
            email_addr = normalize_email(email_addr)
            
            if not is_noise_email(email_addr):
                name = organizer.params.get('CN', [None])[0] if hasattr(organizer, 'params') else None
                self._add_contact(name, email_addr, 'calendar')
        
        # Store meeting info
        self.meetings.append({
            'summary': summary,
            'description': description,
            'location': location,
            'attendees': [str(a) for a in attendees]
        })
    
    def _process_json_event(self, event: Dict[str, Any]) -> None:
        """Process a JSON calendar event."""
        summary = event.get('summary', event.get('Summary', ''))
        description = event.get('description', event.get('Description', ''))
        location = event.get('location', event.get('Location', ''))
        
        # Extract attendees
        attendees = event.get('attendees', event.get('Attendees', []))
        for attendee in attendees:
            if isinstance(attendee, dict):
                email_addr = attendee.get('email', attendee.get('Email', ''))
                name = attendee.get('displayName', attendee.get('DisplayName', ''))
            else:
                name, email_addr = parse_email_address(str(attendee))
            
            if not email_addr or '@' not in email_addr:
                continue
            
            email_addr = normalize_email(email_addr)
            
            if is_noise_email(email_addr):
                continue
            
            self._add_contact(name, email_addr, 'calendar')
        
        # Extract organizer
        organizer = event.get('organizer', event.get('Organizer'))
        if organizer:
            if isinstance(organizer, dict):
                email_addr = organizer.get('email', organizer.get('Email', ''))
                name = organizer.get('displayName', organizer.get('DisplayName', ''))
            else:
                name, email_addr = parse_email_address(str(organizer))
            
            if email_addr and '@' in email_addr:
                email_addr = normalize_email(email_addr)
                if not is_noise_email(email_addr):
                    self._add_contact(name, email_addr, 'calendar')
    
    def _add_contact(self, name: Optional[str], email_addr: str, source: str) -> None:
        """Add or update contact in local cache."""
        email_addr = normalize_email(email_addr)
        
        if email_addr in self.contacts:
            existing = self.contacts[email_addr]
            if name and (not existing.get('name') or len(name) > len(existing['name'])):
                existing['name'] = name
        else:
            self.contacts[email_addr] = {
                'name': name or extract_name_from_email(email_addr),
                'email': email_addr,
                'company': extract_company_from_email(email_addr),
                'source': source
            }


def deduplicate_contacts(contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate contacts based on email, name similarity, and company.
    Returns merged contact list.
    """
    # Group by normalized email first
    by_email = {}
    for contact in contacts:
        email_addr = normalize_email(contact['email'])
        if email_addr in by_email:
            # Merge
            existing = by_email[email_addr]
            for key, value in contact.items():
                if value and (not existing.get(key) or (key == 'name' and len(value) > len(existing[key]))):
                    existing[key] = value
        else:
            by_email[email_addr] = contact.copy()
    
    return list(by_email.values())


def import_contacts(
    gmail_path: Optional[Path] = None,
    calendar_path: Optional[Path] = None,
    dry_run: bool = True,
    db_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Import contacts from Gmail and Calendar exports.
    
    Args:
        gmail_path: Path to Gmail export (MBOX or JSON)
        calendar_path: Path to Calendar export (ICS or JSON)
        dry_run: If True, don't write to database
        db_path: Database path
    
    Returns:
        Summary of imported contacts
    """
    all_contacts = {}
    
    # Parse Gmail
    if gmail_path:
        print(f"Parsing Gmail export: {gmail_path}")
        parser = GmailParser()
        
        if gmail_path.suffix.lower() == '.mbox':
            contacts = parser.parse_mbox(gmail_path)
        elif gmail_path.suffix.lower() == '.json':
            contacts = parser.parse_json(gmail_path)
        else:
            # Try JSON first, then MBOX
            try:
                contacts = parser.parse_json(gmail_path)
            except:
                contacts = parser.parse_mbox(gmail_path)
        
        for contact in contacts:
            email_addr = normalize_email(contact['email'])
            if email_addr not in all_contacts:
                all_contacts[email_addr] = contact
            else:
                # Merge
                existing = all_contacts[email_addr]
                for key, value in contact.items():
                    if value and not existing.get(key):
                        existing[key] = value
        
        print(f"  Found {len(contacts)} contacts from Gmail")
    
    # Parse Calendar
    if calendar_path:
        print(f"Parsing Calendar export: {calendar_path}")
        parser = CalendarParser()
        
        if calendar_path.suffix.lower() == '.ics':
            contacts = parser.parse_ics(calendar_path)
        elif calendar_path.suffix.lower() == '.json':
            contacts = parser.parse_json(calendar_path)
        else:
            try:
                contacts = parser.parse_json(calendar_path)
            except:
                contacts = parser.parse_ics(calendar_path)
        
        for contact in contacts:
            email_addr = normalize_email(contact['email'])
            if email_addr not in all_contacts:
                all_contacts[email_addr] = contact
            else:
                # Merge - calendar might have better meeting context
                existing = all_contacts[email_addr]
                for key, value in contact.items():
                    if value and not existing.get(key):
                        existing[key] = value
        
        print(f"  Found {len(contacts)} contacts from Calendar")
    
    # Deduplicate
    contacts_list = list(all_contacts.values())
    contacts_list = deduplicate_contacts(contacts_list)
    
    # Filter out contacts with no name
    contacts_list = [c for c in contacts_list if c.get('name')]
    
    print(f"\nTotal unique contacts: {len(contacts_list)}")
    
    # Import to database
    if not dry_run:
        imported = 0
        updated = 0
        for contact in contacts_list:
            existing = get_contact_by_email(contact['email'], db_path)
            if existing:
                # Update existing
                update_data = {k: v for k, v in contact.items() 
                              if k not in ['email', 'source'] and v}
                if update_data:
                    update_contact(existing['id'], **update_data)
                    updated += 1
            else:
                # Create new
                create_contact(
                    name=contact.get('name', ''),
                    email=contact.get('email'),
                    company=contact.get('company'),
                    db_path=db_path
                )
                imported += 1
        
        print(f"Imported: {imported}, Updated: {updated}")
    
    return {
        'total': len(contacts_list),
        'contacts': contacts_list
    }


if __name__ == "__main__":
    # Test discovery
    from database import init_db
    
    init_db()
    
    print("Contact Discovery Test")
    print("=" * 50)
    
    # Test with sample data
    test_contacts = [
        {'name': 'John Doe', 'email': 'john.doe@nvidia.com'},
        {'name': 'Jane Smith', 'email': 'jane@openai.com'},
        {'name': 'Bob Wilson', 'email': 'bob.wilson@tesla.com'},
        {'name': 'Alice Chen', 'email': 'alice@airwallex.com'},
    ]
    
    print("Sample contacts:")
    for contact in test_contacts:
        print(f"  {contact['name']} <{contact['email']}>")
    
    # Test noise filtering
    print("\nNoise filtering test:")
    noise_emails = [
        'noreply@google.com',
        'marketing@example.com',
        'notifications@github.com',
        'john.doe@company.com'  # Not noise
    ]
    
    for email_addr in noise_emails:
        is_noise = is_noise_email(email_addr)
        print(f"  {email_addr}: {'NOISE' if is_noise else 'VALID'}")
