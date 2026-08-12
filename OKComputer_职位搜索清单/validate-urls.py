#!/usr/bin/env python3
"""
Automated URL validation for job postings.
Checks all jobs for broken URLs and generates a report.
Run periodically to catch dead links before they waste application time.
"""
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

JOBS_FILE = "jobs-all.json"
REPORT_FILE = "url-validation-report.json"
TIMEOUT = 10  # seconds per request
BATCH_SIZE = 50  # jobs per batch
DELAY = 0.3  # seconds between requests to avoid rate limits

def load_jobs():
    with open(JOBS_FILE) as f:
        return json.load(f)

def check_url(url, timeout=TIMEOUT):
    """Check if URL is reachable. Returns (status, code, redirect_url)."""
    if not url or not url.startswith("http"):
        return "invalid", 0, None
    
    try:
        req = Request(url, method="HEAD", headers={
            "User-Agent": "Mozilla/5.0 (compatible; CareerOS/1.0)"
        })
        resp = urlopen(req, timeout=timeout)
        return "ok", resp.status, resp.url
    except HTTPError as e:
        # HEAD might not be allowed, try GET with small range
        try:
            req = Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; CareerOS/1.0)"
            })
            resp = urlopen(req, timeout=timeout)
            return "ok", resp.status, resp.url
        except HTTPError as e2:
            return "error", e2.code, None
        except Exception as e2:
            return "error", 0, str(e2)
    except URLError as e:
        return "unreachable", 0, str(e.reason)
    except Exception as e:
        return "error", 0, str(e)

def main():
    jobs = load_jobs()
    total = len(jobs)
    
    # Check only jobs with URLs
    jobs_with_urls = [(i, j) for i, j in enumerate(jobs) if j.get("url", "").startswith("http")]
    
    print(f"📋 Validating URLs for {len(jobs_with_urls)} jobs with links (out of {total} total)...")
    
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_jobs": total,
        "jobs_checked": len(jobs_with_urls),
        "ok": 0,
        "broken": 0,
        "unreachable": 0,
        "invalid": 0,
        "errors": [],
        "by_source": {}
    }
    
    for batch_start in range(0, len(jobs_with_urls), BATCH_SIZE):
        batch = jobs_with_urls[batch_start:batch_start + BATCH_SIZE]
        
        for idx, job in batch:
            url = job.get("url", "")
            status, code, redirect = check_url(url)
            
            source = job.get("source", "unknown")
            if source not in results["by_source"]:
                results["by_source"][source] = {"ok": 0, "broken": 0, "unreachable": 0, "total": 0}
            results["by_source"][source]["total"] += 1
            
            if status == "ok":
                results["ok"] += 1
                results["by_source"][source]["ok"] += 1
            elif status in ("error", "unreachable"):
                results["broken"] += 1
                results["by_source"][source]["broken"] += 1
                results["errors"].append({
                    "index": idx,
                    "title": job.get("title", "Unknown"),
                    "company": job.get("company", "Unknown"),
                    "url": url,
                    "status": status,
                    "code": code,
                    "detail": str(redirect or code)[:200]
                })
            else:
                results["invalid"] += 1
            
            time.sleep(DELAY)
        
        # Progress
        done = min(batch_start + BATCH_SIZE, len(jobs_with_urls))
        print(f"  ✓ {done}/{len(jobs_with_urls)} checked...")
    
    # Save report
    with open(REPORT_FILE, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 URL Validation Report:")
    print(f"  ✅ OK: {results['ok']}")
    print(f"  ❌ Broken: {results['broken']}")
    print(f"  🚫 Unreachable: {results['unreachable']}")
    print(f"  ⚠️  Invalid: {results['invalid']}")
    
    if results["errors"]:
        print(f"\n🔧 Top broken URLs:")
        for e in results["errors"][:10]:
            print(f"  [{e['status']}] {e['company']}: {e['title'][:50]}...")
            print(f"    {e['url'][:80]}")
    
    # Source breakdown
    print(f"\n📡 By Source:")
    for source, stats in sorted(results["by_source"].items(), key=lambda x: -x[1]["broken"]):
        if stats["broken"] > 0:
            print(f"  {source}: {stats['broken']}/{stats['total']} broken")
    
    return results["broken"]

if __name__ == "__main__":
    broken = main()
    sys.exit(1 if broken > 0 else 0)
