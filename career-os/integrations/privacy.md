# Privacy & Security Documentation

## Overview

This integration is designed with privacy as a first-class concern. All data is processed locally and stored in your personal SQLite database.

## Data Collection Summary

### What We Collect

| Data Type | Source | Purpose | Retention |
|-----------|--------|---------|-----------|
| Email addresses | Gmail, Calendar, LinkedIn | Contact identification | Permanent (until deleted) |
| Names | Gmail, Calendar, LinkedIn | Contact identification | Permanent (until deleted) |
| Job titles | Gmail signatures, LinkedIn | Professional context | Permanent (until deleted) |
| Companies | Gmail signatures, LinkedIn | Professional context | Permanent (until deleted) |
| Phone numbers | Gmail signatures | Contact information | Permanent (until deleted) |
| LinkedIn URLs | Gmail signatures, LinkedIn | Professional profiles | Permanent (until deleted) |
| Connection dates | LinkedIn | Relationship timeline | Permanent (until deleted) |
| Email dates | Gmail | Interaction timeline | Permanent (until deleted) |
| Email subjects | Gmail | Interaction context | Permanent (until deleted) |
| Email snippets (first 1000 chars) | Gmail | Interaction context | Permanent (until deleted) |
| Meeting titles | Calendar | Interaction context | Permanent (until deleted) |
| Meeting descriptions | Calendar | Interaction context | Permanent (until deleted) |
| Meeting locations | Calendar | Context (in-person vs virtual) | Permanent (until deleted) |
| Sentiment analysis | Computed | Relationship health | Permanent (until deleted) |
| Topics | Computed | Conversation categorization | Permanent (until deleted) |
| Relationship scores | Computed | Prioritization | Permanent (until deleted) |

### What We DO NOT Collect

- ❌ Email body content (beyond 1000-char snippet)
- ❌ Email attachments
- ❌ Attachment contents
- ❌ Calendar attendee response status
- ❌ Passwords (except temporary OAuth tokens)
- ❌ Credit card or financial information
- ❌ Government IDs or sensitive personal data
- ❌ Medical or health information

## Data Storage

### Location
- **Database**: `career-os/crm/crm.db` (SQLite file)
- **Location**: Your local machine only
- **Backup**: Your responsibility (use Time Machine, cloud backup, etc.)

### Access Control
- Database file permissions: Standard user file permissions
- No encryption by default (add disk encryption if needed)
- No network exposure unless you manually configure it

### Data Size
Typical database sizes:
- Light user (500 contacts, 2000 interactions): ~5-10 MB
- Medium user (2000 contacts, 10000 interactions): ~20-50 MB
- Heavy user (5000+ contacts, 50000+ interactions): ~100-200 MB

## Data Processing

### Where Processing Happens
- **All processing is local** on your machine
- No data is sent to external servers during import
- No analytics or telemetry

### OAuth Tokens
- Google OAuth tokens stored in `token.json` (if using API method)
- Tokens allow read-only access to Gmail and Calendar
- Tokens can be revoked at any time from Google Account settings
- Delete `token.json` after import if not reusing

### Temporary Files
- Google Takeout files: Delete after successful import
- LinkedIn export files: Delete after successful import
- No temporary copies are retained

## Security Recommendations

### 1. Disk Encryption
Enable full disk encryption on your machine:
- **macOS**: FileVault (System Preferences → Security)
- **Windows**: BitLocker
- **Linux**: LUKS/dm-crypt

### 2. Database Encryption (Optional)
For additional security, encrypt the SQLite database:

```bash
# Using SQLCipher
sqlite3 ../crm/crm.db "PRAGMA key='your-password';"
```

### 3. Backup Security
If backing up the database:
- Use encrypted backups
- Don't sync to public cloud without encryption
- Consider password-protecting the database file

### 4. Access Control
- Keep database file in your home directory
- Don't share the file or grant access to others
- Use file permissions: `chmod 600 crm.db`

## Data Deletion

### Delete Imported Data

```bash
# Delete entire CRM database
rm ../crm/crm.db

# Or delete from within SQLite
sqlite3 ../crm/crm.db "DELETE FROM interactions;"
sqlite3 ../crm/crm.db "DELETE FROM contacts;"
```

### Delete Source Files

```bash
# After import, delete export files
rm -rf ~/Downloads/Takeout
rm -rf ~/Downloads/LinkedIn\ Data\ Export
rm token.json  # If using Google API
```

### Revoke Google Access

1. Go to https://myaccount.google.com/permissions
2. Find your app/credentials
3. Click "Remove Access"

## Compliance Considerations

### GDPR (European Union)
- You have the right to access, rectify, and delete your data
- Data is processed locally under your control
- No third-party data sharing
- To exercise rights: delete or modify the database directly

### CCPA (California)
- You control your personal information
- No sale of data to third parties
- Right to delete: remove database file

### PIPEDA (Canada)
- Personal information under your control
- Consent implied by local processing
- Access and correction rights via direct database access

## Audit Trail

### Import Logging
All imports are logged in the `import_log` table:

```sql
SELECT * FROM import_log ORDER BY import_date DESC;
```

Shows:
- When data was imported
- Which source (Gmail, Calendar, LinkedIn)
- How many records
- Any errors encountered

### Data Lineage
Each contact and interaction can be traced back to its source via the `raw_data` JSON field in interactions.

## Risk Assessment

### Low Risk
- Local processing, no network transmission
- No sensitive data categories collected
- User maintains full control
- Data easily deletable

### Medium Risk
- Database file contains personal information
- OAuth tokens provide account access (temporary)
- Potential exposure if machine is compromised

### Mitigation Strategies
1. Use disk encryption
2. Delete OAuth tokens after use
3. Regular security updates on your machine
4. Don't share database file
5. Use strong machine password

## Third-Party Dependencies

### Python Libraries
All dependencies are open-source and installed locally:
- `google-auth`, `google-api-python-client`: Google's official libraries
- `icalendar`: Open-source ICS parser
- `tqdm`: Progress bars

### No Hidden Data Collection
- Libraries process data locally
- No telemetry or analytics
- No automatic updates or phone-home

## Questions or Concerns?

If you have privacy concerns:
1. Review this document carefully
2. Run import with `--dry-run` first to see what would be collected
3. Inspect the database after import: `sqlite3 crm.db ".schema"`
4. Delete any data you're uncomfortable keeping
5. Consider using only specific importers (e.g., LinkedIn only)

## Contact

For privacy-related questions about this integration, refer to the main Career OS documentation.

---

**Last updated**: June 2024
**Version**: 1.0
