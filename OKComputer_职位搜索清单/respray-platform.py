#!/usr/bin/env python3
"""Backfill missing platform data from source aliases and deduplicate title+company blocks.

- platform is derived from `source` (case-insensitive).
- multi-source values are normalized to a single `platform`.
- duplicate (title, company) pairs are kept once, preferring records with url.
- If `platform` already exists, the script does not overwrite it.

Usage: python3 respray-platform.py
"""

import json
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).parent
DATA = BASE / 'jobs-all.json'


def normalize_platform(source: str) -> str:
    s = (source or '').strip().lower()
    if not s:
        return 'Unknown'
    mapping = {
        'linkedin': 'LinkedIn',
        'linkedin_search': 'LinkedIn Search',
        'greenhouse': 'Greenhouse',
        'company_site': 'Company Career Site',
        'company site': 'Company Career Site',
        'careers': 'Company Career Site',
        'boss-zhilian': 'Boss Zhipin',
        'boss zhipin': 'Boss Zhipin',
        'boss-zhilian-websearch': 'Boss Zhipin Websearch',
        'zhaopin': 'Zhaopin',
        'jobsdb': 'JobsDB',
        'indeed': 'Indeed',
        'web_search': 'Web Search',
        'web search': 'Web Search',
        'glassdoor': 'Glassdoor',
        'seek': 'SEEK',
        'wellfound': 'Wellfound',
        'angellist': 'Wellfound',
        'builtin': 'Built In',
        'built in': 'Built In',
    }
    return mapping.get(s, s.title())


def respray(jobs):
    updated = 0
    for job in jobs:
        if not job.get('platform'):
            job['platform'] = normalize_platform(job.get('source', ''))
            updated += 1
    # If source missing too, set Unknown if still blank
    for job in jobs:
        if not job.get('platform'):
            job['platform'] = 'Unknown'
    return updated


def dedupe(jobs):
    best = {}
    order = []
    for idx, job in enumerate(jobs):
        title = (job.get('title') or '').strip().lower()
        company = (job.get('company') or '').strip().lower()
        key = (title, company)
        if not title or not company:
            order.append((idx, job))
            continue
        prev = best.get(key)
        if prev is None:
            best[key] = (idx, job)
        else:
            # keep whichever has URL, otherwise first seen
            old_idx, old_job = prev
            if job.get('url') and not old_job.get('url'):
                best[key] = (idx, job)
            # else keep old
    # preserve relative ordering as much as possible
    keep_idxs = {idx for idx, _ in best.values()}
    keep_indices = sorted(
        list(keep_idxs) + [idx for idx, _ in order],
        key=lambda i: i,
    )
    return [jobs[i] for i in keep_indices]


def main():
    if not DATA.exists():
        raise SystemExit(f'Missing {DATA}')

    with DATA.open('r', encoding='utf-8') as f:
        jobs = json.load(f)

    before = len(jobs)
    updated = respray(jobs)
    jobs = dedupe(jobs)
    after = len(jobs)

    with DATA.open('w', encoding='utf-8') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)

    print(f'Backfilled platform on {updated} jobs.')
    print(f'Duplicates removed: {before - after}.')
    print(f'Final count: {after} jobs.')


if __name__ == '__main__':
    main()
