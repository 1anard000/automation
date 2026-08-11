# CRM Enrichment Report

**Generated:** 2026-08-03  
**File:** contacts.json

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total contacts | 206 |
| Real people (executive/peer) | 10 |
| → Executive | 5 |
| → Peer | 5 |
| Company ATS entries | 154 |
| Company Target entries | 42 |
| Other/Uncategorized | 0 |

## Enrichment Changes

- **Fields added:** 10
- **Companies cross-referenced with jobs:** 89

### Changes Applied

#### Real People (Executive/Peer)
- Added `category: person` and `is_person: true`
- Cross-referenced A/S-grade jobs at their company → `matching_a_s_jobs` array
- Preserved all existing fields (email, LinkedIn, connection info)

#### Company ATS Entries
- Added `is_system: true` and `category: ats`
- Cross-referenced total jobs from jobs-all.json → `total_jobs_in_database`, `top_jobs_from_database`, `job_grades_found`

#### Company Target Entries
- Added `is_company: true` and `category: "target"`
- Cross-referenced total jobs from jobs-all.json → `total_jobs_in_database`, `top_jobs_from_database`, `job_grades_found`

## Quality Score

| Metric | Value |
|--------|-------|
| Average enrichment completeness | 100.0% |
| Contacts with 100% completeness | 100.0% |

### Completeness criteria: name, role_type, category

## Data Integrity

- ✅ No contacts deleted
- ✅ All existing fields preserved
- ✅ New fields are additive only

## Real People Detail

### Emily Watson — Head of Product @ Airwallex
- **Email:** emily.w@airwallex.com
- **LinkedIn:** None
- **Connection:** AWS Summit Beijing 2025
- **Relationship:** weak
- **A/S-grade jobs at company:** 2
  - Director, Product Strategy (Grade: A-) — Singapore
  - Senior Product Manager, Kai (AI assistant) (Grade: A) — Singapore

### Robert Kim — Research Engineer @ Anthropic
- **Email:** r.kim@anthropic.com
- **LinkedIn:** None
- **Connection:** Met at ML meetup
- **Relationship:** strong
- **A/S-grade jobs at company:** 4
  - Head of APAC Accounting (Grade: A) — Singapore
  - Finance & Strategy, GTM - Korea (Grade: A) — Seoul, South Korea
  - Product Support Specialist (Singapore) (Grade: A) — Singapore
  - Product Support Specialist (Singapore - Weekend Coverage) (Grade: A) — Singapore

### David Liu — Engineering Director @ ByteDance
- **Email:** david.liu@bytedance.com
- **LinkedIn:** None
- **Connection:** Tech conference in Shanghai
- **Relationship:** weak
- **A/S-grade jobs at company:** 10
  - 印尼中小商家策略Leader-TikTok Shop (Grade: A) — 深圳
  - 国际化商业策略产品经理-端变现 (Grade: A) — 北京
  - 国际投放增长运营专家-飞书 (Grade: A) — 深圳
  - Solutions Expert - Video Cloud (Grade: A) — Singapore
  - AI策略产品经理 - AI创新业务 (Grade: A) — 上海

### Amanda Foster — Staff Software Engineer @ Google
- **Email:** amanda@google.com
- **LinkedIn:** None
- **Connection:** Google I/O 2025
- **Relationship:** strong
- **A/S-grade jobs at company:** 1
  - Head of Strategic SMB Partnerships, JAPAC (Grade: A-1) — Singapore

### Thomas Anderson — Research Scientist @ Meta
- **Email:** t.anderson@meta.com
- **LinkedIn:** None
- **Connection:** FAIR seminar
- **Relationship:** weak
- **A/S-grade jobs at company:** 1
  - Director, Product Management - APAC Products (Grade: A-) — Singapore

### Sarah Chen — VP of AI Research @ NVIDIA
- **Email:** sarah.chen@nvidia.com
- **LinkedIn:** None
- **Connection:** Met at NeurIPS 2025 conference
- **Relationship:** strong
- **A/S-grade jobs at company:** 0

### Michael Zhang — Senior Research Scientist @ OpenAI
- **Email:** m.zhang@openai.com
- **LinkedIn:** None
- **Connection:** Introduced by Sarah Chen
- **Relationship:** strong
- **A/S-grade jobs at company:** 0

### Lisa Wang — Partner @ Sequoia Capital
- **Email:** lisa.wang@sequoiacap.com
- **LinkedIn:** None
- **Connection:** Startup demo day
- **Relationship:** strong
- **A/S-grade jobs at company:** 0

### Jessica Park — Autopilot ML Lead @ Tesla
- **Email:** jessica.park@tesla.com
- **LinkedIn:** None
- **Connection:** Stanford AI Seminar
- **Relationship:** strong
- **A/S-grade jobs at company:** 0

### James Miller — Group Partner @ Y Combinator
- **Email:** james.m@ycombinator.com
- **LinkedIn:** None
- **Connection:** YC office hours
- **Relationship:** weak
- **A/S-grade jobs at company:** 0

## Top Companies by Job Count (from jobs-all.json)

- **OKX**: 191 jobs
- **Okx**: 191 jobs
- **Stripe**: 179 jobs
- **Agoda**: 158 jobs
- **Coupang**: 136 jobs
- **Anthropic**: 91 jobs
- **ByteDance**: 35 jobs
- **Tencent**: 29 jobs
- **Affirm**: 25 jobs
- **Airbnb**: 24 jobs
- **Airwallex**: 15 jobs
- **Adyen**: 14 jobs
- **GitLab**: 12 jobs
- **Gitlab**: 12 jobs
- **Xendit**: 11 jobs
