# Promotion Deep Analysis Report

**Source file:** `scripts/classification_output/classification-2026-06-24T012908.json`
**Generated:** 2026-06-24
**Total articles:** 363
**Promotion threshold:** >= 19 articles (model_6_人才+产业集群 at 19 articles is the last promoted)

---

## 1. Promotion Candidates Verification

### 1.1 Summary

| # | Model | Name | Claimed Articles | Verified Articles | Status |
|---|-------|------|----------------:|------------------:|--------|
| 1 | model_1_three_elements | 体系三要素 | 158 | 158 | OK |
| 2 | model_4_competition | 竞争格局决定论 | 51 | **48** | MISMATCH (-3) |
| 3 | model_2_illusion | 假象认知 | 50 | 50 | OK |
| 4 | model_3_buying | 买入不败 | 46 | **45** | MISMATCH (-1) |
| 5 | model_7_crisis_chain | 危机演绎链 | 43 | **38** | MISMATCH (-5) |
| 6 | model_8_timing | 择时双轨 | 20 | 20 | OK |
| 7 | model_6_talent_cluster | 人才+产业集群 | 19 | 19 | OK |

### 1.2 Verification details

**3 of 7 candidates have article count mismatches:**

- **model_4_competition (竞争格局决定论):** Claimed 51, verifiable unique = 48 (gap: -3). The claimed count may have counted articles appearing in multiple ranking positions more than once, or used theme_distribution's "竞争格局决定论" theme count (41) + other contributions, resulting in an inflated total.

- **model_7_crisis_chain (危机演绎链):** Claimed 43, verifiable unique = 38 (gap: -5). Largest discrepancy. The claimed 43 is suspiciously close to 38 + 5 which could represent articles counted from both model matching AND heuristic matching that share this model's theme.

- **model_3_buying (买入不败):** Claimed 46, verifiable unique = 45 (gap: -1). Minor discrepancy, likely a counting artifact.

### 1.3 Non-promoted models

| Model | Name | Articles | Status |
|-------|------|---------:|--------|
| model_5_scholarship | 显学大于隐学 | 16 (claimed 17) | Below threshold (-1 vs claimed) |
| model_9_ai_reform | AI改造投资本身 | 4 | Not in candidates, far below threshold |

### 1.4 Claimed domain counts

All claimed domain counts appear plausible but cannot be independently verified from `per_article` data alone (the "domains" field likely refers to the number of unique heuristic themes associated with each model, which requires additional cross-referencing logic).

---

## 2. Per-Model Top 3 Articles (by normalized score)

### 2.1 model_1_three_elements — 体系三要素 (158 articles)

| Rank | Score | Article |
|------|-------|---------|
| 1 | 1.000 | 2023-03-10 161631_本周操作记录混乱的竞争格局，导致混乱的择股操作... |
| 2 | 1.000 | 2023-03-19 113043_常见的亏钱认知，第二期，止损 |
| 3 | 1.000 | 2023-03-19 232929_常见的亏钱认知，第三期，懂的都懂 |

**Note:** 158 articles all scored at ~1.0 → this model has zero discriminative power. 体系三要素 is the "base class" model that absorbs almost everything. This is problematic for a 9-model framework.

### 2.2 model_2_illusion — 假象认知 (50 articles)

| Rank | Score | Article |
|------|-------|---------|
| 1 | 1.000 | 2023-03-20 122713_常见的亏钱认知，第四期，概念逻辑 |
| 2 | 1.000 | 2023-04-13 161113_流动性的辩证分析 |
| 3 | 1.000 | 2023-05-10 080020_核心情绪标，套利标，和市场行为的假象 |

### 2.3 model_3_buying — 买入不败 (45 articles)

| Rank | Score | Article |
|------|-------|---------|
| 1 | 1.000 | 2023-05-10 084709_买卖与性格 |
| 2 | 1.000 | 2023-06-20 115912_常见的亏钱认知，第九期，切勿追涨 |
| 3 | 1.000 | 2023-08-21 113941_常见的亏钱认知，第十五期，套利的危害内容列表 |

### 2.4 model_4_competition — 竞争格局决定论 (48 articles)

| Rank | Score | Article |
|------|-------|---------|
| 1 | 1.000 | 2026-05-08 222646_某种意义上看，中米科技上涨，是竞争失败失去国际地位的恐惧下... |
| 2 | 1.000 | 2026-05-08 225743_那么，时代背景是竞争。这个北美去年国情咨文就改了... |
| 3 | 1.000 | 2026-05-11 150905_商业航天交易是封神过的。没有涨的时候就交易了 中国卫星... |

**Note:** Strong 2026 bias — all top 3 are from May 2026. This model is concentrated in recent geopolitical content.

### 2.5 model_6_talent_cluster — 人才+产业集群 (19 articles)

| Rank | Score | Article |
|------|-------|---------|
| 1 | 1.000 | 2026-05-08 095736_基本不受外围影响，材料端的强势是供需周期推动既视感... |
| 2 | 1.000 | 2026-05-08 224142_那么，意识到这种竞争，你就会选择真正硬核科技的企业... |
| 3 | 1.000 | 2026-05-11 141200_说点有的没的。问，是如何发现硬核科技的？... |

**Note:** All top articles also from May 2026. Very narrow temporal concentration.

### 2.6 model_7_crisis_chain — 危机演绎链 (38 articles)

| Rank | Score | Article |
|------|-------|---------|
| 1 | 1.000 | 2025-03-16 185442_分享新闻，立马就有留言，利好什么利空什么... |
| 2 | 1.000 | 2026-05-08 231327_去年黄金美债叙事，核心在于冲突... |
| 3 | 1.000 | 2026-05-14 181830_谈盈利得失没啥意义。我已经尽力。A股很显然博弈剧烈... |

### 2.7 model_8_timing — 择时双轨 (20 articles)

| Rank | Score | Article |
|------|-------|---------|
| 1 | 1.000 | 2026-05-11 170755_如果这一次48提示风险减弱的节点，我没做多科技的话... |
| 2 | 1.000 | 2026-05-14 173920_514魔咒如期而至 |
| 3 | 1.000 | 2026-05-15 142924_短期风险提过514节点。这个节点还满仓ALL IN那么文章白看... |

**Note:** All top articles cluster around the "514 魔咒" event. Strong event-driven, not time-diverse.

---

## 3. Blind Spot Analysis: Models 5 and 9

### 3.1 model_5_scholarship — 显学大于隐学

**Score distribution:** 16 articles matched at scores 0.400 - 1.000

**Top 5 matches:**

| Score | Article |
|-------|---------|
| 1.000 | 2024-04-02 154325_我那个读书年代，很多人鄙视四大名著。甚至出现厚黑学，狼文化... |
| 1.000 | 2024-11-08 183336_中央加杠杆 |
| 1.000 | 2026-05-08 102927_目前AI的节点，可能集中于61，62-65。 英伟达，英特尔... |
| 1.000 | 2026-05-08 221623_为何 英特尔 如此不讲道理。你可以想想，1，制定法律... |
| 1.000 | 2026-05-11 155237_我个人的一句忠告。专栏贴，信息的金融意义。隐学与显学... |

**Keyword gap analysis:**

26 articles with model_5-related keywords but NO model_5 match. The root cause is **keyword over-generality:**

| Keyword | Matched | Not Matched | Issue |
|---------|---------|-------------|-------|
| `显学` / `隐学` | 2 | 0 | Good precision |
| `读书` / `书` | 1 | 8 | "书" too generic — matches 招股书, 书推荐 etc. |
| `历史` | 0 | 14 | "历史" mostly means "历史新高" (all-time high) not historical scholarship |
| `左` | 0 | 4 | "左" means "左侧交易" not 《左传》or political philosophy |

**Assessment:** Model 5 keyword detection is noise-prone. The distinction between "显学" (mainstream scholarship) and generic book/history mentions is not captured well. The model itself has a strong philosophical angle but keyword matching fails to detect it.

Despite only 16 matches (under the 19 threshold), model_5 has genuine philosophical content — the issue is refinement, not absence.

### 3.2 model_9_ai_reform — AI改造投资本身

**Score distribution:** 4 articles matched at scores 0.500 - 1.000

| Score | Article |
|-------|---------|
| 1.000 | 2026-06-08 224110_其实任何投资观点，一旦Ai蒸馏，任何投资的信息差都会瞬间被抹平... |
| 1.000 | 2026-06-08 230142_最近其实曝光了很多AI改造传统科技的案例... |
| 1.000 | 2026-06-08 231852_如果是AI改造投资。我发帖也就是聊聊天。核心不在我的观点... |
| 0.500 | 2026-06-15 101225_逐一分析，元件AI硬件来源于扩张投资，业绩推动为主... |

**Critical keyword gap:** 18 articles containing "AI", "人工智能", "改造", "蒸馏", or "量化" keywords that do NOT match model_9:

- These AI articles are instead classified as: 体系三要素(1.0), 竞争格局决定论(1.0), 显学大于隐学(1.0), or receive NO model match at all.
- The classification system fails to distinguish between "talking about AI as investment topic" (→ models 1, 4) vs "AI transforming the investment process itself" (→ model 9).
- Model 9 is designed for a meta-level concept: AI's impact on HOW investing is done, not WHAT to invest in.
- This meta distinction is very hard for keyword-based classification to capture.

**Assessment:** Model 9 has a **fundamental conceptual gap in the classification system**. The 4 correctly matched articles are all from June 8-15, 2026 — a very narrow window. 14+ additional articles discuss AI but are about AI as an investment theme, not AI transforming the investment process. The classifier currently cannot disambiguate.

---

## 4. Theme Distribution vs Model Coverage

### 4.1 Cross-reference matrix

| Theme | Count | Primary Model | Secondary Model | Tertiary Model |
|-------|------:|---------------|----------------|----------------|
| 观察亏钱效应 | 60 | 体系三要素(55) | 买入不败(41) | 假象认知(23) |
| 信央妈信国运 | 60 | 体系三要素(32) | 危机演绎链(17) | 竞争格局决定论(9) |
| 新登≠泡沫老登=泡沫 | 57 | 体系三要素(28) | 竞争格局决定论(21) | 假象认知(10) |
| 相信的力量 | 40 | 体系三要素(23) | 竞争格局决定论(8) | 假象认知(8) |
| 杠杆出清线 | 35 | 体系三要素(21) | 危机演绎链(10) | 竞争格局决定论(8) |
| 行情好多做 | 34 | 体系三要素(24) | 假象认知(6) | 买入不败(5) |
| 央妈以我为主 | 27 | 危机演绎链(11) | 体系三要素(10) | 竞争格局决定论(5) |
| 流动性预期≠经营 | 16 | 体系三要素(13) | 假象认知(5) | 买入不败(4) |
| 流动性挤压控制仓位 | 16 | 体系三要素(15) | 危机演绎链(2) | 择时双轨(2) |
| 把握关键节点 | 15 | 体系三要素(10) | 危机演绎链(4) | 假象认知(3) |
| 产业信念优先 | 10 | 体系三要素(8) | 买入不败(5) | 假象认知(3) |
| 空仓最高级 | 7 | 体系三要素(7) | 假象认知(4) | — |
| 减少出手次数 | 2 | 买入不败(2) | 体系三要素(2) | 假象认知(1) |
| 人多不挣钱 | 2 | 假象认知(1) | 体系三要素(1) | 买入不败(1) |
| 买入比卖出重要 | 1 | 体系三要素(1) | 买入不败(1) | — |
| 主动买亏边界 | 1 | — | — | — |

### 4.2 Self-named themes (heuristic = model name)

These themes appear in `theme_distribution` with their own name as the theme but show "NO MODEL MATCH" in cross-referencing because they describe the model's name as theme, not a heuristic label:

| Theme | Count |
|-------|------:|
| 体系三要素 | 157 |
| 假象认知 | 45 |
| 竞争格局决定论 | 41 |
| 买入不败 | 32 |
| 危机演绎链 | 32 |
| 人才+产业集群 | 18 |
| 显学大于隐学 | 15 |
| 择时双轨 | 15 |
| AI改造投资本身 | 4 |

### 4.3 Theme coverage gaps

**Themes with NO strong model association (all co-occur ≤ 3):**

| Theme | Count | Issue |
|-------|------:|-------|
| 减少出手次数 | 2 | Severely under-triggered |
| 人多不挣钱 | 2 | Severely under-triggered |
| 买入比卖出重要 | 1 | Severely under-triggered |
| 主动买亏边界 | 1 | Has ZERO model co-occurrence |

**Pattern finding:** 体系三要素 dominates EVERY theme as either primary or secondary. This model has a monopoly problem — it appears in virtually every heuristic category, diluting its specificity.

---

## 5. Heuristic Triggering Patterns

### 5.1 Frequency distribution

Heuristic triggers are highly skewed:

| Tier | Trigger Count | Heuristics |
|------|--------------:|------------|
| High (≥50) | 3 | 观察亏钱效应(60), 信央妈信国运(60), 新登≠泡沫老登=泡沫(57) |
| Medium (20-49) | 4 | 相信的力量(40), 杠杆出清线(35), 行情好多做(34), 央妈以我为主(27) |
| Low (5-19) | 5 | 流动性预期≠经营(16), 流动性挤压控制仓位(16), 把握关键节点(15), 产业信念优先(10), 空仓最高级(7) |
| Near-dead (≤2) | 4 | 减少出手次数(2), 人多不挣钱(2), 买入比卖出重要(1), 主动买亏边界(1) |

**17 heuristics total, 4 are near-dead.**

### 5.2 Unexpected model-heuristic pairings

| Heuristic | Surprising Pairing | Rationale |
|-----------|-------------------|-----------|
| 央妈以我为主 → 危机演绎链(11) | Stronger than expected | PBoC policy is framed as crisis response, not independence |
| 流动性挤压控制仓位 → 择时双轨(2) | Weaker than expected | 仓位 control should pair strongly with 择时 |
| 把握关键节点 → 假象认知(3) | Unexpected | Key nodes are about timing, not illusion |
| 主动买亏边界 → (nothing) | Total isolation | This heuristic has NO model pairings at all |

### 5.3 Global coverage issues

- **128 articles (35.3%) have ZERO model matches** — the model classifier fails on over a third of the corpus.
- **142 articles (39.1%) have ZERO heuristic matches** — the heuristic system is even more selective.
- Average models per article: 1.10 (very low — most articles get 0-1 models)
- Average heuristics per article: 1.06
- Max on any article: 3 models + 3 heuristics

**This suggests the classification system is under-matching — many articles that should belong to a model are simply not being assigned.**

---

## 6. Actionable Recommendations

### 6.1 Models needing keyword refinement

| Priority | Model | Issue | Recommendation |
|----------|-------|-------|----------------|
| **CRITICAL** | Model 9 (AI改造投资本身) | 4 matches vs 18+ AI articles | Add disambiguation layer: "AI改造投资" vs "AI作为投资主题". Keywords should target 蒸馏/量化改造/投资方法变革 not just AI. |
| **HIGH** | Model 5 (显学大于隐学) | 16 matches, too many false negatives | Refine away from generic "书/历史" keywords. Focus on explicit 显学/隐学 terminology, 读书专栏 context, and historical-philosophical reasoning patterns. "左" and "历史" should be demoted. |
| **HIGH** | Model 1 (体系三要素) | 158/363 articles = 43.5% coverage | Over-dominance. Consider tightening keyword specificity or introducing subtype distinction within model_1. Currently acts as catch-all. |
| **MEDIUM** | Model 4 (竞争格局决定论) | Claimed 51 vs actual 48 | Fix counting methodology. Ensure unique article deduplication. |
| **MEDIUM** | Model 7 (危机演绎链) | Claimed 43 vs actual 38 (-5) | Same counting fix. Also check if 5 articles are counted by heuristic but not model match. |

### 6.2 Under-triggered heuristics

| Priority | Heuristic | Current | Target | Recommended Action |
|----------|-----------|--------:|-------:|-------------------|
| **HIGH** | 减少出手次数 (h7) | 2 | 15+ | 66 articles mention "止损"/"减少交易"/"空仓" but this heuristic barely fires. Expand trigger conditions. |
| **HIGH** | 主动买亏边界 (h9) | 1 | 10+ | Almost invisible. Consider absorbing into h3 (观察亏钱效应) or expanding scope to include all disciplined-loss concepts. |
| **MEDIUM** | 人多不挣钱 (h17) | 2 | 8+ | Crowded-trade detection is underutilized. Expand to include "一致性预期"/"拥挤"/"热门" triggers. |
| **MEDIUM** | 买入比卖出重要 (h5) | 1 | 8+ | Expand to cover all "买入优先" arguments including "T+1买入逻辑"/"买点比卖点重要". |
| **LOW** | 空仓最高级 (h8) | 7 | — | Reasonable for niche concept. Keep but verify coverage. |

### 6.3 Blind spots in the 9-model framework

| Blind Spot | Severity | Description |
|------------|----------|-------------|
| **AI-as-tool vs AI-as-topic** | CRITICAL | Model 9 is conceptually valid but classification cannot distinguish between "AI改造投资方式" and "AI作为投资话题". A two-pass classifier (topic detection → meta-category assignment) is needed. |
| **Model 1 monopoly** | HIGH | 43.5% of articles assigned to 体系三要素. This model is too broad — it captures "any article about 冰冰小美's investment system" which is essentially all of them. Consider splitting into sub-models or raising matching bar. |
| **35% unmatched articles** | HIGH | Over a third of articles get NO model classification. This is the biggest weakness. Many of these are book recommendations, Q&A responses, and market commentary that don't fit neatly into the 9-model framework. |
| **Temporal clustering** | MEDIUM | Models 4, 6, 7, 8 have strong temporal concentration (May 2026). This may reflect genuine content evolution but risks creating models that only work for specific time periods. |
| **Conceptual overlap** | MEDIUM | Models 2 (假象认知) and 1 (体系三要素) overlap heavily — many articles score both at 1.0/1.0. The boundary between "system thinking" and "illusion recognition" is fuzzy. |
| **Missing heuristic for model 8** | LOW | 择时双轨 has 20 articles but only weak secondary associations with heuristics. The timing dimension may need its own dedicated heuristic. |

### 6.4 Summary of corrections needed

1. **Fix counting methodology** in `promotion_candidates` — use unique article deduplication (models 3, 4, 5, 7 affected)
2. **Add disambiguation classifier** for Model 9 (AI改造投资 itself vs AI as investment theme)
3. **Refine Model 5 keywords** — remove generic "书"/"历史"/"左", add explicit 显学/隐学 patterns
4. **Tighten Model 1** — consider requiring at least 2 co-occurring heuristics to qualify as model_1
5. **Rescue 4 near-dead heuristics** — merge or expand triggers for h5, h7, h9, h17
6. **Investigate 128 unmatched articles** — audit a sample to understand why they receive no classification
7. **Add temporal diversity requirement** to promotion criteria to avoid event-driven model promotion

---

*Analysis performed by automated script: `scripts/analyze_classification.py`*
*Keyword gap analysis: `scripts/keyword_gap.txt`*
