"""
Database module for Personal CRM.
Manages SQLite schema and CRUD operations for contacts, interactions, relationships, and reminders.
"""

import sqlite3
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from pathlib import Path


DB_PATH = Path(__file__).parent / "crm.db"


@contextmanager
def get_connection(db_path: Optional[Path] = None):
    """Context manager for database connections."""
    db = db_path or DB_PATH
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Optional[Path] = None) -> None:
    """Initialize database with all required tables."""
    db = db_path or DB_PATH
    
    with get_connection(db) as conn:
        cursor = conn.cursor()
        
        # Contacts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                company TEXT,
                title TEXT,
                linkedin_url TEXT,
                location TEXT,
                how_we_met TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL,
                type TEXT CHECK(type IN ('email', 'meeting', 'call', 'linkedin', 'other')),
                date DATE NOT NULL,
                summary TEXT,
                sentiment TEXT CHECK(sentiment IN ('positive', 'neutral', 'negative')),
                follow_up_needed BOOLEAN DEFAULT 0,
                follow_up_date DATE,
                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
            )
        """)
        
        # Relationships table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER UNIQUE NOT NULL,
                health_score INTEGER DEFAULT 50 CHECK(health_score >= 0 AND health_score <= 100),
                last_contact_date DATE,
                strength TEXT CHECK(strength IN ('weak', 'medium', 'strong')) DEFAULT 'weak',
                priority TEXT CHECK(priority IN ('low', 'medium', 'high')) DEFAULT 'medium',
                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
            )
        """)
        
        # Reminders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                task TEXT NOT NULL,
                due_date DATE NOT NULL,
                status TEXT CHECK(status IN ('pending', 'done', 'snoozed')) DEFAULT 'pending',
                snooze_until DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE SET NULL
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contacts_company ON contacts(company)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_interactions_contact_id ON interactions(contact_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_interactions_date ON interactions(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_due_date ON reminders(due_date)")


# ============== Contacts CRUD ==============

def create_contact(
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    company: Optional[str] = None,
    title: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    location: Optional[str] = None,
    how_we_met: Optional[str] = None,
    notes: Optional[str] = None,
    db_path: Optional[Path] = None
) -> int:
    """Create a new contact and return the ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contacts (name, email, phone, company, title, linkedin_url, location, how_we_met, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, email, phone, company, title, linkedin_url, location, how_we_met, notes))
        
        contact_id = cursor.lastrowid
        
        # Initialize relationship record
        cursor.execute("""
            INSERT INTO relationships (contact_id, health_score, last_contact_date, strength, priority)
            VALUES (?, 50, NULL, 'weak', 'medium')
        """, (contact_id,))
        
        return contact_id


def get_contact(contact_id: int, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Get a contact by ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_contact_by_email(email: str, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Get a contact by email."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contacts WHERE email = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_contact(contact_id: int, **kwargs) -> bool:
    """Update contact fields. Returns True if updated."""
    if not kwargs:
        return False
    
    fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
    values = list(kwargs.values()) + [contact_id]
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE contacts SET {fields}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, values)
        return cursor.rowcount > 0


def delete_contact(contact_id: int, db_path: Optional[Path] = None) -> bool:
    """Delete a contact by ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        return cursor.rowcount > 0


def search_contacts(query: str, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Search contacts by name, email, company, or notes."""
    search_pattern = f"%{query}%"
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM contacts
            WHERE name LIKE ? OR email LIKE ? OR company LIKE ? OR notes LIKE ?
            ORDER BY name
        """, (search_pattern, search_pattern, search_pattern, search_pattern))
        return [dict(row) for row in cursor.fetchall()]


def list_contacts(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """List all contacts."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contacts ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]


# ============== Interactions CRUD ==============

def create_interaction(
    contact_id: int,
    interaction_type: str,
    date_str: str,
    summary: Optional[str] = None,
    sentiment: str = "neutral",
    follow_up_needed: bool = False,
    follow_up_date: Optional[str] = None,
    db_path: Optional[Path] = None
) -> int:
    """Create a new interaction and return the ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO interactions (contact_id, type, date, summary, sentiment, follow_up_needed, follow_up_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (contact_id, interaction_type, date_str, summary, sentiment, follow_up_needed, follow_up_date))
        
        interaction_id = cursor.lastrowid
        
        # Update relationship last_contact_date
        cursor.execute("""
            UPDATE relationships SET last_contact_date = ?
            WHERE contact_id = ?
        """, (date_str, contact_id))
        
        return interaction_id


def get_interactions(contact_id: int, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Get all interactions for a contact."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM interactions
            WHERE contact_id = ?
            ORDER BY date DESC
        """, (contact_id,))
        return [dict(row) for row in cursor.fetchall()]


# ============== Relationships CRUD ==============

def get_relationship(contact_id: int, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Get relationship data for a contact."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM relationships WHERE contact_id = ?", (contact_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_relationship(contact_id: int, **kwargs) -> bool:
    """Update relationship fields. Returns True if updated."""
    if not kwargs:
        return False
    
    fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
    values = list(kwargs.values()) + [contact_id]
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE relationships SET {fields}
            WHERE contact_id = ?
        """, values)
        return cursor.rowcount > 0


def get_all_relationships(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Get all relationships with contact info."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.name, c.email, c.company, r.health_score, r.last_contact_date, 
                   r.strength, r.priority
            FROM contacts c
            JOIN relationships r ON c.id = r.contact_id
            ORDER BY r.health_score ASC
        """)
        return [dict(row) for row in cursor.fetchall()]


# ============== Reminders CRUD ==============

def create_reminder(
    contact_id: Optional[int],
    task: str,
    due_date: str,
    status: str = "pending",
    db_path: Optional[Path] = None
) -> int:
    """Create a new reminder and return the ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reminders (contact_id, task, due_date, status)
            VALUES (?, ?, ?, ?)
        """, (contact_id, task, due_date, status))
        return cursor.lastrowid


def get_reminders(status: str = "pending", db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Get reminders by status."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, c.name as contact_name, c.email as contact_email
            FROM reminders r
            LEFT JOIN contacts c ON r.contact_id = c.id
            WHERE r.status = ?
            ORDER BY r.due_date
        """, (status,))
        return [dict(row) for row in cursor.fetchall()]


def update_reminder(reminder_id: int, **kwargs) -> bool:
    """Update reminder fields. Returns True if updated."""
    if not kwargs:
        return False
    
    fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
    values = list(kwargs.values()) + [reminder_id]
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE reminders SET {fields}
            WHERE id = ?
        """, values)
        return cursor.rowcount > 0


def delete_reminder(reminder_id: int, db_path: Optional[Path] = None) -> bool:
    """Delete a reminder by ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        return cursor.rowcount > 0


if __name__ == "__main__":
    # Initialize database when run directly
    init_db()
    print(f"Database initialized at {DB_PATH}")
