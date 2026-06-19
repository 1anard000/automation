#!/usr/bin/env python3
"""Rebuild dashboard.html — reads JS from rebuild-dashboard.js to avoid quoting issues."""
import json, os
from datetime import datetime
from collections import Counter

jobs = json.load(open('OKComputer_职位搜索清单/jobs-all.json'))
# Deduplicate by title+company (case-insensitive), keep higher quality_score
_deduped = {}
for _j in jobs:
    _key = (_j.get('title', '').strip().lower(), _j.get('company', '').strip().lower())
    if _key in _deduped:
        if _j.get('quality_score', 0) > _deduped[_key].get('quality_score', 0):
            _deduped[_key] = _j
    else:
        _deduped[_key] = _j
jobs = list(_deduped.values())
js_code = open('rebuild-dashboard.js').read()

CRYPTO_COMPANIES = ['binance', 'okx', 'coins.ph', 'bitdeer', 'bullish', 'coinmarketcap',
                    'btse', 'decard', 'gate', 'osl', 'bitget', 'huobi', 'kucoin', 'bybit', 'kraken']
CRYPTO_TITLE = ['crypto', 'bitcoin', 'blockchain', 'web3', 'defi', 'token listing',
                'dex trading', 'on chain', 'nft']

def is_aligned(j):
    title = (j.get('title','') + ' ' + j.get('en_title','')).lower()
    summary = j.get('summary', '').lower()
    desc = j.get('description', '').lower()
    company = j.get('company', '').lower()
    pm_signals = ['product manager', 'product director', 'head of product', 'vp product',
                  'strategy', 'program manager', 'general manager', 'bizops', 'chief of staff',
                  'product lead', 'product owner', 'director product', 'director strategy']
    if not any(s in title for s in pm_signals):
        return False
    reject_domains = ['sales', 'marketing', 'hr', 'recruiting', 'finance', 'design',
                      'data scientist', 'engineer', 'developer', 'analyst', 'accountant', 'legal',
                      'admin', 'operations manager', 'supply chain']
    if any(d in title for d in reject_domains):
        return False
    loc = j.get('location_norm', j.get('location','')).lower()
    target_locs = ['hong kong', 'shenzhen', 'shanghai', 'guangzhou', 'singapore', 'tokyo', 'taipei']
    if not any(t in loc for t in target_locs):
        return False
    if j.get('quality_score', 0) < 70:
        return False
    if any(c in company for c in CRYPTO_COMPANIES):
        return False
    if any(c in title or c in summary or c in desc for c in CRYPTO_TITLE):
        return False
    if j.get('english_friendly') == False:
        return False
    bilingual_kw = ['bilingual', '\u4e2d\u82f1', '\u53cc\u8bed', '\u4e2d\u6587', 'chinese required', 'mandarin required']
    if any(b in title or b in summary or b in desc for b in bilingual_kw):
        return False
    return True

aligned = [j for j in jobs if is_aligned(j)]
total = len(aligned)

# Company tier classification
BIGTECH = ['google', 'meta', 'microsoft', 'apple', 'amazon', 'bytedance', 'tiktok', 'tencent', 'alibaba',
           'jd.com', 'baidu', 'bytedance ltd', 'huawei', 'qualcomm', 'cisco', 'mastercard', 'visa',
           'jpmorgan chase', 'hsbc', 'jpmorgan']
GROWTH = ['airwallex', 'shopee', 'grab', 'lalamove', 'klook', 'agoda', 'gojek', 'tokopedia',
          'sea group', ' Lazada', 'sailpoint', 'canva', 'atlassian', 'stripe', 'wise',
          'ninja van', 'carousell', 'futu', 'xiaomi', 'meituan', 'didi', 'ant group', 'antom',
          'dtcpay', 'gotymex', 'equinix', 'ge healthcare', 'abbvie', 'bio-techne', 'ingram micro',
          'dp world', 'codat', 'coda', 'virtuos']
ENTERPRISE = ['aia group', 'axa', 'uob', 'bank of china', 'hang seng bank', 'bny', 'gic',
              'govtech', 'indeed', 'jobsdb', 'kgroup', 'ambition', 'be myjob', 'constructor technology',
              'casetify', 'greaterheat', 'on', 'kgi']

def classify_company(co):
    co_l = co.lower().strip()
    for b in BIGTECH:
        if b in co_l or co_l in b:
            return 'bigtech'
    for g in GROWTH:
        if g.lower() in co_l or co_l in g.lower():
            return 'growth'
    for e in ENTERPRISE:
        if e in co_l or co_l in e:
            return 'enterprise'
    return 'startup'

for j in aligned:
    j['_company_tier'] = classify_company(j.get('company', ''))

# Salary tier classification (monthly USD estimate)
import re as _re
def _parse_salary_monthly_usd(s):
    if not s: return None
    sl = s.lower().replace(',', '').strip()
    sc = _re.sub(r'\s*-\s*', '-', sl)
    has_k = bool(_re.search(r'(\d)k(?!d)', sc))
    m = _re.search(r'(\d+\.?\d*)', sc)
    if not m: return None
    try: val = float(m.group(1))
    except: return None
    if has_k: val *= 1000
    if 'hkd' in sl: rate = 0.128
    elif 'sgd' in sl: rate = 0.75
    elif 'rmb' in sl or 'cny' in sl: rate = 0.137
    else: rate = 1.0
    usd = val * rate
    is_yearly = '/yr' in sl or 'year' in sl
    is_monthly = '/mo' in sl or '/month' in sl or '月' in sl
    if is_yearly: usd /= 12
    elif not is_monthly and val > 500: usd /= 12
    return round(usd)

for j in aligned:
    _usd = _parse_salary_monthly_usd(j.get('salary', ''))
    j['_salary_usd'] = _usd
    if _usd is None: j['_salary_tier'] = 'none'
    elif _usd >= 12000: j['_salary_tier'] = 'high'
    elif _usd >= 8000: j['_salary_tier'] = 'midhigh'
    elif _usd >= 5000: j['_salary_tier'] = 'mid'
    else: j['_salary_tier'] = 'low'

salary_tier_counts = Counter(j['_salary_tier'] for j in aligned)

tier_counts = Counter(j['_company_tier'] for j in aligned)

locs = Counter(j.get('location_norm', j.get('location','')) for j in aligned)
hk = sum(v for k,v in locs.items() if 'hong kong' in k.lower())
sh = sum(v for k,v in locs.items() if 'shanghai' in k.lower())
sz = sum(v for k,v in locs.items() if 'shenzhen' in k.lower())
sg = sum(v for k,v in locs.items() if 'singapore' in k.lower())
gz = sum(v for k,v in locs.items() if 'guangzhou' in k.lower())
now = datetime.now().strftime('%Y-%m-%d %H:%M')
jobs_json = json.dumps(aligned, ensure_ascii=False)

direct_count = sum(1 for j in aligned if j.get('url_type') == 'direct' or
    any(p in j.get('url','') for p in ['viewjob','greenhouse.io/','lever.co/','ashbyhq.com/',
    'linkedin.com/jobs/view/','workday.com/','/job/','/position/','/posting/']))

# Compute staleness stats
from datetime import datetime as _dt
_today = _dt.now()
stale_count = 0
fresh_count = 0
for j in aligned:
    sd = j.get('scanned_date', '')
    if sd:
        try:
            _days = (_today - _dt.strptime(sd[:10], '%Y-%m-%d')).days
            if _days >= 6:
                stale_count += 1
            elif _days <= 2:
                fresh_count += 1
        except Exception:
            pass

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>APAC Senior Roles</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;padding:16px}}
.hdr{{text-align:center;padding:20px 0}}
.hdr h1{{font-size:1.8rem;background:linear-gradient(135deg,#38bdf8,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.hdr .sub{{color:#94a3b8;font-size:0.8rem;margin-top:4px}}
.sts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(90px,1fr));gap:10px;margin:20px 0}}
.st{{background:#1e293b;border-radius:10px;padding:12px;text-align:center;border:1px solid #334155}}
.st .n{{font-size:1.6rem;font-weight:700;color:#38bdf8}}
.st .l{{font-size:0.6rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-top:4px}}
.st.hk .n{{color:#a78bfa}}.st.sh .n{{color:#fb923c}}.st.sz .n{{color:#4ade80}}.st.sg .n{{color:#f472b6}}
.flt{{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}}
.flt button{{background:#1e293b;color:#94a3b8;border:1px solid #334155;border-radius:8px;padding:6px 14px;cursor:pointer;font-size:0.8rem}}
.flt button.on{{background:#38bdf8;color:#0f172a;border-color:#38bdf8}}
.jc{{background:#1e293b;border-radius:12px;padding:16px;margin:10px 0;border:1px solid #334155;transition:border-color 0.2s}}
.jc:hover{{border-color:#38bdf8}}
.jc .t{{font-size:1rem;font-weight:600;color:#f1f5f9}}
.jc .co{{color:#38bdf8;font-size:0.9rem;margin-top:2px}}
.jc .mt{{display:flex;gap:12px;margin-top:8px;font-size:0.75rem;color:#94a3b8;flex-wrap:wrap}}
.jc .mt .lc::before{{content:"📍 "}}.jc .mt .sc::before{{content:"🔗 "}}
.bg{{display:inline-block;border-radius:6px;padding:2px 8px;font-size:0.7rem;font-weight:600}}
.bg-a{{background:#064e3b;color:#34d399}}.bg-b{{background:#1e3a5f;color:#60a5fa}}.bg-c{{background:#78350f;color:#fbbf24}}
.ut{{display:inline-block;border-radius:4px;padding:1px 6px;font-size:0.65rem;font-weight:500;margin-left:6px}}
.ut-direct{{background:#065f46;color:#6ee7b7}}.ut-search{{background:#713f12;color:#fde68a}}.ut-login{{background:#581c87;color:#d8b4fe}}
.lk{{display:flex;gap:10px;margin-top:10px}}
.lk a{{text-decoration:none;font-size:0.85rem;font-weight:500;padding:6px 14px;border-radius:8px;display:inline-block}}
.lk .ap{{background:#064e3b;color:#34d399;border:1px solid #34d399}}
.lk .ap:hover{{background:#34d399;color:#064e3b}}
.lk .gs{{background:#78350f;color:#fbbf24;border:1px solid #fbbf24}}
.lk .gs:hover{{background:#fbbf24;color:#78350f}}
.sm{{color:#64748b;font-size:0.8rem;margin-top:6px}}
.upt{{text-align:center;color:#475569;font-size:0.7rem;margin-top:20px}}
.url-fix{{background:#7f1d1d;color:#fca5a5;border:1px solid #fca5a5;border-radius:4px;padding:2px 6px;font-size:0.65rem;margin-left:8px}}
.en{{background:#1e3a5f;color:#93c5fd;border:1px solid #93c5fd;border-radius:4px;padding:2px 6px;font-size:0.65rem;margin-left:6px}}
.salary{{color:#4ade80;font-size:0.75rem}}
.status-badge{{display:inline-block;border-radius:4px;padding:2px 8px;font-size:0.65rem;font-weight:600;margin-left:6px;cursor:pointer;transition:all 0.2s}}
.status-badge:hover{{transform:scale(1.1);filter:brightness(1.2)}}
.st-not_applied{{background:#334155;color:#94a3b8;border:1px solid #475569}}
.st-applied{{background:#064e3b;color:#34d399;border:1px solid #34d399}}
.st-interviewing{{background:#1e3a5f;color:#60a5fa;border:1px solid #60a5fa}}
.st-offer{{background:#78350f;color:#fbbf24;border:1px solid #fbbf24}}
.st-rejected{{background:#7f1d1d;color:#fca5a5;border:1px solid #fca5a5}}
.st-not_interested{{background:#1e1b4b;color:#a5b4fc;border:1px solid #a5b4fc}}
.st-btn{{background:#1e293b;color:#94a3b8;border:1px solid #334155;border-radius:6px;padding:4px 10px;cursor:pointer;font-size:0.7rem}}
.st-btn.on{{background:#38bdf8;color:#0f172a;border-color:#38bdf8}}
.st-btn:hover{{border-color:#38bdf8}}
.st-stats{{background:#1e293b;border-radius:6px;padding:4px 10px;font-size:0.7rem;color:#94a3b8;border:1px solid #334155}}
.notes-area{{margin-top:8px;padding-top:8px;border-top:1px solid #334155}}
.notes-toggle{{background:none;border:none;color:#94a3b8;font-size:0.7rem;cursor:pointer;padding:2px 6px;border-radius:4px}}
.notes-toggle:hover{{background:#334155;color:#e2e8f0}}
.notes-toggle.has-notes{{color:#4ade80}}
.notes-content{{display:none;margin-top:6px}}
.notes-content.show{{display:block}}
.notes-input{{width:100%;background:#0f172a;color:#e2e8f0;border:1px solid #334155;border-radius:6px;padding:8px;font-size:0.8rem;resize:vertical;min-height:40px;font-family:inherit}}
.notes-input:focus{{border-color:#38bdf8;outline:none}}
.notes-saved{{color:#4ade80;font-size:0.65rem;margin-left:8px;display:none}}
.notes-saved.show{{display:inline}}
.back-to-top{{position:fixed;bottom:24px;right:24px;background:#38bdf8;color:#0f172a;width:44px;height:44px;border-radius:50%;border:none;font-size:1.4rem;cursor:pointer;display:none;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(56,189,248,0.4);z-index:999;transition:opacity 0.2s,transform 0.2s}}
.back-to-top:hover{{transform:scale(1.1)}}
.search-hint{{color:#475569;font-size:0.7rem;margin-top:4px}}
.search-hint kbd{{background:#1e293b;border:1px solid #334155;border-radius:4px;padding:1px 6px;font-family:inherit;font-size:0.65rem;color:#94a3b8}}
.staleness{{display:inline-block;border-radius:4px;padding:1px 6px;font-size:0.65rem;font-weight:500;margin-left:6px}}
.staleness-fresh{{background:#064e3b;color:#34d399;border:1px solid #34d399}}
.staleness-ok{{background:#713f12;color:#fde68a;border:1px solid #fde68a}}
.staleness-stale{{background:#7f1d1d;color:#fca5a5;border:1px solid #fca5a5}}
.staleness-ancient{{background:#4c1d1d;color:#f87171;border:1px solid #f87171}}
.tier{{display:inline-block;border-radius:4px;padding:1px 6px;font-size:0.65rem;font-weight:600;margin-left:6px}}
.tier-bigtech{{background:#1e3a5f;color:#60a5fa;border:1px solid #60a5fa}}
.tier-growth{{background:#064e3b;color:#34d399;border:1px solid #34d399}}
.tier-enterprise{{background:#78350f;color:#fbbf24;border:1px solid #fbbf24}}
.tier-startup{{background:#312e81;color:#a5b4fc;border:1px solid #a5b4fc}}
.st-stats-stale{{background:#1e293b;border-radius:6px;padding:4px 10px;font-size:0.7rem;color:#94a3b8;border:1px solid #334155}}
.st-stats-stale .n{{font-size:0.85rem;font-weight:700}}
.st-stats-stale.stale-warn .n{{color:#fbbf24}}
.st-stats-stale.stale-danger .n{{color:#f87171}}
</style>
</head>
<body>
<div class="hdr">
<h1>🎯 APAC Senior Roles</h1>
<div class="sub">{total} aligned from {len(jobs)} scanned · {direct_count} direct links · {now}</div>
</div>
<div class="sts">
<div class="st"><div class="n">{total}</div><div class="l">Total</div></div>
<div class="st hk"><div class="n">{hk}</div><div class="l">HK</div></div>
<div class="st sh"><div class="n">{sh}</div><div class="l">SH</div></div>
<div class="st sz"><div class="n">{sz}</div><div class="l">SZ</div></div>
<div class="st sg"><div class="n">{sg}</div><div class="l">SG</div></div>
<div class="st"><div class="n">{gz}</div><div class="l">GZ</div></div>
<div class="st-stats-stale{' stale-danger' if stale_count > 5 else ' stale-warn' if stale_count > 0 else ''}"><div class="n">⏰ {stale_count}</div><div class="l">Stale 6d+</div></div>
<div class="st-stats-stale"><div class="n">🟢 {fresh_count}</div><div class="l">Fresh 0-2d</div></div>
</div>
<div class="flt" id="flt">
<button class="on" data-f="all">All ({total})</button>
<button data-f="A">A-tier</button>
<button data-f="B">B-tier</button>
<button data-f="hk">HK</button>
<button data-f="sh">SH</button>
<button data-f="sz">SZ</button>
<button data-f="sg">SG</button>
<button data-f="strategy">Strategy</button>
<button data-f="product">Product</button>
<button data-f="ai">AI</button>
<button data-f="fintech">💳 Fintech</button>
<button data-f="crossborder">🌍 Cross-border</button>
<button data-f="growth">📈 Growth</button>
<button data-f="senior">👔 Senior PM</button>
<button data-f="direct">🎯 Direct Apply</button>
<button data-f="easy">⚡ Easy Apply</button>
<button data-f="english">🌐 English</button>
<button data-f="needs_url">🔧 Needs URL Fix</button>
<button data-f="top20">🏆 Top 20</button>
<button data-f="bigtech" style="color:#60a5fa">🏢 Big Tech ({tier_counts.get('bigtech',0)})</button>
<button data-f="company_growth" style="color:#34d399">🚀 Growth ({tier_counts.get('growth',0)})</button>
<button data-f="enterprise" style="color:#fbbf24">🏛 Enterprise ({tier_counts.get('enterprise',0)})</button>
<button data-f="startup" style="color:#a5b4fc">⚡ Startup ({tier_counts.get('startup',0)})</button>
<button data-f="sal_high" style="color:#4ade80">💰 $12K+/mo ({salary_tier_counts.get('high',0)})</button>
<button data-f="sal_midhigh" style="color:#86efac">💰 $8-12K/mo ({salary_tier_counts.get('midhigh',0)})</button>
<button data-f="sal_mid" style="color:#fde68a">💰 $5-8K/mo ({salary_tier_counts.get('mid',0)})</button>
<button data-f="sal_low" style="color:#fca5a5">💰 &lt;$5K/mo ({salary_tier_counts.get('low',0)})</button>
<button data-f="sal_none" style="color:#94a3b8">📋 No salary ({salary_tier_counts.get('none',0)})</button>
</div>
<div style="margin:12px 0">
<input type="text" id="search-box" placeholder="🔍 Search jobs by title, company, location..." style="width:100%;max-width:600px;background:#1e293b;color:#e2e8f0;border:1px solid #334155;border-radius:8px;padding:10px 14px;font-size:0.9rem;outline:none" oninput="render(currentFilter)">
<div class="search-hint">Press <kbd>/</kbd> to search · <kbd>Esc</kbd> to clear</div>
</div>
<div class="flt" id="status-flt" style="margin-top:4px">
<span style="color:#94a3b8;font-size:0.7rem;margin-right:4px">Status:</span>
<button data-f="st_not_applied" class="st-btn">📥 Not Applied</button>
<button data-f="st_applied" class="st-btn">✅ Applied</button>
<button data-f="st_interviewing" class="st-btn">🎤 Interviewing</button>
<button data-f="st_offer" class="st-btn">🎉 Offer</button>
<button data-f="st_rejected" class="st-btn">❌ Rejected</button>
<button data-f="st_not_interested" class="st-btn">🙈 Not Interested</button>
<button data-f="st_all_status" class="st-btn" style="background:#334155;color:#94a3b8">All Status</button>
</div>
<div id="status-stats" style="display:flex;gap:8px;margin:8px 0;flex-wrap:wrap"></div>
<div style="display:flex;gap:8px;margin:12px 0;align-items:center">
<span style="color:#94a3b8;font-size:0.75rem">Sort:</span>
<select id="sort" style="background:#1e293b;color:#e2e8f0;border:1px solid #334155;border-radius:6px;padding:4px 8px;font-size:0.75rem">
<option value="score">Quality Score</option>
<option value="date">Scan Date (Newest)</option>
<option value="company">Company</option>
<option value="location">Location</option>
<option value="difficulty">Apply Difficulty</option>
<option value="salary">Salary (Highest)</option>
</select>
</div>
<div id="jobs"></div>
<div id="result-count" style="text-align:center;color:#94a3b8;font-size:0.8rem;margin:8px 0"></div>
<div class="upt">Last updated: {now}</div>
<button class="back-to-top" id="btt" title="Back to top">↑</button>
<script>
const jobs = {jobs_json};
{js_code}
</script>
<script>
(function(){{var b=document.getElementById('btt');window.addEventListener('scroll',function(){{b.style.display=window.scrollY>400?'flex':'none'}});b.addEventListener('click',function(){{window.scrollTo({{top:0,behavior:'smooth'}})}})}})();
document.addEventListener('keydown',function(e){{
  if(e.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){{
    e.preventDefault();document.getElementById('search-box').focus();
  }}
  if(e.key==='Escape'){{
    var s=document.getElementById('search-box');
    if(document.activeElement===s){{s.value='';s.blur();render(currentFilter)}}
  }}
}});
/* Staleness badges — compute days since scan and add color-coded badges */
(function(){{
  var jobMap={{}};jobs.forEach(function(j){{jobMap[j.job_id]=j}});
  var today=new Date();
  function daysSince(d){{if(!d)return-1;var dt=new Date(d);return Math.floor((today-dt)/(864e5))}}
  function addStaleness(){{
    document.querySelectorAll('.jc').forEach(function(card){{
      if(card.querySelector('.staleness'))return;
      /* find job_id from status-badge data attribute */
      var badge=card.querySelector('.status-badge[data-job-id]');
      if(!badge)return;
      var jid=badge.dataset.jobId;
      var j=jobMap[jid];
      if(!j||!j.scanned_date)return;
      var d=daysSince(j.scanned_date);
      if(d<0)return;
      var cls,label;
      if(d<=2){{cls='staleness-fresh';label='✅ '+d+'d ago'}}
      else if(d<=4){{cls='staleness-ok';label='📅 '+d+'d ago'}}
      else if(d<=6){{cls='staleness-stale';label='⏰ '+d+'d old'}}
      else{{cls='staleness-ancient';label='🔥 '+d+'d old!'}}
      var span=document.createElement('span');
      span.className='staleness '+cls;
      span.textContent=label;
      span.title='Scanned: '+j.scanned_date;
      var titleEl=card.querySelector('.t');
      if(titleEl)titleEl.appendChild(span);
    }});
  }}
  var obs=new MutationObserver(addStaleness);
  obs.observe(document.getElementById('jobs'),{{childList:true}});
  addStaleness();
}})();
</script>
</body>
</html>"""

with open('dashboard.html', 'w') as f:
    f.write(html)
print(f'Dashboard: {total} jobs, {direct_count} direct, {total - direct_count} need URL fix, {os.path.getsize("dashboard.html")//1024}KB')
