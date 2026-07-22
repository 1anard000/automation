import json, sys
try:
    with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json') as f:
        d = json.load(f)
    print(f'VALID, {len(d)} jobs')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
