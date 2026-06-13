# Changelog

## [1.0.0] - 2024-06-07

### Added

#### Gmail Importer (`gmail_importer.py`)
- IMAP import support for live Gmail access
- Google Takeout MBOX import support
- Contact extraction from email headers (To/CC/BCC)
- Signature parsing for name, title, company, phone, LinkedIn URL
- Sentiment analysis (positive/neutral/negative)
- Topic extraction (job search, project, meeting, networking, etc.)
- Noise filtering for marketing emails, newsletters, auto-confirmations
- Progress bars for large imports
- Dry-run mode for preview

#### Calendar Importer (`calendar_importer.py`)
- Google Calendar API integration with OAuth
- ICS file import support
- Meeting participant extraction
- Meeting categorization (1:1, group, interview, networking, conference)
- Topic extraction from meeting titles and descriptions
- Location tracking (in-person vs virtual)
- Progress bars for large imports
- Dry-run mode for preview

#### LinkedIn Importer (`linkedin_importer.py`)
- LinkedIn connections export parsing (JSON format)
- Contact matching by email and name
- LinkedIn URL extraction and storage
- Connection date tracking
- Smart deduplication with existing contacts
- Progress bars for large imports
- Dry-run mode for preview

#### Unified Pipeline (`import_all.py`)
- Sequential execution of all importers
- Automatic deduplication across sources
- Relationship score calculation
- Import logging for audit trail
- Comprehensive summary reporting
- Error handling with continued execution
- Time range filtering (default: 12 months)
- Record limiting for testing

#### Documentation
- `README.md` - Complete setup and usage guide
- `QUICKSTART.md` - 5-minute quick start guide
- `privacy.md` - Privacy and security documentation
- `test-data/README.md` - Testing instructions

#### Test Data
- Sample MBOX file (5 emails)
- Sample ICS file (4 events)
- Sample LinkedIn JSON (8 connections)
- Full test pipeline validation

### Database Schema

#### Contacts Table
- `id` - Primary key
- `name` - Full name
- `email` - Email address (unique)
- `title` - Job title
- `company` - Company name
- `phone` - Phone number
- `linkedin_url` - LinkedIn profile URL
- `connection_date` - LinkedIn connection date
- `relationship_score` - Calculated health score (-100 to 100)
- `created_at` - Record creation timestamp
- `updated_at` - Last update timestamp

#### Interactions Table
- `id` - Primary key
- `contact_id` - Foreign key to contacts
- `type` - Interaction type (email_received, email_sent, meeting_1:1, etc.)
- `date` - Interaction date
- `subject` - Email subject or meeting title
- `sentiment` - Sentiment analysis result
- `topics` - JSON array of extracted topics
- `raw_data` - JSON with full interaction details
- `created_at` - Record creation timestamp

#### Import Log Table
- `id` - Primary key
- `import_date` - When import occurred
- `source` - Data source (gmail, calendar, linkedin)
- `records_imported` - Count of successful imports
- `records_skipped` - Count of skipped records
- `details` - JSON with import details

### Features

#### Relationship Scoring Algorithm
- Sentiment ratio weighting (positive vs negative)
- Interaction frequency bonus
- Recency bonus (more recent = higher score)
- Score range: -100 to 100
- Automatic calculation after import

#### Deduplication
- Email-based matching (exact)
- Name-based matching (fuzzy, for contacts without email)
- Automatic merging of duplicate contacts
- Interaction history preservation

#### Privacy & Security
- Local-only processing
- No external API calls after import
- Optional OAuth token deletion
- Clear data deletion instructions
- Comprehensive privacy documentation

### Technical Details

#### Dependencies
- `google-auth` (2.23.4)
- `google-auth-oauthlib` (1.1.0)
- `google-auth-httplib2` (0.1.1)
- `google-api-python-client` (2.108.0)
- `email-validator` (2.1.0)
- `tqdm` (4.66.1)
- `python-dateutil` (2.8.2)
- `icalendar` (latest)

#### Python Compatibility
- Python 3.8+
- SQLite 3 (built-in)
- Cross-platform (macOS, Linux, Windows)

#### Performance
- Gmail: ~1000 emails/minute
- Calendar: ~500 events/minute
- LinkedIn: ~2000 connections/minute
- Typical full import: 5-30 minutes depending on data volume

### Known Limitations

1. **Gmail IMAP**: Requires app password, not regular password
2. **LinkedIn**: Export format may change; parser may need updates
3. **Sentiment Analysis**: Basic keyword-based, not ML-powered
4. **Name Matching**: Fuzzy matching could have false positives
5. **Large Imports**: May take 30+ minutes for very large accounts

### Future Enhancements (Not in v1.0.0)

- [ ] ML-powered sentiment analysis
- [ ] Automatic follow-up reminders
- [ ] Contact enrichment from public sources
- [ ] Duplicate detection improvements
- [ ] Export functionality (vCard, CSV)
- [ ] Incremental imports (only new data)
- [ ] Web interface for import management
- [ ] Scheduled automatic imports
- [ ] Email thread grouping
- [ ] Meeting attendee role detection (organizer vs attendee)

---

## Version History

- **1.0.0** (2024-06-07) - Initial release
