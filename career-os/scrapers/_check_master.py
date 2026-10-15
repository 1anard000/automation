import json
from collections import Counter

base = "/Users/iancolrick/.openclaw/workspace/career-os"
with open(f"{base}/OKComputer_职位搜索清单/jobs-all.json") as f:
    master = json.load(f)

print(f"Master DB now has {len(master)} jobs")
dates = Counter(j.get('scanned_date','unknown') for j in master)
print("\nScanned date distribution (top 10):")
for d, c in dates.most_common(10):
    print(f"  {d}: {c}")

sources = Counter(j.get('source','unknown') for j in master)
print("\nTop sources in master:")
for s, c in sources.most_common(15):
    print(f"  {s}: {c}")

blocked = [j for j in master if j.get('quality_block_reason')]
print(f"\nJobs with quality_block_reason in master: {len(blocked)}")

recent = [j for j in master if (j.get('scanned_date') or '') >= '2026-10-10']
print(f"\nJobs scanned since 2026-10-10: {len(recent)}")
for j in recent[:15]:
    print(f"  {j.get('scanned_date')} | {j.get('title','')[:55]} | {j.get('company','')[:25]} | {j.get('source','')}")
