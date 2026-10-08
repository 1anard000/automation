"""Load context for today's run: master + agent file stats."""
import json
from datetime import date
from collections import Counter

BASE = "/Users/iancolrick/.openclaw/workspace/career-os"
MASTER = f"{BASE}/OKComputer_职位搜索清单/jobs-all.json"
AGENT = f"{BASE}/scrapers/agent-discovered-jobs.json"

with open(MASTER) as f:
    master = json.load(f)
with open(AGENT) as f:
    agent = json.load(f)

today = date.today().isoformat()
print(f"Master jobs: {len(master)}")
print(f"Agent jobs: {len(agent)}")
print(f"Today ({today}): master={sum(1 for j in master if j.get('scanned_date')==today)}, agent={sum(1 for j in agent if j.get('scanned_date')==today)}")

master_urls = {j.get('url','') for j in master}
agent_urls = {j.get('url','') for j in agent}
print(f"Unique master URLs: {len(master_urls)}")
print(f"Unique agent URLs: {len(agent_urls)}")
print(f"Overlap (agent in master): {len(agent_urls & master_urls)}")

src_m = Counter(j.get('source','?') for j in master if j.get('scanned_date')==today)
src_a = Counter(j.get('source','?') for j in agent if j.get('scanned_date')==today)
print(f"Master today's sources: {dict(src_m)}")
print(f"Agent today's sources: {dict(src_a)}")
