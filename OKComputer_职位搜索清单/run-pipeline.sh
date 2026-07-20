#!/bin/bash
# Career OS — Full Pipeline: Scan → Grade → Dedup → Build Dashboard
# Usage: bash run-pipeline.sh [--scan-only] [--no-scan]
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
LOG_FILE="$DIR/pipeline.log"

log() { echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG_FILE"; }

SCAN_ONLY=false
NO_SCAN=false
for arg in "$@"; do
    case "$arg" in
        --scan-only) SCAN_ONLY=true ;;
        --no-scan) NO_SCAN=true ;;
    esac
done

# ── Step 1: Scan ──
if [ "$NO_SCAN" = false ]; then
    log "📡 Step 1/6: Scanning Greenhouse boards..."
    if python3 scan-greenhouse.py 2>&1 | tee -a "$LOG_FILE"; then
        log "✅ Scan complete"
    else
        log "⚠️  Scan failed or partial — continuing with existing data"
    fi
else
    log "⏭️  Step 1/4: Skipping scan (--no-scan)"
fi

# ── Step 1b: Scan Ashby boards ──
log "🔍 Step 1b/6: Scanning Ashby boards..."
if python3 scrape-ashby.py 2>&1 | tee -a "$LOG_FILE"; then
    log "✅ Ashby scan complete"
else
    log "⚠️  Ashby scan failed or partial — continuing"
fi

if [ "$SCAN_ONLY" = true ]; then
    log "🏁 Scan-only mode, done."
    exit 0
fi

# ── Step 2: Grade ──
log "📊 Step 2/6: Grading and deduplicating scan results..."
if python3 grade-scan.py 2>&1 | tee -a "$LOG_FILE"; then
    log "✅ Grading complete"
else
    log "⚠️  Grading failed — check grade-scan.py"
    exit 1
fi

# ── Step 3: Merge into jobs-all.json ──
log "🔗 Step 3/6: Merging new jobs into master database..."
if python3 -c "
import json, os, glob

SCAN_FILES = ['scan-latest.json', 'scan-ashby.json']
MASTER = 'jobs-all.json'

new_jobs = []
for sf in SCAN_FILES:
    if os.path.exists(sf):
        with open(sf) as f:
            data = json.load(f)
            if data:
                new_jobs.extend(data)
                print(f'  Loaded {len(data)} jobs from {sf}')

if not new_jobs:
    print('No scan files found, skipping merge')
    exit(0)

master = []
if os.path.exists(MASTER):
    with open(MASTER) as f:
        master = json.load(f)

# Dedup by (title, company, location)
seen = set()
for j in master:
    key = (j.get('title','').lower().strip(), j.get('company','').lower().strip(), j.get('location','').lower().strip())
    seen.add(key)

added = 0
for j in new_jobs:
    key = (j.get('title','').lower().strip(), j.get('company','').lower().strip(), j.get('location','').lower().strip())
    if key not in seen:
        seen.add(key)
        master.append(j)
        added += 1

with open(MASTER, 'w') as f:
    json.dump(master, f, indent=2, ensure_ascii=False)

print(f'Merged {added} new jobs (total: {len(master)})')
" 2>&1 | tee -a "$LOG_FILE"; then
    log "✅ Merge complete"
else
    log "⚠️  Merge failed"
fi

# ── Step 4: Build Dashboard ──
log "🖥️  Step 4/6: Building dashboard..."
if python3 build-dashboard.py 2>&1 | tee -a "$LOG_FILE"; then
    log "✅ Dashboard built: dashboard.html"
else
    log "⚠️  Dashboard build failed"
fi

# ── Step 5: Data Quality Cleanup ──
log "🧹 Step 5/6: Data quality cleanup..."
if python3 -c "
import json, os
from datetime import datetime, timedelta

MASTER = 'jobs-all.json'
if not os.path.exists(MASTER):
    print('No master file, skipping cleanup')
    exit(0)

with open(MASTER) as f:
    jobs = json.load(f)

original = len(jobs)

# 1. Dedup by URL (keep first occurrence)
seen_urls = set()
deduped = []
for j in jobs:
    url = j.get('url','')
    if url and url in seen_urls:
        continue
    if url:
        seen_urls.add(url)
    deduped.append(j)
jobs = deduped

# 2. Normalize grade format: A-1 → A-, A-2 → A-
for j in jobs:
    g = j.get('grade','')
    if g and g.startswith('A-') and len(g) > 2:
        j['grade'] = 'A-'

# 3. Fill missing scanned_date from git (default to today)
today = datetime.now().strftime('%Y-%m-%d')
for j in jobs:
    if not j.get('scanned_date'):
        j['scanned_date'] = today

# 4. Remove jobs with posted date > 60 days ago
now = datetime.now()
cleaned = []
removed = 0
for j in jobs:
    posted = j.get('posted','')
    if posted:
        try:
            d = datetime.fromisoformat(posted.replace('Z',''))
            if (now - d).days > 60:
                removed += 1
                continue
        except:
            pass
    cleaned.append(j)
jobs = cleaned

with open(MASTER, 'w') as f:
    json.dump(jobs, f, indent=2, ensure_ascii=False)

print(f'Cleanup: {original} → {len(jobs)} jobs (removed {original - len(jobs)}: {removed} stale + {original - len(jobs) - removed} URL dupes)')
" 2>&1 | tee -a "$LOG_FILE"; then
    log "✅ Data quality cleanup complete"
else
    log "⚠️  Cleanup failed"
fi

log "🏁 Pipeline complete at $TIMESTAMP"
