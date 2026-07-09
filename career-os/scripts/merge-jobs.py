#!/usr/bin/env python3
"""
merge-jobs.py — Merge new scraper results into the master jobs-all.json.

Scans all *-results.json files in career-os/scrapers/, deduplicates against the
existing master list, assigns grades & tiers, fills missing fields, and writes
back the merged result.

Usage:
    python3 merge-jobs.py              # merge and write
    python3 merge-jobs.py --dry-run    # preview changes without writing

Idempotent: running twice produces the same master file.
"""

import argparse
import glob
import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime

# ---------------------------------------------------------------------------
# Paths (relative to career-os/)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRAPERS_DIR = os.path.join(BASE_DIR, "scrapers")
MASTER_DIR = os.path.join(BASE_DIR, "OKComputer_职位搜索清单")
MASTER_FILE = os.path.join(MASTER_DIR, "jobs-all.json")

# ---------------------------------------------------------------------------
# Company prestige tiers
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
# Grade assignment rules (ordered by priority — first match wins)
# ---------------------------------------------------------------------------
GRADE_RULES = [
    # S-1: C-suite / founding
    (r"\b(cto|ceo|coo|cfo|chief\s+product|founder|co-founder)\b", "S-1"),
    # A-1: VP / Director / Head
    (r"\b(vp|vice\s+president|director|head\s+of|principal\s+(product|pm)|product\s+lead|product\s+owner)\b", "A-1"),
    # A-2: Senior PM
    (r"\b(senior\s+(product\s+manager|pm)|sr\.?\s+(product\s+manager|pm))\b", "A-2"),
    # A-2: Strategy / Growth / Program lead roles
    (r"\b(strategy\s+expert|growth\s+(manager|lead|head)|program\s+manager)\b", "A-2"),
    # B-1: Mid PM
    (r"\b(product\s+manager|pm\b)", "B-1"),
    # B: Associate / junior PM
    (r"\b(associate\s+product\s+manager|junior\s+(product\s+manager|pm)|product\s+analyst)\b", "B"),
]

# Grade priority for conflict resolution (lower = higher priority)
GRADE_PRIORITY = {"S-1": 0, "A-1": 1, "A-2": 2, "B-1": 3, "B": 4, "C": 5, "": 6}


# ---------------------------------------------------------------------------
# Chinese → English title translation (common PM titles)
# ---------------------------------------------------------------------------
ZH_TO_EN_TITLES = {
    "产品总监": "Product Director",
    "产品VP": "VP of Product",
    "产品经理": "Product Manager",
    "高级产品经理": "Senior Product Manager",
    "资深产品经理": "Senior Product Manager",
    "产品专家": "Product Specialist",
    "产品负责人": "Head of Product",
    "产品负责人/产品总监": "Head of Product / Product Director",
    "产品VP/产品总监": "VP of Product / Product Director",
    "用户增长经理": "Growth Product Manager",
    "增长产品经理": "Growth Product Manager",
    "数据产品经理": "Data Product Manager",
    "商业化产品经理": "Monetization Product Manager",
    "B端产品经理": "B2B Product Manager",
    "C端产品经理": "B2C Product Manager",
    "AI产品经理": "AI Product Manager",
    "策略产品经理": "Strategy Product Manager",
    "国际化产品经理": "Internationalization Product Manager",
    "深圳总监": "Director (Shenzhen)",
}


def normalize_company(name: str) -> str:
    """Lowercase and strip whitespace for matching."""
    return (name or "").strip().lower()


def is_chinese(text: str) -> bool:
    """Check if text is predominantly Chinese characters."""
    if not text:
        return False
    chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    return chinese_chars > len(text) * 0.3


def extract_company_from_title(title: str) -> str:
    """Try to extract company name from title patterns like 'Senior PM - Klook'."""
    for sep in [" - ", " – ", " | ", " @ ", "，"]:
        if sep in title:
            candidate = title.rsplit(sep, 1)[-1].strip()
            # Only return if it looks like a company name (not a location)
            if candidate and len(candidate) > 1 and not re.match(
                r"^(Remote|Singapore|Hong Kong|Beijing|Shanghai|Shenzhen|Tokyo|London|New York|Remote\(|Asia|APAC|Global|Multiple)",
                candidate,
                re.IGNORECASE,
            ):
                return candidate
    return ""


def translate_title(title: str) -> str:
    """Provide English translation for Chinese job titles."""
    if not title or not is_chinese(title):
        return title  # Already English or empty

    # Direct match
    clean = title.strip()
    if clean in ZH_TO_EN_TITLES:
        return ZH_TO_EN_TITLES[clean]

    # Partial match — try to translate known Chinese terms
    translated = clean
    for zh, en in sorted(ZH_TO_EN_TITLES.items(), key=lambda x: -len(x[0])):
        translated = translated.replace(zh, en)

    # If still mostly Chinese after replacement, return generic
    if is_chinese(translated):
        return "Product-related role (Chinese title)"

    return translated


def assign_grade(title: str, existing_grade: str) -> str:
    """Assign grade based on title keywords. Keeps existing grade if higher priority."""
    if not title:
        return existing_grade or ""

    title_lower = title.lower()
    new_grade = ""
    for pattern, grade in GRADE_RULES:
        if re.search(pattern, title_lower, re.IGNORECASE):
            new_grade = grade
            break

    if not new_grade:
        new_grade = "C"

    # Keep the higher-priority grade
    existing_pri = GRADE_PRIORITY.get(existing_grade, 6)
    new_pri = GRADE_PRIORITY.get(new_grade, 6)
    return new_grade if new_pri < existing_pri else (existing_grade or new_grade)


def assign_tier(company: str) -> str:
    """Assign tier based on company prestige."""
    c = normalize_company(company)
    if not c:
        return ""
    if c in T1_COMPANIES:
        return "T1"
    if c in T2_COMPANIES:
        return "T2"
    if c in T3_COMPANIES:
        return "T3"
    return "T3"  # Unknown companies default to T3


def make_dedup_key(title: str, company: str, location: str) -> str:
    """
    Create a deduplication key from title + company + location.
    Normalizes to reduce false non-matches.
    """
    def norm(s):
        return re.sub(r"\s+", " ", s.lower().strip())

    t = norm(title)
    c = norm(company)
    l = norm(location)

    # Strip common suffixes/prefixes from title for matching
    t = re.sub(r"\s*[-–|@].*$", "", t)  # Remove trailing separators + what follows (often company)
    t = re.sub(r"\s*\([^)]*\)\s*$", "", t)  # Remove trailing parens
    t = re.sub(r"\s*\b(remote|singapore|hong kong|beijing|shanghai|shenzhen|tokyo|london|new york|asia|apac|global)\b\s*$", "", t, flags=re.IGNORECASE)

    raw = f"{t}|||{c}|||{l}"
    return hashlib.md5(raw.encode()).hexdigest()


def make_job_id(url: str, title: str) -> str:
    """Generate a stable job_id from URL + title."""
    raw = f"{url}|{title}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def generate_summary(job: dict) -> str:
    """Generate a one-liner summary from available fields."""
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


def load_json(path: str) -> list:
    """Load a JSON file, return empty list on error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
        print(f"  ⚠️  Skipping {os.path.basename(path)}: {e}", file=sys.stderr)
        return []


def enrich_job(job: dict) -> dict:
    """Fill missing fields: grade, tier, en_title, summary, job_id."""
    title = job.get("title", "")
    company = job.get("company", "")
    location = job.get("location", "") or job.get("location_norm", "")

    # Grade
    job["grade"] = assign_grade(title, job.get("grade", ""))

    # Tier
    job["tier"] = assign_tier(company)

    # English title
    if not job.get("en_title"):
        job["en_title"] = translate_title(title)

    # Summary
    if not job.get("summary"):
        job["summary"] = generate_summary(job)

    # job_id
    if not job.get("job_id"):
        job["job_id"] = make_job_id(job.get("url", ""), title)

    # status defaults
    if not job.get("status"):
        job["status"] = "not_applied"

    # Ensure company is populated
    if not company:
        extracted = extract_company_from_title(title)
        if extracted:
            job["company"] = extracted
            # Re-evaluate tier with extracted company
            job["tier"] = assign_tier(extracted)

    # location_norm
    if not job.get("location_norm"):
        job["location_norm"] = location

    return job


def load_all_results() -> list:
    """Load all *-results.json files from scrapers directory."""
    pattern = os.path.join(SCRAPERS_DIR, "*-results.json")
    files = sorted(glob.glob(pattern))
    all_jobs = []
    for path in files:
        jobs = load_json(path)
        source = os.path.basename(path).replace("-results.json", "")
        for job in jobs:
            if not job.get("source"):
                job["source"] = source
        all_jobs.extend(jobs)
    return all_jobs


def load_master() -> list:
    """Load the existing master jobs file."""
    return load_json(MASTER_FILE)


def merge(master: list, new_jobs: list):
    """
    Merge new_jobs into master. Returns (merged, stats).

    Stats: new_added, duplicates_skipped
    """
    # Build existing lookup: dedup_key → index (use raw fields, pre-enrichment)
    existing_keys = {}
    for i, job in enumerate(master):
        key = make_dedup_key(
            job.get("title", ""),
            job.get("company", ""),
            job.get("location", "") or job.get("location_norm", ""),
        )
        existing_keys[key] = i

    # Also build URL-based dedup for cases where title differs but URL matches
    existing_urls = set()
    for job in master:
        url = job.get("url", "")
        if url:
            existing_urls.add(url)

    new_added = 0
    duplicates_skipped = 0

    for job in new_jobs:
        # Check dedup BEFORE enrichment (raw fields only)
        title = job.get("title", "")
        company = job.get("company", "")
        location = job.get("location", "") or job.get("location_norm", "")
        url = job.get("url", "")

        dedup_key = make_dedup_key(title, company, location)

        # Check dedup by key OR by URL
        if dedup_key in existing_keys or (url and url in existing_urls):
            duplicates_skipped += 1
            continue

        # Now enrich
        job = enrich_job(job)
        # Set date if missing
        if not job.get("scanned_date"):
            job["scanned_date"] = datetime.now().strftime("%Y-%m-%d")

        master.append(job)
        existing_keys[dedup_key] = len(master) - 1
        if url:
            existing_urls.add(url)
        new_added += 1

    return master, new_added, duplicates_skipped


def print_stats(master: list, new_added: int, duplicates_skipped: int, results_count: int):
    """Print summary statistics."""
    print("\n" + "=" * 60)
    print("  MERGE RESULTS")
    print("=" * 60)
    print(f"  Scraper results scanned : {results_count}")
    print(f"  New jobs added          : {new_added}")
    print(f"  Duplicates skipped      : {duplicates_skipped}")
    print(f"  Total jobs in master    : {len(master)}")
    print()

    # Grade distribution
    grades = Counter(j.get("grade", "?") for j in master)
    print("  Grade Distribution:")
    for g in sorted(grades.keys(), key=lambda x: GRADE_PRIORITY.get(x, 99)):
        bar = "█" * (grades[g] // 5)
        print(f"    {g:>5} : {grades[g]:>4}  {bar}")
    print()

    # Tier distribution
    tiers = Counter(j.get("tier", "") for j in master)
    print("  Tier Distribution:")
    for t in ["T1", "T2", "T3", ""]:
        label = t if t else "(none)"
        if tiers.get(t, 0) > 0:
            bar = "█" * (tiers[t] // 5)
            print(f"    {label:>5} : {tiers[t]:>4}  {bar}")
    print()

    # Source distribution
    sources = Counter(j.get("source", "?") for j in master)
    print("  Top Sources:")
    for src, count in sources.most_common(10):
        print(f"    {src:<30} : {count:>4}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Merge scraper results into master jobs list")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()

    print("🔄 Loading scraper results...")
    new_jobs = load_all_results()
    print(f"   Found {len(new_jobs)} jobs across scraper files")

    print("📂 Loading existing master list...")
    master = load_master()
    print(f"   Existing master: {len(master)} jobs")

    print("🔀 Merging with deduplication...")
    merged, new_added, duplicates_skipped = merge(master, new_jobs)

    print_stats(merged, new_added, duplicates_skipped, len(new_jobs))

    if args.dry_run:
        print("\n🔍 DRY RUN — no files written.")
        if new_added > 0:
            print(f"   Would add {new_added} new jobs to master.")
        return

    # Ensure output directory exists
    os.makedirs(MASTER_DIR, exist_ok=True)

    # Write merged result
    print(f"\n💾 Writing {len(merged)} jobs to {MASTER_FILE}...")
    with open(MASTER_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    print("   ✅ Done!")


if __name__ == "__main__":
    main()
