import json, os

# Count jobs per source
scrapers_dir = './career-os/scrapers'
files = [f for f in os.listdir(scrapers_dir) if f.endswith('-results.json')]
source_counts = {}
for f in sorted(files):
    path = os.path.join(scrapers_dir, f)
    try:
        with open(path) as fh:
            d = json.load(fh)
        count = len(d) if isinstance(d, list) else 'dict'
        source_counts[f] = count
    except Exception as e:
        source_counts[f] = f'error: {e}'

print("=== Source counts ===")
for f, c in sorted(source_counts.items()):
    print(f"  {f}: {c}")

# Final results
final_path = os.path.join(scrapers_dir, 'final-results.json')
if os.path.exists(final_path):
    with open(final_path) as fh:
        d = json.load(fh)
    print(f"\n=== final-results.json: {len(d)} jobs ===")
    grades = {}
    for j in d:
        g = j.get('quality_tier', '?')
        grades[g] = grades.get(g, 0) + 1
    print(f"  Quality tiers: {grades}")

# jobs-all.json
jobs_all_path = './OKComputer_职位搜索清单/jobs-all.json'
if os.path.exists(jobs_all_path):
    with open(jobs_all_path) as fh:
        d = json.load(fh)
    if isinstance(d, list):
        print(f"\n=== jobs-all.json: {len(d)} jobs ===")
    else:
        print(f"\n=== jobs-all.json: dict ===")

# Grade distribution in greenhouse
gh_path = os.path.join(scrapers_dir, 'greenhouse-results.json')
if os.path.exists(gh_path):
    with open(gh_path) as fh:
        d = json.load(fh)
    print(f"\n=== greenhouse: {len(d)} jobs ===")
    grades = {}
    companies = {}
    for j in d:
        g = j.get('grade', '?')
        grades[g] = grades.get(g, 0) + 1
        c = j.get('company', '?')
        companies[c] = companies.get(c, 0) + 1
    print(f"  Grades: {grades}")
    top5 = sorted(companies.items(), key=lambda x: -x[1])[:5]
    print(f"  Top companies: {top5}")
