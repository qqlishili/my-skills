# 文章解释简报模板

## 路由

- 默认输入为 `input_mode=ephemeral`，只在本次回答中使用，不写入 520 篇 corpus，也不改变 corpus digest。
- 文章解读与股票报告路由互斥。用户只要求理解文章时使用本模板；只有用户明确要求个股、估值、仓位或投资决策时，才切换到股票报告模板。
- 输出遵循 `references/schemas/article-interpretation.schema.json`，并通过 `scripts/validate_article_interpretation.py` 的跨对象语义校验。

## 执行顺序

1. 判定 `document_type`：作者原文 `primary_article`、二次解读 `secondary_analysis`、混合文本 `mixed` 或 `unknown`。
2. 按行生成稳定 `input_segments`，角色只用 `quoted_source`、`analyst_text`、`external_context`、`unknown`。
3. 提取最小可验证 Claim。每个 Claim 与一个历史关系结果绑定为 `claim_result`；用户的总结、推演和解释默认是 `analyst_inference`。只有可直接定位且明确归属于作者的引文才是 `author_quote`；`author_judgement` 只用于当前输入本身是作者原文且判断可直接定位的情况。
4. 对每个 Claim 先查历史 `author_primary` 精确短语，再做词法召回；gbrain 仅提供 `semantic_candidate`，graphify 仅提供 `graph_candidate`。
5. 对每个候选回读 `references/sources/articles/` 原文及角色清单。只有 `author_post` 或 `author_reply` 且 `evidence_eligibility=author_primary` 的行段可以支持历史关系。
6. 所有非 `no_evidence` 关系必须记录原文路径、segment、行号、短引，并满足 `verified_against_primary_text=true`。找不到一级证据时输出 `no_evidence`。
7. 映射当前 taxonomy：模型只允许 `m01`-`m06`，启发式只允许 `h01`-`h09`。若 taxonomy 尚未通过 G2，映射状态写 `unavailable_before_G2`，不得沿用历史数量。

## 禁止作为作者一级证据

- `third_party_comment`
- `secondary_analysis`
- `research summary as evidence`
- `graph edge as evidence`

这些内容可以帮助召回候选，但不能替代原作者正文。外部事实也必须与作者观点分开标注。

## 固定输出

### 输入摘要

- 标题：
- 文档类型：
- 一次性输入边界：

### 输入分段

| segment_id | 行段 | 角色 | 摘要 |
|---|---:|---|---|

### Claim 与历史关系（逐项一对一）

| claim_id | segment_id/角色 | Claim 类型 | 标准化概念与陈述 | 历史关系 | 历史文章与行段 | 一级原文已核验 | 理由/置信度 |
|---|---|---|---|---|---|---|---|

关系只允许：`repeats`、`extends`、`narrows`、`revises`、`contradicts`、`applies`、`no_evidence`。

### Taxonomy 映射

- 模型：
- 启发式：
- 映射理由：

### 支持证据

- 仅列 `author_primary` 原文。

### 冲突或反证

- 列出与 Claim 不一致、收窄或修订它的作者原文；没有则写“未发现”。

### 未知项

- 列出作者身份不明、来源缺失、时间不明或无法核验的内容。

### 诚实边界

- 520 篇雪球专栏语料不覆盖作者全部公开表达。
- 新文章默认不进入 corpus；历史未命中不等于作者从未表达，只能输出当前语料内 `no_evidence`。
