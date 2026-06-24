import json, sys

with open("OKComputer_职位搜索清单/jobs-all.json") as f:
    data = json.load(f)

print(f"Total jobs: {len(data)}")

tiers = {}
for j in data:
    t = j.get("quality_tier", "unknown")
    tiers[t] = tiers.get(t, 0) + 1
print(f"By tier: {tiers}")

statuses = {}
for j in data:
    s = j.get("status", "unknown")
    statuses[s] = statuses.get(s, 0) + 1
print(f"By status: {statuses}")

low_q = sum(1 for j in data if j.get("low_quality", False))
print(f"Hard-flagged (low_quality): {low_q}")

sources = {}
for j in data:
    s = j.get("source", "unknown")
    sources[s] = sources.get(s, 0) + 1
print(f"By source: {sources}")

scores = [j.get("quality_score", 0) for j in data if j.get("quality_score")]
if scores:
    print(f"Score range: {min(scores)}-{max(scores)}")
    print(f"Score median: {sorted(scores)[len(scores)//2]}")
