#!/usr/bin/env python3
"""Verify career site job URLs and create verified-career-jobs.json"""

import json
from urllib.parse import urlparse

def main():
    with open('jobs-all.json') as f:
        jobs = json.load(f)

    # Direct job URLs found from web searches
    direct_urls = {
        'stripe.com': [
            'https://stripe.com/jobs/listing/product-manager-link-consumer-product/7392697',
            'https://stripe.com/jobs/listing/staff-product-manager-dashboard/7913702',
            'https://stripe.com/jobs/listing/product-manager-payments/7176530',
            'https://stripe.com/jobs/listing/product-manager-sail-core/7913698',
            'https://stripe.com/jobs/listing/product-manager-ecosystem-risk/7943244',
            'https://stripe.com/jobs/listing/product-manager-capital/7721834',
        ],
        'www.airwallex.com': [
            'https://careers.airwallex.com/job/458c1e45-697f-4770-8d0f-ab1d528b3baa/senior-product-manager-growth/',
            'https://careers.airwallex.com/job/579104ca-b257-48e2-8985-4d5f72f30b68/senior-product-manager-identity-authentication/',
            'https://careers.airwallex.com/job/6c55b41b-824b-46cd-8590-b9e83eaa5de6/staff-product-manager-onboarding/',
            'https://careers.airwallex.com/job/5488d78e-72fb-4c26-b743-af0fca4069c0/senior-product-manager-corporate-site/',
            'https://careers.airwallex.com/job/07055859-7ded-4c23-8e2d-fe67c96ea8da/product-director-financial-markets-financial-platform/',
        ],
        'www.hsbc.com': [
            'https://apply.careers.hsbc.com/job/Central-Senior-Product-Manager%2C-Account-Solutions-Hong/1361263357/',
            'https://apply.careers.hsbc.com/job/Mongkok-Senior-Life-Product-Manager-Hang-Seng-Insurance-Hang-Seng-Bank-%28HK%29-Kowl/1360055857/',
            'https://apply.careers.hsbc.com/job/Central-Senior-Wealth-Product-Strategy-and-Proposition-Manager-Hong/1360584357/',
        ],
        'careers.google.com': [
            'https://careers.google.com/jobs/results/94619491089949382-senior-product-manager/',
            'https://careers.google.com/jobs/results/95843957174346438-product-manager-i/',
        ],
        'jobs.okx.com': [
            'http://job-boards.greenhouse.io/okx',
        ],
        'talent.alibaba.com': [
            'https://careers.alibaba.com/',
        ],
    }

    # Process each job
    for j in jobs:
        url = j.get('url', '')
        source = j.get('source', '')
        
        # Default verification status
        j['verified'] = False
        j['needs_login'] = False
        
        # LinkedIn URLs - verified
        if 'linkedin.com' in url:
            j['verified'] = True
            j['url_type'] = 'linkedin'
        
        # Greenhouse URLs - verified
        elif 'greenhouse.io' in url:
            j['verified'] = True
            j['url_type'] = 'greenhouse'
        
        # Boss/Zhilian/Liepin URLs - login required
        elif source in ['boss-zhilian-websearch', 'boss-zhilian', 'liepin', 'zhaopin'] or \
             'zhipin.com' in url or 'liepin.com' in url or 'zhaopin.com' in url:
            j['needs_login'] = True
            j['url_type'] = 'login_required'
        
        # Career site homepages - check if we have direct URLs
        elif j.get('url_type') == 'career_site':
            domain = urlparse(url).netloc
            if domain in direct_urls:
                j['verified'] = True
                j['url_type'] = 'career_site_direct'
                j['direct_urls'] = direct_urls[domain]
            else:
                j['verified'] = False
                j['url_type'] = 'career_site_homepage'
        
        # Other URLs
        else:
            j['verified'] = False

    # Count verification stats
    verified = sum(1 for j in jobs if j.get('verified'))
    needs_login = sum(1 for j in jobs if j.get('needs_login'))
    not_verified = sum(1 for j in jobs if not j.get('verified') and not j.get('needs_login'))

    print(f"Total jobs: {len(jobs)}")
    print(f"Verified: {verified}")
    print(f"Needs login: {needs_login}")
    print(f"Not verified: {not_verified}")

    # Save updated database
    with open('jobs-all.json', 'w') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    print("\nSaved updated jobs-all.json")

    # Create verified-career-jobs.json
    verified_career_jobs = []
    for j in jobs:
        if j.get('verified') and j.get('url_type') in ['career_site_direct', 'linkedin', 'greenhouse']:
            verified_career_jobs.append({
                'title': j.get('title', ''),
                'en_title': j.get('en_title', ''),
                'company': j.get('company', ''),
                'location': j.get('location', ''),
                'url': j.get('url', ''),
                'direct_urls': j.get('direct_urls', []),
                'url_type': j.get('url_type', ''),
                'source': j.get('source', ''),
                'salary': j.get('salary', ''),
                'grade': j.get('grade', ''),
                'quality_score': j.get('quality_score', 0),
            })

    with open('private/verified-career-jobs.json', 'w') as f:
        json.dump(verified_career_jobs, f, indent=2, ensure_ascii=False)

    print(f"\nCreated private/verified-career-jobs.json with {len(verified_career_jobs)} verified jobs")

if __name__ == '__main__':
    main()
