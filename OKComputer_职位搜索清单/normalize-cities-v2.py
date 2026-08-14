#!/usr/bin/env python3
"""Normalize city from location field for all jobs missing city_normalized."""
import json
import re
from pathlib import Path

JOBS_FILE = Path(__file__).parent / "jobs-all.json"

# Mapping of location patterns → normalized city
CITY_MAP = {
    # Exact matches (case-insensitive)
    "singapore": "Singapore",
    "hong kong": "Hong Kong",
    "hong kong sar": "Hong Kong",
    "shenzhen": "Shenzhen",
    "shenzhen-南山区": "Shenzhen",
    "shenzhen-福田区": "Shenzhen",
    "shenzhen-宝安区": "Shenzhen",
    "taipei": "Taipei",
    "taipei, taiwan": "Taipei",
    "tokyo": "Tokyo",
    "tokyo, japan": "Tokyo",
    "seoul": "Seoul",
    "seoul, south korea": "Seoul",
    "bangkok": "Bangkok",
    "bangkok, thailand": "Bangkok",
    "bengaluru": "Bangalore",
    "bangalore": "Bangalore",
    "shanghai": "Shanghai",
    "shanghai, china": "Shanghai",
    "上海": "Shanghai",
    "深圳": "Shenzhen",
    "北京": "Beijing",
    "杭州": "Hangzhou",
    "成都": "Chengdu",
    "广州": "Guangzhou",
    "kuala lumpur": "Kuala Lumpur",
    "kuala lumpur, malaysia": "Kuala Lumpur",
    "jakarta": "Jakarta",
    "jakarta, indonesia": "Jakarta",
    "manila": "Manila",
    "manila, philippines": "Manila",
    "ho chi minh": "Ho Chi Minh City",
    "ho chi minh city": "Ho Chi Minh City",
    "hanoi": "Hanoi",
    "sydney": "Sydney",
    "melbourne": "Melbourne",
    "auckland": "Auckland",
    "mumbai": "Mumbai",
    "new delhi": "New Delhi",
    "gurugram": "Gurugram",
    "gurgaon": "Gurugram",
    "gurgaon, india": "Gurugram",
    "hyderabad": "Hyderabad",
    "pune": "Pune",
    "chennai": "Chennai",
    "dubai": "Dubai",
    "abu dhabi": "Abu Dhabi",
    "london": "London",
    "berlin": "Berlin",
    "amsterdam": "Amsterdam",
    "paris": "Paris",
    "new york": "New York",
    "new york, ny": "New York",
    "san francisco": "San Francisco",
    "san francisco, ca": "San Francisco",
    "los angeles": "Los Angeles",
    "los angeles, ca": "Los Angeles",
    "toronto": "Toronto",
    "vancouver": "Vancouver",
    "remote us": "Remote US",
    "remote": "Remote",
    "jakarta, indonesia": "Jakarta",
    "bangalore, india": "Bangalore",
    "hyderabad, india": "Hyderabad",
    "gurugram, india": "Gurugram",
    "mumbai, india": "Mumbai",
    "chennai, india": "Chennai",
    "pune, india": "Pune",
    "new delhi, india": "New Delhi",
    "taipei, taiwan": "Taipei",
    "bangkok, thailand": "Bangkok",
    "ho chi minh city, vietnam": "Ho Chi Minh City",
    "hanoi, vietnam": "Hanoi",
    "manila, philippines": "Manila",
    "kuala lumpur, malaysia": "Kuala Lumpur",
    "jakarta, indonesia": "Jakarta",
    "singapore, singapore": "Singapore",
    "hong kong, hong kong sar": "Hong Kong",
    "seoul, south korea": "Seoul",
    "tokyo, japan": "Tokyo",
    "sydney, australia": "Sydney",
    "melbourne, australia": "Melbourne",
    "auckland, new zealand": "Auckland",
    "dubai, uae": "Dubai",
    "abu dhabi, uae": "Abu Dhabi",
    "london, uk": "London",
    "berlin, germany": "Berlin",
    "amsterdam, netherlands": "Amsterdam",
    "paris, france": "Paris",
    "new york, ny": "New York",
    "san francisco, ca": "San Francisco",
    "los angeles, ca": "Los Angeles",
    "toronto, canada": "Toronto",
    "vancouver, canada": "Vancouver",
    "shanghai, china": "Shanghai",
    "beijing, china": "Beijing",
    "shenzhen, china": "Shenzhen",
    "guangzhou, china": "Guangzhou",
    "hangzhou, china": "Hangzhou",
    "chengdu, china": "Chengdu",
    "chicago": "Chicago",
    "chicago, il": "Chicago",
    "cairo": "Cairo",
    "cairo, egypt": "Cairo",
    "thailand": "Bangkok",
    "united states": "Remote US",
    "usa": "Remote US",
    "us": "Remote US",
    "canada": "Toronto",
    "india": "Bangalore",
    "mexico city": "Mexico City",
    "mexico city, mexico": "Mexico City",
    "washington, dc": "Washington DC",
    "washington dc": "Washington DC",
    "zurich": "Zurich",
    "zürich": "Zurich",
    "zürich, ch": "Zurich",
    "zurich, switzerland": "Zurich",
    "boston": "Boston",
    "boston, ma": "Boston",
    "seattle": "Seattle",
    "seattle, wa": "Seattle",
    "hybrid": "Remote",
    "aichi": "Nagoya",
    "taoyuan": "Taoyuan",
    "taoyuan, taiwan": "Taoyuan",
    "petaling jaya": "Kuala Lumpur",
    "petaling jaya, my": "Kuala Lumpur",
    "bangalore, india": "Bangalore",
    "tokyo, japan": "Tokyo",
    "singapore, singapore": "Singapore",
    "hong kong, hong kong sar": "Hong Kong",
    "seoul, south korea": "Seoul",
    "shanghai, china": "Shanghai",
    "shenzhen, china": "Shenzhen",
}

def normalize_city(location: str) -> str:
    """Extract normalized city from location string."""
    if not location:
        return ""
    
    loc = location.strip()
    
    # Handle multi-location (take first)
    if ";" in loc:
        loc = loc.split(";")[0].strip()
    if "|" in loc:
        loc = loc.split("|")[0].strip()
    if "/" in loc:
        loc = loc.split("/")[0].strip()
    
    # Direct lookup
    key = loc.lower().strip()
    if key in CITY_MAP:
        return CITY_MAP[key]
    
    # Try matching just the city part (before comma)
    city_part = loc.split(",")[0].strip().lower()
    if city_part in CITY_MAP:
        return CITY_MAP[city_part]
    
    # Common patterns: "City, Country" or "City, State"
    # Try to match known city names anywhere in the string
    for pattern, city in sorted(CITY_MAP.items(), key=lambda x: -len(x[0])):
        if pattern in key:
            return city
    
    return ""

def main():
    jobs = json.load(open(JOBS_FILE))
    updated = 0
    already = 0
    skipped = 0
    
    for j in jobs:
        if j.get("city_normalized"):
            already += 1
            continue
        
        city = normalize_city(j.get("location", ""))
        if city:
            j["city_normalized"] = city
            updated += 1
        else:
            skipped += 1
    
    # Save
    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    
    print(f"Updated: {updated}, Already had: {already}, Skipped (no match): {skipped}")
    print(f"Total with city_normalized now: {already + updated}/{len(jobs)}")
    
    # Show some skipped for debugging
    if skipped:
        print("\nSample unmatched locations:")
        count = 0
        for j in jobs:
            if not j.get("city_normalized") and j.get("location"):
                print(f"  → {j['location']}")
                count += 1
                if count >= 10:
                    break

if __name__ == "__main__":
    main()
