#!/usr/bin/env python3
"""Build the CRM Dashboard HTML from jobs-all.json and contacts.json."""
import json
import os
import re
from html import escape

DIR = os.path.dirname(os.path.abspath(__file__))

def load(fn):
    with open(os.path.join(DIR, fn)) as f:
        return json.load(f)

def compute_outreach_score(c):
    """From crm-prioritize.py"""
    score = 0
    strength = c.get("relationship_strength", "weak")
    if strength == "strong": score += 40
    elif strength == "warm": score += 25
    mj = c.get("matching_jobs", 0)
    mj_count = len(mj) if isinstance(mj, list) else (mj if isinstance(mj, int) else 0)
    score += min(mj_count * 3, 30)
    if c.get("email"): score += 10
    if c.get("wechat"): score += 8
    if c.get("linkedin"): score += 5
    if c.get("follow_up_needed") == "true": score += 15
    if c.get("application_status") and c["application_status"] != "none": score += 12
    grades = c.get("job_grades_found", [])
    if isinstance(grades, list):
        a_count = sum(1 for g in grades if g == "A")
        score += a_count * 5
    return score

def parse_grade_counts(grade_list):
    """Parse job_grades_found like ['A(5)', 'B(20)'] into {A: 5, B: 20}"""
    result = {}
    if not isinstance(grade_list, list):
        return result
    for g in grade_list:
        m = re.match(r'^([A-Za-z0-9+\-]+)\((\d+)\)$', str(g))
        if m:
            result[m.group(1)] = int(m.group(2))
        else:
            result[str(g)] = 1
    return result

def main():
    jobs = load("jobs-all.json")
    contacts = load("contacts.json")

    # Build company->jobs lookup
    company_jobs = {}
    for j in jobs:
        co = j.get("company", "")
        if co not in company_jobs:
            company_jobs[co] = []
        company_jobs[co].append(j)

    # Global grade distribution
    grade_dist = {}
    for j in jobs:
        g = j.get("grade", "?")
        grade_dist[g] = grade_dist.get(g, 0) + 1

    # Build company summary data
    company_data = []
    for co, cjobs in company_jobs.items():
        grades = {}
        salary_ranges = []
        en_count = 0
        locations = set()
        for j in cjobs:
            g = j.get("grade", "?")
            grades[g] = grades.get(g, 0) + 1
            sal = j.get("salary", "")
            if sal and sal != "Not listed" and sal.strip():
                salary_ranges.append(sal)
            if j.get("english_friendly"):
                en_count += 1
            loc = j.get("location", "")
            if loc:
                locations.add(loc)
        company_data.append({
            "company": co,
            "job_count": len(cjobs),
            "grades": grades,
            "salary_count": len(salary_ranges),
            "en_pct": round(en_count / len(cjobs) * 100) if cjobs else 0,
            "locations": list(locations)[:5],
            "top_jobs": [{"title": j.get("title",""), "grade": j.get("grade",""), "url": j.get("url",""), "location": j.get("location",""), "salary": j.get("salary","")} for j in sorted(cjobs, key=lambda x: -x.get("quality_score",0))[:5]]
        })
    company_data.sort(key=lambda x: -x["job_count"])

    # Build contacts data
    persons = []
    target_contacts = []
    ats_contacts = []
    for c in contacts:
        c["_outreach_score"] = compute_outreach_score(c)
        cat = c.get("category", "")
        if cat == "person":
            persons.append(c)
        elif cat == "target":
            target_contacts.append(c)
        elif cat == "ats":
            ats_contacts.append(c)

    # Determine pipeline stages
    for c in contacts:
        status = c.get("application_status", "prospect")
        strength = c.get("relationship_strength", "weak")
        if status in ("applied", "interviewing", "offer"):
            c["_pipeline_stage"] = "active"
        elif status == "prepared":
            c["_pipeline_stage"] = "warm"
        elif status == "expired":
            c["_pipeline_stage"] = "expired"
        elif strength == "strong" or strength == "warm":
            c["_pipeline_stage"] = "warm"
        else:
            c["_pipeline_stage"] = "cold"

    persons.sort(key=lambda x: -x.get("_outreach_score", 0))
    target_contacts.sort(key=lambda x: -x.get("open_roles_count", 0))
    ats_contacts.sort(key=lambda x: -x.get("open_roles_count", 0))

    # Write dashboard
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CRM Dashboard — Job Search Pipeline</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;padding:16px;min-height:100vh}}
a{{color:#38bdf8;text-decoration:none}}a:hover{{text-decoration:underline}}

/* Header */
.header{{text-align:center;padding:20px 0 10px}}
.header h1{{font-size:1.8rem;background:linear-gradient(135deg,#38bdf8,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.header .subtitle{{color:#94a3b8;font-size:0.9rem;margin-top:4px}}
.header .updated{{color:#64748b;font-size:0.75rem;margin-top:2px}}

/* Stats bar */
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin:16px 0}}
.stat-card{{background:#1e293b;border-radius:12px;padding:14px;text-align:center;border:1px solid #334155}}
.stat-card .num{{font-size:1.8rem;font-weight:700;color:#38bdf8}}
.stat-card .label{{font-size:0.65rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-top:2px}}
.stat-card.green .num{{color:#4ade80}}.stat-card.purple .num{{color:#a78bfa}}.stat-card.orange .num{{color:#fb923c}}.stat-card.pink .num{{color:#f472b6}}.stat-card.teal .num{{color:#2dd4bf}}

/* Tabs */
.tabs{{display:flex;gap:0;margin:16px 0 0;border-bottom:2px solid #334155}}
.tab{{padding:10px 20px;cursor:pointer;color:#94a3b8;font-size:0.85rem;font-weight:600;border-bottom:2px solid transparent;margin-bottom:-2px;transition:all .2s}}
.tab:hover{{color:#e2e8f0}}.tab.active{{color:#38bdf8;border-bottom-color:#38bdf8}}

/* Search/Filter bar */
.filter-bar{{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0;align-items:center}}
.filter-bar input,.filter-bar select{{background:#1e293b;border:1px solid #334155;color:#e2e8f0;padding:7px 12px;border-radius:8px;font-size:0.82rem}}
.filter-bar input{{flex:1;min-width:180px}}.filter-bar select{{min-width:110px}}
.filter-bar .count{{color:#94a3b8;font-size:0.82rem;margin-left:auto}}

/* Tab content */
.tab-content{{display:none}}.tab-content.active{{display:block}}

/* Tables */
table{{width:100%;border-collapse:collapse;font-size:0.8rem}}
thead th{{background:#1e293b;padding:8px 10px;text-align:left;font-weight:600;color:#94a3b8;text-transform:uppercase;font-size:0.62rem;letter-spacing:1px;cursor:pointer;border-bottom:2px solid #334155;white-space:nowrap;user-select:none}}
thead th:hover{{color:#e2e8f0}}
th .arrow{{margin-left:3px;font-size:0.55rem}}
td{{padding:7px 10px;border-bottom:1px solid #1e293b;vertical-align:middle}}
tr:hover{{background:rgba(56,189,248,0.05)}}

/* Badges */
.badge{{display:inline-block;padding:2px 8px;border-radius:20px;font-size:0.6rem;font-weight:700;text-transform:uppercase}}
.grade-s{{background:#3b0764;color:#c084fc;border:1px solid #6b21a8}}
.grade-a{{background:#064e3b;color:#4ade80;border:1px solid #065f46}}
.grade-b{{background:#422006;color:#fbbf24;border:1px solid #854d0e}}
.grade-c{{background:#1e293b;color:#94a3b8;border:1px solid #475569}}
.grade-other{{background:#334155;color:#cbd5e1;border:1px solid #475569}}

/* Pipeline */
.pipeline{{display:flex;gap:12px;margin:16px 0;overflow-x:auto;padding-bottom:8px}}
.pipeline-stage{{flex:1;min-width:220px;background:#1e293b;border-radius:12px;padding:12px;border:1px solid #334155}}
.pipeline-stage .stage-header{{font-weight:700;font-size:0.85rem;margin-bottom:10px;display:flex;align-items:center;gap:6px}}
.pipeline-stage .stage-count{{background:#334155;padding:1px 8px;border-radius:10px;font-size:0.7rem;color:#94a3b8}}
.pipeline-card{{background:#0f172a;border-radius:8px;padding:10px;margin-bottom:8px;border:1px solid #334155;font-size:0.78rem}}
.pipeline-card:hover{{border-color:#38bdf8}}
.pipeline-card .name{{font-weight:600;color:#e2e8f0}}.pipeline-card .company{{color:#94a3b8;font-size:0.72rem}}
.pipeline-card .meta{{margin-top:4px;display:flex;gap:6px;flex-wrap:wrap}}

/* Score pill */
.score{{display:inline-block;padding:1px 7px;border-radius:10px;font-size:0.65rem;font-weight:700}}
.score-high{{background:#064e3b;color:#4ade80}}.score-med{{background:#422006;color:#fbbf24}}.score-low{{background:#450a0a;color:#fca5a5}}

/* Mini pie placeholder */
.mini-pie{{width:32px;height:32px;border-radius:50%;display:inline-block;vertical-align:middle;margin-right:6px}}

/* Charts row */
.charts-row{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:16px 0}}
.chart-box{{background:#1e293b;border-radius:12px;padding:16px;border:1px solid #334155}}
.chart-box h3{{font-size:0.8rem;color:#94a3b8;margin-bottom:10px;text-transform:uppercase;letter-spacing:1px}}
.chart-box canvas{{max-height:260px}}
@media(max-width:768px){{.charts-row{{grid-template-columns:1fr}}}}

/* Relationship strength */
.strength-strong{{color:#4ade80}}.strength-warm{{color:#fbbf24}}.strength-weak{{color:#94a3b8}}

/* Status badges */
.status-prospect{{background:#1e3a5f;color:#60a5fa;border:1px solid #1e40af;padding:2px 8px;border-radius:4px;font-size:0.65rem}}
.status-applied{{background:#064e3b;color:#4ade80;border:1px solid #065f46;padding:2px 8px;border-radius:4px;font-size:0.65rem}}
.status-interviewing{{background:#422006;color:#fbbf24;border:1px solid #854d0e;padding:2px 8px;border-radius:4px;font-size:0.65rem}}
.status-expired{{background:#450a0a;color:#fca5a5;border:1px solid #991b1b;padding:2px 8px;border-radius:4px;font-size:0.65rem}}
.status-prepared{{background:#3b0764;color:#c084fc;border:1px solid #6b21a8;padding:2px 8px;border-radius:4px;font-size:0.65rem}}

/* Health bar */
.health-bar{{width:60px;height:6px;background:#334155;border-radius:3px;display:inline-block;vertical-align:middle;margin-left:6px}}
.health-fill{{height:100%;border-radius:3px}}

/* Funnel */
.funnel{{display:flex;flex-direction:column;align-items:center;gap:4px;margin:16px 0}}
.funnel-bar{{height:36px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.82rem;color:#fff;transition:width .5s}}

/* No-results */
.no-results{{text-align:center;padding:40px;color:#64748b;font-size:0.9rem}}
</style>
</head>
<body>
<div class="header">
  <h1>🎯 CRM Dashboard</h1>
  <div class="subtitle">Job Search Pipeline &amp; Outreach Tracker</div>
  <div class="updated">Last built: Aug 8, 2026 · {len(jobs):,} jobs · {len(contacts)} contacts</div>
</div>

<!-- Stats Bar -->
<div class="stats">
  <div class="stat-card"><div class="num">{len(jobs):,}</div><div class="label">Total Jobs</div></div>
  <div class="stat-card green"><div class="num">{grade_dist.get('A',0)+grade_dist.get('S',0)}</div><div class="label">A/S Grade</div></div>
  <div class="stat-card purple"><div class="num">{len(company_jobs)}</div><div class="label">Companies</div></div>
  <div class="stat-card orange"><div class="num">{len(persons)}</div><div class="label">People</div></div>
  <div class="stat-card pink"><div class="num">{sum(1 for c in contacts if c.get('email'))}</div><div class="label">With Email</div></div>
  <div class="stat-card teal"><div class="num">{sum(1 for c in contacts if c.get('relationship_strength')=='strong')}</div><div class="label">Strong Ties</div></div>
</div>

<!-- Tabs -->
<div class="tabs">
  <div class="tab active" data-tab="companies">🏢 Companies</div>
  <div class="tab" data-tab="contacts">👤 Contacts</div>
  <div class="tab" data-tab="pipeline">📊 Pipeline</div>
  <div class="tab" data-tab="charts">📈 Charts</div>
</div>

<!-- ============ COMPANIES TAB ============ -->
<div class="tab-content active" id="tab-companies">
  <div class="filter-bar">
    <input type="text" id="company-search" placeholder="Search companies...">
    <select id="company-grade-filter">
      <option value="">All Grades</option>
      <option value="S">S Grade</option>
      <option value="A">A Grade</option>
      <option value="B">B Grade</option>
      <option value="C">C Grade</option>
    </select>
    <select id="company-location-filter">
      <option value="">All Locations</option>
    </select>
    <span class="count" id="company-count"></span>
  </div>
  <table id="company-table">
    <thead>
      <tr>
        <th data-sort="company">Company <span class="arrow">▼</span></th>
        <th data-sort="job_count">Jobs <span class="arrow"></span></th>
        <th>Grade Mix</th>
        <th data-sort="en_pct">EN Friendly <span class="arrow"></span></th>
        <th data-sort="health">Health <span class="arrow"></span></th>
        <th>Top Roles</th>
      </tr>
    </thead>
    <tbody id="company-tbody"></tbody>
  </table>
</div>

<!-- ============ CONTACTS TAB ============ -->
<div class="tab-content" id="tab-contacts">
  <div class="filter-bar">
    <input type="text" id="contact-search" placeholder="Search contacts...">
    <select id="contact-type-filter">
      <option value="">All Types</option>
      <option value="person">👤 People</option>
      <option value="target">🏢 Target Companies</option>
      <option value="ats">📋 ATS/Recruiting</option>
    </select>
    <select id="contact-strength-filter">
      <option value="">All Strength</option>
      <option value="strong">💪 Strong</option>
      <option value="warm">🤝 Warm</option>
      <option value="weak">👤 Weak</option>
    </select>
    <span class="count" id="contact-count"></span>
  </div>
  <table id="contact-table">
    <thead>
      <tr>
        <th data-sort="name">Name <span class="arrow">▼</span></th>
        <th data-sort="company">Company <span class="arrow"></span></th>
        <th data-sort="type">Type <span class="arrow"></span></th>
        <th data-sort="relationship_score">Rel. Score <span class="arrow"></span></th>
        <th>Strength</th>
        <th data-sort="open_roles_count">Open Roles <span class="arrow"></span></th>
        <th data-sort="_outreach_score">Priority <span class="arrow"></span></th>
        <th>Status</th>
        <th>Next Action</th>
      </tr>
    </thead>
    <tbody id="contact-tbody"></tbody>
  </table>
</div>

<!-- ============ PIPELINE TAB ============ -->
<div class="tab-content" id="tab-pipeline">
  <div class="charts-row">
    <div class="chart-box">
      <h3>Funnel Overview</h3>
      <div id="funnel-container"></div>
    </div>
    <div class="chart-box">
      <h3>Pipeline by Stage</h3>
      <canvas id="pipelineChart"></canvas>
    </div>
  </div>
  <div class="filter-bar">
    <input type="text" id="pipeline-search" placeholder="Search pipeline...">
    <select id="pipeline-stage-filter">
      <option value="">All Stages</option>
      <option value="warm">🤝 Warm</option>
      <option value="cold">❄️ Cold</option>
      <option value="active">🔥 Active</option>
      <option value="expired">⏱ Expired</option>
    </select>
    <span class="count" id="pipeline-count"></span>
  </div>
  <div class="pipeline" id="pipeline-container"></div>
</div>

<!-- ============ CHARTS TAB ============ -->
<div class="tab-content" id="tab-charts">
  <div class="charts-row">
    <div class="chart-box">
      <h3>Global Grade Distribution</h3>
      <canvas id="gradeChart"></canvas>
    </div>
    <div class="chart-box">
      <h3>Top 15 Companies by Job Count</h3>
      <canvas id="companyChart"></canvas>
    </div>
  </div>
  <div class="charts-row">
    <div class="chart-box">
      <h3>Grade Distribution by Top Companies</h3>
      <canvas id="stackedChart"></canvas>
    </div>
    <div class="chart-box">
      <h3>Contact Health Distribution</h3>
      <canvas id="healthChart"></canvas>
    </div>
  </div>
</div>

<script>
// ============ DATA ============
const JOBS = {json.dumps(jobs, ensure_ascii=False)};
const CONTACTS = {json.dumps(contacts, ensure_ascii=False)};
const COMPANY_DATA = {json.dumps(company_data, ensure_ascii=False)};

// Grade color mapping
const GRADE_COLORS = {{
  'S': '#c084fc', 'S-1': '#c084fc', 'S+': '#c084fc',
  'A': '#4ade80', 'A-': '#4ade80', 'A+': '#4ade80',
  'A-1': '#34d399', 'A-2': '#6ee7b7',
  'B': '#fbbf24', 'B+': '#fbbf24', 'B-': '#fbbf24', 'B-1': '#fde68a', 'B-2': '#fde68a',
  'C': '#94a3b8', 'Unknown': '#64748b'
}};
function gradeColor(g) {{ return GRADE_COLORS[g] || '#64748b'; }}
function gradeBadge(g) {{
  const cls = g.startsWith('S') ? 'grade-s' : g.startsWith('A') ? 'grade-a' : g.startsWith('B') ? 'grade-b' : g === 'C' ? 'grade-c' : 'grade-other';
  return `<span class="badge ${{cls}}">${{g}}</span>`;
}}

// ============ TABS ============
document.querySelectorAll('.tab').forEach(tab => {{
  tab.addEventListener('click', () => {{
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
  }});
}});

// ============ COMPANIES ============
let companySortKey = 'job_count', companySortDir = -1;

function renderCompanies() {{
  const search = document.getElementById('company-search').value.toLowerCase();
  const gradeFilter = document.getElementById('company-grade-filter').value;
  let data = COMPANY_DATA.filter(c => {{
    if (search && !c.company.toLowerCase().includes(search)) return false;
    if (gradeFilter) {{
      const gc = c.grades;
      const has = Object.keys(gc).some(g => g === gradeFilter || g.startsWith(gradeFilter));
      if (!has) return false;
    }}
    return true;
  }});
  data.sort((a, b) => {{
    let va = a[companySortKey], vb = b[companySortKey];
    if (typeof va === 'string') return companySortDir * va.localeCompare(vb);
    return companySortDir * ((va||0) - (vb||0));
  }});
  document.getElementById('company-count').textContent = `${{data.length}} companies`;
  const tbody = document.getElementById('company-tbody');
  tbody.innerHTML = data.map(c => {{
    const gc = c.grades;
    const total = Object.values(gc).reduce((a,b)=>a+b, 0) || 1;
    // Build mini donut as colored segments
    let pie = '<div style="display:inline-flex;border-radius:50%;overflow:hidden;width:32px;height:32px;vertical-align:middle;margin-right:6px">';
    const sortedGrades = Object.entries(gc).sort((a,b) => b[1]-a[1]);
    for (const [g, cnt] of sortedGrades) {{
      const pct = (cnt/total*100).toFixed(1);
      pie += `<div style="width:${{pct}}%;height:100%;background:${{gradeColor(g)}}"></div>`;
    }}
    pie += '</div>';
    const gradeStr = sortedGrades.map(([g,n]) => `${{g}}: ${{n}}`).join(', ');
    // Health
    const healthScore = c.job_count > 50 ? 80 : c.job_count > 20 ? 60 : c.job_count > 5 ? 40 : 20;
    const hColor = healthScore > 60 ? '#4ade80' : healthScore > 40 ? '#fbbf24' : '#fca5a5';
    // Top jobs
    const topHtml = (c.top_jobs||[]).slice(0,3).map(j => `<div style="font-size:0.72rem;color:#cbd5e1;margin:1px 0">${{gradeBadge(j.grade)}} ${{j.title.substring(0,45)}}${{j.title.length>45?'…':''}}</div>`).join('');
    return `<tr>
      <td><strong>${{c.company}}</strong></td>
      <td style="font-weight:700;color:#38bdf8">${{c.job_count}}</td>
      <td><div style="display:flex;align-items:center">${{pie}}<span style="font-size:0.68rem;color:#94a3b8">${{gradeStr}}</span></div></td>
      <td>${{c.en_pct}}%</td>
      <td><div class="health-bar"><div class="health-fill" style="width:${{healthScore}}%;background:${{hColor}}"></div></div></td>
      <td>${{topHtml}}</td>
    </tr>`;
  }}).join('');
}}

document.getElementById('company-search').addEventListener('input', renderCompanies);
document.getElementById('company-grade-filter').addEventListener('change', renderCompanies);
document.querySelectorAll('#company-table th[data-sort]').forEach(th => {{
  th.addEventListener('click', () => {{
    const key = th.dataset.sort;
    if (companySortKey === key) companySortDir *= -1;
    else {{ companySortKey = key; companySortDir = -1; }}
    document.querySelectorAll('#company-table th .arrow').forEach(a => a.textContent = '');
    th.querySelector('.arrow').textContent = companySortDir > 0 ? '▲' : '▼';
    renderCompanies();
  }});
}});

// ============ CONTACTS ============
let contactSortKey = '_outreach_score', contactSortDir = -1;

function renderContacts() {{
  const search = document.getElementById('contact-search').value.toLowerCase();
  const typeFilter = document.getElementById('contact-type-filter').value;
  const strengthFilter = document.getElementById('contact-strength-filter').value;
  let data = CONTACTS.filter(c => {{
    if (search) {{
      const hay = `${{c.name}} ${{c.company}} ${{c.title||''}} ${{c.email||''}}`.toLowerCase();
      if (!hay.includes(search)) return false;
    }}
    if (typeFilter && c.category !== typeFilter) return false;
    if (strengthFilter && c.relationship_strength !== strengthFilter) return false;
    return true;
  }});
  data.sort((a, b) => {{
    let va = a[contactSortKey], vb = b[contactSortKey];
    if (typeof va === 'string') return contactSortDir * (va||'').localeCompare(vb||'');
    return contactSortDir * ((va||0) - (vb||0));
  }});
  document.getElementById('contact-count').textContent = `${{data.length}} contacts`;
  const tbody = document.getElementById('contact-tbody');
  tbody.innerHTML = data.map(c => {{
    const typeEmoji = c.category === 'person' ? '👤' : c.category === 'target' ? '🏢' : '📋';
    const typeName = c.category === 'person' ? 'Person' : c.category === 'target' ? 'Target' : 'ATS';
    const strCls = `strength-${{c.relationship_strength||'weak'}}`;
    const strEmoji = c.relationship_strength === 'strong' ? '💪' : c.relationship_strength === 'warm' ? '🤝' : '👤';
    const scoreVal = c._outreach_score || 0;
    const scoreCls = scoreVal >= 50 ? 'score-high' : scoreVal >= 25 ? 'score-med' : 'score-low';
    const statusCls = `status-${{c.application_status||'prospect'}}`;
    const roles = c.open_roles_count || 0;
    const sGradeRoles = (c.matching_a_s_jobs || []).length;
    const sGradeBadge = sGradeRoles > 0 ? `<span style="color:#4ade80;font-size:0.65rem;margin-left:4px">★${{sGradeRoles}} A/S</span>` : '';
    return `<tr>
      <td><strong>${{c.name}}</strong>${{c.email ? `<br><span style="font-size:0.68rem;color:#64748b">${{c.email}}</span>` : ''}}</td>
      <td>${{c.company}}</td>
      <td>${{typeEmoji}} ${{typeName}}</td>
      <td style="font-weight:700">${{c.relationship_score||0}}</td>
      <td class="${{strCls}}">${{strEmoji}} ${{c.relationship_strength||'weak'}}</td>
      <td>${{roles}}${{sGradeBadge}}</td>
      <td><span class="score ${{scoreCls}}">${{scoreVal}}</span></td>
      <td><span class="${{statusCls}}">${{c.application_status||'prospect'}}</span></td>
      <td style="font-size:0.72rem;color:#94a3b8">${{c.next_action||'—'}}</td>
    </tr>`;
  }}).join('');
}}

document.getElementById('contact-search').addEventListener('input', renderContacts);
document.getElementById('contact-type-filter').addEventListener('change', renderContacts);
document.getElementById('contact-strength-filter').addEventListener('change', renderContacts);
document.querySelectorAll('#contact-table th[data-sort]').forEach(th => {{
  th.addEventListener('click', () => {{
    const key = th.dataset.sort;
    if (contactSortKey === key) contactSortDir *= -1;
    else {{ contactSortKey = key; contactSortDir = -1; }}
    document.querySelectorAll('#contact-table th .arrow').forEach(a => a.textContent = '');
    th.querySelector('.arrow').textContent = contactSortDir > 0 ? '▲' : '▼';
    renderContacts();
  }});
}});

// ============ PIPELINE ============
const PIPELINE_STAGES = [
  {{ id: 'warm', label: '🤝 Warm', color: '#fbbf24' }},
  {{ id: 'cold', label: '❄️ Cold', color: '#60a5fa' }},
  {{ id: 'active', label: '🔥 Active', color: '#4ade80' }},
  {{ id: 'expired', label: '⏱ Expired', color: '#f87171' }}
];

function renderPipeline() {{
  const search = document.getElementById('pipeline-search').value.toLowerCase();
  const stageFilter = document.getElementById('pipeline-stage-filter').value;
  const container = document.getElementById('pipeline-container');
  const funnelContainer = document.getElementById('funnel-container');
  
  let filtered = CONTACTS.filter(c => {{
    if (search) {{
      const hay = `${{c.name}} ${{c.company}}`.toLowerCase();
      if (!hay.includes(search)) return false;
    }}
    return true;
  }});
  
  const stageGroups = {{}};
  PIPELINE_STAGES.forEach(s => stageGroups[s.id] = []);
  filtered.forEach(c => {{
    const stage = c._pipeline_stage || 'cold';
    if (stageGroups[stage]) stageGroups[stage].push(c);
  }});
  
  const maxCount = Math.max(...PIPELINE_STAGES.map(s => stageGroups[s.id].length), 1);
  
  // Funnel
  let funnelHtml = '';
  PIPELINE_STAGES.forEach(s => {{
    const count = stageGroups[s.id].length;
    const width = Math.max(10, (count / maxCount) * 100);
    funnelHtml += `<div class="funnel-bar" style="width:${{width}}%;background:${{s.color}}">${{s.label}} (${{count}})</div>`;
  }});
  funnelContainer.innerHTML = `<div class="funnel">${{funnelHtml}}</div>`;
  
  // Pipeline cards
  let html = '';
  PIPELINE_STAGES.forEach(s => {{
    const contacts = stageGroups[s.id].sort((a,b) => (b._outreach_score||0) - (a._outreach_score||0));
    if (stageFilter && s.id !== stageFilter) return;
    html += `<div class="pipeline-stage">
      <div class="stage-header" style="color:${{s.color}}">${{s.label}} <span class="stage-count">${{contacts.length}}</span></div>`;
    contacts.slice(0,15).forEach(c => {{
      const scoreVal = c._outreach_score || 0;
      const scoreCls = scoreVal >= 50 ? 'score-high' : scoreVal >= 25 ? 'score-med' : 'score-low';
      const roles = c.open_roles_count || 0;
      const hasAJobs = (c.matching_a_s_jobs && c.matching_a_s_jobs.length > 0) || (c.top_jobs_from_database || []).some(j => (j.grade||'').startsWith('A'));
      const flag = hasAJobs ? '<span style="color:#4ade80;font-size:0.65rem">★ A/S roles</span>' : '';
      html += `<div class="pipeline-card">
        <div class="name">${{c.name}} ${{flag}}</div>
        <div class="company">${{c.company}} · ${{c.title||c.role_type||''}}</div>
        <div class="meta">
          <span class="score ${{scoreCls}}">P:${{scoreVal}}</span>
          <span style="font-size:0.65rem;color:#94a3b8">${{roles}} roles</span>
        </div>
      </div>`;
    }});
    if (contacts.length > 15) html += `<div style="text-align:center;color:#64748b;font-size:0.7rem">+${{contacts.length-15}} more</div>`;
    html += `</div>`;
  }});
  container.innerHTML = html;
  document.getElementById('pipeline-count').textContent = `${{filtered.length}} contacts`;
}}

document.getElementById('pipeline-search').addEventListener('input', renderPipeline);
document.getElementById('pipeline-stage-filter').addEventListener('change', renderPipeline);

// ============ CHARTS ============
function initCharts() {{
  // Grade distribution pie
  const gradeLabels = {json.dumps(list(grade_dist.keys()))};
  const gradeValues = {json.dumps(list(grade_dist.values()))};
  const gradeColorsArr = gradeLabels.map(g => gradeColor(g));
  
  new Chart(document.getElementById('gradeChart'), {{
    type: 'doughnut',
    data: {{
      labels: gradeLabels,
      datasets: [{{ data: gradeValues, backgroundColor: gradeColorsArr, borderWidth: 0 }}]
    }},
    options: {{
      responsive: true,
      plugins: {{
        legend: {{ position: 'right', labels: {{ color: '#94a3b8', font: {{ size: 11 }} }} }}
      }}
    }}
  }});
  
  // Top companies bar
  const top15 = COMPANY_DATA.slice(0, 15);
  new Chart(document.getElementById('companyChart'), {{
    type: 'bar',
    data: {{
      labels: top15.map(c => c.company),
      datasets: [{{
        label: 'Jobs',
        data: top15.map(c => c.job_count),
        backgroundColor: '#38bdf8',
        borderRadius: 4
      }}]
    }},
    options: {{
      responsive: true,
      indexAxis: 'y',
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#1e293b' }} }},
        y: {{ ticks: {{ color: '#e2e8f0', font: {{ size: 10 }} }}, grid: {{ display: false }} }}
      }}
    }}
  }});
  
  // Stacked grade by company
  const stackCompanies = COMPANY_DATA.slice(0, 10).map(c => c.company);
  const stackGrades = ['A', 'A-1', 'A-2', 'A-', 'B', 'B+', 'C', 'S'];
  const stackDatasets = stackGrades.map(g => ({{
    label: g,
    data: COMPANY_DATA.slice(0, 10).map(c => c.grades[g] || 0),
    backgroundColor: gradeColor(g),
    borderRadius: 2
  }}));
  new Chart(document.getElementById('stackedChart'), {{
    type: 'bar',
    data: {{ labels: stackCompanies, datasets: stackDatasets }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ labels: {{ color: '#94a3b8', font: {{ size: 9 }} }} }} }},
      scales: {{
        x: {{ stacked: true, ticks: {{ color: '#94a3b8', font: {{ size: 9 }} }}, grid: {{ display: false }} }},
        y: {{ stacked: true, ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#1e293b' }} }}
      }}
    }}
  }});
  
  // Health distribution
  const healthBuckets = {{ 'Strong (70+)': 0, 'Medium (40-69)': 0, 'Weak (<40)': 0 }};
  CONTACTS.forEach(c => {{
    const h = c._health_score || 0;
    if (h >= 70) healthBuckets['Strong (70+)']++;
    else if (h >= 40) healthBuckets['Medium (40-69)']++;
    else healthBuckets['Weak (<40)']++;
  }});
  new Chart(document.getElementById('healthChart'), {{
    type: 'doughnut',
    data: {{
      labels: Object.keys(healthBuckets),
      datasets: [{{ data: Object.values(healthBuckets), backgroundColor: ['#4ade80', '#fbbf24', '#f87171'], borderWidth: 0 }}]
    }},
    options: {{
      responsive: true,
      plugins: {{
        legend: {{ position: 'right', labels: {{ color: '#94a3b8', font: {{ size: 11 }} }} }}
      }}
    }}
  }});
  
  // Pipeline chart
  const pipelineData = PIPELINE_STAGES.map(s => CONTACTS.filter(c => c._pipeline_stage === s.id).length);
  new Chart(document.getElementById('pipelineChart'), {{
    type: 'bar',
    data: {{
      labels: PIPELINE_STAGES.map(s => s.label),
      datasets: [{{ data: pipelineData, backgroundColor: PIPELINE_STAGES.map(s => s.color), borderRadius: 4 }}]
    }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ display: false }} }},
        y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#1e293b' }} }}
      }}
    }}
  }});
}}

// ============ INIT ============
renderCompanies();
renderContacts();
renderPipeline();
initCharts();
</script>
</body>
</html>"""

    out_path = os.path.join(DIR, "crm-dashboard.html")
    with open(out_path, "w") as f:
        f.write(html)
    print(f"✅ Dashboard written to {out_path}")
    print(f"   Jobs: {len(jobs):,} | Companies: {len(company_jobs)} | Contacts: {len(contacts)}")

if __name__ == "__main__":
    main()
