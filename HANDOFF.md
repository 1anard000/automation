# HANDOFF.md — Career OS Full Transfer Brief

> **Purpose:** Bring a new agent completely up to speed on the Career OS system.  
> **Date:** 2026-06-14  
> **Saved at:** `[WORKSPACE]/HANDOFF.md`  
> **Read by:** The接管 agent should read this file as its first action.

---

## 1. What This System Is

An automated **Career OS** — job search, career management, and professional development system for a senior PM/strategy professional targeting APAC roles. It runs mostly on cron autopilot with 7 scheduled jobs scanning the web, building dashboards, and maintaining a private application pipeline.

---

## 2. Current State Snapshot

| Metric | Value |
|--------|-------|
| Jobs in database | 228 (in `jobs-all.json`) |
| Cron jobs | 7 (all healthy, 0 errors) |
| GitHub repo | https://github.com/[GITHUB_USER]/automation (PUBLIC) |
| Google OAuth | Configured (Drive + Gmail read-only) |
| Model | `xiaomi-token-plan/mimo-v2.5` (Xiaomi MiMo v2.5 Pro) |
| Git commits | 9+ (latest: dashboard rebuild with 228 count) |

---

## 3. Complete Directory Map

Everything lives under `[WORKSPACE]/`. Below is every important directory and file.

### 3.1 Root-Level Files

| File | Purpose | Committed? |
|------|---------|------------|
| `AGENTS.md` | Agent behavior rules, memory conventions, heartbeat config | ✅ Yes |
| `SOUL.md` | Agent personality/tone | ✅ Yes |
| `IDENTITY.md` | Agent identity (name: Career, emoji: 🚀) | ✅ Yes |
| `TOOLS.md` | Local tool notes (cameras, SSH, TTS) | ✅ Yes |
| `USER.md` | About the human (mostly empty) | ❌ Gitignored |
| `HEARTBEAT.md` | Heartbeat tasks (currently empty/comments only) | ✅ Yes |
| `ARCHITECTURE.md` | Public vs private vs Google split rationale | ✅ Yes |
| `README.md` | Repo overview | ✅ Yes |
| `HANDOFF.md` | **This file** — transfer brief | ✅ Yes |
| `jobs-all.json` | Root-level copy of job database | ✅ Yes |
| `job-database.html` | Legacy job dashboard (317KB) | ✅ Yes |
| `dashboard.html` | Modern dashboard (64KB) | ✅ Yes |
| `career-hub.html` | Events, companies, AI startups, VC programs | ✅ Yes |
| `index.html` | Homepage with career hub + Google search links | ✅ Yes |
| `pipeline-dashboard.html` | Application pipeline view | ✅ Yes |
| `generate-job-pages.py` | Generates individual HTML pages per job | ✅ Yes |
| `form-mappings.json` | Form field mappings for auto-fill | ✅ Yes |
| `robots.txt` | Robots file for GitHub Pages | ✅ Yes |
| `multi-site-strategy.md` | Multi-platform search strategy doc | ✅ Yes |
| `search-strategy.md` | Search strategy notes | ✅ Yes |
| `.gitignore` | Comprehensive ignore rules (1157 bytes) | N/A |

### 3.2 `OKComputer_职位搜索清单/` — Job Database (PUBLIC)

This is the core data directory. Committed to GitHub.

| File | Purpose | Size |
|------|---------|------|
| `jobs-all.json` | **Master job database** — 228 jobs, all platforms merged | 91KB |
| `scan-latest.json` | Most recent scan results (before merge) | 14KB |
| `index.html` | Full job dashboard (GitHub Pages) | 378KB |
| `job-database-senior.html` | Senior-only roles dashboard | 91KB |
| `build-dashboard.py` | Generates HTML dashboards from JSON | 11KB |
| `merge-jobs.py` | Deduplicates + merges scan results into jobs-all.json | 2.5KB |
| `dedup-jobs.py` | Standalone deduplication logic | 2KB |
| `stats.py` | Quick stats printer (job counts, grades, cities) | 2KB |
| `cleanup.py` | Data cleanup utilities | 4.4KB |
| `builder-log.json` | System improvement scores and history | 4.2KB |
| `applications-tracker.json` | Application tracking data | 27KB ❌ Gitignored |
| `fill-rate-tracker.json` | Form fill rate tracking | 40KB ❌ Gitignored |
| `cover-letters/` | Generated cover letter HTML pages | ❌ Gitignored |
| `screenshots/` | Browser screenshots | ❌ Gitignored |

### 3.3 `career-os/` — Infrastructure Code (PUBLIC)

| Directory | Contents |
|-----------|----------|
| `career-os/crm/` | CRM system — `database.py`, `cli.py`, `discovery.py`, `scorer.py`, `vector_search.py`, `seed_data.py`, `embeddings.json` |
| `career-os/crm-web/` | Web UI for CRM — `index.html`, `contact.html`, `search.html`, `sample-data.sql` |
| `career-os/infra-bot/` | System health checker — `healthcheck.py`, `autofix.py`, `reporter.py`, `runner.py`, `health_results.json` |
| `career-os/integrations/` | Import tools — `linkedin_importer.py`, `gmail_importer.py`, `calendar_importer.py`, `import_all.py` |
| `career-os/scrapers/` | Job scrapers — `greenhouse.py`, `wellfound.py`, `builtin.py`, `liepin.py`, `company_careers.py`, `websearch.py`, `scan-all.py` + result JSONs |
| `career-os/OKComputer_职位搜索清单/` | Nested copy (possibly legacy) |

### 3.4 `skills/job-hunter/` — The Job Hunter Skill

| File | Purpose |
|------|---------|
| `SKILL.md` | Full skill definition — search strategy, grading rules, platform targets, candidate profile, privacy rules |
| `templates/job-database-template.html` | HTML template for job pages |

**Key rules in the skill:**
- Candidate has 9 years experience
- Salary floor: ≥90k RMB/mo (CN), ≥60k HKD (HK), ≥10k SGD (SG)
- Senior+ titles ONLY (reject associate/analyst/graduate)
- Target cities: Shenzhen > Hong Kong > Guangzhou > Shanghai > Singapore
- Platforms: LinkedIn, Liepin, Ashby, Greenhouse, Glassdoor

### 3.5 `private/` — Personal Data (GITIGNORED)

**⚠️ NEVER commit this directory. Contains personal info, credentials, and strategy notes.**

| File/Dir | Purpose |
|----------|---------|
| `.env` | Environment vars (`GOOGLE_SHEET_ID=[SHEET_ID]`) |
| `GOOGLE-MCP-SETUP.md` | Google OAuth setup documentation |
| `README.md` | Private folder overview |
| `REFERENCE.md` | Quick reference for private tools |
| `cover-letters/` | 7 cover letter text files (Gate AI, Hang Seng, Lalamove, Notion, Polymer, WeLab x2) |
| `applications/` | `applications-tracker.json` + `top-jobs/` directory |
| `strategy/` | `career-strategy.md` — personal strategy notes |
| `create-cover-doc.py` | Creates Google Doc cover letters via Drive API |
| `create-top-jobs.py` | Creates curated top-jobs list |
| `push-to-sheets.py` | Pushes data to Google Sheets |
| `scan-gmail-status.py` | Gmail inbox scanner (read-only) |
| `sync-sheets.py` | Python Sheets sync script |
| `sync-sheets.sh` | Shell wrapper for Sheets sync |

### 3.6 `~/.openclaw/google-credentials/` — OAuth Credentials

| File | Purpose |
|------|---------|
| `credentials.json` | Google OAuth client credentials (Desktop type) |
| `token.json` | OAuth token with refresh token |

**Scopes:** Google Drive (read/write) + Gmail (read-only)  
**Gmail:** Configured (read-only)  
**Sheets ID:** `[SHEET_ID]`

### 3.7 `memory/` — Agent Memory (GITIGNORED)

| File | Contents |
|------|----------|
| `2026-06-09-0011.md` | Early session notes |
| `2026-06-13.md` | **Major session log** — privacy scrub, cron rebuild, Google MCP setup, all decisions documented |
| `2026-06-14.md` | Today's log (empty so far) |

### 3.8 Other Directories

| Directory | Purpose | Committed? |
|-----------|---------|------------|
| `jobs/` | 19 individual job HTML pages | ✅ Yes |
| `crm/` | CRM HTML page + database | ❌ Gitignored |
| `interview-prep/` | Interview prep materials | ❌ Gitignored |
| `templates/` | `job-page-template.html` | ✅ Yes |
| `.openclaw/` | OpenClaw workspace state | ❌ Gitignored |

---

## 4. GitHub Repository

- **URL:** https://github.com/[GITHUB_USER]/automation
- **Visibility:** PUBLIC
- **Remote:** `origin` → `https://github.com/[GITHUB_USER]/automation.git`
- **Branch:** `main` (assumed)

### Recent Commits (newest first)
```
df42291 Nightly fix: rebuild dashboard with correct 228 count, update scores
55c8a0a Nightly dedup: remove 4 duplicate jobs (207→203), rebuild dashboard
521c1ee Scan 2026-06-14 02:00: 37 new jobs (10 dupes skipped, 1 filtered out). Total: 207
023b6d5 Career Hub v2: 91 real links, 8 AI startups, chamber events, VC programs, salary data
e98b8f0 Career Hub v1: actionable networking, events, AI ecosystem, VC roles
5e90faf Dashboard: site-specific backup search + fit badges + Gmail scanner
bb86d98 Homepage v2: career hub, Google search links, timestamp tracker
372f37f Clean reset: Career OS — job dashboard, pipeline scripts, career strategy
```

### What Was Pushed
- All job data, dashboards, Python scripts, career hub HTML
- `career-os/` infrastructure code (CRM, scrapers, integrations, infra-bot)
- `skills/job-hunter/` skill definition
- Architecture docs, README, templates

### What Was NOT Pushed (gitignored)
- `private/` — cover letters, applications, strategy, credentials
- `memory/` — agent memory files
- `USER.md` — human's personal info
- Screenshots, `.env`, `*.secret`, `__pycache__`
- Application tracker data, cover letter HTML
- CRM database (`crm.db`, `embeddings.json`)

---

## 5. Cron Jobs (7 Total)

All use `xiaomi-token-plan/mimo-v2.5` model, run in isolated sessions, delivery mode: none.

### 5.1 🔍 Job Scanner — APAC Senior Roles
- **ID:** `0e2ecc34-aeb4-489a-bf3d-8678b37d9b57`
- **Schedule:** Daily 2am CST (`0 2 * * *`)
- **What:** Runs 12-16 web searches (LinkedIn, Greenhouse, Ashby, Liepin, AI startups, VC), filters for senior+ roles, grades A-1/A-2/B, merges to jobs-all.json, builds dashboard, git commits + pushes
- **Last run:** Jun 13 11pm — ok (194s)
- **Next run:** Jun 15 2am

### 5.2 🏗️ System Builder — Continuous Improvement
- **ID:** `e92f6c84-1b2a-425a-beed-9c3913bbdeec`
- **Schedule:** Daily 3am CST (`0 3 * * *`)
- **What:** Scores system on 7 dimensions (data quality, dashboard, strategy, scripts, CRM, automation, coverage), picks lowest, spawns sub-agent to improve it
- **Last run:** Jun 13 midnight — ok (93s)
- **Next run:** Jun 15 3am

### 5.3 🔧 Nightly Improver
- **ID:** `a1a63e6a-34af-4861-8607-dc4a255f72e1`
- **Schedule:** Daily at 0am, 3am, 6am CST (`0 0,3,6 * * *`)
- **What:** Off-peak improvement runs — one concrete fix per run (job scan, dashboard improvement, data cleanup, career hub update)
- **Last run:** Jun 14 3am — ok (67s)
- **Next run:** Jun 14 6pm (0am tonight)

### 5.4 📋 Daily Brief
- **ID:** `029c419f-d824-4a11-a385-f9b54dc66141`
- **Schedule:** Daily 6:30am CST (`30 6 * * *`)
- **What:** Morning summary — reads jobs DB, checks Gmail for recruiter emails, generates brief (top picks, follow-ups, market signals)
- **Last run:** Jun 14 6:30am — ok (23s)
- **Next run:** Jun 15 6:30am

### 5.5 📊 Career Strategist — Weekly Intel
- **ID:** `c7637994-713d-4fa7-9c4d-a8f5bc9827b5`
- **Schedule:** Monday 4am CST (`0 4 * * 1`)
- **What:** Market analysis, company targeting, salary benchmarks, skills gap analysis, weekly strategy report
- **Last run:** Not yet (next: Jun 16 Monday 4am)
- **Status:** Newly created, hasn't run yet

### 5.6 🧭 Career Hub Refresh
- **ID:** `ac3aaa2a-e512-4ec9-b8d9-76ad69bccc46`
- **Schedule:** Monday 3:30am CST (`30 3 * * 1`)
- **What:** Research events, new postings at target companies, update career-hub.html
- **Last run:** Not yet (next: Jun 16 Monday 3:30am)

### 5.7 📑 MCP Sync — Sheets + Docs + Gmail
- **ID:** `1018e9d2-eefb-4bef-9646-7bba528ed862`
- **Schedule:** Wednesday 4:30am CST (`30 4 * * 3`)
- **What:** Sync jobs to Google Sheets, create cover docs for new A-1/A-2 jobs (max 3/run), scan Gmail
- **Last run:** Not yet (next: Jun 18 Wednesday 4:30am)

---

## 6. Candidate Profile

| Field | Value |
|-------|-------|
| Experience | 9 years |
| Past employers | [PREVIOUS_EMPLOYER_1] (acquired by [ACQUIRER]), [PREVIOUS_EMPLOYER_2] |
| Current | Senior PM at [CURRENT_EMPLOYER], Shanghai |
| Education | [UNIVERSITY] — [DEGREE] in [MAJOR] + [SECOND_MAJOR] |
| Languages | English native, Mandarin HSK4 (intermediate) |
| Target cities | Shenzhen > Hong Kong > Guangzhou > Shanghai > Singapore |
| Target roles | Senior PM, Director, VP, Head of, GM — product, strategy, ops, cross-border expansion |
| Differentiator | US + China bridge, tech + business, program + product + strategy |
| Salary floor | ≥90k RMB/mo, ≥60k HKD, ≥10k SGD, ≥$150k USD remote |

---

## 7. Security Rules (CRITICAL — NEVER VIOLATE)

1. **Public repo = zero personal info.** No real names, emails, employer history, specific applications on any public-facing HTML.
2. **`private/` folder is gitignored.** All personal data stays here — cover letters, applications, strategy notes, credentials.
3. **Google Gmail = READ ONLY.** Never send, reply, or draft emails. Scan inbox only.
4. **Google Drive = Read/Write** for cover letters and application tracker sheets.
5. **Credentials at `~/.openclaw/google-credentials/`** — never commit, never share, never log.
6. **Never commit** OAuth tokens, API keys, `.env` files, or personal identifiers to the public repo.
7. **Cover letters** go to `private/cover-letters/` locally, or Google Docs via MCP — never public.

---

## 8. Google MCP Integration

| Item | Detail |
|------|--------|
| Credentials file | `~/.openclaw/google-credentials/credentials.json` |
| Token file | `~/.openclaw/google-credentials/token.json` |
| OAuth type | Desktop (has refresh token) |
| Scopes | `https://www.googleapis.com/auth/drive` + `https://www.googleapis.com/auth/gmail.readonly` |
| Gmail messages | Configured (read-only) |
| Sheets ID | `[SHEET_ID]` |
| Setup doc | `private/GOOGLE-MCP-SETUP.md` |

### Scripts that use Google APIs
- `private/sync-sheets.py` / `sync-sheets.sh` — Push jobs to Google Sheets
- `private/create-cover-doc.py` — Create cover letter as Google Doc
- `private/scan-gmail-status.py` — Scan Gmail inbox for recruiter emails
- `private/push-to-sheets.py` — Alternative Sheets push script

---

## 9. Data Flow

```
Job Scanner (cron 2am) 
    → web_search (LinkedIn, Liepin, Ashby, Greenhouse, AI startups)
    → scan-latest.json
    → merge-jobs.py (dedup + merge)
    → jobs-all.json (master DB)
    → build-dashboard.py
    → index.html + job-database-senior.html
    → git commit + push
    → GitHub Pages (live)

Career Hub Refresh (cron Monday)
    → web_search (events, companies, startups)
    → career-hub.html
    → git commit + push

MCP Sync (cron Wednesday)
    → jobs-all.json
    → Google Sheets (sync-sheets.py)
    → Google Docs (create-cover-doc.py, max 3 new A-1/A-2)
    → Gmail scan (read-only)

Daily Brief (cron 6:30am)
    → jobs-all.json
    → Gmail API (unread recruiter emails)
    → career-strategy.md (if exists)
    → Morning summary report
```

---

## 10. How to Continue

### First actions for the接管 agent:

1. **Read this file** (`HANDOFF.md`) — you're doing that now
2. **Read `memory/2026-06-13.md`** — the full rebuild session log with all decisions
3. **Read `skills/job-hunter/SKILL.md`** — the complete scanning strategy and grading rules
4. **Check cron status** — `cron list` to verify all 7 jobs are healthy
5. **Read the job database** — `OKComputer_职位搜索清单/jobs-all.json` (228 jobs)

### To run a manual scan:
```bash
cd [WORKSPACE]/OKComputer_职位搜索清单
python3 merge-jobs.py scan-latest.json
python3 build-dashboard.py
python3 stats.py
```

### To check system health:
```bash
cd [WORKSPACE]
cat OKComputer_职位搜索清单/builder-log.json   # system scores
git log --oneline -5                            # recent commits
python3 -c "import json; print(len(json.load(open('OKComputer_职位搜索清单/jobs-all.json'))))"  # job count
```

### To manage crons:
Use the `cron` tool — `action=list` to see all, `action=run` to trigger manually, `action=update` to change schedule.

### To fix memory index (if broken):
```bash
openclaw memory index --force
```

---

## 11. What Was Left In Progress

| Item | Status | Notes |
|------|--------|-------|
| URL enrichment | In progress | 93 jobs missing direct application links — builder spawned sub-agent |
| Pipeline scripts | Done | `merge-jobs.py`, `build-dashboard.py`, `dedup-jobs.py`, `stats.py` all created and tested |
| Google MCP | Set up, not fully tested | OAuth works, scripts exist, Sheets sync not verified end-to-end |
| Dashboard visual | Scored 7/10 | Could use modern CSS refresh |
| Career strategy | Scored 5/10 | Monday strategist cron should generate this |
| Memory index | Broken | Embedding provider mismatch — run `openclaw memory index --force` |
| Builder scores | See below | Latest from `builder-log.json` |

### Latest Builder Scores
- data_quality: 5
- dashboard: 7
- career_strategy: 5
- python_scripts: 2→building (was being improved)
- crm: 4
- automation: 7
- coverage: 5

---

## 12. What NOT to Do

- ❌ Don't lower the salary floor (90k RMB is non-negotiable)
- ❌ Don't include junior/associate/analyst/graduate roles
- ❌ Don't commit personal info to the public repo
- ❌ Don't send emails via Gmail MCP (read-only)
- ❌ Don't delete `private/` folder or its contents
- ❌ Don't change cron schedules without asking the user first
- ❌ Don't push OAuth tokens, API keys, or `.env` to git
- ❌ Don't expose real names on public GitHub Pages HTML

---

## 13. Quick Reference — All Important Paths

```
[WORKSPACE]/
├── HANDOFF.md                          ← You are here
├── AGENTS.md                           ← Agent rules
├── ARCHITECTURE.md                     ← System design
├── OKComputer_职位搜索清单/
│   ├── jobs-all.json                   ← Master job DB (228 jobs)
│   ├── scan-latest.json                ← Last scan results
│   ├── index.html                      ← Dashboard (GitHub Pages)
│   ├── job-database-senior.html        ← Senior roles view
│   ├── build-dashboard.py              ← HTML generator
│   ├── merge-jobs.py                   ← Job merger/dedup
│   ├── stats.py                        ← Quick stats
│   ├── builder-log.json                ← System scores
│   └── cover-letters/                  ← Cover letter HTML (gitignored)
├── career-os/
│   ├── crm/                            ← CRM Python code
│   ├── crm-web/                        ← CRM web UI
│   ├── infra-bot/                      ← System health checker
│   ├── integrations/                   ← LinkedIn/Gmail/Calendar importers
│   └── scrapers/                       ← Job site scrapers
├── skills/job-hunter/SKILL.md          ← Full scanning strategy
├── private/                            ← ⚠️ PERSONAL DATA (gitignored)
│   ├── .env                            ← Google Sheet ID
│   ├── cover-letters/                  ← 7 cover letter texts
│   ├── applications/                   ← Application tracker
│   ├── strategy/career-strategy.md     ← Personal strategy
│   ├── create-cover-doc.py             ← Google Doc creator
│   ├── sync-sheets.py                  ← Sheets sync
│   ├── scan-gmail-status.py            ← Gmail scanner
│   └── GOOGLE-MCP-SETUP.md            ← OAuth setup docs
├── ~/.openclaw/google-credentials/
│   ├── credentials.json                ← OAuth client credentials
│   └── token.json                      ← OAuth token + refresh
├── memory/
│   ├── 2026-06-13.md                   ← Major rebuild session log
│   └── 2026-06-14.md                   ← Today (empty)
└── .gitignore                          ← Ignore rules
```

---

*The system works. Keep it running, improve it incrementally, and respect the privacy boundaries. Good luck.*
