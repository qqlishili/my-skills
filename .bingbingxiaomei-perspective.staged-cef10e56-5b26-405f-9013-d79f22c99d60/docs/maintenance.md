# Skill 维护手册

> 最后更新：2026-06-24（关联词权重 0.2→0.05 修复后）| 关联文档：`evals/METHODOLOGY.md` / `CHANGELOG.md` / `evals/agent-prompts.md`

---

## 触发条件（任一成立 → 启动更新）

| # | 条件 | 检测方法 |
|---|------|---------|
| 1 | 新文章 ≥30 篇 | `evals/probe-*/run_probe.py` 跑 probe 扫描 |
| 2 | 30 天窗口 | 距上次 `research/` 更新 >30 天 |
| 3 | 关键事件 | 央行重大政策 / 中米关系转折 / 新模型候选出现 / 主题显著衰减 |
| 4 | 评估分数下降 | Darwin 9 维总分较上一版本跌 >2 分 |

**当前状态**（2026-06-24）：条件 1 ✅ 已处理 — probe 6/13-22 扫描到 58 篇新文章，R5 增量已落 `0ef1332`/`f9f379e`，research/ 6 文件全量更新。下次触发窗口：扫描 6/23 之后的新文章。

---

## 7 步更新流程

### Step 1: Probe 扫描（30 min）

```
1. 在 evals/probe-YYYY-MM-DD_to_YYYY-MM-DD/ 新建目录
2. 复制 run_probe.py 模板（从上一轮 probe 目录）
3. 修改时间窗口参数（START_DATE / END_DATE）
4. 跑 python run_probe.py
5. 输出：probe-freq.txt / probe-keyword.txt / probe-themes.txt
```

**输入**：外部 vault `D:\Temp\karpathy-llm-wiki-vault\raw\02-投资\01-xueqiu\冰冰小美/` 的新文章
**输出**：3 个 probe 文件 + 文章列表

### Step 2: 跨域复现核对（30 min）

对新出现的主题概念（如"流动性挤压""新登老登"），核对其在 ≥3 个独立板块的出现次数。
**判断规则**：
- 翻倍 + ≥3 板块 → 晋升新模型候选
- ≥3 板块 + 边界清晰 + 不重复 → 晋升新启发式候选
- 不满足 → 注入到现有模型的特化段落

### Step 3: Research 增量 — 3 路 Agent 并行（2-3h）

复用 `evals/agent-prompts.md`（10631 字节）中的 Agent 提示词模板。

| Agent | 目标文件 | 工作内容 |
|-------|---------|---------|
| Agent 1 | `references/research/01-writings.md` | 著作与系统思考——识别新主题、框架延伸、概念更新 |
| Agent 5 | `references/research/05-decisions.md` | 决策记录——识别新交易案例、纠错链路、决策理由 |
| Agent 6 | `references/research/06-timeline.md` | 时间线——追加新事件、更新最新动态 |

**Agent 2-4**（conversations / expression-dna / external-views）：当新文章 ≥50 篇或 stale >60 天时做。

**输入**：probe 扫描出的文章列表（≤100 篇时全量，>100 篇时抽样 60 篇覆盖时间窗口）
**输出**：追加到各 research 文件末尾（不覆盖已有内容），标注 `> 来源：[probe 窗口]` 引用

### Step 4: SKILL.md 更新（1-2h）

基于 research 增量，更新：
- 模型证据段（如有新证据）
- 2026 特化段落（如有新内容）
- 决策启发式（如有新启发式）
- 时间线和最新动态
- 诚实边界（如数据窗口有变）
- CHANGELOG 追加热身

**规则**：改动后 `wc -l SKILL.md` 不超过原 150%（当前 768 × 1.5 = 1152）。

### Step 5: Test-prompts 增量（30 min）

对新增/修改的模型或启发式，追加 1-3 条 test case。
**格式**：`{"id": N, "prompt": "...", "expected": "..."}`

### Step 6: Full_test + Darwin 评估（1-2h）

1. 用 `SKILL.core.md`（240 行）作为 agent prompt 注入
2. 回归跑全部 20 case + 新 case
3. 存档 agent 输出到 `evals/full_test_outputs/vN-case-*.txt`
4. Darwin v2.0 评分 9 维
5. 写入 `evals/0N-post-rN.json` → **写前先查 `evals/METHODOLOGY.md` "Eval 自检清单"**（防 R1/v1.5 同源错误：跳过存档直接写 JSON）
6. 更新 `results.tsv`

### Step 7: 落盘 + CHANGELOG（30 min）

```
git add -A bingbingxiaomei-perspective/
git commit -m "vN+1: [改动摘要]"
```
更新 `CHANGELOG.md` 追加版本条目。

---

## 决策规则

### 新模型晋升
```
翻倍（≥4 → ≥8 篇）+ 跨域 ≥3 独立板块 → 晋升
不满足 → 注入到现有模型的特化段落
```

### 新启发式晋升
```
跨域 ≥3 板块 + 边界清晰 + 不与现有启发式重复 → 晋升
不满足 → 观察中候选
```

### 观察中候选管理
在 SKILL.md 末尾维护"观察中候选"section，标注：
- 主题名称 + 当前频次 + 跨域板块数 + 晋升条件

### 模型/启发式过期
```
当某个启发式的"前提条件"中标注的外部事件发生时（如"假设 AI 革命持续"→ AI 泡沫破灭），
立即标注过期并回退到基础三要素。
```

---

## 复用资源

| 资源 | 路径 | 用途 |
|------|------|------|
| Agent 提示词 | `evals/agent-prompts.md` | 3 路 Agent 并行 research |
| Probe 模板 | `evals/probe-*/run_probe.py` | 新文章频率/关键词扫描 |
| 评估方法学 | `evals/METHODOLOGY.md` | Darwin 评分标准 + 分数解读 |
| 变更日志 | `CHANGELOG.md` | 版本记录 + 评估快照 |
| 测试用例 | `test-prompts.json` | full_test 回归 |
| Core 提示词 | `SKILL.core.md` | agent prompt 注入 |

---

## 限制

- **不上 GitHub** — 无 CI/CD 自动化
- **不做本地 cron** — 手动触发，不做 Windows Task Scheduler
- **数据更新靠人工** — articles/ 依赖外部 vault `D:\Temp\karpathy-llm-wiki-vault`
- **no blind baseline per update** — 仅重大版本（v2.0）做完整 blind baseline；小版本（v1.N）只跑 agent_spawn

---

## 当前待执行

| 项 | 紧迫度 | 关联 |
|----|--------|------|
| Stage 2: R5 补做（6/13-22 + 2025）| ✅ 已完成 | commit `0ef1332`/`f9f379e`，research/ 6 文件 +1,465 行 |
| Stage 3: scripts/classify-articles.py | ✅ 已完成 | commit `29ffc0f`，411 行 + 363 篇全量分类 |
| Stage 4: 模型 1 关联词权重调优 | ✅ 已完成 | commit `3410b9b`，0.2→0.05，命中率 34.4%→23.7% 落入目标区间 |
| 下次：扫描 6/23 之后新文章 | 🟢 监控 | 触发条件 1（新文章 ≥30）|
