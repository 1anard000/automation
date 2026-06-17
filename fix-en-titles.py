#!/usr/bin/env python3
"""Fix missing en_title fields for all jobs in jobs-all.json.
Two passes:
1. English titles (no Chinese chars) → en_title = title
2. Chinese titles → translate common PM/strategy terms
"""
import json
import re
import shutil

# Chinese→English translation dictionary for common PM/strategy terms
ZH_EN = {
    '产品总监': 'Product Director',
    '产品线总监': 'Product Line Director',
    '资深产品经理': 'Senior Product Manager',
    '高级产品经理': 'Senior Product Manager',
    '产品经理': 'Product Manager',
    '产品负责人': 'Head of Product',
    '产品专家': 'Product Expert',
    '产品副总': 'VP of Product',
    '副总经理': 'Deputy General Manager',
    '总监': 'Director',
    '高级总监': 'Senior Director',
    '资深总监': 'Senior Director',
    '总经理': 'General Manager',
    '副总裁': 'Vice President',
    '高级副总裁': 'Senior Vice President',
    '首席产品官': 'Chief Product Officer',
    '首席技术官': 'Chief Technology Officer',
    '首席运营官': 'Chief Operating Officer',
    '战略总监': 'Strategy Director',
    '战略经理': 'Strategy Manager',
    '高级战略经理': 'Senior Strategy Manager',
    '战略负责人': 'Head of Strategy',
    '商务总监': 'Business Director',
    '商务经理': 'Business Manager',
    'BD总监': 'BD Director',
    'BD经理': 'BD Manager',
    'GTM总监': 'GTM Director',
    'GTM经理': 'GTM Manager',
    '市场总监': 'Marketing Director',
    '市场经理': 'Marketing Manager',
    '技术总监': 'Technical Director',
    '技术负责人': 'Head of Technology',
    '运营总监': 'Operations Director',
    '运营经理': 'Operations Manager',
    '运营负责人': 'Head of Operations',
    'AI产品经理': 'AI Product Manager',
    '支付产品经理': 'Payment Product Manager',
    '跨境支付产品经理': 'Cross-border Payment Product Manager',
    '金融产品经理': 'Financial Product Manager',
    '电商产品经理': 'E-commerce Product Manager',
    '海外产品经理': 'Overseas Product Manager',
    '机器人产品总监': 'Robotics Product Director',
    '机器人产品经理': 'Robotics Product Manager',
    '手机产品总监': 'Mobile Phone Product Director',
    '存储产品总监': 'Storage Product Director',
    '软件产品经理': 'Software Product Manager',
    '芯片产品经理': 'Chip Product Manager',
    '硬件产品经理': 'Hardware Product Manager',
    '互联网产品经理': 'Internet Product Manager',
    'SaaS产品经理': 'SaaS Product Manager',
    'B2B产品经理': 'B2B Product Manager',
    'ToB产品经理': 'ToB Product Manager',
    'ToC产品经理': 'ToC Product Manager',
    '海外': 'Overseas',
    '跨境': 'Cross-border',
    '出海': 'Global Expansion',
    '全球化': 'Globalization',
    '国际化': 'Internationalization',
    '资深': 'Senior',
    '高级': 'Senior',
    '初级': 'Junior',
    '中级': 'Mid-level',
    '统筹': 'Overseeing',
    '负责': 'Responsible for',
    '方向': 'Focus',
    '专家': 'Expert',
    '某': '(Confidential)',
    '世界500强': 'Fortune 500',
    '上市公司': 'Public Company',
    '知名公司': 'Known Company',
    '大型': 'Large',
    '深圳': 'Shenzhen',
    '上海': 'Shanghai',
    '北京': 'Beijing',
    '广州': 'Guangzhou',
    '杭州': 'Hangzhou',
    '成都': 'Chengdu',
    '南京': 'Nanjing',
    '武汉': 'Wuhan',
    '苏州': 'Suzhou',
    '厦门': 'Xiamen',
    '香港': 'Hong Kong',
    '新加坡': 'Singapore',
    '东京': 'Tokyo',
    '台北': 'Taipei',
    '人工智能': 'AI',
    '智能硬件': 'Smart Hardware',
    '消费电子': 'Consumer Electronics',
    '电子商务': 'E-commerce',
    '互联网': 'Internet',
    '物联网': 'IoT',
    '半导体': 'Semiconductor',
    '新能源': 'New Energy',
    '自动驾驶': 'Autonomous Driving',
    '金融科技': 'Fintech',
    '区块链': 'Blockchain',
    '云服务': 'Cloud Services',
    '大数据': 'Big Data',
    '机器学习': 'Machine Learning',
    '深度学习': 'Deep Learning',
    '自然语言处理': 'NLP',
    '计算机视觉': 'Computer Vision',
    '机器人': 'Robotics',
    '医疗': 'Healthcare',
    '医药': 'Pharmaceutical',
    '教育': 'Education',
    '游戏': 'Gaming',
    '社交': 'Social',
    '视频': 'Video',
    '音乐': 'Music',
    '广告': 'Advertising',
    '供应链': 'Supply Chain',
    '物流': 'Logistics',
    '零售': 'Retail',
    '餐饮': 'Food & Beverage',
    '酒店': 'Hotel',
    '旅游': 'Travel',
    '汽车': 'Automotive',
    '房产': 'Real Estate',
    '金融': 'Finance',
    '银行': 'Banking',
    '保险': 'Insurance',
    '证券': 'Securities',
    '基金': 'Fund',
    '投资': 'Investment',
    '风控': 'Risk Control',
    '合规': 'Compliance',
    '反洗钱': 'AML',
    '电子烟': 'E-cigarette',
    'SSD': 'SSD',
    'UFS': 'UFS',
    'eMMC': 'eMMC',
    '企业级': 'Enterprise',
    '音视频': 'Audio/Video',
    '旗舰': 'Flagship',
}


def translate_chinese_title(title):
    """Translate Chinese title to English, keeping English parts."""
    # If mostly English, just clean up
    if not re.search(r'[\u4e00-\u9fff]', title):
        return title

    result = title
    # Sort by length (longest first) to avoid partial matches
    for zh, en in sorted(ZH_EN.items(), key=lambda x: -len(x[0])):
        result = result.replace(zh, en)

    # If still has Chinese, try to extract meaningful parts
    remaining_zh = re.findall(r'[\u4e00-\u9fff]+', result)
    if remaining_zh:
        # Remove orphan Chinese fragments that couldn't be translated
        for zh in remaining_zh:
            if len(zh) <= 2:
                result = result.replace(zh, '')
            else:
                # Keep as-is if it's a company name or untranslatable
                pass

    # Clean up whitespace and punctuation
    result = re.sub(r'\s+', ' ', result).strip()
    result = re.sub(r'\s*-\s*$', '', result)
    result = re.sub(r'^\s*-\s*', '', result)
    result = re.sub(r'\(\s*\)', '', result)
    result = re.sub(r'\s+', ' ', result).strip()

    return result


def main():
    canonical = 'OKComputer_职位搜索清单/jobs-all.json'
    mirrors = [
        'jobs-all.json',
        'career-os/OKComputer_职位搜索清单/jobs-all.json',
    ]

    jobs = json.load(open(canonical))
    print(f'Loaded {len(jobs)} jobs')

    fixed_en = 0
    fixed_zh = 0
    skipped = 0

    for j in jobs:
        if j.get('en_title'):
            skipped += 1
            continue

        title = j.get('title', '')
        if not title:
            skipped += 1
            continue

        # Check if title is already English
        if not re.search(r'[\u4e00-\u9fff]', title):
            j['en_title'] = title
            fixed_en += 1
        else:
            translated = translate_chinese_title(title)
            if translated and translated != title:
                j['en_title'] = translated
                fixed_zh += 1
            else:
                # Fallback: set en_title to a cleaned version
                j['en_title'] = title
                fixed_zh += 1

    print(f'Fixed en_title from English titles: {fixed_en}')
    print(f'Fixed en_title from Chinese titles: {fixed_zh}')
    print(f'Skipped (already had en_title): {skipped}')

    # Save canonical
    with open(canonical, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f'Saved {canonical}')

    # Sync mirrors
    for mirror in mirrors:
        shutil.copy2(canonical, mirror)
        print(f'Synced to {mirror}')

    # Verify
    verify = json.load(open(canonical))
    still_missing = sum(1 for j in verify if not j.get('en_title'))
    print(f'\nVerification: {still_missing} jobs still missing en_title')


if __name__ == '__main__':
    main()
