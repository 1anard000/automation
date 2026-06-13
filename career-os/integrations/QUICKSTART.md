# Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies (1 min)

```bash
cd career-os/integrations
pip3 install -r requirements.txt
```

### 2. Export Your Data (2-10 min)

**Google Takeout** (recommended):
1. Go to https://takeout.google.com/
2. Select only "Mail" and "Calendar"
3. Create export (takes 10-30 min for large accounts)
4. Download and extract

**LinkedIn Export**:
1. Go to https://www.linkedin.com/psettings/
2. "Get a copy of your data" → "Connections"
3. Download and extract

### 3. Run Import (1-5 min)

```bash
python3 import_all.py \
  --gmail-takeout ~/Downloads/Takeout/Mail/*.mbox \
  --calendar-ics ~/Downloads/Takeout/Calendar/*.ics \
  --linkedin-export ~/Downloads/LinkedIn\ Data\ Export/Connections.json \
  --output ../crm/crm.db
```

### 4. Verify (30 sec)

```bash
sqlite3 ../crm/crm.db "SELECT COUNT(*) FROM contacts;"
sqlite3 ../crm/crm.db "SELECT name, email, company, relationship_score FROM contacts ORDER BY relationship_score DESC LIMIT 10;"
```

## That's It! 🎉

Your Career OS CRM now has:
- All your contacts from Gmail, Calendar, and LinkedIn
- Complete interaction history
- Relationship scores to prioritize follow-ups
- Topic tracking for conversation context

## Next Steps

1. **Review contacts** - Check the imported data
2. **Explore the CRM** - Open `career-os/crm-web/`
3. **Set up regular imports** - Re-run monthly to keep data fresh

## Need Help?

See full documentation in `README.md` for:
- Google API setup (alternative to Takeout)
- Gmail IMAP import
- Troubleshooting
- Privacy & security details
