#!/usr/bin/env python3
"""Build CRM Dashboard from jobs + applications + contacts data."""
import json
import os
from datetime import datetime, timedelta

DIR = os.path.dirname(os.path.abspath(__file__))

def load(fn):
    p = os.path.join(DIR, fn)
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return None

def build_crm():
    jobs = load("jobs-all.json") or []
    apps = load("applications-tracker.json") or {}
    contacts = load("contacts.json") or {"contacts": []}
    
    applications = apps.get("applications", [])
    contact_list = contacts.get("contacts", [])
    
    # Build company index from jobs
    companies = {}
    for j in jobs:
        co = j.get("company", "Unknown")
        if co not in companies:
            companies[co] = {"jobs": [], "contact": None, "applications": []}
        companies[co]["jobs"].append(j)
    
    # Link applications to companies
    for a in applications:
        co = a.get("company", "")
        if co in companies:
            companies[co]["applications"].append(a)
    
    # Link contacts to companies
    contact_map = {}
    for c in contact_list:
        co = c.get("company", "")
        if co not in contact_map:
            contact_map[co] = []
        contact_map[co].append(c)
    
    # Stats
    total_companies = len(companies)
    total_apps = len(applications)
    total_contacts = len(contact_list)
    companies_with_apps = sum(1 for c in companies.values() if c["applications"])
    companies_with_contacts = len(set(c.get("company","") for c in contact_list))
    
    # Pipeline stages
    statuses = {}
    for a in applications:
        s = a.get("status", "not_started")
        # Map 'prepared' to 'not_applied' (cover letter ready, not yet sent)
        if s == "prepared":
            s = "not_applied"
        statuses[s] = statuses.get(s, 0) + 1
    
    # Grade distribution
    grades = {}
    for j in jobs:
        g = j.get("grade", "?")
        grades[g] = grades.get(g, 0) + 1
    
    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CRM Dashboard — Career OS</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:#0a0a0f;--card:#12121a;--border:#1e1e2e;--text:#e0e0e0;--dim:#666;--accent:#6c5ce7;--green:#00b894;--yellow:#fdcb6e;--red:#e17055;--blue:#74b9ff}}
body{{--background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:20px;background:#0a0a0f}}
h1{{font-size:28px;margin-bottom:4px;color:var(--text)}}
.subtitle{{color:var(--dim);margin-bottom:24px;font-size:14px}}
.stats-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:24px}}
.stat-card{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;text-align:center}}
.stat-num{{font-size:32px;font-weight:700;color:var(--accent)}}
.stat-label{{font-size:12px;color:var(--dim);margin-top:4px;text-transform:uppercase;letter-spacing:0.5px}}
.pipeline{{display:flex;gap:8px;margin-bottom:24px;flex-wrap:wrap}}
.pipe-stage{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px 16px;text-align:center;min-width:100px;flex:1}}
.pipe-count{{font-size:24px;font-weight:700}}
.pipe-label{{font-size:11px;color:var(--dim);margin-top:2px}}
.search-box{{width:100%;padding:12px 16px;background:var(--card);border:1px solid var(--border);border-radius:8px;color:var(--text);font-size:14px;margin-bottom:20px;outline:none}}
.search-box:focus{{border-color:var(--accent)}}
.company-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}}
.company-card{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;transition:border-color 0.2s}}
.company-card:hover{{border-color:var(--accent)}}
.company-name{{font-size:18px;font-weight:600;margin-bottom:4px;color:var(--text)}}
.company-meta{{font-size:12px;color:var(--dim);margin-bottom:8px}}
.grade-badges{{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:8px}}
.badge{{padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600}}
.badge-S{{background:rgba(253,203,110,0.2);color:#fdcb6e}}
.badge-A{{background:rgba(0,184,148,0.2);color:#00b894}}
.badge-B{{background:rgba(116,185,255,0.2);color:#74b9ff}}
.badge-C{{background:rgba(99,110,114,0.2);color:#636e72}}
.job-list{{max-height:200px;overflow-y:auto}}
.job-item{{padding:6px 0;border-bottom:1px solid var(--border);font-size:13px;display:flex;justify-content:space-between;align-items:center;color:var(--text)}}
.job-item:last-child{{border-bottom:none}}
.job-title{{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.job-status{{font-size:11px;padding:2px 8px;border-radius:4px;margin-left:8px;white-space:nowrap}}
.status-not_started{{background:rgba(99,110,114,0.2);color:#636e72}}
.status-not_applied{{background:rgba(253,203,110,0.2);color:#fdcb6e}}
.status-applied{{background:rgba(116,185,255,0.2);color:#74b9ff}}
.status-interviewing{{background:rgba(108,92,231,0.2);color:#a29bfe}}
.status-offer{{background:rgba(0,184,148,0.2);color:#00b894}}
.status-rejected{{background:rgba(225,112,85,0.2);color:#e17055}}
.filters{{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}}
.filter-btn{{padding:6px 14px;border-radius:6px;border:1px solid var(--border);background:var(--card);color:var(--text);cursor:pointer;font-size:12px;transition:all 0.2s}}
.filter-btn:hover,.filter-btn.active{{background:var(--accent);border-color:var(--accent);color:#fff}}
.section-title{{font-size:16px;font-weight:600;margin:20px 0 12px;color:var(--dim)}}
.contact-badge{{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:4px;font-size:11px;background:rgba(108,92,231,0.15);color:#a29bfe;margin-left:8px}}
.grade-bar{{display:flex;height:6px;border-radius:3px;overflow:hidden;margin:8px 0}}
.grade-bar div{{height:100%}}
</style>
</head>
<body>
<h1>🎯 CRM Dashboard</h1>
<p class="subtitle">Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} · {total_companies} companies · {total_apps} applications · {total_contacts} contacts</p>

<div class="stats-row">
  <div class="stat-card"><div class="stat-num">{total_companies}</div><div class="stat-label">Companies</div></div>
  <div class="stat-card"><div class="stat-num">{total_apps}</div><div class="stat-label">Applications</div></div>
  <div class="stat-card"><div class="stat-num">{companies_with_apps}</div><div class="stat-label">Applied</div></div>
  <div class="stat-card"><div class="stat-num">{total_contacts}</div><div class="stat-label">Contacts</div></div>
  <div class="stat-card"><div class="stat-num">{companies_with_contacts}</div><div class="stat-label">Contacted</div></div>
  <div class="stat-card"><div class="stat-num">{statuses.get('interviewing',0)}</div><div class="stat-label">Interviews</div></div>
  <div class="stat-card"><div class="stat-num">{statuses.get('offer',0)}</div><div class="stat-label">Offers</div></div>
</div>

<div class="pipeline">
"""
    
    # Pipeline stages
    stage_colors = {
        "not_started": ("#636e72", "📋"),
        "not_applied": ("#fdcb6e", "📝"),
        "prepared": ("#fdcb6e", "📝"),
        "applied": ("#74b9ff", "📤"),
        "interviewing": ("#a29bfe", "🎤"),
        "offer": ("#00b894", "🎉"),
        "rejected": ("#e17055", "❌"),
    }
    for stage in ["not_started", "not_applied", "applied", "interviewing", "offer", "rejected"]:
        count = statuses.get(stage, 0)
        color, icon = stage_colors.get(stage, ("#666", "•"))
        html += f'<div class="pipe-stage"><div class="pipe-count" style="color:{color}">{icon} {count}</div><div class="pipe-label">{stage.replace("_"," ").title()}</div></div>\n'
    
    html += """</div>

<input type="text" class="search-box" id="searchBox" placeholder="🔍 Search companies, roles, grades..." oninput="filterCompanies()">

<div class="filters">
  <button class="filter-btn active" onclick="setFilter('all',this)">All</button>
  <button class="filter-btn" onclick="setFilter('applied',this)">Applied</button>
  <button class="filter-btn" onclick="setFilter('not_applied',this)">Not Applied</button>
  <button class="filter-btn" onclick="setFilter('contacted',this)">Contacted</button>
  <button class="filter-btn" onclick="setFilter('interviewing',this)">Interviewing</button>
</div>

<div class="company-grid">
"""
    
    # Company cards — sorted by grade then by application status
    grade_order = {"S": 0, "A": 1, "A-1": 1, "A-2": 1, "A-3": 1, "B": 2, "B-1": 2, "B-2": 2, "B-3": 2, "C": 3}
    
    sorted_companies = sorted(companies.items(), key=lambda x: (
        min(grade_order.get(j.get("grade","?"), 4) for j in x[1]["jobs"]),
        -len(x[1]["applications"]),
        x[0]
    ))
    
    for co_name, data in sorted_companies:
        co_jobs = data["jobs"]
        co_apps = data["applications"]
        co_contacts = contact_map.get(co_name, [])
        
        # Grades for this company
        co_grades = list(set(j.get("grade","?") or "?" for j in co_jobs))
        best_grade = min(co_grades, key=lambda g: grade_order.get(g, 4))
        grade_badges = "".join(f'<span class="badge badge-{(g[0] if g and g[0] in "SABC" else "C")}">{g}</span>' for g in sorted(set(co_grades), key=lambda g: grade_order.get(g, 4)))
        
        # Application status
        app_status = ""
        if co_apps:
            latest = co_apps[-1].get("status", "not_started")
            app_status = f'<span class="job-status status-{latest}">{latest.replace("_"," ").title()}</span>'
        
        # Contact info
        contact_html = ""
        if co_contacts:
            c = co_contacts[0]
            name = c.get("name", "?")
            contact_html = f'<span class="contact-badge">👤 {name}</span>'
        
        # Grade bar
        grade_counts = {}
        for j in co_jobs:
            g = (j.get("grade", "?") or "?")[0]  # S, A, B, C
            grade_counts[g] = grade_counts.get(g, 0) + 1
        total = len(co_jobs)
        bar_colors = {"S": "#fdcb6e", "A": "#00b894", "B": "#74b9ff", "C": "#636e72"}
        bar_html = '<div class="grade-bar">'
        for g in ["S", "A", "B", "C"]:
            if g in grade_counts:
                pct = grade_counts[g] / total * 100
                bar_html += f'<div style="width:{pct}%;background:{bar_colors.get(g,"#666")}"></div>'
        bar_html += '</div>'
        
        html += f'''<div class="company-card" data-company="{co_name}" data-grades="{" ".join(co_grades)}" data-applied="{"yes" if co_apps else "no"}" data-contacted="{"yes" if co_contacts else "no"}">
  <div class="company-name">{co_name} {contact_html}</div>
  <div class="company-meta">{len(co_jobs)} roles · {len(co_apps)} applied · {len(co_contacts)} contacts</div>
  <div class="grade-badges">{grade_badges}</div>
  {bar_html}
  <div class="job-list">
'''
        for j in co_jobs:
            title = j.get("title", "?")[:60]
            link = j.get("url", "#")
            grade = j.get("grade", "?") or "?"
            gc = grade[0] if grade and grade[0] in "SABC" else "C"
            html += f'    <div class="job-item"><a href="{link}" target="_blank" class="job-title">{title}</a><span class="badge badge-{gc}">{grade}</span></div>\n'
        
        html += '  </div>\n</div>\n'
    
    html += """</div>

<script>
function filterCompanies() {
  const q = document.getElementById('searchBox').value.toLowerCase();
  document.querySelectorAll('.company-card').forEach(c => {
    const name = c.dataset.company.toLowerCase();
    const grades = c.dataset.grades.toLowerCase();
    const match = name.includes(q) || grades.includes(q) || c.textContent.toLowerCase().includes(q);
    c.style.display = match ? '' : 'none';
  });
}
let currentFilter = 'all';
function setFilter(f, btn) {
  currentFilter = f;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.company-card').forEach(c => {
    if (f === 'all') { c.style.display = ''; return; }
    if (f === 'applied' && c.dataset.applied === 'yes') { c.style.display = ''; return; }
    if (f === 'not_applied' && c.dataset.applied === 'no') { c.style.display = ''; return; }
    if (f === 'contacted' && c.dataset.contacted === 'yes') { c.style.display = ''; return; }
    if (f === 'interviewing') {
      const hasInterview = c.querySelector('.status-interviewing');
      c.style.display = hasInterview ? '' : 'none';
      return;
    }
    c.style.display = 'none';
  });
}
</script>
</body>
</html>"""
    
    return html


if __name__ == "__main__":
    html = build_crm()
    out = os.path.join(DIR, "crm-dashboard.html")
    with open(out, "w") as f:
        f.write(html)
    print(f"✅ CRM dashboard written to {out} ({len(html)} bytes)")
