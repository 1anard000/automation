#!/usr/bin/env python3
"""Rebuild apply-today.html from the latest recommendations JSON.

Auto-finds the most recent recommendations file in job_recommender/daily_reports/.
If run with an argument, uses that specific file instead.

Usage:
    python3 rebuild_apply_today.py                    # auto-find latest
    python3 rebuild_apply_today.py recommendations-2026-06-18.json  # explicit file
"""
import json, os, sys, glob
from datetime import datetime

# Find recommendations file
rec_dir = "job_recommender/daily_reports"
if len(sys.argv) > 1:
    rec_file = os.path.join(rec_dir, sys.argv[1]) if not os.path.isabs(sys.argv[1]) else sys.argv[1]
else:
    pattern = os.path.join(rec_dir, "recommendations-*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        print("ERROR: No recommendations files found in", rec_dir)
        sys.exit(1)
    rec_file = files[-1]  # latest by filename (date-sorted)

print(f"Reading: {rec_file}")
with open(rec_file) as f:
    recs = json.load(f)

# Extract date from filename or use today
basename = os.path.basename(rec_file)
if "recommendations-" in basename:
    date_str = basename.replace("recommendations-", "").replace(".json", "")
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        date_display = dt.strftime("%A, %B %d").replace(" 0", " ")
    except ValueError:
        dt = datetime.now()
        date_display = datetime.now().strftime("%A, %B %d").replace(" 0", " ")
else:
    dt = datetime.now()
    date_display = datetime.now().strftime("%A, %B %d").replace(" 0", " ")

weekday = dt.strftime("%A")

# Sort by quality_score descending
recs.sort(key=lambda j: j.get("quality_score", 0), reverse=True)

# Take top 20
recs = recs[:20]

jobs_html = ''
for i, job in enumerate(recs, 1):
    title = job.get('title', 'Unknown')
    company = job.get('company_raw', job.get('company', 'Unknown'))
    location = job.get('location', 'TBD')
    score = job.get('quality_score', 0)
    url = job.get('url', '#')
    tier = job.get('quality_tier', 'B')
    tier_class = 'fast' if tier == 'A' else 'med'
    notes = job.get('notes', '')
    tags = job.get('tags', [])
    english = job.get('english_friendly', False)

    # Extract country code from location
    loc_code = 'XX'
    if location:
        for code in ['SG', 'HK', 'CN', 'US', 'JP', 'KR', 'TW', 'MY', 'TH', 'ID', 'PH', 'AU', 'NZ', 'UK', 'DE']:
            if code in location.upper():
                loc_code = code
                break
        if loc_code == 'XX' and len(location) >= 2:
            loc_code = location[:2].upper()

    tag_badges = ''
    if english:
        tag_badges += ' <span class="speed fast">English OK</span>'

    jobs_html += '<div class="job">\n'
    jobs_html += '<div class="row">\n'
    jobs_html += '  <span class="rank">#' + str(i) + '</span>\n'
    jobs_html += '  <div class="info">\n'
    jobs_html += '    <div class="company">' + company + '</div>\n'
    jobs_html += '    <div class="title">' + title + '</div>\n'
    jobs_html += '    <div class="loc">📍 ' + location + ' | Score: ' + str(score) + '</div>\n'
    jobs_html += '  </div>\n'
    jobs_html += '</div>\n'
    jobs_html += '<span class="speed fast">' + loc_code + '</span> <span class="speed ' + tier_class + '">' + tier + '</span>' + tag_badges + '\n'
    if url and url != '#':
        jobs_html += '<a class="btn" href="' + url + '" target="_blank" rel="noopener">Apply →</a>\n'
    if notes:
        jobs_html += '<div class="note">' + notes[:200] + '</div>\n'
    jobs_html += '</div>\n\n'

html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Apply Today — ''' + date_display + '''</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;padding:16px;max-width:700px;margin:0 auto}
h1{font-size:1.4rem;text-align:center;padding:16px 0;color:#4ade80}
.sub{text-align:center;color:#94a3b8;font-size:0.85rem;margin-bottom:20px}
.speed{font-size:0.7rem;padding:2px 8px;border-radius:4px;font-weight:700;text-transform:uppercase}
.fast{background:#064e3b;color:#4ade80}
.med{background:#422006;color:#fbbf24}
.slow{background:#450a0a;color:#fca5a5}
.job{background:#1e293b;border-radius:10px;padding:14px;margin-bottom:10px;border:1px solid #334155}
.job:hover{border-color:#4ade80}
.row{display:flex;align-items:center;gap:10px;margin-bottom:6px}
.rank{font-size:1.3rem;font-weight:700;color:#38bdf8;min-width:24px}
.info{flex:1}
.company{font-weight:600;font-size:0.95rem}
.title{color:#94a3b8;font-size:0.8rem}
.loc{color:#94a3b8;font-size:0.75rem}
.btn{display:block;text-align:center;padding:10px;background:#38bdf8;color:#0f172a;border-radius:8px;text-decoration:none;font-weight:600;font-size:0.85rem;margin-top:8px}
.btn:hover{background:#7dd3fc}
.note{color:#64748b;font-size:0.7rem;margin-top:4px}
.footer{text-align:center;color:#64748b;font-size:0.7rem;margin-top:24px;padding:16px 0;border-top:1px solid #334155}
</style>
</head>
<body>
<h1>🎯 Apply Today — ''' + weekday + ''', ''' + date_display.split(", ")[-1] + '''</h1>
<p class="sub">Top ''' + str(len(recs)) + ''' recommended roles for today</p>

''' + jobs_html + '''
<div class="footer">
  Generated by Career OS • ''' + datetime.now().strftime('%Y-%m-%d %H:%M') + ''' HKT<br>
  🟢 Green = Easy Apply &nbsp; 🟡 Yellow = Standard
</div>
</body>
</html>'''

with open('apply-today.html', 'w') as f:
    f.write(html)

print('Rebuilt apply-today.html with ' + str(len(recs)) + ' jobs from ' + basename)
for r in recs[:5]:
    print('  ' + str(r.get('quality_score', 0)) + ' - ' + r.get('title', '') + ' @ ' + r.get('company_raw', r.get('company', '?')))
