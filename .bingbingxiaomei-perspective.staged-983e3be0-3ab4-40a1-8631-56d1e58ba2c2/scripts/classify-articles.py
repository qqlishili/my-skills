# -*- coding: utf-8 -*-
"""Article classifier for 冰冰小美 skill.

Maps articles to 9 models + 17 heuristics via keyword-weighted scoring.
Reuses probe infrastructure (VAULT path, article loading) from run_probe.py.
Outputs JSON classification results and promotion candidates.

Usage:
    python classify-articles.py [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--min-score 0.3]
"""

import os, re, json, sys
from collections import Counter, defaultdict
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================
VAULT = r"D:\Temp\karpathy-llm-wiki-vault\raw\02-投资\01-xueqiu\冰冰小美"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(SCRIPT_DIR, "classification_output")
os.makedirs(OUTDIR, exist_ok=True)

# Date range defaults (all available articles)
DEFAULT_START = "2023-01-01"
DEFAULT_END = "2026-12-31"

# ============================================================
# MODEL KEYWORDS (9 models, ordered by priority)
# ============================================================
MODEL_KEYWORDS = {
    "model_1_three_elements": {
        "name": "体系三要素",
        "type": "核心",
        "keywords": ["竞争格局", "流动性", "情绪", "三要素", "共振", "阻力最小",
                     "流动性挤压", "结构性分化", "重仓", "轻仓", "空仓"],
        # v1.1: keyword layering — discriminators (core identity) vs associators (general usage)
        # Hit rate: 43.5% → 16.3% (verified with 382 articles)
        "disc_keywords": ["三要素", "共振", "阻力最小"],
        "disc_weight": 3.0,
        "assoc_weight": 0.05,
    },
    "model_2_illusion": {
        "name": "假象认知",
        "type": "核心",
        "keywords": ["假象", "妖股", "题材", "涨停板", "ETF权重", "造神",
                     "传播", "人人皆知", "自媒体普及", "龙飞凤舞", "龙凤成翔"],
    },
    "model_3_buying": {
        "name": "买入不败",
        "type": "核心",
        "keywords": ["买入不败", "亏钱效应", "挣钱效应", "复利", "胜率",
                     "减少失败", "减少出手", "反向三问", "亏多少"],
    },
    "model_4_competition": {
        "name": "竞争格局决定论",
        "type": "核心",
        "keywords": ["安全与发展", "新质生产力", "国产替代", "十五五",
                     "时代主题", "新登", "老登", "增长性", "溢价",
                     "产业竞争", "国家竞争"],
    },
    "model_5_scholarship": {
        "name": "显学大于隐学",
        "type": "核心",
        "keywords": ["显学", "隐学", "阳谋", "阴谋", "公开知识",
                     "信息平权", "公开可查", "确定性"],
    },
    "model_6_talent_cluster": {
        "name": "人才+产业集群",
        "type": "核心",
        "keywords": ["人才", "千人计划", "产业集群", "海归", "硬核科技",
                     "技术壁垒", "研发投入", "专利", "自由现金流",
                     "光在苏州", "储存在深圳", "芯片在上海"],
    },
    "model_7_crisis_chain": {
        "name": "危机演绎链",
        "type": "扩展",
        "keywords": ["危机演绎", "扩散", "逐级", "传导", "宏观因子",
                     "市场因子", "三层", "共振", "美债", "美元指数",
                     "地缘", "第三方危机"],
    },
    "model_8_timing": {
        "name": "择时双轨",
        "type": "扩展",
        "keywords": ["择时", "低端择时", "高端择时", "冰点的冰点",
                     "风险减弱", "穿越股", "信贷扩张", "高速增长"],
    },
    "model_9_ai": {
        "name": "AI改造投资本身",
        "type": "扩展",
        "keywords": ["AI蒸馏", "信息差抹平", "经验贬值", "体系失效",
                     "AI改造", "AI效率", "AI竞争", "Claude"],
    },
}

# ============================================================
# HEURISTIC KEYWORDS (17 heuristics)
# ============================================================
HEURISTIC_KEYWORDS = {
    "h1_pbc": {"name": "信央妈信国运", "keywords": ["央妈", "央行", "相信国运", "降准", "降息", "MLF", "LPR"]},
    "h2_market_rhythm": {"name": "行情好多做", "keywords": ["行情好", "行情不好", "少做", "多做", "仓位"]},
    "h3_loss_effect": {"name": "观察亏钱效应", "keywords": ["亏钱效应", "风险规避", "买入不败"]},
    "h4_key_nodes": {"name": "把握关键节点", "keywords": ["关键节点", "牌翻出来", "时间表", "5[1-9][0-9]", "观望"]},
    "h5_buy_first": {"name": "买入比卖出重要", "keywords": ["T\\+1", "买入比卖出", "买入时机"]},
    "h6_crowd": {"name": "人多不挣钱", "keywords": ["人多", "人人皆知", "传播极限", "非股民朋友"]},
    "h7_reduce_attempts": {"name": "减少出手次数", "keywords": ["减少出手", "减少失败", "提高胜率", "10000元"]},
    "h8_empty_position": {"name": "空仓最高级", "keywords": ["空仓", "不参与", "行为尊重"]},
    "h9_speed": {"name": "快=理解快", "keywords": ["理解的快", "不是交易的快", "提前理解"]},
    "h10_belief": {"name": "相信的力量", "keywords": ["相信", "坚守", "体系确认", "重头再来"]},
    "h11_liquidity_squeeze": {"name": "流动性挤压控制仓位", "keywords": ["流动性挤压", "控制仓位", "控制风险"]},
    "h12_new_vs_old": {"name": "新登≠泡沫老登=泡沫", "keywords": ["新登", "老登", "无增长", "泡沫", "高估值"]},
    "h13_pboc_first": {"name": "央妈以我为主", "keywords": ["以我为主", "央妈决策", "不跟随", "米联储", "脱钩"]},
    "h14_industry_belief": {"name": "产业信念优先", "keywords": ["产业信念", "技术面", "顶背离", "不一样了", "企业变了"]},
    "h15_leverage": {"name": "杠杆出清线", "keywords": ["杠杆出清", "杠杆", "出清线", "跌破", "编年体"]},
    "h16_liquidity_vs_biz": {"name": "流动性预期≠经营", "keywords": ["杀流动性", "杀逻辑", "企业经营", "没发生", "基本面"]},
    "h17_active_loss": {"name": "主动买亏边界", "keywords": ["主动买亏", "三重边界", "止损线", "产业逻辑"]},
}

# ============================================================
# WEIGHTS
# ============================================================
MODEL_WEIGHT = 1.0       # models are primary classification
HEURISTIC_WEIGHT = 0.7   # heuristics are secondary
TITLE_BOOST = 1.5        # keyword in title gets extra weight

# ============================================================
# ARTICLE LOADING (reuse probe convention)
# ============================================================
def load_articles(start=None, end=None):
    """Load articles from VAULT within date range.
    
    File naming: 'YYYY-MM-DD HHMMSS_冰冰小美_TITLE.md'
    """
    if start is None:
        start = datetime.strptime(DEFAULT_START, "%Y-%m-%d")
    if end is None:
        end = datetime.strptime(DEFAULT_END, "%Y-%m-%d")
    
    articles = []
    for fname in sorted(os.listdir(VAULT)):
        m = re.match(r'(\d{4}-\d{2}-\d{2}) (\d{6})_冰冰小美_(.+)\.md', fname)
        if not m:
            continue
        date_str, time_str, title = m.groups()
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H%M%S")
        if not (start <= dt <= end):
            continue
        filepath = os.path.join(VAULT, fname)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                body = f.read()
        except Exception as e:
            print(f"WARN: Cannot read {fname}: {e}", file=sys.stderr)
            continue
        # Extract content after YAML frontmatter if present
        content = body.split('---', 2)[-1] if body.startswith('---') else body
        articles.append({
            'date': date_str,
            'time': time_str,
            'dt': dt,
            'title': title,
            'fname': fname,
            'content': content,
            'len': len(content),
        })
    articles.sort(key=lambda a: a['dt'])
    return articles


# ============================================================
# SCORING
# ============================================================
def score_keywords(text, keywords, title_text="", title_boost=TITLE_BOOST):
    """Score text against keyword list. Returns raw match count weighted by unique matches."""
    text_lower = text.lower()
    matches = 0
    for kw in keywords:
        kw_lower = kw.lower()
        count = text_lower.count(kw_lower)
        if count > 0:
            matches += min(count, 3)  # cap at 3 per keyword
        # Title boost
        if title_text and kw_lower in title_text.lower():
            matches += title_boost
    return matches


def classify_article(article):
    """Classify one article against all models and heuristics."""
    text = article['content']
    title = article['title']
    
    model_scores = {}
    for model_id, model_info in MODEL_KEYWORDS.items():
        # Support keyword layering (discriminators vs associators)
        if 'disc_keywords' in model_info:
            disc_raw = score_keywords(text, model_info['disc_keywords'], title)
            # Non-disc keywords = full list minus disc list
            assoc_list = [kw for kw in model_info['keywords'] if kw not in model_info['disc_keywords']]
            assoc_raw = score_keywords(text, assoc_list, title)
            raw = disc_raw * model_info.get('disc_weight', 1.0) + assoc_raw * model_info.get('assoc_weight', 1.0)
        else:
            raw = score_keywords(text, model_info['keywords'], title)
        model_scores[model_id] = {
            'name': model_info['name'],
            'type': model_info['type'],
            'raw_score': raw,
            'weighted': raw * MODEL_WEIGHT,
        }
    
    heuristic_scores = {}
    for h_id, h_info in HEURISTIC_KEYWORDS.items():
        raw = score_keywords(text, h_info['keywords'], title)
        heuristic_scores[h_id] = {
            'name': h_info['name'],
            'raw_score': raw,
            'weighted': raw * HEURISTIC_WEIGHT,
        }
    
    # Normalize to 0-1 scale
    max_model = max(s['weighted'] for s in model_scores.values()) or 1
    max_h = max(s['weighted'] for s in heuristic_scores.values()) or 1
    
    for s in model_scores.values():
        s['normalized'] = round(s['weighted'] / max_model, 3) if max_model else 0
    for s in heuristic_scores.values():
        s['normalized'] = round(s['weighted'] / max_h, 3) if max_h else 0
    
    # Top matches (> threshold)
    threshold = 0.3
    top_models = sorted(
        [(mid, s) for mid, s in model_scores.items() if s['normalized'] >= threshold],
        key=lambda x: -x[1]['normalized']
    )
    top_heuristics = sorted(
        [(hid, s) for hid, s in heuristic_scores.items() if s['normalized'] >= threshold],
        key=lambda x: -x[1]['normalized']
    )
    
    return {
        'article': f"{article['date']} {article['time']}_{article['title']}",
        'fname': article['fname'],
        'len': article['len'],
        'top_models': [(mid, s['name'], s['normalized']) for mid, s in top_models[:5]],
        'top_heuristics': [(hid, s['name'], s['normalized']) for hid, s in top_heuristics[:5]],
        'model_scores': model_scores,
        'heuristic_scores': heuristic_scores,
    }


# ============================================================
# PROMOTION CHECK
# ============================================================
def check_promotion(all_results, min_score=0.3, min_articles=4, min_domains=3):
    """Check if any model meets promotion criteria: ≥N articles × ≥M domains."""
    model_domain_hits = defaultdict(list)
    for r in all_results:
        for mid, name, score in r['top_models']:
            if score >= min_score:
                # Use date month as proxy for domain (actual domain would need content analysis)
                domain = r['article'][:7]  # YYYY-MM
                model_domain_hits[mid].append(domain)
    
    candidates = []
    for mid, domains in model_domain_hits.items():
        unique_domains = len(set(domains))
        total_articles = len(domains)
        if total_articles >= min_articles and unique_domains >= min_domains:
            candidates.append({
                'model': mid,
                'name': MODEL_KEYWORDS[mid]['name'],
                'articles': total_articles,
                'domains': unique_domains,
            })
    
    return sorted(candidates, key=lambda c: -c['articles'])


# ============================================================
# THEME TRACKING (probe-themes equivalent)
# ============================================================
def track_themes(all_results, min_theme_articles=3):
    """Track emerging themes from top model/heuristic matches."""
    theme_counts = defaultdict(int)
    article_themes = defaultdict(list)
    
    for r in all_results:
        article_key = r['article'][:35]
        for mid, name, score in r['top_models'][:2]:  # top 2 models per article
            theme_counts[name] += 1
            article_themes[name].append(article_key)
        for hid, name, score in r['top_heuristics'][:2]:
            theme_counts[name] += 1
            article_themes[name].append(article_key)
    
    themes = [
        {'theme': t, 'count': c, 'sample': article_themes[t][:3]}
        for t, c in sorted(theme_counts.items(), key=lambda x: -x[1])
        if c >= min_theme_articles
    ]
    return themes


# ============================================================
# OUTPUT
# ============================================================
def output_json(all_results, outdir, prefix="classification"):
    """Write classification results and promotion candidates to JSON."""
    timestamp = datetime.now().strftime("%Y-%m-%dT%H%M%S")
    
    # Full results
    outfile = os.path.join(outdir, f"{prefix}-{timestamp}.json")
    results_summary = []
    for r in all_results:
        results_summary.append({
            'article': r['article'],
            'top_models': r['top_models'][:3],
            'top_heuristics': r['top_heuristics'][:3],
        })
    
    # Promotion candidates
    candidates = check_promotion(all_results)
    
    # Theme tracking
    themes = track_themes(all_results)
    
    output = {
        'timestamp': timestamp,
        'total_articles': len(all_results),
        'promotion_candidates': candidates,
        'theme_distribution': themes,
        'per_article': results_summary,
    }
    
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"Classification results saved to {outfile}")
    return outfile


def output_summary(all_results):
    """Print human-readable summary to stdout."""
    candidates = check_promotion(all_results)
    themes = track_themes(all_results)
    
    print(f"\n{'='*60}")
    print(f"  Article Classification Summary")
    print(f"  Total: {len(all_results)} articles")
    print(f"{'='*60}\n")
    
    # Promotion candidates
    if candidates:
        print("[PROMOTION] PROMOTION CANDIDATES:")
        for c in candidates:
            print(f"  {c['name']} ({c['model']}): {c['articles']} articles × {c['domains']} domains")
    else:
        print("No promotion candidates found.")
    
    # Theme distribution
    print(f"\n[THEMES] THEME DISTRIBUTION (top {len(themes)}):")
    for t in themes[:15]:
        bar = "█" * min(t['count'], 40)
        print(f"  {t['theme']:<20} {bar} {t['count']}")
    
    # Model coverage
    model_hits = Counter()
    for r in all_results:
        for mid, name, score in r['top_models'][:1]:
            model_hits[name] += 1
    
    print(f"\n[MODELS] MODEL COVERAGE:")
    for name, count in model_hits.most_common():
        pct = count / len(all_results) * 100
        print(f"  {name:<20} {count:>3} articles ({pct:.0f}%)")


# ============================================================
# MAIN
# ============================================================
def main():
    start = DEFAULT_START
    end = DEFAULT_END
    min_score = 0.3
    
    # Parse CLI args
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--start' and i + 1 < len(args):
            start = datetime.strptime(args[i+1], "%Y-%m-%d")
            i += 2
        elif args[i] == '--end' and i + 1 < len(args):
            end = datetime.strptime(args[i+1], "%Y-%m-%d")
            i += 2
        elif args[i] == '--min-score' and i + 1 < len(args):
            min_score = float(args[i+1])
            i += 2
        else:
            i += 1
    
    print(f"Loading articles from {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}...")
    articles = load_articles(start, end)
    print(f"Loaded {len(articles)} articles.")
    
    if not articles:
        print("No articles found in date range.")
        return
    
    # Classify
    all_results = []
    for i, article in enumerate(articles):
        if (i + 1) % 20 == 0:
            print(f"  Processing... {i+1}/{len(articles)}")
        result = classify_article(article)
        all_results.append(result)
    
    # Output
    output_json(all_results, OUTDIR)
    output_summary(all_results)


if __name__ == '__main__':
    main()
