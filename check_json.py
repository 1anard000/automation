import json
import sys

try:
    with open("/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json") as f:
        data = json.load(f)
    count = len(data)
    if count > 400:
        print(f"OK:{count}")
    else:
        print(f"TOO_FEW:{count}")
except json.JSONDecodeError as e:
    print(f"INVALID_JSON:{e}")
except Exception as e:
    print(f"ERROR:{e}")
    sys.exit(1)
