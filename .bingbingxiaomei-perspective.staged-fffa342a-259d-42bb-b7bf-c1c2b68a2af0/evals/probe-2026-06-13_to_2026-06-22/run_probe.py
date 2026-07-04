# -*- coding: utf-8 -*-
"""Probe analyzer for 2026-06-13 to 2026-06-22 articles."""

import os, re, json
from collections import Counter, defaultdict
from datetime import datetime

VAULT = r"D:\Temp\karpathy-llm-wiki-vault\raw\02-投资\01-xueqiu\冰冰小美"
OUTDIR = r"D:\Temp\create_skills\bingbingxiaomei-perspective\evals\probe-2026-06-13_to_2026-06-22"

# --- Load articles ---
articles = []
for fname in sorted(os.listdir(VAULT)):
    m = re.match(r'(\d{4}-\d{2}-\d{2}) (\d{6})_冰冰小美_(.+)\.md', fname)
    if not m:
        continue
    date_str, time_str, title = m.groups()
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H%M%S")
    if not (datetime(2026,6,13) <= dt <= datetime(2026,6,23,0,0)):
        continue
    with open(os.path.join(VAULT, fname), 'r', encoding='utf-8') as f:
        body = f.read()
    content = body.split('---', 2)[-1] if body.startswith('---') else body
    articles.append({
        'date': date_str, 'time': time_str, 'dt': dt,
        'title': title, 'fname': fname,
        'content': content, 'len': len(content)
    })

articles.sort(key=lambda a: a['dt'])
print(f"Loaded {len(articles)} articles from 2026-06-13 to 2026-06-22")

# ============================================================
# 1. FREQUENCY ANALYSIS
# ============================================================
daily = defaultdict(list)
for a in articles:
    daily[a['date']].append(a)

hourly = defaultdict(list)
for a in articles:
    hourly[int(a['time'][:2])].append(a)

freq_lines = []
freq_lines.append(f"# 发帖频率分析 (2026-06-13 ~ 2026-06-22)\n")
freq_lines.append(f"总文章数: {len(articles)}")
freq_lines.append(f"跨度: 10 天")
freq_lines.append(f"日均: {len(articles)/10:.1f} 篇\n")

freq_lines.append("## 每日分布\n")
for d in sorted(daily):
    posts = daily[d]
    weekday = posts[0]['dt'].strftime('%A')
    total_chars = sum(p['len'] for p in posts)
    freq_lines.append(f"- {d} ({weekday}): {len(posts):2d} 篇, {total_chars:,} 字, 均 {total_chars//max(len(posts),1):,} 字/篇")

freq_lines.append("\n## 时段分布\n")
for h in range(24):
    if h not in hourly:
        continue
    posts = hourly[h]
    total_chars = sum(p['len'] for p in posts)
    freq_lines.append(f"- {h:02d}:00-{h:02d}:59: {len(posts):2d} 篇, {total_chars:,} 字")

freq_lines.append(f"\n## 密度对比（与上次 probe 140 篇跨度的对比）\n")
freq_lines.append(f"- 上次 probe (05-19~06-11): 140 篇 / 24 天 = 5.8 篇/天")
freq_lines.append(f"- 本次 probe (06-13~06-22): {len(articles)} 篇 / 10 天 = {len(articles)/10:.1f} 篇/天")
freq_lines.append(f"- 密度变化: {(len(articles)/10 - 5.8):+.1f} 篇/天")

# Identify high-density days (> 1.5x average)
avg = len(articles) / 10
freq_lines.append(f"\n## 高密度日 (> {avg*1.5:.0f} 篇)\n")
for d in sorted(daily):
    if len(daily[d]) > avg * 1.5:
        freq_lines.append(f"- **{d}**: {len(daily[d])} 篇 ← 异常密集")

with open(os.path.join(OUTDIR, 'probe-freq.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(freq_lines))

# ============================================================
# 2. KEYWORD ANALYSIS
# ============================================================
# Chinese keyword extraction - use jieba if available, else simple char-based
all_text = ' '.join(a['content'] for a in articles)

# Manual keyword categories
kw_groups = {
    '市场术语': ['流动性', '挤压', 'ICU', 'KTV', '蹦迪', '冰点', '恐慌', '贪婪', '泡沫',
              '风险', '危机', '杠杆', '仓位', '分仓', '控仓', '空仓', '左侧', '右侧'],
    '产业方向': ['AI', '人工智能', '芯片', '半导体', '算力', '储存', '光', 'PCB', '元件',
              '材料', '铜箔', '锂电', '碳酸锂', '有色', '石油', '商业航天', 'SpaceX',
              '新能源', '消费', '白酒', '银行', '保险', '汽车'],
    '个股': ['紫金', '西部矿业', '江丰', '长电', '赛力斯', '铜冠铜箔', '东材', '东阳光',
            '寒武纪', '兆易创新', '盛龙', '多氟多', '星源材质', '湖南裕能', '柳工', '比亚迪',
            '英特尔', '英伟达', '博通', '江波龙', '中芯国际', '长鑫', '新洁能'],
    '概念框架': ['三要素', '竞争格局', '显学', '隐学', '老登', '新登', '体系', '产业',
              '长期主义', '买入不败', '亏钱效应', '挣钱效应', '穿越', '国运', '央妈',
              '造神', '假象', '确定性'],
    '人物引用': ['格林斯潘', '翟东升', '孙子', '毛泽东', '章盟主', '唐总', '巴菲特', '马斯克'],
    '新增术语': ['蒸馏', '元层面', '七姐妹', 'K型', '新国标', '陆家嘴', '科创', 'IPO',
               '估值拉近', '材料端', '切换', '穿越股', '文明史', '轮回']
}

kw_counts = {}
for cat, words in kw_groups.items():
    kw_counts[cat] = {}
    for w in words:
        count = all_text.count(w)
        if count > 0:
            kw_counts[cat][w] = count

kw_lines = []
kw_lines.append(f"# 关键词频率分析 (2026-06-13 ~ 2026-06-22, {len(articles)} 篇)\n")

for cat in kw_groups:
    items = sorted(kw_counts[cat].items(), key=lambda x: -x[1])
    if not items:
        continue
    kw_lines.append(f"## {cat}\n")
    for word, count in items:
        if count >= 2:
            kw_lines.append(f"- {word}: {count} 次")

# Compare with previous probe if available
prev_keyword_path = r"D:\Temp\create_skills\bingbingxiaomei-perspective\evals\probe-keyword-samples.txt"
prev_keywords = {}
if os.path.exists(prev_keyword_path):
    with open(prev_keyword_path, 'r', encoding='utf-8') as f:
        prev_text = f.read()
    kw_lines.append(f"\n\n## 与上次 probe (05-19~06-11) 对比\n")
    kw_lines.append("> 以下列出两次 probe 中频率变化显著的关键词\n")
    for cat in kw_groups:
        changes = []
        for w in kw_groups[cat]:
            new_count = all_text.count(w)
            old_count = prev_text.count(w)
            if new_count != old_count and (new_count > 3 or old_count > 3):
                changes.append((w, old_count, new_count))
        if changes:
            kw_lines.append(f"### {cat}")
            for w, old, new in sorted(changes, key=lambda x: -(x[2]-x[1])):
                delta = new - old
                kw_lines.append(f"- {w}: {old} → {new} ({delta:+d})")

with open(os.path.join(OUTDIR, 'probe-keyword.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(kw_lines))

# ============================================================
# 3. THEME ANALYSIS
# ============================================================
# Categorize each article into themes
theme_map = {
    '宏观/货币': ['美联储', '议息', '通胀', '降息', '加息', '央妈', '汇率', '缩表', '美元',
               '美债', '货币', '财政', 'GDP', '经济数据', 'Cpi', 'M2', '社融'],
    '地缘/战略': ['中美', '战略', '竞争', '制裁', '日韩', '土耳其', '关税', '贸易'],
    'AI/科技产业': ['AI', '芯片', '半导体', '算力', '储存', '光', '元件', 'PCB', '英特尔',
                 '英伟达', '博通', '寒武纪', '兆易'],
    '材料/周期': ['有色', '铜', '锂', '石油', '稀土', '材料', '铜箔', '树脂', '磷化铟',
               '氮化镓', '碳化硅', '紫金', '西部', '东材'],
    '锂电/新能源': ['锂电', '碳酸锂', '新国标', '多氟多', '星源', '湖南裕能', '电池',
                 '新能源车'],
    '商业航天': ['SpaceX', '商业航天', '航天', '卫星'],
    '交易/仓位': ['仓位', '分仓', '减仓', '建仓', '清仓', '左侧', '右侧', 'T+0', '做T',
               '被套', '止损', '割肉'],
    '投资理念': ['体系', '信念', '国运', '长期', '产业', '认知', '格局', '时代', '穿越',
              '老登', '新登', '价值', '估值'],
    '反思/元层': ['蒸馏', 'Claude', 'AI改造', '更新', '停更', '发帖', '作业'],
    '事件/政策': ['陆家嘴', '证监会', '打击伪科技', '新国标', 'Ipo', 'Space X IPO',
               '格林斯潘'],
    '消费/老登': ['白酒', '消费', '银行', '保险', '房地产', '汽车销售'],
}

theme_articles = defaultdict(list)
for a in articles:
    text = a['content']
    scores = {}
    for theme, keywords in theme_map.items():
        score = sum(text.count(k) for k in keywords)
        if score > 0:
            scores[theme] = score
    if not scores:
        best = '其他'
    else:
        best = max(scores, key=scores.get)
    theme_articles[best].append(a)

theme_lines = []
theme_lines.append(f"# 主题聚类分析 (2026-06-13 ~ 2026-06-22, {len(articles)} 篇)\n")
theme_lines.append("> 方法: 关键词加权匹配，每篇文章归属得分最高的主题\n")

# Sort themes by article count
sorted_themes = sorted(theme_articles.items(), key=lambda x: -len(x[1]))

theme_lines.append("## 主题分布\n")
total = len(articles)
for theme, arts in sorted_themes:
    pct = len(arts) / total * 100
    theme_lines.append(f"### {theme}: {len(arts)} 篇 ({pct:.0f}%)")
    for a in arts[:5]:
        title_short = a['title'][:60]
        theme_lines.append(f"- {a['date']} {a['time'][:4]}: {title_short}")

theme_lines.append(f"\n\n## 新概念候选\n")
theme_lines.append("> 以下概念/术语在本次 probe 中首次出现或强度显著提升\n")

# New/amplified concepts
new_concepts = {
    '文明史视角（500年轮回）': {'source': '06-17 171113', 'desc': '荷兰→西班牙→法国→英国→美国 500 年周期，超越 9 年框架的更大尺度历史观', 'articles': 1, 'significance': '全新层次——从"竞争格局决定论"的 9 年周期扩展到 500 年文明史'},
    '未来七姐妹': {'source': '06-18 214812', 'desc': '谷歌/苹果/SpaceX/英伟达/英特尔/Anthropic/博通，产业格局新命名', 'articles': 1, 'significance': '对标"漂亮 50"的新时代产业标签'},
    '中美战略实施加速转折点': {'source': '06-20 102347', 'desc': '2026 年中美关系从"新型关系"进入"加速实施"阶段的标志', 'articles': 1, 'significance': '对模型 4 竞争格局决定论的直接升级——关系阶段从"定性"进入"量化实施"'},
    'Claude解读自我=AI蒸馏实证': {'source': '06-17 182748', 'desc': '用户用 Claude 分析冰冰小美当天 11 条帖子，她转发并认可。逐条分析从宏观定调到文明史的逻辑链', 'articles': 1, 'significance': '模型 10 AI改造投资的终极证据——不是AI分析市场，是AI分析分析师自身'},
    '铜冠铜箔 20 倍方法论': {'source': '06-21 085651/092036/093344', 'desc': '技术节点卡位+宏观叙事卡位+大宗商品联动，三维度分析一只 20 倍股', 'articles': 3, 'significance': '个股深度研究的完整方法论样本——比八步框架更实战'},
    '新国标锂电产业': {'source': '06-22 193227', 'desc': '强制国标改变锂电池生态，布置 7/1 作业', 'articles': 1, 'significance': '从"科普"到"留作业"——从教师到导师的转变'},
    '材料端→锂电有色切换': {'source': '06-22 135134', 'desc': '从光/PCB/材料端逐步卖出，切换至锂电+有色，完整的产业轮动信号', 'articles': 1, 'significance': '三要素在产业轮动中的实战样本'},
    '格林斯潘去世': {'source': '06-22 233243', 'desc': '"一半财富来自他对危机的定义。繁荣与衰退，非理性繁荣"', 'articles': 1, 'significance': '智识谱系闭环——影响层级从"工具性"升级为"结构性"'},
}

for name, info in new_concepts.items():
    theme_lines.append(f"### {name}")
    theme_lines.append(f"- 来源: {info['source']}")
    theme_lines.append(f"- 描述: {info['desc']}")
    theme_lines.append(f"- 篇数: {info['articles']}")
    theme_lines.append(f"- 意义: {info['significance']}")
    theme_lines.append("")

theme_lines.append(f"\n\n## 与上次 probe 主题对比\n")
theme_lines.append(f"- 上次 (05-19~06-11): 流动性挤压 / AI蒸馏 / 泡沫新定义 / 新美联储焦虑 / 央妈以我为主 / 纠错复盘")
theme_lines.append(f"- 本次 (06-13~06-22): 文明史 / 七姐妹 / 中美加速 / 商业航天 / 铜冠铜箔 / 新国标 / 格林斯潘")
theme_lines.append(f"- 延续: 流动性挤压、老登/新登、AI产业链、风险节点")
theme_lines.append(f"- 新增: 文明史视角、商业航天崛起、新国标监管、产业轮动实操")

with open(os.path.join(OUTDIR, 'probe-themes.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(theme_lines))

# ============================================================
# 4. SUMMARY
# ============================================================
print(f"\nDone. Output files:")
print(f"  {os.path.join(OUTDIR, 'probe-freq.txt')}")
print(f"  {os.path.join(OUTDIR, 'probe-keyword.txt')}")
print(f"  {os.path.join(OUTDIR, 'probe-themes.txt')}")

summary = {
    'total_articles': len(articles),
    'date_range': '2026-06-13 to 2026-06-22',
    'daily_avg': len(articles) / 10,
    'max_day': max(daily, key=lambda d: len(daily[d])),
    'max_day_count': len(daily[max(daily, key=lambda d: len(daily[d]))]),
    'top_themes': [(t, len(a)) for t, a in sorted_themes[:5]],
    'new_concepts': list(new_concepts.keys()),
}
print(f"\nSummary: {json.dumps(summary, ensure_ascii=False, indent=2)}")
