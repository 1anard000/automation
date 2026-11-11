#!/usr/bin/env python3
"""Build today's agent-discovered-jobs.json from pre-fetched results."""
import json, re, hashlib
from datetime import date

TODAY = date.today().isoformat()
BASE = '/Users/iancolrick/.openclaw/workspace/career-os'
MASTER = f'{BASE}/OKComputer_职位搜索清单/jobs-all.json'
AGENT = f'{BASE}/scrapers/agent-discovered-jobs.json'
GH = f'{BASE}/scrapers/greenhouse-results.json'
BOSS = f'{BASE}/scrapers/boss-zhilian-discovery-results.json'
INDEED = f'{BASE}/scrapers/indeed-jobsdb-results.json'
ASHBY = f'{BASE}/scrapers/ashby-results.json'

with open(MASTER) as f:
    master = json.load(f)
master_urls = set(j.get('url','') for j in master)
master_tc = set((j.get('title','') + '||' + j.get('company','')).lower() for j in master)

def jid(url, title):
    return hashlib.sha1((url + title).encode('utf-8')).hexdigest()[:12]

def norm_loc(loc):
    if not loc: return ''
    l = loc.lower()
    if 'hong kong' in l: return 'Hong Kong'
    if 'singapore' in l: return 'Singapore'
    if 'shenzhen' in l: return 'Shenzhen'
    if 'guangzhou' in l: return 'Guangzhou'
    if 'shanghai' in l: return 'Shanghai'
    if 'tokyo' in l: return 'Tokyo'
    if 'seoul' in l: return 'Seoul'
    if 'taipei' in l: return 'Taipei'
    return loc.strip()

def salary_high(s):
    if not s: return 0
    s2 = re.sub(r'[·.]\d+薪', '', str(s))
    m = re.search(r'(\d+)[-–](\d+)K', s2, re.I)
    if m: return int(m.group(2))
    return 0

new_records = []

# === Greenhouse ===
with open(GH) as f:
    gh = json.load(f)
crypto_re = re.compile(r'\b(dex|defi|trading bot|web3|copy trading|on.?chain|token|crypto|blockchain|nft)\b', re.I)
exclude_re = re.compile(r'\b(designer|engineer|developer|sales|account executive|business development|customer success|support|recruiter|hr|financial analyst|accountant|legal|paralegal|copywriter|data scientist)\b', re.I)
seniority_re = re.compile(r'\b(vp|vice president|svp|evp|chief|cto|cfo|ceo|coo|cmo|president|head of)\b', re.I)
apac_kw = ['hong kong', 'singapore', 'shenzhen', 'guangzhou', 'shanghai', 'tokyo', 'seoul', 'taipei', 'bangkok', 'jakarta', 'manila', 'kuala lumpur', 'apac', 'asia pacific', 'southeast asia']

gh_added = 0
for j in gh:
    url = j.get('url','')
    title = j.get('title','')
    if url in master_urls: continue
    if (title + '||' + j.get('company','')).lower() in master_tc: continue
    loc_raw = j.get('location') or ''
    loc = loc_raw.lower()
    if not any(k in loc for k in apac_kw): continue
    if crypto_re.search(title): continue
    if exclude_re.search(title): continue
    if seniority_re.search(title): continue
    rec = {
        'title': title,
        'company': j.get('company',''),
        'location': loc_raw,
        'location_norm': norm_loc(loc_raw),
        'url': url,
        'salary': j.get('salary',''),
        'source': 'greenhouse',
        'scanned_date': TODAY,
        'role_type': j.get('role_type',''),
        'english_friendly': True,
        'has_direct_link': True,
        'url_type': 'greenhouse_board',
        'job_id': jid(url, title),
        'status': 'not_applied',
        'status_date': TODAY,
        'last_touch_date': TODAY,
        'quality_score': None,
        'quality_tier': '',
        'low_quality': False,
        'category': 'other',
    }
    new_records.append(rec)
    gh_added += 1

# === Boss直聘 ===
with open(BOSS) as f:
    boss = json.load(f)
target_locs = ['shenzhen', 'hong kong', 'guangzhou', 'shanghai', 'singapore']
boss_added = 0
for j in boss:
    url = j.get('url','')
    title = j.get('title','')
    if url in master_urls: continue
    if (title + '||' + j.get('company','')).lower() in master_tc: continue
    loc_raw = j.get('location') or ''
    loc = loc_raw.lower()
    if not any(t in loc for t in target_locs): continue
    s = j.get('salary','')
    high = salary_high(s)
    if 'hong kong' in loc:
        floor = 60
    elif 'singapore' in loc:
        floor = 10
    else:
        floor = 30
    if high < floor: continue
    rec = {
        'title': title,
        'company': j.get('company',''),
        'location': loc_raw,
        'location_norm': norm_loc(loc_raw),
        'url': url,
        'salary': s,
        'source': 'boss-zhilian-websearch',
        'scanned_date': TODAY,
        'role_type': j.get('role_type','Product Management'),
        'english_friendly': False,
        'has_direct_link': True,
        'url_type': 'zhipin_listing',
        'job_id': jid(url, title),
        'status': 'not_applied',
        'status_date': TODAY,
        'last_touch_date': TODAY,
        'quality_score': None,
        'quality_tier': '',
        'low_quality': False,
        'category': 'other',
    }
    new_records.append(rec)
    boss_added += 1

# === JobsDB / Indeed ===
with open(INDEED) as f:
    indeed = json.load(f)
indeed_added = 0
for j in indeed:
    url = j.get('url','')
    title = j.get('title','')
    if url in master_urls: continue
    # Skip listing pages
    if '/jobs' in url and 'viewjob' not in url and 'Digital-Payments' not in url:
        continue
    # Only keep the Payments Director listing (specific role)
    if 'Digital-Payments' not in url: continue
    loc_raw = j.get('location') or ''
    rec = {
        'title': title,
        'company': j.get('company',''),
        'location': loc_raw,
        'location_norm': norm_loc(loc_raw),
        'url': url,
        'salary': j.get('salary',''),
        'source': 'jobsdb',
        'scanned_date': TODAY,
        'role_type': j.get('role_type','Product Management'),
        'english_friendly': True,
        'has_direct_link': True,
        'url_type': 'jobsdb_listing',
        'job_id': jid(url, title),
        'status': 'not_applied',
        'status_date': TODAY,
        'last_touch_date': TODAY,
        'quality_score': None,
        'quality_tier': '',
        'low_quality': False,
        'category': 'other',
    }
    new_records.append(rec)
    indeed_added += 1

# === Ashby ===
with open(ASHBY) as f:
    ashby = json.load(f)
ashby_added = 0
for j in ashby:
    url = j.get('url','')
    title = j.get('title','')
    if url in master_urls: continue
    loc_raw = j.get('location') or ''
    loc = loc_raw.lower()
    if 'tokyo' not in loc and 'japan' not in loc: continue
    # Sales Strategy & Operations Manager, APAC (Notion, Tokyo)
    rec = {
        'title': title,
        'company': j.get('company',''),
        'location': loc_raw,
        'location_norm': norm_loc(loc_raw),
        'url': url,
        'salary': j.get('salary',''),
        'source': 'ashby',
        'scanned_date': TODAY,
        'role_type': j.get('role_type','Strategy/Ops'),
        'english_friendly': True,
        'has_direct_link': True,
        'url_type': 'ashby_board',
        'job_id': jid(url, title),
        'status': 'not_applied',
        'status_date': TODAY,
        'last_touch_date': TODAY,
        'quality_score': None,
        'quality_tier': '',
        'low_quality': False,
        'category': 'other',
    }
    new_records.append(rec)
    ashby_added += 1

# Load existing agent, remove today's records (re-idempotent), append new
with open(AGENT) as f:
    agent = json.load(f)
agent = [j for j in agent if j.get('scanned_date') != TODAY]
agent.extend(new_records)
with open(AGENT, 'w') as f:
    json.dump(agent, f, ensure_ascii=False, indent=2)

print(f'Greenhouse new: {gh_added}')
print(f'Boss直聘 new: {boss_added}')
print(f'JobsDB new: {indeed_added}')
print(f'Ashby new: {ashby_added}')
print(f'Total new: {len(new_records)}')
print(f'Total agent: {len(agent)}')
