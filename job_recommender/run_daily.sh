#!/bin/bash
# Daily Job Recommendation Runner
# Run this daily (e.g., via cron at 8:00 AM)
# Usage: ./run_daily.sh [--sheets] [--briefing-only]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
JOBS_DIR="/Users/iancolrick/OKComputer_职位搜索清单"
TODAY=$(date +%Y-%m-%d)

echo "=========================================="
echo "  Career OS — Daily Job Recommendations"
echo "  $TODAY"
echo "=========================================="
echo ""

# Step 1: Run enhanced scoring
echo "[1/3] Running enhanced quality scoring..."
python3 "$SCRIPT_DIR/enhanced_scorer.py"
echo ""

# Step 2: Generate daily recommendations + briefing
echo "[2/3] Generating daily recommendations..."
python3 "$SCRIPT_DIR/daily_recommender.py"
echo ""

# Step 3: Sync to Google Sheets (if --sheets flag)
if [[ "$1" == "--sheets" ]]; then
    echo "[3/3] Syncing to Google Sheets..."
    python3 "$SCRIPT_DIR/sheets_sync.py"
    echo ""
else
    echo "[3/3] Skipping Google Sheets sync (use --sheets to enable)"
fi

echo "=========================================="
echo "  Done! Briefing saved to:"
echo "  $SCRIPT_DIR/daily_reports/briefing-$TODAY.md"
echo "=========================================="
