import json, sys
try:
    with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json') as f:
        data = json.load(f)
    count = len(data)
    if count > 400:
        print(f"PASS:{count}")
    else:
        print(f"FAIL:only_{count}_jobs")
except Exception as e:
    print(f"FAIL:{e}")
