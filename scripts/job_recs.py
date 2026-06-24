import json
from collections import Counter

with open("/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json") as f:
    jobs = json.load(f)

print(f"Total jobs: {len(jobs)}")

# Filter
target_cities = ["hong kong", "hk", "shenzhen", "sz", "guangzhou", "gz", "shanghai", "sh", "singapore", "sg", "tokyo", "taipei"]
crypto_kw = ["crypto", "blockchain", "web3", "defi", "nft", "bitcoin", "ethereum", "solana"]

filtered = []
for j in jobs:
    quality = j.get("quality_score", 0)
    try:
        quality = int(quality)
    except (ValueError, TypeError):
        quality = 0
    if quality < 70:
        continue
    loc = (j.get("location", "") + " " + j.get("location_norm", "")).lower()
    if not any(c in loc for c in target_cities):
        continue
    title_lower = (j.get("title", "") + " " + j.get("en_title", "")).lower()
    if any(kw in title_lower for kw in crypto_kw):
        continue
    filtered.append(j)

print(f"After filter: {len(filtered)}")

cats = Counter(j.get("category", "unknown") for j in filtered)
print(f"Categories: {dict(cats)}")
role_types = Counter(j.get("role_type", "unknown") for j in filtered)
print(f"Role types: {dict(role_types)}")

# Sort by quality score desc
filtered.sort(key=lambda x: (x.get("quality_score", 0), not x.get("stale", True)), reverse=True)

# Print top 50 for selection
for i, j in enumerate(filtered[:50]):
    qs = j.get("quality_score", 0)
    cat = j.get("category", "?")
    rt = j.get("role_type", "?")
    co = j.get("company", "?")
    ti = j.get("title", "?")[:55]
    loc = j.get("location", "?")
    url = j.get("url", "")
    stale = j.get("stale", False)
    fid = j.get("job_id", "")[:8]
    print(f"  {i+1:2d}. Q{qs:3d} [{cat:12s}] [{rt:20s}] {co:25s} | {ti:55s} | {loc:15s} | stale={stale} | id={fid} | {url}")
