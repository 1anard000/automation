import json

with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json', 'r') as f:
    data = json.load(f)

print(f'Total jobs in database: {len(data)}')
print('---URLS---')
for j in data:
    url = j.get('url', '')
    title = j.get('title', '')
    company = j.get('company', '')
    print(f'{company} | {title} | {url}')
