import json
import urllib.request

# Load the new greenhouse jobs
with open('/Users/iancolrick/.openclaw/workspace/new_jobs_greenhouse.json', 'r') as f:
    greenhouse_new = json.load(f)

# Filter to top-tier roles matching profile
# Priority: HK > Shenzhen > Singapore > Shanghai > Guangzhou
# Priority: PM > Strategy > BizOps > Growth > BD
# Skip: engineers, designers, data scientists, lawyers, compliance, HR, accounting
# Skip: Director/VP level titles

priority_locations = ['hong kong', 'shenzhen', 'singapore', 'shanghai', 'guangzhou']
exclude_keywords = [
    'engineer', 'designer', 'data scientist', 'lawyer', 'counsel',
    'compliance', 'hr', 'human resource', 'accounting', 'audit',
    'legal', 'tax', 'risk', 'operations manager', 'talent',
    'communications', 'marketing manager', 'compensation'
]

top_tier = []
for j in greenhouse_new:
    title_lower = j['title'].lower()
    loc_lower = j['location'].lower()
    
    # Skip if title contains excluded keywords
    if any(k in title_lower for k in exclude_keywords):
        continue
    
    # Calculate priority score
    score = 0
    
    # Location score
    for i, loc in enumerate(priority_locations):
        if loc in loc_lower:
            score += (5 - i) * 10
            break
    
    # Role type score
    if 'product manager' in title_lower or 'product director' in title_lower:
        score += 30
    if 'strategy' in title_lower:
        score += 25
    if 'growth' in title_lower:
        score += 20
    if 'business development' in title_lower or 'partnership' in title_lower:
        score += 15
    if 'commercial' in title_lower:
        score += 15
    if 'principal' in title_lower or 'staff' in title_lower:
        score += 10
    if 'senior' in title_lower:
        score += 5
    
    j['priority_score'] = score
    top_tier.append(j)

# Sort by score
top_tier.sort(key=lambda x: x['priority_score'], reverse=True)

# Take top 15
top_15 = top_tier[:15]

print(f"Filtered to {len(top_tier)} relevant jobs, showing top 15:")
for j in top_15:
    print(f"  [{j['priority_score']}] {j['company']} | {j['title']} | {j['location']}")
    print(f"       {j['url']}")

# Save filtered results
with open('/Users/iancolrick/.openclaw/workspace/new_jobs_filtered.json', 'w') as f:
    json.dump(top_15, f, indent=2, ensure_ascii=False)
