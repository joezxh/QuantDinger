# QuantDinger 多源数据采集整合方案

## 一、四项目数据源对比分析

### 1.1 项目概览

| 维度 | QuantDinger | FinceptTerminal | TradingAgents-CN | dexter |
|------|-------------|-----------------|-------------------|--------|
| **语言** | Python (Flask) | C++/Qt + Python脚本 | Python (Streamlit) | TypeScript (Node.js) |
| **定位** | 自托管AI量化交易平台 | 多数据源金融终端 | 多Agent智能交易系统 | AI金融分析助手 |
| **数据架构** | DataSourceFactory + MarketDataCollector | 独立脚本集合(~200+) | Provider模式 + DataSourceManager | Financial Datasets API统一封装 |
| **存储** | PostgreSQL + Redis | SQLite + CSV | MongoDB + 文件缓存 | 本地文件缓存 |
| **中国市场** | AKShare(基础) | AKShare(全面)+BaoStock | AKShare+Tushare+BaoStock | 无 |
| **美股** | yFinance+Finnhub+IBKR | yFinance+AlphaVantage | yFinance+Finnhub+AlphaVantage | Financial Datasets API |
| **加密货币** | CCXT(10+交易所) | CoinGecko+CoinMarketCap+CryptoCompare | 无 | Financial Datasets API |
| **外汇** | MT5 | 无 | 无 | 无 |
| **预测市场** | Polymarket | 无 | 无 | 无 |
| **新闻/舆情** | Finnhub+Search | Finnhub(占位) | Finnhub+GoogleNews+Reddit+东方财富 | Financial Datasets News |
| **宏观** | yFinance(VIX/DXY等) | FRED+BLS+BEA+Census+世界银行 | 无 | 无 |
| **基本面** | Finnhub+akshare | AlphaVantage+SimFin+baostock | AlphaVantage+Finnhub+yFinance+SimFin | Financial Datasets API(完整) |
| **SEC文件** | 无 | 无 | 无 | 10-K/10-Q/8-K Items |
| **内部交易** | 无 | 无 | Finnhub | Financial Datasets API |
| **分析师预估** | 无 | 无 | 无 | Financial Datasets API |

### 1.2 按数据类型分类对比

#### 1.2.1 加密货币数据

| 数据源 | QuantDinger | FinceptTerminal | TradingAgents-CN | dexter | 可靠性 | 成本 |
|--------|:-----------:|:---------------:|:-----------------:|:------:|--------|------|
| **CCXT (10+交易所)** | ✅ 核心数据源 | ✅ agno_trading | ❌ | ❌ | 高 | 免费 |
| **CoinGecko** | ❌ | ✅ coingecko.py | ❌ | ❌ | 高 | 免费(限速) |
| **CoinMarketCap** | ❌ | ✅ coinmarketcap_data.py | ❌ | ❌ | 高 | 免费/付费 |
| **CryptoCompare** | ❌ | ✅ cryptocompare_data.py | ❌ | ❌ | 高 | 免费/付费 |
| **CoinCap** | ❌ | ✅ coincap_data.py | ❌ | ❌ | 中 | 免费 |
| **CoinPaprika** | ❌ | ✅ coinpaprika_data.py | ❌ | ❌ | 中 | 免费 |
| **DeFi Llama** | ❌ | ✅ defillama_data.py | ❌ | ❌ | 高 | 免费 |
| **Coinglass** | ✅ API密钥已配置 | ✅ coinglass_data.py | ❌ | ❌ | 高 | 付费 |
| **CryptoQuant** | ✅ API密钥已配置 | ❌ | ❌ | ❌ | 高 | 付费 |
| **Blockchain.com** | ❌ | ✅ blockchain_com_data.py | ❌ | ❌ | 高 | 免费 |
| **Financial Datasets Crypto** | ❌ | ❌ | ❌ | ✅ | 高 | 付费 |

**整合建议**：QuantDinger已有CCXT核心能力，应补充CoinGecko(免费聚合数据)、DeFi Llama(DeFi TVL)、Coinglass(持仓/OI数据)。

#### 1.2.2 美股数据

| 数据源 | QuantDinger | FinceptTerminal | TradingAgents-CN | dexter | 可靠性 | 成本 |
|--------|:-----------:|:---------------:|:-----------------:|:------:|--------|------|
| **yFinance** | ✅ data_sources/us_stock | ✅ yfinance_data.py | ✅ providers/us/yfinance | ❌ | 中(非官方) | 免费 |
| **Finnhub** | ✅ API密钥已配置 | ✅ fetch_company_news | ✅ providers/us/finnhub | ❌ | 高 | 免费(60次/分) |
| **Alpha Vantage** | ✅ API密钥已配置 | ✅ alphavantage_data.py | ✅ providers/us/alpha_vantage | ❌ | 高 | 免费(5次/分) |
| **Tiingo** | ✅ API密钥已配置 | ❌ | ❌ | ❌ | 高 | 免费/付费 |
| **Twelve Data** | ✅ API密钥已配置 | ❌ | ❌ | ❌ | 高 | 免费(8次/分) |
| **IBKR** | ✅ 实盘交易 | ❌ | ❌ | ❌ | 极高 | 需账户 |
| **Financial Datasets API** | ❌ | ❌ | ❌ | ✅ 核心数据源 | 高 | 付费 |
| **SimFin** | ❌ | ❌ | ✅ CSV离线数据 | ❌ | 中 | 免费(延迟) |
| **FRED** | ❌ | ✅ federal_reserve_data.py | ❌ | ❌ | 极高(官方) | 免费 |

**整合建议**：QuantDinger已覆盖主流免费源，应补充FRED(美联储官方宏观数据)和Financial Datasets API(高质量结构化财务数据)。

#### 1.2.3 中国市场数据

| 数据源 | QuantDinger | FinceptTerminal | TradingAgents-CN | dexter | 可靠性 | 成本 |
|--------|:-----------:|:---------------:|:-----------------:|:------:|--------|------|
| **AKShare** | ✅ cn_stock/hk_stock | ✅ 全面覆盖(15+脚本) | ✅ providers/china/akshare | ❌ | 中(反爬) | 免费 |
| **Tushare** | ❌ | ❌ | ✅ providers/china/tushare | ❌ | 高 | 免费/付费 |
| **BaoStock** | ❌ | ✅ baostock_*.py(3脚本) | ✅ providers/china/baostock | ❌ | 中 | 免费 |
| **腾讯财经** | ✅ tencent.py | ❌ | ❌ | ❌ | 中 | 免费 |
| **东方财富(AKShare内)** | ✅ 间接 | ✅ 间接+直接 | ✅ 间接+curl_cffi | ❌ | 中(反爬) | 免费 |

**整合建议**：QuantDinger已有AKShare基础，应补充Tushare(高质量专业数据，需token)和BaoStock(稳定免费备选)。

#### 1.2.4 港股数据

| 数据源 | QuantDinger | FinceptTerminal | TradingAgents-CN | dexter | 可靠性 | 成本 |
|--------|:-----------:|:---------------:|:-----------------:|:------:|--------|------|
| **AKShare港股** | ✅ hk_stock.py | ✅ akshare_stocks_board | ✅ providers/hk/improved_hk | ❌ | 中 | 免费 |
| **yFinance港股** | ✅ 间接支持 | ✅ yfinance_data.py | ✅ providers/hk/hk_stock | ❌ | 中 | 免费 |

**整合建议**：港股数据QuantDinger已基本覆盖，AKShare+yFinance双源足够。

#### 1.2.5 外汇数据

| 数据源 | QuantDinger | FinceptTerminal | TradingAgents-CN | dexter | 可靠性 | 成本 |
|--------|:-----------:|:---------------:|:-----------------:|:------:|--------|------|
| **MT5** | ✅ 实盘+数据 | ❌ | ❌ | ❌ | 极高 | 需账户 |
| **yFinance外汇** | ✅ forex.py | ❌ | ❌ | ❌ | 中 | 免费 |
| **Alpha Vantage外汇** | ✅ 已配置密钥 | ❌ | ❌ | ❌ | 高 | 免费(限速) |

**整合建议**：外汇QuantDinger已有最完整方案(MT5+yFinance+AlphaVantage)，无需额外补充。

#### 1.2.6 期货数据

| 数据源 | QuantDinger | FinceptTerminal | TradingAgents-CN | dexter | 可靠性 | 成本 |
|--------|:-----------:|:---------------:|:-----------------:|:------:|--------|------|
| **AKShare期货** | ✅ futures.py | ✅ akshare_futures.py | ❌ | ❌ | 中 | 免费 |
| **CFTC持仓** | ❌ | ✅ cftc_data.py | ❌ | ❌ | 极高(官方) | 免费 |
| **COMEX** | ❌ | ✅ comex_data.py | ❌ | ❌ | 高 | 免费 |
| **CBOE/VIX** | ❌ | ✅ cboe_vix_data.py | ❌ | ❌ | 极高(官方) | 免费 |
| **Databento** | ❌ | ✅ databento_provider.py | ❌ | ❌ | 极高 | 付费 |

**整合建议**：应补充CFTC持仓数据(COT报告)和CBOE VIX数据，均免费且权威。

#### 1.2.7 宏观经济数据

| 数据源 | QuantDinger | FinceptTerminal | TradingAgents-CN | dexter | 可靠性 | 成本 |
|--------|:-----------:|:---------------:|:-----------------:|:------:|--------|------|
| **FRED(美联储)** | ❌ | ✅ federal_reserve_data.py | ❌ | ❌ | 极高(官方) | 免费 |
| **BLS(劳工统计局)** | ❌ | ✅ bls_data.py | ❌ | ❌ | 极高(官方) | 免费 |
| **BEA(经济分析局)** | ❌ | ✅ bea_data.py | ❌ | ❌ | 极高(官方) | 免费 |
| **Census(人口普查)** | ❌ | ✅ census_data.py | ❌ | ❌ | 极高(官方) | 免费 |
| **世界银行** | ❌ | ✅ worldbank_*.py(3脚本) | ❌ | ❌ | 极高(官方) | 免费 |
| **WTO** | ❌ | ✅ wto_data.py | ❌ | ❌ | 极高(官方) | 免费 |
| **BIS(国际清算银行)** | ❌ | ✅ bis_*.py(3脚本) | ❌ | ❌ | 极高(官方) | 免费 |
| **央行数据(BOE/BOJ/BOC)** | ❌ | ✅ 多个央行脚本 | ❌ | ❌ | 极高(官方) | 免费 |
| **AKShare宏观** | ✅ 间接支持 | ✅ akshare_macro/economics | ❌ | ❌ | 中 | 免费 |

**整合建议**：宏观数据是QuantDinger最薄弱环节，应优先整合FRED(美联储)、BLS(就业/CPI)、世界银行数据。

#### 1.2.8 新闻/舆情数据

| 数据源 | QuantDinger | FinceptTerminal | TradingAgents-CN | dexter | 可靠性 | 成本 |
|--------|:-----------:|:---------------:|:-----------------:|:------:|--------|------|
| **Finnhub新闻** | ✅ fast_analysis | ✅ fetch_company_news | ✅ providers/us/finnhub | ❌ | 高 | 免费(限速) |
| **Google News** | ❌ | ❌ | ✅ news/google_news | ❌ | 中 | 免费 |
| **Reddit** | ❌ | ❌ | ✅ news/reddit | ❌ | 中 | 免费 |
| **东方财富新闻(AKShare)** | ❌ | ✅ akshare_news.py | ✅ news/chinese_finance | ❌ | 中 | 免费 |
| **Alpha Vantage新闻** | ✅ 已配置密钥 | ❌ | ✅ alpha_vantage_news | ❌ | 高 | 免费(限速) |
| **Adanos情绪** | ✅ 已配置密钥 | ❌ | ❌ | ❌ | 高 | 付费 |
| **Financial Datasets News** | ❌ | ❌ | ❌ | ✅ | 高 | 付费 |
| **Tavily搜索** | ✅ 已配置密钥 | ❌ | ❌ | ✅ | 高 | 免费1000次/月 |
| **SerpAPI** | ✅ 已配置密钥 | ❌ | ❌ | ❌ | 高 | 免费100次/月 |
| **Exa搜索** | ❌ | ❌ | ❌ | ✅ | 高 | 付费 |
| **Perplexity** | ❌ | ❌ | ❌ | ✅ | 高 | 付费 |

**整合建议**：已有Finnhub+Tavily+SerpAPI+Adanos，应补充Google News(免费)和东方财富新闻(A股必备)。

#### 1.2.9 基本面/财务数据

| 数据源 | QuantDinger | FinceptTerminal | TradingAgents-CN | dexter | 可靠性 | 成本 |
|--------|:-----------:|:---------------:|:-----------------:|:------:|--------|------|
| **Finnhub基本面** | ✅ fast_analysis | ✅ fetch_company_news | ✅ finnhub基本面 | ❌ | 高 | 免费 |
| **yFinance基本面** | ✅ us_stock | ✅ yfinance_data | ✅ yfinance基本面 | ❌ | 中 | 免费 |
| **Alpha Vantage基本面** | ✅ 已配置密钥 | ✅ alphavantage_data | ✅ alpha_vantage_fundamentals | ❌ | 高 | 免费(限速) |
| **SimFin财务报表** | ❌ | ❌ | ✅ CSV离线数据 | ❌ | 中 | 免费(延迟) |
| **AKShare财务** | ✅ cn_hk_fundamentals | ✅ akshare_stocks_financial | ✅ akshare财务 | ❌ | 中 | 免费 |
| **BaoStock财务** | ❌ | ✅ baostock_fundamentals | ✅ baostock财务 | ❌ | 中 | 免费 |
| **Financial Datasets** | ❌ | ❌ | ❌ | ✅ 完整三表+比率 | 极高 | 付费 |
| **SEC Filing Items** | ❌ | ❌ | ❌ | ✅ 10-K/10-Q/8-K章节 | 极高 | 付费 |
| **内部交易** | ❌ | ❌ | ✅ Finnhub | ✅ Financial Datasets | 高 | 免费/付费 |
| **分析师预估** | ❌ | ❌ | ❌ | ✅ Financial Datasets | 高 | 付费 |
| **分部营收** | ❌ | ❌ | ❌ | ✅ Financial Datasets | 高 | 付费 |

**整合建议**：QuantDinger基本面覆盖中等，应补充SimFin(免费离线)和考虑Financial Datasets API(专业级数据)。

#### 1.2.10 预测市场

| 数据源 | QuantDinger | FinceptTerminal | TradingAgents-CN | dexter | 可靠性 | 成本 |
|--------|:-----------:|:---------------:|:-----------------:|:------:|--------|------|
| **Polymarket Gamma API** | ✅ data_sources/polymarket | ❌ | ❌ | ❌ | 高 | 免费 |
| **Polymarket CLOB API** | ✅ 订单簿/价格 | ❌ | ❌ | ❌ | 高 | 免费 |
| **Polymarket Data API** | ✅ 用户持仓/交易 | ❌ | ❌ | ❌ | 高 | 免费 |

**整合建议**：QuantDinger已有独家Polymarket集成，领先其他项目，应继续深化。

---

## 二、统一数据源整合技术方案

### 2.1 架构设计

```
┌──────────────────────────────────────────────────────────────────┐
│                      API Routes (Flask)                          │
├──────────────────────────────────────────────────────────────────┤
│                    DataService Layer                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐    │
│  │ UnifiedData  │  │ PriorityRouter│  │ FallbackCoordinator │    │
│  │  Gateway     │  │ (数据源路由)  │  │ (故障转移协调)       │    │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬───────────┘    │
├─────────┼────────────────┼──────────────────────┼────────────────┤
│         │         Provider Layer                 │                │
│  ┌──────┴───────────────────────────────────────┴───────────┐    │
│  │              BaseDataProvider (抽象基类)                   │    │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐   │    │
│  │  │Crypto   │ │Stock     │ │Forex     │ │Macro       │   │    │
│  │  │Provider │ │Provider  │ │Provider  │ │Provider    │   │    │
│  │  ├─────────┤ ├──────────┤ ├──────────┤ ├────────────┤   │    │
│  │  │News     │ │Funda-    │ │Predict-  │ │Alternative │   │    │
│  │  │Provider │ │mentals   │ │ionMarket │ │Data        │   │    │
│  │  │         │ │Provider  │ │Provider  │ │Provider    │   │    │
│  │  └─────────┘ └──────────┘ └──────────┘ └────────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
├──────────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                           │
│  ┌──────────┐ ┌───────────┐ ┌────────────┐ ┌────────────────┐  │
│  │Rate Limiter│ │Cache Mgr  │ │Circuit Brkr│ │Health Monitor │  │
│  │(令牌桶)    │ │(Redis+PG) │ │(熔断器)     │ │(健康检查)      │  │
│  └──────────┘ └───────────┘ └────────────┘ └────────────────┘  │
├──────────────────────────────────────────────────────────────────┤
│                      Storage Layer                                │
│  ┌────────────┐  ┌─────────┐  ┌─────────────────────────────┐  │
│  │ PostgreSQL  │  │  Redis  │  │    External APIs             │  │
│  │ (持久化)    │  │ (缓存)  │  │  (各数据源HTTP/gRPC调用)      │  │
│  └────────────┘  └─────────┘  └─────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 核心模块设计

#### 2.2.1 Provider抽象基类

借鉴TradingAgents-CN的 `BaseStockDataProvider` 模式，定义统一接口：

```python
# app/data_sources/providers/base.py

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime

class DataCategory(str, Enum):
    CRYPTO = "crypto"
    US_STOCK = "us_stock"
    CN_STOCK = "cn_stock"
    HK_STOCK = "hk_stock"
    FOREX = "forex"
    FUTURES = "futures"
    MACRO = "macro"
    NEWS = "news"
    FUNDAMENTALS = "fundamentals"
    PREDICTION_MARKET = "prediction_market"
    ALTERNATIVE = "alternative"

class ProviderStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"

class BaseProvider(ABC):
    name: str
    data_categories: List[DataCategory]
    priority: int = 0
    requires_api_key: bool = False
    rate_limit_per_minute: int = 60

    @abstractmethod
    async def get_kline(self, symbol: str, timeframe: str, limit: int, **kwargs) -> List[Dict]:
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def health_check(self) -> ProviderStatus:
        pass

    @abstractmethod
    async def get_rate_limit_status(self) -> Dict[str, Any]:
        pass
```

#### 2.2.2 数据源优先级与故障转移

借鉴TradingAgents-CN的 `DataSourceManager` 模式：

```python
# app/data_sources/router.py

class PriorityRouter:
    """数据源优先级路由 - 按市场类别管理数据源优先级和故障转移"""

    def __init__(self):
        self._routes: Dict[DataCategory, List[BaseProvider]] = {}
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}

    def register(self, category: DataCategory, provider: BaseProvider):
        if category not in self._routes:
            self._routes[category] = []
        self._routes[category].append(provider)
        self._routes[category].sort(key=lambda p: p.priority, reverse=True)

    async def route(self, category: DataCategory, method: str, **kwargs) -> Any:
        providers = self._routes.get(category, [])
        last_error = None
        for provider in providers:
            breaker = self._circuit_breakers.get(provider.name)
            if breaker and breaker.is_open():
                continue
            try:
                result = await getattr(provider, method)(**kwargs)
                if breaker:
                    breaker.record_success()
                return result
            except RateLimitError:
                self._circuit_breakers[provider.name].record_failure()
                last_error = "rate_limited"
                continue
            except Exception as e:
                self._circuit_breakers[provider.name].record_failure()
                last_error = str(e)
                continue
        raise DataSourceExhaustedError(f"All providers failed for {category}: {last_error}")
```

#### 2.2.3 数据源优先级配置（数据库驱动）

参考TradingAgents-CN的MongoDB数据源配置模式，QuantDinger使用PostgreSQL：

```sql
-- 数据源配置表
CREATE TABLE IF NOT EXISTS qd_data_source_configs (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,       -- crypto/us_stock/cn_stock/forex/macro/news/fundamentals
    provider_name VARCHAR(50) NOT NULL,  -- ccxt/yfinance/finnhub/akshare/tushare/fred/...
    priority INTEGER DEFAULT 0,          -- 数字越大优先级越高
    enabled BOOLEAN DEFAULT TRUE,
    api_key_env VARCHAR(100) DEFAULT '',  -- 环境变量名（不存密钥本身）
    config_json TEXT DEFAULT '{}',        -- 额外配置JSON
    rate_limit_per_minute INTEGER DEFAULT 60,
    timeout_seconds INTEGER DEFAULT 30,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(category, provider_name)
);

-- 数据源健康状态表
CREATE TABLE IF NOT EXISTS qd_data_source_health (
    id SERIAL PRIMARY KEY,
    provider_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'healthy',
    latency_ms INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    last_check_at TIMESTAMP,
    last_error TEXT DEFAULT '',
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 2.2.4 缓存策略

综合QuantDinger现有Redis缓存 + TradingAgents-CN的MongoDB缓存 + dexter的TTL缓存：

```python
# app/data_sources/cache_strategy.py

class CacheStrategy:
    """多级缓存策略"""

    # 缓存TTL配置（按数据类型）
    TTL_CONFIG = {
        # 实时行情 - 极短缓存
        "ticker": 10,           # 10秒
        "ticker_crypto": 5,     # 加密货币5秒

        # K线数据 - 按周期分级
        "kline_1m": 5,
        "kline_5m": 30,
        "kline_15m": 300,
        "kline_1H": 300,
        "kline_1D": 300,

        # 新闻 - 中等缓存
        "news": 900,             # 15分钟
        "news_cn": 600,          # 10分钟

        # 基本面 - 长缓存
        "fundamentals": 86400,   # 24小时
        "financial_statements": 86400,

        # 宏观 - 极长缓存
        "macro": 3600,           # 1小时
        "economic_calendar": 1800,

        # 预测市场
        "polymarket": 300,       # 5分钟
    }

    # 缓存层级: L1=Redis, L2=PostgreSQL
    def __init__(self):
        self.redis = get_redis_client()
        self.pg = get_db_connection

    async def get(self, key: str) -> Optional[Any]:
        # L1: Redis
        data = self.redis.get(key)
        if data:
            return json.loads(data)
        # L2: PostgreSQL (qd_data_cache表)
        data = await self._get_from_pg(key)
        if data:
            self.redis.setex(key, self._get_ttl(key), json.dumps(data))
            return data
        return None

    async def set(self, key: str, value: Any, ttl_override: Optional[int] = None):
        ttl = ttl_override or self._get_ttl(key)
        self.redis.setex(key, ttl, json.dumps(value))
```

#### 2.2.5 限流器

```python
# app/data_sources/rate_limiter.py

class TokenBucketRateLimiter:
    """令牌桶限流器 - 每个Provider独立限流"""

    def __init__(self, provider_name: str, rate: int, period: int = 60):
        self.provider_name = provider_name
        self.rate = rate
        self.period = period
        self._tokens = rate
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(self.rate, self._tokens + elapsed * (self.rate / self.period))
            self._last_refill = now

            if self._tokens < 1:
                wait_time = (1 - self._tokens) * (self.period / self.rate)
                await asyncio.sleep(wait_time)
                self._tokens = 0
            else:
                self._tokens -= 1
```

### 2.3 新增数据源Provider实现

#### 2.3.1 CoinGecko Provider

```python
# app/data_sources/providers/crypto_coingecko.py

class CoinGeckoProvider(BaseProvider):
    name = "coingecko"
    data_categories = [DataCategory.CRYPTO]
    priority = 20  # CCXT=100, CoinGecko=20 (辅助)
    requires_api_key = False
    rate_limit_per_minute = 30  # 免费版

    async def get_coin_list(self) -> List[Dict]:
        return await self._request("/coins/list")

    async def get_market_data(self, ids: str, vs_currency: str = "usd") -> Dict:
        return await self._request("/coins/markets", {
            "ids": ids, "vs_currency": vs_currency,
            "order": "market_cap_desc", "per_page": 250
        })

    async def get_defi_tvl(self) -> Dict:
        """DeFi Llama风格的TVL数据"""
        return await self._request("/global/decentralized_finance")
```

#### 2.3.2 DeFi Llama Provider

```python
# app/data_sources/providers/crypto_defillama.py

class DefiLlamaProvider(BaseProvider):
    name = "defillama"
    data_categories = [DataCategory.CRYPTO, DataCategory.ALTERNATIVE]
    priority = 15
    requires_api_key = False
    rate_limit_per_minute = 60

    BASE_URL = "https://api.llama.fi"

    async def get_protocols(self) -> List[Dict]:
        return await self._request(f"{self.BASE_URL}/protocols")

    async def get_tvl(self, protocol: str) -> Dict:
        return await self._request(f"{self.BASE_URL}/protocol/{protocol}")

    async def get_chains_tvl(self) -> List[Dict]:
        return await self._request(f"{self.BASE_URL}/v2/chains")
```

#### 2.3.3 FRED Provider (宏观)

```python
# app/data_sources/providers/macro_fred.py

class FREDProvider(BaseProvider):
    name = "fred"
    data_categories = [DataCategory.MACRO]
    priority = 100  # 宏观数据最高优先级
    requires_api_key = True
    rate_limit_per_minute = 120

    BASE_URL = "https://api.stlouisfed.org/fred"

    # 关键序列映射
    SERIES = {
        "DFF": "联邦基金利率",
        "DGS10": "10年期国债收益率",
        "DGS2": "2年期国债收益率",
        "T10Y2Y": "10Y-2Y利差(衰退指标)",
        "CPIAUCSL": "CPI(消费者物价指数)",
        "UNRATE": "失业率",
        "GDP": "GDP",
        "PAYEMS": "非农就业",
        "FEDFUNDS": "联邦基金利率(月)",
        "M2SL": "M2货币供应",
    }

    async def get_series(self, series_id: str, observation_start: str = None) -> Dict:
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 100,
        }
        if observation_start:
            params["observation_start"] = observation_start
        return await self._request(f"{self.BASE_URL}/series/observations", params)
```

#### 2.3.4 BLS Provider (宏观)

```python
# app/data_sources/providers/macro_bls.py

class BLSProvider(BaseProvider):
    name = "bls"
    data_categories = [DataCategory.MACRO]
    priority = 90
    requires_api_key = True
    rate_limit_per_minute = 60

    SERIES = {
        "LNS14000000": "失业率",
        "CUSR0000SA0": "CPI",
        "CIU1010000000000I": "时薪增长率",
        "LNS12300000": "劳动参与率",
    }
```

#### 2.3.5 Tushare Provider (A股)

```python
# app/data_sources/providers/cn_stock_tushare.py

class TushareProvider(BaseProvider):
    name = "tushare"
    data_categories = [DataCategory.CN_STOCK]
    priority = 80  # 高于AKShare(50)
    requires_api_key = True
    rate_limit_per_minute = 500  # 根据积分不同

    async def get_daily(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        return self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)

    async def get_financial(self, ts_code: str, period: str) -> Dict:
        income = self.pro.income(ts_code=ts_code, period=period)
        balancesheet = self.pro.balancesheet(ts_code=ts_code, period=period)
        cashflow = self.pro.cashflow(ts_code=ts_code, period=period)
        return {"income": income, "balancesheet": balancesheet, "cashflow": cashflow}
```

#### 2.3.6 BaoStock Provider (A股备选)

```python
# app/data_sources/providers/cn_stock_baostock.py

class BaoStockProvider(BaseProvider):
    name = "baostock"
    data_categories = [DataCategory.CN_STOCK, DataCategory.HK_STOCK]
    priority = 30  # 最低优先级，稳定备选
    requires_api_key = False
    rate_limit_per_minute = 120
```

#### 2.3.7 Financial Datasets API Provider (美股专业级)

```python
# app/data_sources/providers/us_stock_financial_datasets.py

class FinancialDatasetsProvider(BaseProvider):
    name = "financial_datasets"
    data_categories = [DataCategory.US_STOCK, DataCategory.FUNDAMENTALS, DataCategory.NEWS]
    priority = 70
    requires_api_key = True
    rate_limit_per_minute = 60

    BASE_URL = "https://api.financialdatasets.ai"

    async def get_income_statements(self, ticker: str, period: str = "annual") -> Dict:
        return await self._request(f"/financials/income-statements/", {"ticker": ticker, "period": period})

    async def get_balance_sheets(self, ticker: str, period: str = "annual") -> Dict:
        return await self._request(f"/financials/balance-sheets/", {"ticker": ticker, "period": period})

    async def get_cash_flow_statements(self, ticker: str, period: str = "annual") -> Dict:
        return await self._request(f"/financials/cash-flow-statements/", {"ticker": ticker, "period": period})

    async def get_key_ratios(self, ticker: str) -> Dict:
        return await self._request(f"/financial-metrics/snapshot/", {"ticker": ticker})

    async def get_insider_trades(self, ticker: str, limit: int = 10) -> Dict:
        return await self._request(f"/insider-trades/", {"ticker": ticker, "limit": limit})

    async def get_analyst_estimates(self, ticker: str, period: str = "annual") -> Dict:
        return await self._request(f"/analyst-estimates/", {"ticker": ticker, "period": period})

    async def get_filings(self, ticker: str, filing_type: List[str] = None) -> Dict:
        return await self._request(f"/filings/", {"ticker": ticker, "filing_type": filing_type})

    async def get_filing_items(self, ticker: str, filing_type: str, accession_number: str) -> Dict:
        return await self._request(f"/filings/items/", {
            "ticker": ticker, "filing_type": filing_type, "accession_number": accession_number
        })

    async def get_news(self, ticker: str = None, limit: int = 5) -> Dict:
        return await self._request(f"/news", {"ticker": ticker, "limit": limit})

    async def get_segmented_revenues(self, ticker: str, period: str = "annual") -> Dict:
        return await self._request(f"/financials/segmented-revenues/", {"ticker": ticker, "period": period})
```

#### 2.3.8 CFTC Provider (期货持仓)

```python
# app/data_sources/providers/futures_cftc.py

class CFTCProvider(BaseProvider):
    name = "cftc"
    data_categories = [DataCategory.FUTURES, DataCategory.ALTERNATIVE]
    priority = 100
    requires_api_key = False
    rate_limit_per_minute = 30

    async def get_cot_report(self, commodity: str, year: int) -> Dict:
        """获取COT(Commitment of Traders)报告"""
        return await self._request(
            f"https://publicreporting.cftc.gov/resource/tqk6-3h35.json",
            {"commodity": commodity, "report_year": year}
        )
```

#### 2.3.9 Google News Provider

```python
# app/data_sources/providers/news_google.py

class GoogleNewsProvider(BaseProvider):
    name = "google_news"
    data_categories = [DataCategory.NEWS]
    priority = 30  # 低优先级，免费备选
    requires_api_key = False
    rate_limit_per_minute = 10

    async def search(self, query: str, before: str, after: str) -> List[Dict]:
        """Google News搜索 - 借鉴TradingAgents-CN"""
        url = f"https://news.google.com/rss/search?q={query}+after:{after}+before:{before}"
        # 解析RSS返回
```

### 2.4 数据源注册与初始化

```python
# app/data_sources/registry.py

class ProviderRegistry:
    """数据源注册中心 - 应用启动时初始化所有Provider"""

    def __init__(self):
        self._providers: Dict[str, BaseProvider] = {}
        self._router = PriorityRouter()

    def register_all(self):
        """注册所有数据源，按配置的优先级排列"""

        # === 加密货币 ===
        self._register(CryptoCCXTProvider())       # priority=100, 核心
        self._register(CoinGeckoProvider())         # priority=20, 聚合数据
        self._register(DefiLlamaProvider())         # priority=15, DeFi TVL
        self._register(CoinglassProvider())         # priority=10, OI/资金费率
        self._register(CryptoQuantProvider())       # priority=10, 链上数据

        # === 美股 ===
        self._register(USStockYFinanceProvider())   # priority=50, 免费
        self._register(USStockFinnhubProvider())     # priority=60, 新闻+基本面
        self._register(USStockAlphaVantageProvider()) # priority=40, 技术面
        self._register(FinancialDatasetsProvider()) # priority=70, 专业级
        self._register(USStockTiingoProvider())      # priority=30, 备选
        self._register(USStockTwelveDataProvider())  # priority=25, 备选

        # === A股 ===
        self._register(CNStockTushareProvider())     # priority=80, 高质量
        self._register(CNStockAKShareProvider())     # priority=50, 免费全面
        self._register(CNStockBaoStockProvider())    # priority=30, 稳定备选

        # === 港股 ===
        self._register(HKStockAKShareProvider())     # priority=60
        self._register(HKStockYFinanceProvider())    # priority=40

        # === 外汇 ===
        self._register(ForexMT5Provider())          # priority=100, 实盘
        self._register(ForexYFinanceProvider())      # priority=30, 数据

        # === 期货 ===
        self._register(FuturesAKShareProvider())     # priority=50
        self._register(CFTCProvider())              # priority=100, 持仓数据
        self._register(CBOEProvider())              # priority=90, VIX

        # === 宏观 ===
        self._register(FREDProvider())              # priority=100, 美联储
        self._register(BLSProvider())                # priority=90, 就业/CPI
        self._register(BEAProvider())               # priority=80, GDP
        self._register(WorldBankProvider())          # priority=70, 全球

        # === 新闻 ===
        self._register(NewsFinnhubProvider())        # priority=60
        self._register(NewsAlphaVantageProvider())   # priority=50
        self._register(NewsGoogleProvider())          # priority=30
        self._register(NewsEastMoneyProvider())      # priority=40, A股新闻
        self._register(NewsTavilyProvider())          # priority=20, AI搜索
        self._register(NewsSerpAPIProvider())         # priority=15, AI搜索

        # === 预测市场 ===
        self._register(PolymarketProvider())         # priority=100, 独家

        # === 基本面 ===
        self._register(FundamentalsFinnhubProvider())  # priority=50
        self._register(FundamentalsAlphaVantageProvider()) # priority=40
        self._register(FundamentalsYFinanceProvider())   # priority=30

    def _register(self, provider: BaseProvider):
        self._providers[provider.name] = provider
        for category in provider.data_categories:
            self._router.register(category, provider)
```

### 2.5 熔断器实现

```python
# app/data_sources/circuit_breaker.py

class CircuitBreaker:
    """熔断器 - 防止对故障数据源的持续请求"""

    CLOSED = "closed"       # 正常
    OPEN = "open"           # 熔断(拒绝请求)
    HALF_OPEN = "half_open" # 半开(试探)

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.state = self.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = None

    def is_open(self) -> bool:
        if self.state == self.OPEN:
            if time.monotonic() - self.last_failure_time > self.recovery_timeout:
                self.state = self.HALF_OPEN
                return False
            return True
        return False

    def record_success(self):
        self.failure_count = 0
        self.state = self.CLOSED

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.failure_count >= self.failure_threshold:
            self.state = self.OPEN
```

### 2.6 与现有MarketDataCollector的整合

保持 `MarketDataCollector` 接口不变，内部替换为新的 `PriorityRouter`：

```python
# app/services/market_data_collector.py (改造)

class MarketDataCollector:
    def __init__(self):
        self.registry = ProviderRegistry()
        self.registry.register_all()
        self.router = self.registry.router
        self.rate_limiter = RateLimiterManager()
        self.cache = CacheStrategy()

    async def collect_all(self, market, symbol, ...):
        # 原有接口保持不变
        # 内部使用 router 自动选择最优数据源
        price = await self.router.route(DataCategory[market.upper()], "get_ticker", symbol=symbol)
        kline = await self.router.route(DataCategory[market.upper()], "get_kline", symbol=symbol, timeframe=timeframe, limit=60)
        # ...其余逻辑不变
```

---

## 三、实施计划

### Phase 1: 基础设施 (2周)

| 任务 | 优先级 | 说明 |
|------|--------|------|
| 创建 `app/data_sources/providers/` 目录结构 | P0 | 建立Provider抽象体系 |
| 实现 `BaseProvider` 抽象基类 | P0 | 统一接口定义 |
| 实现 `PriorityRouter` 路由器 | P0 | 核心调度逻辑 |
| 实现 `CircuitBreaker` 熔断器 | P0 | 故障隔离 |
| 实现 `TokenBucketRateLimiter` 限流器 | P1 | API保护 |
| 创建 `qd_data_source_configs` 数据库表 | P0 | 数据源配置 |
| 创建 `qd_data_source_health` 数据库表 | P1 | 健康监控 |
| 迁移现有 `DataSourceFactory` 到新Provider体系 | P0 | 向后兼容 |

### Phase 2: 核心数据源迁移 (2周)

| 任务 | 优先级 | 说明 |
|------|--------|------|
| 迁移 CryptoCCXTProvider | P0 | 核心加密货币 |
| 迁移 USStockYFinanceProvider | P0 | 核心美股 |
| 迁移 USStockFinnhubProvider | P0 | 新闻+基本面 |
| 迁移 CNStockAKShareProvider | P0 | 核心A股 |
| 迁移 HKStockAKShareProvider | P1 | 港股 |
| 迁移 ForexMT5Provider | P1 | 外汇 |
| 迁移 PolymarketProvider | P1 | 预测市场 |
| 改造 `MarketDataCollector` 使用新路由 | P0 | 统一入口 |

### Phase 3: 新增数据源 (3周)

| 任务 | 优先级 | 说明 |
|------|--------|------|
| 新增 FREDProvider | P0 | 美联储宏观(最高价值) |
| 新增 BLSProvider | P1 | 就业/CPI数据 |
| 新增 TushareProvider | P1 | A股高质量数据 |
| 新增 BaoStockProvider | P2 | A股稳定备选 |
| 新增 CoinGeckoProvider | P1 | 加密聚合数据 |
| 新增 DefiLlamaProvider | P2 | DeFi TVL |
| 新增 CFTCProvider | P2 | 期货持仓 |
| 新增 CBOEProvider | P2 | VIX数据 |
| 新增 FinancialDatasetsProvider | P2 | 美股专业级数据 |
| 新增 GoogleNewsProvider | P2 | 免费新闻 |
| 新增 EastMoneyNewsProvider | P1 | A股新闻 |

### Phase 4: 优化与监控 (2周)

| 任务 | 优先级 | 说明 |
|------|--------|------|
| 实现多级缓存(Redis+PG) | P1 | 性能优化 |
| 实现数据源健康检查定时任务 | P1 | 监控 |
| 实现数据源管理API(增删改查) | P2 | 运维 |
| 实现数据源优先级动态调整 | P2 | 智能调度 |
| 性能测试与压测 | P1 | 容量规划 |
| 文档更新 | P2 | 使用说明 |

### 总计：约9周

---

## 四、关键设计决策

### 4.1 保持现有数据库管理方式

- **不引入SQLAlchemy ORM**：继续使用 `db_postgres.py` 的 `get_db_connection()` 上下文管理器模式
- **不引入Neo4j**：知识图谱功能通过PostgreSQL的关系查询+JSON字段实现
- **不引入MongoDB**：所有配置和缓存使用PostgreSQL+Redis
- **数据源配置存PostgreSQL**：参考TradingAgents-CN的MongoDB方案，但使用PG实现

### 4.2 向后兼容

- `DataSourceFactory` 保持原有接口，内部委托给新Provider体系
- `MarketDataCollector` 保持原有 `collect_all()` 接口
- 新增 `DataProviderService` 作为新的统一入口，逐步替换老代码

### 4.3 新增依赖

| 包 | 用途 | 是否必须 |
|----|------|----------|
| tushare | A股专业数据 | 可选(需token) |
| defusedxml | Google News RSS解析 | 可选 |
| httpx | 异步HTTP客户端 | 推荐 |

---

## 五、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| AKShare反爬虫升级 | A股数据中断 | BaoStock/Tushare双备选 |
| yFinance非官方API变更 | 美股数据中断 | Finnhub/AlphaVantage降级 |
| Finnhub免费版限速(60次/分) | 新闻获取延迟 | 限流器+缓存+Alpha Vantage备选 |
| FRED API密钥申请延迟 | 宏观数据延迟 | yFinance间接获取(VIX/DXY等) |
| Tushare积分不足 | A股数据受限 | 免费基础接口+AKShare补充 |
| Financial Datasets API成本 | 美股专业数据受限 | 按需调用+长缓存 |

---

## 六、数据源完整清单

### 最终整合后QuantDinger将支持的数据源总计：

| # | 数据源 | 类别 | 优先级 | API Key | 状态 |
|---|--------|------|--------|---------|------|
| 1 | CCXT (10+交易所) | 加密货币 | 100 | 可选 | ✅ 已有 |
| 2 | CoinGecko | 加密货币 | 20 | 可选(免费) | 🆕 新增 |
| 3 | DeFi Llama | 加密货币/DeFi | 15 | 无 | 🆕 新增 |
| 4 | Coinglass | 加密货币/OI | 10 | 需要 | ✅ 已有密钥 |
| 5 | CryptoQuant | 加密货币/链上 | 10 | 需要 | ✅ 已有密钥 |
| 6 | yFinance | 美股/港股/外汇 | 50 | 无 | ✅ 已有 |
| 7 | Finnhub | 美股/新闻/基本面 | 60 | 需要 | ✅ 已有密钥 |
| 8 | Alpha Vantage | 美股/技术面/外汇 | 40 | 需要 | ✅ 已有密钥 |
| 9 | Tiingo | 美股 | 30 | 需要 | ✅ 已有密钥 |
| 10 | Twelve Data | 美股 | 25 | 需要 | ✅ 已有密钥 |
| 11 | IBKR | 美股实盘 | 100 | 需要账户 | ✅ 已有 |
| 12 | Financial Datasets | 美股专业级 | 70 | 需要 | 🆕 新增 |
| 13 | AKShare | A股/港股/期货 | 50 | 无 | ✅ 已有 |
| 14 | Tushare | A股 | 80 | 需要 | 🆕 新增 |
| 15 | BaoStock | A股 | 30 | 无 | 🆕 新增 |
| 16 | 腾讯财经 | A股实时 | 40 | 无 | ✅ 已有 |
| 17 | MT5 | 外汇实盘 | 100 | 需要账户 | ✅ 已有 |
| 18 | FRED | 宏观(美联储) | 100 | 需要 | 🆕 新增 |
| 19 | BLS | 宏观(就业/CPI) | 90 | 需要 | 🆕 新增 |
| 20 | BEA | 宏观(GDP) | 80 | 需要 | 🆕 新增 |
| 21 | 世界银行 | 宏观(全球) | 70 | 无 | 🆕 新增 |
| 22 | CFTC | 期货/持仓 | 100 | 无 | 🆕 新增 |
| 23 | CBOE | 期货/VIX | 90 | 无 | 🆕 新增 |
| 24 | Polymarket | 预测市场 | 100 | 无 | ✅ 已有 |
| 25 | Google News | 新闻 | 30 | 无 | 🆕 新增 |
| 26 | 东方财富新闻 | A股新闻 | 40 | 无 | 🆕 新增 |
| 27 | Tavily | AI搜索 | 20 | 需要 | ✅ 已有密钥 |
| 28 | SerpAPI | AI搜索 | 15 | 需要 | ✅ 已有密钥 |
| 29 | Adanos | 市场情绪 | 30 | 需要 | ✅ 已有密钥 |
| 30 | SimFin | 基本面(离线) | 20 | 无 | 🆕 新增 |
