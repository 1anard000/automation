#!/usr/bin/env python3
"""
Scheduled Runner for Career OS Infrastructure Bot
Run every 15 minutes via cron
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

INFRA_BOT_DIR = Path(__file__).parent
CAREER_OS = INFRA_BOT_DIR.parent


def log(message: str):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def run_health_check() -> dict:
    """Run health checks"""
    log("🔍 Running health checks...")
    
    try:
        result = subprocess.run(
            [sys.executable, str(INFRA_BOT_DIR / "healthcheck.py")],
            capture_output=True,
            text=True,
            timeout=180,  # 3 minutes max
            cwd=INFRA_BOT_DIR
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # Load results
        results_file = INFRA_BOT_DIR / "health_results.json"
        if results_file.exists():
            with open(results_file, 'r') as f:
                return json.load(f)
        else:
            log("❌ Health check completed but no results file")
            return {"error": "No results"}
            
    except subprocess.TimeoutExpired:
        log("❌ Health check timed out (>3 minutes)")
        return {"error": "Timeout"}
    except Exception as e:
        log(f"❌ Health check failed: {e}")
        return {"error": str(e)}


def run_auto_fix(health_results: dict) -> dict:
    """Run auto-fixes if enabled"""
    log("🔧 Running auto-fixes...")
    
    try:
        result = subprocess.run(
            [sys.executable, str(INFRA_BOT_DIR / "autofix.py")],
            capture_output=True,
            text=True,
            timeout=180,  # 3 minutes max
            cwd=INFRA_BOT_DIR
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # Load results
        results_file = INFRA_BOT_DIR / "autofix_results.json"
        if results_file.exists():
            with open(results_file, 'r') as f:
                return json.load(f)
        else:
            log("ℹ️ Auto-fix completed but no results file")
            return {"summary": {"attempted": 0, "successful": 0, "failed": 0}}
            
    except subprocess.TimeoutExpired:
        log("❌ Auto-fix timed out")
        return {"error": "Timeout"}
    except Exception as e:
        log(f"❌ Auto-fix failed: {e}")
        return {"error": str(e)}


def generate_summary(health_results: dict, fix_results: dict = None) -> str:
    """Generate a concise summary for output"""
    
    summary_lines = []
    
    # Health summary
    if "error" not in health_results:
        summary = health_results.get("summary", {})
        healthy = summary.get("healthy", 0)
        total = summary.get("total", 0)
        warnings = summary.get("warnings", 0)
        errors = summary.get("errors", 0)
        
        if errors == 0 and warnings == 0:
            summary_lines.append(f"✅ All systems healthy ({healthy}/{total})")
        elif errors == 0:
            summary_lines.append(f"⚠️ Found {warnings} issues, all auto-fixable")
        else:
            summary_lines.append(f"❌ Found {errors} errors, {warnings} warnings")
    else:
        summary_lines.append(f"❌ Health check failed: {health_results.get('error')}")
    
    # Fix summary
    if fix_results and "error" not in fix_results:
        fix_summary = fix_results.get("summary", {})
        attempted = fix_summary.get("attempted", 0)
        successful = fix_summary.get("successful", 0)
        failed = fix_summary.get("failed", 0)
        
        if attempted > 0:
            if failed == 0:
                summary_lines.append(f"✅ Auto-fixed {successful}/{attempted} issues")
            else:
                summary_lines.append(f"⚠️ Auto-fixed {successful}/{attempted}, {failed} need manual intervention")
    
    return " | ".join(summary_lines)


def main():
    parser = argparse.ArgumentParser(description="Infrastructure Bot Runner")
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Run auto-fixes after health checks"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate and send report"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only output summary"
    )
    
    args = parser.parse_args()
    
    log("🚀 Infrastructure Bot starting...")
    
    # Run health checks
    health_results = run_health_check()
    
    # Run auto-fixes if enabled
    fix_results = None
    if args.auto_fix:
        fix_results = run_auto_fix(health_results)
    
    # Generate report if enabled
    if args.report:
        log("📝 Generating report...")
        try:
            subprocess.run(
                [sys.executable, str(INFRA_BOT_DIR / "reporter.py")],
                cwd=INFRA_BOT_DIR,
                timeout=60
            )
        except Exception as e:
            log(f"⚠️ Report generation failed: {e}")
    
    # Output summary
    summary = generate_summary(health_results, fix_results)
    log("")
    log("=" * 60)
    log(summary)
    log("=" * 60)
    
    log("✅ Infrastructure Bot run complete")
    
    # Return appropriate exit code
    if "error" in health_results:
        sys.exit(1)
    elif health_results.get("summary", {}).get("errors", 0) > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
