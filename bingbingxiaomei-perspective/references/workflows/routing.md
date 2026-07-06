# 研究路由与数据工具

> v1.8 compact 参考文件。涉及具体公司、行业、宏观、市场现状时读取本文件。

## 问题分类

| 类型 | 特征 | 行动 |
|---|---|---|
| 纯框架 | 抽象价值观、交易理念、方法论 | 不查数据，直接用模型回答 |
| 个股 | 具体股票、公司、公告、财报 | 跑个股 8 步框架 |
| 行业/板块 | 半导体、白酒、氟化工、有色、AI等 | 查政策、景气、供需、竞争格局 |
| 宏观/政策 | 央妈、利率、汇率、地缘、财政、美联储 | 查最新政策与市场变量 |
| 信息判断 | 新闻、研报、小作文、媒体、公告 | 用模型 10 + h18 分层 |
| 混合 | 案例 + 抽象道理 | 先补事实，再用框架 |

问题范围模糊时先回问：市场、时间、标的、问题目标四者至少明确三项。

## 研究维度

| 维度 | 看什么 |
|---|---|
| A 竞争格局 | 国家战略、产业政策、中美关系、行业供需、格局变化 |
| B 流动性 | 央妈、美联储、社融、M1/M2、ETF资金、北向、基金发行赎回 |
| C 情绪位置 | 挣钱/亏钱效应、成交、涨跌比、连板、炸板、传播阶段 |
| D 风险节点 | 会议、数据、财报、交割、强平、监管、流动性踩踏 |
| E 底层实质 | 人才、产业集群、研发、自由现金流、技术壁垒 |
| F 个股逻辑 | 主营、核心逻辑、财务、预期、估值、风险、结论 |

## westock-data 快速命令

`westock-data` 不是全局命令。统一用：

```bash
npx -y westock-data-skillhub@latest <子命令>
```

新会话先探测：

```bash
npx -y westock-data-skillhub@latest search 长电
```

常用命令：

```bash
npx -y westock-data-skillhub@latest search <关键词>
npx -y westock-data-skillhub@latest search <关键词> --type sector
npx -y westock-data-skillhub@latest kline <code> --period day --limit 20
npx -y westock-data-skillhub@latest technical <code> --indicator macd
npx -y westock-data-skillhub@latest chip <code>
npx -y westock-data-skillhub@latest consensus <code>
npx -y westock-data-skillhub@latest score <code>
npx -y westock-data-skillhub@latest finance <code> --num 4
npx -y westock-data-skillhub@latest fund flow <code>
npx -y westock-data-skillhub@latest market-overview
npx -y westock-data-skillhub@latest profile <code>
npx -y westock-data-skillhub@latest etf detail sh510300
npx -y westock-data-skillhub@latest macro indicator cn_core --date <日期>
npx -y westock-data-skillhub@latest disclosure <code>
npx -y westock-data-skillhub@latest notice list <code> --type 1
```

代码格式：沪市 `sh600519`，深市 `sz000001`，港股 `hk00700`，美股 `usAAPL`。

## 个股 8 步框架

1. 公司概况：主营、收入利润来源、产业链位置；优先 `profile`。
2. 核心投资逻辑：成长、周期、价值、事件、趋势、格局改善，只抓一条主线。
3. 行业与竞争格局：景气、供需、公司地位；用 `search --type sector` 辅助。
4. 财务质量：收入利润、毛利率、现金流、ROE、费用率、存货应收；用 `finance --num 4`。
5. 市场预期：业绩、产品、政策、情绪；结合 `kline` 和 `consensus`。
6. 估值匹配：成长看 PE/PEG/PS，价值看 PE/PB/股息，周期看 PB 和中枢。
7. 风险分层：短期情绪/拥挤，中期需求/竞争/产能，长期模式/政策/技术；用 `score` 看资金和技术恶化。
8. 投资结论：买入/卖出/持有只能作为框架判断，不构成建议；列至少 2 条「如果 XX，则判断不成立」。

同业对比必须批量查询，例如：

```bash
npx -y westock-data-skillhub@latest consensus sh600584,sz002156,sz002185
```

## 研究足迹

具体事实型回答必须先输出一行：

`小美我看了→[搜索关键词/来源概括]`

没有实际查询或来源时，不得输出具体判断。可以改为：「小美我数据没拉到，只能先讲框架。」

## 失败处理

| 失败 | 处理 |
|---|---|
| npx 首次下载超时 | 重试 1 次；仍失败则用公开搜索兜底 |
| 命令空数据/限流 | 重试 1 次；标注数据源失败 |
| kline 被当实时行情 | 必须标注数据日期，不称现价 |
| 多源冲突 | 标注来源分歧，优先公告/近 30 日研报 |
| neodata 无鉴权 | 跳过，直接 westock-data |
| 所有工具不可用 | 只给框架，不做具体结论 |

更完整命令说明见 `references/tools/finance-data/skills/westock-data/SKILL.md`。
