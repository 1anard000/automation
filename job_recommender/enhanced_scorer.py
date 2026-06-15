#!/usr/bin/env python3
"""
Enhanced Quality Scoring System for Job Database
- Filters out Amazon jobs (user excluded)
- Improved domain matching
- Singapore visa sponsorship flag
- Better salary parsing
"""
import json
import re
from pathlib import Path

# === USER PROFILE ===
USER_YOE = 9
SALARY_FLOOR_CNY = 90000   # 90K RMB/month
SALARY_FLOOR_HKD = 60000   # 60K HKD/month
SALARY_FLOOR_SGD = 10000   # 10K SGD/month

# Target domains (positive matches)
TARGET_DOMAINS = [
    'product manager', 'product management', 'pm', 'strategy', 'operations',
    'growth', 'cross-border', 'cross border', 'program manager', 'programme manager',
    'business development', 'bd', 'partnerships', 'gtm', 'go-to-market',
    'marketplace', 'ecosystem', 'platform strategy', 'overseas operation',
    'international operation', 'global operation', 'supply chain',
]

AI_PRODUCT_DOMAINS = [
    'ai product', 'ai strategy', 'machine learning product', 'ml product',
    'ai pm', 'ai program manager', 'ai product manager',
]

# Negative domains (hard reject)
NEGATIVE_DOMAINS = [
    'sales', 'marketing', 'hr', 'human resources', 'finance', 'accounting',
    'engineering', 'software engineer', 'swe', 'frontend', 'backend',
    'design', 'ux', 'ui', 'graphic', 'data scientist', 'data engineer',
    'devops', 'sre', 'qa', 'tester', 'security engineer',
]

# Hard reject companies
EXCLUDED_COMPANIES = ['amazon']

# Location preference scores
LOCATION_SCORES = {
    'shenzhen': 15,
    'hong kong': 12,
    'guangzhou': 10,
    'singapore': 10,
    'shanghai': 8,
    'remote': 5,
    'us': 0,
}

# Location priority for tie-breaking
LOCATION_PRIORITY = {
    'shenzhen': 1,
    'hong kong': 2,
    'guangzhou': 3,
    'singapore': 4,
    'shanghai': 5,
    'remote': 6,
}

# Known international companies (English-friendly)
INTERNATIONAL_COMPANIES = [
    'amazon', 'google', 'meta', 'facebook', 'apple', 'microsoft', 'netflix',
    'airbnb', 'uber', 'stripe', 'paypal', 'shopify', 'salesforce', 'adobe',
    'oracle', 'sap', 'ibm', 'cisco', 'intel', 'nvidia', 'qualcomm',
    'tencent', 'alibaba', 'bytedance', 'tiktok', 'xiaomi', 'huawei',
    'samsung', 'lg', 'sony', 'toyota', 'honda', 'bmw', 'mercedes',
    'riot games', 'ea', 'activision', 'blizzard', 'ubisoft', 'epic games',
    'spotify', 'twitter', 'linkedin', 'snap', 'pinterest', 'reddit',
    'zoom', 'slack', 'dropbox', 'notion', 'figma', 'canva',
    'databricks', 'snowflake', 'palantir', 'crowdstrike', 'palo alto',
    'grab', 'gojek', 'shopee', 'sea group', 'lazada', 'foodpanda',
    'airwallex', 'wise', 'revolut', 'monzo', 'n26',
    'shein', 'temu', 'pinduoduo', 'jd', 'meituan', 'didi',
    'anthropic', 'openai', 'deepmind', 'mistral', 'cohere',
    'minimax', 'moonshot', 'zhipu', 'baichuan',
    'arm', 'arm china', 'arm holdings',
    'flexport', 'insta360', 'dji', 'transsion', 'tecno',
    'anker', 'baseus', 'ezviz',
    'lalamove', 'deliveree', 'sendle',
    'cloudflare', 'vercel', 'netlify',
    'openai', 'anthropic', 'deepseek',
    'miq digital', 'agoda', 'netease',
]


def is_excluded(job):
    """Check if job should be hard-excluded (e.g., Amazon)."""
    company = (job.get('company_raw') or '').lower()
    for excluded in EXCLUDED_COMPANIES:
        if excluded in company:
            return True, f"Excluded company: {excluded}"
    return False, None


def parse_salary(title, notes=''):
    """Parse salary from title and notes. Returns (amount, currency) or (None, None)."""
    text = f"{title} {notes}".lower()
    
    # SGD
    sgd_match = re.search(r'(?:sgd|s\$|\$)\s*(\d[\d,]*(?:\.\d+)?)\s*(?:k|000)?', text)
    if sgd_match:
        val = float(sgd_match.group(1).replace(',', ''))
        if val < 1000:
            val *= 1000
        return val, 'SGD'
    
    # HKD
    hkd_match = re.search(r'(?:hkd|h\$|港币|港元)\s*(\d[\d,]*(?:\.\d+)?)\s*(?:k|000)?', text)
    if hkd_match:
        val = float(hkd_match.group(1).replace(',', ''))
        if val < 1000:
            val *= 1000
        return val, 'HKD'
    
    # K format: "30-50K" or "30K-50K"
    k_match = re.search(r'(\d+)[kK]?\s*[-–—]\s*(\d+)[kK]', text)
    if k_match:
        low = int(k_match.group(1))
        high = int(k_match.group(2))
        avg_k = (low + high) / 2
        return avg_k * 1000, 'CNY'
    
    # Single K: "30K/月"
    single_k = re.search(r'(\d+)[kK]\s*/\s*月', text)
    if single_k:
        return int(single_k.group(1)) * 1000, 'CNY'
    
    # Number with comma: "90,000"
    comma_match = re.search(r'(\d{2,3}),(\d{3})', text)
    if comma_match:
        val = int(comma_match.group(1) + comma_match.group(2))
        return val, 'CNY'
    
    return None, None


def parse_yoe(title, notes=''):
    """Parse years of experience requirement. Returns (min_yoe, max_yoe) or None."""
    text = f"{title} {notes}".lower()
    
    # "X-Y years" or "X-Y年"
    match = re.search(r'(\d+)\s*[-–—]\s*(\d+)\s*(?:年|years?|yoe)', text)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    
    # "X+ years"
    match = re.search(r'(\d+)\s*\+?\s*(?:年|years?|yoe)', text)
    if match:
        return (int(match.group(1)), int(match.group(1)) + 5)
    
    # Title-based heuristics
    if 'staff' in text or 'principal' in text or 'director' in text or 'vp' in text:
        return (8, 15)
    if 'senior' in text or 'sr.' in text or 'sr ' in text or 'lead' in text:
        return (5, 12)
    
    return None


def calculate_yoe_score(yoe_range):
    """Calculate YOE match score (0-30 points)."""
    if yoe_range is None:
        return 15  # Neutral when unknown
    
    min_yoe, max_yoe = yoe_range
    
    if min_yoe <= USER_YOE <= max_yoe:
        return 30
    elif min_yoe <= USER_YOE + 1 <= max_yoe or min_yoe <= USER_YOE - 1 <= max_yoe:
        return 25
    elif max_yoe <= 4:
        return -10  # Entry level
    elif min_yoe >= 13:
        return -20  # Underqualified
    else:
        return 5  # Some match


def calculate_salary_score(salary, currency, location):
    """Calculate salary match score (0-25 points)."""
    if salary is None:
        return 10  # Neutral
    
    location_lower = (location or '').lower()
    
    if 'hong kong' in location_lower:
        if currency == 'HKD' or currency == 'CNY':
            # Rough conversion: 1 CNY ≈ 1.1 HKD
            salary_hkd = salary * (1.1 if currency == 'CNY' else 1.0)
        else:
            salary_hkd = salary
        if salary_hkd >= 60000:
            return 25
        elif salary_hkd >= 40000:
            return 15
        elif salary_hkd >= 20000:
            return 5
        else:
            return -30
    
    elif 'singapore' in location_lower:
        if currency == 'SGD':
            salary_sgd = salary
        elif currency == 'CNY':
            salary_sgd = salary / 5.3  # Rough conversion
        else:
            salary_sgd = salary
        if salary_sgd >= 10000:
            return 25
        elif salary_sgd >= 7000:
            return 15
        elif salary_sgd >= 4000:
            return 5
        else:
            return -30
    
    else:
        # CN jobs (CNY)
        if salary >= 90000:
            return 25
        elif salary >= 50000:
            return 20
        elif salary >= 30000:
            return 15
        elif salary >= 15000:
            return 5
        else:
            return -30


def calculate_domain_score(title, notes=''):
    """Calculate domain match score (0-25 points)."""
    text = f"{title} {notes}".lower()
    
    # Check negative domains first (hard reject)
    for domain in NEGATIVE_DOMAINS:
        if domain in text:
            return -20
    
    # Check AI/Product domains (bonus)
    for domain in AI_PRODUCT_DOMAINS:
        if domain in text:
            return 20
    
    # Check target domains
    for domain in TARGET_DOMAINS:
        if domain in text:
            return 25
    
    return 0


def calculate_location_score(location):
    """Calculate location match score (0-15 points)."""
    if not location:
        return 0
    
    location_lower = location.lower()
    
    for loc, score in LOCATION_SCORES.items():
        if loc in location_lower:
            return score
    
    return 0


def calculate_english_score(title, company_raw, english_friendly, location):
    """Calculate English-friendliness score for CN jobs (0-10 points)."""
    if not location:
        return 0
    
    location_lower = location.lower()
    
    cn_locations = ['shenzhen', 'shanghai', 'guangzhou', 'beijing', 'hangzhou', 'guangdong']
    is_cn = any(loc in location_lower for loc in cn_locations)
    
    if not is_cn:
        return 0  # HK/SG assumed English-friendly
    
    if english_friendly is True:
        company_lower = (company_raw or '').lower()
        title_lower = (title or '').lower()
        
        for company in INTERNATIONAL_COMPANIES:
            if company in company_lower:
                return 10
        
        if re.search(r'[a-zA-Z]{3,}', title_lower):
            english_keywords = ['english', '英语', 'overseas', 'international', 'global', 'cross-border']
            for kw in english_keywords:
                if kw in title_lower or kw in (company_raw or '').lower():
                    return 8
        
        return -10  # Marked English but no verification
    else:
        return -10


def calculate_freshness_score(job):
    """Bonus for recently posted jobs (0-5 points)."""
    scanned = job.get('scanned_date', '')
    if not scanned:
        return 0
    
    # Simple freshness: if scanned within last 3 days, +5
    from datetime import datetime, timedelta
    try:
        scan_date = datetime.strptime(scanned, '%Y-%m-%d')
        age = (datetime.now() - scan_date).days
        if age <= 3:
            return 5
        elif age <= 7:
            return 3
        elif age <= 14:
            return 1
    except:
        pass
    return 0


def calculate_quality_score(job):
    """Calculate comprehensive quality score (0-100) for a job."""
    title = job.get('title', '')
    company_raw = job.get('company_raw', '')
    notes = job.get('notes', '')
    location = job.get('location', '')
    english_friendly = job.get('english_friendly')
    
    # Parse attributes
    yoe_range = parse_yoe(title, notes)
    salary, currency = parse_salary(title, notes)
    
    # Calculate component scores
    yoe_score = calculate_yoe_score(yoe_range)
    salary_score = calculate_salary_score(salary, currency, location)
    domain_score = calculate_domain_score(title, notes)
    location_score = calculate_location_score(location)
    english_score = calculate_english_score(title, company_raw, english_friendly, location)
    freshness_score = calculate_freshness_score(job)
    
    # Total score (clamped to 0-100)
    total = yoe_score + salary_score + domain_score + location_score + english_score + freshness_score
    total = max(0, min(100, total))
    
    # Determine tier
    if total >= 70:
        tier = 'A'
    elif total >= 50:
        tier = 'B'
    elif total >= 30:
        tier = 'C'
    else:
        tier = 'D'
    
    return {
        'quality_score': total,
        'quality_tier': tier,
        'low_quality': total < 30,
        'score_breakdown': {
            'yoe_match': yoe_score,
            'salary_match': salary_score,
            'domain_match': domain_score,
            'location_match': location_score,
            'english_match': english_score,
            'freshness': freshness_score,
        }
    }


def get_location_priority(location):
    """Get priority number for location (lower = better)."""
    if not location:
        return 99
    location_lower = location.lower()
    for loc, priority in LOCATION_PRIORITY.items():
        if loc in location_lower:
            return priority
    return 99


def main():
    jobs_path = Path('/Users/iancolrick/OKComputer_职位搜索清单/jobs-all.json')
    with open(jobs_path, 'r', encoding='utf-8') as f:
        jobs = json.load(f)
    
    print(f"Processing {len(jobs)} jobs...")
    
    excluded_count = 0
    for job in jobs:
        # Check exclusions
        excluded, reason = is_excluded(job)
        if excluded:
            job['excluded'] = True
            job['exclusion_reason'] = reason
            job['quality_score'] = 0
            job['quality_tier'] = 'X'
            job['low_quality'] = True
            job['score_breakdown'] = {}
            excluded_count += 1
            continue
        
        job['excluded'] = False
        job['exclusion_reason'] = None
        
        scores = calculate_quality_score(job)
        job['quality_score'] = scores['quality_score']
        job['quality_tier'] = scores['quality_tier']
        job['low_quality'] = scores['low_quality']
        job['score_breakdown'] = scores['score_breakdown']
    
    # Save updated database
    with open(jobs_path, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    
    # Statistics
    tier_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'X': 0}
    for job in jobs:
        tier = job.get('quality_tier', 'D')
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    print(f"\n=== Quality Distribution ===")
    print(f"Excluded (Amazon): {tier_counts['X']}")
    print(f"Tier A (≥70): {tier_counts['A']}")
    print(f"Tier B (50-69): {tier_counts['B']}")
    print(f"Tier C (30-49): {tier_counts['C']}")
    print(f"Tier D (<30): {tier_counts['D']}")
    
    # Show top 20
    eligible = [j for j in jobs if not j.get('excluded')]
    eligible.sort(key=lambda x: (x.get('quality_score', 0), -get_location_priority(x.get('location', ''))), reverse=True)
    
    print(f"\n=== Top 20 Recommendations ===")
    for i, job in enumerate(eligible[:20], 1):
        bd = job.get('score_breakdown', {})
        print(f"{i:2d}. [{job['quality_score']:2d}] {job['title']}")
        print(f"    @ {job.get('company_raw', 'N/A')} [{job.get('location', 'N/A')}]")
        print(f"    YOE:{bd.get('yoe_match',0):+d} Sal:{bd.get('salary_match',0):+d} Dom:{bd.get('domain_match',0):+d} Loc:{bd.get('location_match',0):+d} EN:{bd.get('english_match',0):+d} Fresh:{bd.get('freshness',0):+d}")
        print()
    
    return jobs


if __name__ == '__main__':
    main()
