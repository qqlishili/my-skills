# 冰冰小美 · 个股结构化分析报告模板 v3.0

> **v3.0 更新**：基于 7 轮实测验证后重构。数据源从三源扩展为五源。
> - v1.0→v2.0：新增 neodata 数据源 + 修正 changedist/executivetransfer 错误
> - v2.0→v3.0：新增元宝搜索 + tavily（search/extract/finance/research）+ 双搜交叉验证策略
>
> **五源数据优先级**：`[N]`neodata > `[W]`westock > `[Y]`元宝搜索 > `[T]`tavily > `[S]`WebSearch
>
> **核心改进**：3 项候补数据（技术团队/产业集群/地缘动态）从"需 WebSearch 候补"升级为"tavily extract PDF 研报 + 元宝搜索官网"最优路径。

---

## 报告元信息

| 字段 | 内容 |
|---|---|
| 标的名称 | {{股票名称}} |
| 股票代码 | {{sh600519 / sz000001 / hk00700 / usAAPL}} |
| 报告日期 | {{YYYY-MM-DD}} |
| 分析师 | {{分析师署名}} |
| 数据截止 | {{YYYY-MM-DD}} |
| 报告版本 | v3.0 |

---

## 0. 研究足迹（强制开头，单行 ≤60 字）

> 小美我看了→{{搜索关键词/来源概括}}

- [ ] 已输出研究足迹行
- [ ] 内容非空（若为空必须补做研究，不得跳过）

### 数据源准备检查

- [ ] `[N]` neodata 鉴权：`connect_cloud_service` → `--token` 或缓存可用
- [ ] `[W]` westock-data 环境：`npx -y westock-data-skillhub@latest search 测试` 确认可用
- [ ] `[Y]` 元宝搜索：`.env` 中 `TENCENTCLOUD_WSA_APIKEY` 已配置
- [ ] `[T]` tavily：`.env` 中 `TAVILY_API_KEY` 已配置 + `tavily-python` 已安装
- [ ] `[S]` WebSearch：内置工具，兜底备用

> ⚠️ WorkBuddy 不自动读取 `.env`，每次调用元宝/tavily 前需 `set -a && . ~/.workbuddy/.env && set +a`

---

## 0.5 运行模型分流（深度版，强制——先判断"用哪副镜片看"）

> F 个股分析如果不先分流，会退回通用财务报告。冰冰小美 skill 的核心不是财务模板，而是先判断"这只股应该用哪副镜片看"。
> 深度版需要完整分流，并且每个运行模型要落到报告对应章节。

### 分流表

| 分流问题 | 命中运行模型 | 报告落点 |
|---|---|---|
| 是 AI 算力、材料、封装、液冷、电力、国产替代吗？ | **AI 基建材料端**（运行模型 6） | §1.2 硬核科技验证（技术团队+产业集群+材料/封装/算力卡点） |
| 是白酒、地产、银行、保险、旧消费吗？ | **旧红利退出**（运行模型 7） | §1.3 资产属性判断（新登/老登+增长性 vs 资产属性） |
| 是国家战略、产业政策、国产替代、出海竞争吗？ | **国家-金融-产业**（运行模型 3） | §2.2 时代主线校验 + §3.1 行业基本面 |
| 是宏观冲击、美元、美债、石油、地缘风险吗？ | **危机演绎链**（运行模型 4） | §7.3 危机演绎链扫描 + §元要求D 央妈动作扫描 |
| 是公告、小作文、题材传播、市场吹票吗？ | **信息金融意义 / 显学隐学**（运行模型 5） | §5.2 假象识别（传播阶段+谁在制造） |
| 以上都涉及 | 多模型组合 | 按权重排序，主模型先行 |
| 都不是 | 回到 **体系三要素**（运行模型 1） | §3.2 三要素扫描 + §8.4 仓位建议 |

### 运行模型-报告章节落点对照

| 运行模型 | 报告落点 | 深度版要求 |
|---|---|---|
| 体系三要素（模型 1） | §3.2 行业与竞争格局、§5 市场预期、§8.4 仓位建议 | 三要素逐层扫描，共振/不共振明确判断 |
| 买入不败 / 空仓（模型 3+8） | §7 风险分析、§8.5 反向三问、§8 投资结论 | 反向三问必答，三要素不利项数决定仓位 |
| 国家-金融-产业（模型 4） | §2.2 时代主线校验、§3.1 产业政策/国产替代 | 9年周期阶段判断，方向是否和时代主题一致 |
| 危机演绎链（模型 7） | §7.3 危机演绎链扫描、§7.2 地缘动态 | 单点→扩散→宏观确认三层扫描，共振层级判断 |
| 信息金融意义 / 显学隐学（模型 5+2） | §5.2 假象识别、§5.1 公告/小作文/传播阶段 | 假象传播阶段判断，人人皆知=行情终点 |
| AI 基建材料端（模型 6） | §1.2 硬核科技验证（技术团队+产业集群+卡点） | tavily extract PDF研报获取高管履历+基地分布 |
| 旧红利退出（模型 7） | §1.3 资产属性判断（新登/老登） | 新登高估值≠泡沫，无增长老登=泡沫 |

### 分流输出（2-3 句）

> 主运行模型：{{命中模型}}。辅运行模型：{{命中模型}}。
> 理由：{{一句话说明为什么用这副镜片，以及它如何决定后续分析重点}}。
> 报告落点：{{列出本次分析将重点展开的章节}}。

- [ ] 已完成分流表判断（逐行检查）
- [ ] 已确定主运行模型 + 辅运行模型
- [ ] 已输出运行模型 + 理由 + 报告落点（2-3 句）
- [ ] 已确认各运行模型对应的报告章节将重点展开

---

## 1. 公司概况

### 1.1 基础信息

| 数据项 | 最优获取方式 | 命令/查询 |
|---|---|---|
| 主营业务描述 | `[N]` neodata / `[W]` profile | `neodata: "<公司>主营业务"` / `profile <code>` |
| **收入构成百分比** | `[N]` neodata **首选** | `neodata: "<公司>主营业务收入构成"` → apiRecall type=`主营构成与业绩趋势` |
| 细分赛道 | `[W]` profile | `profile <code>` → industry/sector |
| 产业链位置 | `[N]` neodata 研报 + `[T]` tavily extract | neodata docRecall + tavily extract PDF研报 |

> 实测证据：neodata 返回长电科技"电子元器件387.14亿(99.60%)/境外304.39亿(78.31%)/境内82.76亿(21.29%)"

- [ ] 主营业务：{{填写}}
- [ ] 收入构成百分比：{{填写，含产品拆分+地区拆分}}
- [ ] 细分赛道：{{填写}}
- [ ] 产业链位置：{{填写}}

### 1.2 硬核科技验证（科技股必填，非科技股标注「不适用」）

| 数据项 | v2.0 方式 | **v3.0 最优方式** | 实测证据 |
|---|---|---|---|
| **核心技术团队背景** | WebSearch 候补 | **`[T]` tavily extract PDF研报** + `[Y]` 元宝搜索官网 | extract 一次获取5位高管完整履历（李春兴59件专利/郑力东京大学/高永岗南开大学等） |
| **产业集群位置** | WebSearch 候补 | **`[T]` tavily extract PDF研报** | extract 获取全球6大基地分布表（江阴/滁州/宿迁/新加坡/韩国仁川+各厂区产品类型） |
| 研发投入占比 | `[W]` finance RAndD | `[W]` finance RAndD + `[N]` neodata 研报 | RAndD 直接字段 + 研报"研发费用率5.37%" |
| 技术壁垒实质 | `[N]` neodata 研报 | `[N]` neodata 研报 + `[T]` tavily extract | 研报含 XDFOI/CPO/FCBGA 等技术描述 |

> 模型 6 提醒：标签会骗人，不看概念标签。先看人和产业地基。
> **v3.0 改进**：tavily extract 完美解决了 PDF 内容提取问题，技术团队+产业集群一次获取，比 WebSearch 更详细更权威。

**tavily extract 操作步骤**：
1. `[T]` tavily search 发现 PDF 研报链接（Score 排序）
2. `[T]` tavily extract `<PDF_URL>` --query "高管 技术团队 履历 背景" --format markdown
3. 一次提取获取完整高管履历 + 基地分布表

- [ ] 核心技术团队背景：{{填写，含 CTO/CEO 履历+专利+学历}}
- [ ] 产业集群位置：{{填写，含各厂区位置+产品类型}}
- [ ] 研发投入占比：{{填写}}
- [ ] 技术壁垒实质：{{填写}}

### 1.3 资产属性判断

- [ ] 老登还是新登？{{老登/新登}}
- [ ] 增长性还是资产属性？{{有增长/无增长}}
- [ ] 判断依据：{{一句话说明}}

> 启发式 12：新登高估值≠泡沫，无增长老登=泡沫。

---

## 2. 核心投资逻辑

### 2.1 逻辑分类（只抓最核心的一条，不堆逻辑）

- [ ] 逻辑类型：{{成长驱动/周期反转/价值修复/事件催化/产业趋势/竞争格局改善}}
- [ ] 核心一句话：{{用一句话讲清楚为什么买}}

### 2.2 时代主线校验

| 数据项 | 获取方式 |
|---|---|
| 国家战略方向 | `[S]` WebSearch + `[W]` macro indicator |
| 时代主题位置 | `[分析]` 模型 4 判断 |

- [ ] 是否符合国家战略方向？{{十五五/新质生产力/国产替代/AI基建}}
- [ ] 时代主题位置：{{安全与发展→竞争与合作发展}}
- [ ] 逻辑与时代主线一致性：{{一致/部分一致/对抗}}

---

## 3. 行业与竞争格局

### 3.1 行业基本面

| 数据项 | 获取方式 | 命令 |
|---|---|---|
| 景气度方向 | `[W]` sector oper/forecast | `sector oper <行业名>` / `sector forecast <pt代码>` |
| 行业财务截面 | `[W]` sector finance | `sector finance <pt代码>` → roeTTM/grossProfitRatioTTM/debtRatio |
| 行业估值百分位 | `[W]` sector valuation | `sector valuation <pt代码>` → PeTTMPct/PbLFPct/DivTTMPct |
| 格局稳定性/公司地位 | `[N]` neodata 研报 + `[Y]` 元宝搜索 | neodata: "<公司>竞争格局" + 元宝搜索补充国内视角 |

- [ ] 景气度方向：{{填写}}
- [ ] 格局稳定性：{{填写}}
- [ ] 公司地位：{{填写}}
- [ ] 未来 1-2 季度最重要的行业变量：{{填写}}

### 3.2 竞争格局三要素扫描（维度最高的一层）

| 要素 | 获取方式 | 命令 |
|---|---|---|
| **竞争格局比较优势** | `[S]` WebSearch + `[W]` macro indicator | 国家战略/中美关系/产业政策 |
| **流动性辩证分析** | `[W]` market-overview + macro indicator | `market-overview --type all` + `macro indicator cn_core` |
| **情绪位置变化** | `[W]` market-overview + changedist | `market-overview --type updown` + `changedist` |

> 模型 1：三者共振=阻力最小的路径。一项不利=轻仓，两项不利=空仓。

- [ ] 竞争格局比较优势：{{填写}}
- [ ] 流动性辩证分析：{{填写，含央妈动作+水流方向}}
- [ ] 情绪位置变化：{{冰点/犹豫/共识/极度贪婪/退潮}}

### 3.3 产业资本动向

| 数据项 | 获取方式 | 命令/字段 |
|---|---|---|
| 十大股东（含大基金/国家队） | `[W]` shareholder | `shareholder <code>` → holdChange 变动数 |
| 北向季度持仓 | `[W]` fund north-holding | `fund north-holding <code>` → HoldingCap/CapChgQ |
| **核心高管增减持** | `[W]` risk --types executivetransfer | `risk <code> --types executivetransfer` → managerName/managerSharesChange |
| 高管变动 | `[W]` risk --types leaderchange | `risk <code> --types leaderchange` |
| 回购数据 | `[W]` buyback | `buyback <code>` |
| 大宗交易 | `[W]` fund block | `fund block <code>` |

> ⚠️ v1.0 纠正：高管增减持正确命令是 `risk --types executivetransfer`，不是 `changedist`。

- [ ] 大基金/国家队增减持：{{填写}}
- [ ] 北向持仓变动：{{填写}}
- [ ] 核心高管增减持：{{填写}}
- [ ] 回购动向：{{填写}}

---

## 4. 财务质量验证

### 4.1 核心财务指标（`[W]` finance --num 4，三大报表）

| 指标 | westock 字段 | 计算方式 |
|---|---|---|
| 营收增速 | `consensus` revenueYoy | 直接取 |
| 净利润增速 | `consensus` netProfitYoy | 直接取 |
| 毛利率 | `GrossProfitTTM`/`OperatingRevenueTTM` | **需自行计算** |
| 净利率 | `NPParentCompanyOwnersTTM`/`OperatingRevenueTTM` | **需自行计算** |
| ROE | `NPParentCompanyOwnersTTM`/`TotalShareholderEquity` | **需自行计算** |
| 经营现金流/净利润 | `NetOperateCashFlowTTM`/`NPParentCompanyOwnersTTM` | **需自行计算** |
| **自由现金流** | **`FCFF`/`FCFE`** | **直接字段** |
| 费用率 | `FinancialExpense`/`OperatingExpense`/`TotalAdminExpense` | 各自/营收 |
| 存货 | `Inventories` | 直接取 |
| 应收账款 | `BillAccReceivable`/`ReceivablesFin` | 直接取 |
| 研发费用 | **`RAndD`** | **直接字段** |
| 商誉 | `GoodWill` | 直接取 |
| 有息负债 | `InterestBearDebt`/`ShortTermLoan`/`LongtermLoan`/`BondsPayable` | 求和 |

- [ ] 近 4 期财务数据已拉取
- [ ] 毛利率/净利率/ROE 已自行计算
- [ ] 自由现金流（FCFF/FCFE）已确认
- [ ] 研发费用占比已确认

### 4.2 穿越股属性判断

- [ ] 信贷扩张周期（周期股）：{{是/否}}
- [ ] 高速增长景气周期（成长股）：{{是/否}}
- [ ] 自由现金流充裕（价值股）：{{是/否}}
- [ ] 综合判断：{{属于3类之一/不属于}}

> 模型 8：2026-06 实证——流动性挤压下只剩1类半有效：「自由现金流+新登赛道」组合才是真避风港。

### 4.3 叙事-财务匹配度

| 数据项 | 获取方式 |
|---|---|
| 业绩发布会内容 | `[N]` neodata **首选**（A股 T+1） |
| 研报叙事 vs 财报数据 | `[N]` neodata docRecall vs `[W]` finance |

- [ ] 财务与叙事是否匹配？{{匹配/部分匹配/不匹配}}
- [ ] 若不匹配，置信度调整：{{降置信度/维持/提升需更多证据}}

---

## 5. 当前市场预期

### 5.1 预期类型识别

| 数据项 | 获取方式 |
|---|---|
| 机构研报观点 | `[N]` neodata docRecall **首选**（研报全文） |
| 机构一致预期 | `[W]` consensus（EPS/PE/PB/PS/目标价/机构数） |
| 研报列表 | `[W]` report list（含评级） |
| **PDF 研报深度提取** | `[T]` tavily extract（从 PDF URL 精准提取内容） |

- [ ] 市场在交易什么预期？{{业绩超预期/新产品放量/景气反转/估值切换/政策驱动/情绪催化}}

### 5.2 假象识别（模型 2）

- [ ] 上涨/下跌承载什么假象？{{描述}}
- [ ] 谁在制造假象？{{游资/机构/量化/政策/国家意志/自媒体}}
- [ ] 假象传播阶段：
  - [ ] 初期共识
  - [ ] 故事展开
  - [ ] 券商推投顾
  - [ ] 人人皆知（传播极限=行情终点）

### 5.3 流动性挤压环境检查

| 数据项 | 获取方式 | 命令 |
|---|---|---|
| 市场涨跌分布 | `[W]` changedist | `changedist` |
| 主力资金流向 | `[W]` fund flow | `fund flow <code>` |
| 融资融券 | `[W]` fund margin | `fund margin <code>` |
| 北向日度流向 | `[W]` market-overview | `market-overview --type all` |

- [ ] 是否处于流动性挤压环境？{{是/否}}
- [ ] 资金行为：{{向少数标的集中/全面流出/正常轮动}}
- [ ] 该标的是否处于 AI/硬核科技产业链核心位置？{{是/否}}

---

## 6. 估值与位置判断

### 6.1 估值数据

| 指标 | 获取方式 | 字段 |
|---|---|---|
| PE/PEG/PB/PS | `[W]` consensus | forecasts[].pe/pb/ps |
| 目标价/机构数 | `[W]` consensus | targetPrice + institutionCnt |
| **行业历史百分位** | `[W]` sector valuation | PeTTMPct/PbLFPct/PsTTMPct/DivTTMPct |
| 股息率 | `[W]` dividend list + sector valuation | cashDiviRMB / DivTTM |
| 机构评级 | `[W]` rating + `[N]` neodata 研报 | rating + 研报评级 |

| 指标 | 当前值 | 行业中位数 | 历史5年分位 |
|---|---|---|---|
| PE(TTM) | {{}} | {{}} | {{}} |
| PEG | {{}} | {{}} | — |
| PB | {{}} | {{}} | {{}} |
| PS | {{}} | {{}} | {{}} |
| 股息率 | {{}} | {{}} | {{}} |
| 机构目标价 | {{}} | — | — |
| 覆盖机构数 | {{}} | — | — |

### 6.2 估值-逻辑匹配判断

- [ ] 高估值是否=泡沫？（新登+有增长→合理 / 老登+无增长→真泡沫）
- [ ] 估值是否已反映预期？{{已充分反映/部分反映/未反映}}

### 6.3 同业可比公司评分对比

| 公司 | 综合评分 | 基本面评分 | 风险评分 | 技术评分 | 资金评分 |
|---|---|---|---|---|---|
| {{标的}} | {{}} | {{}} | {{}} | {{}} | {{}} |
| {{可比1}} | {{}} | {{}} | {{}} | {{}} | {{}} |
| {{可比2}} | {{}} | {{}} | {{}} | {{}} | {{}} |
| {{可比3}} | {{}} | {{}} | {{}} | {{}} | {{}} |
| 中位数 | {{}} | {{}} | {{}} | {{}} | {{}} |

> `[W]` score 批量查询：`score <code1>,<code2>,<code3>,<code4>`

---

## 7. 风险分析（最关键的一段，风险永远在收益前面）

### 7.1 分层风险清单

#### 短期风险（1-3个月）

| 数据项 | 获取方式 | 字段 |
|---|---|---|
| 资金评分+周月趋势 | `[W]` score | 资金评分(周↓/月↓/季↑) |
| 技术评分+周月趋势 | `[W]` score | 技术评分(周↓/月↓/季↑) |
| 技术指标 | `[W]` technical | MACD/KDJ/RSI/BOLL |
| 筹码分布 | `[W]` chip | chipProfitRate/chipAvgCost/chipConcentration |
| K线走势 | `[W]` kline | `kline <code> --period day --limit 60` |

- [ ] 资金评分：{{数值}}（周趋势{{↑/↓}} 月趋势{{↑/↓}}）
- [ ] 技术评分：{{数值}}（周趋势{{↑/↓}} 月趋势{{↑/↓}}）
- [ ] **周内显著下跌=派发/恶化的硬信号**：{{是/否}}
- [ ] 筹码集中度变化：{{集中/分散}}

#### 中期风险（3-12个月）

- [ ] 需求风险：{{描述}}
- [ ] 竞争风险：{{描述}}
- [ ] 产能风险：{{描述}}

#### 长期风险（1年以上）

- [ ] 商业模式风险：{{描述}}（`[W]` finance GoodWill）
- [ ] 政策风险：{{描述}}
- [ ] 技术替代风险：{{描述}}

### 7.2 风险事件扫描（`[W]` risk，A股专属）

| 风险类型 | 命令 |
|---|---|
| ST特别处理 | `risk <code> --types st` |
| 股权质押 | `risk <code> --types pledge` |
| 解禁信息 | `risk <code> --types unlock` |
| 诉讼仲裁 | `risk <code> --types lawsuit` |
| 增发信息 | `risk <code> --types seo` |
| 高管变动 | `risk <code> --types leaderchange` |
| **高管增减持** | `risk <code> --types executivetransfer` |
| 评级变动 | `risk <code> --types bondrating`（⚠️文档自承返回空） |

- [ ] ST风险：{{无/有}}
- [ ] 股权质押比例：{{数值}}（≥50%高风险）
- [ ] 近期解禁：{{无/有，金额}}
- [ ] 诉讼仲裁：{{无/有，涉诉金额}}
- [ ] 高管增减持：{{无/有，变动方向}}

### 7.3 危机演绎链扫描（模型 7）

| 层级 | 数据项 | 获取方式 |
|---|---|---|
| 单点市场因子 | 流动性挤压/亏钱效应/龙头闪崩 | `[W]` market-overview + changedist |
| 宏观因子扩散 | 美债收益率/汇率/海外资产 | `[W]` macro indicator us_monetary + `[T]` tavily finance |
| **宏观确认** | 美联储政策/地缘冲突/第三方危机 | **`[T]` tavily finance search**（AI摘要+Score）+ `[Y]` 元宝搜索（国内视角）+ `[S]` WebSearch |

> **v3.0 改进**：地缘动态从"WebSearch 为主"升级为"tavily finance search（AI摘要+Score+时间过滤）+ 元宝搜索（国内视角）双搜交叉验证"。

- [ ] 单点信号：{{有/无}}
- [ ] 扩散信号：{{有/无}}
- [ ] 宏观确认：{{有/无}}
- [ ] 共振层级：{{单层/两层共振→减仓/三层确认→空仓}}

### 7.4 杀流动性 vs 杀逻辑判断（周期股必填）

- [ ] 近期下跌性质：{{杀流动性/杀逻辑/两者叠加}}
- [ ] 杠杆出清判断：{{是否跌破上一轮杠杆起点}}
- [ ] 基本面是否同步恶化：{{铜价/产量/利润是否变化}}

### 7.5 主动买亏三重边界检查（若考虑逆势建仓）

- [ ] 边界①：产业逻辑无变化？{{是/否}}
- [ ] 边界②：下跌为杀流动性非杀逻辑？{{是/否}}
- [ ] 边界③：止损线清晰（事前列）？{{是/否}}
- [ ] 三重边界齐全？{{齐全→可主动买亏/缺一不买}}

---

## 8. 投资结论

### 8.1 综合判断

- [ ] 结论：{{买入/卖出/持有/观察}}
- [ ] 合理估值区间：{{下限-上限}}（来源：`[W]` consensus + `[N]` neodata + `[T]` tavily 研报）
- [ ] 当前价格相对位置：{{低于区间/区间内/高于区间}}

### 8.2 量化评分综合解读（`[W]` score）

| 评分维度 | 数值 | 周趋势 | 月趋势 | 季趋势 |
|---|---|---|---|---|
| 综合评分 | {{}} | {{}} | {{}} | {{}} |
| 基本面评分 | {{}} | {{}} | {{}} | {{}} |
| 风险评分 | {{}} | {{}} | {{}} | {{}} |
| 资金评分 | {{}} | {{}} | {{}} | {{}} |
| 技术评分 | {{}} | {{}} | {{}} | {{}} |

- [ ] 解读：{{高综合+高基本面=行业地位强、基本面稳健}}

### 8.3 前提条件（至少2条，每条以「如果XX，则判断可能不成立」开头）

- [ ] 前提1：如果 {{XX}}，则判断可能不成立
- [ ] 前提2：如果 {{XX}}，则判断可能不成立
- [ ] 前提3（可选）：如果 {{XX}}，则判断可能不成立

### 8.4 仓位建议

- [ ] 三要素有利项数：{{竞争格局/流动性/情绪各有几项有利}}
- [ ] 仓位建议：{{重仓/中仓/轻仓/空仓}}

### 8.5 反向三问（结论前必答，模型 3）

- [ ] 最大亏钱风险在哪里？{{回答}}
- [ ] 当前主要亏钱效应集中在哪个方向？{{回答}}
- [ ] 判断错了亏多少能出来？{{回答}}

---

## 元要求检查清单（贯穿全报告）

### A. 事实/逻辑/预期/风险四分类标注

- [ ] 每个判断已标明：[事实] / [逻辑] / [预期] / [风险]
- [ ] 四类不可混写

### B. 数据来源标注（显学原则，模型 5）

- [ ] `[N]`/`[W]`/`[Y]`/`[T]`/`[S]` 来源已标注
- [ ] 数据来源分歧处理：多源冲突时标注 [来源分歧]，优先采信近30日研报/官方公告
- [ ] 禁用知乎/微信公众号/百度百科

### C. 时代主线校验（报告开头必过）

- [ ] 当前竞争格局处于哪个9年周期阶段？{{2008-2017蜜月期/2017-2026对抗期/2026-2035竞争期}}
- [ ] 方向是否和时代主题一致？{{是/否}}

### D. 央妈动作扫描（流动性层必含）

| 数据项 | 获取方式 | 命令 |
|---|---|---|
| 央妈最新动作 | `[W]` macro indicator | `macro indicator cn_core --date <今天>` |
| M2/M1/SHIBOR/CPI/PPI | `[W]` macro indicator cn_core | 一键返回7大核心指标 |
| MLF/LPR | `[W]` macro indicator cn_mlf/cn_lpr | |
| 股债溢价率（10年分位） | `[W]` macro indicator cn_premium_value | EprPct10Y（>80%股市偏便宜） |
| 期限利差（曲线形态） | `[W]` macro indicator cn_term_spread | 牛陡/牛平/熊陡/熊平 |
| 美联储动作 | `[W]` macro indicator us_monetary | `macro indicator us_monetary --date <今天>` |
| **地缘动态补充** | **`[T]` tavily finance + `[Y]` 元宝搜索** | 双搜交叉验证 |

> **v3.0 改进**：地缘动态从"WebSearch 兜底"升级为"tavily finance search（AI摘要+财经媒体+Score+时间过滤）+ 元宝搜索（国内视角）双搜交叉验证"。

- [ ] 央妈最新动作：{{降准/降息/MLF/LPR/逆回购}}
- [ ] 水往哪里流？{{流向方向}}
- [ ] 是否「以我为主」独立周期？{{是/否}}
- [ ] 地缘动态（双搜验证）：{{tavily 视角 + 元宝视角}}

### E. 重校准触发检查

- [ ] 美联储再次降息+A股独立走强验证失效？→启发式12/13
- [ ] 新登/老登标签被市场重新混合？→启发式12
- [ ] 流动性挤压从「分化极端」转为「全面熊市」？→启发式11
- [ ] 中美货币政策重新同步？→启发式13
- [ ] 任一触发→回退到基础三要素做交叉验证

### F. 研究足迹非空验证

- [ ] 第0节研究足迹行已输出且内容非空

### G. 双搜交叉验证（v3.0 新增）

> 元宝搜索 vs tavily 互补性极强：元宝擅长国内财经媒体+官网，tavily 擅长投资研究+PDF+Score。

- [ ] 技术团队背景：`[Y]` 元宝搜索（官网+国内媒体）+ `[T]` tavily extract（PDF研报）已交叉验证
- [ ] 产业集群位置：`[T]` tavily extract（PDF研报基地分布表）已确认
- [ ] 地缘动态：`[T]` tavily finance（AI摘要+Score）+ `[Y]` 元宝搜索（国内视角）已交叉验证



---

## 适用边界

- [ ] 主战场：A股（neodata + westock 全覆盖 + 元宝/tavily 补充）
- [ ] 港股：westock 覆盖 + neodata 部分覆盖 + tavily 补充
- [ ] 美股：westock 部分覆盖 + tavily 补充（元宝搜索覆盖较弱）
- [ ] 加密货币/外汇：不适用
- [ ] 非科技行业：模型6（人才+产业集群）不适用
- [ ] 短线情绪标的：启发式14（产业信念优先于技术面）边界不适用

---

## v3.0 五源数据能力速查表

| 数据维度 | `[N]` neodata | `[W]` westock | `[Y]` 元宝搜索 | `[T]` tavily | `[S]` WebSearch |
|---|---|---|---|---|---|
| 收入构成百分比 | ✅ **首选** | ❌ | ⚠️ | ❌ | ⚠️ |
| 财务三大报表 | ⚠️ 部分 | ✅ **首选** | ❌ | ❌ | ❌ |
| 自由现金流 | ❌ | ✅ **直接字段** | ❌ | ❌ | ❌ |
| 研发费用 | ⚠️ | ✅ **直接字段** | ❌ | ❌ | ❌ |
| 研报全文 | ✅ **首选** | ✅ report | ⚠️ | ⚠️ | ⚠️ |
| **PDF研报内容提取** | ❌ | ❌ | ❌ | ✅ **extract** | ❌ |
| 机构一致预期 | ⚠️ | ✅ **首选** | ❌ | ❌ | ❌ |
| 机构评级 | ✅ 研报内含 | ✅ rating | ⚠️ | ⚠️ | ⚠️ |
| 股东变动 | ⚠️ | ✅ shareholder | ❌ | ❌ | ❌ |
| 高管增减持 | ❌ | ✅ risk | ❌ | ❌ | ⚠️ |
| 北向持仓 | ❌ | ✅ fund north-holding | ❌ | ❌ | ❌ |
| 资金流向 | ⚠️ | ✅ fund flow | ❌ | ❌ | ❌ |
| 筹码分布 | ❌ | ✅ chip | ❌ | ❌ | ❌ |
| 技术指标 | ❌ | ✅ technical | ❌ | ❌ | ❌ |
| 量化评分 | ❌ | ✅ score | ❌ | ❌ | ❌ |
| 风险事件 | ❌ | ✅ risk（A股） | ❌ | ❌ | ⚠️ |
| 行业估值百分位 | ❌ | ✅ sector valuation | ❌ | ❌ | ❌ |
| 宏观指标 | ❌ | ✅ macro indicator | ❌ | ❌ | ❌ |
| **技术团队背景** | ⚠️ 研报部分 | ❌ | ✅ **官网+国内媒体** | ✅ **extract PDF** | ✅ |
| **产业集群位置** | ⚠️ 研报部分 | ❌ | ⚠️ | ✅ **extract PDF** | ✅ |
| **地缘动态** | ⚠️ 资讯 | ❌ | ✅ **国内视角** | ✅ **finance+AI摘要** | ✅ |
| 业绩发布会 | ✅ **首选** | ❌ | ❌ | ❌ | ⚠️ |
| 多模态（股价/金价） | ❌ | ✅ 行情数据 | ✅ `--mode=2` | ❌ | ❌ |
| **深度研究** | ❌ | ❌ | ❌ | ✅ **research** | ❌ |

---

## v3.0 搜索 skill 调用方式速查

### 元宝搜索（`[Y]`）

```bash
# 基础搜索
set -a && . ~/.workbuddy/.env && set +a && \
python -X utf8 ~/.workbuddy/skills/tencent-yuanbao-standard-search/scripts/websearch.py \
  --query="查询内容"

# 时间过滤
python -X utf8 ~/.workbuddy/skills/tencent-yuanbao-standard-search/scripts/websearch.py \
  --query="查询内容" --freshness=week

# 多模态（股价/金价/汇率）
python -X utf8 ~/.workbuddy/skills/tencent-yuanbao-standard-search/scripts/websearch.py \
  --query="查询内容" --mode=2

# 站点限定
python -X utf8 ~/.workbuddy/skills/tencent-yuanbao-standard-search/scripts/websearch.py \
  --query="查询内容" --site="sogou.com"
```

### Tavily（`[T]`）— workbuddy-tavily 或 tavily-search-pro 任选其一

```bash
# 通用搜索（含AI Answer）
set -a && . ~/.workbuddy/.env && set +a && \
python -X utf8 ~/.workbuddy/skills/workbuddy-tavily/scripts/tavily.py \
  search --query="查询内容" --max-results 5 --include-answer basic

# 财经搜索（AI摘要+Score+时间过滤）
python -X utf8 ~/.workbuddy/skills/workbuddy-tavily/scripts/tavily.py \
  search --query="查询内容" --topic finance --include-answer basic --time-range month

# 新闻搜索
python -X utf8 ~/.workbuddy/skills/workbuddy-tavily/scripts/tavily.py \
  search --query="查询内容" --topic news --time-range week

# ★ PDF/URL 内容提取（关键技术团队+产业集群获取方式）
python -X utf8 ~/.workbuddy/skills/tavily-search-pro/lib/tavily_search.py \
  extract "https://pdf.dfcfw.com/..." --query "高管 技术团队 履历 背景" --format markdown

# 深度研究（AI多轮+自动引用）
python -X utf8 ~/.workbuddy/skills/workbuddy-tavily/scripts/tavily.py \
  research --input "研究问题" --model pro --citation-format numbered

# 用量查询
python -X utf8 ~/.workbuddy/skills/workbuddy-tavily/scripts/tavily.py usage
```

### westock-data（`[W]`）

```bash
npx -y westock-data-skillhub@latest search <关键词>
npx -y westock-data-skillhub@latest profile <code>
npx -y westock-data-skillhub@latest finance <code> --num 4
npx -y westock-data-skillhub@latest consensus <code>
npx -y westock-data-skillhub@latest score <code>,<code2>,<code3>
npx -y westock-data-skillhub@latest shareholder <code>
npx -y westock-data-skillhub@latest risk <code> --types executivetransfer,leaderchange,pledge,unlock,lawsuit
npx -y westock-data-skillhub@latest fund flow <code>
npx -y westock-data-skillhub@latest fund north-holding <code>
npx -y westock-data-skillhub@latest market-overview --type all
npx -y westock-data-skillhub@latest macro indicator cn_core --date <今天>
npx -y westock-data-skillhub@latest sector valuation <pt代码>
npx -y westock-data-skillhub@latest report list <code>
```

### neodata（`[N]`）

```bash
# 需先 connect_cloud_service 获取 token
set -a && . ~/.workbuddy/.env && set +a && \
python -X utf8 ~/.workbuddy/skills/bingbingxiaomei-perspective/references/tools/finance-data/skills/neodata-financial-search/scripts/query.py \
  --query "长电科技主营业务收入构成" --token "$(cat ~/.workbuddy/.neodata_token | python -c 'import json,sys;print(json.loads(sys.stdin.read())["token"])')" 2>/dev/null || \
python -X utf8 ~/.workbuddy/skills/bingbingxiaomei-perspective/references/tools/finance-data/skills/neodata-financial-search/scripts/query.py \
  --query "查询内容"
```

---

## 使用说明

1. **数据源准备**：确认 5 源全部可用（neodata 鉴权 + westock 环境 + .env 配置）
2. **复制模板**，替换所有 `{{}}` 占位符
3. **按八步顺序填写**，每步完成后勾选对应 checkbox
4. **数据源优先级**：`[N]` > `[W]` > `[Y]` > `[T]` > `[S]`
5. **3 项候补数据最优路径**：
   - 技术团队 → `[T]` tavily extract PDF + `[Y]` 元宝搜索官网
   - 产业集群 → `[T]` tavily extract PDF
   - 地缘动态 → `[T]` tavily finance + `[Y]` 元宝搜索（双搜交叉验证）
6. **元要求检查清单**在报告完成后统一过一遍
7. **研究足迹**（第0节）必须在动笔前完成
8. **风险分析**（第7节）最关键，不可省略任何子项
9. **投资结论**（第8节）前提条件至少2条

### v2.0→v3.0 核心变更总结

| 变更项 | v2.0 | v3.0 |
|---|---|---|
| 数据源数量 | 3源（N/W/S） | **5源（N/W/Y/T/S）** |
| 技术团队获取 | WebSearch 候补 | **tavily extract PDF + 元宝搜索官网** |
| 产业集群获取 | WebSearch 候补 | **tavily extract PDF** |
| 地缘动态获取 | WebSearch 为主 | **tavily finance + 元宝搜索双搜** |
| PDF 内容提取 | 不支持 | **tavily extract（--query重排）** |
| AI Answer 摘要 | 不支持 | **tavily --include-answer** |
| Score 评分 | 不支持 | **tavily search 返回 Score** |
| 深度研究 | 不支持 | **tavily research（AI多轮+引用）** |
| 多模态查询 | 不支持 | **元宝搜索 --mode=2（股价/金价/汇率）** |
| 双搜交叉验证 | 无 | **元宝+tavily 互补验证** |

---

*模板版本：v3.0*
*基于：冰冰小美 F.看个股逻辑八步框架 + 7运行模型 + 17启发式 + 7轮实测验证*
*数据源：neodata + westock-data + 元宝搜索 + tavily(search/extract/finance/research) + WebSearch*
*生成日期：2026-07-07*
