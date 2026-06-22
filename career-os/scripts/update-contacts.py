#!/usr/bin/env python3
"""Update contacts.json with cleaned research queue and new companies."""
import json
import os

contacts_path = os.path.expanduser("~/.openclaw/workspace/career-os/contacts/contacts.json")

with open(contacts_path) as f:
    contacts = json.load(f)

# Update research queue to reflect current state
contacts["research_queue"] = [
    {
        "company": "Wellington Management",
        "priority": 1,
        "roles_to_find": ["Director Product Strategy APAC"],
        "cities": ["Singapore"],
        "linkedin_search": "https://www.linkedin.com/search/results/people/?keywords=product%20director%20Wellington%20Management%20Singapore&geoUrn=%5B%22102222073%22%5D",
        "notes": "Score-100 Director role. Investment management + strategy. Direct apply available. HIGHEST PRIORITY - find contact."
    },
    {
        "company": "Mastercard",
        "priority": 2,
        "roles_to_find": ["Director AI & Data Strategy"],
        "cities": ["Singapore"],
        "linkedin_search": "https://www.linkedin.com/search/results/people/?keywords=director%20strategy%20Mastercard%20Singapore&geoUrn=%5B%22102222073%22%5D",
        "notes": "Score-100 Director role. Fintech + AI intersection. Direct apply available. HIGH PRIORITY."
    },
    {
        "company": "BlackRock",
        "priority": 3,
        "roles_to_find": ["Aladdin Product Solutions Director"],
        "cities": ["Singapore"],
        "linkedin_search": "https://www.linkedin.com/search/results/people/?keywords=product%20director%20BlackRock%20Aladdin&geoUrn=%5B%22102222073%22%5D",
        "notes": "Score-100 Director role. Asset management platform. Direct apply available. HIGH PRIORITY."
    },
    {
        "company": "BNY",
        "priority": 4,
        "roles_to_find": ["Director Commercial PM Custody Platform"],
        "cities": ["Singapore"],
        "linkedin_search": "https://www.linkedin.com/search/results/people/?keywords=product%20director%20BNY%20custody&geoUrn=%5B%22102222073%22%5D",
        "notes": "Score-100 Director role. Custody + digital assets. Direct apply available. HIGH PRIORITY."
    },
    {
        "company": "DBS Bank",
        "priority": 5,
        "roles_to_find": ["VP DBS Digital Exchange", "Head of Digital Products"],
        "cities": ["Singapore"],
        "linkedin_search": "https://www.linkedin.com/search/results/people/?keywords=product%20director%20DBS%20digital%20exchange&geoUrn=%5B%22102222073%22%5D",
        "notes": "Score-82 role. Largest SG bank. Digital exchange focus. Need contact."
    },
    {
        "company": "UOB",
        "priority": 6,
        "roles_to_find": ["VP Digital Currency & Payments"],
        "cities": ["Singapore"],
        "linkedin_search": "https://www.linkedin.com/search/results/people/?keywords=product%20director%20UOB%20digital&geoUrn=%5B%22102222073%22%5D",
        "notes": "Score-82 role. Banking + crypto intersection. Need contact."
    },
    {
        "company": "OKX",
        "priority": 7,
        "roles_to_find": ["Director of Product, Web3 Wallet", "Director of Product, Local Market & Growth"],
        "cities": ["Hong Kong"],
        "linkedin_search": "https://www.linkedin.com/search/results/people/?keywords=product%20director%20OKX%20wallet&geoUrn=%5B%22102222072%22%5D",
        "notes": "4 high-score roles. Web3 Wallet PM (89) and Local Market PM (87) in HK. ASK DAVID LIU FOR INTROS. Replace placeholder contacts with real people."
    },
    {
        "company": "Airwallex",
        "priority": 8,
        "roles_to_find": ["Director Product Strategy Payments"],
        "cities": ["Singapore"],
        "linkedin_search": "https://www.linkedin.com/search/results/people/?keywords=product%20director%20airwallex&geoUrn=%5B%22102222073%22%5D",
        "notes": "3 score-100 Director roles in SG. Emily Watson (existing contact) is Head of Product in Beijing. ASK FOR SG INTROS."
    },
    {
        "company": "ByteDance",
        "priority": 9,
        "roles_to_find": ["Growth Strategy PM Global Payment", "Card Growth PM Global Payment"],
        "cities": ["Singapore"],
        "linkedin_search": "https://www.linkedin.com/search/results/people/?keywords=product%20director%20bytedance%20global%20payment&geoUrn=%5B%22102222073%22%5D",
        "notes": "2 cross-border payment PM roles in SG (score 85 each). David Liu can intro. HIGH PRIORITY."
    },
    {
        "company": "Crypto.com",
        "priority": 10,
        "roles_to_find": ["Lead PM Exchange Institutional", "Head of AI Products"],
        "cities": ["Singapore"],
        "linkedin_search": "https://www.linkedin.com/search/results/people/?keywords=product%20director%20crypto.com&geoUrn=%5B%22102222073%22%5D",
        "notes": "3 high-score roles. Lead PM Exchange Institutional (82, SG), Senior PM AI Transformation (80, SG). Replace placeholder contacts."
    },
    {
        "company": "Google",
        "priority": 11,
        "roles_to_find": ["Regional Product Lead Foundational Measurement"],
        "cities": ["Singapore"],
        "linkedin_search": "https://www.linkedin.com/search/results/people/?keywords=bizops%20director%20google&geoUrn=%5B%22102222073%22%5D",
        "notes": "Score-80 role. Amanda Foster (existing contact) can ask for APAC intros."
    },
    {
        "company": "Binance",
        "priority": 12,
        "roles_to_find": ["AI Chatbot PM", "Director PM Earn Products"],
        "cities": ["Hong Kong", "Singapore"],
        "linkedin_search": "https://www.linkedin.com/search/results/people/?keywords=product%20director%20binance&geoUrn=%5B%22102222072%22%5D",
        "notes": "AI Chatbot PM in HK (score 77) + Earn Structured Product in SG (score 70). Replace placeholder contact."
    },
    {
        "company": "SymphonyAI",
        "priority": 13,
        "roles_to_find": ["SME & Product Lead APAC"],
        "cities": ["Singapore"],
        "linkedin_search": "https://www.linkedin.com/search/results/people/?keywords=product%20lead%20symphonyai&geoUrn=%5B%22102222073%22%5D",
        "notes": "Score-81 role. AI product leadership. Not direct apply — need referral."
    },
    {
        "company": "Visa",
        "priority": 14,
        "roles_to_find": ["AVP Chief of Staff & Head of Strategy", "Director Client Consulting"],
        "cities": ["Singapore", "Hong Kong"],
        "linkedin_search": "https://www.linkedin.com/search/results/people/?keywords=strategy%20director%20visa%20apac&geoUrn=%5B%22102222073%22%2C%22102222072%22%5D",
        "notes": "2 roles. AVP Chief of Staff (79) + Director Client Consulting Stablecoin/AI (78). Fintech strategy."
    }
]

# Update notes
contacts["notes"] = "Contacts managed by Career OS. Key APAC contacts: David Liu (ByteDance, URGENT reconnection needed), Emily Watson (Airwallex, needs SG intros), Amanda Foster (Google, warm). 5 placeholder contacts need replacing with real people. 8 companies have NO contacts — Wellington, Mastercard, BlackRock, BNY have score-100 Director roles. See contact-mapping-plan.md for detailed research plan."

# Update contact count targets
contacts["contact_targets"] = {
    "wellington_management": {"current": 0, "target": 2, "roles": ["Director Product Strategy APAC"]},
    "mastercard": {"current": 0, "target": 2, "roles": ["Director AI & Data Strategy"]},
    "blackrock": {"current": 0, "target": 2, "roles": ["Aladdin Product Solutions Director"]},
    "bny": {"current": 0, "target": 2, "roles": ["Director Commercial PM Custody"]},
    "dbs_bank": {"current": 0, "target": 1, "roles": ["VP DBS Digital Exchange"]},
    "uob": {"current": 0, "target": 1, "roles": ["VP Digital Currency"]},
    "symphonyai": {"current": 0, "target": 1, "roles": ["SME & Product Lead APAC"]},
    "visa": {"current": 0, "target": 1, "roles": ["AVP Chief of Staff"]},
    "okx": {"current": 0, "target": 3, "roles": ["Director Product Web3 Wallet", "Director Product Growth", "Director Institutional"]},
    "crypto.com": {"current": 0, "target": 2, "roles": ["Director Institutional", "Head of AI Products"]},
    "binance": {"current": 0, "target": 2, "roles": ["Director Earn Products", "Head of AI Products"]}
}

with open(contacts_path, 'w') as f:
    json.dump(contacts, f, indent=2, ensure_ascii=False)

print("Updated contacts.json:")
print(f"  - Research queue: {len(contacts['research_queue'])} companies")
print(f"  - Contact targets: {len(contacts['contact_targets'])} companies")
print(f"  - Notes updated with current status")
