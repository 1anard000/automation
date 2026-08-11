import json
with open("/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json") as f:
    data = json.load(f)
print(f"Jobs count: {len(data)}")
if len(data) < 400:
    print("ERROR: Less than 400 jobs")
    exit(1)
print("OK")
