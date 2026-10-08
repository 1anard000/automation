"""Final verification of today's discovery run."""
import json
from collections import Counter
from datetime import date

BASE = "/Users/iancolrick/.openclaw/workspace/career-os"
AGENT = f"{BASE}/scrapers/agent-discovered-jobs.json"
MASTER = f"{BASE}/OKComputer_职位搜索清单/jobs-all.json"

with open(AGENT) as f:
    agent = json.load(f)
with open(MASTER) as f:
    master = json.load(f)

today = date.today().isoformat()
agent_today = [j for j in agent if j.get('scanned_date') == today]
master_today = [j for j in master if j.get('scanned_date') == today]

print(f"Agent total: {len(agent)} | today: {len(agent_today)}")
print(f"Master total: {len(master)} | today: {len(master_today)}")
print()

# Verify no dups within agent
agent_urls = [j.get('url','') for j in agent_today]
agent_ids = [j.get('job_id','') for j in agent_today]
print(f"Agent today URL dups: {len(agent_urls) - len(set(agent_urls))}")
print(f"Agent today ID dups: {len(agent_ids) - len(set(agent_ids))}")

# Verify no cross-file dups
master_urls = {j.get('url','') for j in master}
cross_dups = [j for j in agent_today if j.get('url','') in master_urls]
print(f"Agent->Master cross-dups today: {len(cross_dups)}")

# Amazon check
amazon = [j for j in agent_today + master_today if 'amazon' in ((j.get('company','') + ' ' + j.get('title','')).lower())]
print(f"Amazon leaks: {len(amazon)}")

# Location check for agent today
print(f"\nAgent today locations: {dict(Counter(j.get('location','') for j in agent_today))}")
print(f"Agent today sources: {dict(Counter(j.get('source','') for j in agent_today))}")
print(f"Agent today role_types: {dict(Counter(j.get('role_type','') for j in agent_today))}")

# Master today sources
print(f"\nMaster today sources: {dict(Counter(j.get('source','') for j in master_today))}")
print(f"Master today role_types: {dict(Counter(j.get('role_type','') for j in master_today))}")

# Salary-floor violations in master today (should have been cleaned)
floor_violations = []
for j in master_today:
    sal = j.get('salary','')
    if not sal:
        continue
    import re
    s = re.sub(r'[·.]\d+薪', '', sal)
    m = re.search(r'(\d+)[-–](\d+)K', s)
    if m:
        high = int(m.group(2))
        loc = (j.get('location_norm') or j.get('location') or '').lower()
        if any(c in loc for c in ['shenzhen','guangzhou','shanghai','beijing']) and high < 30:
            floor_violations.append((j.get('title','')[:40], sal))
        elif 'hong kong' in loc and high < 60:
            floor_violations.append((j.get('title','')[:40], sal))
        elif 'singapore' in loc and high < 10:
            floor_violations.append((j.get('title','')[:40], sal))

print(f"\nMaster today salary-floor violations: {len(floor_violations)}")
for t, s in floor_violations:
    print(f"  [FLOOR] {t} | {s}")
