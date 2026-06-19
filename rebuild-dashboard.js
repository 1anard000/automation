const STORAGE_KEY = 'career_os_app_status';
const NOTES_KEY = 'career_os_notes';
const STATUS_CYCLE = ['not_applied','applied','interviewing','offer','rejected','not_interested'];
const STATUS_LABELS = {not_applied:'📥 Not Applied',applied:'✅ Applied',interviewing:'🎤 Interviewing',offer:'🎉 Offer',rejected:'❌ Rejected',not_interested:'🙈 Not Interested'};
function loadStatus(){try{return JSON.parse(localStorage.getItem(STORAGE_KEY))||{}}catch(e){return{}}}
function saveStatus(s){localStorage.setItem(STORAGE_KEY,JSON.stringify(s))}
function loadNotes(){try{return JSON.parse(localStorage.getItem(NOTES_KEY))||{}}catch(e){return{}}}
function saveNotes(n){localStorage.setItem(NOTES_KEY,JSON.stringify(n))}
function getNote(id){return loadNotes()[id]||''}
function setNote(id,text){const n=loadNotes();if(text.trim())n[id]=text;else delete n[id];saveNotes(n)}
function getStatus(j){const s=loadStatus();return s[j.job_id]||j.status||'not_applied'}
function toggleNotes(id){const el=document.getElementById('notes-'+id);if(el)el.classList.toggle('show')}
function saveNote(id,text){setNote(id,text);const e=document.getElementById('saved-'+id);if(e){e.classList.add('show');setTimeout(()=>e.classList.remove('show'),1500)}}
function cycleStatus(jobId){const s=loadStatus();const cur=s[jobId]||'not_applied';const idx=STATUS_CYCLE.indexOf(cur);s[jobId]=STATUS_CYCLE[(idx+1)%STATUS_CYCLE.length];saveStatus(s);render(currentFilter);updateStats()}
function updateStats(){const s=loadStatus();const c={not_applied:0,applied:0,interviewing:0,offer:0,rejected:0,not_interested:0};jobs.forEach(j=>{const st=s[j.job_id]||j.status||'not_applied';c[st]=(c[st]||0)+1});const el=document.getElementById('status-stats');if(el)el.innerHTML=Object.entries(c).map(([k,v])=>v>0?'<span class="st-stats">'+STATUS_LABELS[k]+': <b>'+v+'</b></span>':'').join('')}
function gs(j){return 'https://www.google.com/search?q='+encodeURIComponent((j.en_title||j.title||'')+' '+(j.company||'')+' '+(j.location_norm||j.location||'')+' job apply')}
function ok(u){if(!u)return false;return u.includes('viewjob')||u.includes('greenhouse.io/')||u.includes('lever.co/')||u.includes('ashbyhq.com/')||u.includes('linkedin.com/jobs/view/')||u.includes('workday.com/')||u.includes('myworkdayjobs.com/')||u.includes('/job/')&&!u.endsWith('/jobs/')&&!u.endsWith('/jobs')||u.includes('/position/')||u.includes('/posting/')}
let currentFilter='all';let statusFilter=null;
function render(f){
  currentFilter=f;
  document.querySelectorAll('.flt button:not(.st-btn)').forEach(b=>b.classList.remove('on'));
  const mb=document.querySelector('.flt button[data-f="'+f+'"]');
  if(mb&&!mb.classList.contains('st-btn'))mb.classList.add('on');
  const el=document.getElementById('jobs');
  const sk=document.getElementById('sort').value;
  let d=jobs;
  if(f==='hk')d=jobs.filter(j=>(j.location_norm||j.location||'').toLowerCase().includes('hong kong'));
  else if(f==='sh')d=jobs.filter(j=>(j.location_norm||j.location||'').toLowerCase().includes('shanghai'));
  else if(f==='sz')d=jobs.filter(j=>(j.location_norm||j.location||'').toLowerCase().includes('shenzhen'));
  else if(f==='sg')d=jobs.filter(j=>(j.location_norm||j.location||'').toLowerCase().includes('singapore'));
  else if(f==='A')d=jobs.filter(j=>(j.quality_score||0)>=85);
  else if(f==='B')d=jobs.filter(j=>(j.quality_score||0)>=70&&(j.quality_score||0)<85);
  else if(f==='strategy')d=jobs.filter(j=>(j.role_type||'').toLowerCase().includes('strat'));
  else if(f==='product')d=jobs.filter(j=>(j.role_type||'').toLowerCase().includes('product'));
  else if(f==='bizops')d=jobs.filter(j=>{
    const t=((j.title||'')+' '+(j.role_type||'')+' '+(j.summary||'')).toLowerCase();
    return t.includes('business operations')||t.includes('bizops')||t.includes('chief of staff');
  });
  else if(f==='gm')d=jobs.filter(j=>{
    const t=((j.role_type||'')+' '+(j.title||'')).toLowerCase();
    return t.includes('gm')||t.includes('general manager')||t.includes('country manager');
  });
  else if(f==='ai')d=jobs.filter(j=>(j.title||'').toLowerCase().includes('ai'));
  else if(f==='fintech')d=jobs.filter(j=>(j.category||'').toLowerCase().includes('fintech'));
  else if(f==='crossborder')d=jobs.filter(j=>{
    const t=((j.category||'')+' '+(j.role_type||'')+' '+(j.title||'')+' '+(j.summary||'')).toLowerCase();
    return t.includes('cross-border')||t.includes('cross border')||t.includes('marketplace')||t.includes('expansion');
  });
  else if(f==='growth')d=jobs.filter(j=>{
    const t=((j.category||'')+' '+(j.role_type||'')+' '+(j.title||'')).toLowerCase();
    return t.includes('growth')||t.includes('expansion');
  });
  else if(f==='senior')d=jobs.filter(j=>(j.category||'').toLowerCase().includes('senior_pm')||(j.title||'').toLowerCase().includes('principal product')||(j.title||'').toLowerCase().includes('lead product')||(j.title||'').toLowerCase().includes('lead product manager'));
  else if(f==='direct')d=jobs.filter(j=>j.url_type==='direct');
  else if(f==='easy')d=jobs.filter(j=>j.app_difficulty==='easy');
  else if(f==='english')d=jobs.filter(j=>j.english_friendly===true);
  else if(f==='visa_likely')d=jobs.filter(j=>(j.location_norm||j.location||'').toLowerCase().includes('singapore')&&(j._company_tier==='bigtech'||j._company_tier==='growth'));
  else if(f==='needs_url')d=jobs.filter(j=>j.url_type!=='direct');
  else if(f==='top20')d=jobs.filter(j=>j.top20===true);
  else if(f==='best_fit')d=jobs.filter(j=>(j._fit_score||0)>=70);
  else if(f==='strong_fit')d=jobs.filter(j=>(j._fit_score||0)>=55&&(j._fit_score||0)<70);
  else if(f==='bigtech')d=jobs.filter(j=>j._company_tier==='bigtech');
  else if(f==='company_growth')d=jobs.filter(j=>j._company_tier==='growth');
  else if(f==='enterprise')d=jobs.filter(j=>j._company_tier==='enterprise');
  else if(f==='startup')d=jobs.filter(j=>j._company_tier==='startup');
  else if(f==='sal_high')d=jobs.filter(j=>j._salary_tier==='high');
  else if(f==='sal_midhigh')d=jobs.filter(j=>j._salary_tier==='midhigh');
  else if(f==='sal_mid')d=jobs.filter(j=>j._salary_tier==='mid');
  else if(f==='sal_low')d=jobs.filter(j=>j._salary_tier==='low');
  else if(f==='sal_none')d=jobs.filter(j=>j._salary_tier==='none');
  const sb=document.getElementById('search-box');
  if(sb&&sb.value.trim()){const q=sb.value.trim().toLowerCase();d=d.filter(j=>[j.en_title||j.title||'',j.company||'',j.location_norm||j.location||'',j.summary||'',j.role_type||'',j.salary||''].join(' ').toLowerCase().includes(q))}
  if(statusFilter)d=d.filter(j=>getStatus(j)===statusFilter);
  if(sk==='score')d.sort((a,b)=>(b.quality_score||0)-(a.quality_score||0));
  else if(sk==='date')d.sort((a,b)=>(b.scanned_date||'').localeCompare(a.scanned_date||''));
  else if(sk==='company')d.sort((a,b)=>(a.company||'').localeCompare(b.company||''));
  else if(sk==='location')d.sort((a,b)=>(a.location_norm||a.location||'').localeCompare(b.location_norm||b.location||''));
  else if(sk==='difficulty'){const o={easy:0,medium:1,hard:2};d.sort((a,b)=>(o[a.app_difficulty]||2)-(o[b.app_difficulty]||2))}
  else if(sk==='salary')d.sort((a,b)=>(b._salary_usd||0)-(a._salary_usd||0));
  else if(sk==='tier'){const o={bigtech:0,growth:1,enterprise:2,startup:3};d.sort((a,b)=>((a._company_tier in o)?o[a._company_tier]:3)-((b._company_tier in o)?o[b._company_tier]:3))}
  else if(sk==='apply_ease'){const o={direct:0,search:1,login_required:2};d.sort((a,b)=>((a.url_type in o)?o[a.url_type]:2)-((b.url_type in o)?o[b.url_type]:2))}
  else if(sk==='fit')d.sort((a,b)=>(b._fit_score||0)-(a._fit_score||0));
  el.innerHTML=d.map(j=>{
    var s=j.quality_score||0,t=s>=85?'A':s>=70?'B':'C';
    var ti=j.en_title||j.title||'Untitled',co=j.company||'Unknown',l=j.location_norm||j.location||'',sc=j.source||'',u=j.url||'',sm=j.summary||'';
    var g=gs(j),dk=ok(u),au=dk?u:g,ac=dk?'ap':'gs',at=dk?'Apply \u2192':'🔍 Search & Apply';
    var nf=j.url_type!=='direct',ie=j.english_friendly===true;
    var sal=j.salary?'<span class="salary">💰 '+j.salary+'</span>':'';
    var st=getStatus(j);
    var fitScore=j._fit_score||0;
    var fitCls=fitScore>=70?'fit-excellent':fitScore>=55?'fit-strong':fitScore>=40?'fit-moderate':'fit-weak';
    var fitBadge='<span class="fit-badge '+fitCls+'">🎯 '+fitScore+'</span>';
    var stBadge='<span class="status-badge st-'+st+'" data-job-id="'+j.job_id+'" title="Click to change status">'+STATUS_LABELS[st]+'</span>';
    var note=getNote(j.job_id),ni=note?'📝':'💬',nc=note?'has-notes':'';
    var nh='<div class="notes-area"><button class="notes-toggle '+nc+'" data-toggle-notes="'+j.job_id+'">'+ni+' Notes</button><span class="notes-saved" id="saved-'+j.job_id+'">✓ saved</span><div class="notes-content" id="notes-'+j.job_id+'"><textarea class="notes-input" placeholder="Add a note..." data-save-note="'+j.job_id+'">'+note+'</textarea></div></div>';
    return '<div class="jc"><div class="t">'+ti+'<span class="ut ut-'+(j.url_type||'unknown')+'">'+{direct:'🎯 Direct',search:'🔍 Search',login_required:'🔒 Login'}[j.url_type||'unknown']+'</span>'+(nf?'<span class="url-fix">🔧 URL Fix Needed</span>':'')+(ie?'<span class="en">🌐 EN</span>':'')+'</div><div class="co">'+co+' <span class="tier tier-'+(j._company_tier||'startup')+'">'+((j._company_tier||'startup').charAt(0).toUpperCase()+(j._company_tier||'startup').slice(1))+'</span> '+fitBadge+' '+stBadge+'</div>'+(sm?'<div class="sm">'+sm.substring(0,150)+(sm.length>150?'...':'')+'</div>':'')+'<div class="mt"><span class="lc">'+l+'</span><span class="sc">'+sc+'</span><span class="bg bg-'+t.toLowerCase()+'">'+t+' '+s+'</span>'+sal+(j.app_difficulty?'<span>⚡ '+j.app_difficulty+'</span>':'')+'</div><div class="lk"><a href="'+au+'" target="_blank" class="'+ac+'">'+at+'</a>'+(dk?'<a href="'+g+'" target="_blank" class="gs">🔍 Google</a>':'')+'</div>'+nh+'</div>';
  }).join('');
  var ce=document.getElementById('result-count');
  if(ce){var hasSb=sb&&sb.value.trim();ce.textContent=d.length+' of '+jobs.length+' jobs'+(hasSb?' matching "'+sb.value.trim()+'"':'')}
}
document.querySelectorAll('#status-flt .st-btn').forEach(b=>{b.addEventListener('click',()=>{document.querySelectorAll('#status-flt .st-btn').forEach(x=>x.classList.remove('on'));b.classList.add('on');const f=b.dataset.f;if(f==='st_all_status'){statusFilter=null;render(currentFilter)}else{statusFilter=f.replace('st_','');render(currentFilter)}})});
document.querySelectorAll('.flt button:not(.st-btn)').forEach(b=>{b.addEventListener('click',()=>{document.querySelectorAll('.flt button:not(.st-btn)').forEach(x=>x.classList.remove('on'));b.classList.add('on');render(b.dataset.f)})});
document.getElementById('sort').addEventListener('change',()=>{render(currentFilter)});
document.addEventListener('click',e=>{
  const badge=e.target.closest('.status-badge[data-job-id]');
  if(badge){cycleStatus(badge.dataset.jobId);return}
  const toggle=e.target.closest('[data-toggle-notes]');
  if(toggle){toggleNotes(toggle.dataset.toggleNotes);return}
});
document.addEventListener('input',e=>{
  if(e.target.dataset.saveNote)saveNote(e.target.dataset.saveNote,e.target.value);
});
updateStats();
render('all');
