import json
path = "/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json"
with open(path) as f:
    data = json.load(f)
jobs = data if isinstance(data, list) else data.get("jobs", data.get("positions", []))
print(f"JOB_COUNT={len(jobs)}")
if len(jobs) <= 400:
    print("FAIL: <=400 jobs")
else:
    print("PASS: >400 jobs")
