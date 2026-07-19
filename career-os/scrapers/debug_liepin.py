#!/usr/bin/env python3
"""Try different Liepin search approaches."""
import re

with open('/tmp/liepin.html', 'r', encoding='utf-8') as f:
    html = f.read()

print(f'HTML length: {len(html)}')

# Look for any job-related content
job_indicators = ['产品经理', '职位', '招聘', 'job', 'position', 'salary', 'salaryRange']
for indicator in job_indicators:
    count = html.count(indicator)
    print(f'  "{indicator}": {count} occurrences')

# Look for script tags that might contain job data
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
print(f'\nFound {len(scripts)} script tags')

# Look for __NEXT_DATA__ or similar
next_data = re.search(r'__NEXT_DATA__\s*=\s*({.*?})</script>', html, re.DOTALL)
if next_data:
    print('Found __NEXT_DATA__')
    
# Look for window.__INITIAL_STATE__ or similar
initial_state = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.DOTALL)
if initial_state:
    print('Found __INITIAL_STATE__')

# Print first 2000 chars of HTML to understand structure
print('\n--- First 2000 chars ---')
print(html[:2000])
print('\n--- Last 1000 chars ---')
print(html[-1000:])
