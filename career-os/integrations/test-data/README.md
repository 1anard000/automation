# Test Data for Integration Testing

This directory contains sample data files for testing the import pipeline without using real personal data.

## Files

- `sample.mbox` - Sample Gmail export with 5 emails
- `sample.ics` - Sample calendar export with 4 events
- `linkedin.json` - Sample LinkedIn connections with 8 contacts

## Quick Test

```bash
# Run full import test
python3 import_all.py \
  --gmail-takeout test-data/sample.mbox \
  --calendar-ics test-data/sample.ics \
  --linkedin-export test-data/linkedin.json \
  --output test-data/test.db

# Query results
sqlite3 test-data/test.db "SELECT COUNT(*) FROM contacts;"
sqlite3 test-data/test.db "SELECT COUNT(*) FROM interactions;"

# Clean up
rm test-data/test.db
```

## Expected Results

With the sample data, you should get:
- ~9 unique contacts
- ~18 interactions
- Contacts from all three sources merged by email/name
- Relationship scores calculated
- Topics extracted from emails and meetings

## Sample Data Contents

### Emails (sample.mbox)
1. John Doe - Coffee follow-up, job opportunity
2. Jane Smith - Technical interview follow-up
3. Mike Johnson - Project collaboration
4. David Brown - Recruiter outreach
5. Emily Williams - Design collaboration

### Events (sample.ics)
1. Coffee with John - Networking
2. Technical Interview - Jane Smith
3. TechConf 2024 - Conference
4. Weekly Team Sync - Group meeting

### LinkedIn (linkedin.json)
- 8 connections with varying companies and roles
- Includes engineers, managers, recruiters, designers
- Connection dates from 2022-2024
