#!/usr/bin/env python3
"""
Health Check System for Career OS Infrastructure
Runs every 15 minutes to monitor system health
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path(__file__).resolve().parents[3]))
CAREER_OS = WORKSPACE / "career-os"
RESULTS_FILE = CAREER_OS / "infra-bot" / "health_results.json"

# Configuration
GITHUB_DASHBOARD_URL = "https://1ancol000.github.io/automation/OKComputer_职位搜索清单/job-database-senior.html"
GITHUB_API_BASE = "https://api.github.com/repos/1anard000/automation"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
JOBS_DB_FILE = CAREER_OS / "jobs-all.json"
CRM_DB_FILE = CAREER_OS / "crm" / "crm.db"
COVER_LETTERS_DIR = CAREER_OS / "cover-letters"


def log(message: str):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Encode to handle special characters
    print(f"[{timestamp}] {message}".encode('utf-8', errors='replace').decode('utf-8'))


def check_github_pages() -> dict:
    """Check if GitHub Pages dashboard is accessible"""
    result = {
        "name": "GitHub Pages",
        "status": "healthy",
        "details": "",
        "auto_fixable": False
    }
    
    try:
        # Encode URL to handle Chinese characters
        encoded_url = GITHUB_DASHBOARD_URL.encode('utf-8').decode('utf-8')
        req = Request(encoded_url, headers={"User-Agent": "CareerOS-HealthCheck"})
        response = urlopen(req, timeout=10)
        if response.status == 200:
            result["details"] = "Dashboard accessible"
            log("✅ GitHub Pages: Dashboard accessible")
        else:
            result["status"] = "error"
            result["details"] = f"HTTP {response.status}"
            result["auto_fixable"] = True
            log(f"❌ GitHub Pages: HTTP {response.status}")
    except HTTPError as e:
        result["status"] = "error"
        result["details"] = f"HTTP {e.code}"
        result["auto_fixable"] = True
        if e.code == 404:
            log("❌ GitHub Pages: 404 - Not configured or branch missing")
        else:
            log(f"❌ GitHub Pages: HTTP {e.code}")
    except URLError as e:
        result["status"] = "error"
        result["details"] = str(e.reason)
        result["auto_fixable"] = True
        log(f"❌ GitHub Pages: {e.reason}")
    except Exception as e:
        result["status"] = "error"
        result["details"] = str(e)
        result["auto_fixable"] = False
        log(f"❌ GitHub Pages: {e}")
    
    return result


def check_cron_jobs() -> dict:
    """Check if all cron jobs are running properly"""
    result = {
        "name": "Cron Jobs",
        "status": "healthy",
        "details": "",
        "auto_fixable": False,
        "issues": []
    }
    
    try:
        # Use cron tool to list jobs
        cmd = ["node", "-e", """
            const { execSync } = require('child_process');
            try {
                const result = execSync('openclaw cron list', { encoding: 'utf8' });
                console.log(result);
            } catch (e) {
                console.error(e.message);
                process.exit(1);
            }
        """]
        output = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if output.returncode != 0:
            result["status"] = "error"
            result["details"] = "Failed to list cron jobs"
            result["auto_fixable"] = True
            log(f"❌ Cron Jobs: {output.stderr}")
            return result
        
        # Parse cron jobs
        jobs = []
        for line in output.stdout.strip().split('\n'):
            if line.strip():
                jobs.append(line.strip())
        
        if len(jobs) < 10:
            result["status"] = "warning"
            result["details"] = f"Only {len(jobs)} jobs found (expected 10+)"
            result["issues"].append(f"Missing jobs: expected 10+, found {len(jobs)}")
            log(f"⚠️ Cron Jobs: Only {len(jobs)} jobs found")
        else:
            log(f"✅ Cron Jobs: {len(jobs)} jobs running")
        
        # Check for errors in job output
        result["details"] = f"{len(jobs)} jobs active"
        
    except subprocess.TimeoutExpired:
        result["status"] = "error"
        result["details"] = "Timeout checking cron jobs"
        result["auto_fixable"] = True
        log("❌ Cron Jobs: Timeout")
    except Exception as e:
        result["status"] = "error"
        result["details"] = str(e)
        result["auto_fixable"] = False
        log(f"❌ Cron Jobs: {e}")
    
    return result


def check_database() -> dict:
    """Check if jobs database is healthy and up-to-date"""
    result = {
        "name": "Database",
        "status": "healthy",
        "details": "",
        "auto_fixable": False
    }
    
    if not JOBS_DB_FILE.exists():
        result["status"] = "error"
        result["details"] = "jobs-all.json not found"
        result["auto_fixable"] = True
        log("❌ Database: jobs-all.json not found")
        return result
    
    try:
        with open(JOBS_DB_FILE, 'r') as f:
            data = json.load(f)
        
        job_count = len(data) if isinstance(data, list) else 0
        
        if job_count < 100:
            result["status"] = "warning"
            result["details"] = f"Only {job_count} jobs (expected 100+)"
            result["auto_fixable"] = True
            log(f"⚠️ Database: Only {job_count} jobs")
        else:
            log(f"✅ Database: {job_count} jobs")
        
        # Check last merge timestamp
        # Look for metadata in the file or check file modification time
        file_mtime = datetime.fromtimestamp(JOBS_DB_FILE.stat().st_mtime)
        now = datetime.now()
        age_hours = (now - file_mtime).total_seconds() / 3600
        
        if age_hours > 4:
            result["status"] = "warning" if result["status"] == "healthy" else result["status"]
            result["details"] += f"; Last update {age_hours:.1f}h ago"
            result["auto_fixable"] = True
            log(f"⚠️ Database: Last update {age_hours:.1f}h ago (>4h)")
        else:
            result["details"] = f"{job_count} jobs, updated {age_hours:.1f}h ago"
            
    except json.JSONDecodeError:
        result["status"] = "error"
        result["details"] = "Invalid JSON"
        result["auto_fixable"] = False
        log("❌ Database: Invalid JSON")
    except Exception as e:
        result["status"] = "error"
        result["details"] = str(e)
        result["auto_fixable"] = False
        log(f"❌ Database: {e}")
    
    return result


def check_crm() -> dict:
    """Check if CRM database and API are healthy"""
    result = {
        "name": "CRM",
        "status": "healthy",
        "details": "",
        "auto_fixable": False
    }
    
    if not CRM_DB_FILE.exists():
        result["status"] = "error"
        result["details"] = "CRM database not found"
        result["auto_fixable"] = True
        log("❌ CRM: Database not found")
        return result
    
    log("✅ CRM: Database exists")
    
    # Try to ping API server if running
    # Assuming API runs on port 3000
    try:
        req = Request("http://localhost:3000/health", headers={"User-Agent": "CareerOS-HealthCheck"})
        response = urlopen(req, timeout=5)
        if response.status == 200:
            result["details"] = "API responding"
            log("✅ CRM: API responding")
        else:
            result["status"] = "warning"
            result["details"] = f"API returned {response.status}"
            log(f"⚠️ CRM: API returned {response.status}")
    except (URLError, HTTPError):
        result["status"] = "warning"
        result["details"] = "API not responding (may not be running)"
        log("⚠️ CRM: API not responding")
    except Exception as e:
        result["details"] = "API status unknown"
        log(f"ℹ️ CRM: API check skipped ({e})")
    
    return result


def check_cover_letters() -> dict:
    """Check cover letter coverage"""
    result = {
        "name": "Cover Letters",
        "status": "healthy",
        "details": "",
        "auto_fixable": False
    }
    
    if not COVER_LETTERS_DIR.exists():
        result["status"] = "warning"
        result["details"] = "Cover letters directory not found"
        result["auto_fixable"] = True
        log("⚠️ Cover Letters: Directory not found")
        return result
    
    try:
        # Count .docx files
        docx_files = list(COVER_LETTERS_DIR.glob("*.docx"))
        count = len(docx_files)
        
        # Check jobs database for A-1 jobs without cover letters
        if JOBS_DB_FILE.exists():
            with open(JOBS_DB_FILE, 'r') as f:
                jobs = json.load(f)
            
            a1_jobs = [j for j in jobs if isinstance(j, dict) and j.get('priority') == 'A-1']
            a1_count = len(a1_jobs)
            
            # Simple heuristic: assume we need cover letters for A-1 jobs
            gap = max(0, a1_count - count)
            
            if gap > 10:
                result["status"] = "warning"
                result["details"] = f"{count} cover letters, {gap} A-1 jobs without"
                result["auto_fixable"] = True
                log(f"⚠️ Cover Letters: {count} files, {gap} A-1 jobs need letters")
            else:
                result["details"] = f"{count} cover letters, gap: {gap}"
                log(f"✅ Cover Letters: {count} files, gap: {gap}")
        else:
            result["details"] = f"{count} cover letters"
            log(f"✅ Cover Letters: {count} files")
            
    except Exception as e:
        result["status"] = "error"
        result["details"] = str(e)
        result["auto_fixable"] = False
        log(f"❌ Cover Letters: {e}")
    
    return result


def run_health_checks() -> dict:
    """Run all health checks and return results"""
    log("🔍 Starting health checks...")
    
    checks = [
        check_github_pages(),
        check_cron_jobs(),
        check_database(),
        check_crm(),
        check_cover_letters()
    ]
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "checks": checks,
        "summary": {
            "total": len(checks),
            "healthy": sum(1 for c in checks if c["status"] == "healthy"),
            "warnings": sum(1 for c in checks if c["status"] == "warning"),
            "errors": sum(1 for c in checks if c["status"] == "error"),
            "auto_fixable": sum(1 for c in checks if c.get("auto_fixable", False))
        }
    }
    
    # Save results
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    log(f"📊 Summary: {results['summary']['healthy']}/{results['summary']['total']} healthy, "
        f"{results['summary']['warnings']} warnings, {results['summary']['errors']} errors")
    
    return results


if __name__ == "__main__":
    results = run_health_checks()
    sys.exit(0 if results["summary"]["errors"] == 0 else 1)
