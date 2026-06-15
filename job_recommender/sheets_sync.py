#!/usr/bin/env python3
"""
Google Sheets Sync for Job Recommendations
Syncs the full job database and daily recommendations to Google Sheets.

Setup:
1. Place credentials.json in ~/.openclaw/google-credentials/
2. Or set GOOGLE_SHEETS_CREDENTIALS env var
3. First run will create the spreadsheet and ask for auth
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

try:
    import gspread
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False
    print("WARNING: gspread not installed. Run: pip3 install gspread google-auth google-auth-oauthlib")

# Config
SPREADSHEET_NAME = "Job Recommendations - Career OS"
_HOME = Path.home()
CREDENTIALS_DIR = _HOME / '.openclaw' / 'google-credentials'
TOKEN_FILE = CREDENTIALS_DIR / 'sheets_token.json'
CREDENTIALS_FILE = CREDENTIALS_DIR / 'credentials.json'
CONFIG_FILE = Path(__file__).parent / 'sheets_config.json'

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]


def load_config():
    """Load sheets config (spreadsheet ID etc)."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}


def save_config(config):
    """Save sheets config."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def get_credentials():
    """Get Google API credentials (OAuth or service account)."""
    if not HAS_GSPREAD:
        return None
    
    # Try service account first
    sa_file = os.environ.get('GOOGLE_SERVICE_ACCOUNT', str(CREDENTIALS_DIR / 'service_account.json'))
    if Path(sa_file).exists():
        creds = service_account.Credentials.from_service_account_file(
            sa_file, scopes=SCOPES
        )
        return creds
    
    # Try OAuth token
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, 'w') as f:
                f.write(creds.to_json())
        return creds
    
    # Try OAuth flow with credentials.json
    if CREDENTIALS_FILE.exists():
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
        return creds
    
    print("ERROR: No Google credentials found.")
    print(f"  Expected: {CREDENTIALS_FILE} or {TOKEN_FILE}")
    print(f"  Or set GOOGLE_SERVICE_ACCOUNT env var")
    return None


def get_or_create_spreadsheet(client, config):
    """Get existing spreadsheet or create new one."""
    spreadsheet_id = config.get('spreadsheet_id')
    
    if spreadsheet_id:
        try:
            return client.open_by_key(spreadsheet_id)
        except Exception as e:
            print(f"Could not open spreadsheet {spreadsheet_id}: {e}")
            print("Creating new spreadsheet...")
    
    try:
        spreadsheet = client.create(SPREADSHEET_NAME)
        config['spreadsheet_id'] = spreadsheet.id
        config['spreadsheet_url'] = spreadsheet.url
        save_config(config)
        print(f"Created spreadsheet: {spreadsheet.url}")
        return spreadsheet
    except Exception as e:
        print(f"ERROR creating spreadsheet: {e}")
        return None


def ensure_worksheet(spreadsheet, name, headers, rows=1000):
    """Get or create a worksheet with headers."""
    try:
        ws = spreadsheet.worksheet(name)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=name, rows=rows, cols=len(headers))
        ws.update(range_name='A1', values=[headers])
        try:
            ws.format('A1:Z1', {'textFormat': {'bold': True}})
        except:
            pass
    return ws


def sync_full_database(jobs, client):
    """Sync the full job database to 'All Jobs' sheet."""
    config = load_config()
    spreadsheet = get_or_create_spreadsheet(client, config)
    if not spreadsheet:
        return False
    
    headers = [
        'ID', 'Title', 'Company', 'Location', 'Quality Score', 'Tier',
        'YOE Score', 'Salary Score', 'Domain Score', 'Location Score',
        'English Score', 'Freshness', 'English OK', 'Excluded',
        'URL', 'Notes', 'Tags', 'Scanned Date'
    ]
    
    ws = ensure_worksheet(spreadsheet, 'All Jobs', headers)
    
    rows = []
    for job in jobs:
        bd = job.get('score_breakdown', {})
        rows.append([
            job.get('id', ''),
            job.get('title', ''),
            job.get('company_raw', ''),
            job.get('location', ''),
            job.get('quality_score', 0),
            job.get('quality_tier', 'D'),
            bd.get('yoe_match', 0),
            bd.get('salary_match', 0),
            bd.get('domain_match', 0),
            bd.get('location_match', 0),
            bd.get('english_match', 0),
            bd.get('freshness', 0),
            'Yes' if job.get('english_friendly') else 'No',
            'Yes' if job.get('excluded') else 'No',
            job.get('url', ''),
            (job.get('notes', '') or '')[:200],  # Truncate long notes
            ', '.join(job.get('tags', [])),
            job.get('scanned_date', ''),
        ])
    
    # Sort by quality score descending
    rows.sort(key=lambda r: r[4], reverse=True)
    
    # Clear and update
    ws.clear()
    ws.update(range_name='A1', values=[headers] + rows)
    
    print(f"Synced {len(rows)} jobs to 'All Jobs' sheet")
    return True


def sync_daily_recommendations(recommendations, client):
    """Sync daily recommendations to 'Daily Picks' sheet."""
    config = load_config()
    spreadsheet = get_or_create_spreadsheet(client, config)
    if not spreadsheet:
        return False
    
    today = datetime.now().strftime('%Y-%m-%d')
    headers = [
        'Rank', 'Title', 'Company', 'Location', 'Score', 'Tier',
        'YOE', 'Salary', 'Domain', 'Location Score', 'English',
        'Action Items', 'URL'
    ]
    
    ws = ensure_worksheet(spreadsheet, 'Daily Picks', headers)
    
    rows = []
    for i, job in enumerate(recommendations, 1):
        bd = job.get('score_breakdown', {})
        rows.append([
            i,
            job.get('title', ''),
            job.get('company_raw', ''),
            job.get('location', ''),
            job.get('quality_score', 0),
            job.get('quality_tier', 'B'),
            bd.get('yoe_match', 0),
            bd.get('salary_match', 0),
            bd.get('domain_match', 0),
            bd.get('location_match', 0),
            bd.get('english_match', 0),
            '',  # Action items (to be filled manually)
            job.get('url', ''),
        ])
    
    ws.clear()
    ws.update(range_name='A1', values=[headers] + rows)
    
    # Add date stamp
    ws.update(range_name=f'A{len(rows)+3}', values=[[f"Generated: {today}"]])
    
    print(f"Synced {len(rows)} daily recommendations to 'Daily Picks' sheet")
    return True


def sync_summary_stats(jobs, client):
    """Sync summary statistics to 'Dashboard' sheet."""
    config = load_config()
    spreadsheet = get_or_create_spreadsheet(client, config)
    if not spreadsheet:
        return False
    
    headers = ['Metric', 'Value']
    ws = ensure_worksheet(spreadsheet, 'Dashboard', headers)
    
    from collections import Counter
    tiers = Counter(j.get('quality_tier', 'D') for j in jobs if not j.get('excluded'))
    locs = Counter(j.get('location', '?') for j in jobs if not j.get('excluded'))
    eligible = [j for j in jobs if not j.get('excluded')]
    
    rows = [
        ['Total Jobs', len(jobs)],
        ['Excluded (Amazon)', sum(1 for j in jobs if j.get('excluded'))],
        ['Eligible Jobs', len(eligible)],
        ['', ''],
        ['Tier A (≥70)', tiers.get('A', 0)],
        ['Tier B (50-69)', tiers.get('B', 0)],
        ['Tier C (30-49)', tiers.get('C', 0)],
        ['Tier D (<30)', tiers.get('D', 0)],
        ['', ''],
        ['--- Locations ---', ''],
    ]
    for loc, count in sorted(locs.items(), key=lambda x: -x[1]):
        rows.append([loc, count])
    
    rows.append(['', ''])
    rows.append([f'Last Updated', datetime.now().strftime('%Y-%m-%d %H:%M')])
    
    ws.clear()
    ws.update(range_name='A1', values=[headers] + rows)
    
    print(f"Synced dashboard stats")
    return True


def main():
    """Sync all data to Google Sheets."""
    if not HAS_GSPREAD:
        print("Cannot sync: gspread not installed")
        sys.exit(1)
    
    creds = get_credentials()
    if not creds:
        print("Cannot sync: no credentials")
        sys.exit(1)
    
    client = gspread.authorize(creds)
    
    # Load jobs
    jobs_path = Path('/Users/iancolrick/OKComputer_职位搜索清单/jobs-all.json')
    with open(jobs_path) as f:
        jobs = json.load(f)
    
    print(f"Loaded {len(jobs)} jobs")
    
    # Sync full database
    sync_full_database(jobs, client)
    
    # Sync daily recommendations
    eligible = [j for j in jobs if not j.get('excluded') and not j.get('low_quality')]
    eligible.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
    daily_picks = eligible[:20]
    sync_daily_recommendations(daily_picks, client)
    
    # Sync summary
    sync_summary_stats(jobs, client)
    
    config = load_config()
    if config.get('spreadsheet_url'):
        print(f"\nView spreadsheet: {config['spreadsheet_url']}")


if __name__ == '__main__':
    main()
