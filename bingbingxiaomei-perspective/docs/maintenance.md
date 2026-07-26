# 冰冰小美 Skill 维护指南

## 当前基线

- `references/sources/articles/` 是真实目录，包含 520 篇雪球专栏语料。
- 2025 年本地有 68 篇；当前年份分布为 2023/2024/2025/2026 = 70/35/68/347。
- 本地 corpus 不含作者全部日常发言和非专栏内容，因此不覆盖作者全部公开表达。
- `references/taxonomy.json` 是模型、启发式 ID 和状态的唯一机器可读真相源。
- 当前分类入口是 `scripts/classification_output/current.json`。
- 新文章解读默认 `input_mode=ephemeral`，不进入 corpus，也不触发 taxonomy 重建。

## 触发条件

以下任一条件成立时，进入正式 corpus 更新流程：

1. 经用户确认新增作者专栏原文；
2. 现有文章正文、来源身份或角色分段发生纠正；
3. corpus digest 与 taxonomy、角色清单或当前分类产物不一致；
4. 新证据可能导致当前模型或启发式合并、拆分、退役或改变状态；
5. 当前分类、测试或 MCP 索引无法覆盖 canonical corpus。

用户临时粘贴的新文章不属于以上条件，除非另行明确授权持久化。

## 更新流程

### 1. 固化语料快照

- 只读扫描 canonical articles 目录；
- 记录文章数、稳定路径 manifest、逐文件 SHA-256 和 corpus digest；
- 禁止删除、移动、批量覆盖原文。

### 2. 内容角色分段

- 对每篇文章生成无重叠 segment；
- 角色只允许 `author_post`、`author_reply`、`third_party_comment`、`secondary_analysis`、`unknown`；
- 只有前两类获得 `author_primary` 资格；
- override 必须有人工复核理由。

### 3. 全量重读与 taxonomy 审查

- 模型数量和启发式数量只能由全量重读后的证据决定，不预设数量；
- 每个模型须有支持证据、反例和失效边界；
- 每条启发式须有支持证据、反例/失效边界、适用场景和禁用条件；
- 旧 ID 必须显式映射为保留、合并、拆分或退役；
- 用户通过 Gate 后才能更新 taxonomy。

### 4. 同步派生产物

按以下顺序同步：

1. `references/models/` 与 `references/heuristics/catalog.md`；
2. research 差异文件；
3. `scripts/classify-articles.py` 与 `scripts/analyze_classification.py`；
4. 520 篇当前分类产物、人工审查和 current 指针；
5. `SKILL.md`、`SKILL.core.md`、模板、Schema 和 `test-prompts.json`；
6. codebase-memory、graphify 和 codegraph 索引。

不得手改 graphify 生成图；必须由工具重新生成。

### 5. 验证

- taxonomy、模型文档、启发式 catalog、Skill、Schema 和测试中的当前 ID 集合一致；
- 520 篇角色覆盖完整，无重叠、无未解释正文；
- 当前分类覆盖 520 篇，未决状态显式保留；
- current 指针 SHA 与不可变 artifact 一致；
- MCP 能召回作者原文，但候选结论必须回读 `author_primary`；
- 所有相关单元测试、集成测试和 `git diff --check` 通过。

## 新文章解读维护

权威文件：

- Schema：`references/schemas/article-interpretation.schema.json`；
- 跨对象语义校验：`scripts/validate_article_interpretation.py`；
- 模板：`references/templates/article-interpretation.md`；
- 入口：`SKILL.md` 和 `SKILL.core.md`；
- 回归：`tests/test_article_interpretation_contract.py` 与 `test-prompts.json`。

维护时必须保持：

- 输入默认一次性，不自动改变 corpus；
- 二次解读默认归为分析者推断；
- 历史关系枚举封闭；
- 非 `no_evidence` 关系必须回到作者一级原文；
- 每个 Claim 必须与一个历史关系结果绑定，且通过 Schema 与跨对象语义校验；
- 文章解释简报和股票报告按用户意图分流；
- 历史未命中只表示当前 520 篇语料内无证据。

## 当前 taxonomy

模型：`m01`、`m02`、`m03`、`m04`、`m05`、`m06`。

启发式：`h01`、`h02`、`h03`、`h04`、`h05`、`h06`、`h07`、`h08`、`h09`。

不要在维护文档复制完整定义；定义、状态、证据与映射统一从 taxonomy 读取。

## 回退规则

- 原文不回退、不覆盖；
- 旧分类和历史 eval 保留为 legacy baseline；
- 新 taxonomy 或 current 未通过 Gate 时，默认入口继续指向上一个已验证版本；
- 索引失败时如实记录 fail/deferred，不把候选索引状态写成 pass；
- 任何持久化、Git 提交或外部发布都需要当轮明确授权。
