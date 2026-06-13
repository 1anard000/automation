"""
Relationship Health Scorer for Personal CRM.
Calculates health scores based on contact frequency, sentiment, reciprocity, and priority.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

from database import (
    get_connection, DB_PATH, get_all_relationships, 
    get_interactions, update_relationship, list_contacts
)


# Health score thresholds
HEALTH_THRESHOLDS = {
    'healthy': 70,    # 🟢 Contacted <30 days
    'warming': 50,    # 🟡 30-90 days
    'stale': 30,      # 🟠 90-180 days
    'cold': 0,        # 🔴 >180 days
}

# Days thresholds
DAYS_THRESHOLDS = {
    'healthy': 30,
    'warming': 90,
    'stale': 180,
}

# Score modifiers
MODIFIERS = {
    'positive_sentiment': 10,
    'neutral_sentiment': 0,
    'negative_sentiment': -10,
    'high_priority_decay': 0.5,    # VIP contacts decay slower
    'medium_priority_decay': 1.0,  # Normal decay
    'low_priority_decay': 1.5,     # Low priority decay faster
    'reciprocity_boost': 15,       # They reach out too
    'frequency_bonus': 5,          # Multiple interactions per month
}


def days_since_contact(last_contact_date: Optional[str]) -> int:
    """Calculate days since last contact."""
    if not last_contact_date:
        return float('inf')
    
    try:
        last_date = datetime.strptime(last_contact_date, '%Y-%m-%d').date()
        return (date.today() - last_date).days
    except (ValueError, TypeError):
        return float('inf')


def get_health_status(health_score: int) -> Tuple[str, str]:
    """Get health status emoji and label from score."""
    if health_score >= HEALTH_THRESHOLDS['healthy']:
        return '🟢', 'Healthy'
    elif health_score >= HEALTH_THRESHOLDS['warming']:
        return '🟡', 'Warming'
    elif health_score >= HEALTH_THRESHOLDS['stale']:
        return '🟠', 'Stale'
    else:
        return '🔴', 'Cold'


def get_days_status(days: int) -> Tuple[str, str]:
    """Get status from days since contact."""
    if days <= DAYS_THRESHOLDS['healthy']:
        return '🟢', 'Healthy'
    elif days <= DAYS_THRESHOLDS['warming']:
        return '🟡', 'Warming'
    elif days <= DAYS_THRESHOLDS['stale']:
        return '🟠', 'Stale'
    else:
        return '🔴', 'Cold'


def calculate_base_score(days: int, priority: str = 'medium') -> int:
    """
    Calculate base health score from days since last contact.
    Score decays over time, with priority affecting decay rate.
    """
    if days == float('inf'):
        return 20  # Never contacted
    
    # Exponential decay: score = 100 * e^(-decay * days)
    decay_rate = MODIFIERS[f'{priority}_priority_decay']
    
    # Adjust decay based on priority
    if priority == 'high':
        # VIP: slower decay, starts at 100
        base = 100 * (0.995 ** (days * decay_rate))
    elif priority == 'medium':
        # Normal: standard decay
        base = 100 * (0.99 ** (days * decay_rate))
    else:
        # Low: faster decay
        base = 100 * (0.985 ** (days * decay_rate))
    
    # Floor at 0, cap at 100
    return max(0, min(100, int(base)))


def calculate_sentiment_score(contact_id: int, db_path: Optional[Path] = None) -> int:
    """
    Calculate sentiment bonus from recent interactions.
    Looks at last 10 interactions.
    """
    interactions = get_interactions(contact_id, db_path)
    
    if not interactions:
        return 0
    
    # Take last 10 interactions
    recent = interactions[:10]
    
    score = 0
    for interaction in recent:
        sentiment = interaction.get('sentiment', 'neutral')
        if sentiment == 'positive':
            score += MODIFIERS['positive_sentiment']
        elif sentiment == 'negative':
            score += MODIFIERS['negative_sentiment']
    
    # Average and normalize to 0-10 range
    avg_score = score / len(recent)
    return max(-10, min(10, int(avg_score)))


def calculate_reciprocity_score(contact_id: int, db_path: Optional[Path] = None) -> int:
    """
    Calculate reciprocity bonus.
    If they initiate contact (outgoing emails to us), boost score.
    This is a simplified version - would need email direction data.
    """
    interactions = get_interactions(contact_id, db_path)
    
    if not interactions:
        return 0
    
    # For now, assume LinkedIn interactions are often reciprocal
    # and meetings indicate mutual interest
    reciprocal_types = ['meeting', 'linkedin']
    reciprocal_count = sum(1 for i in interactions if i.get('type') in reciprocal_types)
    
    if reciprocal_count > 0:
        return MODIFIERS['reciprocity_boost']
    
    return 0


def calculate_frequency_score(contact_id: int, db_path: Optional[Path] = None) -> int:
    """
    Calculate frequency bonus for regular contact.
    Bonus for multiple interactions per month.
    """
    interactions = get_interactions(contact_id, db_path)
    
    if not interactions:
        return 0
    
    # Count interactions in last 90 days
    ninety_days_ago = date.today() - timedelta(days=90)
    recent_count = 0
    
    for interaction in interactions:
        try:
            int_date = datetime.strptime(interaction['date'], '%Y-%m-%d').date()
            if int_date >= ninety_days_ago:
                recent_count += 1
        except (ValueError, TypeError):
            continue
    
    # Bonus for 3+ interactions in 90 days (1+ per month)
    if recent_count >= 3:
        return MODIFIERS['frequency_bonus']
    
    return 0


def calculate_health_score(
    contact_id: int,
    db_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Calculate comprehensive health score for a contact.
    
    Returns:
        Dict with score, breakdown, status, and recommendations.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.name, c.email, c.company, 
                   r.health_score, r.last_contact_date, r.strength, r.priority
            FROM contacts c
            JOIN relationships r ON c.id = r.contact_id
            WHERE c.id = ?
        """, (contact_id,))
        row = cursor.fetchone()
        
        if not row:
            return {'error': 'Contact not found'}
        
        contact = dict(row)
    
    days = days_since_contact(contact['last_contact_date'])
    priority = contact['priority'] or 'medium'
    
    # Calculate components
    base_score = calculate_base_score(days, priority)
    sentiment_score = calculate_sentiment_score(contact_id, db_path)
    reciprocity_score = calculate_reciprocity_score(contact_id, db_path)
    frequency_score = calculate_frequency_score(contact_id, db_path)
    
    # Combine scores
    total_score = base_score + sentiment_score + reciprocity_score + frequency_score
    total_score = max(0, min(100, total_score))
    
    # Determine status
    status_emoji, status_label = get_health_status(total_score)
    days_emoji, days_label = get_days_status(days)
    
    # Update strength based on score
    if total_score >= 70:
        strength = 'strong'
    elif total_score >= 40:
        strength = 'medium'
    else:
        strength = 'weak'
    
    # Generate recommendations
    recommendations = []
    if days > 180:
        recommendations.append("🔴 Critical: No contact in 6+ months. Reach out soon!")
    elif days > 90:
        recommendations.append("🟠 Stale: Consider sending a check-in message.")
    elif days > 30:
        recommendations.append("🟡 Warming: Good time to reconnect.")
    
    if contact.get('follow_up_needed'):
        recommendations.append("⚠️ Follow-up pending from last interaction.")
    
    return {
        'contact_id': contact_id,
        'name': contact['name'],
        'email': contact['email'],
        'company': contact.get('company'),
        'health_score': total_score,
        'previous_score': contact['health_score'],
        'score_change': total_score - (contact['health_score'] or 0),
        'days_since_contact': days if days != float('inf') else None,
        'last_contact_date': contact['last_contact_date'],
        'priority': priority,
        'strength': strength,
        'status_emoji': status_emoji,
        'status_label': status_label,
        'breakdown': {
            'base_score': base_score,
            'sentiment_score': sentiment_score,
            'reciprocity_score': reciprocity_score,
            'frequency_score': frequency_score,
        },
        'recommendations': recommendations,
    }


def update_all_health_scores(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Recalculate health scores for all contacts.
    Updates database and returns results.
    """
    relationships = get_all_relationships(db_path)
    results = []
    
    for rel in relationships:
        contact_id = rel['id']
        result = calculate_health_score(contact_id, db_path)
        
        if 'error' not in result:
            # Update relationship in database
            update_relationship(
                contact_id,
                health_score=result['health_score'],
                strength=result['strength']
            )
            results.append(result)
    
    return results


def get_stale_contacts(
    days_threshold: int = 90,
    db_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Get contacts that haven't been contacted in specified days.
    Sorted by days since contact (oldest first).
    """
    relationships = get_all_relationships(db_path)
    stale = []
    
    for rel in relationships:
        days = days_since_contact(rel['last_contact_date'])
        if days != float('inf') and days >= days_threshold:
            result = calculate_health_score(rel['id'], db_path)
            if 'error' not in result:
                stale.append(result)
    
    # Sort by days descending (oldest first)
    stale.sort(key=lambda x: x['days_since_contact'] or 0, reverse=True)
    return stale


def get_health_dashboard(db_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Generate relationship health dashboard.
    Returns summary statistics and categorized contacts.
    """
    relationships = get_all_relationships(db_path)
    
    dashboard = {
        'total_contacts': len(relationships),
        'healthy': [],
        'warming': [],
        'stale': [],
        'cold': [],
        'summary': {
            'healthy_count': 0,
            'warming_count': 0,
            'stale_count': 0,
            'cold_count': 0,
            'average_score': 0,
            'needs_outreach': 0,
        }
    }
    
    total_score = 0
    
    for rel in relationships:
        result = calculate_health_score(rel['id'], db_path)
        
        if 'error' not in result:
            total_score += result['health_score']
            
            if result['health_score'] >= HEALTH_THRESHOLDS['healthy']:
                dashboard['healthy'].append(result)
                dashboard['summary']['healthy_count'] += 1
            elif result['health_score'] >= HEALTH_THRESHOLDS['warming']:
                dashboard['warming'].append(result)
                dashboard['summary']['warming_count'] += 1
            elif result['health_score'] >= HEALTH_THRESHOLDS['stale']:
                dashboard['stale'].append(result)
                dashboard['summary']['stale_count'] += 1
            else:
                dashboard['cold'].append(result)
                dashboard['summary']['cold_count'] += 1
            
            if result['days_since_contact'] and result['days_since_contact'] > 90:
                dashboard['summary']['needs_outreach'] += 1
    
    dashboard['summary']['average_score'] = (
        int(total_score / len(relationships)) if relationships else 0
    )
    
    return dashboard


def print_health_report(result: Dict[str, Any]) -> None:
    """Print formatted health report for a contact."""
    print(f"\n{result['status_emoji']} {result['name']}")
    print(f"   Email: {result['email']}")
    if result.get('company'):
        print(f"   Company: {result['company']}")
    print(f"   Health Score: {result['health_score']}/100 ({result['status_label']})")
    
    if result['days_since_contact']:
        print(f"   Days Since Contact: {result['days_since_contact']}")
    if result.get('last_contact_date'):
        print(f"   Last Contact: {result['last_contact_date']}")
    
    print(f"   Priority: {result['priority'].title()} | Strength: {result['strength'].title()}")
    
    if result['recommendations']:
        print("   Recommendations:")
        for rec in result['recommendations']:
            print(f"     - {rec}")


if __name__ == "__main__":
    from database import init_db
    
    init_db()
    
    print("Relationship Health Scorer Test")
    print("=" * 50)
    
    # Get dashboard
    dashboard = get_health_dashboard()
    
    print(f"\n📊 Health Dashboard")
    print(f"   Total Contacts: {dashboard['total_contacts']}")
    print(f"   Average Score: {dashboard['summary']['average_score']}/100")
    print(f"\n   🟢 Healthy: {dashboard['summary']['healthy_count']}")
    print(f"   🟡 Warming: {dashboard['summary']['warming_count']}")
    print(f"   🟠 Stale: {dashboard['summary']['stale_count']}")
    print(f"   🔴 Cold: {dashboard['summary']['cold_count']}")
    print(f"   ⚠️  Needs Outreach: {dashboard['summary']['needs_outreach']}")
