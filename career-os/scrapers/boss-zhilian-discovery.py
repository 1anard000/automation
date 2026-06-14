#!/usr/bin/env python3
"""
Boss直聘 / Zhilian targeted discovery via web_search.

This script is designed to be run through Hermes Agent's web_search tool.
It processes pre-fetched web_search results into structured job listings.

Usage:
  1. Run web_search queries via Hermes Agent
  2. Paste results into WEB_SEARCH_RESULTS below
  3. Run this script to generate boss-zhilian-discovery-results.json

Heuristics for [CANDIDATE]:
- Prefer roles HK/SZ/GZ/SH/Hangzhou.
- Seniority: 资深, 专家, 总监, 负责人, 经理, lead, director, head, VP.
- English-work-friendly signal keywords.
- Exclude staffing/猎头 listings when possible.
"""
import json, os, re, sys
from datetime import datetime

# Pre-fetched web_search results (populated by Hermes Agent)
WEB_SEARCH_RESULTS = [
    # Query: site:zhipin.com "资深产品经理" "香港"
    {"url": "https://www.zhipin.com/job_detail/2c0770d02bba234a03N-3tu-ElVT.html", "title": "资深产品经理（美股交易方向）招聘 - 某小型计算机软件公司", "description": "北京某小型计算机软件公司资深产品经理（美股交易方向）招聘，地点：香港，要求：5-10年，学历：本科"},
    {"url": "https://www.zhipin.com/job_detail/51735f12a5fd32cd03By2dW4GVBV.html", "title": "资深产品经理招聘 - 腾讯", "description": "腾讯资深产品经理招聘，地点：北京"},
    {"url": "https://www.zhipin.com/job_detail/3678a63f2b1254fa03180tu1EltY.html", "title": "资深产品经理（机器人本体方向）", "description": "深圳5-10年本科，B端产品"},
    {"url": "https://m.zhipin.com/job_detail/b835dbf034c54ba603Zz3dm-FFRS.html", "title": "资深产品经理（信贷中台）- 货拉拉科技", "description": "深圳5-10年本科，中后台"},
    {"url": "https://www.zhipin.com/job_detail/1723a1a58888099b1Hdy0tu-GFFT.html", "title": "资深产品经理 - 诺禾致源", "description": "香港、美国、英国、新加坡、荷兰和日本设有子公司"},

    # Query: site:zhipin.com "产品总监" "深圳"
    {"url": "https://www.zhipin.com/zhaopin/9cdede60377cba100Xd_0tm1/", "title": "海外产品总监招聘 - BOSS直聘", "description": "海外DSP产品总监【深圳/北京】100-200K·16薪"},
    {"url": "https://www.zhipin.com/zhaopin/97ac91ee3c0cabd91H1639y8/", "title": "腾讯产品总监招聘 - BOSS直聘", "description": "腾讯产品总监，深圳，腾讯云联络中心"},
    {"url": "https://www.zhipin.com/zhaopin/9ace3613dde98d7f03Jz39-4Fg~~/", "title": "深圳供应链产品总监招聘 - BOSS直聘", "description": "资深产品总监（电商/供应链方向）11-22K，深圳龙华区民治"},
    {"url": "https://www.zhipin.com/zhaopin/61b62bedfdbfd9e03nx739k~/", "title": "产品总监/资深产品经理 - 迅雷网络", "description": "30-55K·15薪，深圳南山区科技园，5-10年本科"},
    {"url": "https://www.zhipin.com/zhaopin/38bfbdfb2e4d63170Xxy29S0/", "title": "产品总监（穿戴类）- 广和通", "description": "35-60K·14薪，深圳南山区西丽，5-10年本科"},
    {"url": "https://www.zhipin.com/zhaopin/ceaec9afaebf12ca0nB909W5/", "title": "产品总监 - 创新工场", "description": "储能产品总监，35-40K·14薪，深圳宝安区西乡"},

    # Query: site:zhipin.com "产品负责人" "广州"
    {"url": "https://www.zhipin.com/zhaopin/d7e21dd9ddf7606603x_0tu_/", "title": "产品负责人(AI项目) - 广州小迈", "description": "30-50K·13薪，广州天河区体育中心，5-10年本科"},
    {"url": "https://m.zhipin.com/job_detail/a2a2bc22b83f0e5c03F62dq8E1tW.html", "title": "AI产品负责人（AI社交/AI游戏方向）- 易娱网络", "description": "广州，3-5年本科"},
    {"url": "https://m.zhipin.com/job_detail/8cc9d3d746a677dc03B709y7FFtQ.html", "title": "海外工具类产品负责人（IAP) 2C - 幂动科技", "description": "广州，3-5年本科"},
    {"url": "https://www.zhipin.com/job_detail/a5a91720fbc6b54b0nZ93dS1EVpX.html", "title": "海外产品负责人（语音/直播）- 百度", "description": "广州，5-10年本科"},

    # Query: site:zhipin.com "高级产品经理" "上海"
    {"url": "https://www.zhipin.com/zhaopin/7499fb0dd9e529a60nV52tu8Fw~~/", "title": "上海高级产品经理招聘 - BOSS直聘", "description": "上海-高级产品经理（多方向）30-60K·15薪，SHEIN"},
    {"url": "https://www.zhipin.com/zhaopin/4ae12d13d49c60510nZ73N21GQ~~/", "title": "上海小程序高级产品经理招聘 - BOSS直聘", "description": "小程序高级产品经理25-50K·15薪，亚朵集团"},
    {"url": "https://www.zhipin.com/zhaopin/77e91979ca5c865f1HJ63ti9/", "title": "大数据平台高级产品经理招聘 - BOSS直聘", "description": "上海-高级产品经理（B端开放平台）30-50K·15薪，SHEIN"},
    {"url": "https://www.zhipin.com/zhaopin/17a009436a99293b03Ny29i1FA~~/", "title": "上海企业端产品经理招聘 - BOSS直聘", "description": "高级产品经理（外汇方向）上海/深圳 45-75K·15薪"},

    # Query: site:zhipin.com "产品负责人" "杭州"
    {"url": "https://m.zhipin.com/job_detail/73329495a53feefb03x80tu8GVdU.html", "title": "1688-策略产品负责人-杭州 - 阿里巴巴集团", "description": "杭州5-10年本科，策略产品"},
    {"url": "https://www.zhipin.com/zhaopin/3aa07c4a1938e7ac3n1z09q6/", "title": "产品负责人（客户体验）- 杭州促聚科技", "description": "30-60K，杭州西湖区西溪，5-10年本科"},
    {"url": "https://www.zhipin.com/job_detail/c4ea7ca308587a2b1Hx-29-8EFRR.html", "title": "产品负责人（支付、sdk）- 杭州某大型游戏及IP生态平台", "description": "杭州"},

    # Query: site:zhipin.com "产品经理" "AI" "上海"
    {"url": "https://www.zhipin.com/zhaopin/2c781dbe237d76690ndz2925FA~~/", "title": "上海AI数据产品经理招聘 - BOSS直聘", "description": "【中台】AI数据产品经理 30-50K·16薪，沐瞳科技"},
    {"url": "https://m.zhipin.com/zhaopin/99f1939718b0e60e03160921GA~~/", "title": "上海AI平台产品经理招聘 - BOSS直聘", "description": "资深AI平台产品经理 40-50K·15薪，XTransfer"},
    {"url": "https://www.zhipin.com/zhaopin/904d936bb2f094f90XB62d26/", "title": "AI产品经理招聘 - BOSS直聘", "description": "AI产品经理，深圳福田区，12-24K，1-3年本科"},
    {"url": "https://www.zhipin.com/zhaopin/17a009436a99293b03Ny29i1FA~~/", "title": "AI产品经理-上海 - 万得基金", "description": "22-40K，上海浦东新区陆家嘴，3-5年本科"},

    # Query: site:zhipin.com "产品经理" "大模型" "深圳"
    {"url": "https://m.zhipin.com/job_detail/77fa354260bbecb903Jy3Ny6FldR.html", "title": "AI产品经理（大模型/视觉/NLP/转运）- 顺丰科技", "description": "深圳，3-5年本科"},
    {"url": "https://m.zhipin.com/job_detail/4dae8a602c8900880nV72ty6FVJT.html", "title": "元宝-大模型评测产品经理(北京/深圳) - 腾讯", "description": "深圳，3-5年本科"},
    {"url": "https://www.zhipin.com/job_detail/28ea4da8913c694003x_09y4EFtV.html", "title": "AI/大模型产品经理 - 百度", "description": "深圳，硕士"},
    {"url": "https://www.zhipin.com/job_detail/2d69bcddcaae9d7c03B92dm0FVNT.html", "title": "医疗大模型/医疗智能体产品经理 - 有米科技", "description": "深圳，3-5年本科"},
    {"url": "https://m.zhipin.com/job_detail/5c7c0c0c6193d4540nRz2d-7EVJX.html", "title": "大模型策略产品经理 - 腾讯", "description": "深圳，3-5年本科"},

    # Query: site:zhipin.com "增长产品经理" "香港"
    {"url": "https://m.zhipin.com/job_detail/9009a4275b1db6770nV82t28EFZT.html", "title": "QQ浏览器-高级增长产品经理(深圳) - 腾讯", "description": "深圳5-10年本科"},
    {"url": "https://www.zhipin.com/job_detail/d9689946ec363c1a0nZ929u0E1FY.html", "title": "AI增长产品经理（线索挖掘方向）", "description": "北京1-3年本科，ADTiger虎视（HK 01163）香港上市"},
    {"url": "https://www.zhipin.com/zhaopin/ac986ed29788fa031nx92966GQ~~/", "title": "新加坡产品经理招聘 - BOSS直聘", "description": "付费增长产品经理-国际化直播-新加坡 40-50K·15薪，字节跳动"},
    {"url": "https://www.zhipin.com/zhaopin/3813b7f8769a51bf1XF42NU~/", "title": "WEB产品经理招聘 - BOSS直聘", "description": "高级用户增长产品经理（Web方向）-TikTok 40-70K·15薪，字节跳动"},

    # Query: site:zhipin.com "商业策略" "香港"
    {"url": "https://m.zhipin.com/zhaopin/885477597706d67f0HV83du7/", "title": "国际业务拓展与商业策略经理/总监 - 深圳市途龄科技", "description": "15-30K，香港，3-5年硕士，Libpet途龄"},

    # Query: site:zhipin.com "GTM" "深圳"
    {"url": "https://www.zhipin.com/zhaopin/34a953986480921303V43t2-FA~~/", "title": "深圳GTM经理招聘 - BOSS直聘", "description": "GTM经理/总监 14-28K·14薪，御界科技"},
    {"url": "https://m.zhipin.com/zhaopin/92f29b3a4aabed7c1HJy0tm6Fg~~/", "title": "深圳GTM助理招聘 - BOSS直聘", "description": "产品经理/GTM（base苏州/深圳/北京）25-50K·15薪，追觅科技"},
    {"url": "https://www.zhipin.com/zhaopin/2ab2d9e3137e45ff1nN42dW4GA~~/", "title": "GTM产品经理招聘 - BOSS直聘", "description": "15-16K，优之科技(深圳)，深圳龙岗区，3-5年硕士"},

    # Query: site:zhipin.com "商业化产品经理" "上海"
    {"url": "https://www.zhipin.com/zhaopin/9e2304017b44c2df0HFz2g~~/", "title": "商业化产品经理招聘 - BOSS直聘", "description": "25-45K·13薪，趣头条，上海浦东新区三林，3-5年本科"},
    {"url": "https://www.zhipin.com/zhaopin/557be08402ce4e4c0nV939u-FA~~/", "title": "商业化产品经理（通用）- 小红书", "description": "30-50K，上海黄浦区淮海路，3-5年本科"},
    {"url": "https://www.zhipin.com/zhaopin/128c0bca69f82d570nRy09m9Eg~~/", "title": "商业化产品经理 - 麦糖", "description": "20-25K·13薪，上海浦东新区张江，3-5年本科"},

    # Query: site:zhaopin.com "产品总监" "深圳"
    {"url": "https://m.zhaopin.com/jobs/CC137934930J40842193614.htm", "title": "集团产品线总监（P02/P03）- 中明科技", "description": "深圳，2-3万，本科"},
    {"url": "https://www.zhaopin.com/zhaopin/199c2f3536074cbaa9c6e9cb054ee756/", "title": "深圳总监招聘信息 - 智联招聘", "description": "高级硬件产品总监 2.5-4万，5-10年，本科"},
    {"url": "https://www.zhaopin.com/jobdetail/CCL1495979550J40716381511.htm", "title": "跨境电商产品总监/VP - 河南江舸云科技", "description": "深圳龙岗区，4-8万，5-10年，大专"},
    {"url": "https://www.zhaopin.com/zhaopin/56d4c78479064ed193355a4e63443c74/", "title": "健康险产品总监/经理 - 深圳", "description": "3-4万·15薪，5-10年，本科"},

    # Query: site:zhaopin.com "资深产品经理" "上海"
    {"url": "https://www.zhaopin.com/zhaopin/eaa924d1c1ac47c3981ebc04ff247f77/", "title": "资深产品经理（蛋白质组学）- 上海", "description": "2-3万，1-3年，硕士"},
    {"url": "http://www.zhaopin.com/jobdetail/CC383625320J40806457409.htm", "title": "账号资深产品经理 - 美团", "description": "北京，1-3年，本科"},
    {"url": "https://m.zhaopin.com/jobs/CCL1255416450J40843533508.htm", "title": "资深产品经理（网络营运）- 广东君润人力资源", "description": "3.5-5万，上海，10年以上，本科"},

    # Query: site:zhaopin.com "产品经理" "大模型" "杭州"
    {"url": "https://www.zhaopin.com/jobdetail/CCL1522194530J40937863402.htm", "title": "AI产品经理 - 杭州星核引力人工智能科技", "description": "1-2万·13薪，杭州，1-3年，AIGC大模型"},
    {"url": "https://m.zhaopin.com/zhaopin/8fe0d9ba93244152aa3147626584ba87/", "title": "杭州模型工作室招聘信息 - 智联招聘", "description": "ai大模型产品经理 2.2-3.5万，本科，3-5年"},
    {"url": "https://m.zhaopin.com/jobs/CC383625320J40658385209.htm", "title": "大模型评测产品经理 - 美团", "description": "杭州"},

    # Query: site:zhaopin.com "商业化" "产品经理" "香港"
    {"url": "http://www.zhaopin.com/jobdetail/CCL1474859510J40843727811.htm", "title": "建材产品经理 - 香港尚居綠色室内設計有限公司", "description": "深圳福田区，5-10年"},

    # Query: site:zhaopin.com "AI产品" "负责人" "上海"
    {"url": "http://jobs.zhaopin.com/CC000553110J40848152509.htm", "title": "人力资源AI产品经理 - 中智经济技术合作", "description": "1.8-2.5万，上海徐汇区，3-5年，本科"},
    {"url": "https://www.zhaopin.com/jobdetail/CC342985980J40849453909.htm", "title": "AI产品经理 - 上海勋厚人力资源", "description": "2-3万，上海浦东新区，5-10年，本科"},
    {"url": "https://www.zhaopin.com/jobdetail/CC153170410J40776545902.htm", "title": "ai产品经理（外企直签）", "description": "4-8万，10年以上，本科"},

    # Query: site:zhipin.com "产品经理" "50-70K" "深圳"
    {"url": "https://www.zhipin.com/zhaopin/29cb89de37b6e0361n140ty_Fw~~/", "title": "vivo产品经理 - 应用分发广告流量变现", "description": "50-70K，深圳，5-10年本科"},
    {"url": "https://www.zhipin.com/zhaopin/bf27f8b5a2d228403nRz3924/", "title": "产品经理 - 中澳通", "description": "50-70K·15薪，香港湾仔区铜锣湾，10年以上本科"},
    {"url": "https://www.zhipin.com/zhaopin/bcdae826b6f56f930nVz096-/", "title": "资深产品经理 - 迅雷网络", "description": "50-70K·16薪，深圳"},
    {"url": "https://www.zhipin.com/job_detail/8b381209a92177b81nN90t-_/", "title": "概率游戏产品负责人 - 迅雷网络", "description": "50-70K·15薪，深圳南山区科技园"},

    # Query: site:zhipin.com "产品总监" "60-90K" "上海"
    {"url": "https://www.zhipin.com/zhaopin/36aff8e9c717284b1nV639m1/", "title": "产品VP/产品总监招聘 - BOSS直聘", "description": "产品总监/产品VP 80-110K·15薪，AI业务负责人 60-90K·15薪"},
    {"url": "https://www.zhipin.com/zhaopin/b38fa49d1080ccdf1nF_3tW1FQ~~/", "title": "产品总监（女性向陪伴类海外产品）- 作业帮", "description": "60-90K·15薪，北京海淀区上地，5-10年本科"},
    {"url": "https://www.zhipin.com/zhaopin/8f628526395193ad0HRz39S4/", "title": "AI产品总监/医疗AI产品负责人 - 同花顺", "description": "80-110K·15薪，杭州余杭区五常，5-10年本科"},

    # Query: site:zhaopin.com "产品经理" "40-60K" "杭州"
    {"url": "https://m.zhaopin.com/zhaopin/8859214dbe0e460e9861d53fa0df5e36/", "title": "高级产品经理 - 杭州", "description": "3-5万，10年以上，硕士，工业自动化"},
]

TITLE_KEYWORDS = [
    '产品', 'product', '策略', 'strategy', '商业化', 'gtm', 'growth', '增长',
    '负责人', 'lead', 'director', '总监', 'head', 'vp', 'vice president',
    'ai', '大模型', 'model', 'platform', 'marketplace'
]
SENIORITY_KEYWORDS = [
    '资深', '专家', '总监', '负责人', 'head', 'lead', 'director', 'vp',
    'vice president', 'senior', 'sr.', 'manager', 'chief', 'coo', 'cmo',
    '产品经理', '产品总监', '产品负责人', 'product manager'
]
STOP_COMPANY_KEYWORDS = ['猎头', '人力', 'hr', 'staffing', 'recruitment']

def relevant(title, snippet):
    text = f'{title} {snippet}'.lower()
    return any(k.lower() in text for k in TITLE_KEYWORDS) and any(k.lower() in text for k in SENIORITY_KEYWORDS)

def dedup_staffing(title, snippet):
    text = f'{title} {snippet}'.lower()
    return not any(k in text for k in STOP_COMPANY_KEYWORDS)

def classify_from_title(title: str):
    t = title.lower()
    for s in ['vp ', 'vice president', 'c-level', 'chief ', 'coo', 'cmo']:
        if s in t:
            return 'S-1'
    for s in ['director', 'head of', '总监', '负责人', 'lead', 'principal']:
        if s in t:
            return 'A-1'
    for s in ['senior', 'sr.', '资深', '高级']:
        if s in t:
            return 'A-2'
    return 'A-2'

def extract_company(title, url, snippet):
    """Try to extract company name from title."""
    # Pattern: "Company - Title" or "Title - Company"
    dash_match = re.search(r'[-|–]\s*([^-|–]+?)$', title)
    if dash_match:
        candidate = dash_match.group(1).strip()
        if len(candidate) < 50 and not any(kw in candidate.lower() for kw in ['招聘', 'boos', 'boss', '智联']):
            return candidate
    return ''

def extract_location(title, snippet):
    text = f'{title} {snippet}'.lower()
    for loc, kws in {
        'Shenzhen': ['shenzhen','深圳'],
        'Guangzhou': ['guangzhou','广州'],
        'Hong Kong': ['hong kong','香港','kowloon','港'],
        'Shanghai': ['shanghai','上海'],
        'Hangzhou': ['hangzhou','杭州'],
        'Singapore': ['singapore'],
        'Tokyo': ['tokyo','东京'],
        'Taipei': ['taipei','台北'],
        'Beijing': ['beijing','北京'],
    }.items():
        if any(k in text for k in kws):
            return loc
    return ''

def main():
    print(f'Boss/Zhilian web_search processing: {len(WEB_SEARCH_RESULTS)} raw results')
    
    seen = set()
    formatted = []
    
    for r in WEB_SEARCH_RESULTS:
        url = r.get('url', '')
        title = r.get('title', '')
        snippet = r.get('description', r.get('snippet', ''))
        
        if not url or not title:
            continue
        if url in seen:
            continue
        if not relevant(title, snippet):
            continue
        if not dedup_staffing(title, snippet):
            continue
        seen.add(url)
        
        company = extract_company(title, url, snippet)
        location = extract_location(title, snippet)
        
        # Clean title - remove BOSS直聘/智联招聘 suffixes
        clean_title = re.sub(r'\s*[-|–]\s*(?:BOSS直聘|智联招聘|招聘)\s*$', '', title).strip()
        clean_title = re.sub(r'\s*[-|–]\s*BOSS\s*直聘\s*$', '', clean_title).strip()
        
        # Extract salary from description
        salary_match = re.search(r'(\d+[-–]\d+K(?:·\d+薪)?)', snippet)
        salary = salary_match.group(1) if salary_match else ''
        
        formatted.append({
            'title': clean_title,
            'company': company,
            'location': location,
            'grade': classify_from_title(clean_title),
            'url': url,
            'role_type': 'Product Management',
            'salary': salary,
            'scanned_date': datetime.now().strftime('%Y-%m-%d'),
            'source': 'boss-zhilian-websearch',
        })
    
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'boss-zhilian-discovery-results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(formatted, f, indent=2, ensure_ascii=False)
    print(f'Saved {len(formatted)} jobs to {out_path}')
    return formatted

if __name__ == '__main__':
    main()
