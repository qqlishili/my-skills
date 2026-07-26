# Darwin 评估方法学说明

> 创建时间：2026-06-12 | 适用范围：bingbingxiaomei-perspective skill 全部 Darwin 评估

## 当前 taxonomy 分类评估边界

自 `references/taxonomy.json` 成为当前唯一 taxonomy 后，`01-baseline-pre-improvement.json` 至 `09-promotion-deep-analysis.md` 及 `scripts/classification_output/` 中旧 schema JSON 均为 **legacy baseline**。它们保留原文和原始统计，不回写当前模型 ID，也不与当前分类准确率直接比较。

当前分类评估只使用：

- `scripts/classification_output/current.json` 指向的不可变 schema v2 产物；
- `evals/current-classification-review-2026-07-26.json` 的可复算待审查队列；
- `evals/current-classification-manual-review-2026-07-26.json` 的人工原文复核结论。
- `evals/review-batches/task9-unresolved-batch-01.json` 至 `-06.json` 的 334 篇逐篇原文复核结论；
- `evals/current-classification-review-status-2026-07-26.json` 的当前完成度与 Gate 状态。

分类器输出是候选路由，不是语义真值。`unresolved=true` 或置信度低于 `0.65` 的文章必须进入待审查队列；每个已解析模型另取至少 4 篇。队列中的 `pending` 只表示尚未人工复核，不能被计作通过。人工复核必须回读原文，并分别判断主模型和启发式候选。

2026-07-26 首次当前 taxonomy 运行结果为 520 篇、334 篇 unresolved；队列共 358 篇。首批每模型 4 篇、共 24 篇人工复核得到 20 篇主模型正确、3 篇错误、1 篇有歧义。其余 334 篇已按稳定排序拆成 6 个批次并逐篇回读原文：107 篇获得主模型，227 篇保留未决。独立复核另发现 3 组过度归类模式，将其中 28 篇保守降回未决；加上首批样本中的 1 篇歧义条目，正式裁决产物最终保留 228 篇 unresolved。这里的 unresolved 是显式诚实边界，不是待审查遗漏；358/358 条队列均已复核，任务 9 的数据前提已完成。

正式当前产物由 `current.json` 指向 `classification-adjudicated-*` 不可变文件；文件名使用微秒时间戳并以排他创建写入，已存在路径不得覆盖。裁决器只接受 raw 分类产物，禁止对已裁决产物再次覆盖，以免污染 `classifier_*` 原始值。`corpus_digest` 必须由本次实际加载的同一批文章字节计算；只有与 taxonomy 的 canonical digest 相等时才允许更新 current 指针。默认正式 current 还必须使用项目内 canonical taxonomy 与 articles 路径，自定义输入只能写入非默认输出目录。

## 评估器版本

| 版本 | 关联文件 | 评分尺度 | 备注 |
|------|----------|----------|------|
| v1 | `01-baseline-pre-improvement.json` / `02-post-p0.json` / `03-post-full.json` | 9 维度评分，总分 0-90 | 与 v2 不可直接对比 |
| v2 | `04-post-r2.json` / `05-post-r3.json` / `06-post-r4.json` | 9 维度评分（严格模式），100 分制 | 总分尺度与 v1 不同 |

## eval_mode

| 模式 | 含义 | 首次出现 |
|------|------|----------|
| `dry_run` | 打分基于 AI 对自身改动的**预期效果估计**，未 spawn agent 做真实测试 | v1.0–v1.2 |
| **`agent_spawn`** | spawn **独立子 agent** 实际跑 test-prompts，原始输出存档于 `full_test_outputs/`。**若缺少 blind baseline 对比（未同时 spawn 无 skill 的对照 agent），仍不视为完整 full_test。** | v1.3 (5 case), **v1.4 (9 case)** |

v1.3–v1.4 的 `agent_spawn` vs v1.0–v1.2 的 `dry_run` 是评估方法学的本质升级：
- `dry_run` = 自己评自己 → 乐观偏差
- `agent_spawn` = 独立 agent 跑测试 → 真实行为验证

**仍缺 blind baseline**：v1.4 未 spawn 无 skill 的对照 agent 跑同一 prompt → 按 METHODOLOGY 严格定义，dim8 的 `agent_spawn` 不等于 `full_test`。未来应补 blind baseline 对比。

## 分数解读

| 迭代 | 评估器 | 总分 | Δ | eval_mode | 是否可比 |
|------|--------|------|---|-----------|----------|
| v1.0 baseline | v1 | 81.3 | — | dry_run | 起点 |
| v1.0 + P0 | v1 | 83.5 | +2.2 | dry_run | v1 内部有效 |
| v1.1 (P0+P1+P2) | v1 | 85.2 | +3.9 | dry_run | v1 内部有效 |
| v1.1 baseline (R2) | v2 | 80.4 | — | dry_run | **与 v1.0–v1.1 不可比** |
| v1.2 (R2 dim3 fallback) | v2 | 82.0 | +1.6 | dry_run | v2 内部有效 |
| v1.3 (模型9+启发式14-17) | v2 | 77.4 | — | agent_spawn (5 case) | v2 内部有效 |
| **v1.4 (容错+清晰度双维)** | v2 | **79.2** | **+1.8** | **agent_spawn (9 case)** | **v2 内部有效** |

**v1.4 ratchet check**: v1.4 79.2 > v1.3 77.4 → ✅ 通过（v2 rubric 首次可比 ratchet pass）

**绝对分不可比**：v1.1 绝对分 85.2（v1 尺度）≠ v1.4 绝对分 79.2（v2 尺度）。两套评估器的内部校验规则不同。

## 已知评估器偏差

- v1 评估器对**结构/形式**敏感（表格化、分层、CHECKPOINT 视觉锚收益高）
- v2 评估器对**失败模式覆盖**敏感（fallback 表格收益高）
- 两套都**无法**测出实际运行效果——必须用真实跑分（test-prompts.json）补充

## 真实跑分建议

未来版本升级时，建议：

1. 至少 6 条 test-prompts.json 全量回归
2. 至少 3 条边缘测试（如角色退出、沉默规则、研究足迹空、工具完全失败、个股 8 步框架）
3. 至少 1 次盲测（人类评估者不知版本，对比 v1.0 vs v1.2 输出）
4. 任何新加入的模型/启发式必须有原文引用 + 决策链路（参考 `research/05-decisions.md` 格式）

## 限制声明

- Darwin 评估是**单点评分**，未做时间序列分析
- 没有跨 skill 对照组（仅 skill 内迭代对比）
- 没有"未改动版本"的 baseline 重复测量（v1.0 baseline 只跑了一次）
- 评估者本身（darwin-v1 / darwin-v2 脚本）未公开算法细节——属于黑盒评估
- **v1.4 agent spawn prompt 精简效应**：回归 case 12-14 得分从 v1.3 的 9→8，是 agent prompt 使用精简版（~200行）而非完整 SKILL.md 所致，核心行为全部正确。未来若补 blind baseline 应统一 prompt 注入方式

## v1.4 评估细节

| 项 | 值 |
|---|---|
| 评估文件 | `06-post-r4.json` |
| 总分 | 79.2/100 |
| 评估器 | Darwin v2.0 strict |
| eval_mode | agent_spawn |
| agent 数 | 9（5 回归 + 4 新增） |
| test-prompts 覆盖 | 20 case（case 1-20） |
| 回归 case 平均 | 8.6（case 12-14 微降为精简 prompt 效应） |
| 新增 case 平均 | 9.5（case 17-20 全部通过） |
| dim5 改善 | 6→7（M1 沉默规则改写 + M2 路由决策树） |
| dim3 改善 | 7→7.5（3.1 认知失败表 + 3.2 漂移检测 + 3.3 双表统一） |
| ratchet | ✅ 通过（v1.4 79.2 > v1.3 77.4） |

---

## Eval 自检清单（防步骤遗漏）

> 根因：R1 初版和 v1.5 初版两次重演同一错误——评分完直接写 JSON，跳过"先存档 agent 原始输出"步骤。

每次写完 `evals/0N-post-rN.json` **前**，对照本清单：

- [ ] agent 输出已存档到 `full_test_outputs/vN-case-N-*-agent-XXXX.txt`
- [ ] `0N-post-rN.json` 每个 case 含 `output_file` 字段
- [ ] `agent_id` 与 `output_file` 文件名一致（如 `agent-488811b5` → `...agent-488811b5.txt`）

*修复成本：无代码，纯清单审查。流程：agent 返回 → 存档 txt → 写 JSON（含 output_file）→ commit。*
