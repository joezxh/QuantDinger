以下按层梳理每个数据源/提供者返回的数据结构（字段名 → 类型 → 含义）。

---

## 一、Data Sources — K 线数据结构

### 1.1 `BaseDataSource`（所有数据源统一格式）

**`get_kline(symbol, timeframe, limit, before_time)`**

```json
[
  {
    "time":   int,    // Unix 秒时间戳（UTC）
    "open":   float,  // 开盘价
    "high":   float,  // 最高价
    "low":    float,  // 最低价
    "close":  float,  // 收盘价
    "volume": float   // 成交量
  }
]
```

**`get_ticker(symbol)`** — 格式因数据源而异，各子类如下：

---

### 1.2 CryptoDataSource（CCXT）

```json
// CCXT fetch_ticker 原生格式
{
  "symbol":         str,    // "BTC/USDT"
  "last":           float,  // 最新价
  "bid":            float,  // 买一价
  "ask":            float,  // 卖一价
  "high":           float,  // 24h 最高
  "low":            float,  // 24h 最低
  "open":           float,  // 24h 开盘
  "close":          float,  // 24h 收盘
  "baseVolume":     float,  // 基础币成交量
  "quoteVolume":    float,  // 报价币成交量
  "change":         float,  // 涨跌额
  "percentage":     float,  // 涨跌幅(%)
  "previousClose":  float   // 昨收价
}
```

**配置**：`CCXT_DEFAULT_EXCHANGE`（默认 `coinbase`）、`CCXT_TIMEOUT`、代理环境变量

---

### 1.3 USStockDataSource（yfinance + Finnhub）

```json
{
  "last":           float,  // 当前价格
  "change":         float,  // 涨跌额
  "changePercent":  float,  // 涨跌幅(%)
  "high":           float,  // 日内最高
  "low":            float,  // 日内最低
  "open":           float,  // 开盘价
  "previousClose":  float   // 昨收价
}
```

**配置**：`FINNHUB_API_KEY`（可选，ticker 主源，无则 yfinance）

---

### 1.4 CNStockDataSource（TwelveData → 腾讯 → yfinance → AkShare）

```json
{
  "last":           float,  // 最新价
  "change":         float,  // 涨跌额
  "changePercent":  float,  // 涨跌幅(%)
  "high":           float,  // 日内最高
  "low":            float,  // 日内最低
  "open":           float,  // 开盘价
  "previousClose":  float,  // 昨收价
  "name":           str,    // 股票名称
  "symbol":         str     // 腾讯代码（如 SH600519）
}
```

**配置**：`TWELVE_DATA_API_KEY`（推荐，主源）

---

### 1.5 HKStockDataSource（格式同上）

```json
{
  "last":           float,
  "change":         float,
  "changePercent":  float,
  "high":           float,
  "low":            float,
  "open":           float,
  "previousClose":  float,
  "name":           str,
  "symbol":         str     // 如 HK00700
}
```

**配置**：`TWELVE_DATA_API_KEY`（推荐，主源）

---

### 1.6 ForexDataSource（TwelveData → Tiingo → yfinance）

```json
// TwelveData / yfinance 格式
{
  "last":           float,  // 最新汇率（四舍五入到 5 位小数）
  "change":         float,
  "changePercent":  float,
  "previousClose":  float,
  "symbol":         str
}

// Tiingo 格式（多了买/卖价）
{
  "last":           float,
  "bid":            float,
  "ask":            float,
  "change":         float,
  "changePercent":  float,
  "previousClose":  float,
  "symbol":         str
}
```

**配置**：`TWELVE_DATA_API_KEY`（主）、`TIINGO_API_KEY`（备选）

---

### 1.7 FuturesDataSource（TwelveData / yfinance / Tiingo / CCXT）

```json
// 传统期货（TwelveData / yfinance）
{
  "symbol":         str,    // e.g. "GC=F"
  "last":           float,
  "change":         float,
  "changePercent":  float,
  "previousClose":  float
}

// 传统期货贵金属（Tiingo 备选）
{
  "symbol":         str,
  "last":           float    // 仅返回最新价
}

// 加密货币期货（CCXT Binance Futures）
// 同 CryptoDataSource 的 CCXT fetch_ticker 格式
```

**配置**：`TWELVE_DATA_API_KEY`、`TIINGO_API_KEY`、`CCXT_DEFAULT_EXCHANGE`

---

### 1.8 PolymarketDataSource

**`get_trending_markets(category, limit)`**

```json
// 以 market_id + question + current_probability 为核心
[
  {
    "market_id":            str,    // Polymarket 市场 ID
    "question":             str,    // 预测问题标题
    "current_probability":  float,  // 当前 YES 概率 (0~1)
    // + 更多原始字段
  }
]
```

**配置**：无需 API Key，使用 `https://gamma-api.polymarket.com` 等公开端点

---

### 1.9 CN/HK 基本面数据（cn_hk_fundamentals.py）

**`fetch_twelvedata_fundamental(tencent_code, is_hk)`**

```json
{
  "source":         "twelvedata",
  "market_cap":     float|null,  // 市值
  "pe_ratio":       float|null,  // 市盈率 (TTM)
  "forward_pe":     float|null,  // 远期市盈率
  "pb_ratio":       float|null,  // 市净率 (MRQ)
  "ps_ratio":       float|null,  // 市销率 (TTM)
  "peg":            float|null,  // PEG
  "enterprise_value": float|null, // 企业价值
  "profit_margin":    float|null, // 利润率
  "gross_margin":     float|null, // 毛利率
  "operating_margin": float|null, // 营业利润率
  "roe":              float|null, // ROE
  "roa":              float|null, // ROA
  "revenue_growth":   float|null, // 营收增长率(%)
  "earnings_growth":  float|null, // 盈利增长率(%)
  "revenue_ttm":      float|null, // TTM 营收
  "ebitda":           float|null,
  "eps":              float|null, // 稀释每股收益 (TTM)
  "debt_to_equity":   float|null, // 负债权益比
  "current_ratio":    float|null, // 流动比率
  "total_debt":       float|null, // 总负债
  "total_cash":       float|null, // 总现金
  "operating_cash_flow":    float|null, // 经营现金流 (TTM)
  "free_cash_flow":         float|null, // 自由现金流 (TTM)
  "total_shares":           float|null, // 总股本
  "float_shares":           float|null, // 流通股本
  "52w_high":               float|null, // 52 周最高
  "52w_low":                float|null, // 52 周最低
  "beta":                   float|null,
  "dividend_yield":         float|null, // 股息率
  "dividend_rate":          float|null, // 股息额
  "financial_statements": {            // 完整三张报表（可选，需额外 fetch_twelvedata_statements）
    "income_statement":  { ... },
    "balance_sheet":     { ... },
    "cash_flow":         { ... }
  }
}
```

**`fetch_cn_fundamental_akshare(tencent_code)`**（A 股备选）
```json
{
  "source":          "akshare_em",
  "market_cap":      float|null,  // 总市值
  "float_market_cap": float|null, // 流通市值
  "industry":        str|null,    // 行业
  "total_shares":    float|null,  // 总股本
  "float_shares":    float|null,  // 流通股
  "pe_ratio":        float|null,  // 市盈率-TTM
  "pb_ratio":        float|null,  // 市净率-MRQ
  "ps_ratio":        float|null,  // 市销率-TTM
  "peg":             float|null   // PEG
}
```

**`fetch_hk_fundamental_akshare(tencent_code)`**（港股备选）
```json
{
  "source":          "akshare_em",
  "pe_ratio":        float|null,
  "pb_ratio":        float|null,
  "eps":             float|null,
  "roe":             float|null,
  "profit_margin":   float|null,
  "market_cap":      float|null,
  "dividend_yield":  float|null
}
```

**配置**：`TWELVE_DATA_API_KEY`（推荐，主源）

---

## 二、Data Providers — 市场概览数据结构

### 2.1 crypto.py

**`fetch_crypto_prices()`** — 加密货币价格列表（带三级降级：CCXT → yfinance → CoinGecko）

```json
[
  {
    "symbol":      str,    // "BTC"
    "name":        str,    // "Bitcoin"
    "price":       float,  // 当前价格 (USD)
    "change_24h":  float,  // 24h 涨跌幅(%)
    "change_7d":   float,  // 7日涨跌幅(%)
    "market_cap":  float,  // 市值
    "volume_24h":  float,  // 24h 成交量
    "image":       str,    // 币种图标 URL
    "category":    "crypto"
  }
]
```
覆盖 15 个主流币：BTC, ETH, BNB, SOL, XRP, ADA, DOGE, AVAX, DOT, POL, LINK, LTC, ATOM, XLM

**`fetch_crypto_heatmap_coingecko()` / `fetch_crypto_heatmap_coincap()`**

```json
// 同 fetch_crypto_prices 格式（不含 change_7d）
[
  {
    "symbol":      str,
    "name":        str,
    "price":       float,
    "change_24h":  float,
    "market_cap":  float,
    "volume_24h":  float,
    "image":       str,   // CoinGecko 版本有；CoinCap 版本为 ""
    "category":    "crypto"
  }
]
```

---

### 2.2 forex.py

**`fetch_forex_pairs()`** — 主要货币对概览（8个 pair）

```json
[
  {
    "symbol":    str,    // "EUR/USD"
    "name":      str,    // "EUR/USD"
    "name_cn":   str,    // "欧元/美元"
    "name_en":   str,    // "EUR/USD"
    "price":     float,  // 汇率（四舍五入到 5 位小数）
    "change":    float,  // 涨跌幅(%)
    "base":      str,    // "EUR"
    "quote":     str,    // "USD"
    "category":  "forex"
  }
]
```
覆盖：EUR/USD, GBP/USD, USD/JPY, USD/CNH, AUD/USD, USD/CAD, USD/CHF, NZD/USD

---

### 2.3 indices.py

**`fetch_stock_indices()`** — 全球股指（10 个）

```json
[
  {
    "symbol":    str,    // "^GSPC"
    "name_cn":   str,    // "标普500"
    "name_en":   str,    // "S&P 500"
    "price":     float,  // 指数点数
    "change":    float,  // 涨跌幅(%)
    "region":    str,    // "US" / "EU" / "JP" / "KR" / "AU" / "IN"
    "flag":      str,    // 国旗 emoji
    "lat":       float,  // 纬度（地图展示用）
    "lng":       float,  // 经度（地图展示用）
    "category":  "index"
  }
]
```
覆盖：S&P 500, 道琼斯, NASDAQ, DAX, FTSE 100, CAC 40, 日经 225, KOSPI, ASX 200, SENSEX

---

### 2.4 commodities.py

**`fetch_commodities()`** — 大宗商品价格（6 个品种）

```json
[
  {
    "symbol":    str,    // "GC=F"
    "name_cn":   str,    // "黄金"
    "name_en":   str,    // "Gold"
    "price":     float,  // 价格 (USD)
    "change":    float,  // 涨跌幅(%)
    "unit":      str,    // "USD/oz" / "USD/bbl" / "USD/lb" / "USD/MMBtu"
    "category":  "commodity"
  }
]
```
覆盖：黄金(GC)、白银(SI)、WTI原油(CL)、布伦特(BZ)、铜(HG)、天然气(NG)

---

### 2.5 heatmap.py

**`generate_heatmap_data()`** — 市场热力图聚合

```json
{
  "crypto": [
    {
      "name":       str,    // 币种符号 "BTC"
      "fullName":   str,    // 全名 "Bitcoin"
      "value":      float,  // 24h 涨跌幅(%)
      "marketCap":  float,  // 市值
      "volume":     float,  // 成交量
      "price":      float   // 价格
    }
  ],
  "sectors": [
    {
      "name":     str,    // "科技"
      "name_en":  str,    // "Technology"
      "etf":      str,    // "XLK"
      "value":    float,  // ETF 涨跌幅(%)
      "stocks":   [str]   // 代表股列表 ["AAPL","MSFT","GOOGL","NVDA","META"]
    }
  ],
  "forex": [
    {
      "name":     str,    // "EUR/USD"
      "name_cn":  str,    // "欧元/美元"
      "name_en":  str,    // "EUR/USD"
      "value":    float,  // 涨跌幅(%)
      "price":    float   // 汇率
    }
  ],
  "commodities": [
    {
      "name":     str,    // "黄金"
      "name_cn":  str,    // "黄金"
      "name_en":  str,    // "Gold"
      "value":    float,  // 涨跌幅(%)
      "price":    float,  // 价格
      "unit":     str     // "USD/oz"
    }
  ],
  "indices": [
    {
      "symbol":   str,    // "^GSPC"
      "name":     str,    // "标普500"
      "name_cn":  str,    // "标普500"
      "name_en":  str,    // "S&P 500"
      "region":   str,    // "US"
      "value":    float,  // 涨跌幅(%)
      "price":    float,  // 点数
      "flag":     str     // 国旗 emoji
    }
  ]
}
```

行业板块覆盖 10 个：科技(XLK)、金融(XLF)、医疗(XLV)、消费(XLY)、能源(XLE)、工业(XLI)、材料(XLB)、公用事业(XLU)、房地产(XLRE)、通信(XLC)

---

### 2.6 news.py

**`fetch_financial_news(lang)`**

```json
{
  "cn": [
    {
      "title":      str,  // 标题
      "link":       str,  // 原文链接
      "snippet":    str,  // 摘要
      "source":     str,  // 来源
      "published":  str,  // 发布时间
      "category":   str,  // 搜索分类（"加密货币新闻" / "美联储利率" 等）
      "lang":       "cn"
    }
  ],
  "en": [ /* 同上, lang: "en" */ ]
}
```

**`get_economic_calendar()`**

```json
[
  {
    "id":              int,    // 事件 ID
    "name":            str,    // "美国非农就业数据"
    "name_en":         str,    // "US Non-Farm Payrolls"
    "country":         str,    // "US" / "EU" / "JP" / "UK" / "INTL"
    "date":            str,    // "2026-04-25"
    "time":            str,    // "08:30"
    "importance":      str,    // "high" / "medium"
    "actual":          str|null, // 实际值（已发布则模拟生成）
    "forecast":        str,    // 预期值 "180K"
    "previous":        str,    // 前值 "175K"
    "impact_if_above": str,    // "bullish" / "bearish"
    "impact_if_below": str,
    "impact_desc":     str,    // 中文影响说明
    "impact_desc_en":  str,    // 英文影响说明
    "expected_impact": str,    // 预期影响方向
    "actual_impact":   str|null, // 实际影响
    "is_released":     bool    // 是否已发布
  }
]
```

覆盖 9 类事件：非农、FOMC、CPI、ECB、BoJ、初请、BoE、零售销售、OPEC

---

### 2.7 sentiment.py — 市场情绪指标

**`fetch_fear_greed_index()`**

```json
{
  "value":           int,    // 0~100 恐惧贪婪指数
  "classification":  str,    // "Fear" / "Greed" / "Neutral"
  "timestamp":       int,    // Unix 秒
  "source":          "alternative.me"
}
```

**`fetch_vix()`**

```json
{
  "value":             float,  // VIX 点数
  "change":            float,  // 涨跌幅(%)
  "level":             str,    // "very_low" / "low" / "moderate" / "high" / "very_high"
  "interpretation":    str,    // "低波动 - 市场稳定"
  "interpretation_en": str     // "Low - Market Stable"
}
```

**`fetch_dollar_index()`**

```json
{
  "value":             float,  // DXY 点数
  "change":            float,
  "level":             str,    // "strong" / "moderate_strong" / "neutral" / "moderate_weak" / "weak"
  "interpretation":    str,    // "美元偏强 - 关注资金流向"
  "interpretation_en": str
}
```

**`fetch_yield_curve()`**

```json
{
  "yield_10y":         float,  // 10 年期收益率(%)
  "yield_2y":          float,  // 2 年期收益率(%)
  "spread":            float,  // 利差(%)
  "change":            float,  // 利差变动
  "level":             str,    // "deeply_inverted" / "inverted" / "flat" / "normal" / "steep"
  "signal":            str,    // "bullish" / "bearish" / "neutral"
  "interpretation":    str,
  "interpretation_en": str
}
```

**`fetch_vxn()`**

```json
{
  "value":             float,  // VXN 点数
  "change":            float,
  "level":             str,
  "interpretation":    str,
  "interpretation_en": str
}
```

**`fetch_gvz()`**

```json
{
  "value":             float,  // GVZ 点数
  "change":            float,
  "level":             str,
  "interpretation":    str,
  "interpretation_en": str
}
```

**`fetch_put_call_ratio()`**

```json
{
  "value":             float,  // VIX / VIX3M 比率
  "vix":               float,  // VIX
  "vix3m":             float,  // 3 个月 VIX
  "change":            float,
  "level":             str,
  "signal":            str,
  "interpretation":    str,
  "interpretation_en": str
}
```

---

### 2.8 opportunities.py — 交易机会扫描

**`fetch_stock_opportunity_prices()`** — 美股机会价格列表

```json
[
  {
    "symbol":  str,    // "AAPL"
    "name":    str,    // "Apple"
    "price":   float,  // 当前价格
    "change":  float   // 日涨跌幅(%)
  }
]
```
覆盖 15 只：AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META, NFLX, AMD, CRM, COIN, BABA, NIO, PLTR, INTC

**`fetch_local_stock_opportunity_prices(market)`** — A/港股机会价格

```json
[
  {
    "symbol":  str,    // "600519" / "00700"
    "name":    str,    // "贵州茅台" / "腾讯控股"
    "price":   float,
    "change":  float,
    "market":  str     // "CNStock" / "HKStock"
  }
]
```
CNStock 覆盖 20 只热门 A 股，HKStock 覆盖 15 只热门港股

**`analyze_opportunities_*()`** 各扫描函数生成的信号记录：

```json
// 通用格式
{
  "symbol":      str,    // 标的代码
  "name":        str,    // 标的名称
  "price":       float,  // 当前价格
  "change_24h":  float,  // 24h/日涨跌幅(%)
  "change_7d":   float,  // 7d 涨跌幅(仅 Crypto 有)
  "signal":      str,    // "overbought" / "oversold" / "bullish_momentum" / "bearish_momentum" / "consolidation" / "prediction_opportunity"
  "strength":    str,    // "strong" / "medium" / "weak"
  "reason":      str,    // 中文信号解读
  "impact":      str,    // "bullish" / "bearish" / "neutral"
  "market":      str,    // "Crypto" / "USStock" / "CNStock" / "HKStock" / "Forex" / "PredictionMarket"
  "timestamp":   int,    // Unix 秒
  // Polymarket 额外字段
  "market_id":   str,    // 预测市场 ID
  "ai_analysis": {
    "predicted_probability":  float,
    "recommendation":         str,  // "YES" / "NO" / "HOLD"
    "confidence_score":       float,
    "opportunity_score":      float
  }
}
```

---

### 2.9 adanos_sentiment.py — Adanos 美股情感

**`fetch_adanos_market_sentiment(tickers, source, days)`**

```json
{
  "enabled":   bool,         // false 表示未配置 API Key
  "provider":  "adanos",
  "source":    str,          // "reddit" / "x" / "news" / "polymarket"
  "days":      int,          // 回溯天数
  "tickers":   [str],        // 请求的 ticker 列表
  "stocks": [
    {
      "ticker":          str,         // "AAPL"
      "company_name":    str|null,    // "Apple Inc."
      "source":          str,         // "reddit"
      "sentiment_score": float|null,  // 情感分数
      "buzz_score":      float|null,  // 热度分数
      "bullish_pct":     float|null,  // 看多比例(%)
      "bearish_pct":     float|null,  // 看空比例(%)
      "mentions":        int|null,    // 提及次数
      "source_count":    int|null,    // 来源数量
      "subreddit_count": int|null,    // subreddit 数量
      "unique_posts":    int|null,    // 独立帖子数
      "unique_tweets":   int|null,    // 独立推文数
      "trade_count":     int|null,    // 交易笔数
      "market_count":    int|null,    // 市场数量(Polymarket)
      "unique_traders":  int|null,    // 独立交易者数
      "total_upvotes":   int|null,    // 总点赞数
      "total_liquidity": float|null,  // 总流动性
      "trend":           str|null,    // 趋势
      "trend_history":   []           // 趋势历史
    }
  ],
  "error":     str|null      // 错误信息（无 API Key 时给出说明）
}
```

**配置**：`ADANOS_API_KEY`（可选，无则 `enabled=false`）、`ADANOS_SENTIMENT_SOURCE`（默认 `reddit`）、`ADANOS_API_BASE_URL`



全部完成，3 个文件已创建/修改，无语法错误。以下是设计概要：

---

## 设计说明

### 表 1：`qd_data_source_configs` — 数据源访问配置

| 字段 | 类型 | 说明 |
|---|---|---|
| `source_code` | `VARCHAR(80) UNIQUE` | 唯一标识，如 `crypto_ccxt`、`forex_twelvedata` |
| `source_name` | `VARCHAR(150)` | 可读名称 |
| `layer` | `VARCHAR(30)` | 分层标签：`data_source` / `data_provider` / `fundamental` / `sentiment` / `collector` |
| `market_categories` | `ARRAY[VARCHAR(50)]` | 市场标签，如 `{"Crypto","USStock","Forex"}` |
| `enabled` | `BOOLEAN` | 全局启用/禁用 |
| **`config_json`** | **`JSONB`** | **核心字段**，存储灵活键值对： |
|  |  | `api_key_env`: 该源使用的环境变量名（非密钥原文） |
|  |  | `api_key_required`: 是否需要 API Key |
|  |  | `base_url`: 接口基地址 |
|  |  | `timeout_sec` / `retry_count` / `rate_limit_per_min` ... |
| `dependencies` | `ARRAY[VARCHAR(80)]` | 依赖的其他 source_code |
| `notes` | `TEXT` | 备注 |

> **密钥安全**：实际密钥值仅存在于环境变量/`.env` 文件中，数据库中只存环境变量名。

### 表 2：`qd_data_source_datasets` — 数据集返回结构

| 字段 | 类型 | 说明 |
|---|---|---|
| `source_id` | `FK → qd_data_source_configs.id` | 所属数据源 |
| `dataset_code` | `VARCHAR(80) UNIQUE` | 唯一标识，如 `crypto_prices` |
| `dataset_name` | `VARCHAR(150)` | 可读名称，如 "加密货币价格列表" |
| `function_name` | `VARCHAR(100)` | 对应函数，如 `fetch_crypto_prices()` |
| `return_type` | `VARCHAR(30)` | `list[dict]` / `dict` / `list` |
| **`fields_schema`** | **`JSONB`** | **核心字段**，字段定义数组： |
|  |  | `[{"name":"symbol","type":"str","description":"币种符号","nullable":false,"example":"BTC"}, ...]` |
| **`sample_output`** | **`JSONB`** | **样本数据**，1~2 条记录 |
| `coverage_text` | `TEXT` | 覆盖范围说明 |
| `source_file_ref` | `VARCHAR(255)` | 源文件路径引用 |

### 表关系

```
qd_data_source_configs (1) ──── (N) qd_data_source_datasets
       └─ config_json                   └─ fields_schema
       └─ market_categories             └─ sample_output
```

### 运行迁移

```
python backend_api_python/run_migration.py
```

或手动：
```
cd backend_api_python
alembic upgrade head
```