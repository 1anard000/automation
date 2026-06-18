#!/usr/bin/env python3
"""Rebuild dashboard.html with Google search fallback and application tracking."""
import json, os
from datetime import datetime
from collections import Counter

jobs = json.load(open('OKComputer_职位搜索清单/jobs-all.json'))

def is_aligned(j):
    title = (j.get('title','') + ' ' + j.get('en_title','')).lower()
    pm_signals = ['product manager', 'product director', 'head of product', 'vp product',
                  'strategy', 'program manager', 'general manager', 'bizops', 'chief of staff',
                  'product lead', 'product owner', 'director product', 'director strategy']
    if not any(s in title for s in pm_signals):
        return False
    reject_domains = ['sales', 'marketing', 'hr', 'recruiting', 'finance', 'design',
                      'data scientist', 'engineer', 'developer', 'analyst', 'accountant',
                      'legal', 'admin', 'operations manager', 'supply chain']
    if any(d in title for d in reject_domains):
        return False
    loc = j.get('location_norm', j.get('location','')).lower()
    target_locs = ['hong kong', 'shenzhen', 'shanghai', 'guangzhou', 'singapore', 'tokyo', 'taipei']
    if not any(t in loc for t in target_locs):
        return False
    if j.get('quality_score', 0) < 60:
        return False
    return True

aligned = [j for j in jobs if is_aligned(j)]
total = len(aligned)

locs = Counter(j.get('location_norm', j.get('location','')) for j in aligned)
hk = sum(v for k,v in locs.items() if 'hong kong' in k.lower())
sh = sum(v for k,v in locs.items() if 'shanghai' in k.lower())
sz = sum(v for k,v in locs.items() if 'shenzhen' in k.lower())
sg = sum(v for k,v in locs.items() if 'singapore' in k.lower())
gz = sum(v for k,v in locs.items() if 'guangzhou' in k.lower())
sources = Counter(j.get('source','unknown') for j in aligned)
now = datetime.now().strftime('%Y-%m-%d %H:%M')
jobs_json = json.dumps(aligned, ensure_ascii=False)

direct_count = sum(1 for j in aligned if j.get('url_type') == 'direct' or any(p in j.get('url','') for p in ['viewjob','greenhouse.io/','lever.co/','ashbyhq.com/','linkedin.com/jobs/view/','workday.com/','/job/','/position/','/posting/']))

# Count jobs needing URL fixes
needs_url_fix = sum(1 for j in aligned if j.get('url_type') != 'direct')

html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>APAC Senior Roles</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;padding:16px}
.hdr{text-align:center;padding:20px 0}
.hdr h1{font-size:1.8rem;background:linear-gradient(135deg,#38bdf8,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hdr .sub{color:#94a3b8;font-size:0.8rem;margin-top:4px}
.sts{display:grid;grid-template-columns:repeat(auto-fit,minmax(90px,1fr));gap:10px;margin:20px 0}
.st{background:#1e293b;border-radius:10px;padding:12px;text-align:center;border:1px solid #334155}
.st .n{font-size:1.6rem;font-weight:700;color:#38bdf8}
.st .l{font-size:0.6rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-top:4px}
.st.hk .n{color:#a78bfa}.st.sh .n{color:#fb923c}.st.sz .n{color:#4ade80}.st.sg .n{color:#f472b6}
.flt{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}
.flt button{background:#1e293b;color:#94a3b8;border:1px solid #334155;border-radius:8px;padding:6px 14px;cursor:pointer;font-size:0.8rem}
.flt button.on{background:#38bdf8;color:#0f172a;border-color:#38bdf8}
.jc{background:#1e293b;border-radius:12px;padding:16px;margin:10px 0;border:1px solid #334155;transition:border-color 0.2s}
.jc:hover{border-color:#38bdf8}
.jc .t{font-size:1rem;font-weight:600;color:#f1f5f9}
.jc .co{color:#38bdf8;font-size:0.9rem;margin-top:2px}
.jc .mt{display:flex;gap:12px;margin-top:8px;font-size:0.75rem;color:#94a3b8;flex-wrap:wrap}
.jc .mt .lc::before{content:"📍 "}.jc .mt .sc::before{content:"🔗 "}
.bg{display:inline-block;border-radius:6px;padding:2px 8px;font-size:0.7rem;font-weight:600}
.bg-a{background:#064e3b;color:#34d399}.bg-b{background:#1e3a5f;color:#60a5fa}.bg-c{background:#78350f;color:#fbbf24}
.ut{display:inline-block;border-radius:4px;padding:1px 6px;font-size:0.65rem;font-weight:500;margin-left:6px}
.ut-direct{background:#065f46;color:#6ee7b7}.ut-search{background:#713f12;color:#fde68a}.ut-login{background:#581c87;color:#d8b4fe}
.lk{display:flex;gap:10px;margin-top:10px}
.lk a{text-decoration:none;font-size:0.85rem;font-weight:500;padding:6px 14px;border-radius:8px;display:inline-block}
.lk .ap{background:#064e3b;color:#34d399;border:1px solid #34d399}
.lk .ap:hover{background:#34d399;color:#064e3b}
.lk .gs{background:#78350f;color:#fbbf24;border:1px solid #fbbf24}
.lk .gs:hover{background:#fbbf24;color:#78350f}
.sm{color:#64748b;font-size:0.8rem;margin-top:6px}
#search-box:focus{border-color:#38bdf8;box-shadow:0 0 0 2px rgba(56,189,248,0.2)}
.upt{text-align:center;color:#475569;font-size:0.7rem;margin-top:20px}
.url-fix{background:#7f1d1d;color:#fca5a5;border:1px solid #fca5a5;border-radius:4px;padding:2px 6px;font-size:0.65rem;margin-left:8px}
.en{background:#1e3a5f;color:#93c5fd;border:1px solid #93c5fd;border-radius:4px;padding:2px 6px;font-size:0.65rem;margin-left:6px}
.salary{color:#4ade80;font-size:0.75rem}
.status-badge{display:inline-block;border-radius:4px;padding:2px 8px;font-size:0.65rem;font-weight:600;margin-left:6px;cursor:pointer;transition:all 0.2s}
.status-badge:hover{transform:scale(1.1);filter:brightness(1.2)}
.st-not_applied{background:#334155;color:#94a3b8;border:1px solid #475569}
.st-applied{background:#064e3b;color:#34d399;border:1px solid #34d399}
.st-interviewing{background:#1e3a5f;color:#60a5fa;border:1px solid #60a5fa}
.st-offer{background:#78350f;color:#fbbf24;border:1px solid #fbbf24}
.st-rejected{background:#7f1d1d;color:#fca5a5;border:1px solid #fca5a5}
.st-not_interested{background:#1e1b4b;color:#a5b4fc;border:1px solid #a5b4fc}
.st-btn{background:#1e293b;color:#94a3b8;border:1px solid #334155;border-radius:6px;padding:4px 10px;cursor:pointer;font-size:0.7rem}
.st-btn.on{background:#38bdf8;color:#0f172a;border-color:#38bdf8}
.st-btn:hover{border-color:#38bdf8}
.st-stats{background:#1e293b;border-radius:6px;padding:4px 10px;font-size:0.7rem;color:#94a3b8;border:1px solid #334155}
.notes-area{margin-top:8px;padding-top:8px;border-top:1px solid #334155}
.notes-toggle{background:none;border:none;color:#94a3b8;font-size:0.7rem;cursor:pointer;padding:2px 6px;border-radius:4px}
.notes-toggle:hover{background:#334155;color:#e2e8f0}
.notes-toggle.has-notes{color:#4ade80}
.notes-content{display:none;margin-top:6px}
.notes-content.show{display:block}
.notes-input{width:100%;background:#0f172a;color:#e2e8f0;border:1px solid #334155;border-radius:6px;padding:8px;font-size:0.8rem;resize:vertical;min-height:40px;font-family:inherit}
.notes-input:focus{border-color:#38bdf8;outline:none}
.notes-saved{color:#4ade80;font-size:0.65rem;margin-left:8px;display:none}
.notes-saved.show{display:inline}
</style>
</head>
<body>
<div class="hdr">
<h1>🎯 APAC Senior Roles</h1>
<div class="sub">TOTAL_JOBS aligned from TOTAL_SCANNED scanned · DIRECT_COUNT direct links · UPDATED_AT</div>
</div>
<div class="sts">
<div class="st"><div class="n">TOTAL_JOBS</div><div class="l">Total</div></div>
<div class="st hk"><div class="n">HK_COUNT</div><div class="l">HK</div></div>
<div class="st sh"><div class="n">SH_COUNT</div><div class="l">SH</div></div>
<div class="st sz"><div class="n">SZ_COUNT</div><div class="l">SZ</div></div>
<div class="st sg"><div class="n">SG_COUNT</div><div class="l">SG</div></div>
<div class="st"><div class="n">GZ_COUNT</div><div class="l">GZ</div></div>
</div>
<div class="flt" id="flt">
<button class="on" data-f="all">All (TOTAL_JOBS)</button>
<button data-f="A">A-tier</button>
<button data-f="B">B-tier</button>
<button data-f="hk">HK</button>
<button data-f="sh">SH</button>
<button data-f="sz">SZ</button>
<button data-f="strategy">Strategy</button>
<button data-f="product">Product</button>
<button data-f="ai">AI</button>
<button data-f="direct">🎯 Direct Apply</button>
<button data-f="easy">⚡ Easy Apply</button>
<button data-f="english">🌐 English</button>
<button data-f="needs_url">🔧 Needs URL Fix</button>
<button data-f="top20">🏆 Top 20</button>
</div>
<div style="margin:12px 0">
<input type="text" id="search-box" placeholder="🔍 Search jobs by title, company, location..." style="width:100%;max-width:600px;background:#1e293b;color:#e2e8f0;border:1px solid #334155;border-radius:8px;padding:10px 14px;font-size:0.9rem;outline:none" oninput="render(currentFilter)">
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
<option value="status">Application Status</option>
</select>
</div>
<div id="jobs"></div>
<div id="result-count" style="text-align:center;color:#94a3b8;font-size:0.8rem;margin:8px 0"></div>
<div class="upt">Last updated: UPDATED_AT</div>
<script>
const jobs = JOBS_JSON;
const STORAGE_KEY = 'career_os_app_status';
const NOTES_KEY = 'career_os_notes';
const STATUS_CYCLE = ['not_applied','applied','interviewing','offer','rejected','not_interested'];
const STATUS_LABELS = {not_applied:'📥 Not Applied',applied:'✅ Applied',interviewing:'🎤 Interviewing',offer:'🎉 Offer',rejected:'❌ Rejected',not_interested:'🙈 Not Interested'};

function loadStatus(){try{return JSON.parse(localStorage.getItem(STORAGE_KEY))||{}}catch(e){return{}}}
function saveStatus(s){localStorage.setItem(STORAGE_KEY,JSON.stringify(s))}
function loadNotes(){try{return JSON.parse(localStorage.getItem(NOTES_KEY))||{}}catch(e){return{}}}
function saveNotes(n){localStorage.setItem(NOTES_KEY,JSON.stringify(n))}
function getNote(jobId){return loadNotes()[jobId]||''}
function setNote(jobId,text){
  const n=loadNotes();
  if(text.trim())n[jobId]=text;else delete n[jobId];
  saveNotes(n);
}
function getStatus(j){const s=loadStatus();return s[j.job_id]||j.status||'not_applied'}
function toggleNotes(jobId){
  const el=document.getElementById('notes-'+jobId);
  if(el)el.classList.toggle('show');
}
function saveNote(jobId,text){
  setNote(jobId,text);
  const savedEl=document.getElementById('saved-'+jobId);
  if(savedEl){savedEl.classList.add('show');setTimeout(()=>savedEl.classList.remove('show'),1500)}
  const toggleEl=savedEl?.previousElementSibling;
  if(toggleEl){toggleEl.classList.toggle('has-notes',!!text.trim())}
}
function cycleStatus(j){
  const s=loadStatus();
  const cur=s[j.job_id]||j.status||'not_applied';
  const idx=STATUS_CYCLE.indexOf(cur);
  s[j.job_id]=STATUS_CYCLE[(idx+1)%STATUS_CYCLE.length];
  saveStatus(s);
  render(currentFilter);
  updateStats();
}
function updateStats(){
  const s=loadStatus();
  const counts={not_applied:0,applied:0,interviewing:0,offer:0,rejected:0,not_interested:0};
  jobs.forEach(j=>{const st=s[j.job_id]||j.status||'not_applied';counts[st]=(counts[st]||0)+1});
  const el=document.getElementById('status-stats');
  el.innerHTML=Object.entries(counts).map(([k,v])=>v>0?'<span class="st-stats">'+STATUS_LABELS[k]+': <b>'+v+'</b></span>':'').join('');
}
function gs(j) {
  const t = j.en_title || j.title || '';
  const c = j.company || '';
  const l = j.location_norm || j.location || '';
  return 'https://www.google.com/search?q=' + encodeURIComponent(t + ' ' + c + ' ' + l + ' job apply');
}
function ok(u) {
  if (!u) return false;
  return u.includes('viewjob') || u.includes('greenhouse.io/') || u.includes('lever.co/') || 
         u.includes('ashbyhq.com/') || u.includes('linkedin.com/jobs/view/') || u.includes('workday.com/') ||
         u.includes('myworkdayjobs.com/') || u.includes('/job/') && !u.endsWith('/jobs/') && !u.endsWith('/jobs') ||
         u.includes('/position/') || u.includes('/posting/');
}
let currentFilter = 'all';
let statusFilter = null;
function render(f) {
  currentFilter = f;
  // Update main filter buttons
  document.querySelectorAll('.flt button:not(.st-btn)').forEach(b=>b.classList.remove('on'));
  const mainBtn = document.querySelector('.flt button[data-f="'+f+'"]');
  if(mainBtn && !mainBtn.classList.contains('st-btn')) mainBtn.classList.add('on');
  
  const el = document.getElementById('jobs');
  const sortKey = document.getElementById('sort').value;
  let d = jobs;
  
  // Apply main filter
  if (f==='hk') d=jobs.filter(j=>(j.location_norm||j.location||'').toLowerCase().includes('hong kong'));
  else if (f==='sh') d=jobs.filter(j=>(j.location_norm||j.location||'').toLowerCase().includes('shanghai'));
  else if (f==='sz') d=jobs.filter(j=>(j.location_norm||j.location||'').toLowerCase().includes('shenzhen'));
  else if (f==='A') d=jobs.filter(j=>(j.quality_score||0)>=85);
  else if (f==='B') d=jobs.filter(j=>(j.quality_score||0)>=70&&(j.quality_score||0)<85);
  else if (f==='strategy') d=jobs.filter(j=>(j.role_type||'').toLowerCase().includes('strat'));
  else if (f==='product') d=jobs.filter(j=>(j.role_type||'').toLowerCase().includes('product'));
  else if (f==='ai') d=jobs.filter(j=>(j.title||'').toLowerCase().includes('ai'));
  else if (f==='direct') d=jobs.filter(j=>j.url_type==='direct');
  else if (f==='easy') d=jobs.filter(j=>j.app_difficulty==='easy');
  else if (f==='english') d=jobs.filter(j=>j.english_friendly===true);
  else if (f==='needs_url') d=jobs.filter(j=>j.url_type!=='direct');
  else if (f==='top20') d=jobs.filter(j=>j.top20===true);
  
  // Apply text search
  const searchBox = document.getElementById('search-box');
  if (searchBox && searchBox.value.trim()) {
    const q = searchBox.value.trim().toLowerCase();
    d = d.filter(j => {
      const searchable = [
        j.en_title || j.title || '',
        j.company || '',
        j.location_norm || j.location || '',
        j.summary || '',
        j.role_type || '',
        j.salary || ''
      ].join(' ').toLowerCase();
      return searchable.includes(q);
    });
  }
  
  // Apply status filter
  if (statusFilter) d=d.filter(j=>getStatus(j)===statusFilter);
  
  // Sort
  if (sortKey==='score') d.sort((a,b)=>(b.quality_score||0)-(a.quality_score||0));
  else if (sortKey==='date') d.sort((a,b)=>(b.scanned_date||'').localeCompare(a.scanned_date||''));
  else if (sortKey==='company') d.sort((a,b)=>(a.company||'').localeCompare(b.company||''));
  else if (sortKey==='location') d.sort((a,b)=>(a.location_norm||a.location||'').localeCompare(b.location_norm||b.location||''));
  else if (sortKey==='difficulty') {
    const order = {easy:0,medium:1,hard:2};
    d.sort((a,b)=>(order[a.app_difficulty]||2)-(order[b.app_difficulty]||2));
  }
  else if (sortKey==='status') {
    const order = {not_applied:0,applied:1,interviewing:2,offer:3,rejected:4,not_interested:5};
    d.sort((a,b)=>(order[getStatus(a)]||0)-(order[getStatus(b)]||0));
  }
  
  el.innerHTML = d.map(j=>{
    const s=j.quality_score||0;
    const t=s>=85?'A':s>=70?'B':'C';
    const ti=j.en_title||j.title||'Untitled';
    const co=j.company||'Unknown';
    const l=j.location_norm||j.location||'';
    const sc=j.source||'';
    const u=j.url||'';
    const sm=j.summary||'';
    const g=gs(j);
    const dk=ok(u);
    const au=dk?u:g;
    const ac=dk?'ap':'gs';
    const at=dk?'Apply →':'🔍 Search & Apply';
    const needsFix=j.url_type!=='direct';
    const isEn=j.english_friendly===true;
    const salary=j.salary?'<span class="salary">💰 '+j.salary+'</span>':'';
    const st=getStatus(j);
    const stBadge='<span class="status-badge st-'+st+'" onclick="event.stopPropagation();cycleStatus(jobs.find(x=>x.job_id===\''+j.job_id+'\'))" title="Click to change status">'+STATUS_LABELS[st]+'</span>';
    const note=getNote(j.job_id);
    const noteIcon=note?'📝':'💬';
    const noteClass=note?'has-notes':'';
    const noteHtml='<div class="notes-area"><button class="notes-toggle '+noteClass+'" onclick="toggleNotes(\''+j.job_id+'\')">'+noteIcon+' Notes</button><span class="notes-saved" id="saved-'+j.job_id+'">✓ saved</span><div class="notes-content" id="notes-'+j.job_id+'"><textarea class="notes-input" placeholder="Add a note..." oninput="saveNote(\''+j.job_id+'\',this.value)">'+note+'</textarea></div></div>';
    return '<div class="jc"><div class="t">'+ti+'<span class="ut ut-'+(j.url_type||'unknown')+'">'+{direct:'🎯 Direct',search:'🔍 Search',login_required:'🔒 Login'}[j.url_type||'unknown']+'</span>'+(needsFix?'<span class="url-fix">🔧 URL Fix Needed</span>':'')+(isEn?'<span class="en">🌐 EN</span>':'')+'</div><div class="co">'+co+' '+stBadge+'</div>'+(sm?'<div class="sm">'+sm.substring(0,150)+(sm.length>150?'...':'')+'</div>':'')+'<div class="mt"><span class="lc">'+l+'</span><span class="sc">'+sc+'</span><span class="bg bg-'+t.toLowerCase()+'">'+t+' '+s+'</span>'+salary+(j.app_difficulty?'<span>⚡ '+j.app_difficulty+'</span>':'')+'</div><div class="lk"><a href="'+au+'" target="_blank" class="'+ac+'">'+at+'</a>'+(dk?'<a href="'+g+'" target="_blank" class="gs">🔍 Google</a>':'')+'</div>'+noteHtml+'</div>';
  }).join('');
  // Update result count
  const countEl = document.getElementById('result-count');
  if (countEl) {
    const searchBox = document.getElementById('search-box');
    const hasSearch = searchBox && searchBox.value.trim();
    countEl.textContent = d.length + ' of ' + jobs.length + ' jobs' + (hasSearch ? ' matching "' + searchBox.value.trim() + '"' : '');
  }
}
// Status filter buttons
document.querySelectorAll('#status-flt .st-btn').forEach(b=>{
  b.addEventListener('click',()=>{
    document.querySelectorAll('#status-flt .st-btn').forEach(x=>x.classList.remove('on'));
    b.classList.add('on');
    const f=b.dataset.f;
    if(f==='st_all_status'){statusFilter=null;render(currentFilter);}
    else{statusFilter=f.replace('st_','');render(currentFilter);}
  });
});
document.querySelectorAll('.flt button:not(.st-btn)').forEach(b=>{
  b.addEventListener('click',()=>{
    document.querySelectorAll('.flt button:not(.st-btn)').forEach(x=>x.classList.remove('on'));
    b.classList.add('on');
    render(b.dataset.f);
  });
});
document.getElementById('sort').addEventListener('change',()=>{
  render(currentFilter);
});
updateStats();
render('all');
</script>
</body>
</html>'''

html = html.replace('TOTAL_JOBS', str(total))
html = html.replace('TOTAL_SCANNED', str(len(jobs)))
html = html.replace('DIRECT_COUNT', str(direct_count))
html = html.replace('UPDATED_AT', now)
html = html.replace('HK_COUNT', str(hk))
html = html.replace('SH_COUNT', str(sh))
html = html.replace('SZ_COUNT', str(sz))
html = html.replace('SG_COUNT', str(sg))
html = html.replace('GZ_COUNT', str(gz))
html = html.replace('JOBS_JSON', jobs_json)

with open('dashboard.html', 'w') as f:
    f.write(html)
print(f'Dashboard: {total} jobs, {direct_count} direct, {needs_url_fix} need URL fix, {os.path.getsize("dashboard.html")//1024}KB')
