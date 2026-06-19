# MEMORY.md — Long-Term Memory

> Curated system knowledge. Updated periodically during heartbeats/improver runs.
> Last updated: 2026-06-19

---

## System Overview

**Career OS** — automated job search + career management for Ian (senior PM/strategy, APAC focus).

| Metric | Value |
|--------|-------|
| Jobs in database | 554 (jobs-all.json) |
| Dashboard filter count | ~174 after quality gate (crypto/Chinese-only/bilingual excluded) |
| Cron jobs | 8 active, all healthy |
| GitHub repo | PUBLIC — https://github.com/1anard000/automation |
| Model | xiaomi-token-plan/mimo-v2.5-pro |
| Local server | Port 17888 (career applier) |
| Google OAuth | Configured — Drive + Gmail read-only |
| Disk | ~6.9GB free |

## Data Sources

- **LinkedIn**: 201 jobs (largest source)
- **Liepin**: 184 jobs
- **Company sites**: 56
- **Greenhouse**: 30
- **Boss/Zhilian**: 20
- **Indeed**: 12
- **JobsDB**: 7
- **Ashby**: 6

## Key Locations

- Shenzhen: 229 jobs
- Singapore: 166 jobs
- Hong Kong: 121 jobs
- Shanghai: 33 jobs
- Guangzhou: 5 jobs

## Architecture

### Public (GitHub)
- `dashboard.html` — main dashboard (built from rebuild-dashboard.py)
- `jobs-all.json` — master job database
- `career-hub.html` — events, companies, AI startups
- `pipeline-dashboard.html` — application pipeline view
- `index.html` — homepage

### Private (gitignored)
- `private/applications/` — application tracker, Gmail status
- `private/cover-letters/` — generated cover letters
- `private/strategy/` — personal strategy notes
- `private/career-os/` — kanban, quality scorer, stricter screener

### Dashboard Build Chain
1. Scrapers → `jobs-all.json`
2. `rebuild-dashboard.py` → generates `dashboard.html` + `rebuild-dashboard.js`
3. **NEVER edit dashboard.html directly** — always edit rebuild-dashboard.py
4. **NEVER edit rebuild-dashboard.js** unless fixing a JS bug (Python escaping issues)
5. After changes: `python3 rebuild-dashboard.py` → `node --check` → browser test → commit

## Cron Jobs

| Name | Schedule | Status |
|------|----------|--------|
| Job Scanner — APAC Senior Roles | 0 2 * * * | ✅ OK |
| Daily Brief | 30 6 * * * | ✅ OK |
| Gmail Daily Status Scan | 0 7 * * * | ✅ OK |
| Job Scraper — All Sources | 0 3 * * 1,3,5 | ✅ OK |
| Career OS Status Pulse – WeChat | 0 */2 * * * | ✅ OK |
| Career Site Browser — Find Real Jobs | 0 10 * * * | ✅ OK |
| Daily Job Picks — Top 20 | 0 8 * * * | ⚠️ Rate limited delivery sometimes |
| Career OS Improver v2 | every 60m | ✅ OK |

## Dashboard Features (as of 2026-06-19)

- **Filters**: Location (SG/HK/SHENZHEN/SHANGHAI), Category (Strategy/Growth/Fintech/etc), Source, Salary Tier, Company Size, Search
- **Sort**: Date, Salary, Quality Score
- **Theme**: Dark/Light toggle (auto-detects system preference, persisted in localStorage)
- **Keyboard shortcuts**: `/` to search, `Esc` to clear
- **Back-to-top** button on scroll
- **Staleness badges**: color-coded scan age on each card
- **Salary tiers**: High (>5k USD/mo), Mid-High (3-5k), Mid (1.5-3k), Low (<1.5k), None
- **Company size**: Big Tech, Growth, Enterprise, Startup

## Security

- `private/` directory is gitignored — never commit
- No cover letters, application trackers, or personal strategy in public repo
- Previous model leaked personal info to GitHub — repo was made private, then restructured as public with private split
- Google OAuth: Desktop type, Drive read/write + Gmail read-only

## Lessons Learned

1. **Dashboard JS escaping is fragile** — separate JS file avoids Python string issues
2. **Dedup is critical** — same jobs appear across sources; dedup by title+company
3. **Quality gate matters** — filter crypto-only, Chinese-only, bilingual-required roles
4. **Rate limiting** — WeChat delivery sometimes hits iLink rate limits; use cooldown
5. **Location normalization** — some jobs had mismatched location text vs location_norm; verify after merge
6. **Git push to both main and gh-pages** — `git push origin main:gh-pages --force`

## Improvement Round Tracker

Last completed: Round 6 (System Health — 2026-06-19)
Next: Round 1 (Data Quality — deduplicate by title+company)
