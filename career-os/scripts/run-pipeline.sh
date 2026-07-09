#!/usr/bin/env bash
#
# run-pipeline.sh — Run the career-os data pipeline.
#
# Steps:
#   1. Merge all scraper results into master jobs-all.json
#   2. Update coverage-report.json
#   3. Regenerate dashboard stats
#
# Usage:
#   ./run-pipeline.sh              # full pipeline
#   ./run-pipeline.sh --dry-run    # preview only
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

DRY_RUN_FLAG=""
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN_FLAG="--dry-run"
    echo "🔍 DRY RUN MODE — no files will be written"
    echo
fi

# ── Step 1: Merge jobs ──────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  STEP 1/3: Merge scraper results into master jobs list"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 "$SCRIPT_DIR/merge-jobs.py" $DRY_RUN_FLAG
echo

# ── Step 2: Coverage report ─────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  STEP 2/3: Update coverage-report.json"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ "$DRY_RUN_FLAG" == "--dry-run" ]]; then
    echo "  (skipped — dry run mode)"
else
    python3 - "$BASE_DIR" <<'PYEOF'
import json, os, sys, glob
from collections import Counter
from datetime import datetime

base_dir = sys.argv[1]
master_file = os.path.join(base_dir, "OKComputer_职位搜索清单", "jobs-all.json")
report_file = os.path.join(base_dir, "OKComputer_职位搜索清单", "coverage-report.json")

try:
    with open(master_file) as f:
        jobs = json.load(f)
except FileNotFoundError:
    print(f"  ⚠️  {master_file} not found — skipping coverage report")
    sys.exit(0)

report = {
    "generated_at": datetime.now().isoformat(),
    "total_jobs": len(jobs),
    "by_grade": dict(Counter(j.get("grade", "") for j in jobs)),
    "by_tier": dict(Counter(j.get("tier", "") for j in jobs)),
    "by_source": dict(Counter(j.get("source", "") for j in jobs)),
    "by_status": dict(Counter(j.get("status", "") for j in jobs)),
    "with_url": sum(1 for j in jobs if j.get("url")),
    "with_company": sum(1 for j in jobs if j.get("company")),
    "with_en_title": sum(1 for j in jobs if j.get("en_title")),
    "with_summary": sum(1 for j in jobs if j.get("summary")),
}

os.makedirs(os.path.dirname(report_file), exist_ok=True)
with open(report_file, "w") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"  ✅ Coverage report updated: {report_file}")
print(f"     Total jobs: {report['total_jobs']}")
print(f"     With company: {report['with_company']}/{report['total_jobs']}")
print(f"     With en_title: {report['with_en_title']}/{report['total_jobs']}")
PYEOF
fi
echo

# ── Step 3: Dashboard stats ─────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  STEP 3/3: Regenerate dashboard stats"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ "$DRY_RUN_FLAG" == "--dry-run" ]]; then
    echo "  (skipped — dry run mode)"
else
    python3 - "$BASE_DIR" <<'PYEOF'
import json, os, sys
from collections import Counter
from datetime import datetime

base_dir = sys.argv[1]
master_file = os.path.join(base_dir, "OKComputer_职位搜索清单", "jobs-all.json")
dashboard_file = os.path.join(base_dir, "docs", "data", "dashboard.json")

try:
    with open(master_file) as f:
        jobs = json.load(f)
except FileNotFoundError:
    print(f"  ⚠️  {master_file} not found — skipping dashboard")
    sys.exit(0)

# Build dashboard stats
t1_count = sum(1 for j in jobs if j.get("tier") == "T1")
t2_count = sum(1 for j in jobs if j.get("tier") == "T2")
a_grade = sum(1 for j in jobs if j.get("grade", "").startswith("A"))
s_grade = sum(1 for j in jobs if j.get("grade") == "S-1")

dashboard = {
    "updated_at": datetime.now().isoformat(),
    "summary": {
        "total_jobs": len(jobs),
        "a_grade_jobs": a_grade,
        "s_grade_jobs": s_grade,
        "t1_companies": t1_count,
        "t2_companies": t2_count,
        "applied": sum(1 for j in jobs if j.get("status") == "applied"),
        "not_applied": sum(1 for j in jobs if j.get("status") == "not_applied"),
    },
    "grade_distribution": dict(Counter(j.get("grade", "") for j in jobs)),
    "tier_distribution": dict(Counter(j.get("tier", "") for j in jobs)),
    "source_distribution": dict(Counter(j.get("source", "") for j in jobs)),
}

os.makedirs(os.path.dirname(dashboard_file), exist_ok=True)
with open(dashboard_file, "w") as f:
    json.dump(dashboard, f, indent=2, ensure_ascii=False)

s = dashboard["summary"]
print(f"  ✅ Dashboard updated: {dashboard_file}")
print(f"     Total: {s['total_jobs']} | S-1: {s['s_grade_jobs']} | A-grade: {s['a_grade_jobs']}")
print(f"     T1: {s['t1_companies']} | T2: {s['t2_companies']}")
print(f"     Applied: {s['applied']} | Pending: {s['not_applied']}")
PYEOF
fi

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Pipeline complete ✅"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
