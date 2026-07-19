#!/usr/bin/env python3
import json
r = json.load(open('/tmp/greenhouse_results.json'))
print(f"Total new jobs: {r['new_count']}")
for j in r['new_jobs']:
    print(f"  {j['title']} | {j['company']} | {j['location']} | {j['url']}")
print(f"\nErrors: {r['errors']}")
