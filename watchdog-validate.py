import json
import sys

try:
    with open("/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json") as f:
        data = json.load(f)
    count = len(data)
    print(f"Jobs count: {count}")
    if count <= 400:
        print(f"ERROR: Only {count} jobs, need >400")
        sys.exit(1)
    print("PASS")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
