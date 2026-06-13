# Personal CRM - Career OS

A clean, professional web dashboard for managing your professional relationships.

## Quick Start

### 1. Start the Python API Server

From the `career-os` directory:

```bash
cd ${WORKSPACE}/career-os
python3 api_server.py
```

The API server runs on `http://localhost:5000`

### 2. Open the Dashboard

Open `index.html` in your browser:

```bash
open crm-web/index.html
```

Or navigate to the file in Finder and double-click.

## Features

### Dashboard (`index.html`)
- **Relationship Health Chart** - Visual breakdown of your network health
- **Stale Relationships** - Contacts needing outreach, sorted by priority
- **Upcoming Follow-ups** - Reminders due this week
- **Quick Search** - Natural language search ("who at NVIDIA?")
- **Recent Interactions** - Last 10 logged interactions
- **Add Contact** - Quick form to add new contacts

### Contact Profile (`contact.html?id=123`)
- Full contact profile with all details
- Interaction history timeline
- Relationship health score with trend
- Editable notes field
- Quick actions: Send follow-up, Schedule reminder, Log interaction

### Search (`search.html?q=nvidia`)
- Advanced search across all contacts
- Filter by health score
- Sort by name, company, last contact, or health
- Click any result to view full profile

## Design

- **Dark mode** - Matches Career OS aesthetic
- **Responsive** - Works on mobile and desktop
- **Tailwind CSS** - Clean, professional styling via CDN
- **No build step** - Vanilla HTML/CSS/JS

## API Endpoints Required

The frontend expects these endpoints from your Python API server:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/contacts` | GET | List all contacts |
| `/api/contacts/:id` | GET | Get single contact |
| `/api/contacts/:id` | PUT | Update contact |
| `/api/contacts/:id` | DELETE | Delete contact |
| `/api/contacts` | POST | Create contact |
| `/api/contacts/stale` | GET | Get stale relationships |
| `/api/contacts/search?q=` | GET | Search contacts |
| `/api/contacts/:id/interactions` | GET | Get contact interactions |
| `/api/interactions/recent?limit=10` | GET | Recent interactions |
| `/api/interactions` | POST | Log interaction |
| `/api/reminders/upcoming` | GET | Upcoming reminders |
| `/api/reminders` | POST | Create reminder |

## Sample Data

Load sample data for testing:

```bash
sqlite3 crm.db < crm-web/sample-data.sql
```

## File Structure

```
career-os/crm-web/
├── index.html          # Main dashboard
├── contact.html        # Contact profile page
├── search.html         # Search results page
├── sample-data.sql     # Test data
└── README.md           # This file
```

## Tips

- **Search**: Try natural queries like "engineers at NVIDIA" or "product managers"
- **Health Scores**: 
  - 🟢 Excellent (80+): Strong relationships
  - 🟡 Good (60-79): Regular contact
  - 🟠 Fair (40-59): Need attention
  - 🔴 Poor (<40): At risk of going stale
- **Stale Alerts**: Contacts you haven't contacted in 30+ days appear here
- **Quick Add**: Use the "+ Add Contact" button for new connections

## Browser Support

- Chrome/Edge (recommended)
- Firefox
- Safari
- Mobile browsers (responsive design)

## Troubleshooting

**"Cannot connect to API"**
- Make sure the Python API server is running
- Check that it's on port 5000
- Verify CORS is enabled

**"No contacts showing"**
- Load sample data: `sqlite3 crm.db < sample-data.sql`
- Or add contacts through the dashboard

**Search not working**
- Type at least 2 characters to trigger search
- Check browser console for errors
