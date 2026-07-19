#!/usr/bin/env python3
"""Parse Tencent career search results."""
import re, json, hashlib
from datetime import datetime

with open('/tmp/tencent.html', 'r', encoding='utf-8') as f:
    html = f.read()

print(f'HTML length: {len(html)}')

# Look for job data in scripts or structured elements
# Try finding JSON data
json_matches = re.findall(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.DOTALL)
if json_matches:
    print('Found __INITIAL_STATE__')
    try:
        data = json.loads(json_matches[0])
        print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
    except:
        print('Failed to parse JSON')

# Try other patterns
data_patterns = [
    r'var\s+jobList\s*=\s*(\[.*?\]);',
    r'"positionList"\s*:\s*(\[.*?\])',
    r'"jobs"\s*:\s*(\[.*?\])',
]

for pattern in data_patterns:
    matches = re.findall(pattern, html, re.DOTALL)
    if matches:
        print(f'Found pattern: {pattern[:30]}...')
        for m in matches[:2]:
            print(m[:500])

# Look for job titles in the HTML
job_titles = re.findall(r'<[^>]*class="[^"]*job[^"]*"[^>]*>(.*?)</[^>]*>', html, re.DOTALL)
print(f'\nFound {len(job_titles)} elements with "job" in class')
for t in job_titles[:10]:
    clean = re.sub(r'<[^>]+>', '', t).strip()
    if clean:
        print(f'  {clean}')

# Look for any links to job details
job_links = re.findall(r'href="([^"]*position[^"]*)"', html)
print(f'\nFound {len(job_links)} position links')
for link in job_links[:10]:
    print(f'  {link}')

# Print a sample of the HTML body
body_start = html.find('<body')
if body_start > 0:
    body = html[body_start:body_start+3000]
    print('\n--- Body sample ---')
    print(body)
