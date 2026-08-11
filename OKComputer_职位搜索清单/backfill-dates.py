#!/usr/bin/env python3
"""Backfill missing posted_date fields in jobs-all.json.

Strategy:
1. Jobs with existing dates are kept as-is
2. Jobs with a 'created_at' or 'fetched_at' field use those
3. Remaining jobs get estimated dates based on their position
   (assuming jobs were appended in rough chronological order)
4. Jobs with no temporal info at all get a conservative estimate
   based on the midpoint of the date range
"""
import json
import sys
from datetime import datetime, timedelta

DATA_FILE = 'jobs-all.json'

def parse_date(s):
    if not s:
        return None
    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S+08:00', '%Y-%m-%dT%H:%M:%SZ'):
        try:
            return datetime.strptime(s.replace('+08:00','').replace('Z',''), fmt)
        except ValueError:
            continue
    return None

def main():
    with open(DATA_FILE) as f:
        jobs = json.load(f)

    filled = 0
    estimated = 0
    already_had = 0
    dates = []

    # First pass: collect all known dates
    for j in jobs:
        d = parse_date(j.get('posted') or j.get('posted_date') or j.get('date') or j.get('created_at') or j.get('fetched_at') or j.get('scanned_date'))
        if d:
            dates.append(d)

    if not dates:
        print("No reference dates found, using today as midpoint")
        mid = datetime.now()
    else:
        dates.sort()
        mid = dates[len(dates)//2]
        print(f"Date range: {dates[0].date()} to {dates[-1].date()}, midpoint: {mid.date()}")

    now = datetime.now()

    # Second pass: backfill
    for i, j in enumerate(jobs):
        existing = j.get('posted') or j.get('posted_date') or j.get('date')
        if existing and parse_date(existing):
            already_had += 1
            continue

        # Try other fields
        for field in ('created_at', 'fetched_at', 'scraped_at', 'scanned_date'):
            alt = j.get(field)
            if alt and parse_date(alt):
                j['posted'] = alt
                filled += 1
                break
        else:
            # Estimate based on position
            # Assume jobs are roughly in order, spread across date range
            if dates:
                earliest = dates[0]
                latest = dates[-1]
                span = (latest - earliest).total_seconds()
                if len(jobs) > 1:
                    fraction = i / (len(jobs) - 1)
                    estimated_date = earliest + timedelta(seconds=span * fraction)
                else:
                    estimated_date = mid
                j['posted'] = estimated_date.strftime('%Y-%m-%d')
                j['date_source'] = 'estimated'
                estimated += 1
            else:
                j['posted'] = mid.strftime('%Y-%m-%d')
                j['date_source'] = 'estimated'
                estimated += 1

    with open(DATA_FILE, 'w') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    print(f"Results: {already_had} already had dates, {filled} filled from metadata, {estimated} estimated")
    print(f"Total jobs now with dates: {len(jobs)}")

if __name__ == '__main__':
    main()
