#!/usr/bin/env python3
"""
auto-maintain.py — Unified maintenance pipeline for Career OS.

Runs a full maintenance cycle on jobs-all.json:
  1. Merge       — Consolidate all scraper outputs
  2. Dedup       — Remove exact duplicates (same title + company)
  3. Stale       — Remove jobs older than 30 days
  4. Grade       — Assign grades to ungraded jobs
  5. Fill Gaps   — Fill missing fields (en_title, summary, quality_tier, quality_score, posted_date)
  6. Normalize   — Fix inconsistent field values
  7. Dashboard   — Regenerate dashboard.html
  8. Coverage    — Update coverage-report.json
  9. Report      — Print summary of changes

Usage:
    python3 auto-maintain.py                # full pipeline
    python3 auto-maintain.py --dry-run      # preview changes
    python3 auto-maintain.py --step 4       # run only step 4 (grade)
    python3 auto-maintain.py --report       # generate markdown report
"""

import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
MASTER_DIR = BASE_DIR / "OKComputer_职位搜索清单"
MASTER_FILE = MASTER_DIR / "jobs-all.json"
COVERAGE_REPORT = MASTER_DIR / "coverage-report.json"
DASHBOARD_HTML = MASTER_DIR / "dashboard.html"
DASHBOARD_JSON = BASE_DIR / "docs" / "data" / "dashboard.json"
MARKDOWN_REPORT = MASTER_DIR / "maintenance-report.md"

# ---------------------------------------------------------------------------
# Company prestige tiers (from merge-jobs.py)
# ---------------------------------------------------------------------------
T1_COMPANIES = {
    "okx", "stripe", "tencent", "bytedance", "bytedance inc.", "bytedance (tiktok)",
    "google", "meta", "apple", "amazon", "microsoft", "netease", "alibaba",
    "alibaba group", "jd.com", "jd", "meituan", "didi", "samsung", "bytedance/lark",
    "tiktok", "tiktok pte. ltd.", "lark", "feishu",
}

T2_COMPANIES = {
    "agoda", "shopee", "lazada", "grab", "sea group", "sea limited",
    "airbnb", "uber", "stripe (hk)", "coinbase", "binance", "huobi",
    "kraken", "crypto.com", "okx (subsidiary)", "dbs", "hsbc", "standard chartered",
    "samsung sdi", "sony", "nintendo", "epic games", "riot games",
    "snap", "spotify", "netflix", "linkedin", "salesforce", "oracle",
    "shopify", "twilio", "cloudflare", "datadog", "snowflake", "databricks",
    "figma", "notion", "canva", "atlassian", "gitlab", "github",
    "anthropic", "openai", "scale ai", "midjourney", "mistral",
}

T3_COMPANIES = {
    "robinhood", "plaid", "brex", "ramp", "chime", "nubank",
    "wise", "revolut", "n26", "klarna", "affirm", "afterpay",
    "square", "block", "paypal", "venmo", "zelle",
}

# ---------------------------------------------------------------------------
# Grade rules (from merge-jobs.py)
# ---------------------------------------------------------------------------
GRADE_RULES = [
    (r"\b(cto|ceo|coo|cfo|chief\s+product|founder|co-founder)\b", "S-1"),
    (r"\b(vp|vice\s+president|director|head\s+of|principal\s+(product|pm)|product\s+lead|product\s+owner)\b", "A-1"),
    (r"\b(senior\s+(product\s+manager|pm)|sr\.?\s+(product\s+manager|pm))\b", "A"),
    (r"\b(strategy\s+expert|growth\s+(manager|lead|head)|program\s+manager)\b", "A"),
    (r"\b(product\s+manager|pm\b)", "B"),
    (r"\b(associate\s+product\s+manager|junior\s+(product\s+manager|pm)|product\s+analyst)\b", "C"),
]

GRADE_PRIORITY = {"S-1": 0, "A-1": 1, "A": 2, "A-2": 3, "B": 4, "C": 5, "": 6}

# Canonical quality_tier values
CANONICAL_TIERS = {"S-1", "A-1", "A", "A-2", "B", "C"}

# Quality score ranges by grade
GRADE_SCORE_RANGES = {
    "S-1": (90, 100),
    "A-1": (80, 95),
    "A":   (70, 85),
    "A-2": (65, 80),
    "B":   (50, 70),
    "C":   (30, 55),
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  ⚠️  Could not load {path}: {e}", file=sys.stderr)
        return []


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def normalize_company(name):
    return (name or "").strip().lower()


def is_chinese(text):
    if not text:
        return False
    chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    return chinese_chars > len(text) * 0.3


# ---------------------------------------------------------------------------
# Chinese → English title translation
# ---------------------------------------------------------------------------
ZH_TO_EN_TITLES = {
    "产品总监": "Product Director",
    "产品VP": "VP of Product",
    "产品经理": "Product Manager",
    "高级产品经理": "Senior Product Manager",
    "资深产品经理": "Senior Product Manager",
    "产品专家": "Product Specialist",
    "产品负责人": "Head of Product",
    "用户增长经理": "Growth Product Manager",
    "增长产品经理": "Growth Product Manager",
    "数据产品经理": "Data Product Manager",
    "商业化产品经理": "Monetization Product Manager",
    "B端产品经理": "B2B Product Manager",
    "C端产品经理": "B2C Product Manager",
    "AI产品经理": "AI Product Manager",
    "策略产品经理": "Strategy Product Manager",
    "国际化产品经理": "Internationalization Product Manager",
}


def translate_title(title):
    if not title or not is_chinese(title):
        return title
    clean = title.strip()
    if clean in ZH_TO_EN_TITLES:
        return ZH_TO_EN_TITLES[clean]
    translated = clean
    for zh, en in sorted(ZH_TO_EN_TITLES.items(), key=lambda x: -len(x[0])):
        translated = translated.replace(zh, en)
    if is_chinese(translated):
        return "Product-related role (Chinese title)"
    return translated


def assign_grade_from_title(title):
    if not title:
        return ""
    title_lower = title.lower()
    for pattern, grade in GRADE_RULES:
        if re.search(pattern, title_lower, re.IGNORECASE):
            return grade
    return "C"


def assign_tier(company):
    c = normalize_company(company)
    if not c:
        return ""
    if c in T1_COMPANIES:
        return "T1"
    if c in T2_COMPANIES:
        return "T2"
    if c in T3_COMPANIES:
        return "T3"
    return "T3"


def generate_summary(job):
    parts = []
    if job.get("company"):
        parts.append(job["company"])
    title = job.get("en_title") or job.get("title", "")
    if title:
        parts.append(title)
    loc = job.get("location") or job.get("location_norm", "")
    if loc:
        parts.append(f"in {loc}")
    return " — ".join(parts) if parts else ""


def estimate_quality_score(grade, tier):
    """Estimate quality_score from grade and tier if missing."""
    lo, hi = GRADE_SCORE_RANGES.get(grade, (40, 60))
    base = (lo + hi) / 2
    if tier == "T1":
        base = min(base + 10, 100)
    elif tier == "T2":
        base = min(base + 5, 100)
    return int(base)


def parse_date(date_str):
    """Parse various date formats and return datetime or None."""
    if not date_str:
        return None
    s = str(date_str).strip()
    # Try ISO format with timezone
    for fmt in [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]:
        try:
            dt = datetime.strptime(s, fmt)
            # Make timezone-aware if naive
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# Step 1: Merge
# ---------------------------------------------------------------------------
def step_merge(master, dry_run=False):
    """Run merge-jobs.py as subprocess to consolidate scraper outputs."""
    merge_script = SCRIPT_DIR / "merge-jobs.py"
    if not merge_script.exists():
        print("  ⚠️  merge-jobs.py not found — skipping merge step")
        return master, {}

    cmd = [sys.executable, str(merge_script)]
    if dry_run:
        cmd.append("--dry-run")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BASE_DIR))
    if result.returncode != 0:
        print(f"  ⚠️  merge-jobs.py failed: {result.stderr}", file=sys.stderr)
        # Still try to continue with current master
        return master, {"merge_error": result.stderr}

    # Reload master after merge
    master = load_json(MASTER_FILE)
    return master, {"merge_output": result.stdout.strip()}


# ---------------------------------------------------------------------------
# Step 2: Dedup
# ---------------------------------------------------------------------------
def step_dedup(master, dry_run=False):
    """Remove exact duplicates (same title + company)."""
    before = len(master)
    seen = set()
    unique = []
    dupes_removed = 0

    for job in master:
        title = (job.get("title") or "").strip().lower()
        company = (job.get("company") or "").strip().lower()
        key = f"{title}|||{company}"

        if key in seen:
            dupes_removed += 1
            continue
        seen.add(key)
        unique.append(job)

    after = len(unique)
    stats = {"before": before, "after": after, "removed": dupes_removed}

    if not dry_run and dupes_removed > 0:
        master = unique

    return master, stats


# ---------------------------------------------------------------------------
# Step 3: Stale cleanup
# ---------------------------------------------------------------------------
def step_stale(master, dry_run=False, days=30):
    """Remove jobs older than `days` days."""
    before = len(master)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    kept = []
    stale_removed = 0

    for job in master:
        # Check multiple date fields
        date_str = job.get("posted_date") or job.get("posted") or job.get("scanned_date")
        dt = parse_date(date_str)

        if dt and dt < cutoff:
            stale_removed += 1
            continue
        kept.append(job)

    after = len(kept)
    stats = {"before": before, "after": after, "removed": stale_removed, "cutoff_days": days}

    if not dry_run and stale_removed > 0:
        master = kept

    return master, stats


# ---------------------------------------------------------------------------
# Step 4: Grade
# ---------------------------------------------------------------------------
def step_grade(master, dry_run=False):
    """Assign grades to ungraded jobs based on title and company."""
    graded = 0
    upgraded = 0

    for job in master:
        old_grade = job.get("grade", "")
        title = job.get("title", "")
        company = job.get("company", "")

        if not old_grade:
            new_grade = assign_grade_from_title(title)
            job["grade"] = new_grade
            graded += 1
        else:
            # Re-check: upgrade if company is T1/T2
            tier = assign_tier(company)
            if tier in ("T1", "T2") and old_grade in ("B", "C"):
                new_grade = assign_grade_from_title(title)
                if GRADE_PRIORITY.get(new_grade, 99) < GRADE_PRIORITY.get(old_grade, 99):
                    job["grade"] = new_grade
                    upgraded += 1

    return master, {"graded": graded, "upgraded": upgraded}


# ---------------------------------------------------------------------------
# Step 5: Fill gaps
# ---------------------------------------------------------------------------
def step_fill_gaps(master, dry_run=False):
    """Fill missing fields: en_title, summary, quality_tier, quality_score, posted_date."""
    filled = Counter()

    for job in master:
        # en_title
        if not job.get("en_title"):
            title = job.get("title", "")
            translated = translate_title(title)
            if translated != title or not is_chinese(title):
                job["en_title"] = title  # English title = title if already English
            else:
                job["en_title"] = translated
            filled["en_title"] += 1

        # summary
        if not job.get("summary"):
            job["summary"] = generate_summary(job)
            filled["summary"] += 1

        # quality_tier (use grade if available)
        qt = job.get("quality_tier", "")
        if not qt or qt not in CANONICAL_TIERS:
            grade = job.get("grade", "")
            if grade and grade in CANONICAL_TIERS:
                job["quality_tier"] = grade
                filled["quality_tier"] += 1

        # quality_score
        if not job.get("quality_score"):
            grade = job.get("grade", "")
            tier = job.get("tier", "") or assign_tier(job.get("company", ""))
            job["quality_score"] = estimate_quality_score(grade, tier)
            filled["quality_score"] += 1

        # posted_date — backfill from scanned_date if missing
        if not job.get("posted_date"):
            scanned = job.get("scanned_date")
            if scanned:
                job["posted_date"] = scanned
                filled["posted_date"] += 1

    return master, dict(filled)


# ---------------------------------------------------------------------------
# Step 6: Normalize
# ---------------------------------------------------------------------------
def step_normalize(master, dry_run=False):
    """Fix inconsistent field values."""
    fixed = Counter()

    GRADE_CANONICAL = {
        "s": "S-1", "s-1": "S-1",
        "a-1": "A-1", "a1": "A-1",
        "a": "A",
        "a-2": "A-2", "a2": "A-2",
        "a-": "A-2",
        "b-1": "B", "b1": "B", "b+": "B",
        "b": "B",
        "c": "C",
    }

    TIER_CANONICAL = {
        "tier1": "T1", "tier 1": "T1", "t1": "T1",
        "tier2": "T2", "tier 2": "T2", "t2": "T2",
        "tier3": "T3", "tier 3": "T3", "t3": "T3",
    }

    STATUS_CANONICAL = {
        "applied": "applied",
        "not_applied": "not_applied",
        "pending": "not_applied",
        "rejected": "rejected",
        "interviewing": "interviewing",
        "offer": "offer",
    }

    for job in master:
        # Normalize grade
        grade = (job.get("grade") or "").strip().lower()
        if grade in GRADE_CANONICAL:
            new_g = GRADE_CANONICAL[grade]
            if job.get("grade") != new_g:
                job["grade"] = new_g
                fixed["grade"] += 1

        # Normalize quality_tier to match grade
        qt = (job.get("quality_tier") or "").strip().lower()
        if qt in GRADE_CANONICAL:
            new_qt = GRADE_CANONICAL[qt]
            if job.get("quality_tier") != new_qt:
                job["quality_tier"] = new_qt
                fixed["quality_tier"] += 1
        elif qt not in CANONICAL_TIERS and qt:
            # Map non-standard tiers to grade
            grade_val = job.get("grade", "")
            if grade_val in CANONICAL_TIERS:
                job["quality_tier"] = grade_val
                fixed["quality_tier"] += 1

        # Normalize tier (from company prestige)
        tier = (job.get("tier") or "").strip().upper()
        if not tier or tier not in ("T1", "T2", "T3"):
            computed = assign_tier(job.get("company", ""))
            if computed:
                job["tier"] = computed
                if not tier:
                    fixed["tier"] += 1

        # Normalize status
        status = (job.get("status") or "").strip().lower()
        if status in STATUS_CANONICAL:
            new_s = STATUS_CANONICAL[status]
            if job.get("status") != new_s:
                job["status"] = new_s
                fixed["status"] += 1

        # Normalize quality_score to int
        score = job.get("quality_score")
        if score is not None and not isinstance(score, int):
            try:
                job["quality_score"] = int(float(score))
                fixed["quality_score"] += 1
            except (ValueError, TypeError):
                pass

    return master, dict(fixed)


# ---------------------------------------------------------------------------
# Step 7: Rebuild dashboard
# ---------------------------------------------------------------------------
def step_dashboard(master, dry_run=False):
    """Regenerate dashboard data files."""
    if dry_run:
        return {"status": "skipped (dry run)"}

    total = len(master)
    from collections import Counter as C

    # Build dashboard.json (used by build-dashboard.py)
    grade_dist = dict(C(j.get("grade", "") for j in master))
    tier_dist = dict(C(j.get("tier", "") for j in master))
    status_dist = dict(C(j.get("status", "") for j in master))
    source_dist = dict(C(j.get("source", "") for j in master))

    a_grade = sum(1 for j in master if j.get("grade", "").startswith("A"))
    s_grade = sum(1 for j in master if j.get("grade") == "S-1")
    t1_count = sum(1 for j in master if j.get("tier") == "T1")
    t2_count = sum(1 for j in master if j.get("tier") == "T2")

    dashboard_data = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_jobs": total,
            "a_grade_jobs": a_grade,
            "s_grade_jobs": s_grade,
            "t1_companies": t1_count,
            "t2_companies": t2_count,
            "applied": sum(1 for j in master if j.get("status") == "applied"),
            "not_applied": sum(1 for j in master if j.get("status") == "not_applied"),
        },
        "grade_distribution": grade_dist,
        "tier_distribution": tier_dist,
        "source_distribution": source_dist,
    }

    os.makedirs(DASHBOARD_JSON.parent, exist_ok=True)
    save_json(DASHBOARD_JSON, dashboard_data)

    # Also try to run build-dashboard.py if it exists
    build_script = SCRIPT_DIR / "build-dashboard.py"
    if build_script.exists():
        result = subprocess.run(
            [sys.executable, str(build_script)],
            capture_output=True, text=True, cwd=str(BASE_DIR)
        )
        if result.returncode != 0:
            print(f"  ⚠️  build-dashboard.py failed: {result.stderr}", file=sys.stderr)

    return {
        "dashboard_json": str(DASHBOARD_JSON),
        "total_jobs": total,
        "grade_dist": grade_dist,
    }


# ---------------------------------------------------------------------------
# Step 8: Coverage report
# ---------------------------------------------------------------------------
def step_coverage(master, dry_run=False):
    """Update coverage-report.json."""
    if dry_run:
        return {"status": "skipped (dry run)"}

    # Try running coverage_audit.py if it exists
    coverage_script = SCRIPT_DIR / "coverage_audit.py"
    if coverage_script.exists():
        result = subprocess.run(
            [sys.executable, str(coverage_script)],
            capture_output=True, text=True, cwd=str(BASE_DIR)
        )
        if result.returncode == 0:
            return {"output": result.stdout.strip()}

    # Fallback: build report inline
    total = len(master)
    report = {
        "report_date": datetime.now(timezone.utc).date().isoformat(),
        "generated_by": "auto-maintain.py",
        "total_jobs": total,
        "by_grade": dict(Counter(j.get("grade", "") for j in master)),
        "by_tier": dict(Counter(j.get("tier", "") for j in master)),
        "by_source": dict(Counter(j.get("source", "") for j in master)),
        "by_status": dict(Counter(j.get("status", "") for j in master)),
        "with_url": sum(1 for j in master if j.get("url")),
        "with_company": sum(1 for j in master if j.get("company")),
        "with_en_title": sum(1 for j in master if j.get("en_title")),
        "with_summary": sum(1 for j in master if j.get("summary")),
        "with_grade": sum(1 for j in master if j.get("grade")),
        "with_quality_score": sum(1 for j in master if j.get("quality_score")),
    }

    save_json(COVERAGE_REPORT, report)
    return {"report_file": str(COVERAGE_REPORT), "total_jobs": total}


# ---------------------------------------------------------------------------
# Step 9: Report
# ---------------------------------------------------------------------------
def step_report(master, all_stats, output_file=None):
    """Generate a markdown maintenance report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(master)

    lines = [
        f"# Career OS Maintenance Report",
        f"",
        f"**Generated:** {now}",
        f"**Total jobs:** {total}",
        f"",
        f"## Pipeline Results",
        f"",
    ]

    # Merge
    merge = all_stats.get("merge", {})
    if "merge_output" in merge:
        lines.append(f"### Step 1: Merge")
        lines.append(f"```")
        lines.append(merge["merge_output"])
        lines.append(f"```")
        lines.append("")

    # Dedup
    dedup = all_stats.get("dedup", {})
    if dedup:
        lines.append(f"### Step 2: Deduplication")
        lines.append(f"- Before: {dedup.get('before', '?')}")
        lines.append(f"- After: {dedup.get('after', '?')}")
        lines.append(f"- Removed: {dedup.get('removed', 0)}")
        lines.append("")

    # Stale
    stale = all_stats.get("stale", {})
    if stale:
        lines.append(f"### Step 3: Stale Cleanup ({stale.get('cutoff_days', 30)} day cutoff)")
        lines.append(f"- Before: {stale.get('before', '?')}")
        lines.append(f"- After: {stale.get('after', '?')}")
        lines.append(f"- Removed: {stale.get('removed', 0)}")
        lines.append("")

    # Grade
    grade = all_stats.get("grade", {})
    if grade:
        lines.append(f"### Step 4: Grading")
        lines.append(f"- Newly graded: {grade.get('graded', 0)}")
        lines.append(f"- Upgraded: {grade.get('upgraded', 0)}")
        lines.append("")

    # Fill gaps
    gaps = all_stats.get("fill_gaps", {})
    if gaps:
        lines.append(f"### Step 5: Gap Filling")
        for field, count in sorted(gaps.items()):
            lines.append(f"- {field}: {count} filled")
        lines.append("")

    # Normalize
    norm = all_stats.get("normalize", {})
    if norm:
        lines.append(f"### Step 6: Normalization")
        for field, count in sorted(norm.items()):
            lines.append(f"- {field}: {count} fixed")
        lines.append("")

    # Dashboard
    dash = all_stats.get("dashboard", {})
    if dash and "summary" in dash:
        s = dash["summary"]
        lines.append(f"### Step 7: Dashboard Rebuilt")
        lines.append(f"- Total: {s.get('total_jobs', '?')}")
        lines.append(f"- S-1: {s.get('s_grade_jobs', 0)} | A-grade: {s.get('a_grade_jobs', 0)}")
        lines.append(f"- T1: {s.get('t1_companies', 0)} | T2: {s.get('t2_companies', 0)}")
        lines.append("")

    # Coverage
    cov = all_stats.get("coverage", {})
    if cov and "total_jobs" in cov:
        lines.append(f"### Step 8: Coverage Report Updated")
        lines.append(f"- Total jobs: {cov['total_jobs']}")
        lines.append("")

    # Grade distribution
    grades = Counter(j.get("grade", "") for j in master)
    lines.append("## Final Grade Distribution")
    lines.append("")
    for g in sorted(grades.keys(), key=lambda x: GRADE_PRIORITY.get(x, 99)):
        bar = "█" * (grades[g] // 5)
        lines.append(f"| `{g}` | {grades[g]} | {bar} |")
    lines.append("")

    # Tier distribution
    tiers = Counter(j.get("tier", "") for j in master)
    lines.append("## Final Tier Distribution")
    lines.append("")
    for t in ["T1", "T2", "T3", ""]:
        label = t if t else "(none)"
        if tiers.get(t, 0) > 0:
            bar = "█" * (tiers[t] // 5)
            lines.append(f"| `{label}` | {tiers[t]} | {bar} |")
    lines.append("")

    # Field coverage
    lines.append("## Field Coverage")
    lines.append("")
    fields = [
        ("title", "Title"), ("company", "Company"), ("location", "Location"),
        ("url", "URL"), ("grade", "Grade"), ("en_title", "English Title"),
        ("summary", "Summary"), ("quality_tier", "Quality Tier"),
        ("quality_score", "Quality Score"), ("posted_date", "Posted Date"),
        ("status", "Status"), ("tier", "Tier"), ("source", "Source"),
    ]
    for key, label in fields:
        count = sum(1 for j in master if j.get(key))
        pct = count / total * 100 if total else 0
        lines.append(f"- **{label}**: {count}/{total} ({pct:.0f}%)")

    report_text = "\n".join(lines)

    if output_file:
        save_json(output_file, report_text) if output_file.endswith(".json") else None
        if not output_file.endswith(".json"):
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report_text)
        print(f"\n📄 Report saved to {output_file}")
    else:
        # Print to stdout
        print("\n" + report_text)

    return report_text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Career OS automated maintenance pipeline"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing files")
    parser.add_argument("--step", type=int, metavar="N",
                        help="Run only step N (1-9)")
    parser.add_argument("--report", action="store_true",
                        help="Generate markdown maintenance report")
    parser.add_argument("--report-file", type=str, default=None,
                        help="Write report to specified file")
    parser.add_argument("--stale-days", type=int, default=30,
                        help="Days threshold for stale job removal (default: 30)")
    args = parser.parse_args()

    print("=" * 70)
    print("  CAREER OS — Automated Maintenance Pipeline")
    print(f"  {'DRY RUN' if args.dry_run else 'LIVE RUN'} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    # Load master
    print("📂 Loading master jobs list...")
    master = load_json(MASTER_FILE)
    print(f"   {len(master)} jobs loaded")
    print()

    all_stats = {}
    steps_to_run = [args.step] if args.step else list(range(1, 10))

    # ── Step 1: Merge ──
    if 1 in steps_to_run:
        print("━━━ STEP 1/9: Merge Scraper Results ━━━")
        master, stats = step_merge(master, args.dry_run)
        all_stats["merge"] = stats
        print(f"   Master now has {len(master)} jobs")
        print()

    # ── Step 2: Dedup ──
    if 2 in steps_to_run:
        print("━━━ STEP 2/9: Deduplication ━━━")
        master, stats = step_dedup(master, args.dry_run)
        all_stats["dedup"] = stats
        print(f"   Removed {stats['removed']} duplicates ({stats['before']} → {stats['after']})")
        print()

    # ── Step 3: Stale cleanup ──
    if 3 in steps_to_run:
        print(f"━━━ STEP 3/9: Stale Cleanup ({args.stale_days} day cutoff) ━━━")
        master, stats = step_stale(master, args.dry_run, args.stale_days)
        all_stats["stale"] = stats
        print(f"   Removed {stats['removed']} stale jobs ({stats['before']} → {stats['after']})")
        print()

    # ── Step 4: Grade ──
    if 4 in steps_to_run:
        print("━━━ STEP 4/9: Grading ━━━")
        master, stats = step_grade(master, args.dry_run)
        all_stats["grade"] = stats
        print(f"   Graded {stats['graded']} new jobs, upgraded {stats['upgraded']}")
        print()

    # ── Step 5: Fill gaps ──
    if 5 in steps_to_run:
        print("━━━ STEP 5/9: Gap Filling ━━━")
        master, stats = step_fill_gaps(master, args.dry_run)
        all_stats["fill_gaps"] = stats
        total_filled = sum(stats.values())
        print(f"   Filled {total_filled} missing values: {dict(stats)}")
        print()

    # ── Step 6: Normalize ──
    if 6 in steps_to_run:
        print("━━━ STEP 6/9: Normalization ━━━")
        master, stats = step_normalize(master, args.dry_run)
        all_stats["normalize"] = stats
        total_fixed = sum(stats.values())
        print(f"   Fixed {total_fixed} inconsistencies: {dict(stats)}")
        print()

    # ── Step 7: Dashboard ──
    if 7 in steps_to_run:
        print("━━━ STEP 7/9: Dashboard Rebuild ━━━")
        stats = step_dashboard(master, args.dry_run)
        all_stats["dashboard"] = stats
        if "summary" in stats:
            s = stats["summary"]
            print(f"   Dashboard updated: {s['total_jobs']} jobs")
        else:
            print(f"   {stats}")
        print()

    # ── Step 8: Coverage ──
    if 8 in steps_to_run:
        print("━━━ STEP 8/9: Coverage Report ━━━")
        stats = step_coverage(master, args.dry_run)
        all_stats["coverage"] = stats
        print(f"   Coverage report updated")
        print()

    # ── Write master (if not dry run and changes were made) ──
    if not args.dry_run and any(s in steps_to_run for s in range(1, 7)):
        print("💾 Writing updated master file...")
        save_json(MASTER_FILE, master)
        print(f"   ✅ Saved {len(master)} jobs to {MASTER_FILE}")
        print()

    # ── Step 9: Report ──
    if 9 in steps_to_run or args.report:
        print("━━━ STEP 9/9: Summary Report ━━━")
        report_file = args.report_file or str(MARKDOWN_REPORT) if args.report else None
        step_report(master, all_stats, report_file)
        print()

    # ── Final summary ──
    print("=" * 70)
    print("  ✅ MAINTENANCE COMPLETE")
    print(f"  Total jobs: {len(master)}")
    grades = Counter(j.get("grade", "") for j in master)
    top_grades = sorted(grades.items(), key=lambda x: GRADE_PRIORITY.get(x[0], 99))[:4]
    print(f"  Top grades: {', '.join(f'{g}:{c}' for g, c in top_grades)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
