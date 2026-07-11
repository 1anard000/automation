#!/usr/bin/env python3
"""Scrape Ashby career pages for APAC product/strategy roles."""
import json
import os
import urllib.request
import sys
from datetime import datetime, timedelta

# Ashby companies to check
ASHBY_COMPANIES = [
    "notion", "whatnot", "higgsfield", "ramp", "brex",
    "deel", "remote", "oyster", "velocity-global",
    "retool", "vercel", "netlify", "cloudflare",
    "figma", "linear", "posthog", "plausible",
    "supabase", "hasura", "nhost",
    "luma", "cal.com", "calendly",
    "mixture", "arc", "serpapi",
    "perplexity", "openai", "anthropic",
    "mistral", "cohere", "stability",
]

APAC_KEYWORDS = [
    "singapore", "hong kong", "shenzhen", "guangzhou", "shanghai",
    "tokyo", "seoul", "bangkok", "jakarta", "kuala lumpur",
    "australia", "sydney", "melbourne", "apac", "asia",
    "china", "remote", "hybrid", "worldwide", "global",
]

SENIOR_KEYWORDS = [
    "director", "vp", "vice president", "head of", "senior",
    "lead", "principal", "chief", "general manager", "gm",
    "总监", "总经理", "资深", "专家",
]

PRODUCT_KEYWORDS = [
    "product manager", "product lead", "product director",
    "product strategy", "strategy", "operations", "biz ops",
    "program manager", "programme manager", "business development",
    "partnerships", "expansion", "market entry", "growth",
    "cross-border", "international", "gtm", "go-to-market",
    "fintech", "platform", "api", "developer relations",
    "ai product", "ai strategy", "ai ops",
]


def fetch_ashby(company):
    """Try to fetch Ashby job board for a company."""
    # Try common Ashby URL patterns
    urls = [
        f"https://jobs.ashbyhq.com/{company}",
        f"https://jobs.ashbyhq.com/{company}?nonexistent_roles=true",
    ]
    
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8")
                # Look for job data in HTML (Ashby embeds JSON in script tags)
                import re
                # Find JSON data in script tags
                patterns = [
                    r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                    r'window\.__remixContext\s*=\s*({.*?});',
                ]
                for pattern in patterns:
                    match = re.search(pattern, html, re.DOTALL)
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            return data
                        except:
                            pass
                return {"html": html[:5000]}  # Return raw HTML for parsing
        except Exception as e:
            continue
    return None


def main():
    results = []
    checked = 0
    
    for company in ASHBY_COMPANIES:
        checked += 1
        data = fetch_ashby(company)
        if not data:
            continue
        
        print(f"  {company}: fetched data")
        
        # Try to extract jobs from the response
        if isinstance(data, dict) and "html" in data:
            # Parse HTML for job listings
            html = data["html"]
            # Look for job titles and locations in HTML
            import re
            # Simple extraction - look for common patterns
            title_patterns = [
                r'<h2[^>]*>(.*?)</h2>',
                r'<h3[^>]*>(.*?)</h3>',
                r'class="job-title"[^>]*>(.*?)<',
                r'class="posting-headline"[^>]*>(.*?)<',
            ]
            for pattern in title_patterns:
                matches = re.findall(pattern, html)
                for title in matches:
                    title = re.sub(r'<[^>]+>', '', title).strip()
                    if title and len(title) > 5:
                        # Check if it matches our criteria
                        title_lower = title.lower()
                        if any(kw in title_lower for kw in SENIOR_KEYWORDS):
                            if any(kw in title_lower for kw in PRODUCT_KEYWORDS):
                                results.append({
                                    "title": title,
                                    "company": company.title(),
                                    "location": "APAC (check listing)",
                                    "salary": "",
                                    "url": f"https://jobs.ashbyhq.com/{company}",
                                    "source": "ashby",
                                    "role_type": "unknown",
                                    "description": f"Senior role at {company.title()}. Check Ashby listing for details.",
                                    "grade": "",
                                })
    
    print(f"\nChecked {checked} Ashby companies, found {len(results)} matching jobs")
    
    # Save
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan-ashby.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(results)} jobs to scan-ashby.json")


if __name__ == "__main__":
    main()
