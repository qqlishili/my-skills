# 冰冰小美 · 标准版个股分析报告模板

> **定位**：普通个股问题的默认输出格式。8 步精简，数据源以 westock + neodata 为主。
> **触发条件**：默认。用户要求"深度分析"时切换至 [deep-stock-report.md](./deep-stock-report.md)。
> **核心原则**：先分流（用哪副镜片看），再八步框架。不分流 = 退回通用财务报告。

---

## 报告元信息

| 字段 | 内容 |
|---|---|
| 标的名称 | {{股票名称}} |
| 股票代码 | {{sh600519 / sz000001 / hk00700 / usAAPL}} |
| 报告日期 | {{YYYY-MM-DD}} |

---

## 0. 研究足迹（强制开头，单行 ≤60 字）

> 小美我看了→{{搜索关键词/来源概括}}

- [ ] 已输出研究足迹行
- [ ] 内容非空

---

## 0.5 运行模型分流（强制，报告开头先判断"用哪副镜片看"）

> F 个股分析如果不先分流，会退回通用财务报告。冰冰小美 skill 的核心不是财务模板，而是先判断"这只股应该用哪副镜片看"。

### 分流表

| 分流问题 | 命中运行模型 |
|---|---|
| 是 AI 算力、材料、封装、液冷、电力、国产替代吗？ | **AI 基建材料端**（运行模型 6） |
| 是白酒、地产、银行、保险、旧消费吗？ | **旧红利退出**（运行模型 7） |
| 是国家战略、产业政策、国产替代、出海竞争吗？ | **国家-金融-产业**（运行模型 3） |
| 是宏观冲击、美元、美债、石油、地缘风险吗？ | **危机演绎链**（运行模型 4） |
| 是公告、小作文、题材传播、市场吹票吗？ | **信息金融意义 / 显学隐学**（运行模型 5） |
| 都不是 | 回到 **体系三要素**（运行模型 1） |

### 分流输出（1-2 句）

> 运行模型：{{命中模型}} + 体系三要素。理由：{{一句话说明为什么用这副镜片}}。

- [ ] 已完成分流表判断
- [ ] 已输出运行模型 + 理由（1-2 句）

---

## 1. 公司概况

- [ ] 主营业务：{{填写}}（`[W]` `profile <code>` / `[N]` neodata `"<公司>主营业务"`）
- [ ] 收入构成：{{填写}}（`[N]` neodata `"<公司>主营业务收入构成"` → 收入构成百分比）
- [ ] 细分赛道/产业链位置：{{填写}}（`[W]` `profile <code>` → industry/sector）

---

## 2. 核心投资逻辑

- [ ] 逻辑类型：{{成长驱动/周期反转/价值修复/事件催化/产业趋势/竞争格局改善}}（只抓最核心一条）
- [ ] 时代主线一致性：{{是否符合国家战略方向}}

---

## 3. 行业与竞争格局

### 三要素扫描

- [ ] **竞争格局比较优势**：{{国家战略/中美关系/产业政策}}
- [ ] **流动性辩证分析**：{{央妈动作 + 水流方向}}（`[W]` `macro indicator cn_core --date <今天>` + `market-overview --type all`）
- [ ] **情绪位置变化**：{{冰点/犹豫/共识/极度贪婪/退潮}}（`[W]` `market-overview --type updown` + `changedist`）

> 模型 1：三者共振=阻力最小。一项不利=轻仓，两项不利=空仓。

---

## 4. 财务质量

- [ ] 近 4 期三大报表：{{填写}}（`[W]` `finance <code> --num 4`）
  - 营收/净利润增速：`consensus` 的 revenueYoy/netProfitYoy
  - 毛利率/净利率/ROE：`finance` 返回绝对值，**需自行计算比率**
  - **自由现金流**：`finance` 返回 `FCFF`/`FCFE` **直接字段**
  - **研发费用**：`finance` 返回 `RAndD` **直接字段**
- [ ] 财务与叙事匹配度：{{匹配/部分匹配/不匹配}}

> 行业对标可用 `sector finance <pt代码>` → 返回 roeTTM/grossProfitRatioTTM 等**直接比率**

---

## 5. 市场预期

- [ ] 机构一致预期：{{填写}}（`[W]` `consensus <code>` → EPS/PE/PB/PS/目标价/机构数）
- [ ] 市场在交易什么预期：{{业绩超预期/新产品放量/景气反转/估值切换/政策驱动/情绪催化}}
- [ ] 研报观点：{{填写}}（`[W]` `report list <code> --limit 5` → 研报标题+评级）

---

## 6. 估值与位置

- [ ] PE/PB/PS + 目标价：{{填写}}（`[W]` `consensus <code>`）
- [ ] 行业估值百分位：{{填写}}（`[W]` `sector valuation <pt代码>` → PeTTMPct/PbLFPct）
- [ ] 同业评分对比：{{填写}}（`[W]` `score <code1>,<code2>,<code3>` → 综合/资金/基本面/风险/技术评分）

---

## 7. 风险分析

### 分层风险

- [ ] 短期（1-3月）：{{情绪/预期差/交易拥挤}} + 资金评分/技术评分趋势（`[W]` `score <code>` → 周内显著下跌=派发硬信号）
- [ ] 中期（3-12月）：{{需求/竞争/产能}}
- [ ] 长期（1年+）：{{商业模式/政策/技术替代}}

### 风险事件扫描

- [ ] `[W]` `risk <code> --types st,pledge,unlock,lawsuit,executivetransfer,leaderchange` → ST/质押/解禁/诉讼/高管增减持/高管变动

---

## 8. 投资结论

- [ ] 结论：{{买入/卖出/持有/观察}} + 合理估值区间
- [ ] 至少 2 条前提条件（每条以「如果 XX，则判断可能不成立」开头）：
  1. 如果 {{XX}}，则判断可能不成立
  2. 如果 {{XX}}，则判断可能不成立
- [ ] 反向三问（模型 3）：
  1. 最大亏钱风险在哪里？
  2. 当前主要亏钱效应在哪个方向？
  3. 判断错了亏多少能出来？

---

## 数据源调用命令速查

### westock-data（`[W]`，结构化数据主源）

```bash
npx -y westock-data-skillhub@latest search <关键词>                    # 股票搜索
npx -y westock-data-skillhub@latest profile <code>                     # 公司概况
npx -y westock-data-skillhub@latest finance <code> --num 4             # 三大报表
npx -y westock-data-skillhub@latest consensus <code>                   # 机构一致预期
npx -y westock-data-skillhub@latest score <code>,<code2>,<code3>       # 量化评分（批量）
npx -y westock-data-skillhub@latest shareholder <code>                 # 十大股东+变动
npx -y westock-data-skillhub@latest risk <code> --types st,pledge,unlock,lawsuit,executivetransfer,leaderchange
npx -y westock-data-skillhub@latest fund flow <code>                   # 资金流向
npx -y westock-data-skillhub@latest fund north-holding <code>          # 北向季度持仓
npx -y westock-data-skillhub@latest market-overview --type all         # 市场总览
npx -y westock-data-skillhub@latest changedist                         # 涨跌分布
npx -y westock-data-skillhub@latest macro indicator cn_core --date <今天>  # 核心宏观
npx -y westock-data-skillhub@latest sector valuation <pt代码>          # 行业估值百分位
npx -y westock-data-skillhub@latest sector finance <pt代码>            # 行业财务（直接比率）
npx -y westock-data-skillhub@latest sector forecast <pt代码>           # 行业盈利预测
npx -y westock-data-skillhub@latest report list <code> --limit 5       # 研报列表
npx -y westock-data-skillhub@latest buyback <code>                    # 回购数据
npx -y westock-data-skillhub@latest kline <code> --period day --limit 60  # K线
npx -y westock-data-skillhub@latest technical <code> --indicator macd  # 技术指标
npx -y westock-data-skillhub@latest chip <code>                       # 筹码分布
```

### neodata（`[N]`，自然语言搜索，需鉴权）

```bash
# 需先 connect_cloud_service 获取 token
python -X utf8 "<neodata路径>/query.py" --query "<公司>主营业务收入构成" --token "<token>"
```

### 元宝搜索（`[Y]`，国内财经媒体，需 .env 配置）

```bash
set -a && . ~/.workbuddy/.env && set +a && \
python -X utf8 ~/.workbuddy/skills/tencent-yuanbao-standard-search/scripts/websearch.py \
  --query="查询内容" --freshness=week
```

### Tavily（`[T]`，投资研究+PDF提取，需 .env 配置）

```bash
# 搜索（含AI Answer）
set -a && . ~/.workbuddy/.env && set +a && \
python -X utf8 ~/.workbuddy/skills/workbuddy-tavily/scripts/tavily.py \
  search --query="查询内容" --max-results 5 --include-answer basic

# PDF内容提取（技术团队/产业集群获取方式）
python -X utf8 ~/.workbuddy/skills/tavily-search-pro/lib/tavily_search.py \
  extract "<PDF_URL>" --query "高管 技术团队 履历 背景" --format markdown

# 财经搜索（地缘动态获取方式）
python -X utf8 ~/.workbuddy/skills/workbuddy-tavily/scripts/tavily.py \
  search --query="查询内容" --topic finance --include-answer basic --time-range month
```

### WebSearch（`[S]`，内置工具，兜底）

```
直接调用，无需配置
```

---

## 使用说明

1. **默认使用标准版**：普通个股问题按本模板 8 步输出
2. **深度分析时切换**：用户要求"深度个股分析"时，按 [deep-stock-report.md](./deep-stock-report.md) 输出
3. **运行模型分流强制**：第 0.5 节必须在八步框架之前完成——先判断"用哪副镜片看"
4. **数据源优先级**：`[N]` neodata > `[W]` westock > `[Y]` 元宝搜索 > `[T]` tavily > `[S]` WebSearch
5. **研究足迹强制**：第 0 节必须在动笔前完成
6. **投资结论前提条件**：至少 2 条

---

*模板版本：v1.0（标准版）*
*基于：冰冰小美 F.看个股逻辑八步框架 + 7运行模型 + 17启发式*
*数据源：neodata + westock-data + 元宝搜索 + tavily + WebSearch*
*生成日期：2026-07-07*
