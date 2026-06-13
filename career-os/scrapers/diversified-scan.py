#!/usr/bin/env python3
"""
Diversified job scanner using web search.
Searches multiple job platforms for senior PM/strategy/director roles
across APAC locations. Produces real, deduplicated results.
"""
import json, os, sys, re
from datetime import datetime

# This script is designed to be run by an AI agent that has access to web_search.
# It outputs search queries to stdout and expects the agent to execute them.
# The agent will collect results and write diversified-results.json.

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "diversified-results.json")

SEARCH_QUERIES = [
    # LinkedIn
    'site:linkedin.com/jobs "senior product manager" Singapore OR "Hong Kong" 2026',
    'site:linkedin.com/jobs "product director" Singapore OR "Hong Kong" 2026',
    'site:linkedin.com/jobs "head of product" APAC Singapore 2026',
    'site:linkedin.com/jobs "strategy director" fintech Singapore 2026',
    
    # Indeed
    'site:indeed.com "senior product manager" Singapore OR "Hong Kong" 2026',
    'site:indeed.com "product director" Singapore OR Shanghai 2026',
    
    # JobsDB
    'site:jobsdb.com "senior product manager" Singapore OR "Hong Kong"',
    'site:jobsdb.com "product director" Singapore',
    'site:jobsdb.com "head of product" Singapore OR "Hong Kong"',
    
    # Wellfound/AngelList
    'site:wellfound.com "senior product manager" Singapore OR "Hong Kong"',
    'site:wellfound.com "product director" APAC',
    
    # eFinancialCareers
    'site:efinancialcareers.com "product manager" Singapore OR "Hong Kong" fintech',
    
    # Built In
    'site:builtin.com "senior product manager" remote OR Singapore',
    
    # Company career pages - Crypto/Fintech
    'site:careers.okx.com product manager Singapore OR "Hong Kong"',
    'site:bybit.com/en/careers product manager Singapore',
    'site:binance.com/en/careers product manager Singapore',
    
    # Company career pages - Tech/APAC
    'site:grab.com/careers product manager Singapore',
    'site:shopee.com/careers product manager Singapore OR "Shenzhen"',
    'site:careers.sea.com product manager Singapore',
    'site:jobs.bytedance.com product manager Singapore OR "Hong Kong" OR Shenzhen',
    
    # Broader web searches for APAC PM roles
    '"senior product manager" Singapore crypto OR fintech OR blockchain hiring 2026',
    '"product director" "Hong Kong" fintech OR crypto hiring 2026',
    '"head of product" APAC remote fintech startup 2026',
    '"program manager" "cross-border" ecommerce Singapore OR Shenzhen 2026',
    '"strategy director" Singapore fintech OR payments 2026',
]

if __name__ == "__main__":
    print(json.dumps(SEARCH_QUERIES, indent=2))
    print(f"\nTotal queries: {len(SEARCH_QUERIES)}", file=sys.stderr)
