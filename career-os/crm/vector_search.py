"""
Vector Search module for Personal CRM.
Uses sentence-transformers to embed contact profiles and enable semantic search.
Supports queries like "who do I know at NVIDIA?" or "haven't talked to in 6 months".
"""

import sqlite3
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import json

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("Warning: sentence-transformers not installed. Vector search disabled.")
    print("Install with: pip install sentence-transformers")

from database import get_connection, DB_PATH, list_contacts, get_all_relationships


EMBEDDING_DIM = 384  # Default for all-MiniLM-L6-v2
MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDINGS_DB_PATH = Path(__file__).parent / "embeddings.json"


class VectorSearch:
    """Vector search engine for contact profiles."""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.embeddings_path = EMBEDDINGS_DB_PATH
        self.model = None
        self.embeddings = {}  # contact_id -> embedding vector
        self._load_model()
        self._load_embeddings()
    
    def _load_model(self) -> None:
        """Load sentence-transformers model."""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(MODEL_NAME)
            except Exception as e:
                print(f"Warning: Failed to load model: {e}")
                self.model = None
        else:
            self.model = None
    
    def _load_embeddings(self) -> None:
        """Load existing embeddings from disk."""
        if self.embeddings_path.exists():
            try:
                with open(self.embeddings_path, 'r') as f:
                    data = json.load(f)
                    self.embeddings = {int(k): v for k, v in data.items()}
            except Exception as e:
                print(f"Warning: Failed to load embeddings: {e}")
                self.embeddings = {}
    
    def _save_embeddings(self) -> None:
        """Save embeddings to disk."""
        try:
            with open(self.embeddings_path, 'w') as f:
                json.dump(self.embeddings, f)
        except Exception as e:
            print(f"Warning: Failed to save embeddings: {e}")
    
    def _create_profile_text(self, contact: Dict[str, Any]) -> str:
        """Create text profile for embedding from contact data."""
        parts = []
        
        if contact.get('name'):
            parts.append(f"Name: {contact['name']}")
        if contact.get('email'):
            parts.append(f"Email: {contact['email']}")
        if contact.get('company'):
            parts.append(f"Company: {contact['company']}")
        if contact.get('title'):
            parts.append(f"Title: {contact['title']}")
        if contact.get('location'):
            parts.append(f"Location: {contact['location']}")
        if contact.get('how_we_met'):
            parts.append(f"Met: {contact['how_we_met']}")
        if contact.get('notes'):
            parts.append(f"Notes: {contact['notes']}")
        
        return ". ".join(parts)
    
    def _embed_text(self, text: str) -> List[float]:
        """Embed text using sentence-transformers or fallback."""
        if self.model:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        else:
            # Fallback: simple hash-based pseudo-embedding
            # This allows the system to work without sentence-transformers
            np.random.seed(hash(text) % (2**32))
            return np.random.randn(EMBEDDING_DIM).tolist()
    
    def index_contact(self, contact_id: int, contact: Optional[Dict[str, Any]] = None) -> List[float]:
        """Index a contact's profile. Returns the embedding."""
        if contact is None:
            with get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
                row = cursor.fetchone()
                if not row:
                    return []
                contact = dict(row)
        
        profile_text = self._create_profile_text(contact)
        embedding = self._embed_text(profile_text)
        self.embeddings[contact_id] = embedding
        self._save_embeddings()
        return embedding
    
    def index_all_contacts(self) -> int:
        """Index all contacts. Returns count of indexed contacts."""
        contacts = list_contacts(self.db_path)
        count = 0
        for contact in contacts:
            self.index_contact(contact['id'], contact)
            count += 1
        return count
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a_np = np.array(a)
        b_np = np.array(b)
        dot_product = np.dot(a_np, b_np)
        norm_a = np.linalg.norm(a_np)
        norm_b = np.linalg.norm(b_np)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot_product / (norm_a * norm_b))
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search contacts by semantic query.
        Returns list of (contact, similarity_score) tuples.
        """
        if not self.embeddings:
            self.index_all_contacts()
        
        query_embedding = self._embed_text(query)
        
        results = []
        for contact_id, embedding in self.embeddings.items():
            similarity = self._cosine_similarity(query_embedding, embedding)
            if similarity > 0:  # Only include positive matches
                contact = get_contact_by_id(contact_id, self.db_path)
                if contact:
                    results.append((contact, similarity))
        
        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def search_stale_relationships(self, months: int = 6) -> List[Dict[str, Any]]:
        """
        Find contacts not contacted in specified months.
        This is a temporal query, not semantic.
        """
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, r.last_contact_date, r.health_score, r.strength, r.priority
                FROM contacts c
                JOIN relationships r ON c.id = r.contact_id
                WHERE r.last_contact_date IS NULL OR r.last_contact_date < ?
                ORDER BY r.last_contact_date ASC NULLS FIRST
            """, (cutoff_str,))
            return [dict(row) for row in cursor.fetchall()]
    
    def search_by_company(self, company: str) -> List[Tuple[Dict[str, Any], float]]:
        """Search contacts by company name (semantic + keyword match)."""
        # First try semantic search
        semantic_results = self.search(f"works at {company}", top_k=20)
        
        # Also do keyword search for exact matches
        keyword_results = []
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM contacts
                WHERE company LIKE ? OR notes LIKE ?
            """, (f"%{company}%", f"%{company}%"))
            for row in cursor.fetchall():
                contact = dict(row)
                # Check if not already in semantic results
                if not any(c['id'] == contact['id'] for c, _ in semantic_results):
                    keyword_results.append((contact, 0.5))  # Lower score for keyword-only
        
        # Combine and deduplicate
        all_results = semantic_results + keyword_results
        seen = set()
        unique_results = []
        for contact, score in all_results:
            if contact['id'] not in seen:
                seen.add(contact['id'])
                unique_results.append((contact, score))
        
        return sorted(unique_results, key=lambda x: x[1], reverse=True)


def get_contact_by_id(contact_id: int, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Get contact by ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def search_contacts(query: str, top_k: int = 10, db_path: Optional[Path] = None) -> List[Tuple[Dict[str, Any], float]]:
    """Convenience function for semantic search."""
    searcher = VectorSearch(db_path)
    return searcher.search(query, top_k)


def find_stale_contacts(months: int = 6, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Convenience function for finding stale relationships."""
    searcher = VectorSearch(db_path)
    return searcher.search_stale_relationships(months)


if __name__ == "__main__":
    # Test vector search
    from database import init_db
    
    init_db()
    searcher = VectorSearch()
    
    print("Vector Search Test")
    print("=" * 50)
    
    # Index all contacts
    count = searcher.index_all_contacts()
    print(f"Indexed {count} contacts")
    
    # Test search
    query = "who do I know at NVIDIA?"
    print(f"\nQuery: {query}")
    results = searcher.search(query, top_k=5)
    for contact, score in results:
        print(f"  {contact['name']} ({contact.get('company', 'N/A')}) - Score: {score:.3f}")
    
    # Test stale search
    print("\nStale contacts (6+ months):")
    stale = searcher.search_stale_relationships(6)
    for contact in stale[:5]:
        print(f"  {contact['name']} - Last contact: {contact.get('last_contact_date', 'Never')}")
