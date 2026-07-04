#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deep analysis of classification JSON for promotion evaluation."""
import json
from collections import Counter, defaultdict

with open('scripts/classification_output/classification-2026-06-24T012908.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 80)
print("=== 1. PROMOTION CANDIDATES VERIFICATION ===")
print("=" * 80)

promotion_candidates = data.get('promotion_candidates', [])
all_models = {
    'model_1_three_elements': '体系三要素',
    'model_2_illusion': '假象认知',
    'model_3_buying': '买入不败',
    'model_4_competition': '竞争格局决定论',
    'model_5_scholarship': '显学大于隐学',
    'model_6_talent_cluster': '人才+产业集群',
    'model_7_crisis_chain': '危机演绎链',
    'model_8_timing': '择时双轨',
    'model_9_ai_reform': 'AI改造投资本身',
}

# Count actual articles per model from per_article data
model_article_count = defaultdict(int)
model_article_set = defaultdict(set)
for art in data.get('per_article', []):
    for m in art.get('top_models', []):
        model_id = m[0]
        model_article_count[model_id] += 1
        model_article_set[model_id].add(art['article'])

print(f"Total unique articles: {len(data['per_article'])}")
print(f"promotion_candidates list has {len(promotion_candidates)} entries")
print()
print(f"{'Model':<25} {'Name':<20} {'Claimed':>8} {'Actual':>8} {'OK?':>6}")
print("-" * 70)
for pc in promotion_candidates:
    model_id = pc['model']
    claimed = pc['articles']
    actual = len(model_article_set.get(model_id, set()))
    ok = "OK" if claimed == actual else f"MISMATCH ({actual})"
    print(f"{model_id:<25} {pc['name']:<20} {claimed:>8} {actual:>8} {ok:>6}")

# Check for model_9
m9_count = len(model_article_set.get('model_9_ai_reform', set()))
print(f"{'model_9_ai_reform':<25} {'AI改造投资本身':<20} {'(not listed)':>8} {m9_count:>8} {'N/A':>6}")

print()

# Domain count verification
print(f"{'Model':<25} {'Claimed Domains':>15}")
print("-" * 45)
for pc in promotion_candidates:
    model_id = pc['model']
    actual_articles = model_article_set.get(model_id, set())
    # Count unique themes from theme_distribution that match model's name
    # The domains field likely refers to unique heuristic themes
    print(f"{model_id:<25} {pc['domains']:>15}")

print()
print("=" * 80)
print("=== 2. PER-MODEL TOP 3 ARTICLES (by normalized score) ===")
print("=" * 80)

# For each of the 7 promoted models, find top 3 articles by score
promoted_models = ['model_1_three_elements', 'model_2_illusion', 'model_3_buying',
                   'model_4_competition', 'model_6_talent_cluster', 'model_7_crisis_chain',
                   'model_8_timing']

model_best = defaultdict(list)
for art in data.get('per_article', []):
    for m in art.get('top_models', []):
        model_id, model_name, score = m
        model_best[model_id].append((art['article'], score, model_name))

for model_id in promoted_models:
    name = all_models.get(model_id, model_id)
    articles = sorted(model_best.get(model_id, []), key=lambda x: -x[1])
    print(f"\n--- {model_id}: {name} ({len(articles)} total) ---")
    for i, (art_name, score, mname) in enumerate(articles[:3]):
        short_name = art_name[:80] + "..." if len(art_name) > 80 else art_name
        print(f"  {i+1}. [{score:.3f}] {short_name}")

print()
print("=" * 80)
print("=== 3. BLIND SPOT ANALYSIS: Models 5 (显学大于隐学) and 9 (AI改造投资本身) ===")
print("=" * 80)

for model_id in ['model_5_scholarship', 'model_9_ai_reform']:
    name = all_models.get(model_id, model_id)
    articles = sorted(model_best.get(model_id, []), key=lambda x: -x[1])
    print(f"\n--- {model_id}: {name} ---")
    print(f"  Total articles matched at ANY score: {len(articles)}")
    if articles:
        print(f"  Score range: {articles[-1][1]:.3f} - {articles[0][1]:.3f}")
        print(f"  Top 5 articles:")
        for i, (art_name, score, mname) in enumerate(articles[:5]):
            short_name = art_name[:100] + "..." if len(art_name) > 100 else art_name
            print(f"    {i+1}. [{score:.3f}] {short_name}")
    else:
        print("  No articles matched this model at all.")

# Check theme_distribution for model 5 and 9 themes
print("\nTheme distribution for model 5 and 9 themes:")
for td in data.get('theme_distribution', []):
    if '显学' in td['theme'] or 'AI改造' in td['theme']:
        print(f"  {td['theme']}: {td['count']}")

print()
print("=" * 80)
print("=== 4. THEME DISTRIBUTION vs MODEL COVERAGE ===")
print("=" * 80)

theme_model_count = defaultdict(lambda: defaultdict(int))
for art in data.get('per_article', []):
    for h in art.get('top_heuristics', []):
        h_id, h_theme, score = h
        for m in art.get('top_models', []):
            m_id, m_name, m_score = m
            theme_model_count[h_theme][m_name] += 1

print(f"\n{'Theme':<25} {'Count':>6} | Dominant Models")
print("-" * 80)
for td in sorted(data.get('theme_distribution', []), key=lambda x: -x['count']):
    theme = td['theme']
    count = td['count']
    models = theme_model_count.get(theme, {})
    if models:
        top_models = sorted(models.items(), key=lambda x: -x[1])[:3]
        model_str = ", ".join([f"{m}({c})" for m, c in top_models])
    else:
        model_str = "NO MODEL MATCH"
    print(f"{theme:<25} {count:>6} | {model_str}")

print()
print("=" * 80)
print("=== 5. HEURISTIC TRIGGERING PATTERNS ===")
print("=" * 80)

# Heuristic -> model co-occurrence
heuristic_model_cooccur = defaultdict(lambda: defaultdict(int))
heuristic_total = defaultdict(int)

for art in data.get('per_article', []):
    heuristics = art.get('top_heuristics', [])
    models = art.get('top_models', [])
    for h in heuristics:
        h_id, h_name, h_score = h
        heuristic_total[h_name] += 1
        for m in models:
            m_id, m_name, m_score = m
            heuristic_model_cooccur[h_name][m_name] += 1

print(f"\n{'Heuristic':<25} {'Total':>6} | {'Top Co-occurring Models':<50}")
print("-" * 85)
for h_name in sorted(heuristic_total.keys(), key=lambda x: -heuristic_total[x]):
    total = heuristic_total[h_name]
    co_models = sorted(heuristic_model_cooccur[h_name].items(), key=lambda x: -x[1])[:3]
    co_str = ", ".join([f"{m}({c})" for m, c in co_models])
    print(f"{h_name:<25} {total:>6} | {co_str}")

# Check for unexpected pairings
print("\n=== Unexpected Pairings Check ===")
# Heuristics that appear WITHOUT any model match
articles_no_model = []
articles_no_heuristic = []
for art in data.get('per_article', []):
    if not art.get('top_models'):
        articles_no_model.append(art['article'])
    if not art.get('top_heuristics'):
        articles_no_heuristic.append(art['article'])

print(f"Articles with NO model match: {len(articles_no_model)}")
if articles_no_model:
    for a in articles_no_model[:5]:
        print(f"  - {a[:100]}")

print(f"Articles with NO heuristic match: {len(articles_no_heuristic)}")
if articles_no_heuristic:
    for a in articles_no_heuristic[:5]:
        print(f"  - {a[:100]}")

print()
print("=" * 80)
print("=== 6. ADDITIONAL STATISTICS ===")
print("=" * 80)

# Average number of models and heuristics per article
model_counts_per_article = []
heuristic_counts_per_article = []
for art in data.get('per_article', []):
    model_counts_per_article.append(len(art.get('top_models', [])))
    heuristic_counts_per_article.append(len(art.get('top_heuristics', [])))

avg_models = sum(model_counts_per_article) / len(model_counts_per_article) if model_counts_per_article else 0
avg_heuristics = sum(heuristic_counts_per_article) / len(heuristic_counts_per_article) if heuristic_counts_per_article else 0

print(f"Average models per article: {avg_models:.2f}")
print(f"Average heuristics per article: {avg_heuristics:.2f}")
print(f"Max models on a single article: {max(model_counts_per_article)}")
print(f"Max heuristics on a single article: {max(heuristic_counts_per_article)}")

# Score distribution summary
all_scores = []
for art in data.get('per_article', []):
    for m in art.get('top_models', []):
        all_scores.append(m[2])

if all_scores:
    print(f"\nModel score stats: min={min(all_scores):.3f}, max={max(all_scores):.3f}, "
          f"avg={sum(all_scores)/len(all_scores):.3f}")
