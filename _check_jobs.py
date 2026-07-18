import json
with open("/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json") as f:
    data = json.load(f)
print(f"Valid JSON: {isinstance(data, list)}")
print(f"Job count: {len(data)}")
