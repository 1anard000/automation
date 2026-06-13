# Infrastructure Self-Healing Bot

Automated health monitoring and self-healing for Career OS infrastructure.

## Overview

This bot runs every 15 minutes to:
- Monitor system health across 5 key areas
- Automatically fix common issues
- Report status to Ian

## Components

### `healthcheck.py`
Runs health checks for:
- **GitHub Pages**: Dashboard HTML accessibility
- **Cron Jobs**: All 10+ jobs running without errors
- **Database**: jobs-all.json exists with 100+ jobs, updated <4h ago
- **CRM**: Database exists, API responding
- **Cover Letters**: Coverage for A-1 priority jobs

### `autofix.py`
Auto-fixes detected issues:
- **GitHub Pages**: Enable via API or create gh-pages branch
- **Cron Jobs**: Re-enable broken jobs, reset error counters
- **Database**: Trigger merge-jobs.py + build-dashboard.py
- **CRM**: Run CRM builder scripts if database missing
- **Cover Letters**: Trigger cover letter generator

### `runner.py`
Main entry point for scheduled runs:
```bash
python3 runner.py --auto-fix --report
```

Options:
- `--auto-fix`: Run auto-fixes after health checks
- `--report`: Generate and send report
- `--quiet`: Only output summary

### `reporter.py`
Generates human-readable reports:
- Health check results
- Auto-fix actions taken
- Current system stats
- Items needing manual attention

## Installation

### 1. Set up cron job

The bot is designed to run every 15 minutes via the OpenClaw cron system:

```python
{
  "name": "Infrastructure Self-Heal",
  "schedule": {"kind": "cron", "expr": "*/15 * * * *"},
  "payload": {
    "kind": "agentTurn",
    "message": "Run career-os/infra-bot/runner.py --auto-fix --report and report results"
  }
}
```

### 2. Configure environment variables

Set these in your environment or `.env` file:

```bash
export GITHUB_TOKEN="your_github_token"  # For GitHub Pages API
export WECOM_USER_ID="your_wecom_id"     # For WeCom notifications (optional)
```

### 3. Verify prerequisites

Ensure these exist:
- `${WORKSPACE}/career-os/` directory
- GitHub token with repo permissions
- Python 3.8+

## Usage

### Manual run

```bash
cd ${WORKSPACE}/career-os/infra-bot

# Health check only
python3 healthcheck.py

# Health check + auto-fix
python3 runner.py --auto-fix

# Full run with report
python3 runner.py --auto-fix --report
```

### Scheduled run

The cron job will automatically run:
```
*/15 * * * * → runner.py --auto-fix --report
```

## Output

### Console output
```
[2026-06-07 21:44:00] 🚀 Infrastructure Bot starting...
[2026-06-07 21:44:00] 🔍 Running health checks...
[2026-06-07 21:44:05] ✅ GitHub Pages: Dashboard accessible
[2026-06-07 21:44:05] ✅ Cron Jobs: 12 jobs active
[2026-06-07 21:44:05] ✅ Database: 150 jobs, updated 2.3h ago
[2026-06-07 21:44:05] ✅ CRM: Database exists
[2026-06-07 21:44:05] ✅ Cover Letters: 45 files, gap: 5
[2026-06-07 21:44:05] 📊 Summary: 5/5 healthy, 0 warnings, 0 errors
[2026-06-07 21:44:05] 🔧 Running auto-fixes...
[2026-06-07 21:44:05] ℹ️ No auto-fixes needed
============================================================
✅ All systems healthy (5/5)
============================================================
[2026-06-07 21:44:05] ✅ Infrastructure Bot run complete
```

### Report format
```markdown
🤖 **Infrastructure Self-Healing Bot Report**

## 🔍 Health Check Results
*Checked 2m ago*

✅ **All systems healthy**

✅ **GitHub Pages**: Dashboard accessible
✅ **Cron Jobs**: 12 jobs active
✅ **Database**: 150 jobs, updated 2.3h ago
✅ **CRM**: Database exists
✅ **Cover Letters**: 45 files, gap: 5

## 🔧 Auto-Fix Actions
ℹ️ No auto-fixes needed

## 📊 Current System Stats
• **Jobs Database**: 150 jobs
• **CRM**: Database exists
• **Cover Letters**: 45 files
• **Cron Jobs**: 12 active

## 💡 Recommendations
✅ No manual intervention needed
```

## Files Generated

- `health_results.json` - Latest health check results
- `autofix_results.json` - Latest auto-fix results
- `latest_report.md` - Most recent report
- `report_YYYYMMDD_HHMMSS.md` - Historical reports

## Safety Features

- **Idempotent**: Safe to run repeatedly
- **Timeout protection**: All operations timeout after 3 minutes
- **Non-destructive**: No destructive operations (uses `git push -f` only for gh-pages)
- **Clear reporting**: Distinguishes auto-fixed vs manual intervention needed
- **Rollback safe**: GitHub Pages changes can be reverted via GitHub UI

## Troubleshooting

### GitHub Pages not updating
1. Check GITHUB_TOKEN is valid
2. Verify repo permissions (needs `repo` scope)
3. Check GitHub API rate limits

### Cron jobs not running
1. Verify OpenClaw cron system is active
2. Check cron job list: `openclaw cron list`
3. Re-create if missing

### Database stale
1. Manually run: `python3 merge-jobs.py`
2. Check job sources are accessible
3. Verify network connectivity

### Reports not sending
1. Check WECOM_USER_ID is set
2. Verify WeCom plugin is configured
3. Reports are saved locally regardless

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Cron (every 15 min)                │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│              runner.py                          │
│  ┌─────────────┐  ┌─────────────┐              │
│  │ healthcheck │→ │   autofix   │ (if enabled) │
│  │     .py     │  │     .py     │              │
│  └─────────────┘  └─────────────┘              │
│         │                │                      │
│         └────────┬───────┘                      │
│                  ▼                              │
│         ┌─────────────┐                         │
│         │  reporter   │ (if enabled)            │
│         │     .py     │                         │
│         └─────────────┘                         │
└─────────────────────────────────────────────────┘
```

## Extending

### Add new health check

1. Add function in `healthcheck.py`:
```python
def check_your_service() -> dict:
    result = {
        "name": "Your Service",
        "status": "healthy",
        "details": "",
        "auto_fixable": False
    }
    # ... implement check ...
    return result
```

2. Add to `run_health_checks()`:
```python
checks = [
    check_github_pages(),
    check_cron_jobs(),
    check_database(),
    check_crm(),
    check_cover_letters(),
    check_your_service(),  # Add here
]
```

### Add new auto-fix

1. Add function in `autofix.py`:
```python
def fix_your_service() -> dict:
    result = {
        "action": "fix_your_service",
        "success": False,
        "details": ""
    }
    # ... implement fix ...
    return result
```

2. Add to `run_auto_fixes()`:
```python
if check_name == "your_service":
    result = fix_your_service()
```

## License

Part of Career OS - Internal use only
