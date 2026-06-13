# Career OS — Architecture Spec

## Where Things Live

### 🌐 Public GitHub Pages (https://1anard000.github.io/automation/)
**Purpose:** Things useful to pull up on your phone or any browser.

| Item | Why Public |
|---|---|
| Job dashboard (HTML) | Quick reference when networking, at events, on the go |
| Career strategy (anonymized) | Market trends, salary benchmarks — no personal info |
| Event/conference links | Useful to access from mobile |
| Company target list | Quick lookup during conversations |

**Rule:** Zero personal info. No names, emails, employer history, specific applications.

---

### 📄 Google Drive (via MCP)
**Purpose:** Documents you need to read/edit from any device.

| Item | Why Google Drive |
|---|---|
| Cover letters | Edit from phone, share with recruiters, version history |
| Application tracker (Sheets) | Update from anywhere, auto-formulas, shareable |
| Resume variants | Access anywhere, easy to send links |
| Interview notes | If needed — quick reference during calls |

**Access:** Read via MCP in OpenClaw. Write when needed (cover letter generation → Google Doc).

**Gmail (read-only):** Scan inbox for recruiter emails, application confirmations, interview invites. Never send.

---

### 📁 Local Private Folder (`private/`, gitignored)
**Purpose:** Working files that should never leave the machine.

| Item | Why Local |
|---|---|
| Raw application data | Tracker JSON, priority queue |
| Personal strategy notes | Unfiltered thoughts, negotiation prep |
| Credential files | OAuth secrets, API keys |
| Draft documents | Work-in-progress before uploading to Drive |

---

## Data Flow

```
Scanner (cron) → jobs-all.json → build-dashboard.py → index.html → GitHub Pages
                                  ↓
                          Google Sheets (app tracker) ← Application Pipeline
                                  ↓
                          Google Docs (cover letters) ← Cover Letter Generator
                                  ↓
                          Gmail (read-only) ← Inbox Scanner (recruiter emails)
```

## MCP Servers

| Server | Access | Purpose |
|---|---|---|
| `google-drive` | Read/Write | Create/update Google Docs & Sheets |
| `gmail-readonly` | **Read-only** | Scan inbox for opportunities, never send |
| `google-calendar` | Read | Check schedule for interviews/events |

## Security Rules

1. **Public repo:** Never commit names, emails, employer history, specific applications
2. **Gmail MCP:** Read-only. No sending, no replying, no drafts.
3. **Google Drive:** Write access for cover letters and tracker. No deleting.
4. **Private folder:** Gitignored. Never pushed. Contains raw personal data.
5. **Credentials:** `~/.openclaw/google-credentials/` — never commit, never share.

## What Goes Where — Decision Tree

```
Is it personal info (name, email, employer, specific apps)?
  YES → private/ folder or Google Drive
  NO  → Is it useful on mobile/browser?
    YES → Public GitHub Pages (dashboard, strategy, events)
    NO  → Does it need editing from multiple devices?
      YES → Google Drive
      NO  → private/ folder
```
