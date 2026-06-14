#!/usr/bin/env python3
"""Generate job-database-senior.html from jobs-all.json — dark-theme, filterable, sortable dashboard."""
import json
import os
import html as html_mod
from datetime import datetime

DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DIR, "jobs-all.json")
OUT_FILE = os.path.join(DIR, "job-database-senior.html")


def load_jobs():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_html(jobs):
    # Gather dynamic filter options
    grades = sorted(set(j.get("grade", "") for j in jobs if j.get("grade")))
    locations = sorted(set(j.get("location", "") for j in jobs if j.get("location")))
    role_types = sorted(set(j.get("role_type", "") for j in jobs if j.get("role_type")))
    categories = sorted(set(j.get("category", "") for j in jobs if j.get("category")))
    statuses = sorted(set(j.get("status", "not_applied") for j in jobs))

    grade_opts = "".join(f'<option value="{html_mod.escape(g)}">{html_mod.escape(g)}</option>' for g in grades)
    city_opts = "".join(f'<option value="{html_mod.escape(c)}">{html_mod.escape(c)}</option>' for c in locations)
    role_opts = "".join(f'<option value="{html_mod.escape(r)}">{html_mod.escape(r)}</option>' for r in role_types)
    cat_opts = "".join(f'<option value="{html_mod.escape(c)}">{html_mod.escape(c)}</option>' for c in categories)
    status_opts = "".join(f'<option value="{html_mod.escape(s)}">{html_mod.escape(s)}</option>' for s in statuses)

    # Build stat cards dynamically
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

    stat_cards = [
        ('totalCount', str(len(jobs)), 'Total Roles', '', '#38bdf8'),
        ('a1Count', str(grade_counts.get('A-1', 0)), 'A-1 Perfect', 'a1', '#4ade80'),
        ('a2Count', str(grade_counts.get('A-2', 0)), 'A-2 Strong', '', '#60a5fa'),
        ('engCount', str(eng_count), 'English Friendly', '', '#fbbf24'),
    ]
    # Add top cities
    city_colors = {
        'Singapore': ('sgCount', '#f472b6'),
        'Shanghai': ('shCount', '#fb923c'),
        'Hong Kong': ('hkCount', '#a78bfa'),
        'Shenzhen': ('szCount', '#2dd4bf'),
    }
    for city, (cid, color) in city_colors.items():
        if city in city_counts:
            stat_cards.append((cid, str(city_counts[city]), city, '', color))

    # Add top categories
    cat_colors = {
        'ai_product': ('aiCount', '#c084fc'),
        'cross_border': ('cbCount', '#86efac'),
        'strategy': ('stratCount', '#fca5a5'),
    }
    for cat, (cid, color) in cat_colors.items():
        if cat in cat_counts:
            label = cat.replace('_', ' ').title()
            stat_cards.append((cid, str(cat_counts[cat]), label, '', color))

    cards_html = ""
    for elem_id, num, label, extra_cls, _ in stat_cards:
        cls = f"stat-card {extra_cls}" if extra_cls else "stat-card"
        cards_html += f'<div class="{cls}"><div class="num" id="{elem_id}">{num}</div><div class="label">{label}</div></div>\n'

    # Serialize jobs as JS
    jobs_json = json.dumps(jobs, ensure_ascii=False)

    now = datetime.now().strftime("%A, %B %d, %Y — %I:%M %p")

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
.stat-card.sg .num{{color:#f472b6}}
.stat-card.sh .num{{color:#fb923c}}
.stat-card.hk .num{{color:#a78bfa}}
.stat-card.sz .num{{color:#2dd4bf}}
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
.role-tag{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.65rem}}
.role-pm{{background:#164e63;color:#67e8f9}}
.role-strat{{background:#2d1b69;color:#c4b5fd}}
.role-cross{{background:#1a3a2a;color:#86efac}}
.role-bd{{background:#4a1d1d;color:#fca5a5}}
.role-gm{{background:#3d2e0b;color:#fde68a}}
.cat-tag{{display:inline-block;padding:2px 6px;border-radius:4px;font-size:0.6rem;margin-left:4px}}
.cat-ai{{background:#3b0764;color:#c084fc}}
.cat-cross{{background:#14532d;color:#86efac}}
.cat-strat{{background:#450a0a;color:#fca5a5}}
.cat-growth{{background:#422006;color:#fbbf24}}
.cat-platform{{background:#1e3a5f;color:#93c5fd}}
.cat-general{{background:#334155;color:#cbd5e1}}
.en-title{{color:#94a3b8;font-size:0.75rem;font-style:italic}}
.diff-easy{{background:#064e3b;color:#4ade80;border:1px solid #065f46;padding:2px 6px;border-radius:4px;font-size:0.6rem}}
.diff-medium{{background:#422006;color:#fbbf24;border:1px solid #854d0e;padding:2px 6px;border-radius:4px;font-size:0.6rem}}
.diff-hard{{background:#450a0a;color:#fca5a5;border:1px solid #991b1b;padding:2px 6px;border-radius:4px;font-size:0.6rem}}
.tier-a{{color:#4ade80;font-weight:700}}
.tier-b{{color:#60a5fa}}
.tier-c{{color:#fbbf24}}
.tier-d{{color:#f87171}}
.url-quality{{margin:12px 0;padding:10px 16px;background:#1e293b;border-radius:8px;border:1px solid #334155;font-size:0.8rem;color:#94a3b8}}
.url-quality .good{{color:#4ade80}}
.url-quality .bad{{color:#f87171}}
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
  <div class="subtitle">Generated: {now}</div>
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
  <th onclick="sortTable(4)" class="hide-mobile">Category <span class="arrow"></span></th>
  <th onclick="sortTable(5)" class="hide-mobile">Apply <span class="arrow"></span></th>
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
    const diffClass = j.app_difficulty === 'easy' ? 'diff-easy' : j.app_difficulty === 'medium' ? 'diff-medium' : 'diff-hard';
    const diffLabel = j.app_difficulty === 'easy' ? '⚡ Quick' : j.app_difficulty === 'medium' ? '📋 Medium' : '⏳ Hard';
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
      <td><span class="city-tag">${{j.location}}</span></td>
      <td class="hide-mobile"><span class="cat-tag ${{cc}}">${{catLabel}}</span></td>
      <td class="hide-mobile"><span class="${{diffClass}}">${{diffLabel}}</span></td>
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
    if (c && j.location !== c) return false;
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
  const keys = ['grade','title','company','location','category','salary'];
  const order = {{'S-1':-1,'A-1':0,'A-2':1,'B':2,'C':3}};
  jobs.sort((a,b) => {{
    let va = a[keys[col]] || '', vb = b[keys[col]] || '';
    if (col === 0) {{ va = order[va]||9; vb = order[vb]||9; }}
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


def main():
    jobs = load_jobs()
    html_content = build_html(jobs)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Dashboard generated: {OUT_FILE}")
    print(f"  Total jobs: {len(jobs)}")
    grades = {}
    cats = {}
    eng = 0
    for j in jobs:
        g = j.get("grade", "?")
        c = j.get("category", "?")
        grades[g] = grades.get(g, 0) + 1
        cats[c] = cats.get(c, 0) + 1
        if j.get("english_friendly"):
            eng += 1
    for g in sorted(grades):
        print(f"  {g}: {grades[g]}")
    print(f"  English friendly: {eng}")
    print("  Categories:")
    for c in sorted(cats, key=lambda x: cats[x], reverse=True):
        print(f"    {c}: {cats[c]}")


if __name__ == "__main__":
    main()
