#!/usr/bin/env python3
import json
from collections import Counter

with open("/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json") as f:
    jobs = json.load(f)

dates = Counter(j.get("scanned_date", "unknown") for j in jobs)
print("Scan dates:")
for d, count in sorted(dates.items()):
    print(f"  {d}: {count}")

# Count by source
sources = Counter(j.get("source", "unknown") for j in jobs)
print("\nSources:")
for s, count in sources.most_common():
    print(f"  {s}: {count}")

# Total
print(f"\nTotal: {len(jobs)}")
