#!/usr/bin/env python3
import json
jobs = json.load(open('OKComputer_职位搜索清单/jobs-all.json'))
print(f'Total jobs: {len(jobs)}')
sources = {}
for j in jobs:
    src = j.get('source', 'unknown')
    sources[src] = sources.get(src, 0) + 1
for s, c in sorted(sources.items(), key=lambda x: -x[1]):
    print(f'  {s}: {c}')
# Count new today
today = [j for j in jobs if j.get('scanned_date') == '2026-08-01']
print(f'Scanned today: {len(today)}')
# Count aligned
from rebuild_dashboard import is_aligned
aligned = [j for j in jobs if is_aligned(j)]
print(f'Aligned jobs: {len(aligned)}')
