import json
from collections import Counter
from datetime import datetime

with open('/Users/iancolrick/.openclaw/workspace/OKComputer_职位搜索清单/jobs-all.json', 'r') as f:
    data = json.load(f)

# Target cities (case-insensitive substring match)
target_locs = ['hong kong', 'shenzhen', 'guangzhou', 'shanghai', 'singapore', 'tokyo', 'taipei']

# Crypto-related keywords (company + title)
crypto_kw = ['crypto', 'blockchain', 'web3', 'defi', 'nft', 'bitcoin', 'ethereum', 'token', 'staking']
crypto_companies = ['binance', 'okx', 'coins.ph', 'coinbase', 'bybit', 'huobi', 'kucoin', 'bitget', 'gate.io']

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
    
    # Skip pure crypto - check company name
    if any(kw in company for kw in crypto_companies):
        continue
    
    # Skip crypto-related titles
    if any(kw in title for kw in crypto_kw):
        continue
    
    # Skip Binance specifically
    if 'binance' in company:
        continue
    
    filtered.append(j)

print(f'After filtering: {len(filtered)} jobs')

# Categorize into role types based on category and title
def classify(j):
    cat = j.get('category', '').lower()
    title = j.get('title', '').lower()
    
    # Strategy / BizOps / Chief of Staff
    if cat in ['strategy', 'strategy_ops', 'bizops', 'chief_of_staff']:
        return 'strategy_bizops'
    if any(kw in title for kw in ['strategy', 'bizops', 'chief of staff', 'chief operating']):
        return 'strategy_bizops'
    
    # Product Management
    if cat in ['product', 'product_management', 'general_pm', 'senior_pm', 'ai_product', 'product management']:
        return 'product'
    if any(kw in title for kw in ['product manager', 'product lead', 'product owner']):
        return 'product'
    
    # Growth / Expansion / GM
    if cat in ['growth', 'gm', 'general_manager', 'growth_expansion', 'general manager']:
        return 'growth_gm'
    if any(kw in title for kw in ['growth', 'expansion', 'general manager', 'country manager', 'head of']):
        return 'growth_gm'
    
    # Cross-border / Marketplace / Operations
    if cat in ['cross_border', 'marketplace', 'cross-border_platform']:
        return 'cross_border'
    if any(kw in title for kw in ['cross-border', 'marketplace', 'international', 'global']):
        return 'cross_border'
    
    if cat in ['ops', 'operations', 'business operations']:
        return 'cross_border'
    
    return 'other'

for j in filtered:
    j['role_type'] = classify(j)

# Sort by quality score
filtered.sort(key=lambda j: j.get('quality_score', 0), reverse=True)

# Pick top 20 with role diversity
target_per_category = {
    'strategy_bizops': 5,
    'product': 5,
    'growth_gm': 5,
    'cross_border': 5
}
selected = []
cat_counts = Counter()
seen = set()

# First pass: pick from each category to fill quota
for rt in ['strategy_bizops', 'product', 'growth_gm', 'cross_border']:
    for j in filtered:
        if j['role_type'] != rt:
            continue
        key = j.get('url', j.get('title'))
        if key in seen:
            continue
        selected.append(j)
        seen.add(key)
        cat_counts[rt] += 1
        if cat_counts[rt] >= target_per_category[rt]:
            break

# Fill remaining with best from 'other' category
remaining = 20 - len(selected)
if remaining > 0:
    for j in filtered:
        if j['role_type'] == 'other':
            key = j.get('url', j.get('title'))
            if key not in seen:
                selected.append(j)
                seen.add(key)
                if len(selected) >= 20:
                    break

# Sort selected by quality desc
selected.sort(key=lambda j: j.get('quality_score', 0), reverse=True)

print(f'Selected: {len(selected)} jobs')
print(f'Role breakdown: {dict(Counter(j["role_type"] for j in selected))}')

# Format output
emoji_map = {
    'strategy_bizops': '🧭',
    'product': '📦',
    'growth_gm': '🚀',
    'cross_border': '🌏',
    'other': '💼'
}

lines = []
lines.append('🎯 Career OS Daily Job Rec — Top 20')
lines.append(f'📅 {datetime.now().strftime("%Y-%m-%d")}')
lines.append('━' * 30)

for i, j in enumerate(selected, 1):
    emoji = emoji_map.get(j['role_type'], '💼')
    title = j.get('en_title') or j.get('title', 'N/A')
    company = j.get('company', 'N/A')
    location = j.get('location', 'N/A')
    quality = j.get('quality_score', 'N/A')
    url = j.get('url', '')
    
    lines.append(f'\n{i}. {emoji} [{company}]')
    lines.append(f'   {title}')
    lines.append(f'   📍 {location} | Q: {quality}')
    if url:
        lines.append(f'   🔗 {url}')

output = '\n'.join(lines)
print('\n' + output)
