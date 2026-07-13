#!/usr/bin/env python3
"""Auto-maintain: run the full maintenance pipeline in one shot.

Steps:
  1. Merge *-results.json files into jobs-all.json
  2. Dedup by (company, title)
  3. Grade ungraded jobs
  4. Fill missing summaries, en_titles, quality_tiers
  5. Remove stale jobs (>30 days without posted_date)
  6. Regenerate coverage-report.json
  7. Rebuild dashboard.html
  8. Print summary of changes

Usage:
  python auto-maintain.py                # full run
  python auto-maintain.py --dry-run      # preview only, no writes
  python auto-maintain.py --skip-dashboard
  python auto-maintain.py --skip-cleanup
  python auto-maintain.py --report          # generate weekly-summary.md after pipeline
"""

import argparse
import glob
import json
import os
import re
import shutil
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

DIR = os.path.dirname(os.path.abspath(__file__))
ALL_FILE = os.path.join(DIR, "jobs-all.json")
COVERAGE_FILE = os.path.join(DIR, "coverage-report.json")
DASHBOARD_FILE = os.path.join(DIR, "dashboard.html")
BACKUP_FILE = ALL_FILE + ".bak"

# ─── Grading logic (adapted from grade-jobs.py) ───────────────────────────────

SENIOR_KEYWORDS = ["vp", "vice president", "director", "head of", "principal",
                   "chief", "c-level", "cxo", "svp", "evp", "general manager"]
MID_KEYWORDS = ["senior", "lead", "staff", "principal", "distinguished"]
ENTRY_KEYWORDS = ["associate", "junior", "intern", "assistant", "coordinator"]

TOP_COMPANIES = {
    "anthropic", "openai", "google", "meta", "bytedance", "tiktok", "alibaba",
    "tencent", "airbnb", "stripe", "coinbase", "binance", "okx", "huobi",
    "grab", "shopee", "lazada", "gojek", "sea group", "sea limited",
    "databricks", "snowflake", "figma", "notion", "vercel", "supabase",
    "toptal", "airwallex", "xendit", "revolut", "n26", "monzo",
    "plaid", "ramp", "brex", "chime", "nubank", "mercado pago",
    "agoda", "booking", "expedia", "klook", "trip.com",
    "samsung", "lg", "sony", "coupang", "instacart", "datadog",
    "twilio", "mercury", "adyen", "figma", "cloudflare", "affirm",
}

TIER1_LOCATIONS = {"singapore", "hong kong", "remote", "shanghai", "beijing", "shenzhen"}
TIER2_LOCATIONS = {"tokyo", "seoul", "taipei", "bangkok", "jakarta", "kuala lumpur", "manila"}

ZH_TITLE_MAP = {
    "高级": "Senior", "资深": "Senior", "总监": "Director", "经理": "Manager",
    "主管": "Lead", "专家": "Specialist", "架构师": "Architect",
    "工程师": "Engineer", "设计师": "Designer", "产品经理": "Product Manager",
    "数据": "Data", "算法": "Algorithm", "后端": "Backend", "前端": "Frontend",
    "移动端": "Mobile", "全栈": "Full Stack", "运维": "DevOps", "测试": "QA",
    "架构": "Architecture", "技术": "Tech", "产品": "Product", "运营": "Operations",
    "市场": "Marketing", "销售": "Sales", "财务": "Finance", "人力": "HR",
    "行政": "Admin", "法务": "Legal", "合规": "Compliance",
}


def is_chinese(text):
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def translate_title(zh_title):
    if not zh_title or not is_chinese(zh_title):
        return zh_title
    result = zh_title
    for zh, en in ZH_TITLE_MAP.items():
        result = result.replace(zh, en + " ")
    result = re.sub(r"\s+", " ", result).strip()
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", result))
    if chinese_chars > len(result) * 0.3:
        return zh_title
    return result


def classify_role(title):
    t = title.lower()
    if any(k in t for k in ["product manager", "product director", "product lead",
                             "product owner", "head of product", "product strategy",
                             "product operations", "product analyst"]):
        return "pm"
    if any(k in t for k in ["strategy", "operations", "gtm", "go-to-market"]):
        return "adjacent"
    if any(k in t for k in ["engineer", "developer", "architect", "sre", "devops"]):
        return "tech"
    if any(k in t for k in ["designer", "design lead", "ux", "ui"]):
        return "design"
    if any(k in t for k in ["marketing", "sales", "account executive",
                             "business development", "partnerships"]):
        return "business"
    if any(k in t for k in ["finance", "accounting", "financial", "controller"]):
        return "finance"
    if any(k in t for k in ["compliance", "legal", "regulatory", "risk"]):
        return "compliance"
    return "other"


def get_seniority(title):
    t = title.lower()
    if any(k in t for k in SENIOR_KEYWORDS):
        return "senior"
    if any(k in t for k in MID_KEYWORDS):
        return "mid"
    if any(k in t for k in ENTRY_KEYWORDS):
        return "entry"
    return "mid"


def grade_job(j):
    title = j.get("title", "")
    company = j.get("company", "").lower()
    location = j.get("location", "").lower()

    role = classify_role(title)
    seniority = get_seniority(title)

    if role == "pm":
        base = "A-2"
    elif role == "adjacent":
        base = "B"
    elif role in ("tech", "design"):
        base = "C"
    else:
        base = "C"

    if seniority == "senior":
        if base == "A-2":
            base = "A-1"
        elif base == "B":
            base = "A-2"
    elif seniority == "entry":
        if base == "A-2":
            base = "B"
        elif base == "A-1":
            base = "A-2"

    if company in TOP_COMPANIES:
        if base == "A-2":
            base = "A-1"
        elif base == "B":
            base = "A-2"

    if role not in ("pm", "adjacent") and seniority == "senior":
        if company in TOP_COMPANIES:
            base = "B"
        else:
            base = "C"

    return base


def auto_tier(grade):
    tier_map = {"S-1": "A", "A-1": "A", "A": "A", "A-2": "B",
                "B-1": "B", "B": "B", "B+": "B", "C": "C"}
    return tier_map.get(grade, "B")


def generate_summary(job):
    parts = []
    title = job.get("en_title") or job.get("title", "")
    company = job.get("company", "")
    location = job.get("location") or job.get("city_normalized", "")
    role_type = job.get("role_type", "")
    category = job.get("category", "")
    source = job.get("source", "")

    if title:
        parts.append(f"{title} role")
    if company:
        parts.append(f"at {company}")
    if location:
        parts.append(f"in {location}")
    if role_type:
        parts.append(f"({role_type})")
    if category:
        parts.append(f"— {category} focus")

    if not parts:
        return f"Job posting from {source}" if source else "Job posting"
    return " ".join(parts)


# ─── URL dedup helpers (from dedup-jobs.py) ───────────────────────────────────

LINKEDIN_SEARCH_RE = re.compile(
    r"^https?://(?:www\.)?linkedin\.com/jobs/search/", re.IGNORECASE
)


def is_generic_url(url):
    if not url:
        return True
    return bool(LINKEDIN_SEARCH_RE.match(url))


def url_specificity(url):
    if not url:
        return 0
    if is_generic_url(url):
        return 1
    return 2


# ─── Stale-date parsing ───────────────────────────────────────────────────────

def parse_posted_date(j):
    """Return a date or None from any of the date fields."""
    for field in ("date_posted", "posted_date", "created_at", "first_seen"):
        raw = j.get(field)
        if raw:
            try:
                return datetime.fromisoformat(str(raw)[:10]).date()
            except (ValueError, TypeError):
                continue
    return None


# ─── Coverage report builder ─────────────────────────────────────────────────

def build_coverage_report(jobs):
    source_counts = Counter()
    company_counts = Counter()
    grade_counts = Counter()
    location_counts = Counter()

    for j in jobs:
        source_counts[j.get("source", "?")] += 1
        company_counts[j.get("company", "?")] += 1
        grade_counts[j.get("grade", "?")] += 1
        location_counts[j.get("city_normalized") or j.get("location", "?")] += 1

    top_companies = dict(company_counts.most_common(20))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_jobs": len(jobs),
        "sources": {
            "unique_count": len(source_counts),
            "counts": dict(source_counts.most_common()),
        },
        "companies": {
            "unique_count": len(company_counts),
            "top_20": top_companies,
        },
        "grade_distribution": dict(grade_counts.most_common()),
        "locations": dict(location_counts.most_common(15)),
    }


# ─── Dashboard builder (inline, based on build-dashboard.py) ─────────────────

def build_dashboard_html(jobs):
    """Generate dashboard.html from jobs list. Returns the HTML string."""
    import html as html_mod

    grades = sorted(set(j.get("grade", "") for j in jobs if j.get("grade")))
    locations = sorted(set(j.get("city_normalized", j.get("location", ""))
                          for j in jobs if j.get("city_normalized") or j.get("location")))
    role_types = sorted(set(j.get("role_type", "") for j in jobs if j.get("role_type")))
    categories = sorted(set(j.get("category", "") for j in jobs if j.get("category")))

    grade_opts = "".join(
        f'<option value="{html_mod.escape(g)}">{html_mod.escape(g)}</option>' for g in grades
    )
    city_opts = "".join(
        f'<option value="{html_mod.escape(c)}">{html_mod.escape(c)}</option>' for c in locations
    )
    role_opts = "".join(
        f'<option value="{html_mod.escape(r)}">{html_mod.escape(r)}</option>' for r in role_types
    )
    cat_opts = "".join(
        f'<option value="{html_mod.escape(c)}">{html_mod.escape(c)}</option>' for c in categories
    )

    grade_counts = {}
    city_counts = {}
    cat_counts = {}
    eng_count = 0
    for j in jobs:
        g = j.get("grade", "")
        c = j.get("location", "")
        cat = j.get("category", "")
        grade_counts[g] = grade_counts.get(g, 0) + 1
        city_counts[c] = city_counts.get(c, 0) + 1
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        if j.get("english_friendly"):
            eng_count += 1

    now_dt = datetime.now()
    cutoff_7 = now_dt - timedelta(days=7)
    cutoff_30 = now_dt - timedelta(days=30)
    fresh_7d = 0
    fresh_30d = 0
    stale_count = 0
    for j in jobs:
        d = j.get("date_posted") or j.get("posted_date")
        if d:
            try:
                dt = datetime.fromisoformat(d.replace("Z", "+00:00"))
                if dt > cutoff_7:
                    fresh_7d += 1
                elif dt > cutoff_30:
                    fresh_30d += 1
                else:
                    stale_count += 1
            except Exception:
                pass

    stat_cards = [
        ("totalCount", str(len(jobs)), "Total Roles", "", "#38bdf8"),
        ("a1Count", str(grade_counts.get("A-1", 0)), "A-1 Perfect", "a1", "#4ade80"),
        ("a2Count", str(grade_counts.get("A-2", 0)), "A-2 Strong", "", "#60a5fa"),
        ("engCount", str(eng_count), "English Friendly", "", "#fbbf24"),
        ("fresh7", str(fresh_7d), "Past 7 Days", "fresh7", "#34d399"),
        ("fresh30", str(fresh_30d), "7-30 Days", "fresh30", "#fbbf24"),
        ("stale", str(stale_count), "30+ Days", "stale", "#f87171"),
    ]

    cards_html = ""
    for elem_id, num, label, extra_cls, _ in stat_cards:
        cls = f"stat-card {extra_cls}" if extra_cls else "stat-card"
        cards_html += f'<div class="{cls}"><div class="num" id="{elem_id}">{num}</div><div class="label">{label}</div></div>\n'

    jobs_json = json.dumps(jobs, ensure_ascii=False)
    now_str = datetime.now().strftime("%A, %B %d, %Y — %I:%M %p")

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>APAC Senior Roles Dashboard</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;padding:16px}}
.header{{text-align:center;padding:20px 0}}
.header h1{{font-size:1.8rem;background:linear-gradient(135deg,#38bdf8,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.header .subtitle{{color:#94a3b8;font-size:0.9rem;margin-top:4px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin:20px 0}}
.stat-card{{background:#1e293b;border-radius:12px;padding:16px;text-align:center;border:1px solid #334155}}
.stat-card .num{{font-size:2rem;font-weight:700;color:#38bdf8}}
.stat-card .label{{font-size:0.7rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-top:4px}}
.stat-card.a1 .num{{color:#4ade80}}
.filters{{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0;align-items:center}}
.filters select,.filters input{{background:#1e293b;border:1px solid #334155;color:#e2e8f0;padding:8px 12px;border-radius:8px;font-size:0.85rem}}
.filters input{{flex:1;min-width:200px}}
.filters select{{min-width:120px}}
.count{{color:#94a3b8;font-size:0.85rem;margin:8px 0}}
table{{width:100%;border-collapse:collapse;font-size:0.82rem}}
thead{{position:sticky;top:0;z-index:10}}
th{{background:#1e293b;padding:8px 10px;text-align:left;font-weight:600;color:#94a3b8;text-transform:uppercase;font-size:0.65rem;letter-spacing:1px;cursor:pointer;border-bottom:2px solid #334155;user-select:none}}
th:hover{{color:#e2e8f0}}
th .arrow{{margin-left:4px;font-size:0.6rem}}
td{{padding:8px 10px;border-bottom:1px solid #1e293b;vertical-align:middle}}
tr:hover{{background:#1e293b}}
.badge{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:0.65rem;font-weight:700;text-transform:uppercase}}
.badge-a1{{background:#064e3b;color:#4ade80;border:1px solid #065f46}}
.badge-a2{{background:#1e3a5f;color:#60a5fa;border:1px solid #1e40af}}
.badge-b{{background:#422006;color:#fbbf24;border:1px solid #854d0e}}
.badge-s1{{background:#3b0764;color:#c084fc;border:1px solid #6b21a8}}
.badge-en{{background:#1a3a2a;color:#86efac;border:1px solid #166534;font-size:0.6rem;padding:2px 6px;margin-left:4px}}
.city-tag{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.7rem;background:#334155;color:#cbd5e1}}
a{{color:#38bdf8;text-decoration:none}}
a:hover{{text-decoration:underline}}
.cat-tag{{display:inline-block;padding:2px 6px;border-radius:4px;font-size:0.6rem;margin-left:4px}}
.cat-ai{{background:#3b0764;color:#c084fc}}
.cat-cross{{background:#14532d;color:#86efac}}
.cat-strat{{background:#450a0a;color:#fca5a5}}
.cat-growth{{background:#422006;color:#fbbf24}}
.cat-platform{{background:#1e3a5f;color:#93c5fd}}
.cat-general{{background:#334155;color:#cbd5e1}}
.en-title{{color:#94a3b8;font-size:0.75rem;font-style:italic}}
.tier-a{{color:#4ade80;font-weight:700}}
.tier-b{{color:#60a5fa}}
.tier-c{{color:#fbbf24}}
.tier-d{{color:#f87171}}
.fresh-badge{{display:inline-block;padding:1px 6px;border-radius:4px;font-size:0.6rem;font-weight:700;margin-left:3px}}
.fresh-new{{background:#064e3b;color:#4ade80;border:1px solid #065f46}}
.fresh-old{{background:#450a0a;color:#fca5a5;border:1px solid #991b1b}}
.stat-card.fresh7 .num{{color:#34d399}}
.stat-card.fresh30 .num{{color:#fbbf24}}
.stat-card.stale .num{{color:#f87171;font-size:1rem}}
@media(max-width:768px){{
  table{{font-size:0.7rem}}
  td,th{{padding:5px 6px}}
  .stats{{grid-template-columns:repeat(3,1fr)}}
  .hide-mobile{{display:none}}
}}
</style>
</head>
<body>
<div class="header">
  <h1>🎯 APAC Senior Roles Dashboard</h1>
  <div class="subtitle">Generated: {now_str}</div>
</div>

<div class="stats">
{cards_html}</div>

<div class="filters">
  <input type="text" id="search" placeholder="🔍 Search title, company...">
  <select id="filterGrade"><option value="">All Grades</option>{grade_opts}</select>
  <select id="filterCity"><option value="">All Cities</option>{city_opts}</select>
  <select id="filterCategory"><option value="">All Categories</option>{cat_opts}</select>
  <select id="filterDifficulty"><option value="">All Platforms</option><option value="easy">⚡ Easy Apply</option><option value="medium">📋 Medium</option><option value="hard">⏳ Hard</option></select>
  <select id="filterEnglish"><option value="">All</option><option value="true">English Friendly</option></select>
</div>
<div class="count" id="showCount"></div>

<table>
<thead>
<tr>
  <th onclick="sortTable(0)">Grade <span class="arrow"></span></th>
  <th onclick="sortTable(1)">Title <span class="arrow"></span></th>
  <th onclick="sortTable(2)">Company <span class="arrow"></span></th>
  <th onclick="sortTable(3)">Location <span class="arrow"></span></th>
  <th onclick="sortTable(4)" class="hide-mobile">Posted <span class="arrow"></span></th>
  <th onclick="sortTable(5)" class="hide-mobile">Category <span class="arrow"></span></th>
  <th onclick="sortTable(6)" class="hide-mobile">Salary <span class="arrow"></span></th>
  <th>Link</th>
  <th>Search</th>
</tr>
</thead>
<tbody id="tableBody"></tbody>
</table>

<script>
const jobs = {jobs_json};

const catClasses = {{
  'ai_product': 'cat-ai',
  'cross_border': 'cat-cross',
  'strategy': 'cat-strat',
  'growth': 'cat-growth',
  'platform': 'cat-platform',
}};

function renderTable(data) {{
  const tbody = document.getElementById('tableBody');
  tbody.innerHTML = data.map(j => {{
    const gc = j.grade === 'A-1' ? 'badge-a1' : j.grade === 'A-2' ? 'badge-a2' : j.grade === 'B' ? 'badge-b' : 'badge-s1';
    const cc = catClasses[j.category] || 'cat-general';
    const catLabel = (j.category || '').replace(/_/g, ' ');
    const engBadge = j.english_friendly ? '<span class="badge badge-en">EN</span>' : '';
    const enTitle = j.en_title ? `<div class="en-title">${{j.en_title}}</div>` : '';
    let dateHtml = '—';
    const dp = j.date_posted || j.posted_date;
    if (dp) {{
      try {{
        const dt = new Date(dp);
        const now = new Date();
        const diffMs = now - dt;
        const diffDays = Math.floor(diffMs / (1000*60*60*24));
        const dateStr = dt.toLocaleDateString('en-US', {{month:'short', day:'numeric'}});
        if (diffDays < 7) dateHtml = `<span style="color:#34d399">${{dateStr}} <span class="fresh-badge fresh-new">NEW</span></span>`;
        else if (diffDays < 30) dateHtml = `<span style="color:#fbbf24">${{dateStr}}</span>`;
        else dateHtml = `<span style="color:#f87171">${{dateStr}} <span class="fresh-badge fresh-old">${{diffDays}}d</span></span>`;
      }} catch(e) {{ dateHtml = `<span style="color:#94a3b8">${{dp}}</span>`; }}
    }}
    const qualityTier = j.quality_tier || '';
    const qualityClass = qualityTier === 'A' ? 'tier-a' : qualityTier === 'B' ? 'tier-b' : qualityTier === 'C' ? 'tier-c' : 'tier-d';
    const qualityHtml = qualityTier ? `<span class="${{qualityClass}}">Q${{qualityTier}}</span>` : '';
    const link = j.url ? `<a href="${{j.url}}" target="_blank" rel="noopener">Apply →</a>` : '<span style="color:#64748b">—</span>';
    let searchLink = '';
    if (j.url) {{
      try {{
        const domain = new URL(j.url).hostname.replace('www.','');
        const siteQuery = encodeURIComponent(`site:${{domain}} "${{j.title}}"`);
        searchLink = `<a href="https://www.google.com/search?q=${{siteQuery}}" target="_blank" rel="noopener" style="color:#8b949e;font-size:0.7rem">🔍</a>`;
      }} catch(e) {{
        const fallback = encodeURIComponent(j.title + ' ' + j.company);
        searchLink = `<a href="https://www.google.com/search?q=${{fallback}}" target="_blank" rel="noopener" style="color:#8b949e;font-size:0.7rem">🔍</a>`;
      }}
    }}
    return `<tr>
      <td><span class="badge ${{gc}}">${{j.grade}}</span> ${{qualityHtml}}</td>
      <td><strong>${{j.title}}</strong>${{engBadge}}${{enTitle}}</td>
      <td>${{j.company}}</td>
      <td><span class="city-tag">${{j.city_normalized || j.location}}</span></td>
      <td class="hide-mobile">${{dateHtml}}</td>
      <td class="hide-mobile"><span class="cat-tag ${{cc}}">${{catLabel}}</span></td>
      <td class="hide-mobile" style="color:#94a3b8;font-size:0.7rem">${{j.salary||'—'}}</td>
      <td>${{link}}</td>
      <td>${{searchLink}}</td>
    </tr>`;
  }}).join('');
  document.getElementById('showCount').textContent = `Showing ${{data.length}} of ${{jobs.length}} roles`;
}}

function filterData() {{
  const q = document.getElementById('search').value.toLowerCase();
  const g = document.getElementById('filterGrade').value;
  const c = document.getElementById('filterCity').value;
  const cat = document.getElementById('filterCategory').value;
  const diff = document.getElementById('filterDifficulty').value;
  const eng = document.getElementById('filterEnglish').value;
  let d = jobs.filter(j => {{
    if (q && !j.title.toLowerCase().includes(q) && !j.company.toLowerCase().includes(q) && !(j.en_title||'').toLowerCase().includes(q)) return false;
    if (g && j.grade !== g) return false;
    const cLoc = j.city_normalized || j.location || '';
    if (c && cLoc !== c) return false;
    if (cat && j.category !== cat) return false;
    if (diff && j.app_difficulty !== diff) return false;
    if (eng === 'true' && !j.english_friendly) return false;
    return true;
  }});
  renderTable(d);
}}

let sortCol = -1, sortAsc = true;
function sortTable(col) {{
  if (sortCol === col) sortAsc = !sortAsc; else {{ sortCol = col; sortAsc = true; }}
  const keys = ['grade','title','company','location','date_posted','category','salary'];
  const order = {{'S-1':-1,'A-1':0,'A-2':1,'B':2,'C':3}};
  jobs.sort((a,b) => {{
    let va = a[keys[col]] || '', vb = b[keys[col]] || '';
    if (col === 0) {{ va = order[va]||9; vb = order[vb]||9; }}
    if (col === 4 && keys[col] === 'date_posted') {{ va = a.date_posted||a.posted_date||''; vb = b.date_posted||b.posted_date||''; }}
    if (va < vb) return sortAsc ? -1 : 1;
    if (va > vb) return sortAsc ? 1 : -1;
    return 0;
  }});
  filterData();
}}

['search','filterGrade','filterCity','filterCategory','filterDifficulty','filterEnglish'].forEach(id => document.getElementById(id).addEventListener('input', filterData));
renderTable(jobs);
</script>
</body>
</html>'''


# ─── Main pipeline ────────────────────────────────────────────────────────────

def log(msg, dry_run=False):
    prefix = "[DRY-RUN] " if dry_run else ""
    print(f"{prefix}{msg}")


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        return None


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    parser = argparse.ArgumentParser(description="Run the full job database maintenance pipeline.")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files.")
    parser.add_argument("--skip-dashboard", action="store_true", help="Skip dashboard.html regeneration.")
    parser.add_argument("--skip-cleanup", action="store_true", help="Skip stale job removal.")
    parser.add_argument("--report", action="store_true", help="Generate weekly-summary.md after pipeline.")
    args = parser.parse_args()

    dry_run = args.dry_run
    log("═══════════════════════════════════════════════════", dry_run)
    log("  Auto-Maintain Pipeline", dry_run)
    log(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", dry_run)
    log(f"  Mode: {'DRY-RUN (no writes)' if dry_run else 'LIVE'}", dry_run)
    log("═══════════════════════════════════════════════════", dry_run)

    # ── Load existing jobs ────────────────────────────────────────────────
    existing = load_json(ALL_FILE)
    if existing is None:
        existing = []
        log(f"⚠  No jobs-all.json found — starting fresh", dry_run)

    count_before = len(existing)
    log(f"\n📂 Starting jobs: {count_before}", dry_run)

    # ── Step 1: Merge *-results.json files ────────────────────────────────
    log("\n── Step 1: Merge *-results.json files ──", dry_run)
    # Collect all candidate source files: *-results.json, scan-*.json, *-jobs.json
    result_files = sorted(glob.glob(os.path.join(DIR, "*-results.json")))
    scan_files = sorted(glob.glob(os.path.join(DIR, "scan-*.json")))
    source_files = sorted(glob.glob(os.path.join(DIR, "*-jobs.json")))
    # Deduplicate
    all_sources = list(dict.fromkeys(result_files + scan_files + source_files))

    if not all_sources:
        log("  No source files found (*-results.json or *-jobs.json)", dry_run)
    else:
        seen = set()
        for j in existing:
            key = (j.get("title", "").strip(), j.get("company", "").strip(),
                   j.get("location", "").strip())
            seen.add(key)

        new_count = 0
        for src in all_sources:
            basename = os.path.basename(src)
            raw = load_json(src)
            if raw is None:
                log(f"  ⚠  Skipping unreadable file: {basename}", dry_run)
                continue
            # Handle dict-format files (e.g. {jobs: [...]})
            if isinstance(raw, dict):
                jobs = raw.get("jobs", [])
            elif isinstance(raw, list):
                jobs = raw
            else:
                log(f"  ⚠  Skipping {basename}: unexpected format ({type(raw).__name__})", dry_run)
                continue
            added = 0
            for j in jobs:
                if not isinstance(j, dict):
                    continue
                key = (j.get("title", "").strip(), j.get("company", "").strip(),
                       j.get("location", "").strip())
                if key not in seen:
                    seen.add(key)
                    existing.append(j)
                    new_count += 1
                    added += 1
            log(f"  {basename}: {added} new / {len(jobs)} total", dry_run)

        log(f"  Merged: {new_count} new jobs from {len(all_sources)} files", dry_run)

    # ── Step 2: Dedup by (company, title) ─────────────────────────────────
    log("\n── Step 2: Dedup by (company, title) ──", dry_run)
    dedup_before = len(existing)
    groups = {}
    for j in existing:
        key = (j.get("title", "").strip(), j.get("company", "").strip())
        groups.setdefault(key, []).append(j)

    cleaned = []
    dedup_removed = 0
    for key, group in groups.items():
        if len(group) == 1:
            cleaned.append(group[0])
        else:
            best = max(group, key=lambda j: (
                url_specificity(j.get("url", "")),
                j.get("scanned_date", ""),
            ))
            cleaned.append(best)
            dedup_removed += len(group) - 1

    existing = cleaned
    log(f"  Before dedup: {dedup_before} → After: {len(existing)} (removed {dedup_removed} dupes)", dry_run)

    # ── Step 3: Grade ungraded jobs ───────────────────────────────────────
    log("\n── Step 3: Grade ungraded jobs ──", dry_run)
    graded_count = 0
    for j in existing:
        if not j.get("grade"):
            j["grade"] = grade_job(j)
            graded_count += 1
    log(f"  Graded {graded_count} previously ungraded jobs", dry_run)

    # Show grade distribution
    grades = Counter(j.get("grade", "?") for j in existing)
    log(f"  Grade distribution: {dict(sorted(grades.items()))}", dry_run)

    # ── Step 4: Fill missing summaries, en_titles, quality_tiers ──────────
    log("\n── Step 4: Fill missing fields ──", dry_run)
    stats = {"en_titles": 0, "summaries": 0, "quality_tiers": 0, "en_translated": 0}

    for job in existing:
        # en_title
        if not job.get("en_title"):
            title = job.get("title", "")
            if is_chinese(title):
                translated = translate_title(title)
                if translated != title:
                    job["en_title"] = translated
                    stats["en_translated"] += 1
                else:
                    job["en_title"] = title
            else:
                job["en_title"] = title
            stats["en_titles"] += 1

        # summary
        if not job.get("summary"):
            job["summary"] = generate_summary(job)
            stats["summaries"] += 1

        # quality_tier
        if not job.get("quality_tier"):
            job["quality_tier"] = auto_tier(job.get("grade", "B"))
            stats["quality_tiers"] += 1

    log(f"  en_titles filled: {stats['en_titles']} ({stats['en_translated']} translated from Chinese)", dry_run)
    log(f"  summaries filled: {stats['summaries']}", dry_run)
    log(f"  quality_tiers filled: {stats['quality_tiers']}", dry_run)

    # ── Step 5: Remove stale jobs (>30 days) ─────────────────────────────
    removed_stale = 0
    removed_empty = 0
    if not args.skip_cleanup:
        log("\n── Step 5: Remove stale/empty jobs ──", dry_run)
        today = datetime.now().date()
        kept = []
        for j in existing:
            title = (j.get("title") or "").strip()
            company = (j.get("company") or "").strip()
            if not title or not company:
                removed_empty += 1
                continue

            posted = parse_posted_date(j)
            if posted and (today - posted).days > 30:
                removed_stale += 1
                continue

            kept.append(j)

        existing = kept
        log(f"  Removed {removed_stale} stale (>30d) + {removed_empty} empty-field jobs", dry_run)
        log(f"  Remaining: {len(existing)}", dry_run)
    else:
        log("\n── Step 5: Skipped (--skip-cleanup) ──", dry_run)

    # Sort by grade then company
    grade_order = {"A-1": 0, "A-2": 1, "B": 2, "C": 3}
    existing.sort(key=lambda j: (grade_order.get(j.get("grade", ""), 9),
                                 j.get("company", "")))

    # ── Step 6: Regenerate coverage-report.json ───────────────────────────
    log("\n── Step 6: Regenerate coverage-report.json ──", dry_run)
    coverage = build_coverage_report(existing)
    if not dry_run:
        save_json(COVERAGE_FILE, coverage)
        log(f"  Written to {COVERAGE_FILE}", dry_run)
    else:
        log(f"  Would write {COVERAGE_FILE} ({len(existing)} jobs, {coverage['sources']['unique_count']} sources)", dry_run)

    # ── Step 7: Rebuild dashboard.html ────────────────────────────────────
    if not args.skip_dashboard:
        log("\n── Step 7: Rebuild dashboard.html ──", dry_run)
        if not dry_run:
            html = build_dashboard_html(existing)
            with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
                f.write(html)
            log(f"  Written to {DASHBOARD_FILE}", dry_run)
        else:
            log(f"  Would write {DASHBOARD_FILE}", dry_run)
    else:
        log("\n── Step 7: Skipped (--skip-dashboard) ──", dry_run)

    # ── Save jobs-all.json ────────────────────────────────────────────────
    if not dry_run:
        # Backup before overwrite
        if os.path.exists(ALL_FILE):
            shutil.copy2(ALL_FILE, BACKUP_FILE)
            log(f"\n💾 Backup saved: {BACKUP_FILE}", dry_run)
        save_json(ALL_FILE, existing)
        log(f"💾 Saved: {ALL_FILE}", dry_run)
    else:
        log(f"\n💾 Would save {ALL_FILE} ({len(existing)} jobs)", dry_run)

    # ── Step 8: Summary ───────────────────────────────────────────────────
    log("\n═══════════════════════════════════════════════════", dry_run)
    log("  Summary", dry_run)
    log("═══════════════════════════════════════════════════", dry_run)
    log(f"  Before:    {count_before} jobs", dry_run)
    log(f"  After:     {len(existing)} jobs", dry_run)
    log(f"  Merged:    +{new_count if all_sources else 0} from source files", dry_run)
    log(f"  Deduped:   -{dedup_removed}", dry_run)
    log(f"  Graded:    {graded_count} new grades", dry_run)
    log(f"  Filled:    {stats['en_titles']} en_titles, {stats['summaries']} summaries, {stats['quality_tiers']} tiers", dry_run)
    if not args.skip_cleanup:
        log(f"  Stale removed: {removed_stale + removed_empty} ({removed_stale} stale, {removed_empty} empty)", dry_run)
    log(f"  Coverage:  {coverage['sources']['unique_count']} sources, {coverage['companies']['unique_count']} companies", dry_run)
    log(f"  Grade dist: {dict(sorted(Counter(j.get('grade','?') for j in existing).items()))}", dry_run)
    log(f"  English friendly: {sum(1 for j in existing if j.get('english_friendly'))}", dry_run)
    log("═══════════════════════════════════════════════════", dry_run)

    if dry_run:
        log("\n🔍 Dry-run complete — no files were modified.", dry_run)
    else:
        log("\n✅ Pipeline complete!", dry_run)

    # ── Optional: Weekly Summary Report ──────────────────────────────────
    if args.report and not dry_run:
        generate_weekly_report(existing)


def generate_weekly_report(jobs):
    """Generate a human-readable weekly-summary.md from the current job data."""
    from collections import Counter
    report_path = os.path.join(DIR, "weekly-summary.md")

    today = datetime.now().strftime("%Y-%m-%d")
    total = len(jobs)

    # Grade distribution
    grades = Counter(j.get("grade", "?") for j in jobs)
    grade_lines = "\n".join(f"  - **{g}**: {c}" for g, c in sorted(grades.items()))

    # Quality tiers
    tiers = Counter(j.get("quality_tier", "unknown") for j in jobs)
    tier_lines = "\n".join(f"  - **{t}**: {c}" for t, c in sorted(tiers.items()))

    # Top companies by job count
    companies = Counter()
    for j in jobs:
        co = j.get("company", "unknown")
        if co and co != "unknown":
            companies[co] += 1
    top10 = companies.most_common(10)
    top_lines = "\n".join(f"  1. {co} ({n})" for co, n in top10)

    # Language split
    en_friendly = sum(1 for j in jobs if j.get("english_friendly"))
    zh_only = total - en_friendly

    # Sources
    sources = Counter()
    for j in jobs:
        src = j.get("source", j.get("platform", "unknown"))
        if src:
            sources[src] += 1
    src_lines = "\n".join(f"  - **{s}**: {c}" for s, c in sources.most_common(10))

    # Recent additions (last 7 days)
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(days=7)
    recent = []
    for j in jobs:
        ds = j.get("date_found", "") or j.get("scanned_date", "")
        if ds:
            try:
                dt = datetime.fromisoformat(ds[:19])
                if dt >= cutoff:
                    recent.append(j)
            except:
                pass

    recent_lines = "\n".join(
        f"  - **{j.get('company','?')}** — {j.get('title','?')[:60]}"
        for j in recent[:15]
    ) or "  _No new jobs in the last 7 days._"

    md = f"""# 📊 Weekly Career Summary — {today}

> Auto-generated by `auto-maintain.py --report`

## Overview
- **Total jobs**: {total}
- **English-friendly**: {en_friendly}
- **Chinese-only**: {zh_only}
- **New this week**: {len(recent)}

## Grade Distribution
{grade_lines}

## Quality Tiers
{tier_lines}

## Top 10 Companies
{top_lines}

## Job Sources
{src_lines}

## New Jobs (Last 7 Days)
{recent_lines}

---
_Generated {today} by Career OS auto-maintain_
"""

    with open(report_path, "w") as f:
        f.write(md)
    log(f"\n📋 Weekly summary written to {report_path}", False)
    log(f"   {total} jobs | {len(recent)} new this week", False)


if __name__ == "__main__":
    main()
