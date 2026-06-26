import json
from collections import Counter

with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json', 'r') as f:
    data = json.load(f)

print(f'Total jobs: {len(data)}')

# Category distribution
cats = Counter(j.get('category', 'unknown') for j in data)
print(f'Categories: {dict(cats)}')

# Target cities
target_locs = ['hong kong', 'shenzhen', 'guangzhou', 'shanghai', 'singapore', 'tokyo', 'taipei']
for loc in target_locs:
    count = sum(1 for j in data if loc in j.get('location', '').lower())
    print(f'  {loc}: {count}')
print()

# Quality >= 70, target cities, no pure crypto
crypto_kw = ['crypto', 'blockchain', 'web3', 'defi', 'nft', 'bitcoin', 'ethereum', 'token', 'staking']
filtered = []
for j in data:
    q = j.get('quality_score', 0)
    loc = j.get('location', '').lower()
    title = j.get('title', '').lower()
    company = j.get('company', '').lower()
    
    if q < 70:
        continue
    
    if not any(t in loc for t in target_locs):
        continue
    
    # Skip pure crypto
    if any(kw in title or kw in company for kw in crypto_kw):
        continue
    
    filtered.append(j)

print(f'After filtering (q>=70, target cities, no crypto): {len(filtered)}')

# Category breakdown after filter
cats2 = Counter(j.get('category', 'unknown') for j in filtered)
print(f'Filtered categories: {dict(cats2)}')

# Location breakdown after filter
locs2 = Counter(j.get('location', 'unknown') for j in filtered)
print(f'Filtered locations: {dict(locs2)}')

# Now sort: quality_score desc, then by fit_score if present, then freshness
# Categorize into role types
role_map = {
    'strategy': 'strategy_bizops',
    'bizops': 'strategy_bizops',
    'chief_of_staff': 'strategy_bizops',
    'product': 'product',
    'pm': 'product',
    'growth': 'growth_gm',
    'general_manager': 'growth_gm',
    'gm': 'growth_gm',
    'expansion': 'growth_gm',
    'cross_border': 'cross_border',
    'marketplace': 'cross_border',
    'ops': 'cross_border',
    'operations': 'cross_border',
}

def classify(j):
    cat = j.get('category', '').lower()
    title = j.get('title', '').lower()
    
    # Check category first
    if cat in role_map:
        return role_map[cat]
    
    # Check title keywords
    if any(kw in title for kw in ['strategy', 'bizops', 'chief of staff', 'coo', 'chief operating']):
        return 'strategy_bizops'
    if any(kw in title for kw in ['product manager', 'product lead', 'product owner', 'pm ']):
        return 'product'
    if any(kw in title for kw in ['growth', 'expansion', 'general manager', 'gm ']):
        return 'growth_gm'
    if any(kw in title for kw in ['cross-border', 'marketplace', 'operations']):
        return 'cross_border'
    
    return 'other'

# Classify all filtered jobs
for j in filtered:
    j['role_type'] = classify(j)

role_counts = Counter(j['role_type'] for j in filtered)
print(f'\nRole type distribution: {dict(role_counts)}')

# Sort by quality score desc
filtered.sort(key=lambda j: (j.get('quality_score', 0), j.get('fit_score', 0)), reverse=True)

# Pick top 20 with diversity: at least 3-4 from each category if available
target_per_category = {'strategy_bizops': 5, 'product': 5, 'growth_gm': 5, 'cross_border': 5}
selected = []
cat_counts = Counter()

# First pass: pick top from each category
for j in filtered:
    rt = j['role_type']
    if rt == 'other':
        continue
    if cat_counts[rt] < target_per_category.get(rt, 5):
        selected.append(j)
        cat_counts[rt] += 1
        if len(selected) >= 20:
            break

# Fill remaining slots from remaining jobs
if len(selected) < 20:
    seen_ids = {j.get('url', j.get('title')) for j in selected}
    for j in filtered:
        if j.get('url', j.get('title')) not in seen_ids:
            selected.append(j)
            seen_ids.add(j.get('url', j.get('title')))
            if len(selected) >= 20:
                break

print(f'\nSelected {len(selected)} jobs:')
print(f'Role type breakdown: {dict(Counter(j["role_type"] for j in selected))}')

# Format output
output_lines = []
output_lines.append('🎯 Career OS Daily Job Rec — Top 20')
output_lines.append(f'📅 {__import__("datetime").datetime.now().strftime("%Y-%m-%d")}')
output_lines.append('━' * 30)

emoji_map = {
    'strategy_bizops': '🧭',
    'product': '📦',
    'growth_gm': '🚀',
    'cross_border': '🌏',
    'other': '💼'
}

for i, j in enumerate(selected, 1):
    emoji = emoji_map.get(j['role_type'], '💼')
    title = j.get('en_title') or j.get('title', 'N/A')
    company = j.get('company', 'N/A')
    location = j.get('location', 'N/A')
    quality = j.get('quality_score', 'N/A')
    fit = j.get('fit_score', 'N/A')
    url = j.get('url', '')
    
    output_lines.append(f'\n{i}. {emoji} [{company}]')
    output_lines.append(f'   {title}')
    output_lines.append(f'   📍 {location} | Q: {quality}')
    if url:
        output_lines.append(f'   🔗 {url}')

output = '\n'.join(output_lines)
print('\n' + '=' * 50)
print('WECHAT OUTPUT:')
print('=' * 50)
print(output)
