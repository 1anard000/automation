#!/usr/bin/env python3
"""Fill missing summaries, en_titles, grades, and quality tiers in jobs-all.json."""
import json
import re
import os

JOBS_FILE = os.path.join(os.path.dirname(__file__), "jobs-all.json")

# Role keywords for auto-grading
SENIOR_KEYWORDS = ["director", "vp", "vice president", "chief", "head of", "general manager", "svp", "evp"]
HIGH_KEYWORDS = ["senior", "staff", "principal", "lead", "group", "architect", "founding"]
MID_KEYWORDS = ["manager", "specialist", "analyst", "consultant", "engineer", "developer", "designer"]
JUNIOR_KEYWORDS = ["junior", "intern", "associate", "assistant", "trainee", "graduate"]

# Chinese to English title mapping
ZH_TITLE_MAP = {
    "高级": "Senior", "资深": "Senior", "总监": "Director", "经理": "Manager",
    "主管": "Lead", "专家": "Specialist", "架构师": "Architect",
    "工程师": "Engineer", "设计师": "Designer", "产品经理": "Product Manager",
    "数据": "Data", "算法": "Algorithm", "后端": "Backend", "前端": "Frontend",
    "移动端": "Mobile", "全栈": "Full Stack", "运维": "DevOps", "测试": "QA",
    "架构": "Architecture", "技术": "Tech", "产品": "Product", "运营": "Operations",
    "市场": "Marketing", "销售": "Sales", "财务": "Finance", "人力": "HR",
    "行政": "Admin", "法务": "Legal", "合规": "Compliance",
}

def auto_grade(title, role_type=""):
    """Assign grade based on title keywords."""
    t = (title or "").lower()
    rt = (role_type or "").lower()
    
    for kw in SENIOR_KEYWORDS:
        if kw in t:
            return "A-1"
    for kw in HIGH_KEYWORDS:
        if kw in t:
            return "A-2"
    if "lead" in rt or "senior" in rt or "principal" in rt:
        return "A-2"
    for kw in MID_KEYWORDS:
        if kw in t:
            return "B"
    for kw in JUNIOR_KEYWORDS:
        if kw in t:
            return "C"
    return "B"  # default

def auto_tier(grade):
    """Map grade to quality tier."""
    tier_map = {"S-1": "A", "A-1": "A", "A": "A", "A-2": "B", "B-1": "B", "B": "B", "B+": "B", "C": "C"}
    return tier_map.get(grade, "B")

def is_chinese(text):
    """Check if text contains Chinese characters."""
    return bool(re.search(r'[\u4e00-\u9fff]', text or ""))

def translate_title(zh_title):
    """Best-effort translate Chinese title to English."""
    if not zh_title or not is_chinese(zh_title):
        return zh_title
    
    result = zh_title
    for zh, en in ZH_TITLE_MAP.items():
        result = result.replace(zh, en + " ")
    
    # Clean up
    result = re.sub(r'\s+', ' ', result).strip()
    
    # If still mostly Chinese, just return original
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', result))
    if chinese_chars > len(result) * 0.3:
        return zh_title  # Translation failed, keep original
    
    return result

def generate_summary(job):
    """Generate a summary from available fields."""
    parts = []
    
    title = job.get("en_title") or job.get("title", "")
    company = job.get("company", "")
    location = job.get("location") or job.get("location_norm", "")
    role_type = job.get("role_type", "")
    category = job.get("category", "")
    source = job.get("source", "")
    
    if title:
        parts.append(f"{title} role")
    if company:
        parts.append(f"at {company}")
    if location:
        parts.append(f"in {location}")
    if role_type:
        parts.append(f"({role_type})")
    if category:
        parts.append(f"— {category} focus")
    
    if not parts:
        return f"Job posting from {source}" if source else "Job posting"
    
    return " ".join(parts)

def main():
    with open(JOBS_FILE) as f:
        jobs = json.load(f)
    
    stats = {"summaries_filled": 0, "en_titles_filled": 0, "en_titles_translated": 0, 
             "grades_filled": 0, "tiers_filled": 0, "companies_filled": 0}
    
    for job in jobs:
        # Fill en_title
        if not job.get("en_title"):
            title = job.get("title", "")
            if is_chinese(title):
                translated = translate_title(title)
                if translated != title:
                    job["en_title"] = translated
                    stats["en_titles_translated"] += 1
                    stats["en_titles_filled"] += 1
                else:
                    job["en_title"] = title  # Keep original if can't translate
                    stats["en_titles_filled"] += 1
            else:
                job["en_title"] = title
                stats["en_titles_filled"] += 1
        
        # Fill summary
        if not job.get("summary"):
            job["summary"] = generate_summary(job)
            stats["summaries_filled"] += 1
        
        # Fill grade
        if not job.get("grade") or job.get("grade") in ("?", "", "Senior"):
            job["grade"] = auto_grade(job.get("title", ""), job.get("role_type", ""))
            stats["grades_filled"] += 1
        
        # Fill quality_tier
        if not job.get("quality_tier") or job.get("quality_tier") in ("?", None):
            job["quality_tier"] = auto_tier(job.get("grade", "B"))
            stats["tiers_filled"] += 1
        
        # Fill company from title if missing
        if not job.get("company") or job.get("company") in ("", "?"):
            title = job.get("title", "")
            # Try to extract company from title patterns like "X - Company" or "Company: X"
            for pattern in [r'[-–—]\s*(.+)', r'@\s*(.+)', r'at\s+(.+)', r'(.+?):']:
                m = re.search(pattern, title)
                if m:
                    candidate = m.group(1).strip()
                    if len(candidate) > 2 and len(candidate) < 50:
                        job["company"] = candidate
                        stats["companies_filled"] += 1
                        break
    
    # Save
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    
    print("Data gap filling complete:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"  Total jobs: {len(jobs)}")

if __name__ == "__main__":
    main()
