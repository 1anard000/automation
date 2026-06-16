#!/usr/bin/env python3
"""
Career OS Quality Improver
- Aligns jobs to PM/strategy roles only in target cities
- Fixes missing company names, salary estimation, URL quality
- Writes improved jobs back and rebuilds dashboard
"""
import json, re, os
from collections import Counter
from datetime import datetime, timedelta

WORKSPACE = '/Users/iancolrick/.openclaw/workspace'
DB_PATH = os.path.join(WORKSPACE, 'OKComputer_职位搜索清单', 'jobs-all.json')
DASHBOARD_PATH = os.path.join(WORKSPACE, 'dashboard.html')

# === Load ===
with open(DB_PATH) as f:
    all_jobs = json.load(f)

print(f"Total jobs loaded: {len(all_jobs)}")

# === Step 1: Alignment filter ===
TARGET_ROLES = {
    'Product Management', 'Strategy/Ops', 'Strategy', 'Product Leadership',
    'Cross-border/Expansion', 'GM/Country Manager', 'Program Management',
    'VC/PE', 'Growth'
}

REJECT_ROLES = {
    'Sales', 'Healthcare', 'Automotive', 'Gaming', 'Entertainment',
    'Logistics', 'Supply Chain', 'Food Delivery', 'Energy',
    'CleanTech/Energy', 'Cybersecurity', 'Telecommunications',
    'E-commerce', 'Banking', 'Banking/Finance', 'Insurance',
    'Asset Management', 'Financial Services', 'AI/ML', 'Technology',
    'Cloud', 'Productivity'
}

US_LOCATIONS = [
    'united states', 'denver', 'san francisco', 'new york', 'los angeles',
    'seattle', 'chicago', 'atlanta', 'phoenix', 'cupertino', 'remote - us',
    'usa', 'us-', 'sf, sea', 'sf, ny', 'sf, new', 'seattle, sf',
    'remote in the us', 'us remote', 'sf, seattle', 'chicago, atlanta',
    'new-york', 'toronto', 'boston', 'remote us'
]

NON_APAC = ['canada', 'romania', 'latam', 'mexico']

def is_target_location(loc):
    loc_lower = loc.lower().strip()
    if not loc_lower:
        return False
    for us in US_LOCATIONS:
        if us in loc_lower:
            return False
    for non in NON_APAC:
        if non in loc_lower:
            return False
    # Check for explicit non-APAC countries
    if any(x in loc_lower for x in ['united states', 'california', 'colorado']):
        return False
    
    target_keywords = [
        'hong kong', 'wan chai', 'hung hom', 'kowloon', 'central',
        'quarry bay', 'admiralty', 'lai chi kok', 'kwun tong',
        'sheung wan', 'kwai tsing', 'science park',
        'shenzhen', 'shanghai', 'guangzhou',
        'singapore', 'changi', 'kampong', 'west singapore',
        'tokyo', 'taipei'
    ]
    for kw in target_keywords:
        if kw in loc_lower:
            return True
    if 'remote' in loc_lower and ('asia' in loc_lower or 'apac' in loc_lower):
        return True
    if loc_lower in ['remote - asia', 'remote asia', 'asia remote']:
        return True
    return False

def is_target_role(role_type):
    if not role_type:
        return False
    if role_type in REJECT_ROLES:
        return False
    if role_type in TARGET_ROLES:
        return True
    return False

def is_purely_crypto(job):
    title = job.get('title', '').lower()
    company = job.get('company', '').lower()
    ok_signals = ['crypto.com', 'fintech', 'banking', 'payments', 'digital asset', 'insurance']
    for ok in ok_signals:
        if ok in title or ok in company:
            return False
    crypto_signals = ['web3', 'defi', 'nft', 'blockchain protocol', 'mining', 'token economy']
    for signal in crypto_signals:
        if signal in title:
            return True
    return False

# Apply filters
filtered = []
rejected = Counter()

for job in all_jobs:
    if job.get('quality_bar_reject', False):
        rejected['excluded'] += 1
        continue
    if job.get('quality_score', 0) < 60:
        rejected['low_score'] += 1
        continue
    role = job.get('role_type', '')
    if not is_target_role(role):
        rejected['wrong_domain'] += 1
        continue
    loc = job.get('location', '')
    if not is_target_location(loc):
        rejected['wrong_city'] += 1
        continue
    if is_purely_crypto(job):
        rejected['crypto'] += 1
        continue
    filtered.append(job)

print(f"After filter: {len(filtered)} jobs")
print(f"Rejected: {dict(rejected)}")

# === Step 2: Normalize locations ===
def normalize_location(loc):
    loc_lower = loc.lower()
    if 'hong kong' in loc_lower or 'wan chai' in loc_lower or 'hung hom' in loc_lower or 'kowloon' in loc_lower or 'central' in loc_lower or 'quarry bay' in loc_lower or 'admiralty' in loc_lower or 'lai chi kok' in loc_lower or 'kwun tong' in loc_lower or 'sheung wan' in loc_lower or 'kwai tsing' in loc_lower or 'science park' in loc_lower:
        return 'Hong Kong'
    if 'shenzhen' in loc_lower:
        return 'Shenzhen'
    if 'shanghai' in loc_lower:
        return 'Shanghai'
    if 'guangzhou' in loc_lower:
        return 'Guangzhou'
    if 'singapore' in loc_lower or 'changi' in loc_lower or 'kampong' in loc_lower:
        return 'Singapore'
    if 'tokyo' in loc_lower:
        return 'Tokyo'
    if 'taipei' in loc_lower:
        return 'Taipei'
    return loc

for job in filtered:
    job['location_norm'] = normalize_location(job.get('location', ''))

# === Step 3: Fix missing company names ===
company_fixes = 0
for job in filtered:
    if not job.get('company', '').strip():
        title = job.get('title', '')
        # Try pattern: "Title - Company" or "Title @ Company"
        m = re.search(r'\s*[-–—@]\s*([A-Z][A-Za-z0-9\s&.]+?)(?:\s*$|\s*—)', title)
        if m:
            job['company'] = m.group(1).strip()
            company_fixes += 1
            continue
        # Try: "Company Product Director" patterns
        m = re.match(r'^(腾讯|阿里巴巴|字节跳动|百度|美团|小米|华为|京东|网易|快手|拼多多|蚂蚁集团)', title)
        if m:
            job['company'] = m.group(1)
            company_fixes += 1
            continue
        # Try from source or URL
        url = job.get('url', '')
        if 'linkedin.com' in url:
            job['company'] = 'LinkedIn (company unknown)'
            company_fixes += 1
        elif 'indeed.com' in url:
            job['company'] = 'Indeed (company unknown)'
            company_fixes += 1

print(f"Company fixes: {company_fixes}")

# === Step 4: Salary estimation ===
# CN salary floor: 90k RMB/year (~7.5k/month), HK: 60k HKD/month, SG: 10k SGD/month
SALARY_ESTIMATES = {
    'Product Director': {'Hong Kong': '60-100K HKD/mo', 'Shenzhen': '80-150K RMB/yr', 'Shanghai': '80-150K RMB/yr', 'Singapore': '15-25K SGD/mo'},
    'Head of Product': {'Hong Kong': '80-120K HKD/mo', 'Shenzhen': '100-180K RMB/yr', 'Shanghai': '100-180K RMB/yr', 'Singapore': '18-30K SGD/mo'},
    'Senior Product Manager': {'Hong Kong': '50-80K HKD/mo', 'Shenzhen': '60-120K RMB/yr', 'Shanghai': '60-120K RMB/yr', 'Singapore': '12-20K SGD/mo'},
    'Product Manager': {'Hong Kong': '40-65K HKD/mo', 'Shenzhen': '40-80K RMB/yr', 'Shanghai': '40-80K RMB/yr', 'Singapore': '10-18K SGD/mo'},
    'default': {'Hong Kong': '50-80K HKD/mo', 'Shenzhen': '60-120K RMB/yr', 'Shanghai': '60-120K RMB/yr', 'Singapore': '12-20K SGD/mo'},
}

salary_fixes = 0
for job in filtered:
    if not job.get('salary', '').strip():
        title = job.get('title', '').lower()
        loc = job.get('location_norm', job.get('location', ''))
        
        # Determine role level
        if 'director' in title or 'head of' in title or 'vp' in title or 'chief' in title:
            level = 'Head of Product'
        elif 'senior' in title or 'sr.' in title or 'principal' in title:
            level = 'Senior Product Manager'
        elif 'product' in title or 'manager' in title:
            level = 'Product Manager'
        else:
            level = 'Product Director'
        
        estimates = SALARY_ESTIMATES.get(level, SALARY_ESTIMATES['default'])
        for city_key, estimate in estimates.items():
            if city_key.lower() in loc.lower():
                job['salary'] = f"(est) {estimate}"
                salary_fixes += 1
                break

print(f"Salary estimates added: {salary_fixes}")

# === Step 5: URL quality check ===
# Mark search URLs vs direct job URLs
direct_url_patterns = ['viewjob', 'greenhouse.io/', 'lever.co/', 'ashbyhq.com/', 'linkedin.com/jobs/view/']
search_url_patterns = ['search?', 'query=', 'keyword=', '/search?', 'search.html', 'category']

url_fixes = 0
for job in filtered:
    url = job.get('url', '')
    if not url:
        continue
    
    is_direct = any(p in url for p in direct_url_patterns)
    is_search = any(p in url for p in search_url_patterns)
    
    job['url_type'] = 'direct' if is_direct else ('search' if is_search else 'unknown')
    
    if job.get('login_required') and not is_direct:
        job['url_type'] = 'login_required'
    
    if is_search or job.get('login_required'):
        job['has_direct_apply'] = False
    elif is_direct:
        job['has_direct_apply'] = True

# === Step 6: English-friendly verification for CN roles ===
ENGLISH_SIGNALS = ['english', '英语', 'overseas', 'international', 'global', '出海', '跨境', 'bilingual']

for job in filtered:
    loc = job.get('location_norm', '')
    if loc in ['Shenzhen', 'Shanghai', 'Guangzhou']:
        title = job.get('title', '').lower()
        company = job.get('company', '').lower()
        
        # Check if already marked
        if job.get('english_friendly'):
            continue
        
        # Known international companies
        intl_companies = ['google', 'apple', 'microsoft', 'amazon', 'meta', 'bytedance',
                         'tencent', 'alibaba', 'stripe', 'airwallex', 'databricks',
                         'snowflake', 'twilio', 'shopify', 'coinbase', 'rippling']
        
        english_score = 0
        for ic in intl_companies:
            if ic in company:
                english_score += 2
        
        for signal in ENGLISH_SIGNALS:
            if signal in title:
                english_score += 1
        
        if english_score >= 2:
            job['english_friendly'] = True

# === Step 7: Stale detection ===
today = datetime.now()
for job in filtered:
    scanned = job.get('scanned_date', '')
    if scanned:
        try:
            scan_date = datetime.strptime(scanned, '%Y-%m-%d')
            age_days = (today - scan_date).days
            if age_days > 7:
                job['stale'] = True
                job['stale_days'] = age_days
            else:
                job['stale'] = False
        except:
            pass

# === Step 8: Recalculate quality tiers ===
for job in filtered:
    score = job.get('quality_score', 0)
    if score >= 85:
        job['quality_tier'] = 'A'
    elif score >= 70:
        job['quality_tier'] = 'B'
    elif score >= 55:
        job['quality_tier'] = 'C'
    else:
        job['quality_tier'] = 'D'

# Sort by quality score descending
filtered.sort(key=lambda j: j.get('quality_score', 0), reverse=True)

# === Step 9: Compute stats ===
stats = Counter()
for j in filtered:
    loc = j.get('location_norm', j.get('location', ''))
    if 'Hong Kong' in loc:
        stats['HK'] += 1
    elif 'Shenzhen' in loc:
        stats['SZ'] += 1
    elif 'Shanghai' in loc:
        stats['SH'] += 1
    elif 'Guangzhou' in loc:
        stats['GZ'] += 1
    elif 'Singapore' in loc:
        stats['SG'] += 1
    elif 'Tokyo' in loc:
        stats['Tokyo'] += 1
    elif 'Taipei' in loc:
        stats['Taipei'] += 1
    else:
        stats['Other'] += 1

tier_stats = Counter(j.get('quality_tier', '') for j in filtered)
source_stats = Counter(j.get('source', '') for j in filtered)
stale_count = sum(1 for j in filtered if j.get('stale', False))
direct_count = sum(1 for j in filtered if j.get('url_type') == 'direct')
login_count = sum(1 for j in filtered if j.get('url_type') == 'login_required')

print(f"\nFinal aligned database:")
print(f"  Total: {len(filtered)}")
print(f"  Locations: {dict(stats)}")
print(f"  Tiers: {dict(tier_stats)}")
print(f"  Stale (>7 days): {stale_count}")
print(f"  Direct URLs: {direct_count}")
print(f"  Login-required: {login_count}")
print(f"  Top sources: {dict(source_stats.most_common(10))}")

# === Write improved jobs ===
with open(DB_PATH, 'w') as f:
    json.dump(filtered, f, indent=2, ensure_ascii=False)

print(f"\nWrote {len(filtered)} aligned jobs to {DB_PATH}")

# === Step 10: Build dashboard.html ===
now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
total_scanned = len(all_jobs)
total_aligned = len(filtered)

# Build job cards data for JS
jobs_json = json.dumps(filtered, ensure_ascii=False)

dashboard_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>APAC Senior Roles — Curated</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;padding:16px}}
.header{{text-align:center;padding:20px 0}}
.header h1{{font-size:1.8rem;background:linear-gradient(135deg,#38bdf8,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.header .subtitle{{color:#94a3b8;font-size:0.8rem;margin-top:4px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:10px;margin:20px 0}}
.stat{{background:#1e293b;border-radius:10px;padding:14px;text-align:center;border:1px solid #334155}}
.stat .num{{font-size:1.8rem;font-weight:700;color:#38bdf8}}
.stat .label{{font-size:0.65rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-top:4px}}
.stat.hk .num{{color:#a78bfa}}.stat.sh .num{{color:#fb923c}}.stat.sz .num{{color:#4ade80}}.stat.sg .num{{color:#f472b6}}
.filters{{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}}
.filters button{{background:#1e293b;color:#94a3b8;border:1px solid #334155;border-radius:8px;padding:6px 14px;cursor:pointer;font-size:0.8rem}}
.filters button.active{{background:#38bdf8;color:#0f172a;border-color:#38bdf8}}
.job-card{{background:#1e293b;border-radius:12px;padding:16px;margin:10px 0;border:1px solid #334155;transition:border-color 0.2s}}
.job-card:hover{{border-color:#38bdf8}}
.job-card .title{{font-size:1rem;font-weight:600;color:#f1f5f9}}
.job-card .company{{color:#38bdf8;font-size:0.9rem;margin-top:2px}}
.job-card .meta{{display:flex;gap:12px;margin-top:8px;font-size:0.75rem;color:#94a3b8;flex-wrap:wrap}}
.job-card .meta .loc::before{{content:"📍 "}}.job-card .meta .src::before{{content:"🔗 "}}
.badge{{display:inline-block;border-radius:6px;padding:2px 8px;font-size:0.7rem;font-weight:600}}
.badge-a{{background:#064e3b;color:#34d399}}.badge-b{{background:#1e3a5f;color:#60a5fa}}.badge-c{{background:#78350f;color:#fbbf24}}.badge-d{{background:#4a1d1d;color:#f87171}}
.job-card a{{color:#38bdf8;text-decoration:none;font-size:0.8rem}}
.job-card a:hover{{text-decoration:underline}}
.summary{{color:#64748b;font-size:0.8rem;margin-top:6px}}
.stale-tag{{background:#78350f;color:#fbbf24;border-radius:4px;padding:1px 6px;font-size:0.65rem;margin-left:6px}}
.login-tag{{background:#4a1d1d;color:#f87171;border-radius:4px;padding:1px 6px;font-size:0.65rem;margin-left:6px}}
.updated{{text-align:center;color:#475569;font-size:0.7rem;margin-top:20px}}
</style>
</head>
<body>
<div class="header">
<h1>🎯 APAC Senior Roles — Curated</h1>
<div class="subtitle">{total_aligned} aligned jobs from {total_scanned} scanned · Updated {now_str}</div>
</div>
<div class="stats">
<div class="stat"><div class="num">{total_aligned}</div><div class="label">Total</div></div>
<div class="stat hk"><div class="num">{stats.get("HK",0)}</div><div class="label">HK</div></div>
<div class="stat sh"><div class="num">{stats.get("SH",0)}</div><div class="label">Shanghai</div></div>
<div class="stat sz"><div class="num">{stats.get("SZ",0)}</div><div class="label">Shenzhen</div></div>
<div class="stat sg"><div class="num">{stats.get("SG",0)}</div><div class="label">Singapore</div></div>
{f'<div class="stat"><div class="num">{stats.get("GZ",0)}</div><div class="label">Guangzhou</div></div>' if stats.get("GZ",0) else ''}
</div>
<div class="filters" id="filters">
<button class="active" data-filter="all">All ({total_aligned})</button>
<button data-filter="A">Tier A ({tier_stats.get("A",0)})</button>
<button data-filter="B">Tier B ({tier_stats.get("B",0)})</button>
<button data-filter="C">Tier C ({tier_stats.get("C",0)})</button>
<button data-filter="hk">HK ({stats.get("HK",0)})</button>
<button data-filter="sh">SH ({stats.get("SH",0)})</button>
<button data-filter="sz">SZ ({stats.get("SZ",0)})</button>
<button data-filter="sg">SG ({stats.get("SG",0)})</button>
<button data-filter="strategy">Strategy</button>
<button data-filter="product">Product</button>
<button data-filter="direct">Direct URLs ({direct_count})</button>
<button data-filter="stale">Stale ({stale_count})</button>
</div>
<div id="jobs"></div>
<div class="updated">Last updated: {now_str} · {total_aligned} jobs from {len(source_stats)} sources · {direct_count} direct URLs · {login_count} login-required</div>
<script>
const jobs = {jobs_json};
function render(filter) {{
  const el = document.getElementById('jobs');
  let filtered = jobs;
  if (filter === 'hk') filtered = jobs.filter(j => (j.location_norm||j.location||'').toLowerCase().includes('hong kong'));
  else if (filter === 'sh') filtered = jobs.filter(j => (j.location_norm||j.location||'').toLowerCase().includes('shanghai'));
  else if (filter === 'sz') filtered = jobs.filter(j => (j.location_norm||j.location||'').toLowerCase().includes('shenzhen'));
  else if (filter === 'sg') filtered = jobs.filter(j => (j.location_norm||j.location||'').toLowerCase().includes('singapore'));
  else if (filter === 'A') filtered = jobs.filter(j => j.quality_tier === 'A');
  else if (filter === 'B') filtered = jobs.filter(j => j.quality_tier === 'B');
  else if (filter === 'C') filtered = jobs.filter(j => j.quality_tier === 'C');
  else if (filter === 'strategy') filtered = jobs.filter(j => (j.role_type||'').toLowerCase().includes('strat'));
  else if (filter === 'product') filtered = jobs.filter(j => (j.role_type||'').toLowerCase().includes('product'));
  else if (filter === 'direct') filtered = jobs.filter(j => j.url_type === 'direct');
  else if (filter === 'stale') filtered = jobs.filter(j => j.stale);
  filtered.sort((a,b) => (b.quality_score||0) - (a.quality_score||0));
  el.innerHTML = filtered.map(j => {{
    const score = j.quality_score||0;
    const tier = j.quality_tier || (score >= 85 ? 'A' : score >= 70 ? 'B' : score >= 55 ? 'C' : 'D');
    const title = j.en_title || j.title || 'Untitled';
    const company = j.company || 'Unknown';
    const loc = j.location_norm || j.location || '';
    const src = j.source || '';
    const url = j.url || '#';
    const summary = j.summary || '';
    const salary = j.salary || '';
    const stale = j.stale ? '<span class="stale-tag">⚠️ Stale</span>' : '';
    const login = j.login_required ? '<span class="login-tag">🔒 Login Required</span>' : '';
    const urlBadge = j.url_type === 'direct' ? '✅' : j.url_type === 'login_required' ? '🔒' : '⚠️';
    return `<div class="job-card">
      <div class="title">${{title}}${{stale}}${{login}}</div>
      <div class="company">${{company}}</div>
      ${{summary ? `<div class="summary">${{summary.substring(0,120)}}${{summary.length>120?'...':''}}</div>` : ''}}
      <div class="meta">
        <span class="loc">${{loc}}</span>
        <span class="src">${{urlBadge}} ${{src}}</span>
        <span class="badge badge-${{tier.toLowerCase()}}">${{tier}} ${{score}}</span>
        ${{salary ? `<span>💰 ${{salary}}</span>` : ''}}
      </div>
      <a href="${{url}}" target="_blank">Apply →</a>
    </div>`;
  }}).join('');
}}
document.querySelectorAll('.filters button').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.filters button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    render(btn.dataset.filter);
  }});
}});
render('all');
</script>
</body>
</html>'''

with open(DASHBOARD_PATH, 'w') as f:
    f.write(dashboard_html)

# Also copy to OKComputer copy
OKC_DASH = os.path.join(WORKSPACE, 'OKComputer_职位搜索清单', 'dashboard.html')
with open(OKC_DASH, 'w') as f:
    f.write(dashboard_html)

# Copy to career-os copy
CO_DB = os.path.join(WORKSPACE, 'career-os', 'OKComputer_职位搜索清单', 'jobs-all.json')
with open(CO_DB, 'w') as f:
    json.dump(filtered, f, indent=2, ensure_ascii=False)

print(f"\nDashboard written: {DASHBOARD_PATH}")
print(f"Dashboard size: {os.path.getsize(DASHBOARD_PATH)} bytes")
print(f"OKC dashboard: {OKC_DASH}")
print(f"Career-os DB synced: {CO_DB}")

# === Summary report ===
print("\n" + "="*60)
print("QUALITY IMPROVEMENT REPORT")
print("="*60)
print(f"Input: {len(all_jobs)} total jobs")
print(f"Output: {len(filtered)} aligned jobs ({len(filtered)/len(all_jobs)*100:.0f}% retained)")
print(f"\nImprovements applied:")
print(f"  Company names fixed: {company_fixes}")
print(f"  Salary estimates added: {salary_fixes}")
print(f"  Locations normalized: {len(filtered)} (all jobs)")
print(f"  URL types classified: {len(filtered)} (all jobs)")
print(f"  Stale jobs flagged: {stale_count}")
print(f"\nRejected by filter:")
print(f"  Wrong domain: {rejected['wrong_domain']}")
print(f"  Wrong city: {rejected['wrong_city']}")
print(f"  Low score (<60): {rejected['low_score']}")
print(f"  Purely crypto: {rejected['crypto']}")
print(f"  Excluded: {rejected['excluded']}")
print(f"\nTier breakdown: {dict(tier_stats)}")
print(f"Location breakdown: {dict(stats)}")
print(f"Direct URL jobs: {direct_count}")
print(f"Login-required jobs: {login_count}")
