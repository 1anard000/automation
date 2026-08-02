import json
import sys

path = "/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json"
try:
    with open(path) as f:
        data = json.load(f)
    count = len(data)
    if count > 400:
        print(f"PASS: {count} jobs")
    else:
        print(f"FAIL: only {count} jobs (need >400)")
        sys.exit(1)
except json.JSONDecodeError as e:
    print(f"FAIL: invalid JSON - {e}")
    sys.exit(2)
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(3)
