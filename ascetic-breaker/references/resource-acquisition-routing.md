# 资源获取路由策略

> 本文档作为 SKILL.md Step 2 的详细参考。核心原则：**不重复实现检索逻辑**——调研类委托domain-research，代码类用WebSearch/WebFetch定向检索，项目内优先Glob/Grep。

## 目录
1. [路由决策树](#路由决策树)
2. [本Skill直接执行的检索（代码类）](#本skill直接执行的检索代码类)
3. [委托domain-research的检索（调研类）](#委托domainresearch的检索调研类)
4. [降级策略](#降级策略)
5. [检索结果处理](#检索结果处理)

---

## 路由决策树

```
Step 1 识别出缺口
│
├─ 缺口在项目内？（已有代码/配置/依赖文件）
│   └─ YES → Glob/Grep 本地搜索（P0，不联网）
│
├─ 缺口是代码/API/错误信息？
│   ├─ API签名/参数/版本 → WebSearch + WebFetch 官方文档（P1）
│   ├─ 错误信息排查 → WebSearch 搜错误，优先SO/GitHub Issues（P2）
│   └─ 成熟库发现 → WebSearch 搜GitHub + WebFetch README（P2）
│
├─ 缺口是行业数据/市场/政策/方案对比？
│   └─ YES → 委托 domain-research（多平台交叉验证）
│
├─ 缺口是学术文献？
│   └─ YES → 委托 literature-survey 或 scholar_search
│
└─ 以上都不是？
    └─ WebSearch 通用搜索（P4）
```

---

## 本Skill直接执行的检索（代码类）

### P0：项目内搜索（不联网）

| 目标 | 工具 | 示例 |
|------|------|------|
| 查找依赖文件 | Glob | `**/requirements*.txt`, `**/package.json` |
| 查找已有函数 | Grep | `def.*flatten`, `function.*parse` |
| 查找配置文件 | Glob | `**/.eslintrc*`, `**/pyproject.toml` |
| 查找测试模式 | Grep | `def test_`, `describe(` |
| 查找数据文件 | Glob | `**/*.csv`, `**/*.json` |

### P1：官方文档检索

```
WebSearch(query="{库名} {功能}", allowed_domains=["docs.{官方域名}"])
→ WebFetch(url=结果URL, prompt="提取{具体需要的信息}：API签名、参数说明、返回值、版本要求、代码示例")
```

要点：
- 用 `allowed_domains` 参数限定官方文档站（不用 `site:` 语法）
- WebFetch的 `prompt` 必须精确指定提取目标，不要抓整页
- 注意版本：文档可能对应最新版，需确认与项目版本一致
- WebFetch内容截断至100KB后通过Haiku摘要，无分页——摘要不完整时用更具体的prompt重新提取特定部分
- 跨域重定向不自动跟随，需用返回的新URL重新调用WebFetch

### P2：GitHub / Stack Overflow

```
WebSearch(query="{功能描述} {语言}", allowed_domains=["github.com"])
WebSearch(query="{错误信息}", allowed_domains=["stackoverflow.com"])
→ WebFetch(url=结果URL, prompt="提取解决方案、代码示例、适用版本、注意事项")
```

要点：
- GitHub优先高star、最近更新的项目
- Stack Overflow优先高票回答，但注意回答时间（可能过时）
- 检查许可证和版本兼容性
- 非预批准域名引用限制125字符，需要代码示例时优先预批准域名

### P3：技术博客

```
WebSearch(query="{功能} best practice {语言} 2025")
→ WebFetch(url=结果URL, prompt="提取核心方法、与其他方案对比、适用场景")
```

要点：
- 博客内容需交叉验证（单一来源不可全信）
- 注意发布时间，技术博客可能过时

### 检索约束
- WebSearch每次最多8次搜索，复杂检索分多批执行
- 每个缺口最多3轮关键词调整
- 第1轮：主体+功能（"pandas read_csv skip rows"）
- 第2轮：加版本/限定（"pandas 2.x read_csv skiprows header"）
- 第3轮：换同义词/英文（"pandas skip rows before header"）
- 3轮无结果 → 标记"未找到"，不继续死磕

---

## 委托domain-research的检索（调研类）

### 何时委托

满足任一条件即委托domain-research，不自行实现多平台搜索：
- 需要跨平台信息（CSDN/掘金/知乎/B站/公众号/小红书等）
- 需要行业数据、市场规模、政策法规
- 需要技术方案对比/选型分析
- 需要最新动态/趋势判断
- 需要多来源交叉验证

### 委托方式

将Step 1的缺口清单转化为domain-research的输入：

```
委托domain-research执行以下调研：
- 主题：{核心主题}
- 目的：{为什么需要这些信息，对应哪些缺口}
- 深度：{快速概览/中等调研/深度研究}
- 时间限定：{如近12个月}
- 必须覆盖的缺口：
  1. {缺口1描述}
  2. {缺口2描述}
```

### 委托后的处理

1. domain-research返回结果后，进入Step 3校验
2. 不重复domain-research已执行的搜索
3. 如果domain-research结果中某个缺口未覆盖，补充定向检索（不重新委托）
4. 如果domain-research不可用，降级为WebSearch通用搜索（见降级策略）

---

## 降级策略

| 失败场景 | 处理 |
|----------|------|
| domain-research不可用 | 降级为WebSearch 2-3组关键词 + WebFetch获取内容，标注"未做多平台交叉验证" |
| WebFetch超时/503 | 退避重试（1s→2s，最多2次）；仍失败用搜索摘要替代，标注"未获取全文" |
| WebFetch返回404/403 | 不重试，换一个搜索结果 |
| 官方文档站无法访问 | 降级到GitHub README或SO回答 |
| WebSearch返回结果不足 | 换关键词/去掉域名限定重试1次 |
| 3轮检索无结果 | 标记"未找到"，Step 4中列为假设 |
| 搜索结果全是低质量内容 | 标记"未找到可靠来源"，向用户说明 |

**重试原则**：
- 瞬时错误（超时、503）：退避重试，最多2次
- 永久错误（404、403）：不重试，直接换源
- 不要因为检索失败就编造内容

---

## 检索结果处理

### 去重
- URL去重：相同链接只保留一条
- 内容去重：核心观点相同的不同来源合并，保留信息更完整的
- 跨站转载：保留原始来源，标注"转载自"

### 摘要提取
每个检索结果提取以下结构化信息：
```
- 来源：[平台/网站名](URL)
- 标题：...
- 发布时间：...
- 核心内容：1-2句话
- 关键数据：[如有]
- 适用版本：[如有]
- 可信度：S/A/B/C（见下）
```

### 来源可信度

| 等级 | 来源 | 处理 |
|------|------|------|
| S | 官方文档 | 直接采用 |
| A | 高star GitHub / 高票SO | 采用，检查版本 |
| B | 知名技术博客/大厂团队博客 | 采用，交叉验证 |
| C | 个人博客/论坛帖子 | 需另一来源验证 |
| D | AI生成内容/未知来源 | 不采用或仅作参考 |
