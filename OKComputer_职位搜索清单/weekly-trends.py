#!/usr/bin/env python3
"""Generate weekly job market trends summary from jobs-all.json.

Output: weekly-trends.md (human-readable) and weekly-trends.json (machine-readable).
Usage: python3 weekly-trends.py [--days N]
"""
import json
import sys
import os
from datetime import datetime, timedelta
from collections import Counter

DIR = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.join(DIR, "jobs-all.json")
OUT_MD = os.path.join(DIR, "weekly-trends.md")
OUT_JSON = os.path.join(DIR, "weekly-trends.json")

def load_jobs():
    with open(MASTER) as f:
        return json.load(f)

def parse_date(s):
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(s[:19], fmt[:len(s[:19])+2])
        except ValueError:
            continue
    return None

def trends(jobs, days=7):
    cutoff = datetime.now() - timedelta(days=days)
    
    recent = []
    for j in jobs:
        d = parse_date(j.get("scanned_date", "") or j.get("date_saved", ""))
        if d and d >= cutoff:
            recent.append(j)
    
    # All-time stats
    total = len(jobs)
    grades_all = Counter(j.get("grade", "?") for j in jobs)
    companies_all = Counter(j.get("company", "unknown") for j in jobs)
    categories_all = Counter(j.get("category", "unknown") for j in jobs)
    
    # Recent stats
    companies_recent = Counter(j.get("company", "unknown") for j in recent)
    grades_recent = Counter(j.get("grade", "?") for j in recent)
    categories_recent = Counter(j.get("category", "unknown") for j in recent)
    sources_recent = Counter(j.get("source", "unknown") for j in recent)
    locs_recent = Counter(j.get("city_normalized", j.get("location", "?")) for j in recent)
    
    # A-1 jobs (top tier) in recent
    a1_recent = [j for j in recent if j.get("grade") == "A-1"]
    a1_companies = Counter(j.get("company", "?") for j in a1_recent)
    
    # A-1 jobs all time
    a1_all = [j for j in jobs if j.get("grade") == "A-1"]
    
    return {
        "generated_at": datetime.now().isoformat(),
        "period_days": days,
        "total_jobs": total,
        "recent_count": len(recent),
        "a1_total": len(a1_all),
        "a1_recent": len(a1_recent),
        "top_companies_recent": companies_recent.most_common(10),
        "top_companies_all": companies_all.most_common(15),
        "grades_recent": sorted(grades_recent.items()),
        "grades_all": sorted(grades_all.items()),
        "categories_recent": categories_recent.most_common(10),
        "categories_all": categories_all.most_common(15),
        "sources_recent": sources_recent.most_common(10),
        "locations_recent": locs_recent.most_common(10),
        "a1_recent_companies": a1_companies.most_common(10),
        "a1_recent_jobs": [
            {"title": j.get("title"), "company": j.get("company"), 
             "location": j.get("location"), "url": j.get("url")}
            for j in a1_recent[:20]
        ],
    }

def render_md(t):
    lines = []
    lines.append(f"# 📊 Weekly Job Market Trends")
    lines.append(f"*Generated {t['generated_at'][:10]} · Last {t['period_days']} days*\n")
    
    lines.append(f"## Overview")
    lines.append(f"- **Total jobs in database:** {t['total_jobs']}")
    lines.append(f"- **New this week:** {t['recent_count']}")
    lines.append(f"- **A-1 (top tier) all-time:** {t['a1_total']}")
    lines.append(f"- **A-1 added this week:** {t['a1_recent']}\n")
    
    if t["a1_recent_jobs"]:
        lines.append(f"## 🎯 A-1 Jobs This Week ({t['a1_recent']})")
        for j in t["a1_recent_jobs"]:
            lines.append(f"- **{j['title']}** @ {j['company']} ({j['location']})")
        lines.append("")
    
    lines.append(f"## Top Companies (This Week)")
    for c, n in t["top_companies_recent"]:
        lines.append(f"- {c}: {n}")
    lines.append("")
    
    lines.append(f"## Top Companies (All Time)")
    for c, n in t["top_companies_all"]:
        lines.append(f"- {c}: {n}")
    lines.append("")
    
    lines.append(f"## Categories (This Week)")
    for c, n in t["categories_recent"]:
        lines.append(f"- {c}: {n}")
    lines.append("")
    
    lines.append(f"## Grade Distribution (This Week)")
    for g, n in t["grades_recent"]:
        lines.append(f"- {g}: {n}")
    lines.append("")
    
    lines.append(f"## Sources (This Week)")
    for s, n in t["sources_recent"]:
        lines.append(f"- {s}: {n}")
    lines.append("")
    
    lines.append(f"## Locations (This Week)")
    for l, n in t["locations_recent"]:
        lines.append(f"- {l}: {n}")
    
    return "\n".join(lines)

def main():
    days = 7
    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        if idx + 1 < len(sys.argv):
            days = int(sys.argv[idx + 1])
    
    jobs = load_jobs()
    t = trends(jobs, days)
    
    # Write JSON
    with open(OUT_JSON, "w") as f:
        json.dump(t, f, indent=2, ensure_ascii=False, default=str)
    
    # Write Markdown
    md = render_md(t)
    with open(OUT_MD, "w") as f:
        f.write(md)
    
    print(f"✅ Weekly trends generated: {t['recent_count']} jobs in last {days} days")
    print(f"   → {OUT_MD}")
    print(f"   → {OUT_JSON}")

if __name__ == "__main__":
    main()
