#!/usr/bin/env python3
"""Parse Liepin search results from saved HTML."""
import json, re, hashlib
from datetime import datetime
from html.parser import HTMLParser

class LiepinParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.jobs = []
        self.current = {}
        self.in_title = False
        self.in_company = False
        self.in_salary = False
        self.in_location = False
        self.capture = ''
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get('class', '')
        
        if tag == 'a' and 'job-title' in cls:
            self.in_title = True
            self.capture = ''
            href = attrs_dict.get('href', '')
            if href and not href.startswith('http'):
                href = 'https://www.liepin.com' + href
            self.current['url'] = href
        elif 'company-name' in cls or 'company' in cls:
            self.in_company = True
            self.capture = ''
        elif 'job-salary' in cls or 'salary' in cls:
            self.in_salary = True
            self.capture = ''
        elif 'job-area' in cls or 'area' in cls or 'job-dq' in cls:
            self.in_location = True
            self.capture = ''
    
    def handle_data(self, data):
        if self.in_title:
            self.capture += data.strip()
        elif self.in_company:
            self.capture += data.strip()
        elif self.in_salary:
            self.capture += data.strip()
        elif self.in_location:
            self.capture += data.strip()
    
    def handle_endtag(self, tag):
        if self.in_title and tag == 'a':
            self.current['title'] = self.capture
            self.in_title = False
            self.capture = ''
        elif self.in_company:
            self.current['company'] = self.capture
            self.in_company = False
            self.capture = ''
        elif self.in_salary:
            self.current['salary'] = self.capture
            self.in_salary = False
            self.capture = ''
        elif self.in_location:
            self.current['location'] = self.capture
            self.in_location = False
            self.capture = ''
            if 'title' in self.current and 'url' in self.current:
                self.jobs.append(self.current.copy())
                self.current = {}

# Also try regex-based extraction
with open('/tmp/liepin.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Regex approach - look for job listing patterns
jobs = []
# Find job titles and links
title_pattern = re.compile(r'<a[^>]*class="[^"]*job-title[^"]*"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', re.DOTALL)
company_pattern = re.compile(r'<span[^>]*class="[^"]*company-name[^"]*"[^>]*>(.*?)</span>', re.DOTALL)
salary_pattern = re.compile(r'<span[^>]*class="[^"]*job-salary[^"]*"[^>]*>(.*?)</span>', re.DOTALL)
area_pattern = re.compile(r'<span[^>]*class="[^"]*job-area[^"]*"[^>]*>(.*?)</span>', re.DOTALL)

# Try a simpler approach - look for structured data
job_blocks = re.findall(r'job-title.*?(?=job-title|$)', html, re.DOTALL)
print(f'Found {len(job_blocks)} potential job blocks')

# Extract any JSON-LD or structured data
json_ld = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL)
print(f'Found {len(json_ld)} JSON-LD blocks')

# Look for any data attributes or script tags with job data
job_data = re.findall(r'"title"\s*:\s*"([^"]+)"', html)
company_data = re.findall(r'"companyName"\s*:\s*"([^"]+)"', html)
url_data = re.findall(r'"url"\s*:\s*"(https?://[^"]+liepin[^"]+)"', html)

print(f'Extracted: {len(job_data)} titles, {len(company_data)} companies, {len(url_data)} URLs')
for i, title in enumerate(job_data[:20]):
    company = company_data[i] if i < len(company_data) else 'unknown'
    url = url_data[i] if i < len(url_data) else ''
    print(f'  {i+1}. {title} | {company} | {url}')
