# Personal CRM for Career OS

A relationship management backend for tracking professional contacts, interactions, and relationship health.

## Features

- **Contact Management**: Store contacts with company, title, LinkedIn, and notes
- **Interaction Tracking**: Log emails, meetings, calls, and LinkedIn interactions
- **Relationship Health Scoring**: Automatic health scores based on contact frequency, sentiment, and reciprocity
- **Vector Search**: Semantic search to find contacts ("who do I know at NVIDIA?")
- **Contact Discovery**: Import from Gmail and Google Calendar exports
- **Reminders**: Set follow-up reminders for important contacts
- **Health Dashboard**: Visual overview of relationship health status

## Installation

### Requirements

- Python 3.9+
- SQLite3 (built-in)
- sentence-transformers (optional, for semantic search)

### Setup

```bash
cd career-os/crm

# Install dependencies
pip install sentence-transformers  # Optional but recommended
pip install icalendar              # Optional, for ICS calendar parsing

# Initialize database (happens automatically on first run)
python3 database.py
```

## Usage

### CLI Commands

```bash
# Show help
python3 cli.py --help

# Search contacts (semantic search)
python3 cli.py search "who do I know at NVIDIA?"
python3 cli.py search "machine learning engineers"
python3 cli.py search "people in Beijing"

# Show stale relationships (need outreach)
python3 cli.py stale
python3 cli.py stale --months 3

# Add a new contact
python3 cli.py add "John Doe, john@nvidia.com, VP Engineering, met at AWS Summit"

# Create reminders
python3 cli.py remind "Follow up with Sarah about job opportunity" --date 2026-06-15
python3 cli.py remind "Send article to Bob" --contact bob@company.com
python3 cli.py remind --list
python3 cli.py remind --done 1

# Health dashboard
python3 cli.py health
python3 cli.py health --contact john@nvidia.com

# Import contacts from exports
python3 cli.py import --gmail ~/Downloads/gmail-export.json
python3 cli.py import --calendar ~/Downloads/calendar-export.ics
python3 cli.py import --gmail ~/Downloads/gmail-export.json --dry-run

# Recalculate health scores
python3 cli.py score
python3 cli.py score --show-changes

# List all contacts
python3 cli.py list

# Log an interaction
python3 cli.py interact john@nvidia.com --type meeting --summary "Discussed AI roadmap" --sentiment positive
python3 cli.py interact john@nvidia.com --type call --follow-up --follow-up-date 2026-06-20
```

### Programmatic Usage

```python
from database import init_db, create_contact, create_interaction
from vector_search import VectorSearch
from scorer import get_health_dashboard

# Initialize
init_db()

# Add contact
contact_id = create_contact(
    name="Jane Smith",
    email="jane@openai.com",
    company="OpenAI",
    title="Research Scientist",
    how_we_met="Met at NeurIPS 2025"
)

# Log interaction
create_interaction(
    contact_id=contact_id,
    interaction_type="email",
    date_str="2026-06-07",
    summary="Discussed collaboration opportunities",
    sentiment="positive",
    follow_up_needed=True,
    follow_up_date="2026-06-14"
)

# Search
searcher = VectorSearch()
results = searcher.search("who works on LLMs?")
for contact, score in results:
    print(f"{contact['name']} at {contact.get('company')} - {score:.3f}")

# Health dashboard
dashboard = get_health_dashboard()
print(f"Average health score: {dashboard['summary']['average_score']}/100")
```

## Database Schema

### contacts
- `id`: Primary key
- `name`: Full name
- `email`: Unique email address
- `phone`: Phone number
- `company`: Company name
- `title`: Job title
- `linkedin_url`: LinkedIn profile URL
- `location`: Geographic location
- `how_we_met`: Context of first meeting
- `notes`: Additional notes
- `created_at`, `updated_at`: Timestamps

### interactions
- `id`: Primary key
- `contact_id`: Foreign key to contacts
- `type`: email/meeting/call/linkedin/other
- `date`: Interaction date
- `summary`: What happened
- `sentiment`: positive/neutral/negative
- `follow_up_needed`: Boolean
- `follow_up_date`: When to follow up

### relationships
- `id`: Primary key
- `contact_id`: Foreign key (unique)
- `health_score`: 0-100 score
- `last_contact_date`: Last interaction date
- `strength`: weak/medium/strong
- `priority`: low/medium/high

### reminders
- `id`: Primary key
- `contact_id`: Foreign key (nullable)
- `task`: Reminder text
- `due_date`: When due
- `status`: pending/done/snoozed
- `snooze_until`: Snooze date
- `created_at`: Timestamp

## Health Score Calculation

Health scores (0-100) are calculated based on:

1. **Days Since Contact** (base score)
   - <30 days: 🟢 Healthy (70-100)
   - 30-90 days: 🟡 Warming (50-69)
   - 90-180 days: 🟠 Stale (30-49)
   - >180 days: 🔴 Cold (0-29)

2. **Sentiment Bonus** (±10 points)
   - Positive interactions boost score
   - Negative interactions reduce score

3. **Reciprocity Bonus** (+15 points)
   - Mutual interactions (meetings, LinkedIn) indicate two-way relationship

4. **Frequency Bonus** (+5 points)
   - 3+ interactions in 90 days

5. **Priority Modifier**
   - High priority contacts decay slower
   - Low priority contacts decay faster

## Gmail/Calendar Import

### Export Gmail Data

1. Go to [Google Takeout](https://takeout.google.com/)
2. Select "Mail"
3. Choose export format (JSON recommended)
4. Download and extract

### Export Calendar Data

1. Go to [Google Calendar](https://calendar.google.com/)
2. Settings → Export calendar
3. Download ICS file

### Import

```bash
python3 cli.py import --gmail ~/Downloads/takeout/mail.json --calendar ~/Downloads/calendar.ics
```

The importer:
- Filters noise (no-reply, marketing, newsletters)
- Deduplicates contacts
- Extracts company from email domains
- Merges data from multiple sources

## Example Queries

```bash
# Find contacts at specific companies
python3 cli.py search "who do I know at NVIDIA?"
python3 cli.py search "people at OpenAI"
python3 cli.py search "contacts at Airwallex"

# Find people by role
python3 cli.py search "product managers"
python3 cli.py search "engineering leaders"
python3 cli.py search "recruiters"

# Find stale relationships
python3 cli.py stale --months 6
python3 cli.py health

# Check specific contact health
python3 cli.py health --contact john@example.com
```

## Project Structure

```
career-os/crm/
├── database.py      # SQLite schema and CRUD operations
├── vector_search.py # Semantic search with sentence-transformers
├── discovery.py     # Gmail/Calendar import and parsing
├── scorer.py        # Relationship health scoring
├── cli.py           # Command-line interface
├── crm.db           # SQLite database (created on first run)
├── embeddings.json  # Contact embeddings (created on first search)
└── README.md        # This file
```

## Integration with Career OS

This CRM is designed to integrate with the broader Career OS:

- **Job Hunter**: Cross-reference contacts with job opportunities
- **TaskFlow**: Create automated outreach workflows
- **Notion**: Sync contacts to Notion database
- **WeCom**: Log WeChat interactions automatically

## Future Enhancements

- [ ] Email integration (IMAP/SMTP for automatic logging)
- [ ] LinkedIn scraper for profile updates
- [ ] Automated outreach suggestions
- [ ] Meeting notes extraction from calendar
- [ ] Integration with email clients
- [ ] REST API for web/mobile access
- [ ] Contact enrichment (Clearbit, Hunter.io)
- [ ] Graph visualization of network

## License

MIT License - Part of Career OS
