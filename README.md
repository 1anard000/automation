# Job Hunter Automation

Automated job search and career management system for a senior product/program manager targeting roles in **Shenzhen, Hong Kong, Guangzhou, Shanghai, and Singapore**.

## 🔒 Privacy

This repo is **public**. No personal info (names, emails, employers, education) is stored in tracked files. Sensitive files are gitignored.

## 📁 Structure

### Job Database
| File | Purpose |
|------|---------|
| `job-database.html` | Live HTML dashboard of all jobs |
| `jobs-all.json` | Unified job database |
| `*-jobs.json` | Per-source job files (LinkedIn, Ashby, etc.) |
| `build-dashboard.py` | Dashboard generator |
| `merge-jobs.py` | Merges source files into jobs-all.json |
| `improvement-engine.py` | Continuous improvement agent |

### Live Dashboard
**URL:** https://1ancol000.github.io/automation/job-database.html

### Automation
Runs every 15 minutes via cron — searches, merges, and deploys.

## 📊 Current Stats

- **296 jobs** tracked across 5 geographies
- **99 A-1** (top fit) roles
- **58 cover letters** generated
- Sources: LinkedIn, Ashby, Liepin, direct career pages

## 🎯 Focus Areas

1. **Fintech & Digital Banking** — HK/SG virtual banks, payments
2. **Cross-Border E-Commerce** — Marketplace, logistics, payments
3. **AI/LLM Product Management** — AI product strategy & GTM

## 🛠️ Tech

- Python 3 (job search, merging, dashboard)
- HTML/CSS/JS (dashboards)
- GitHub Pages (hosting)
- OpenClaw cron (automation)

---

*Last updated: 2026-06-08*
