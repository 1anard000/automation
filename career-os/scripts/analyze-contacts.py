#!/usr/bin/env python3
"""Analyze job data to identify contact mapping priorities."""
import json
import os

jobs_path = os.path.expanduser("~/.openclaw/workspace/career-os/OKComputer_职位搜索清单/jobs-all.json")
contacts_path = os.path.expanduser("~/.openclaw/workspace/career-os/contacts/contacts.json")

with open(jobs_path) as f:
    jobs = json.load(f)

with open(contacts_path) as f:
    contacts = json.load(f)

print(f"Total jobs: {len(jobs)}")
print(f"Total contacts: {len(contacts['contacts'])}")

# Count by company
companies = {}
for job in jobs:
    co = job.get('company', 'Unknown')
    if co not in companies:
        companies[co] = {'count': 0, 'scores': [], 'cities': set(), 'roles': []}
    companies[co]['count'] += 1
    score = job.get('quality_score', 0)
    if score:
        companies[co]['scores'].append(score)
    city = job.get('location_norm', job.get('city', job.get('location', 'Unknown')))
    companies[co]['cities'].add(city)
    companies[co]['roles'].append({
        'title': job.get('title', 'Unknown'),
        'score': score,
        'city': city,
        'url': job.get('url', ''),
        'status': job.get('status', 'unknown'),
        'has_direct_apply': job.get('has_direct_apply', False),
        'app_platform': job.get('app_platform', ''),
        'category': job.get('category', '')
    })

# Sort by count
sorted_cos = sorted(companies.items(), key=lambda x: x[1]['count'], reverse=True)
print("\nTop 20 companies by job count:")
for co, info in sorted_cos[:20]:
    avg = sum(info['scores'])/len(info['scores']) if info['scores'] else 0
    cities = ', '.join(c for c in info['cities'] if c)
    print(f"  {co}: {info['count']} jobs, avg score {avg:.1f}, cities: {cities}")

# Find high-score roles at top companies
print("\n\n=== HIGH-SCORE ROLES (80+) AT TOP COMPANIES ===")
target_cos = ['OKX', 'Airwallex', 'ByteDance', 'Crypto.com', 'Google', 'Binance', 
              'DBS Bank', 'UOB', 'Wellington Management', 'Mastercard', 'BlackRock', 
              'BNY', 'SymphonyAI', 'Visa', 'Shopee', 'Gate', 'HashKey Group']
for co in target_cos:
    if co in companies:
        info = companies[co]
        high_score = [r for r in info['roles'] if r['score'] and r['score'] >= 80]
        if high_score:
            print(f"\n{co} ({info['count']} total roles, {len(high_score)} score-80+):")
            for r in sorted(high_score, key=lambda x: x['score'], reverse=True):
                status = '✅' if r['status'] == 'applied' else '⬜'
                direct = 'DIRECT' if r['has_direct_apply'] else r['app_platform']
                print(f"  {status} [{r['score']}] {r['title']} ({r['city']}) [{direct}]")

# Check which companies have existing contacts
print("\n\n=== CONTACT COVERAGE ===")
contact_companies = set()
for c in contacts['contacts']:
    company = c.get('company', '')
    contact_companies.add(company)
    if company in [co for co in target_cos]:
        print(f"  ✅ {company}: {c['name']} ({c['title']}) — {c.get('relationship_strength', 'unknown')}")

print("\n=== COMPANIES WITHOUT CONTACTS ===")
for co in target_cos:
    if co not in contact_companies and co in companies:
        print(f"  ❌ {co}: NEEDS CONTACT MAPPING")

# Research queue status
print("\n=== RESEARCH QUEUE ===")
for item in contacts.get('research_queue', []):
    print(f"  [{item['priority']}] {item['company']}: {item['notes'][:100]}")

# Summary of contact gaps
print("\n=== SUMMARY ===")
with_contact = [co for co in target_cos if co in contact_companies]
without_contact = [co for co in target_cos if co not in contact_companies and co in companies]
print(f"Companies with contacts: {len(with_contact)} / {len([co for co in target_cos if co in companies])}")
print(f"Companies needing contact mapping: {len(without_contact)}")
for co in without_contact:
    if co in companies:
        print(f"  {co}: {companies[co]['count']} roles, highest score: {max(r['score'] for r in companies[co]['roles'] if r['score']) if companies[co]['scores'] else 'N/A'}")
