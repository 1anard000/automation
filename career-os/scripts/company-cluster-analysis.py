#!/usr/bin/env python3
"""Analyze jobs database to create company cluster insights for resume tailoring."""

import json
from collections import defaultdict
from pathlib import Path

JOBS_PATH = Path(__file__).parent.parent / "OKComputer_职位搜索清单" / "jobs-all.json"

def load_jobs():
    with open(JOBS_PATH) as f:
        return json.load(f)

def classify_resume_cluster(job):
    """Classify job into resume tailoring clusters based on role characteristics."""
    category = job.get("category", "unclassified")
    title_lower = (job.get("title", "") or job.get("en_title", "")).lower()
    company = job.get("company", "")
    
    clusters = []
    
    # Cluster 1: Cross-border / Marketplace
    cross_border_keywords = ["cross-border", "cross border", "marketplace", "e-commerce", 
                            "ecommerce", "seller", "merchant", "logistics", "supply chain",
                            "lazada", "shopee", "tiktok", "bytedance"]
    if any(kw in title_lower for kw in cross_border_keywords) or category == "cross_border":
        clusters.append("cross_border_marketplace")
    
    # Cluster 2: Strategy / BizOps
    strategy_keywords = ["strategy", "bizops", "chief of staff", "operations", "planning",
                        "strategic", "consulting", "advisory"]
    if any(kw in title_lower for kw in strategy_keywords) or category == "strategy":
        clusters.append("strategy_bizops")
    
    # Cluster 3: Fintech / Payments
    fintech_keywords = ["payment", "fintech", "financial", "banking", "crypto", "blockchain",
                       "defi", "wallet", "trading", "exchange", "custody", "lending",
                       "risk", "compliance", "aml"]
    if any(kw in title_lower for kw in fintech_keywords) or category == "fintech":
        clusters.append("fintech_payments")
    
    # Cluster 4: AI / Product
    ai_keywords = ["ai", "artificial intelligence", "machine learning", "ml", "data",
                  "analytics", "platform", "infrastructure"]
    if any(kw in title_lower for kw in ai_keywords) or category == "ai_product":
        clusters.append("ai_product_platform")
    
    # Cluster 5: Growth / Expansion
    growth_keywords = ["growth", "expansion", "acquisition", "retention", "engagement",
                      "marketing", "user acquisition"]
    if any(kw in title_lower for kw in growth_keywords) or category == "growth":
        clusters.append("growth_expansion")
    
    # If no cluster matched, use category as fallback
    if not clusters:
        if category == "general_pm":
            clusters.append("general_product")
        else:
            clusters.append("general_product")
    
    return clusters

def analyze_visa_risk(job):
    """Assess visa sponsorship likelihood."""
    company = job.get("company", "")
    city = job.get("location_norm", "")
    
    # Companies known for visa sponsorship
    visa_friendly = {
        "Google", "Meta", "Microsoft", "Amazon", "Apple", "Airwallex", 
        "OKX", "ByteDance", "Stripe", "Mastercard", "Visa", "JPMorgan",
        "Goldman Sachs", "Morgan Stanley", "BlackRock", "Wellington Management",
        "BNY", "Manulife", "HSBC", "DBS Bank", "UOB", "Agoda", "SymphonyAI"
    }
    
    # Companies unlikely to sponsor
    visa_unlikely = set()  # Would need more data
    
    if company in visa_friendly:
        return "high_likely"
    elif job.get("sg_visa_likely"):
        return "high_likely"
    elif job.get("low_quality") and "work authorization" in str(job.get("score_breakdown", {}).get("reject_reason", "")):
        return "low_unlikely"
    else:
        return "unknown"

def main():
    jobs = load_jobs()
    
    # Filter to actionable jobs (not Stripe/Instacart dead weight)
    dead_companies = {"Stripe", "Instacart"}
    actionable = [j for j in jobs if j.get("company") not in dead_companies]
    
    # Classify all jobs into clusters
    cluster_map = defaultdict(list)
    company_clusters = defaultdict(lambda: defaultdict(list))
    visa_analysis = defaultdict(list)
    
    for job in actionable:
        clusters = classify_resume_cluster(job)
        visa = analyze_visa_risk(job)
        company = job.get("company", "Unknown")
        city = job.get("location_norm", "Unknown")
        score = job.get("quality_score", 0)
        
        for cluster in clusters:
            cluster_map[cluster].append({
                "company": company,
                "title": job.get("en_title") or job.get("title", ""),
                "city": city,
                "score": score,
                "visa": visa,
                "category": job.get("category", "unclassified")
            })
            company_clusters[company][cluster].append({
                "title": job.get("en_title") or job.get("title", ""),
                "city": city,
                "score": score
            })
        
        visa_analysis[company].append({
            "visa": visa,
            "city": city,
            "score": score
        })
    
    # Generate cluster report
    report = []
    report.append("# Company Cluster Analysis — Resume Tailoring Guide")
    report.append(f"## Generated: June 22, 2026")
    report.append(f"## Jobs Analyzed: {len(actionable)} (excluded {len(jobs) - len(actionable)} dead weight)")
    report.append("")
    
    # Cluster summary
    report.append("## Resume Clusters")
    report.append("")
    report.append("Companies grouped by resume tailoring needs. Apply the same resume version to all jobs in a cluster.")
    report.append("")
    
    cluster_names = {
        "cross_border_marketplace": ("🌐 Cross-border & Marketplace", "Your strongest differentiator. Emphasize Amazon marketplace ops, cross-border logistics, seller dynamics."),
        "fintech_payments": ("💳 Fintech & Payments", "Emphasize payments experience, financial products, cross-border payment flows."),
        "strategy_bizops": ("📊 Strategy & BizOps", "Emphasize Microsoft/Salesforce strategy ops, data-driven decision making, incentive design."),
        "ai_product_platform": ("🤖 AI & Platform", "Emphasize GitHub Copilot launch, AI go-to-market, platform thinking."),
        "growth_expansion": ("📈 Growth & Expansion", "Emphasize growth metrics, user acquisition, market expansion."),
        "general_product": ("📦 General Product", "Standard PM resume. Emphasize product lifecycle, stakeholder management.")
    }
    
    for cluster_key, (cluster_title, cluster_desc) in cluster_names.items():
        jobs_in_cluster = cluster_map.get(cluster_key, [])
        if not jobs_in_cluster:
            continue
        
        # Sort by score descending
        jobs_in_cluster.sort(key=lambda x: x["score"], reverse=True)
        
        report.append(f"### {cluster_title}")
        report.append(f"*{cluster_desc}*")
        report.append(f"**{len(jobs_in_cluster)} roles** | Avg score: {sum(j['score'] for j in jobs_in_cluster) / len(jobs_in_cluster):.0f}")
        report.append("")
        
        # Group by company
        by_company = defaultdict(list)
        for j in jobs_in_cluster:
            by_company[j["company"]].append(j)
        
        report.append("| Company | Roles | Cities | Top Score |")
        report.append("|---------|-------|--------|-----------|")
        for company, company_jobs in sorted(by_company.items(), key=lambda x: max(j["score"] for j in x[1]), reverse=True):
            cities = ", ".join(sorted(set(j["city"] or "Unknown" for j in company_jobs)))
            top_score = max(j["score"] for j in company_jobs)
            report.append(f"| {company} | {len(company_jobs)} | {cities} | {top_score} |")
        report.append("")
    
    # Company-level cluster view
    report.append("## Company-Level View")
    report.append("")
    report.append("Which companies need which resume version:")
    report.append("")
    
    report.append("| Company | Resume Cluster(s) | # Roles | Avg Score | Visa Risk |")
    report.append("|---------|-------------------|---------|-----------|-----------|")
    
    for company in sorted(company_clusters.keys(), 
                          key=lambda c: max(j["score"] for jobs in company_clusters[c].values() for j in jobs),
                          reverse=True):
        clusters = list(company_clusters[company].keys())
        total_roles = sum(len(jobs) for jobs in company_clusters[company].values())
        avg_score = sum(j["score"] for jobs in company_clusters[company].values() for j in jobs) / total_roles
        
        # Visa assessment
        visas = [v["visa"] for v in visa_analysis[company]]
        if "high_likely" in visas:
            visa_str = "✅ High"
        elif "low_unlikely" in visas:
            visa_str = "⚠️ Low"
        else:
            visa_str = "❓ Unknown"
        
        cluster_names_short = [cluster_names.get(c, (c,))[0].split(" ", 1)[1] if c in cluster_names else c for c in clusters]
        report.append(f"| {company} | {', '.join(cluster_names_short)} | {total_roles} | {avg_score:.0f} | {visa_str} |")
    report.append("")
    
    # Batch application recommendations
    report.append("## Batch Application Recommendations")
    report.append("")
    report.append("Apply these groups together for maximum efficiency:")
    report.append("")
    
    # Find the best batches (high-score, same resume version)
    batch_num = 1
    for cluster_key, (cluster_title, _) in cluster_names.items():
        jobs_in_cluster = cluster_map.get(cluster_key, [])
        high_score = [j for j in jobs_in_cluster if j["score"] >= 80]
        if len(high_score) >= 2:
            report.append(f"**Batch {batch_num}: {cluster_title}** ({len(high_score)} roles, score 80+)")
            report.append("Apply same resume version to all:")
            for j in high_score[:5]:  # Top 5
                report.append(f"- {j['company']} — {j['title']} ({j['city']}, score {j['score']})")
            if len(high_score) > 5:
                report.append(f"- ... and {len(high_score) - 5} more")
            report.append("")
            batch_num += 1
    
    # Visa sponsorship summary
    report.append("## Visa Sponsorship Risk Summary")
    report.append("")
    
    visa_counts = {"high_likely": 0, "low_unlikely": 0, "unknown": 0}
    for company, visas in visa_analysis.items():
        for v in visas:
            visa_counts[v["visa"]] += 1
    
    report.append(f"- **High likelihood (visa-friendly company):** {visa_counts['high_likely']} roles")
    report.append(f"- **Low likelihood (work authorization barrier):** {visa_counts['low_unlikely']} roles")
    report.append(f"- **Unknown:** {visa_counts['unknown']} roles")
    report.append("")
    report.append("**Recommendation:** Prioritize the {0} high-likelihood roles for immediate applications.".format(visa_counts['high_likely']))
    report.append("")
    
    # Write output
    output_path = Path(__file__).parent.parent / "strategy" / "company-cluster-analysis.md"
    with open(output_path, "w") as f:
        f.write("\n".join(report))
    
    print(f"✅ Analysis complete: {output_path}")
    print(f"   Jobs analyzed: {len(actionable)}")
    print(f"   Clusters: {len(cluster_map)}")
    print(f"   Companies: {len(company_clusters)}")
    print(f"   Batches: {batch_num - 1}")

if __name__ == "__main__":
    main()
