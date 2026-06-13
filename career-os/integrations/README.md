# Gmail + Calendar + LinkedIn Integration for Career OS CRM

This integration imports your communication history and contacts from Gmail, Google Calendar, and LinkedIn into your Career OS CRM database.

## 📁 What Gets Imported

### Gmail Importer
- **Contacts** from To/CC/BCC fields
- **Contact details** from email signatures (name, title, company, phone)
- **Interactions** - every email exchange logged with date and subject
- **Sentiment analysis** - positive/neutral/negative tone detection
- **Topic extraction** - job search, project, meeting, networking, etc.
- **Filters out** marketing emails, newsletters, auto-confirmations, spam

### Calendar Importer
- **Meeting participants** from event invites
- **Meeting categorization** - 1:1, group, interview, networking, conference
- **Interaction logging** - each meeting recorded per attendee
- **Topic extraction** - from meeting titles and descriptions

### LinkedIn Importer
- **Connections** from LinkedIn export (JSON)
- **Profile data** - name, title, company, connection date
- **LinkedIn URLs** - linked to existing contacts
- **Smart matching** - merges with existing contacts by email/name

## 🔧 Setup Instructions

### 1. Install Dependencies

```bash
cd career-os/integrations
pip3 install -r requirements.txt
```

### 2. Prepare Your Data Sources

#### Option A: Google Takeout (Recommended for privacy)

1. Go to [Google Takeout](https://takeout.google.com/)
2. Deselect all, then select only:
   - **Mail** (for Gmail)
   - **Calendar** (for Calendar)
3. Choose export format:
   - Delivery method: Download link via email
   - Frequency: Export once
   - File type: .zip
   - Size: 2GB or 10GB (depending on your data)
4. Create export and download when ready
5. Extract the ZIP file:
   - Gmail: Look for `Takeout/Mail/*.mbox` files
   - Calendar: Look for `Takeout/Calendar/*.ics` files

#### Option B: Google API (Live access)

1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Create a new project or select existing
3. Enable APIs:
   - Gmail API
   - Calendar API
4. Create OAuth 2.0 credentials:
   - Go to "Credentials" → "Create Credentials" → "OAuth client ID"
   - Application type: Desktop app
   - Download the JSON file as `credentials.json`
5. Place `credentials.json` in this directory

**Note:** First run will open a browser for OAuth authorization.

#### LinkedIn Export

1. Go to [LinkedIn Settings](https://www.linkedin.com/psettings/)
2. Under "Data privacy", click "Get a copy of your data"
3. Select "Connections" only (or full archive)
4. Request archive (takes 10-30 minutes)
5. Download and extract the ZIP
6. Find `Connections.json` in the extracted folder

### 3. Run the Import

#### Import from all sources at once:

```bash
python3 import_all.py \
  --gmail-takeout ~/Downloads/Takeout/Mail/*.mbox \
  --calendar-ics ~/Downloads/Takeout/Calendar/*.ics \
  --linkedin-export ~/Downloads/LinkedIn\ Data\ Export/Connections.json \
  --output ../crm/crm.db
```

#### Import from individual sources:

```bash
# Gmail via Takeout
python3 gmail_importer.py --db ../crm/crm.db --takeout ~/Downloads/Takeout/Mail/*.mbox

# Gmail via IMAP (requires app password)
python3 gmail_importer.py --db ../crm/crm.db --imap \
  --email your.email@gmail.com \
  --password "your-app-password" \
  --months 12

# Calendar via ICS
python3 calendar_importer.py --db ../crm/crm.db --ics ~/Downloads/Takeout/Calendar/*.ics

# Calendar via API
python3 calendar_importer.py --db ../crm/crm.db --api \
  --credentials credentials.json

# LinkedIn
python3 linkedin_importer.py --db ../crm/crm.db \
  --export ~/Downloads/LinkedIn\ Data\ Export/Connections.json
```

### 4. Verify Import

```bash
# Check database
sqlite3 ../crm/crm.db "SELECT COUNT(*) FROM contacts;"
sqlite3 ../crm/crm.db "SELECT COUNT(*) FROM interactions;"

# Sample contacts
sqlite3 ../crm/crm.db "SELECT name, email, company, relationship_score FROM contacts LIMIT 10;"

# Recent interactions
sqlite3 ../crm/crm.db "SELECT c.name, i.type, i.date, i.subject FROM interactions i JOIN contacts c ON i.contact_id = c.id ORDER BY i.date DESC LIMIT 20;"
```

## 🔒 Privacy & Security

### Data Storage
- **All data stored locally** in SQLite database (`crm.db`)
- **No external API calls** after import completes
- **No cloud sync** unless you manually set it up

### What Data Is Collected

| Source | Data Collected | Purpose |
|--------|---------------|---------|
| Gmail | Email addresses, names, signatures, dates, subjects | Contact info + interaction history |
| Calendar | Event attendees, titles, dates, locations | Meeting history + contact info |
| LinkedIn | Name, title, company, connection date, profile URL | Professional context |

### What Is NOT Collected
- Email body content (only subject lines and snippets)
- Attachment contents
- Passwords or credentials (stored temporarily in OAuth token only)
- Sensitive personal data beyond what's in signatures

### Deleting Raw Data After Import

After successful import, you can safely delete:
- Google Takeout files (`.mbox`, `.ics`)
- LinkedIn export files (`.json`)
- OAuth token files (`token.json`) if not reusing

```bash
# Example cleanup
rm -rf ~/Downloads/Takeout
rm ~/Downloads/LinkedIn\ Data\ Export/*.json
rm token.json  # Only if you won't re-import soon
```

### Gmail App Password (if using IMAP)

If you use 2FA on Gmail, you need an App Password:

1. Go to [Google Account](https://myaccount.google.com/)
2. Security → 2-Step Verification → App passwords
3. Generate password for "Mail"
4. Use this password (not your regular password) in `--gmail-password`

## 🧪 Testing with Sample Data

### Create Test Data

```bash
# Create small test export
mkdir -p test-data

# Create sample ICS file
cat > test-data/sample.ics << 'EOF'
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
DTSTART:20240101T100000Z
DTEND:20240101T110000Z
SUMMARY:Coffee with John
DESCRIPTION:Catch up on job search
ATTENDEE;CN=John Doe:mailto:john@example.com
LOCATION:Coffee Shop
END:VEVENT
END:VCALENDAR
EOF

# Create sample LinkedIn JSON
cat > test-data/linkedin.json << 'EOF'
{
  "connections": [
    {
      "firstName": "Jane",
      "lastName": "Smith",
      "emailAddress": "jane@example.com",
      "position": "Engineer",
      "companyName": "Tech Corp",
      "connectedAt": "2024-01-15"
    }
  ]
}
EOF
```

### Run Dry Run

```bash
# Preview without importing
python3 import_all.py \
  --calendar-ics test-data/sample.ics \
  --linkedin-export test-data/linkedin.json \
  --output test-data/test.db \
  --dry-run

# Import to test database
python3 import_all.py \
  --calendar-ics test-data/sample.ics \
  --linkedin-export test-data/linkedin.json \
  --output test-data/test.db

# Verify
sqlite3 test-data/test.db ".schema"
sqlite3 test-data/test.db "SELECT * FROM contacts;"
```

## 📊 Database Schema

### Contacts Table
```sql
CREATE TABLE contacts (
  id INTEGER PRIMARY KEY,
  name TEXT,
  email TEXT UNIQUE,
  title TEXT,
  company TEXT,
  phone TEXT,
  linkedin_url TEXT,
  connection_date TEXT,
  relationship_score REAL DEFAULT 0.0,
  created_at TEXT,
  updated_at TEXT
);
```

### Interactions Table
```sql
CREATE TABLE interactions (
  id INTEGER PRIMARY KEY,
  contact_id INTEGER,
  type TEXT,  -- email_received, email_sent, meeting_1:1, meeting_group, etc.
  date TEXT,
  subject TEXT,
  sentiment TEXT,  -- positive, neutral, negative
  topics TEXT,  -- JSON array
  raw_data TEXT,  -- JSON with full details
  created_at TEXT
);
```

## 🎯 Relationship Scoring

Contacts are automatically scored (-100 to 100) based on:

- **Sentiment ratio** (positive vs negative interactions)
- **Interaction frequency** (more interactions = higher score)
- **Recency** (recent contact = bonus points)

Scores help prioritize relationship maintenance:
- **80-100**: Strong relationship, maintain regularly
- **40-79**: Good relationship, check in monthly
- **0-39**: Weak relationship, consider re-engaging
- **-100 to -1**: Negative interactions, handle carefully

## 🛠️ Troubleshooting

### Gmail IMAP Errors
- Enable IMAP in Gmail settings
- Use App Password, not regular password
- Check firewall/antivirus isn't blocking IMAP

### Google API OAuth Issues
- Delete `token.json` and re-authenticate
- Ensure API is enabled in Google Cloud Console
- Check credentials.json is valid

### LinkedIn Export Format Changes
- LinkedIn occasionally changes export format
- Check `Connections.json` structure matches expected format
- Update parser if LinkedIn changes fields

### Database Lock Errors
- Close any other processes using the database
- Check for stale SQLite locks: `rm *.db-journal`

## 📝 Notes

- **First import may take 10-60 minutes** depending on data volume
- **Progress bars** show real-time status
- **Error handling** skips problematic items and continues
- **Deduplication** runs automatically after import
- **Relationship scores** calculated at end of import

## 🚀 Next Steps

After import:
1. Review imported contacts in CRM
2. Check relationship scores for priority contacts
3. Set up regular re-imports (monthly recommended)
4. Explore CRM web interface at `career-os/crm-web/`

---

**Questions or issues?** Check the main Career OS documentation or file an issue.
