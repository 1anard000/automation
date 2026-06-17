import json
from datetime import datetime, timedelta
from collections import Counter

with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json', 'r') as f:
    data = json.load(f)

jobs = data if isinstance(data, list) else data.get('jobs', data.get('data', []))

cities = Counter()
grades = Counter()
platforms = Counter()
statuses = Counter()
role_types = Counter()
recent_jobs = []
top_jobs = []
action_items = []
followup_items = []

today = datetime.now()

for job in jobs:
    city = job.get('city', job.get('location', 'Unknown'))
    grade = job.get('grade', job.get('rating', 'N/A'))
    platform = job.get('platform', job.get('source', 'Unknown'))
    status = job.get('status', 'unknown')
    role_type = job.get('role_type', 'N/A')
    
    cities[city] += 1
    grades[grade] += 1
    platforms[platform] += 1
    statuses[status] += 1
    role_types[role_type] += 1
    
    # Check for recent jobs (last 24h) via scanned_date or status_date
    for date_field in ['scanned_date', 'status_date', 'last_touch_date']:
        date_str = job.get(date_field, '')
        if date_str:
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                if dt > today - timedelta(hours=24):
                    recent_jobs.append(job)
                    break
            except:
                pass
    
    # Top grade A-1/A-2 jobs
    if grade in ['A-1', 'A-2']:
        top_jobs.append(job)
    
    # Action items
    if status in ['needs_followup', 'followup_needed', 'pending', 'interview_scheduled', 'screening']:
        action_items.append(job)
    
    # Stale jobs needing follow-up
    last_touch = job.get('last_touch_date', '')
    if last_touch and status not in ['applied', 'rejected', 'withdrawn', 'not_applied']:
        try:
            dt = datetime.strptime(last_touch, '%Y-%m-%d')
            if (today - dt).days > 7:
                followup_items.append(job)
        except:
            pass

# Output
print(json.dumps({
    'total': len(jobs),
    'new_today': len(recent_jobs),
    'cities': dict(cities.most_common(10)),
    'grades': dict(sorted(grades.items())),
    'platforms': dict(platforms.most_common(10)),
    'statuses': dict(statuses.most_common(15)),
    'role_types': dict(role_types.most_common(10)),
    'top_jobs': [{'title': j.get('title','?'), 'company': j.get('company','?'), 'city': j.get('city', j.get('location','?')), 'grade': j.get('grade','?'), 'status': j.get('status','?'), 'salary': j.get('salary','?'), 'url': j.get('url','?')} for j in top_jobs[:5]],
    'recent_jobs': [{'title': j.get('title','?'), 'company': j.get('company','?'), 'grade': j.get('grade','?'), 'scanned': j.get('scanned_date','')} for j in recent_jobs[:10]],
    'action_items': [{'title': j.get('title','?'), 'company': j.get('company','?'), 'status': j.get('status','?'), 'last_touch': j.get('last_touch_date','')} for j in action_items[:10]],
    'stale_followup': [{'title': j.get('title','?'), 'company': j.get('company','?'), 'status': j.get('status','?'), 'last_touch': j.get('last_touch_date','?')} for j in followup_items[:10]],
}))
