import json, sys
try:
    with open("/Users/iancolrick/.openclaw/workspace/OKComputer_\u804c\u4f4d\u641c\u7d22\u6e05\u5355/jobs-all.json") as f:
        data = json.load(f)
    count = len(data)
    print(f"JOB_COUNT={count}")
    if count > 400:
        print("OK")
    else:
        print(f"TOO_FEW_JOBS")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
