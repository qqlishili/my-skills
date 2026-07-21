# TdxQuant 技能 - 通达信量化交易助手

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Claude](https://img.shields.io/badge/Claude-Skill-green.svg)](https://claude.ai)
[![Python](https://img.shields.io/badge/Python-3.7+-yellow.svg)](https://www.python.org)

> 完整的通达信 TdxQuant 量化交易平台 Claude AI 技能 - 涵盖从数据获取到策略执行的全流程指南

## 📖 简介

本技能为 Claude AI 提供通达信 TdxQuant 量化交易平台的完整使用指南。当您需要获取 A 股市场数据、开发量化交易策略、进行 K 线分析或技术指标计算时，Claude 会自动使用此技能为您提供专业支持。

### ✨ 核心特性

- 📊 **全面的 API 覆盖** - 涵盖所有 15 个 TdxQuant 核心模块
- 🚀 **实战策略示例** - 5 个完整的量化交易策略代码
- 🇨🇳 **中文原生支持** - 完全中文文档和代码注释
- 💡 **最佳实践指导** - 数据获取、性能优化、错误处理技巧
- 🎯 **智能触发** - 自动识别 A 股数据需求并激活技能

## 🎯 适用场景

当您在 Claude 中询问以下任何内容时，此技能会自动激活：

- 获取 A 股市场数据（实时行情、历史 K 线、财务数据）
- 通达信平台使用问题
- 量化交易策略开发
- K 线分析、技术指标计算
- 实时行情订阅与监控
- 股票选股策略
- 回测框架搭建
- 财务数据查询
- 交易接口调用
- 自定义板块管理
- 可转债、ETF、新股申购信息

## 📚 内容概览

### 1. 快速开始
```python
from tqcenter import tq

# 初始化连接（所有策略必须调用）
tq.initialize(__file__)

# 获取平安银行最近30天日线数据
data = tq.get_market_data(
    stock_list=['000001.SZ'],
    period='1d',
    count=30,
    field_list=['Open', 'High', 'Low', 'Close', 'Volume']
)

print(data)
tq.close()
```

### 2. 核心 API 模块（15 个完整模块）

| 模块 | 功能 | 主要 API |
|------|------|----------|
| **初始化** | 连接管理 | `tq.initialize()`, `tq.close()` |
| **行情数据** | K线、快照、除权 | `get_market_data()`, `get_full_tick()` |
| **实时订阅** | 行情推送 | `subscribe_hq()`, `unsubscribe_hq()` |
| **板块列表** | 板块、成分股查询 | `get_sector_list()`, `get_stock_list_in_sector()` |
| **财务数据** | 200+ 财务字段 | `get_financial()`, `get_profitability()` 等 |
| **交易日历** | 交易日查询 | `get_trading_calendar()`, `get_trading_dates()` |
| **消息预警** | 预警、消息推送 | `send_warn()`, `send_message()` |
| **自定义板块** | 板块管理 | `create_sector()`, `send_user_block()` |
| **缓存刷新** | 数据更新 | `refresh_cache()`, `refresh_kline()` |
| **特殊信息** | 可转债、ETF、IPO | `get_cb_info()`, `get_ipo_info()` |
| **交易接口** | 下单、撤单、查询 | `order_stock()`, `cancel_order_stock()` |
| **数据工具** | 数据处理、公式 | `price_df()`, `formula_zb()` |
| **常量定义** | 市场、周期、订单类型 | 市场代码、周期参数等 |
| **量化入门** | 5步交易流程 | 从想法到实盘 |
| **策略示例** | 5个完整策略 | 选股、预警、回测、监控、财务 |

### 3. 实战策略示例

#### 📈 连续上涨选股策略
从板块中筛选连续上涨 N 天的股票并添加到自定义板块

#### 📊 均线金叉预警策略
计算均线交叉信号并发送买卖预警

#### 💰 财务指标选股策略
基于 ROE、负债率、增长率等指标筛选优质股票

#### ⚡ 实时涨幅监控策略
订阅板块股票，实时监控涨幅突破并发送预警

#### 📉 技术指标回测策略
使用 VectorBT 进行均线策略回测并生成报告

## 🛠️ 安装使用

### 方式 1：Claude Code 用户（推荐）

1. **克隆本仓库**
   ```bash
   git clone https://github.com/your-username/tdxquant-skill.git
   ```

2. **复制到技能目录**
   ```bash
   cp -r tdxquant-skill ~/.claude/skills/tdxquant
   ```

3. **重启 Claude Code** - 技能会自动加载

### 方式 2：手动安装

1. 下载 `SKILL.md` 文件
2. 放置到 `~/.claude/skills/tdxquant/SKILL.md`
3. 重启 Claude Code

### 验证安装

在 Claude 中询问：
> "帮我用 TdxQuant 获取平安银行最近 30 天的股价数据"

如果 Claude 提供了完整的代码示例，说明技能已成功加载！

## 📖 使用示例

### 示例 1：获取股票数据
```python
from tqcenter import tq

tq.initialize(__file__)

# 获取多只股票的历史K线
data = tq.get_market_data(
    stock_list=['600519.SH', '000001.SZ'],
    period='1d',
    start_time='20240101',
    end_time='20241231',
    field_list=['Open', 'High', 'Low', 'Close', 'Volume'],
    dividend_type='front',
    fill_data=True
)

tq.close()
```

### 示例 2：实时监控预警
```python
import json
from tqcenter import tq

def price_callback(data_str):
    quote = json.loads(data_str)
    code = quote.get('Code')
    latest = float(quote['Now'])
    pre_close = float(quote['LastClose'])

    rise_rate = ((latest - pre_close) / pre_close) * 100
    if rise_rate > 5:
        # 发送预警
        tq.send_warn(
            stock_list=[code],
            price_list=[str(latest)],
            reason_list=[f'涨幅突破{rise_rate:.2f}%'],
            count=1
        )

tq.initialize(__file__)
tq.subscribe_hq(['600519.SH'], callback=price_callback)
```

### 示例 3：财务选股策略
```python
from tqcenter import tq

tq.initialize(__file__)

# 获取沪深300成分股
stock_list = tq.get_stock_list(market='23')

# 获取财务数据
financial = tq.get_financial(
    stock_list=stock_list,
    start_time='20230101',
    end_time='20241231'
)

# 筛选：ROE>15%，负债率<60%
filtered = []
for stock in stock_list:
    if stock in financial:
        roe = float(financial[stock][-1].get('ROE', 0))
        debt = float(financial[stock][-1].get('DebtToAssetRatio', 100))
        if roe > 15 and debt < 60:
            filtered.append(stock)

# 创建自定义板块
tq.create_sector('QUALITY', '优质股')
tq.send_user_block('QUALITY', filtered)

tq.close()
```

## 🔧 系统要求

- **Python**: 3.7+
- **通达信终端**: 支持 TQ 插件版本
- **操作系统**: Windows
- **Claude Code**: 最新版本

## 📚 完整文档

本技能包含以下完整文档：

- **平台介绍** - TdxQuant 功能特性
- **环境配置** - 安装和设置步骤
- **API 参考** - 所有函数的详细说明
- **实战示例** - 可直接运行的策略代码
- **最佳实践** - 性能优化和错误处理
- **常见问题** - FAQ 和代码速查表

查看 `SKILL.md` 获取完整文档。

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 贡献方式

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 贡献内容建议

- 🐛 Bug 修复
- ✨ 新增策略示例
- 📖 文档改进
- 🌐 国际化翻译
- ⚡ 性能优化

## 📜 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [TdxQuant](https://github.com/xxx111ooo/TdxQuant_Docs) - 通达信量化交易平台
- [Claude Code](https://claude.ai/code) - Claude AI 代码助手
- 所有贡献者和使用者

## 📞 联系方式

- **Issues**: [GitHub Issues](https://github.com/your-username/tdxquant-skill/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/tdxquant-skill/discussions)

## 🌟 Star History

如果这个项目对您有帮助，请给一个 Star ⭐️

---

<div align="center">

**Made with ❤️ for Chinese Quantitative Traders**

[⬆ 返回顶部](#tdxquant-技能---通达信量化交易助手)

</div>
