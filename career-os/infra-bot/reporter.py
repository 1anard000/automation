#!/usr/bin/env python3
"""
Reporter for Career OS Infrastructure Bot
Sends summary reports to Ian
"""

import json
import sys
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path(__file__).resolve().parents[3]))
CAREER_OS = WORKSPACE / "career-os"
INFRA_BOT_DIR = CAREER_OS / "infra-bot"


def log(message: str):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def format_duration(iso_timestamp: str) -> str:
    """Format ISO timestamp as human-readable duration"""
    try:
        ts = datetime.fromisoformat(iso_timestamp)
        now = datetime.now()
        delta = now - ts
        
        if delta.total_seconds() < 60:
            return "just now"
        elif delta.total_seconds() < 3600:
            return f"{int(delta.total_seconds() / 60)}m ago"
        elif delta.total_seconds() < 86400:
            return f"{int(delta.total_seconds() / 3600)}h ago"
        else:
            return f"{int(delta.total_seconds() / 86400)}d ago"
    except:
        return "unknown"


def generate_report(health_results: dict = None, fix_results: dict = None) -> str:
    """Generate a human-readable report"""
    
    report_lines = []
    report_lines.append("🤖 **Infrastructure Self-Healing Bot Report**")
    report_lines.append("")
    
    # Health Check Summary
    if health_results:
        timestamp = health_results.get("timestamp", "unknown")
        summary = health_results.get("summary", {})
        
        report_lines.append("## 🔍 Health Check Results")
        report_lines.append(f"*Checked {format_duration(timestamp)}*")
        report_lines.append("")
        
        healthy = summary.get("healthy", 0)
        total = summary.get("total", 0)
        warnings = summary.get("warnings", 0)
        errors = summary.get("errors", 0)
        
        if errors == 0 and warnings == 0:
            report_lines.append("✅ **All systems healthy**")
        elif errors == 0:
            report_lines.append(f"⚠️ **{warnings} warnings**, {healthy}/{total} checks passed")
        else:
            report_lines.append(f"❌ **{errors} errors**, {warnings} warnings, {healthy}/{total} checks passed")
        
        report_lines.append("")
        
        # Detail each check
        for check in health_results.get("checks", []):
            name = check.get("name", "Unknown")
            status = check.get("status", "unknown")
            details = check.get("details", "")
            
            icon = "✅" if status == "healthy" else "⚠️" if status == "warning" else "❌"
            report_lines.append(f"{icon} **{name}**: {details}")
        
        report_lines.append("")
    
    # Auto-Fix Summary
    if fix_results:
        fix_summary = fix_results.get("summary", {})
        attempted = fix_summary.get("attempted", 0)
        successful = fix_summary.get("successful", 0)
        failed = fix_summary.get("failed", 0)
        
        report_lines.append("## 🔧 Auto-Fix Actions")
        
        if attempted == 0:
            report_lines.append("ℹ️ No auto-fixes needed")
        elif failed == 0:
            report_lines.append(f"✅ **{successful}/{attempted} fixes successful**")
        else:
            report_lines.append(f"⚠️ **{successful}/{attempted} fixes successful**, {failed} failed")
        
        report_lines.append("")
        
        # Detail fixes by category
        fixes = fix_results.get("fixes", {})
        for category, fix_list in fixes.items():
            if fix_list:
                category_name = category.replace("_", " ").title()
                report_lines.append(f"### {category_name}")
                for fix in fix_list:
                    action = fix.get("action", "unknown")
                    success = fix.get("success", False)
                    details = fix.get("details", "")
                    
                    icon = "✅" if success else "❌"
                    report_lines.append(f"{icon} {action}: {details}")
                report_lines.append("")
    
    # System Stats
    report_lines.append("## 📊 Current System Stats")
    
    # Database stats
    jobs_db = CAREER_OS / "jobs-all.json"
    if jobs_db.exists():
        try:
            with open(jobs_db, 'r') as f:
                jobs = json.load(f)
            job_count = len(jobs) if isinstance(jobs, list) else 0
            report_lines.append(f"• **Jobs Database**: {job_count} jobs")
        except:
            report_lines.append("• **Jobs Database**: Unable to read")
    else:
        report_lines.append("• **Jobs Database**: Not found")
    
    # CRM stats
    crm_db = CAREER_OS / "crm" / "crm.db"
    if crm_db.exists():
        report_lines.append("• **CRM**: Database exists")
    else:
        report_lines.append("• **CRM**: Not found")
    
    # Cover letters
    cover_letters_dir = CAREER_OS / "cover-letters"
    if cover_letters_dir.exists():
        docx_count = len(list(cover_letters_dir.glob("*.docx")))
        report_lines.append(f"• **Cover Letters**: {docx_count} files")
    else:
        report_lines.append("• **Cover Letters**: Not found")
    
    # Cron jobs
    try:
        import subprocess
        result = subprocess.run(
            ["openclaw", "cron", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            cron_count = len([l for l in result.stdout.strip().split('\n') if l.strip()])
            report_lines.append(f"• **Cron Jobs**: {cron_count} active")
        else:
            report_lines.append("• **Cron Jobs**: Unable to check")
    except:
        report_lines.append("• **Cron Jobs**: Unable to check")
    
    report_lines.append("")
    
    # Recommendations
    report_lines.append("## 💡 Recommendations")
    
    needs_attention = []
    
    if health_results:
        for check in health_results.get("checks", []):
            if check.get("status") == "error" and not check.get("auto_fixable", False):
                needs_attention.append(f"• **{check.get('name')}**: {check.get('details')} (manual intervention needed)")
            elif check.get("status") == "warning" and not check.get("auto_fixable", False):
                needs_attention.append(f"• **{check.get('name')}**: {check.get('details')}")
    
    if fix_results:
        for category, fix_list in fix_results.get("fixes", {}).items():
            for fix in fix_list:
                if not fix.get("success", False):
                    needs_attention.append(f"• **Auto-fix failed**: {fix.get('action')} - {fix.get('details')}")
    
    if needs_attention:
        report_lines.append("### Items Needing Attention:")
        report_lines.extend(needs_attention)
    else:
        report_lines.append("✅ No manual intervention needed")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append(f"*Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    return "\n".join(report_lines)


def send_report(report: str):
    """Send report to Ian (via WeCom or other configured channel)"""
    
    # Save report to file for now
    report_file = INFRA_BOT_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_file.write_text(report)
    log(f"📄 Report saved to {report_file}")
    
    # Also save as latest report
    latest_file = INFRA_BOT_DIR / "latest_report.md"
    latest_file.write_text(report)
    
    # Try to send via WeCom if available
    try:
        import subprocess
        
        # Get WeCom user ID (Ian's)
        # This would need to be configured
        user_id = os.environ.get("WECOM_USER_ID", "")
        
        if user_id:
            # Send via WeCom message tool
            cmd = [
                "openclaw", "mcp", "tool", "wecom_mcp",
                "--name", "send_message",
                "--args", json.dumps({
                    "user_id": user_id,
                    "msg_type": "markdown",
                    "content": {"content": report}
                })
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                log("✅ Report sent via WeCom")
            else:
                log(f"⚠️ WeCom send failed: {result.stderr}")
        else:
            log("ℹ️ WeCom not configured, report saved locally")
            
    except Exception as e:
        log(f"ℹ️ Could not send via WeCom: {e}")
        log("ℹ️ Report saved locally")


def main():
    """Main entry point"""
    log("📝 Generating report...")
    
    # Load results
    health_file = INFRA_BOT_DIR / "health_results.json"
    fix_file = INFRA_BOT_DIR / "autofix_results.json"
    
    health_results = None
    fix_results = None
    
    if health_file.exists():
        with open(health_file, 'r') as f:
            health_results = json.load(f)
    
    if fix_file.exists():
        with open(fix_file, 'r') as f:
            fix_results = json.load(f)
    
    # Generate report
    report = generate_report(health_results, fix_results)
    
    # Print to stdout
    print(report)
    
    # Send/save report
    send_report(report)
    
    log("✅ Report generation complete")


if __name__ == "__main__":
    import os
    main()
