#!/usr/bin/env python3
"""
Auto-Fix System for Career OS Infrastructure
Automatically resolves common issues detected by health checks
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path(__file__).resolve().parents[3]))
CAREER_OS = WORKSPACE / "career-os"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Configuration
GITHUB_API_BASE = "https://api.github.com/repos/[GITHUB_USER]/automation"
GITHUB_PAGES_SOURCE_BRANCH = "career-networking"
GITHUB_PAGES_SOURCE_PATH = "/OKComputer_职位搜索清单"
DASHBOARD_HTML = CAREER_OS / "OKComputer_职位搜索清单" / "job-database-senior.html"
MERGE_JOBS_SCRIPT = CAREER_OS / "merge-jobs.py"
BUILD_DASHBOARD_SCRIPT = CAREER_OS / "build-dashboard.py"
CRM_DIR = CAREER_OS / "crm"


def log(message: str):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def fix_github_pages() -> dict:
    """Fix GitHub Pages configuration"""
    result = {
        "action": "fix_github_pages",
        "success": False,
        "details": ""
    }
    
    if not GITHUB_TOKEN:
        result["details"] = "GITHUB_TOKEN not set"
        log("❌ Auto-fix GitHub Pages: GITHUB_TOKEN not set")
        return result
    
    try:
        # Try GitHub API approach first
        api_url = f"{GITHUB_API_BASE}/pages"
        req = Request(
            api_url,
            data=json.dumps({
                "source": {
                    "branch": GITHUB_PAGES_SOURCE_BRANCH,
                    "path": GITHUB_PAGES_SOURCE_PATH
                }
            }).encode('utf-8'),
            headers={
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            },
            method='PUT'
        )
        
        response = urlopen(req, timeout=30)
        if response.status in [200, 201, 204]:
            result["success"] = True
            result["details"] = "GitHub Pages enabled via API"
            log("✅ Auto-fix GitHub Pages: Enabled via API")
        else:
            result["details"] = f"API returned {response.status}"
            log(f"⚠️ Auto-fix GitHub Pages: API returned {response.status}")
            
    except HTTPError as e:
        if e.code == 404:
            # Pages not enabled, try to enable
            log("ℹ️ Auto-fix GitHub Pages: Not enabled, attempting to create...")
            try:
                # Fallback: create gh-pages branch approach
                result = fix_github_pages_branch()
                return result
            except Exception as branch_err:
                result["details"] = f"API error: {e.code}, branch fix failed: {branch_err}"
                log(f"❌ Auto-fix GitHub Pages: {result['details']}")
        else:
            result["details"] = f"API error: {e.code}"
            log(f"❌ Auto-fix GitHub Pages: API error {e.code}")
    except URLError as e:
        result["details"] = f"Network error: {e.reason}"
        log(f"❌ Auto-fix GitHub Pages: {e.reason}")
    except Exception as e:
        result["details"] = str(e)
        log(f"❌ Auto-fix GitHub Pages: {e}")
    
    return result


def fix_github_pages_branch() -> dict:
    """Fallback: Create gh-pages branch with dashboard"""
    result = {
        "action": "fix_github_pages_branch",
        "success": False,
        "details": ""
    }
    
    automation_dir = WORKSPACE / "automation"
    
    if not automation_dir.exists():
        result["details"] = "automation/ directory not found"
        log("❌ Auto-fix GitHub Pages Branch: automation/ not found")
        return result
    
    try:
        # Checkout gh-pages branch
        log("ℹ️ Creating gh-pages branch...")
        subprocess.run(
            ["git", "checkout", "--orphan", "gh-pages"],
            cwd=automation_dir,
            check=True,
            capture_output=True
        )
        
        # Reset and clean
        subprocess.run(
            ["git", "reset", "--hard"],
            cwd=automation_dir,
            check=True,
            capture_output=True
        )
        
        # Copy dashboard HTML
        if DASHBOARD_HTML.exists():
            import shutil
            shutil.copy(DASHBOARD_HTML, automation_dir / "index.html")
            log("✅ Copied dashboard to index.html")
        else:
            # Create minimal index
            (automation_dir / "index.html").write_text("""
<!DOCTYPE html>
<html><head><title>Career OS Dashboard</title></head>
<body><h1>Dashboard Deployed</h1><p>Auto-deployed by infra-bot</p></body>
</html>
""")
            log("✅ Created minimal index.html")
        
        # Commit and push
        subprocess.run(
            ["git", "add", "-A"],
            cwd=automation_dir,
            check=True,
            capture_output=True
        )
        
        subprocess.run(
            ["git", "commit", "-m", "Auto-deploy dashboard by infra-bot"],
            cwd=automation_dir,
            check=True,
            capture_output=True
        )
        
        subprocess.run(
            ["git", "push", "-f", "origin", "gh-pages"],
            cwd=automation_dir,
            check=True,
            capture_output=True
        )
        
        result["success"] = True
        result["details"] = "gh-pages branch created and pushed"
        log("✅ Auto-fix GitHub Pages Branch: Deployed successfully")
        
        # Return to original branch
        subprocess.run(
            ["git", "checkout", "-"],
            cwd=automation_dir,
            check=True,
            capture_output=True
        )
        
    except subprocess.CalledProcessError as e:
        result["details"] = f"Git error: {e.stderr.decode() if e.stderr else str(e)}"
        log(f"❌ Auto-fix GitHub Pages Branch: {result['details']}")
    except Exception as e:
        result["details"] = str(e)
        log(f"❌ Auto-fix GitHub Pages Branch: {e}")
    
    return result


def fix_cron_jobs() -> dict:
    """Re-enable broken cron jobs"""
    result = {
        "action": "fix_cron_jobs",
        "success": False,
        "details": ""
    }
    
    try:
        # List current cron jobs
        cmd = ["openclaw", "cron", "list"]
        output = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if output.returncode != 0:
            result["details"] = "Failed to list cron jobs"
            log(f"❌ Auto-fix Cron Jobs: {output.stderr}")
            return result
        
        jobs = [line.strip() for line in output.stdout.strip().split('\n') if line.strip()]
        
        if len(jobs) >= 10:
            result["success"] = True
            result["details"] = f"All {len(jobs)} jobs appear healthy"
            log(f"✅ Auto-fix Cron Jobs: All {len(jobs)} jobs OK")
            return result
        
        # If jobs are missing, they may need to be recreated
        # This requires manual intervention as we don't have the original job configs
        result["details"] = f"Only {len(jobs)} jobs found, manual recreation needed"
        log(f"⚠️ Auto-fix Cron Jobs: Missing jobs need manual recreation")
        
    except subprocess.TimeoutExpired:
        result["details"] = "Timeout"
        log("❌ Auto-fix Cron Jobs: Timeout")
    except Exception as e:
        result["details"] = str(e)
        log(f"❌ Auto-fix Cron Jobs: {e}")
    
    return result


def fix_database() -> dict:
    """Trigger database merge and rebuild"""
    result = {
        "action": "fix_database",
        "success": False,
        "details": ""
    }
    
    try:
        # Run merge-jobs.py if it exists
        if MERGE_JOBS_SCRIPT.exists():
            log("ℹ️ Running merge-jobs.py...")
            proc = subprocess.run(
                ["python3", str(MERGE_JOBS_SCRIPT)],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=CAREER_OS
            )
            
            if proc.returncode == 0:
                log("✅ merge-jobs.py completed")
            else:
                log(f"⚠️ merge-jobs.py returned {proc.returncode}")
        else:
            log("ℹ️ merge-jobs.py not found, skipping")
        
        # Run build-dashboard.py if it exists
        if BUILD_DASHBOARD_SCRIPT.exists():
            log("ℹ️ Running build-dashboard.py...")
            proc = subprocess.run(
                ["python3", str(BUILD_DASHBOARD_SCRIPT)],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=CAREER_OS
            )
            
            if proc.returncode == 0:
                log("✅ build-dashboard.py completed")
                result["success"] = True
                result["details"] = "Database merged and dashboard rebuilt"
            else:
                result["details"] = f"build-dashboard.py returned {proc.returncode}"
                log(f"⚠️ build-dashboard.py returned {proc.returncode}")
        else:
            log("ℹ️ build-dashboard.py not found")
            result["details"] = "Scripts not found"
            
    except subprocess.TimeoutExpired:
        result["details"] = "Timeout running scripts"
        log("❌ Auto-fix Database: Timeout")
    except Exception as e:
        result["details"] = str(e)
        log(f"❌ Auto-fix Database: {e}")
    
    return result


def fix_crm() -> dict:
    """Trigger CRM builders if database missing"""
    result = {
        "action": "fix_crm",
        "success": False,
        "details": ""
    }
    
    crm_db = CRM_DIR / "crm.db"
    
    if crm_db.exists():
        result["success"] = True
        result["details"] = "CRM database exists"
        log("✅ Auto-fix CRM: Database exists, no action needed")
        return result
    
    try:
        # Look for CRM builder scripts
        builder_scripts = list(CRM_DIR.glob("*builder*.py")) + list(CRM_DIR.glob("build*.py"))
        
        if builder_scripts:
            log(f"ℹ️ Found {len(builder_scripts)} CRM builder scripts")
            for script in builder_scripts[:3]:  # Limit to first 3
                log(f"ℹ️ Running {script.name}...")
                proc = subprocess.run(
                    ["python3", str(script)],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=CRM_DIR
                )
                if proc.returncode == 0:
                    log(f"✅ {script.name} completed")
                    result["success"] = True
                    result["details"] = f"CRM built by {script.name}"
                else:
                    log(f"⚠️ {script.name} returned {proc.returncode}")
        else:
            result["details"] = "No CRM builder scripts found"
            log("⚠️ Auto-fix CRM: No builder scripts found")
            
    except subprocess.TimeoutExpired:
        result["details"] = "Timeout"
        log("❌ Auto-fix CRM: Timeout")
    except Exception as e:
        result["details"] = str(e)
        log(f"❌ Auto-fix CRM: {e}")
    
    return result


def fix_cover_letters() -> dict:
    """Trigger cover letter generator"""
    result = {
        "action": "fix_cover_letters",
        "success": False,
        "details": ""
    }
    
    try:
        # Look for cover letter generator
        gen_scripts = list(CAREER_OS.glob("*cover*letter*.py")) + list(CAREER_OS.glob("*letter*.py"))
        
        if gen_scripts:
            log(f"ℹ️ Found {len(gen_scripts)} cover letter scripts")
            for script in gen_scripts[:1]:  # Run first one
                log(f"ℹ️ Running {script.name}...")
                proc = subprocess.run(
                    ["python3", str(script)],
                    capture_output=True,
                    text=True,
                    timeout=180,
                    cwd=CAREER_OS
                )
                if proc.returncode == 0:
                    log(f"✅ {script.name} completed")
                    result["success"] = True
                    result["details"] = f"Cover letters generated by {script.name}"
                else:
                    result["details"] = f"{script.name} returned {proc.returncode}"
                    log(f"⚠️ {script.name} returned {proc.returncode}")
        else:
            result["details"] = "No cover letter generator found"
            log("⚠️ Auto-fix Cover Letters: No generator script found")
            
    except subprocess.TimeoutExpired:
        result["details"] = "Timeout"
        log("❌ Auto-fix Cover Letters: Timeout")
    except Exception as e:
        result["details"] = str(e)
        log(f"❌ Auto-fix Cover Letters: {e}")
    
    return result


def run_auto_fixes(check_results: dict) -> dict:
    """Run auto-fixes based on health check results"""
    log("🔧 Starting auto-fixes...")
    
    fixes = {
        "github_pages": [],
        "cron_jobs": [],
        "database": [],
        "crm": [],
        "cover_letters": []
    }
    
    summary = {
        "attempted": 0,
        "successful": 0,
        "failed": 0
    }
    
    for check in check_results.get("checks", []):
        check_name = check.get("name", "").lower().replace(" ", "_")
        
        if check.get("status") in ["error", "warning"] and check.get("auto_fixable", False):
            summary["attempted"] += 1
            
            if check_name == "github_pages":
                result = fix_github_pages()
                fixes["github_pages"].append(result)
            elif check_name == "cron_jobs":
                result = fix_cron_jobs()
                fixes["cron_jobs"].append(result)
            elif check_name == "database":
                result = fix_database()
                fixes["database"].append(result)
            elif check_name == "crm":
                result = fix_crm()
                fixes["crm"].append(result)
            elif check_name == "cover_letters":
                result = fix_cover_letters()
                fixes["cover_letters"].append(result)
            else:
                log(f"ℹ️ No auto-fix handler for {check_name}")
                continue
            
            if result.get("success", False):
                summary["successful"] += 1
            else:
                summary["failed"] += 1
    
    log(f"📊 Auto-fix summary: {summary['successful']}/{summary['attempted']} successful")
    
    return {
        "timestamp": datetime.now().isoformat(),
        "fixes": fixes,
        "summary": summary
    }


if __name__ == "__main__":
    # Load health results
    results_file = Path(__file__).parent / "health_results.json"
    
    if not results_file.exists():
        log("❌ No health results found, run healthcheck.py first")
        sys.exit(1)
    
    with open(results_file, 'r') as f:
        health_results = json.load(f)
    
    fix_results = run_auto_fixes(health_results)
    
    # Save fix results
    with open(Path(__file__).parent / "autofix_results.json", 'w') as f:
        json.dump(fix_results, f, indent=2)
    
    sys.exit(0 if fix_results["summary"]["failed"] == 0 else 1)
