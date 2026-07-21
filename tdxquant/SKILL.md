---
name: tdxquant
description: 完整的通达信TdxQuant量化交易平台使用指南。当用户提及以下任何内容时必须使用此技能：获取A股市场数据、通达信平台、量化交易策略开发、K线数据分析、技术指标计算、实时行情订阅、股票选股策略、回测框架搭建、财务数据查询、交易接口调用、自定义板块管理、可转债信息、ETF数据、新股申购。即使没有明确提到"TdxQuant"，只要用户需要获取中国A股市场数据（沪深京股票的实时行情、历史K线、财务数据、板块数据等）或开发量化交易策略，都应该触发此技能。
compatibility: 需要安装 Python 和通达信客户端
---

# TdxQuant 全能量化交易助手

本技能提供通达信TdxQuant量化交易平台的完整使用指南，涵盖从数据获取到策略执行的全流程。

## 目录

- [快速开始](#快速开始)
- [环境配置](#环境配置)
- [核心API模块](#核心api模块)
- [实战策略示例](#实战策略示例)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

---

## 快速开始

### TdxQuant 是什么

TdxQuant 是深圳市财富趋势科技股份有限公司推出的量化投研平台，提供：

- **行情数据获取**：实时行情、历史K线、财务数据
- **实时订阅监控**：行情推送、价格预警
- **交易接口**：模拟/实盘交易、账户管理
- **板块管理**：自定义板块、成分股查询
- **技术指标**：公式系统、指标计算
- **数据工具**：数据处理、导出功能

### 典型应用场景

1. **量化策略开发**：从数据获取到回测验证
2. **实时监控预警**：价格突破、技术指标信号
3. **股票选股**：基于技术面或基本面筛选
4. **数据研究**：A股历史数据分析
5. **自动化交易**：策略执行、订单管理

### 第一个TdxQuant程序

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

# 关闭连接
tq.close()
```

---

## 环境配置

### 系统要求

- Python 3.7+
- 通达信终端（支持TQ插件版本）
- Windows 操作系统

### 安装步骤

1. **安装TdxQuant Python包**
   ```bash
   pip install TdxQuant
   ```

2. **配置通达信终端**
   - 安装通达信终端
   - 启用TQ插件功能
   - 下载必要的历史数据

3. **验证安装**
   ```python
   from tqcenter import tq
   tq.initialize(__file__)
   print("TdxQuant连接成功！")
   ```

---

## 核心API模块

### 1. 初始化与连接管理

**必须首先调用的函数**

```python
from tqcenter import tq

# 初始化（每个策略必须调用）
tq.initialize(__file__)

# ... 使用各种API ...

# 手动关闭连接
tq.close()
```

**注意事项**：
- `initialize` 函数名不可修改
- 任何一个策略都必须包含此函数
- 用于建立与通达信客户端的连接

---

### 2. 行情数据获取

#### 2.1 获取K线数据

```python
# 获取多只股票的历史K线
data = tq.get_market_data(
    stock_list=['600519.SH', '000001.SZ'],  # 股票代码列表
    period='1d',                              # 周期：1m/5m/15m/30m/1h/1d/1w/1mon
    start_time='20240101',                    # 起始日期 YYYYMMDD
    end_time='20241231',                      # 结束日期
    field_list=['Open', 'High', 'Low', 'Close', 'Volume', 'Amount'],
    dividend_type='front',                    # 复权类型：none/front/back
    fill_data=True                            # 填充缺失数据
)
```

**支持的周期**：
- `1m`, `5m`, `15m`, `30m`, `1h` - 分钟线
- `1d` - 日线
- `1w` - 周线
- `1mon` - 月线
- `tick` - 分笔数据

**复权类型**：
- `none` - 不复权
- `front` - 前复权
- `back` - 后复权

#### 2.2 获取市场快照

```python
# 获取实时行情快照
snapshot = tq.get_full_tick(stock_list=['600519.SH', '000001.SZ'])
# 返回：最新价、昨收价、涨跌幅、成交量等
```

#### 2.3 获取除权数据

```python
# 获取除权除息信息
dividend = tq.get_dividend_factors(
    stock_code='600519.SH',
    start_time='20200101',
    end_time='20241231'
)
```

#### 2.4 获取股票信息

```python
# 获取股票基本信息
info = tq.get_stock_info('600519.SH')
# 返回：股票名称、行业、总股本、流通股本等
```

#### 2.5 获取更多数据

```python
# 获取更多扩展数据
more_data = tq.get_stock_more_info(
    stock_list=['600519.SH'],
    field_list=['GO1', 'GO2', 'GO3']  # 具体字段见文档
)
```

---

### 3. 实时订阅功能

#### 3.1 订阅行情

```python
# 定义回调函数
def on_quote_data(data):
    """接收到行情数据时的回调"""
    import json
    quote = json.loads(data)
    print(f"收到行情：{quote}")

# 订阅实时行情
result = tq.subscribe_hq(
    stock_list=['600519.SH', '000001.SZ'],
    callback=on_quote_data
)
```

#### 3.2 取消订阅

```python
# 取消指定股票的订阅
tq.unsubscribe_hq(stock_list=['600519.SH'])
```

**使用场景**：
- 实时价格监控
- 涨幅突破预警
- 技术指标实时计算

---

### 4. 板块与股票列表

#### 4.1 获取板块列表

```python
# 获取所有板块代码
sectors = tq.get_sector_list(list_type=0)
# 返回：['880081.SH', '880082.SH', ...]

# 获取板块代码和名称
sectors_with_name = tq.get_sector_list(list_type=1)
# 返回：[{'Code': '880081.SH', 'Name': '轮动趋势'}, ...]
```

#### 4.2 获取自定义板块

```python
# 获取用户自定义板块列表
user_sectors = tq.get_user_sector()
# 返回：[{'Code': 'CSBK', 'Name': '测试板块'}, ...]
```

#### 4.3 获取板块成分股

```python
# 通过板块代码获取成分股
stocks = tq.get_stock_list_in_sector('880081.SH', list_type=0)

# 通过板块名称获取成分股
stocks = tq.get_stock_list_in_sector('钛金属', list_type=1)

# 获取自定义板块成分股
stocks = tq.get_stock_list_in_sector('CSBK', block_type=1, list_type=1)
```

#### 4.4 获取股票列表

```python
# 获取市场类型股票列表
stock_list = tq.get_stock_list(
    market='23',  # 23=沪深300，5=所有A股，50=沪深A股
    list_type=1   # 0=只返回代码，1=返回代码和名称
)
```

**常用市场代码**：
- `5` - 所有A股
- `23` - 沪深300
- `24` - 中证500
- `25` - 中证1000
- `50` - 沪深A股
- `51` - 创业板

#### 4.5 获取股票所属板块

```python
# 查询股票所属的板块信息
relations = tq.get_relation(stock_code='600519.SH')
# 返回：行业板块、概念板块、地区板块、风格板块等
```

---

### 5. 财务数据获取（200+字段）

#### 5.1 主要财务数据

```python
# 获取主要财务指标
financial = tq.get_financial(
    stock_list=['600519.SH'],
    start_time='20230101',
    end_time='20241231',
    report_type='report',
    fields=['TotalAssets', 'TotalLiability', 'NetProfit', 'EPS']
)
```

**常用字段**：
- `TotalAssets` - 总资产
- `TotalLiability` - 总负债
- `NetProfit` - 净利润
- `EPS` - 每股收益
- `ROE` - 净资产收益率
- `OperatingRevenue` - 营业收入

#### 5.2 获利能力指标

```python
# 获取获利能力数据
profitability = tq.get_profitability(
    stock_list=['600519.SH'],
    start_time='20230101',
    end_time='20241231'
)
```

**包含字段**：ROE、ROA、毛利率、净利率等

#### 5.3 营运能力指标

```python
# 获取营运能力数据
operation = tq.get_operation(
    stock_list=['600519.SH'],
    start_time='20230101',
    end_time='20241231'
)
```

**包含字段**：总资产周转率、存货周转率、应收账款周转率等

#### 5.4 偿债能力指标

```python
# 获取偿债能力数据
solvency = tq.get_solvency(
    stock_list=['600519.SH'],
    start_time='20230101',
    end_time='20241231'
)
```

**包含字段**：流动比率、速动比率、资产负债率等

#### 5.5 成长能力指标

```python
# 获取成长能力数据
growth = tq.get_growth(
    stock_list=['600519.SH'],
    start_time='20230101',
    end_time='20241231'
)
```

**包含字段**：营收增长率、净利润增长率等

#### 5.6 估值指标

```python
# 获取估值数据
valuation = tq.get_valuation(
    stock_list=['600519.SH'],
    start_time='20230101',
    end_time='20241231'
)
```

**包含字段**：PE、PB、PS、市销率等

#### 5.7 其他财务API

```python
# 每股指标
tq.get_per_share()

# 现金流
tq.get_cash_flow()

# 业绩预告
tq.get_performance_forecast()

# 业绩快报
tq.get_performance_express()
```

---

### 6. 交易日历

```python
# 获取交易日历
calendar = tq.get_trading_calendar(
    market='SH',           # SH=上海，SZ=深圳
    start_time='20240101',
    end_time='20241231'
)

# 获取交易日列表
dates = tq.get_trading_dates(
    market='SH',
    start_time='20240101',
    end_time='20241231',
    count=10  # 返回最近10个交易日
)
```

---

### 7. 消息与预警

#### 7.1 发送消息到客户端

```python
# 发送文本消息（支持\n换行）
tq.send_message("策略信号：金叉买入\n股票：600519.SH")
```

#### 7.2 发送预警信息

```python
# 发送买卖预警
tq.send_warn(
    stock_list=['600519.SH', '000001.SZ'],
    time_list=['20241215140000', '20241215140100'],
    price_list=['1850.00', '12.50'],
    close_list=['1840.00', '12.30'],
    volum_list=['1000', '5000'],
    bs_flag_list=['0', '0'],      # 0=买入，1=卖出
    warn_type_list=['0', '0'],
    reason_list=['金叉买入', '突破压力位'],
    count=2
)
```

#### 7.3 发送文件

```python
# 发送文件到客户端（支持txt/pdf/html）
tq.send_file("analysis_report.pdf")
```

#### 7.4 发送回测数据

```python
# 发送回测结果到客户端
tq.send_bt_data(
    stock_code='600519.SH',
    time_list=['20241215140000'],
    data_list=[[100, 200, 300]],  # 最多16个数据
    count=1
)
```

---

### 8. 自定义板块管理

#### 8.1 创建自定义板块

```python
# 创建新板块
result = tq.create_sector(
    block_code='MYSTK',
    block_name='我的自选股'
)
```

#### 8.2 添加股票到板块

```python
# 添加股票到自定义板块
tq.send_user_block(
    block_code='MYSTK',
    stocks=['600519.SH', '000001.SZ', '600036.SH'],
    show=False  # 是否切换到板块界面
)

# 清空板块（传入空列表）
tq.send_user_block(block_code='MYSTK', stocks=[])
```

#### 8.3 删除板块

```python
# 删除自定义板块
tq.delete_sector(block_code='MYSTK')
```

#### 8.4 重命名板块

```python
# 重命名自定义板块
tq.rename_sector(
    block_code='MYSTK',
    block_name='我的优质股票'
)
```

#### 8.5 清空板块

```python
# 清空板块成分股
tq.clear_sector(block_code='MYSTK')
```

---

### 9. 缓存与数据刷新

#### 9.1 刷新行情缓存

```python
# 刷新指定市场行情缓存
tq.refresh_cache(
    market='AG',  # AG=A股，HK=港股，US=美股，QH=期货
    force=False   # False=10分钟内不重复刷新，True=强制刷新
)
```

**市场代码**：
- `AG` - A股
- `HK` - 港股
- `US` - 美股
- `QH` - 国内期货

#### 9.2 刷新K线缓存

```python
# 定向下载历史K线数据
tq.refresh_kline(
    stock_list=['600519.SH'],
    period='1d'  # 支持1m/5m/1d等
)
```

#### 9.3 下载特殊文件

```python
# 下载10大股东数据
tq.download_file(
    stock_code='600519.SH',
    down_time='2024',
    down_type=1  # 1=十大股东，2=ETF申赎清单
)
```

---

### 10. 特殊信息获取

#### 10.1 可转债信息

```python
# 获取所有可转债
cb_info = tq.get_cb_info(
    cb_type=0,       # 类型筛选
    list_type=1      # 返回代码和名称
)

# 获取单只可转债详情
kzz_detail = tq.get_kzz_info(
    stock_code='123039.SZ',
    field_list=['KZZCode', 'ZGPrice', 'ZGValue', 'KZZYj']
)
```

**可转债字段**：
- `ZGPrice` - 转股价格
- `ZGValue` - 转股价值
- `KZZYj` - 溢价率
- `ForceRedeem` - 强赎触发价
- `PutBack` - 回售触发价

#### 10.2 ETF信息

```python
# 获取跟踪指数的ETF
etf_info = tq.get_trackzs_etf_info(zs_code='950162.CSI')
# 返回ETF代码、名称、净值、规模等
```

#### 10.3 新股申购信息

```python
# 获取新股和新发债信息
ipo_info = tq.get_ipo_info(
    ipo_type=2,   # 0=新股，1=新债，2=新股+新债
    ipo_date=1    # 0=今天，1=今天及以后
)
```

---

### 11. 交易接口

#### 11.1 获取账户句柄

```python
# 获取资金账户句柄（交易前必须调用）
my_account = tq.stock_account(
    account="1190008847",
    account_type="STOCK"  # STOCK=股票，CREDIT=信用
)
```

#### 11.2 查询账户资产

```python
# 查询账户资产信息
asset = tq.query_stock_asset(account_id=my_account)
# 返回：总资产、可用资金、持仓市值等
```

#### 11.3 查询持仓

```python
# 查询持仓信息
positions = tq.query_stock_positions(account_id=my_account)
# 返回：股票代码、成本价、持仓数量、可用数量
```

#### 11.4 查询委托

```python
# 查询当日委托
orders = tq.query_stock_orders(
    account_id=my_account,
    stock_code=""  # 空字符串=查询所有，指定代码=查询单只
)
```

**订单状态**：
- `0` - 无效单
- `1` - 未成交
- `2` - 部分成交
- `3` - 全部成交
- `5` - 全部撤单

#### 11.5 下单

```python
from tqcenter import tqconst

# 买入股票
order = tq.order_stock(
    account_id=my_account,
    stock_code="600519.SH",
    order_type=tqconst.STOCK_BUY,  # 0=买入，1=卖出
    order_volume=100,               # 数量（股）
    price_type=tqconst.PRICE_MY,    # 0=自填价，1=市价，2=涨停价，3=跌停价
    price=1850.0                    # 委托价格
)
```

**订单类型**：
- `0` - 买入（STOCK_BUY）
- `1` - 卖出（STOCK_SELL）
- `69` - 融资买入（CREDIT_FIN_BUY）
- `70` - 融券卖出（CREDIT_SLO_SELL）

**价格类型**：
- `0` - 自填价（PRICE_MY）
- `1` - 市价（PRICE_SJ）
- `2` - 涨停价/笼子上限（PRICE_ZTJ）
- `3` - 跌停价/笼子下限（PRICE_DTJ）

#### 11.6 撤单

```python
# 撤销委托
cancel_result = tq.cancel_order_stock(
    account_id=my_account,
    stock_code="600519.SH",
    order_id="12345"  # 委托编号
)
```

---

### 12. 数据处理工具

#### 12.1 提取价格DataFrame

```python
import pandas as pd

# 从市场数据中提取收盘价DataFrame
close_df = tq.price_df(
    market_data,
    price_type='close',  # open/high/low/close
    column_names=['600519.SH', '000001.SZ']
)
```

#### 12.2 导出数据到通达信

```python
# 将计算结果导出到通达信展示
tq.print_to_tdx(
    df_list=[df1, df2],
    sp_name="strategy",
    xml_filename="output.xml",
    jsn_filenames=["factor1.jsn", "factor2.jsn"],
    vertical=2,
    height=[0.4, 0.6],
    table_names=["因子1", "因子2"]
)
```

#### 12.3 字段筛选

```python
# 筛选字典中的特定字段
filtered = tq.filter_dict_by_fields(
    data_dict={'Name': '茅台', 'Code': '600519.SH', 'Price': 1850},
    fields=['Name', 'Code']
)
# 返回：{'Name': '茅台', 'Code': '600519.SH'}
```

#### 12.4 调用通达信公式系统

```python
# 调用技术指标公式（如MACD）
tq.formula_set_data_info(
    stock_code='600519.SH',
    stock_period='1d',
    count=100,
    dividend_type=1
)

# 计算MACD
macd_result = tq.formula_zb(
    formula_name='MACD',
    formula_arg='12,26,9',
    xsflag=-1
)

# 调用选股公式
xg_result = tq.formula_xg(
    formula_name='UPN',
    formula_arg='3'
)

# 批量调用指标公式
mul_zb = tq.formula_process_mul_zb(
    formula_name='MA',
    formula_arg='5',
    stock_list=['600519.SH', '000001.SZ'],
    stock_period='1d',
    count=20
)
```

---

### 13. 常量定义

#### 市场类型

```python
# 交易所
.SZ = 0   # 深圳交易所
.SH = 1   # 上海交易所
.BJ = 2   # 北京交易所
.HK = 31  # 香港交易所
.US = 74  # 美国股票

# 指数
.CSI = 62   # 中证指数
.CNI = 102  # 国证指数
```

#### 周期类型

```python
'1m', '5m', '15m', '30m', '1h'  # 分钟/小时
'1d'   # 日线
'1w'   # 周线
'1mon' # 月线
'tick' # 分笔
```

#### 复权类型

```python
'none'   # 不复权
'front'  # 前复权
'back'   # 后复权
```

#### 订单类型

```python
STOCK_BUY = 0        # 买入
STOCK_SELL = 1       # 卖出
CREDIT_FIN_BUY = 69  # 融资买入
CREDIT_SLO_SELL = 70 # 融券卖出
```

#### 价格类型

```python
PRICE_MY = 0   # 自填价
PRICE_SJ = 1   # 市价
PRICE_ZTJ = 2  # 涨停价
PRICE_DTJ = 3  # 跌停价
```

---

## 实战策略示例

### 示例1：连续上涨选股策略

从板块中筛选连续上涨N天的股票并添加到自定义板块。

```python
import pandas as pd
import numpy as np
from datetime import datetime
from tqcenter import tq

# 初始化
tq.initialize(__file__)

# 配置参数
sector_name = '通达信88'
N = 3  # 连续上涨天数
block_code = 'LZXG'
block_name = '连涨选股'

# 获取板块股票列表
stock_list = tq.get_stock_list_in_sector(sector_name)

# 获取收盘价数据
df = tq.get_market_data(
    field_list=['Close'],
    stock_list=stock_list,
    start_time='20241025',
    end_time=datetime.now().strftime('%Y%m%d'),
    dividend_type='front',
    period='1d',
    fill_data=True
)

# 转换为DataFrame
close_df = tq.price_df(df, 'Close', column_names=stock_list)

# 计算连续上涨天数
is_up = close_df > close_df.shift(1)
up_mask = np.where(is_up, 1, np.nan)
up_mask_df = pd.DataFrame(up_mask, index=close_df.index, columns=close_df.columns)
filled_df = up_mask_df.ffill()
consec_up_days = filled_df.notna().cumsum()
reset_counts = consec_up_days.where(~is_up).ffill().fillna(0)
consec_up_days = (consec_up_days - reset_counts).astype(int)

# 筛选符合条件的股票
latest_date = consec_up_days.index[-1]
latest_consec_up = consec_up_days.loc[latest_date]
target_stocks = latest_consec_up[latest_consec_up >= N].sort_values(ascending=False)
target_stocks_list = target_stocks.index.tolist()

# 创建板块并添加股票
tq.create_sector(block_code=block_code, block_name=block_name)
if len(target_stocks_list) > 0:
    tq.send_user_block(block_code=block_code, stocks=target_stocks_list)
    msg = f"筛选出{len(target_stocks_list)}只连续上涨≥{N}天的股票"
else:
    tq.send_user_block(block_code=block_code, stocks=[])
    msg = "暂无符合条件的股票"

tq.send_message(msg)
print(msg)
```

### 示例2：均线金叉预警策略

计算均线交叉信号并发送买卖预警。

```python
from datetime import datetime, timedelta
from tqcenter import tq
import vectorbt as vbt
import pandas as pd

# 初始化
tq.initialize(__file__)

# 配置
N = 5  # 均线周期
sector_name = '通达信88'

# 获取股票列表
stock_list = tq.get_stock_list_in_sector(sector_name)

# 获取数据
end_date = datetime.now().strftime('%Y%m%d')
start_date = (datetime.now() - timedelta(days=2*N+20)).strftime('%Y%m%d')

df = tq.get_market_data(
    field_list=['Close'],
    stock_list=stock_list,
    start_time=start_date,
    end_date=end_date,
    dividend_type='front',
    period='1d',
    fill_data=True
)

close_df = tq.price_df(df, 'Close', column_names=stock_list)

# 计算均线和信号
ma = vbt.MA.run(close_df, window=N).ma
ma.columns = close_df.columns
entries = close_df.vbt.crossed_above(ma)  # 买入信号
exits = close_df.vbt.crossed_below(ma)    # 卖出信号

latest_date = close_df.index[-1]

# 筛选信号
buy_signals = []
sell_signals = []

for code in stock_list:
    if code not in close_df.columns:
        continue

    if entries.loc[latest_date, code]:
        buy_signals.append(code)

    if exits.loc[latest_date, code]:
        sell_signals.append(code)

# 发送预警
warn_time = datetime.now().strftime('%Y%m%d%H%M%S')

if buy_signals:
    tq.send_warn(
        stock_list=buy_signals,
        time_list=[warn_time]*len(buy_signals),
        price_list=[str(close_df.loc[latest_date, code]) for code in buy_signals],
        close_list=[str(close_df.loc[latest_date, code]) for code in buy_signals],
        bs_flag_list=['0']*len(buy_signals),
        reason_list=['均线金叉买入']*len(buy_signals),
        count=len(buy_signals)
    )

if sell_signals:
    tq.send_warn(
        stock_list=sell_signals,
        time_list=[warn_time]*len(sell_signals),
        price_list=[str(close_df.loc[latest_date, code]) for code in sell_signals],
        close_list=[str(close_df.loc[latest_date, code]) for code in sell_signals],
        bs_flag_list=['1']*len(sell_signals),
        reason_list=['均线死叉卖出']*len(sell_signals),
        count=len(sell_signals)
    )

print(f"买入信号：{len(buy_signals)}只，卖出信号：{len(sell_signals)}只")
```

### 示例3：财务指标选股策略

基于财务指标筛选优质股票。

```python
from datetime import datetime
from tqcenter import tq

# 初始化
tq.initialize(__file__)

# 获取沪深300成分股
stock_list = tq.get_stock_list(market='23', list_type=0)

# 获取财务数据
financial_data = tq.get_financial(
    stock_list=stock_list,
    start_time='20230101',
    end_time='20241231',
    report_type='report'
)

# 筛选条件
# 1. ROE > 15%
# 2. 负债率 < 60%
# 3. 净利润增长 > 10%
filtered_stocks = []

for stock in stock_list:
    if stock in financial_data:
        latest_data = financial_data[stock][-1]

        roe = float(latest_data.get('ROE', 0))
        debt_ratio = float(latest_data.get('DebtToAssetRatio', 100))
        profit_growth = float(latest_data.get('NetProfitGrowthRate', 0))

        if roe > 15 and debt_ratio < 60 and profit_growth > 10:
            filtered_stocks.append(stock)

# 创建自定义板块
tq.create_sector(block_code='FINSTK', block_name='财务优质股')
tq.send_user_block(block_code='FINSTK', stocks=filtered_stocks)

print(f"筛选出{len(filtered_stocks)}只财务优质股票")
```

### 示例4：实时涨幅监控策略

订阅板块股票，实时监控涨幅突破。

```python
import json
import time
from datetime import datetime
from collections import defaultdict
from tqcenter import tq

# 配置
SECTOR_NAMES = ['通达信88']
PRICE_RISE_THRESHOLD = 5.0  # 涨幅阈值5%
EXIT_FLAG = False
TRIGGERED_STOCKS = set()

def price_callback(data_str):
    """行情回调函数"""
    global TRIGGERED_STOCKS

    data = json.loads(data_str)
    code = data.get('Code')

    if code in TRIGGERED_STOCKS:
        return

    # 获取最新行情
    quote = tq.get_full_tick(code)
    if not quote:
        return

    latest_price = float(quote['Now'])
    pre_close = float(quote['LastClose'])

    if pre_close > 0:
        rise_rate = ((latest_price - pre_close) / pre_close) * 100

        if rise_rate > PRICE_RISE_THRESHOLD:
            TRIGGERED_STOCKS.add(code)

            # 发送预警
            warn_time = datetime.now().strftime('%Y%m%d%H%M%S')
            tq.send_warn(
                stock_list=[code],
                time_list=[warn_time],
                price_list=[str(latest_price)],
                close_list=[str(pre_close)],
                bs_flag_list=['0'],
                reason_list=[f'涨幅突破{rise_rate:.2f}%'],
                count=1
            )

            # 取消订阅
            tq.unsubscribe_hq(stock_list=[code])
            print(f"{code} 涨幅{rise_rate:.2f}%，已发送预警并取消订阅")

# 初始化
tq.initialize(__file__)

# 获取股票列表
stock_list = []
for sector in SECTOR_NAMES:
    stocks = tq.get_stock_list_in_sector(sector)
    stock_list.extend(stocks)

# 订阅行情
tq.subscribe_hq(stock_list=stock_list, callback=price_callback)

print("涨幅监控已启动，按Ctrl+C退出")

try:
    while not EXIT_FLAG:
        time.sleep(0.1)
except KeyboardInterrupt:
    print("程序退出")
```

### 示例5：技术指标回测策略

使用VectorBT进行均线策略回测。

```python
import pandas as pd
import vectorbt as vbt
from tqcenter import tq

# 初始化
tq.initialize(__file__)

# 配置
stock_code = '600519.SH'
start_date = '20230101'
end_date = '20241231'
window = 20  # MA周期

# 获取数据
df = tq.get_market_data(
    field_list=['Close', 'Open'],
    stock_list=[stock_code],
    start_time=start_date,
    end_date=end_date,
    dividend_type='front',
    period='1d',
    fill_data=True
)

close_df = tq.price_df(df, 'Close', column_names=[stock_code])
open_df = tq.price_df(df, 'Open', column_names=[stock_code])

# 计算均线
ma = vbt.MA.run(close_df, window=window).ma
ma.columns = close_df.columns

# 生成信号
entries = close_df.vbt.crossed_above(ma).shift(1).fillna(False).astype(bool)
exits = close_df.vbt.crossed_below(ma).shift(1).fillna(False).astype(bool)

# 回测
portfolio = vbt.Portfolio.from_signals(
    close=close_df,
    entries=entries,
    exits=exits,
    price=open_df,
    init_cash=100000,
    fees=0.0003,
    freq='D',
    size_granularity=100
)

# 输出结果
print("\n回测表现：")
print(portfolio.stats())

print("\n交易记录：")
print(portfolio.trades.records_readable)

# 绘图
portfolio[stock_code].plot().show()
```

---

## 最佳实践

### 1. 数据获取原则

**批量获取优于单个查询**
```python
# 好的做法：一次获取多只股票
data = tq.get_market_data(stock_list=['600519.SH', '000001.SZ', '600036.SH'], ...)

# 避免：多次单个查询
for stock in stock_list:
    data = tq.get_market_data(stock_list=[stock], ...)  # 效率低
```

**合理使用缓存刷新**
```python
# 盘前刷新一次即可
tq.refresh_cache(market='AG', force=False)

# 避免频繁刷新
# tq.refresh_cache(market='AG', force=True)  # 不要在循环中调用
```

### 2. 策略开发建议

**信号移位避免未来函数**
```python
# 错误：使用当日数据产生信号
entries = close_df > ma_df  # 这会在当日产生信号

# 正确：信号移位到下一日
entries = (close_df > ma_df).shift(1)  # 次日才能执行
```

**使用复权数据计算指标**
```python
# 好的做法：前复权
df = tq.get_market_data(..., dividend_type='front')

# 避免使用不复权数据（除权除息会跳空）
# df = tq.get_market_data(..., dividend_type='none')
```

### 3. 性能优化技巧

**使用DataFrame批量计算**
```python
# 好的做法：向量化计算
ma5 = close_df.rolling(5).mean()
ma10 = close_df.rolling(10).mean()

# 避免：逐个股票循环
# for stock in stock_list:
#     ma5[stock] = close_df[stock].rolling(5).mean()
```

**合理订阅实时行情**
```python
# 分批订阅，避免单次订阅过多
batch_size = 50
for i in range(0, len(stock_list), batch_size):
    batch = stock_list[i:i+batch_size]
    tq.subscribe_hq(stock_list=batch, callback=callback)
```

### 4. 错误处理

**检查返回值有效性**
```python
# 获取行情后检查
quote = tq.get_full_tick('600519.SH')
if quote and quote.get('ErrorId') == '0':
    price = float(quote['Now'])
else:
    print("获取行情失败")
```

**异常捕获**
```python
try:
    result = tq.subscribe_hq(stock_list=stock_list, callback=callback)
    if not result:
        raise Exception("订阅失败")
except Exception as e:
    print(f"订阅异常：{e}")
```

### 5. 风险管理

**设置止损止盈**
```python
# 在策略中加入止损逻辑
stop_loss = -0.05  # 5%止损
take_profit = 0.15  # 15%止盈

for trade in portfolio.trades.records:
    if trade['pnl'] < stop_loss:
        # 执行止损
        pass
    elif trade['pnl'] > take_profit:
        # 执行止盈
        pass
```

**控制仓位**
```python
# 分仓建仓
position_size = init_cash * 0.2  # 单只股票不超过20%
max_positions = 5  # 最多同时持仓5只
```

---

## 常见问题

### Q1: 为什么获取不到数据？

**检查清单**：
1. 确认已调用 `tq.initialize(__file__)`
2. 确认通达信客户端已启动
3. 确认股票代码格式正确（如 600519.SH）
4. 尝试刷新缓存：`tq.refresh_cache(market='AG', force=True)`

### Q2: 订阅行情为什么没有回调？

**可能原因**：
1. 股票代码不在交易时段
2. 回调函数定义有误
3. 订阅失败（检查返回值）

**解决方法**：
```python
# 检查订阅结果
result = tq.subscribe_hq(stock_list=['600519.SH'], callback=callback)
if result:
    print("订阅成功")
else:
    print("订阅失败")
```

### Q3: 如何处理除权除息？

**使用复权数据**：
```python
# 计算技术指标时使用前复权
df = tq.get_market_data(..., dividend_type='front')

# 回测时用未复权计算收益
df_real = tq.get_market_data(..., dividend_type='none')
```

### Q4: 实盘交易注意事项？

**重要提醒**：
1. 先用模拟账户充分测试
2. 下单前检查账户可用资金
3. 设置合理的止损止盈
4. 监控订单执行状态
5. 避免在开盘/收盘剧烈波动时下单

### Q5: 性能优化建议？

**提升性能**：
1. 批量获取数据而非单个查询
2. 使用向量化运算而非循环
3. 合理使用缓存，避免重复刷新
4. 分批订阅大量股票
5. 及时取消不需要的订阅

### Q6: 常用代码速查

```python
# 初始化
tq.initialize(__file__)

# 获取K线
tq.get_market_data(stock_list=['600519.SH'], period='1d', count=100)

# 获取快照
tq.get_full_tick(['600519.SH'])

# 订阅行情
tq.subscribe_hq(['600519.SH'], callback)

# 取消订阅
tq.unsubscribe_hq(['600519.SH'])

# 发送预警
tq.send_warn(stock_list=['600519.SH'], time_list=['20241215140000'],
             price_list=['1850'], count=1)

# 查询资产
account = tq.stock_account('account', 'STOCK')
tq.query_stock_asset(account)

# 下单
tq.order_stock(account, '600519.SH', 0, 100, 0, 1850.0)

# 撤单
tq.cancel_order_stock(account, '600519.SH', '12345')

# 创建板块
tq.create_sector('CODE', '名称')

# 添加股票
tq.send_user_block('CODE', ['600519.SH'])

# 刷新缓存
tq.refresh_cache('AG', False)

# 关闭连接
tq.close()
```

---

## 常用字段参考

### K线数据字段

- `Date` - 日期
- `Time` - 时间
- `Open` - 开盘价
- `High` - 最高价
- `Low` - 最低价
- `Close` - 收盘价
- `Volume` - 成交量
- `Amount` - 成交额

### 快照数据字段

- `Code` - 代码
- `Name` - 名称
- `Now` - 最新价
- `LastClose` - 昨收
- `Open` - 今开
- `High` - 最高
- `Low` - 最低
- `Volume` - 成交量
- `Amount` - 成交额

### 主要财务字段

- `TotalAssets` - 总资产
- `TotalLiability` - 总负债
- `NetProfit` - 净利润
- `EPS` - 每股收益
- `ROE` - 净资产收益率
- `OperatingRevenue` - 营业收入
- `DebtToAssetRatio` - 资产负债率
- `CurrentRatio` - 流动比率
- `QuickRatio` - 速动比率

---

## 参考资源

- TdxQuant官方文档
- 通达信客户端使用手册
- Python量化交易相关库
