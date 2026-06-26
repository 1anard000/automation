#!/usr/bin/env python3
"""Normalize city names in jobs-all.json into clean groups."""
import json, re

CITY_MAP = {
    # Singapore
    r'singapore': 'Singapore',
    # Hong Kong
    r'hong kong': 'Hong Kong',
    r'central.*district.*hong kong': 'Hong Kong',
    r'kowloon.*hong kong': 'Hong Kong',
    r'wan chai.*hong kong': 'Hong Kong',
    r'hk': 'Hong Kong',
    # Shanghai
    r'shanghai': 'Shanghai',
    # Shenzhen
    r'shenzhen': 'Shenzhen',
    r'深圳': 'Shenzhen',
    # Beijing
    r'beijing': 'Beijing',
    # Bangkok
    r'bangkok': 'Bangkok',
    # Tokyo
    r'tokyo': 'Tokyo',
    # Seoul
    r'seoul': 'Seoul',
    r'south korea': 'Seoul',
    # Kuala Lumpur
    r'kuala lumpur': 'Kuala Lumpur',
    r'kl': 'Kuala Lumpur',
    # Jakarta
    r'jakarta': 'Jakarta',
    # Manila
    r'manila': 'Manila',
    r'taguig': 'Manila',
    # Taipei
    r'taipei': 'Taipei',
    r'taiwan': 'Taipei',
    r'taoyuan': 'Taipei',
    # Sydney
    r'sydney': 'Sydney',
    r'melbourne': 'Sydney',
    r'australia': 'Sydney',
    # Bangalore/Bengaluru
    r'bengaluru': 'Bangalore',
    r'bangalore': 'Bangalore',
    # Mumbai
    r'mumbai': 'Mumbai',
    # New Delhi
    r'new delhi': 'New Delhi',
    r'delhi': 'New Delhi',
    # Osaka
    r'osaka': 'Osaka',
    # Guangzhou
    r'guangzhou': 'Guangzhou',
    r'广州': 'Guangzhou',
    # Hangzhou
    r'hangzhou': 'Hangzhou',
    # Remote groups
    r'remote.*us': 'Remote US',
    r'us.*remote': 'Remote US',
    r'us-remote': 'Remote US',
    r'remote.*canada': 'Remote CA',
    r'remote.*uk': 'Remote UK',
    r'remote.*india': 'Remote IN',
    r'remote.*asia': 'Remote APAC',
    r'remote.*emea': 'Remote EMEA',
    r'remote$': 'Remote',
    r'remote-?friendly': 'Remote',
    # Abu Dhabi
    r'abu dhabi': 'Abu Dhabi',
    # Ho Chi Minh
    r'ho chi minh': 'HCMC',
    # Denver
    r'denver': 'Denver',
    r'chicago': 'Chicago',
    r'san francisco': 'SF',
    r'\bsf\b': 'SF',
    r'seattle': 'Seattle',
    r'new york': 'NYC',
    r'\bnyc\b': 'NYC',
    r'toronto': 'Toronto',
    r'portland': 'Portland',
    r'austin': 'Austin',
    r'atlanta': 'Atlanta',
    r'boston': 'Boston',
}

def normalize_city(loc):
    if not loc:
        return 'Unknown'
    loc_lower = loc.lower().strip()
    
    # Check for multi-city with specific APAC cities first
    apac_keywords = ['singapore', 'hong kong', 'shanghai', 'shenzhen', 'bangkok', 'tokyo', 
                     'seoul', 'kuala lumpur', 'jakarta', 'manila', 'taipei', 'taiwan',
                     'sydney', 'melbourne', 'australia', 'bengaluru', 'bangalore', 'mumbai',
                     'new delhi', 'osaka', 'guangzhou', 'hangzhou', 'beijing', 'abu dhabi',
                     'ho chi minh', 'hcmc']
    
    # If contains APAC city names, pick the primary one
    for kw in apac_keywords:
        if re.search(kw, loc_lower):
            for pattern, city in CITY_MAP.items():
                if re.search(pattern, loc_lower):
                    return city
    
    # Remote patterns
    if 'remote' in loc_lower:
        for pattern, city in CITY_MAP.items():
            if 'remote' in pattern and re.search(pattern, loc_lower):
                return city
        return 'Remote'
    
    # Fallback: try all patterns
    for pattern, city in CITY_MAP.items():
        if re.search(pattern, loc_lower):
            return city
    
    return loc.strip()

# Process
jobs = json.load(open('jobs-all.json'))
changed = 0
city_counts = {}
for j in jobs:
    old = j.get('location', '')
    new = normalize_city(old)
    j['city_normalized'] = new
    city_counts[new] = city_counts.get(new, 0) + 1
    if old != new:
        changed += 1

with open('jobs-all.json', 'w') as f:
    json.dump(jobs, f, ensure_ascii=False, indent=2)

print(f'Updated {len(jobs)} jobs, {changed} locations normalized')
print(f'\nTop 20 normalized cities:')
for city, count in sorted(city_counts.items(), key=lambda x: -x[1])[:20]:
    print(f'  {city}: {count}')
