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
    log "📡 Step 1/4: Scanning Greenhouse boards..."
    if python3 scan-greenhouse.py 2>&1 | tee -a "$LOG_FILE"; then
        log "✅ Scan complete"
    else
        log "⚠️  Scan failed or partial — continuing with existing data"
    fi
else
    log "⏭️  Step 1/4: Skipping scan (--no-scan)"
fi

if [ "$SCAN_ONLY" = true ]; then
    log "🏁 Scan-only mode, done."
    exit 0
fi

# ── Step 2: Grade ──
log "📊 Step 2/4: Grading and deduplicating scan results..."
if python3 grade-scan.py 2>&1 | tee -a "$LOG_FILE"; then
    log "✅ Grading complete"
else
    log "⚠️  Grading failed — check grade-scan.py"
    exit 1
fi

# ── Step 3: Merge into jobs-all.json ──
log "🔗 Step 3/4: Merging new jobs into master database..."
if python3 -c "
import json, os

SCAN = 'scan-latest.json'
MASTER = 'jobs-all.json'

if not os.path.exists(SCAN):
    print('No scan-latest.json found, skipping merge')
    exit(0)

with open(SCAN) as f:
    new_jobs = json.load(f)

if not new_jobs:
    print('No new jobs to merge')
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
log "🖥️  Step 4/4: Building dashboard..."
if python3 build-dashboard.py 2>&1 | tee -a "$LOG_FILE"; then
    log "✅ Dashboard built: dashboard.html"
else
    log "⚠️  Dashboard build failed"
fi

log "🏁 Pipeline complete at $TIMESTAMP"
