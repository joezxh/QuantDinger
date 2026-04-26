

**当前可采集/查询的完整数据源清单**，分为两层结构：**Data Sources**（K线/实时报价层）和 **Data Providers**（市场概览层）。

---

## 一、Data Sources — K线数据层

通过 `DataSourceFactory.get_source(market)` 统一访问，支持 **K 线** (`get_kline`) 和 **实时报价** (`get_ticker`)。

| 市场 | 工厂 Key | 数据源实现 | 数据内容范围 | 底层 API / 备选降级 |
|---|---|---|---|---|
| **加密货币** | `Crypto` | [CryptoDataSource](file:///d:\projects\QuantDinger\backend_api_python\app\data_sources\crypto.py) | 任意交易对的 OHLCV K 线 + 实时报价 | **CCXT**（默认交易所 Coinbase，可配置 Binance/OKX/Bybit 等） |
| **美股** | `USStock` | [USStockDataSource](file:///d:\projects\QuantDinger\backend_api_python\app\data_sources\us_stock.py) | 任意美股的 OHLCV K 线 + 实时报价 | **yfinance**（主）→ **Finnhub**（Ticker 备选） |
| **A股** | `CNStock` | [CNStockDataSource](file:///d:\projects\QuantDinger\backend_api_python\app\data_sources\cn_stock.py) | 任意 A 股的 OHLCV K 线 + 实时报价 | **Twelve Data** → **腾讯 fqkline**（日/周）→ **yfinance** → **AkShare** |
| **港股** | `HKStock` | [HKStockDataSource](file:///d:\projects\QuantDinger\backend_api_python\app\data_sources\hk_stock.py) | 任意港股的 OHLCV K 线 + 实时报价 | **Twelve Data** → **腾讯 fqkline**（日/周）→ **yfinance** → **AkShare** |
| **外汇** | `Forex` | [ForexDataSource](file:///d:\projects\QuantDinger\backend_api_python\app\data_sources\forex.py) | 14 个货币对（EUR/USD, XAU/USD 等）OHLCV + 实时报价 | **Twelve Data** → **Tiingo** → **yfinance** |
| **传统期货** | `Futures` | [FuturesDataSource](file:///d:\projects\QuantDinger\backend_api_python\app\data_sources\futures.py) | GC(黄金), SI(白银), CL(原油), NG(天然气), ZC(玉米), ZW(小麦) 等 | **Twelve Data** → **yfinance** → **Tiingo**(贵金属) |
| **加密货币期货** | `Futures`（同上） | [FuturesDataSource](file:///d:\projects\QuantDinger\backend_api_python\app\data_sources\futures.py) | 永续合约 K 线（如 BTC/USDT 期货） | **CCXT**(Binance Futures) |
| **港股/日股基础面** | — | [cn_hk_fundamentals.py](file:///d:\projects\QuantDinger\backend_api_python\app\data_sources\cn_hk_fundamentals.py) | PE/PB/PS、市值、利润表、资产负债表、现金流量表、ROE、52周高低等 | **Twelve Data**(/statistics, /profile, /earnings) → **AkShare**(东方财富) |
| **预测市场** | — | [PolymarketDataSource](file:///d:\projects\QuantDinger\backend_api_python\app\data_sources\polymarket.py) | Polymarket 热门市场、价格、概率、交易记录、持仓等 | **Polymarket Gamma/CLOB/Data API**（公开，无需认证） |
| **腾讯行情辅助** | — | [tencent.py](file:///d:\projects\QuantDinger\backend_api_python\app\data_sources\tencent.py) | A/港股实时报价 + 日线/周线 fqkline | **qt.gtimg.cn** / **web.ifzq.gtimg.cn**（免费，无需 API Key） |

**支持的时间周期**：`1m`、`5m`、`15m`、`30m`、`1H`、`4H`、`1D`、`1W`

---

## 二、Data Providers — 市场概览层

通过上层服务（如路由 `/api/market/...` 调用），聚合多种数据源生成面向仪表盘/分析的"二次加工数据"。

| 模块 | 数据集 | 数据集内容 | 底层依赖 |
|---|---|---|---|
| [crypto.py](file:///d:\projects\QuantDinger\backend_api_python\app\data_providers\crypto.py) | **加密货币行情 & 热力图** | BTC/ETH/SOL/BNB… 等 15 个主流币的价格、24h/7d 涨跌幅、市值、成交量；CoinGecko/CoinCap 热力图 | CCXT → yfinance → CoinGecko API ；CoinCap API |
| [forex.py](file:///d:\projects\QuantDinger\backend_api_python\app\data_providers\forex.py) | **外汇概览** | EUR/USD、GBP/USD、USD/JPY、USD/CNH 等 8 个主要货币对的实时汇率、涨跌幅 | Twelve Data → yfinance → Tiingo |
| [indices.py](file:///d:\projects\QuantDinger\backend_api_python\app\data_providers\indices.py) | **全球股指** | S&P 500、道琼斯、纳斯达克、德国DAX、富时100、日经225、KOSPI、ASX200、SENSEX 共 10 个 | yfinance |
| [commodities.py](file:///d:\projects\QuantDinger\backend_api_python\app\data_providers\commodities.py) | **大宗商品价格** | 黄金(GC)、白银(SI)、原油 WTI(CL)、布伦特(BZ)、铜(HG)、天然气(NG) | Twelve Data → yfinance → Tiingo(金银) |
| [heatmap.py](file:///d:\projects\QuantDinger\backend_api_python\app\data_providers\heatmap.py) | **市场热力图** | 聚合 5 类数据：crypto, forex, commodities, sectors(10 个行业ETF), indices | 从其他 Provider 获取 + yfinance(行业ETF) |
| [news.py](file:///d:\projects\QuantDinger\backend_api_python\app\data_providers\news.py) | **金融新闻 & 经济日历** | 中/英文财经新闻（分类查询）；宏观经济事件日历（非农、FOMC、CPI 等 9 类预设事件） | SearchService（Google 搜索）；预设模板事件 |
| [sentiment.py](file:///d:\projects\QuantDinger\backend_api_python\app\data_providers\sentiment.py) | **市场情绪指标** | 恐惧贪婪指数(VIX)、美元指数(DXY)、国债收益率曲线(10Y-2Y)、VXN、GVZ、看跌/看涨比(VIX期限结构) | alternative.me、yfinance、AkShare |
| [opportunities.py](file:///d:\projects\QuantDinger\backend_api_python\app\data_providers\opportunities.py) | **交易机会扫描** | 跨市场扫描：加密超买/超卖信号、美股/港股/A 股异动、外汇波动机会、预测市场套利 | 聚合其他 Provider + yfinance + Polymarket + DataSource |
| [adanos_sentiment.py](file:///d:\projects\QuantDinger\backend_api_python\app\data_providers\adanos_sentiment.py) | **Adanos 市场情绪** | 美股个股情感评分（Reddit/X/News/Polymarket 来源的可选情绪数据） | **Adanos API**（需配置 `ADANOS_API_KEY`，可选） |

---

## 三、采集器系统（Collectors）

另有数据采集器框架用于自动抓取和持久化：

| 模块 | 用途 |
|---|---|
| [collectors/registry.py](file:///d:\projects\QuantDinger\backend_api_python\app\collectors\registry.py) | 采集器注册中心，当前注册`market_data` |
| [collectors/base.py](file:///d:\projects\QuantDinger\backend_api_python\app\collectors\base.py) | 采集器基类 |
| [collectors/graph_pipeline.py](file:///d:\projects\QuantDinger\backend_api_python\app\collectors\graph_pipeline.py) | 图谱知识采集管道 |
| [collectors/dedup.py](file:///d:\projects\QuantDinger\backend_api_python\app\collectors\dedup.py) | 数据去重 |
| [collectors/storage.py](file:///d:\projects\QuantDinger\backend_api_python\app\collectors\storage.py) | 数据持久化存储 |

---

## 四、汇总速览

| 大类 | 子类 | 覆盖数量 | 主要 API/库 |
|---|---|---|---|
| **加密货币** | K 线 + 报价 + 热力图 + 期货 | 15+ 交易对 | CCXT、CoinGecko、CoinCap |
| **美股** | K 线 + 报价 + 机会扫描 | 15+ 热门股 | yfinance、Finnhub |
| **A 股** | K 线 + 报价 + 基本面 + 财务数据 | 20+ 热门股 | Twelve Data、腾讯、yfinance、AkShare(东方财富) |
| **港股** | K 线 + 报价 + 基本面 + 财务数据 | 15+ 热门股 | Twelve Data、腾讯、yfinance、AkShare(东方财富) |
| **外汇** | K 线 + 报价 + 概览 | 8 个主要货币对 | Twelve Data、Tiingo、yfinance |
| **大宗商品** | K 线 + 报价 + 价格 | 6 个品种 | Twelve Data、yfinance、Tiingo |
| **全球股指** | 实时价格 | 10 个指数 | yfinance |
| **预测市场** | 热门市场 + AI 分析 | 20+ 市场 | Polymarket API |
| **新闻 & 经济日历** | 财经新闻、经济事件 | 6 类中英文新闻 + 9 类经济事件 | SearchService（Google）、预设模板 |
| **市场情绪** | VIX、DXY、Yield Curve、Fear&Greed、VXN、GVZ、PCR | 7 个指标 | alternative.me、yfinance、AkShare |
| **交易机会** | 跨市场异动信号 | 全市场扫描 | 聚合所有上层 Provider |
| **Adanos 情绪** | US 个股情感分析 | 最多 20 个 ticker | Adanos API（可选） |


**补全所有数据源的配置参数（API Key / Base URL / 相关环境变量）**：

---

## 一、Data Sources — K线/报价数据层

| 数据源 | API Key / 配置项 | 环境变量 | 默认值 | 是否必需 | Base URL |
|---|---|---|---|---|---|
| **CryptoDataSource** (CCXT) | 默认交易所 | `CCXT_DEFAULT_EXCHANGE` | `coinbase` | 否 | 交易所原生 API |
| | 超时(ms) | `CCXT_TIMEOUT` | `10000` | 否 | — |
| | 代理 | `PROXY_URL` / `HTTPS_PROXY` / `HTTP_PROXY` | 空 | 否 | — |
| **USStockDataSource** (yfinance) | 无（免费公开API） | — | — | **不需要** | — |
| | **Finnhub**（Ticker 备选）API Key | `FINNHUB_API_KEY` | 空 | 否（无则降级 yfinance） | `https://finnhub.io/api/v1` |
| **CNStockDataSource** (A股) | **Twelve Data** API Key（付费推荐） | `TWELVE_DATA_API_KEY` | 空 | 否（无则降级腾讯→yfinance→AkShare） | `https://api.twelvedata.com/time_series` |
| | 腾讯行情（免费） | — | — | **不需要** | `https://qt.gtimg.cn/q=` |
| | 腾讯 fqkline（免费） | — | — | **不需要** | `https://web.ifzq.gtimg.cn/appstock/app/fqkline/get` |
| **HKStockDataSource** (港股) | **Twelve Data** API Key | `TWELVE_DATA_API_KEY` | 空 | 否 | 同上 |
| | 腾讯行情（免费） | — | — | **不需要** | 同上 |
| **ForexDataSource** | **Twelve Data** API Key | `TWELVE_DATA_API_KEY` | 空 | 否（无则 Tiingo / yfinance） | `https://api.twelvedata.com/time_series` |
| | **Tiingo** API Key | `TIINGO_API_KEY` | 空 | 否（无则降级 yfinance） | `https://api.tiingo.com/tiingo` |
| **FuturesDataSource** (传统期货) | **Twelve Data** API Key | `TWELVE_DATA_API_KEY` | 空 | 否 | 同上 |
| | **Tiingo** API Key（仅贵金属） | `TIINGO_API_KEY` | 空 | 否 | 同上 |
| **FuturesDataSource** (加密期货) | 同 CCXT 配置 | 同 Crypto | — | 否 | Binance Futures |
| **AkShare 辅助**（A/港股备选，境外不稳定） | 无（免费，东方财富/新浪） | — | — | **不需要** | 国内站点 |
| **PolymarketDataSource** | 无（公开 REST API） | — | — | **不需要** | `https://gamma-api.polymarket.com` `https://clob.polymarket.com` `https://data-api.polymarket.com` |

---

## 二、Data Providers — 市场概览数据层

| 提供者模块 | API Key / 配置项 | 环境变量 | 默认值 | 是否必需 | Notes |
|---|---|---|---|---|---|
| **crypto.py**（行情+热力图） | **CoinGecko**（免费，限速） | — | — | **不需要** | `https://api.coingecko.com/api/v3` |
| | **CoinCap**（免费，无限速） | — | — | **不需要** | `https://api.coincap.io/v2` |
| **forex.py**（外汇概览） | **Twelve Data** API Key | `TWELVE_DATA_API_KEY` | 空 | 否（无则 yfinance/Tiingo） | — |
| **indices.py**（股指） | 无 | — | — | **不需要** | yfinance 公开接口 |
| **commodities.py**（大宗商品） | **Twelve Data** API Key | `TWELVE_DATA_API_KEY` | 空 | 否（无则 yfinance/Tiingo） | — |
| | **Tiingo** API Key（金银） | `TIINGO_API_KEY` | 空 | 否 | — |
| **heatmap.py**（热力图） | 无（聚合其他 Provider） | — | — | **不需要** | 依赖其他 Provider 数据 |
| **news.py**（新闻+经济日历） | **搜索服务 API Key**（Google/Bing/Tavily/SerpAPI） | `SEARCH_GOOGLE_API_KEY`+`SEARCH_GOOGLE_CX` / `TAVILY_API_KEYS` / `SERPAPI_KEYS` | 空 | 否（无则新闻为空，日历为预设模板） | `SEARCH_PROVIDER=google` |
| **sentiment.py**（市场情绪） | 无（alternative.me / yfinance / akshare 均为免费公开API） | — | — | **不需要** | `https://api.alternative.me/fng/` |
| **opportunities.py**（交易机会） | 无（聚合其他 Provider） | — | — | **不需要** | 依赖其他 Provider |
| **adanos_sentiment.py**（Adanos 美股情感） | **Adanos** API Key | `ADANOS_API_KEY` | 空 | **不需要**（无则 `enabled=false`） | `ADANOS_API_BASE_URL=https://api.adanos.org` |
| | 情感数据来源 | `ADANOS_SENTIMENT_SOURCE` | `reddit` | 否 | 可选 `reddit`/`x`/`news`/`polymarket` |
| | 超时 | `ADANOS_API_TIMEOUT` | `10` | 否 | — |

---

## 三、CN/HK 基本面数据层

| 数据源 | API Key / 配置项 | 环境变量 | 默认值 | 是否必需 | Notes |
|---|---|---|---|---|---|
| **cn_hk_fundamentals.py**（A/港股基本面） | **Twelve Data** API Key（/statistics, /profile, /earnings, /income_statement 等） | `TWELVE_DATA_API_KEY` | 空 | 否（无则降级 AkShare 东方财富） | `https://api.twelvedata.com` |
| | **AkShare**（东方财富，国内备选） | 无（免费） | — | **不需要** | 东方财富国内站点，海外不稳定 |

---

## 四、共用/通用配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|---|---|---|---|
| 数据源超时 | `DATA_SOURCE_TIMEOUT` | `30` | 所有 DataSource 通用超时 |
| 数据源重试 | `DATA_SOURCE_RETRY` | `3` | 通用重试次数 |
| 数据源重试退避 | `DATA_SOURCE_RETRY_BACKOFF` | `0.5` | 通用重试退避秒数 |
| Redis 缓存 | `REDIS_HOST` / `REDIS_PORT` / `CACHE_ENABLED` | `redis` / `6379` / `true` | 缓存可用时 Data Provider 结果会缓存 |
| 代理 | `PROXY_URL` / `HTTPS_PROXY` / `HTTP_PROXY` | 空 | 影响 CCXT 及部分 HTTP 请求 |

---

## 五、总结：无需任何 API Key 即可使用的核心数据

以下数据源**开箱即用**，无需配置任何密钥：

| 数据 | 来源 |
|---|---|
| 全球股指（S&P 500, Dow, NASDAQ 等 10 个） | yfinance |
| 加密货币热力图（Top 30） | CoinGecko / CoinCap |
| 市场情绪（Fear&Greed, VIX, DXY, Yield Curve, VXN, GVZ, P/C Ratio） | alternative.me + yfinance |
| A/港股实时报价 + 日线/周线 K 线 | 腾讯行情（qt.gtimg.cn） |
| A/港股分钟级 K 线（备选） | yfinance |
| Polymarket 预测市场数据 | 公开 REST API |
| 交易机会扫描（跨市场信号计算） | 聚合上述免费数据 |

**需要 API Key（可选）以获得更优体验**：`TWELVE_DATA_API_KEY`（A/港股K线主源）、`FINNHUB_API_KEY`（美股 Ticker）、`TIINGO_API_KEY`（外汇/贵金属）、`ADANOS_API_KEY`（美股情感）、搜索 API Key（新闻）