import json

with open("/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json") as f:
    jobs = json.load(f)

# Filter
target_cities = ["hong kong", "hk", "shenzhen", "sz", "guangzhou", "gz", "shanghai", "sh", "singapore", "sg", "tokyo", "taipei"]
crypto_kw = ["crypto", "blockchain", "web3", "defi", "nft", "bitcoin", "ethereum", "solana"]
# Pure crypto companies to exclude
crypto_companies = ["binance", "okx", "gate", "coins.ph", "bitget", "bybit", "kucoin", "huobi", "htx", "deribit", "crypto.com"]

filtered = []
for j in jobs:
    quality = j.get("quality_score", 0)
    try:
        quality = int(quality)
    except:
        quality = 0
    if quality < 70:
        continue
    loc = (j.get("location", "") + " " + j.get("location_norm", "")).lower()
    if not any(c in loc for c in target_cities):
        continue
    title_lower = (j.get("title", "") + " " + j.get("en_title", "")).lower()
    company_lower = j.get("company", "").lower()
    if any(kw in title_lower for kw in crypto_kw):
        continue
    if any(cc in company_lower for cc in crypto_companies):
        continue
    filtered.append(j)

print(f"After filter: {len(filtered)}")
print()

# Categorize
for j in filtered:
    cat = j.get("category", "unknown")
    rt = j.get("role_type", "unknown")
    
    if cat in ["strategy"] or rt in ["Strategy/Ops", "Strategy"]:
        j["_group"] = "strategy"
    elif cat in ["growth", "general_manager", "gm"] or rt in ["Growth", "Growth/GM", "GM/Country Manager", "General Manager", "GM/Head"]:
        j["_group"] = "growth_gm"
    elif cat in ["cross_border"] or rt in ["Cross-border/Expansion"]:
        j["_group"] = "cross_border"
    else:
        j["_group"] = "product"

from collections import Counter
groups = Counter(j["_group"] for j in filtered)
print(f"Groups: {dict(groups)}")

# Sort by quality
filtered.sort(key=lambda x: (x.get("quality_score", 0), not x.get("stale", True)), reverse=True)

# Pick top 20 with diversity:
# Aim for: 5 strategy, 8 product, 4 growth/gm, 3 cross-border
targets = {"strategy": 5, "product": 8, "growth_gm": 4, "cross_border": 3}
selected = []
used = set()

for group, count in targets.items():
    candidates = [j for j in filtered if j["_group"] == group and j.get("job_id", "") not in used]
    for j in candidates[:count]:
        selected.append(j)
        used.add(j.get("job_id", ""))

# Fill remaining from top quality
remaining = [j for j in filtered if j.get("job_id", "") not in used]
for j in remaining:
    if len(selected) >= 20:
        break
    selected.append(j)
    used.add(j.get("job_id", ""))

# Sort selected by quality desc
selected.sort(key=lambda x: x.get("quality_score", 0), reverse=True)

print(f"\n=== TOP {len(selected)} ===\n")
for i, j in enumerate(selected):
    qs = j.get("quality_score", 0)
    co = j.get("company", "?")
    ti = j.get("title", "?")
    loc = j.get("location", "?")
    url = j.get("url", "")
    group = j.get("_group", "?")
    cat = j.get("category", "?")
    rt = j.get("role_type", "?")
    stale = j.get("stale", False)
    fid = j.get("job_id", "")[:8]
    
    # Build bing fallback if url is generic search
    bing = j.get("bing_fallback", "")
    
    print(f"{i+1:2d}. [{group:12s}] Q{qs:3d} | {co}")
    print(f"    {ti}")
    print(f"    📍 {loc} | stale={stale} | id={fid}")
    print(f"    🔗 {url}")
    if bing and ("search" in url or "position-list" in url or "search.html" in url):
        print(f"    🔍 {bing}")
    print()
