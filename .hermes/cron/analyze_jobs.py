#!/usr/bin/env python3
import json
from datetime import datetime, timedelta
from collections import Counter

with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json', 'r') as f:
    jobs = json.load(f)

today = datetime.now().strftime('%Y-%m-%d')
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

total = len(jobs)

cities = Counter(j.get('location', 'Unknown') or 'Unknown' for j in jobs)
grades = Counter(j.get('grade', 'Unknown') or 'Unknown' for j in jobs)
platforms = Counter(j.get('platform', j.get('source', 'Unknown')) or 'Unknown' for j in jobs)
role_types = Counter(j.get('role_type', 'Unknown') or 'Unknown' for j in jobs)
categories = Counter(j.get('category', 'Unknown') or 'Unknown' for j in jobs)

new_today = [j for j in jobs if j.get('scanned_date') == today]
applied = [j for j in jobs if j.get('applied_date')]
follow_up = [j for j in jobs if j.get('status') and j.get('status') not in ('not_applied',)]
low_q = [j for j in jobs if j.get('low_quality')]
qb_reject = [j for j in jobs if j.get('quality_bar_reject')]
eng_friendly = [j for j in jobs if j.get('english_friendly')]

top_candidates = [
    j for j in jobs
    if j.get('grade', '').startswith('A-')
    and not j.get('low_quality', False)
    and not j.get('quality_bar_reject', False)
    and j.get('quality_score', 0) > 0
]
top_candidates.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
top5 = top_candidates[:5]

result = {
    "total": total,
    "new_today": len(new_today),
    "applied": len(applied),
    "follow_up": len(follow_up),
    "low_quality": len(low_q),
    "qb_reject": len(qb_reject),
    "eng_friendly": len(eng_friendly),
    "today_date": today,
    "cities": dict(cities.most_common(15)),
    "grades": dict(sorted(grades.items())),
    "platforms": dict(platforms.most_common(10)),
    "role_types": dict(role_types.most_common(10)),
    "categories": dict(categories.most_common(10)),
    "top5": [
        {
            "title": j.get('en_title') or j.get('title', 'N/A'),
            "company": j.get('company', '') or 'Unknown',
            "location": j.get('location', 'N/A'),
            "grade": j.get('grade', ''),
            "score": j.get('quality_score', 0),
            "salary": j.get('salary', 'Not listed'),
            "platform": j.get('platform', j.get('source', '')),
        }
        for j in top5
    ],
    "new_today_jobs": [
        {
            "title": j.get('en_title') or j.get('title', 'N/A'),
            "company": j.get('company', '') or 'Unknown',
            "location": j.get('location', 'N/A'),
            "grade": j.get('grade', ''),
            "score": j.get('quality_score', 0),
        }
        for j in new_today[:10]
    ],
}

print(json.dumps(result, ensure_ascii=False, indent=2))
