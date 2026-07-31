import json
from datetime import datetime, timedelta
from collections import Counter

with open("/Users/iancolrick/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json") as f:
    jobs = json.load(f)

total = len(jobs)

# Jobs by location
loc_counts = Counter(j.get("location_norm","") or j.get("location","") or "Unknown" for j in jobs)

# Jobs by category
cat_counts = Counter(j.get("category","other") or "other" for j in jobs)

# Jobs from last 24h
today = datetime(2026, 8, 1)
yesterday = today - timedelta(days=1)

recent = []
for j in jobs:
    sd = j.get("scanned_date","")
    if sd:
        try:
            d = datetime.strptime(sd, "%Y-%m-%d")
            if d >= yesterday:
                recent.append(j)
        except:
            pass

# Status counts
status_counts = Counter(j.get("status","not_applied") for j in jobs)

# Apply link stats
direct_apply = sum(1 for j in recent if j.get("has_direct_link"))

# Filter for target profile
target_locations = {"Shenzhen", "Hong Kong", "Guangzhou", "Shanghai", "Singapore"}

def relevance_score(j):
    score = j.get("quality_score") or 50
    title = (j.get("title","") + " " + j.get("role_type","")).lower()
    loc = j.get("location_norm","")
    company = j.get("company","").lower()
    
    if loc in target_locations:
        loc_boost = {"Shenzhen": 20, "Hong Kong": 15, "Guangzhou": 10, "Shanghai": 8, "Singapore": 5}
        score += loc_boost.get(loc, 0)
    
    for kw in ["director", "vp", "head", "总监", "产品", "product", "growth", "strategy", "bizops", "general manager", "gm"]:
        if kw in title:
            score += 10
            break
    
    if j.get("english_friendly"):
        score += 5
    
    if j.get("has_direct_link"):
        score += 10
    
    url = j.get("url","")
    if "linkedin.com/jobs" in url or "lever.co" in url or "greenhouse.io" in url or "apply.workable" in url:
        score += 5
    
    if "amazon" in company or "亚马逊" in company:
        score -= 100
    
    return score

all_scored = sorted(jobs, key=relevance_score, reverse=True)

week_cutoff = today - timedelta(days=7)
recent_week = [j for j in jobs if j.get("scanned_date","") >= week_cutoff.strftime("%Y-%m-%d")]
recent_scored = sorted(recent_week, key=relevance_score, reverse=True)

top_recent = [j for j in recent_scored[:30] if j.get("company","").lower() != "amazon"]

sz_jobs = [j for j in all_scored if j.get("location_norm","") == "Shenzhen" and j.get("company","").lower() != "amazon"]
sz_top = sz_jobs[:5]

print(f"Total: {total}")
print(f"Locations:")
for loc, cnt in loc_counts.most_common(15):
    print(f"  {loc or 'Unknown'}: {cnt}")
print(f"Categories:")
for cat, cnt in cat_counts.most_common(10):
    print(f"  {cat}: {cnt}")
print(f"Status:")
for s, cnt in status_counts.most_common():
    print(f"  {s}: {cnt}")
print(f"Recent_24h: {len(recent)}")
print(f"Recent_7d: {len(recent_week)}")
print(f"Top_recent_count: {len(top_recent)}")
print("Top 10 recent picks:")
for i, j in enumerate(top_recent[:10]):
    company = j.get("company","") or "(not listed)"
    url = j.get("url","")
    link = url if url else "no_link"
    score = relevance_score(j)
    sal = j.get("salary","")
    print(f"PICK|{i+1}|{j['title']}|{company}|{j.get('location','')}|{score}|{link}|{sal}")

print("Best in Shenzhen:")
for i, j in enumerate(sz_top):
    company = j.get("company","") or "(not listed)"
    url = j.get("url","")
    print(f"SZ|{i+1}|{j['title']}|{company}|{relevance_score(j)}|{url}")
