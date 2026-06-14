---
name: "job-hunter"
description: "Senior-level job search monitor for the candidate: parallel sub-agent scanning, ≥90k RMB floor, senior+ roles only, 100+ quality leads"
---

# Job Hunter Skill — Senior PM/Strategy Roles

## ⚠️ CRITICAL RULES (NEVER VIOLATE)

### Rule 1: Seniority Level
**The candidate has 9 years experience** at [Current Employer], [Past Employer 1], [Past Employer 2].

**✅ KEEP these titles:**
- Senior Product Manager
- Lead Product Manager
- Principal Product Manager
- Director of Product / Director, Product
- VP Product / Vice President
- Head of Product
- Senior Program Manager / Lead Program Manager
- Senior Strategy Manager / Director of Strategy
- General Manager / Country Manager
- 专家 (Expert), 资深 (Senior), 总监 (Director), 总经理 (GM)

**❌ ALWAYS REMOVE these titles:**
- Associate Product Manager / Associate, XYZ
- Assistant Product Manager / Assistant, XYZ
- Junior Product Manager
- Graduate / Campus / FY26 Graduate / 2026 Graduates
- Entry-level / Trainee / Intern
- Product Support Specialist / Support Manager
- Analyst (Business Analyst, Marketing Analyst)
- Plain "Product Manager" with NO seniority indicator (too junior)
- Product Specialist (unless 专家/Expert level)

### Rule 2: Salary Floor
- **Liepin:** ≥90k RMB/month — THIS IS THE FLOOR. NOT 70k. NOT 80k. 90k.
- **Hong Kong:** ≥60k HKD/month
- **Singapore:** ≥10k SGD/month
- **Remote US:** ≥$150k USD/year
- **NEVER lower the salary floor to get more results.**

### Rule 3: Quality Filters
**❌ ALWAYS REMOVE:**
- Pure engineering roles (SWE, backend, frontend, ML engineer)
- Hardware / manufacturing / semiconductor IC roles
- Roles requiring "fluent Mandarin" or "native Chinese"
- Entry-level / associate / assistant / graduate roles
- Support roles, analyst roles (unless Strategy Analyst)
- Old postings (>30 days)
- US location-specific only (unless remote APAC-friendly)

**✅ KEEP:**
- Senior+ PM/Program/Strategy roles
- English working language / international roles
- Fintech, cross-border, AI/LLM, digital banking, logistics tech
- HK, SG, SZ, GZ, SH, Remote (APAC-compatible)
- **AI product roles (non-technical):** AI product strategy, AI GTM, AI partnerships, AI business operations
- **Cross-border expansion roles:** China→APAC, APAC→China, Head of Expansion, Country Manager, GM
- **Business expansion:** Market entry strategy, international BD, cross-border commerce growth

**🔍 KEY SEARCH TERMS TO ALWAYS INCLUDE:**
- "business expansion" + China/APAC
- "cross-border" + product/strategy/program
- "AI product strategy" / "AI go-to-market" / "AI GTM"
- "China expansion" / "APAC expansion" / "international growth"
- "market entry" + China/Asia
- 深圳 / 上海 + 英语 / senior / director (for SZ/SH local roles)
- "head of China" / "head of APAC" / "country manager"

---

## Candidate Profile

- **9 years experience** — Senior PM at [CURRENT EMPLOYER] (Shanghai)
- **Past:** GitHub (Microsoft), Salesforce
- **Education:** [REDACTED] Econ, [REDACTED], China Studies [REDACTED]
- **Location priority:** Shenzhen > Hong Kong > Guangzhou > Shanghai > Singapore > Remote
- **Languages:** English native, Mandarin HSK4 (intermediate, NOT fluent)
- **Differentiator:** US + China bridge, tech + business, program + product + strategy
- 

---

## Architecture: Parallel Sub-Agents

### Main Agent (Orchestrator)
- Spawns sub-agents, coordinates, quality control
- Does NOT scan sites itself

### Scanning Sub-Agents (spawned in parallel)

| Sub-Agent | Platform | Target | How |
|-----------|----------|--------|-----|
| **LinkedIn Scanner** | LinkedIn | 40-50 jobs | agent-browser or web_search |
| **Liepin Scanner** | 猎聘 | 30-40 jobs | agent-browser (≥90k FLOOR) |
| **Ashby Scanner** | Ashby career pages | 15-20 jobs | web_search + web_fetch |
| **Greenhouse Scanner** | Greenhouse boards | 5-10 jobs | web_fetch company boards |
| **Glassdoor Scanner** | Glassdoor | 5-10 jobs | web_search (may be blocked) |

### OpenCode Coding Agent (port 4096)
- Use for HTML template generation
- Use for Python script writing/modification
- Use for data analysis and report generation
- Can run multiple parallel coding agents

### Post-Scan Sub-Agents (spawned after scan completes)
| Sub-Agent | Task |
|-----------|------|
| **Merger** | Deduplicate, grade, merge into jobs-all.json |
| **HTML Builder** | Generate job-database.html, individual job pages |
| **Git Pusher** | Commit and push to GitHub |
| **WeChat Notifier** | Send summary via WeCom |

---

## Platforms & Search Strategy

### LinkedIn (40-50 jobs target)
**Search URLs (15 total):**
- Product Manager + HK, SG, SZ (senior-level only)
- Program Manager + HK, SG (senior-level only)
- Strategy Manager + HK, SG, SZ
- Cross-border PM + HK, SG
- Fintech PM/Strategy + HK, SG
- Remote PM/Program + APAC

**LinkedIn search keywords to add:** Senior, Lead, Principal, Director, VP

### Liepin 猎聘 (30-40 jobs target)
**Search terms (19 total):**
- 产品经理 英语, 出海 产品经理, 海外 产品经理, 跨境 产品经理, 国际业务 产品经理
- 英语 项目经理, 英语 策略经理, 深圳 英语, 广州 英语, 香港 英语
- 程序经理 英语, 运营经理 英语, 业务经理 英语, 市场经理 英语
- 上海 英语, 新加坡 英语

**Liepin seniority keywords to add:** 资深, 专家, 总监, 总经理

**Salary filter:** ≥90k RMB/month (FLOOR — NEVER lower)

### Ashby (15-20 jobs target)
- All roles with APAC-friendly filter
- Target: Notion, Whatnot, Higgsfield, Stripe, Shopify
- Remove: US location-specific, healthcare-only

### Greenhouse (5-10 jobs target)
- Target: Stripe, Shopify, Airbnb, Figma
- URL pattern: `https://boards.greenhouse.io/{company}/jobs`
- Filter: PM/Program/Strategy Manager, APAC locations only

### Glassdoor (5-10 jobs target)
- HK/SZ/GZ/SG strategic PM roles
- May be blocked by bot detection (skip if blocked)

---

## Grading System

### Grade A+ (Top Priority)
- Director/VP level at major company
- HK/SG location
- Fintech, cross-border, AI focus

### Grade A (Strong Fit)
- English working language
- Senior/Lead/Principal level
- ≥90k RMB or competitive USD/HKD/SGD
- HK/SG/Remote (APAC-compatible)
- Fintech, cross-border, AI, digital banking, logistics tech

### Grade B (Good Fit)
- English mentioned
- Manager level (not senior, but not junior either)
- SZ/GZ/SH location
- Good company, strategic role

### Grade C (Stretch)
- No English mentioned but expert/senior level
- Target city
- ≥90k RMB/month
- Strategic role at good company

### Grade D / REMOVE
- Associate/assistant/graduate/entry-level
- <90k RMB/month on Liepin
- Engineering, hardware, manufacturing
- Chinese-language-only
- Old postings (>30 days)
- Support/analyst roles

---

## Output Files

| File | Purpose |
|------|---------|
| `OKComputer_职位搜索清单/jobs-all.json` | Unified database (all platforms) |
| `OKComputer_职位搜索清单/liepin-jobs.json` | Liepin results |
| `OKComputer_职位搜索清单/linkedin-jobs.json` | LinkedIn results |
| `OKComputer_职位搜索清单/ashby-jobs.json` | Ashby results |
| `OKComputer_职位搜索清单/greenhouse-jobs.json` | Greenhouse results |
| `OKComputer_职位搜索清单/glassdoor-jobs.json` | Glassdoor results |
| `OKComputer_职位搜索清单/job-database.html` | Main dashboard (GitHub Pages) |
| `OKComputer_职位搜索清单/jobs/*.html` | Individual job pages |

## GitHub
- **Repo:** https://github.com/[GITHUB_USER]/automation (HTTPS)
- **Live:** https://[GITHUB_USER].github.io/automation/job-database.html
- **Anonymized:** No personal name on public pages

---

## Automation Schedule
- **Cron Job ID:** `13fa95cd-5157-4b37-86de-0580923056ae`
- **Schedule:** Mon/Thu 9am Shanghai time
- **Workflow:** Parallel sub-agents → merge → grade → HTML → git push → WeChat

---

## WeChat Summary Format
```
🔍 Job Scan Complete — [DATE]
📊 Total: X quality jobs (Y new)
📍 HK (a), SG (b), SZ (c), Remote (d)
⭐ Grade A: X | Grade B: Y | Grade C: Z

🏆 Top 5:
1. [Title] — [Company] ([Location])
2. [Title] — [Company] ([Location])
3. [Title] — [Company] ([Location])
4. [Title] — [Company] ([Location])
5. [Title] — [Company] ([Location])

📋 Full database: https://[GITHUB_USER].github.io/automation/
```

---

## Privacy
- Resume is strictly private — context matching only
- Never upload/share resume publicly
- GitHub Pages anonymized (no personal name)

---

**Last updated:** 2026-06-06
**Version:** 3.0 (post-feedback — senior-level filters, ≥90k floor, parallel architecture)
