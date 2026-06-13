#!/usr/bin/env python3
"""
Job Page Generator — Creates individual HTML pages from job data
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Paths
WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path(__file__).resolve().parent)) / "OKComputer_职位搜索清单"
TEMPLATE_FILE = WORKSPACE / "templates" / "job-page-template.html"
JOBS_FILE = WORKSPACE / "liepin-jobs.json"
OUTPUT_DIR = WORKSPACE / "jobs"

def load_template():
    """Load the HTML template"""
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        return f.read()

def load_jobs():
    """Load jobs from JSON file"""
    with open(JOBS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_job_page(template, job):
    """Generate an individual job HTML page"""
    # Extract job ID from URL
    job_id = job['url'].split('/')[-1].split('.shtml')[0] or f"job-{hash(job['url'])}"

    # Replace placeholders
    page = template.replace('{{title}}', job['title'])
    page = page.replace('{{company}}', job['company'])
    page = page.replace('{{location}}', job['location'])
    page = page.replace('{{salary}}', job['salary'])
    page = page.replace('{{experience}}', job['experience'])
    page = page.replace('{{education}}', job['education'])
    page = page.replace('{{grade}}', job['grade'])
    page = page.replace('{{notes}}', job.get('notes', ''))
    page = page.replace('{{url}}', job['url'])
    page = page.replace('{{dateAdded}}', datetime.now().strftime('%Y-%m-%d'))
    page = page.replace('{{lastUpdated}}', datetime.now().strftime('%Y-%m-%d'))

    return job_id, page

def save_job_page(job_id, page):
    """Save job page to file"""
    output_file = OUTPUT_DIR / f"{job_id}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(page)
    print(f"✓ Created: {output_file}")

def main():
    """Main execution"""
    print("📝 Job Page Generator")
    print("=" * 50)

    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Load template
    template = load_template()
    print(f"✓ Loaded template: {TEMPLATE_FILE}")

    # Load jobs
    jobs = load_jobs()
    print(f"✓ Loaded {len(jobs)} jobs from: {JOBS_FILE}")

    # Generate pages
    for job in jobs:
        job_id, page = generate_job_page(template, job)
        save_job_page(job_id, page)

    print("=" * 50)
    print(f"✓ Generated {len(jobs)} job pages in: {OUTPUT_DIR}")

if __name__ == '__main__':
    main()