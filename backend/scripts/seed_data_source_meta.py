"""
Seed data population for data source meta tables (qd_data_source_configs,
qd_data_source_datasets, qd_api_keys).

Run after migration 007 has been applied:
    python scripts/seed_data_source_meta.py

Idempotent — safe to run multiple times.
"""
import sys
import os

# Ensure backend_api_python is on sys.path
_CURRENT = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.normpath(os.path.join(_CURRENT, ".."))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# Load .env so database URL is available
from dotenv import load_dotenv

load_dotenv(os.path.join(_BACKEND, ".env"))

from sqlalchemy import update as _update
from sqlalchemy import text as sa_text
from app.database.session import get_session
from app.models.data_source_meta import (
    DataSourceConfig,
    DataSourceDataset,
    ApiKey,
)
from app.utils.logger import get_logger

logger = get_logger("seed_data_source_meta")

# ──────────────────────────────────────────────────────────────────────
# 1. Data Source Configurations
# ──────────────────────────────────────────────────────────────────────

DATA_SOURCES = [
    # ==================== Data Sources (K线/报价层) ====================
    DataSourceConfig(
        source_code="crypto_ccxt",
        source_name="CryptoDataSource (CCXT)",
        layer="data_source",
        market_categories=["Crypto"],
        load_balance_strategy="round_robin",
        config_json={
            "api_key_env": "CCXT_API_KEY",
            "api_key_required": False,
            "base_url": "https://api.coinbase.com",
            "fallback_base_url": None,
            "timeout_sec": 30,
            "retry_count": 3,
            "default_exchange": "coinbase",
            "supported_exchanges": ["coinbase", "binance", "okx", "bybit"],
            "rate_limit_per_min": 10,
            "proxy_supported": True,
        },
        dependencies=None,
        notes="CCXT unified crypto exchange interface. Default exchange configurable via CCXT_DEFAULT_EXCHANGE env var.",
    ),
    DataSourceConfig(
        source_code="us_stock",
        source_name="USStockDataSource (yfinance / Finnhub)",
        layer="data_source",
        market_categories=["USStock"],
        load_balance_strategy="health_first",
        config_json={
            "api_key_env": "FINNHUB_API_KEY",
            "api_key_required": False,
            "base_url": "https://yfinance-api.com",
            "fallback_base_url": "https://finnhub.io/api/v1",
            "timeout_sec": 30,
            "retry_count": 3,
            "rate_limit_per_min": 60,
            "proxy_supported": False,
        },
        dependencies=None,
        notes="3-tier fallback: yfinance fast_info -> yfinance info -> 1min K-line. Finnhub ticker optional.",
    ),
    DataSourceConfig(
        source_code="cn_stock",
        source_name="CNStockDataSource (TwelveData / 腾讯 / yfinance / AkShare)",
        layer="data_source",
        market_categories=["CNStock"],
        load_balance_strategy="health_first",
        config_json={
            "api_key_env": "TWELVE_DATA_API_KEY",
            "api_key_required": True,
            "base_url": "https://api.twelvedata.com",
            "fallback_base_url": "http://web.ifzq.gtimg.cn",
            "timeout_sec": 20,
            "retry_count": 4,
            "rate_limit_per_min": 8,
            "proxy_supported": False,
        },
        dependencies=None,
        notes="4-tier fallback: TwelveData -> Tencent fqkline -> yfinance -> AkShare(东方财富). TwelveData recommended, needs API key (800 credits/day free).",
    ),
    DataSourceConfig(
        source_code="hk_stock",
        source_name="HKStockDataSource (TwelveData / 腾讯 / yfinance / AkShare)",
        layer="data_source",
        market_categories=["HKStock"],
        load_balance_strategy="health_first",
        config_json={
            "api_key_env": "TWELVE_DATA_API_KEY",
            "api_key_required": True,
            "base_url": "https://api.twelvedata.com",
            "fallback_base_url": "http://web.ifzq.gtimg.cn",
            "timeout_sec": 20,
            "retry_count": 4,
            "rate_limit_per_min": 8,
            "proxy_supported": False,
        },
        dependencies=None,
        notes="Same 4-tier fallback as CNStock. TwelveData primary, Tencent free backup.",
    ),
    DataSourceConfig(
        source_code="forex",
        source_name="ForexDataSource (TwelveData / Tiingo / yfinance)",
        layer="data_source",
        market_categories=["Forex"],
        load_balance_strategy="health_first",
        config_json={
            "api_key_env": "TWELVE_DATA_API_KEY",
            "api_key_required": True,
            "base_url": "https://api.twelvedata.com/time_series",
            "fallback_base_url": "https://api.tiingo.com/tiingo/fx",
            "timeout_sec": 20,
            "retry_count": 3,
            "rate_limit_per_min": 8,
            "proxy_supported": False,
        },
        dependencies=None,
        notes="3-tier fallback: TwelveData -> Tiingo(/fx/top or /fx/{sym}/prices) -> yfinance. 14 major pairs.",
    ),
    DataSourceConfig(
        source_code="futures",
        source_name="FuturesDataSource (TwelveData / yfinance / Tiingo / CCXT)",
        layer="data_source",
        market_categories=["Futures"],
        load_balance_strategy="health_first",
        config_json={
            "api_key_env": "TWELVE_DATA_API_KEY",
            "api_key_required": True,
            "base_url": "https://api.twelvedata.com",
            "fallback_base_url": "https://query1.finance.yahoo.com",
            "timeout_sec": 20,
            "retry_count": 3,
            "rate_limit_per_min": 8,
            "proxy_supported": False,
        },
        dependencies=None,
        notes="Traditional futures (TwelveData -> yfinance -> Tiingo precious metals) + crypto futures (CCXT Binance Futures).",
    ),
    DataSourceConfig(
        source_code="polymarket",
        source_name="PolymarketDataSource (Polymarket REST API)",
        layer="data_source",
        market_categories=["PredictionMarket"],
        load_balance_strategy="round_robin",
        config_json={
            "api_key_env": "POLYMARKET_API_KEY",
            "api_key_required": False,
            "base_url": "https://gamma-api.polymarket.com",
            "fallback_base_url": "https://clob.polymarket.com",
            "timeout_sec": 15,
            "retry_count": 2,
            "rate_limit_per_min": 30,
            "proxy_supported": False,
        },
        dependencies=None,
        notes="Prediction market data via 3 public API endpoints: gamma-api (markets), clob (orderbook), data-api (trades). No API key required.",
    ),

    # ==================== Data Providers (概览聚合层) ====================
    DataSourceConfig(
        source_code="crypto_provider",
        source_name="Crypto - 加密货币行情提供者",
        layer="data_provider",
        market_categories=["Crypto"],
        load_balance_strategy="round_robin",
        config_json={
            "api_key_env": None,
            "api_key_required": False,
            "timeout_sec": 20,
            "retry_count": 3,
            "rate_limit_per_min": 30,
            "proxy_supported": False,
        },
        dependencies=["crypto_ccxt"],
        notes="Provides crypto price list + heatmap. 3-tier fallback internally: CCXT -> yfinance -> CoinGecko. 15 major coins.",
    ),
    DataSourceConfig(
        source_code="forex_provider",
        source_name="Forex - 主要货币对概览",
        layer="data_provider",
        market_categories=["Forex"],
        load_balance_strategy="round_robin",
        config_json={
            "api_key_env": None,
            "api_key_required": False,
            "timeout_sec": 20,
            "retry_count": 2,
            "rate_limit_per_min": 30,
        },
        dependencies=["forex"],
        notes="8 major currency pairs overview with bilingual names (CN/EN).",
    ),
    DataSourceConfig(
        source_code="indices_provider",
        source_name="Indices - 全球股指提供者",
        layer="data_provider",
        market_categories=["Indices"],
        load_balance_strategy="round_robin",
        config_json={
            "api_key_env": None,
            "api_key_required": False,
            "timeout_sec": 20,
            "retry_count": 2,
            "rate_limit_per_min": 30,
        },
        dependencies=None,
        notes="10 global indices via yfinance: S&P500, Dow, NASDAQ, DAX, FTSE, CAC40, Nikkei225, KOSPI, ASX200, SENSEX.",
    ),
    DataSourceConfig(
        source_code="commodities_provider",
        source_name="Commodities - 大宗商品价格",
        layer="data_provider",
        market_categories=["Commodities"],
        load_balance_strategy="round_robin",
        config_json={
            "api_key_env": None,
            "api_key_required": False,
            "timeout_sec": 20,
            "retry_count": 2,
            "rate_limit_per_min": 30,
        },
        dependencies=None,
        notes="6 major commodities via yfinance: Gold(GC), Silver(SI), WTI(CL), Brent(BZ), Copper(HG), Natural Gas(NG).",
    ),
    DataSourceConfig(
        source_code="heatmap_provider",
        source_name="Heatmap - 市场热力图聚合",
        layer="data_provider",
        market_categories=["Crypto", "USStock", "Forex", "Commodities", "Indices"],
        load_balance_strategy="round_robin",
        config_json={
            "api_key_env": None,
            "api_key_required": False,
            "timeout_sec": 30,
            "retry_count": 2,
            "rate_limit_per_min": 10,
        },
        dependencies=[
            "crypto_provider",
            "forex_provider",
            "indices_provider",
            "commodities_provider",
        ],
        notes="Aggregated heatmap: crypto(15) + sectors(10 ETFs) + forex(8) + commodities(6) + indices(10).",
    ),
    DataSourceConfig(
        source_code="news_provider",
        source_name="News - 财经新闻与经济日历",
        layer="data_provider",
        market_categories=["General"],
        load_balance_strategy="round_robin",
        config_json={
            "api_key_env": "TAVILY_API_KEYS",
            "api_key_required": False,
            "timeout_sec": 25,
            "retry_count": 2,
            "rate_limit_per_min": 20,
        },
        dependencies=None,
        notes="Financial news via configured search service (Tavily/Google/Bing) + preset economic calendar with 9 event types.",
    ),
    DataSourceConfig(
        source_code="sentiment_provider",
        source_name="Sentiment - 市场情绪指标",
        layer="data_provider",
        market_categories=["USStock", "General"],
        load_balance_strategy="round_robin",
        config_json={
            "api_key_env": None,
            "api_key_required": False,
            "timeout_sec": 15,
            "retry_count": 2,
            "rate_limit_per_min": 30,
        },
        dependencies=None,
        notes="7 sentiment indicators: Fear&Greed, VIX, DXY, Yield Curve, VXN, GVZ, Put/Call Ratio.",
    ),
    DataSourceConfig(
        source_code="opportunities_provider",
        source_name="Opportunities - 交易机会扫描",
        layer="data_provider",
        market_categories=["Crypto", "USStock", "CNStock", "HKStock", "Forex", "PredictionMarket"],
        load_balance_strategy="round_robin",
        config_json={
            "api_key_env": None,
            "api_key_required": False,
            "timeout_sec": 30,
            "retry_count": 2,
            "rate_limit_per_min": 10,
        },
        dependencies=[
            "crypto_provider",
            "us_stock",
            "cn_stock",
            "hk_stock",
            "forex",
            "polymarket",
        ],
        notes="Cross-market opportunity scanner covering crypto, US/CN/HK stocks, forex, prediction markets.",
    ),
    DataSourceConfig(
        source_code="adanos_provider",
        source_name="Adanos - 美股情感分析 (Reddit/X/News/Polymarket)",
        layer="data_provider",
        market_categories=["USStock"],
        load_balance_strategy="health_first",
        config_json={
            "api_key_env": "ADANOS_API_KEY",
            "api_key_required": False,
            "base_url": "https://api.adanos.xyz",
            "timeout_sec": 30,
            "retry_count": 2,
            "rate_limit_per_min": 10,
        },
        dependencies=None,
        notes="Fail-open design: returns enabled=false when ADANOS_API_KEY is not configured. Sources: Reddit, X, News, Polymarket.",
    ),

    # ==================== Fundamental ====================
    DataSourceConfig(
        source_code="cn_hk_fundamentals",
        source_name="CN/HK 基本面数据 (TwelveData / AkShare)",
        layer="fundamental",
        market_categories=["CNStock", "HKStock"],
        load_balance_strategy="health_first",
        config_json={
            "api_key_env": "TWELVE_DATA_API_KEY",
            "api_key_required": True,
            "base_url": "https://api.twelvedata.com",
            "timeout_sec": 25,
            "retry_count": 3,
            "rate_limit_per_min": 8,
        },
        dependencies=None,
        notes="Fundamentals (PE/PB/PS/ROE/DCF/ratios) + 3 financial statements. TwelveData primary, AkShare(东方财富) backup. 30+ fundamental fields.",
    ),

    # ==================== Collectors ====================
    DataSourceConfig(
        source_code="market_data_collector",
        source_name="MarketDataCollector - 市场数据采集器",
        layer="collector",
        market_categories=["Crypto", "USStock", "CNStock", "HKStock", "Forex", "Futures"],
        load_balance_strategy="round_robin",
        config_json={
            "api_key_env": None,
            "api_key_required": False,
            "timeout_sec": 60,
            "retry_count": 2,
            "rate_limit_per_min": 5,
        },
        dependencies=[
            "crypto_ccxt",
            "us_stock",
            "cn_stock",
            "hk_stock",
            "forex",
            "futures",
        ],
        notes="Background collector for periodic market data aggregation. Used by scheduled jobs and registry.",
    ),
]


# ──────────────────────────────────────────────────────────────────────
# 2. Dataset Definitions
# ──────────────────────────────────────────────────────────────────────

_datasets_by_source = {
    # ── CryptoDataSource ──────────────────────────────────────────
    "crypto_ccxt": [
        DataSourceDataset(
            dataset_code="crypto_kline",
            dataset_name="加密货币 K线数据",
            description="统一 K线数据，CCXT fetch_ohlcv 格式，按插入时间排序。",
            function_name="get_kline(symbol, timeframe, limit, before_time)",
            return_type="list[dict]",
            fields_schema=[
                {"name": "time", "type": "int", "description": "Unix 秒时间戳 (UTC)", "nullable": False, "example": 1712620800},
                {"name": "open", "type": "float", "description": "开盘价", "nullable": False, "example": 65430.5},
                {"name": "high", "type": "float", "description": "最高价", "nullable": False, "example": 65800.0},
                {"name": "low", "type": "float", "description": "最低价", "nullable": False, "example": 65200.0},
                {"name": "close", "type": "float", "description": "收盘价", "nullable": False, "example": 65600.0},
                {"name": "volume", "type": "float", "description": "成交量", "nullable": False, "example": 12500.5},
            ],
            sample_output=[
                {"time": 1712620800, "open": 65430.5, "high": 65800.0, "low": 65200.0, "close": 65600.0, "volume": 12500.5},
                {"time": 1712624400, "open": 65600.0, "high": 66100.0, "low": 65500.0, "close": 66000.0, "volume": 13800.2},
            ],
            coverage_text="CCXT unified format. Supports any CCXT exchange pair symbol.",
            source_file_ref="app/data_sources/crypto.py",
        ),
        DataSourceDataset(
            dataset_code="crypto_ticker",
            dataset_name="加密货币实时报价",
            description="CCXT fetch_ticker 格式的完整报价数据。",
            function_name="get_ticker(symbol)",
            return_type="dict",
            fields_schema=[
                {"name": "symbol", "type": "str", "description": "交易对符号", "nullable": False, "example": "BTC/USDT"},
                {"name": "last", "type": "float", "description": "最新价", "nullable": False, "example": 65430.5},
                {"name": "bid", "type": "float", "description": "买一价", "nullable": True, "example": 65430.0},
                {"name": "ask", "type": "float", "description": "卖一价", "nullable": True, "example": 65431.0},
                {"name": "high", "type": "float", "description": "24h最高", "nullable": False, "example": 66500.0},
                {"name": "low", "type": "float", "description": "24h最低", "nullable": False, "example": 64800.0},
                {"name": "open", "type": "float", "description": "24h开盘", "nullable": False, "example": 65000.0},
                {"name": "close", "type": "float", "description": "24h收盘", "nullable": False, "example": 65430.5},
                {"name": "baseVolume", "type": "float", "description": "基础币成交量", "nullable": False, "example": 12500.5},
                {"name": "quoteVolume", "type": "float", "description": "报价币成交量", "nullable": False, "example": 820000000},
                {"name": "change", "type": "float", "description": "涨跌额", "nullable": True, "example": 430.5},
                {"name": "percentage", "type": "float", "description": "涨跌幅(%)", "nullable": True, "example": 0.66},
                {"name": "previousClose", "type": "float", "description": "昨收价", "nullable": True, "example": 65000.0},
            ],
            sample_output={
                "symbol": "BTC/USDT", "last": 65430.5, "bid": 65430.0, "ask": 65431.0,
                "high": 66500.0, "low": 64800.0, "open": 65000.0, "close": 65430.5,
                "baseVolume": 12500.5, "quoteVolume": 820000000, "change": 430.5,
                "percentage": 0.66, "previousClose": 65000.0,
            },
            coverage_text="Standard CCXT fetch_ticker format.",
            source_file_ref="app/data_sources/crypto.py",
        ),
    ],

    # ── USStock ───────────────────────────────────────────────────
    "us_stock": [
        DataSourceDataset(
            dataset_code="us_stock_kline",
            dataset_name="美股 K线数据",
            description="yfinance 获取的美股 K线数据。",
            function_name="get_kline(symbol, timeframe, limit, before_time)",
            return_type="list[dict]",
            fields_schema=[
                {"name": "time", "type": "int", "description": "Unix 秒时间戳 (UTC)", "nullable": False, "example": 1712620800},
                {"name": "open", "type": "float", "description": "开盘价", "nullable": False},
                {"name": "high", "type": "float", "description": "最高价", "nullable": False},
                {"name": "low", "type": "float", "description": "最低价", "nullable": False},
                {"name": "close", "type": "float", "description": "收盘价", "nullable": False},
                {"name": "volume", "type": "float", "description": "成交量", "nullable": False},
            ],
            sample_output=[
                {"time": 1712620800, "open": 178.5, "high": 180.2, "low": 177.8, "close": 179.6, "volume": 52000000},
            ],
            coverage_text="All timeframes supported (1m, 5m, 15m, 30m, 1H, 4H, 1D, 1W).",
            source_file_ref="app/data_sources/us_stock.py",
        ),
        DataSourceDataset(
            dataset_code="us_stock_ticker",
            dataset_name="美股实时报价",
            description="3-tier fallback: yfinance fast_info -> yfinance info -> 1min K-line. Finnhub ticker as optional backup.",
            function_name="get_ticker(symbol)",
            return_type="dict",
            fields_schema=[
                {"name": "last", "type": "float", "description": "当前价格", "nullable": False, "example": 179.6},
                {"name": "change", "type": "float", "description": "涨跌额", "nullable": False, "example": 1.1},
                {"name": "changePercent", "type": "float", "description": "涨跌幅(%)", "nullable": False, "example": 0.62},
                {"name": "high", "type": "float", "description": "日内最高", "nullable": False, "example": 180.2},
                {"name": "low", "type": "float", "description": "日内最低", "nullable": False, "example": 177.8},
                {"name": "open", "type": "float", "description": "开盘价", "nullable": False, "example": 178.5},
                {"name": "previousClose", "type": "float", "description": "昨收价", "nullable": False, "example": 178.5},
            ],
            sample_output={
                "last": 179.6, "change": 1.1, "changePercent": 0.62,
                "high": 180.2, "low": 177.8, "open": 178.5, "previousClose": 178.5,
            },
            coverage_text="Any US stock symbol via yfinance.",
            source_file_ref="app/data_sources/us_stock.py",
        ),
    ],

    # ── CNStock ───────────────────────────────────────────────────
    "cn_stock": [
        DataSourceDataset(
            dataset_code="cn_kline",
            dataset_name="A股 K线数据",
            description="4-tier fallback: TwelveData -> Tencent fqkline -> yfinance -> AkShare(东方财富)。",
            function_name="get_kline(symbol, timeframe, limit, before_time)",
            return_type="list[dict]",
            fields_schema=[
                {"name": "time", "type": "int", "description": "Unix 秒时间戳 (UTC)", "nullable": False},
                {"name": "open", "type": "float", "description": "开盘价", "nullable": False},
                {"name": "high", "type": "float", "description": "最高价", "nullable": False},
                {"name": "low", "type": "float", "description": "最低价", "nullable": False},
                {"name": "close", "type": "float", "description": "收盘价", "nullable": False},
                {"name": "volume", "type": "float", "description": "成交量", "nullable": False},
            ],
            coverage_text="A stock symbols in Tencent format (e.g. SH600519, SZ000001).",
            source_file_ref="app/data_sources/cn_stock.py",
        ),
        DataSourceDataset(
            dataset_code="cn_ticker",
            dataset_name="A股实时报价",
            description="4-tier fallback ticker with name and symbol fields.",
            function_name="get_ticker(symbol)",
            return_type="dict",
            fields_schema=[
                {"name": "last", "type": "float", "description": "最新价", "nullable": False},
                {"name": "change", "type": "float", "description": "涨跌额", "nullable": False},
                {"name": "changePercent", "type": "float", "description": "涨跌幅(%)", "nullable": False},
                {"name": "high", "type": "float", "description": "日内最高", "nullable": False},
                {"name": "low", "type": "float", "description": "日内最低", "nullable": False},
                {"name": "open", "type": "float", "description": "开盘价", "nullable": False},
                {"name": "previousClose", "type": "float", "description": "昨收价", "nullable": False},
                {"name": "name", "type": "str", "description": "股票中文名称", "nullable": True, "example": "贵州茅台"},
                {"name": "symbol", "type": "str", "description": "腾讯代码", "nullable": False, "example": "SH600519"},
            ],
            coverage_text="A股主板/创业板/科创板/北交所所有标的.",
            source_file_ref="app/data_sources/cn_stock.py",
        ),
    ],

    # ── HKStock ───────────────────────────────────────────────────
    "hk_stock": [
        DataSourceDataset(
            dataset_code="hk_kline",
            dataset_name="港股 K线数据",
            description="Same 4-tier fallback as CNStock.",
            function_name="get_kline(symbol, timeframe, limit, before_time)",
            return_type="list[dict]",
            fields_schema=[
                {"name": "time", "type": "int", "description": "Unix 秒时间戳 (UTC)", "nullable": False},
                {"name": "open", "type": "float", "description": "开盘价", "nullable": False},
                {"name": "high", "type": "float", "description": "最高价", "nullable": False},
                {"name": "low", "type": "float", "description": "最低价", "nullable": False},
                {"name": "close", "type": "float", "description": "收盘价", "nullable": False},
                {"name": "volume", "type": "float", "description": "成交量", "nullable": False},
            ],
            coverage_text="HK symbols in Tencent format (e.g. HK00700 for Tencent).",
            source_file_ref="app/data_sources/hk_stock.py",
        ),
        DataSourceDataset(
            dataset_code="hk_ticker",
            dataset_name="港股实时报价",
            description="4-tier fallback ticker.",
            function_name="get_ticker(symbol)",
            return_type="dict",
            fields_schema=[
                {"name": "last", "type": "float", "description": "最新价"},
                {"name": "change", "type": "float", "description": "涨跌额"},
                {"name": "changePercent", "type": "float", "description": "涨跌幅(%)"},
                {"name": "high", "type": "float", "description": "日内最高"},
                {"name": "low", "type": "float", "description": "日内最低"},
                {"name": "open", "type": "float", "description": "开盘价"},
                {"name": "previousClose", "type": "float", "description": "昨收价"},
                {"name": "name", "type": "str", "description": "股票中文名称", "nullable": True},
                {"name": "symbol", "type": "str", "description": "腾讯代码", "nullable": False, "example": "HK00700"},
            ],
            source_file_ref="app/data_sources/hk_stock.py",
        ),
    ],

    # ── Forex ─────────────────────────────────────────────────────
    "forex": [
        DataSourceDataset(
            dataset_code="forex_kline",
            dataset_name="外汇 K线数据",
            description="3-tier fallback: TwelveData -> Tiingo -> yfinance.",
            function_name="get_kline(symbol, timeframe, limit, before_time)",
            return_type="list[dict]",
            fields_schema=[
                {"name": "time", "type": "int"}, {"name": "open", "type": "float"},
                {"name": "high", "type": "float"}, {"name": "low", "type": "float"},
                {"name": "close", "type": "float"}, {"name": "volume", "type": "float"},
            ],
            coverage_text="14 major forex pairs (EUR/USD, GBP/USD, USD/JPY, etc.).",
            source_file_ref="app/data_sources/forex.py",
        ),
        DataSourceDataset(
            dataset_code="forex_ticker",
            dataset_name="外汇实时报价",
            description="Latest forex rates with bid/ask when available.",
            function_name="get_ticker(symbol)",
            return_type="dict",
            fields_schema=[
                {"name": "last", "type": "float", "description": "最新汇率", "nullable": False},
                {"name": "bid", "type": "float", "description": "买价 (Tiingo)", "nullable": True},
                {"name": "ask", "type": "float", "description": "卖价 (Tiingo)", "nullable": True},
                {"name": "change", "type": "float", "description": "涨跌额"},
                {"name": "changePercent", "type": "float", "description": "涨跌幅(%)"},
                {"name": "previousClose", "type": "float", "description": "昨收"},
                {"name": "symbol", "type": "str", "description": "交易对", "example": "EUR/USD"},
            ],
            coverage_text="Rates rounded to 5 decimal places.",
            source_file_ref="app/data_sources/forex.py",
        ),
    ],

    # ── Futures ───────────────────────────────────────────────────
    "futures": [
        DataSourceDataset(
            dataset_code="futures_kline",
            dataset_name="期货 K线数据",
            description="Traditional + crypto futures.",
            function_name="get_kline(symbol, timeframe, limit, before_time)",
            return_type="list[dict]",
            fields_schema=[
                {"name": "time", "type": "int"}, {"name": "open", "type": "float"},
                {"name": "high", "type": "float"}, {"name": "low", "type": "float"},
                {"name": "close", "type": "float"}, {"name": "volume", "type": "float"},
            ],
            coverage_text="Traditional(GC, SI, CL, NG, HG) + crypto futures via CCXT Binance Futures.",
            source_file_ref="app/data_sources/futures.py",
        ),
        DataSourceDataset(
            dataset_code="futures_ticker",
            dataset_name="期货实时报价",
            description="Latest futures prices with change info.",
            function_name="get_ticker(symbol)",
            return_type="dict",
            fields_schema=[
                {"name": "symbol", "type": "str", "example": "GC=F"},
                {"name": "last", "type": "float"},
                {"name": "change", "type": "float"},
                {"name": "changePercent", "type": "float"},
                {"name": "previousClose", "type": "float"},
            ],
            source_file_ref="app/data_sources/futures.py",
        ),
    ],

    # ── Polymarket ────────────────────────────────────────────────
    "polymarket": [
        DataSourceDataset(
            dataset_code="polymarket_trending",
            dataset_name="Polymarket热门预测市场",
            description="热门预测市场列表。",
            function_name="get_trending_markets(category, limit)",
            return_type="list[dict]",
            fields_schema=[
                {"name": "market_id", "type": "str", "description": "Polymarket 市场 ID", "nullable": False, "example": "0x1234..."},
                {"name": "question", "type": "str", "description": "预测问题标题", "nullable": False, "example": "Will BTC reach $100k by 2025?"},
                {"name": "current_probability", "type": "float", "description": "当前 YES 概率 (0~1)", "nullable": False, "example": 0.45},
            ],
            sample_output=[
                {"market_id": "0x1234...", "question": "Will BTC reach $100k by 2025?", "current_probability": 0.45},
            ],
            coverage_text="Polymarket trending markets via gamma-api/public endpoints.",
            source_file_ref="app/data_sources/polymarket.py",
        ),
    ],

    # ── Crypto Provider ───────────────────────────────────────────
    "crypto_provider": [
        DataSourceDataset(
            dataset_code="crypto_prices",
            dataset_name="加密货币价格列表",
            description="15 个主流加密货币的实时价格、涨跌幅、市值等。3-tier fallback: CCXT -> yfinance -> CoinGecko。",
            function_name="fetch_crypto_prices()",
            return_type="list[dict]",
            fields_schema=[
                {"name": "symbol", "type": "str", "description": "币种符号", "nullable": False, "example": "BTC"},
                {"name": "name", "type": "str", "description": "全名", "nullable": False, "example": "Bitcoin"},
                {"name": "price", "type": "float", "description": "当前价格 (USD)", "nullable": False, "example": 65430.5},
                {"name": "change_24h", "type": "float", "description": "24h涨跌幅(%)", "nullable": False, "example": 0.66},
                {"name": "change_7d", "type": "float", "description": "7日涨跌幅(%)", "nullable": True, "example": 2.34},
                {"name": "market_cap", "type": "float", "description": "市值", "nullable": False, "example": 1280000000000},
                {"name": "volume_24h", "type": "float", "description": "24h成交量", "nullable": False, "example": 45000000000},
                {"name": "image", "type": "str", "description": "币种图标URL", "nullable": True},
                {"name": "category", "type": "str", "description": "分类标签", "nullable": False, "example": "crypto"},
            ],
            sample_output=[
                {"symbol": "BTC", "name": "Bitcoin", "price": 65430.5, "change_24h": 0.66, "change_7d": 2.34,
                 "market_cap": 1280000000000, "volume_24h": 45000000000, "image": "", "category": "crypto"},
            ],
            coverage_text="15 coins: BTC, ETH, BNB, SOL, XRP, ADA, DOGE, AVAX, DOT, POL, LINK, LTC, ATOM, XLM, +more.",
            source_file_ref="app/data_providers/crypto.py",
        ),
        DataSourceDataset(
            dataset_code="crypto_heatmap",
            dataset_name="加密货币热力图数据",
            description="CoinGecko / CoinCap 来源的加密热力图。",
            function_name="fetch_crypto_heatmap_coingecko() / fetch_crypto_heatmap_coincap()",
            return_type="list[dict]",
            fields_schema=[
                {"name": "symbol", "type": "str"}, {"name": "name", "type": "str"},
                {"name": "price", "type": "float"}, {"name": "change_24h", "type": "float"},
                {"name": "market_cap", "type": "float"}, {"name": "volume_24h", "type": "float"},
                {"name": "image", "type": "str"}, {"name": "category", "type": "str", "example": "crypto"},
            ],
            source_file_ref="app/data_providers/crypto.py",
        ),
    ],

    # ── Forex Provider ────────────────────────────────────────────
    "forex_provider": [
        DataSourceDataset(
            dataset_code="forex_pairs",
            dataset_name="主要货币对概览",
            description="8 个主要货币对的实时汇率。",
            function_name="fetch_forex_pairs()",
            return_type="list[dict]",
            fields_schema=[
                {"name": "symbol", "type": "str", "example": "EUR/USD"},
                {"name": "name", "type": "str"},
                {"name": "name_cn", "type": "str", "description": "中文名称"},
                {"name": "name_en", "type": "str"},
                {"name": "price", "type": "float", "description": "汇率(5位小数)"},
                {"name": "change", "type": "float", "description": "涨跌幅(%)"},
                {"name": "base", "type": "str", "example": "EUR"},
                {"name": "quote", "type": "str", "example": "USD"},
                {"name": "category", "type": "str", "example": "forex"},
            ],
            coverage_text="8 pairs: EUR/USD, GBP/USD, USD/JPY, USD/CNH, AUD/USD, USD/CAD, USD/CHF, NZD/USD.",
            source_file_ref="app/data_providers/forex.py",
        ),
    ],

    # ── Indices Provider ──────────────────────────────────────────
    "indices_provider": [
        DataSourceDataset(
            dataset_code="stock_indices",
            dataset_name="全球股指概览",
            description="10 个全球主要股票指数。",
            function_name="fetch_stock_indices()",
            return_type="list[dict]",
            fields_schema=[
                {"name": "symbol", "type": "str", "example": "^GSPC"},
                {"name": "name_cn", "type": "str", "description": "中文名"},
                {"name": "name_en", "type": "str", "description": "英文名"},
                {"name": "price", "type": "float", "description": "指数点数"},
                {"name": "change", "type": "float", "description": "涨跌幅(%)"},
                {"name": "region", "type": "str", "description": "地区代码", "example": "US"},
                {"name": "flag", "type": "str", "description": "国旗emoji"},
                {"name": "lat", "type": "float", "description": "纬度(地图展示)"},
                {"name": "lng", "type": "float", "description": "经度(地图展示)"},
                {"name": "category", "type": "str", "example": "index"},
            ],
            coverage_text="10 indices: S&P500, Dow, NASDAQ, DAX, FTSE100, CAC40, Nikkei225, KOSPI, ASX200, SENSEX.",
            source_file_ref="app/data_providers/indices.py",
        ),
    ],

    # ── Commodities Provider ──────────────────────────────────────
    "commodities_provider": [
        DataSourceDataset(
            dataset_code="commodities",
            dataset_name="大宗商品价格",
            description="6 种主要大宗商品的美元价格。",
            function_name="fetch_commodities()",
            return_type="list[dict]",
            fields_schema=[
                {"name": "symbol", "type": "str", "example": "GC=F"},
                {"name": "name_cn", "type": "str", "description": "中文名"},
                {"name": "name_en", "type": "str"},
                {"name": "price", "type": "float"},
                {"name": "change", "type": "float", "description": "涨跌幅(%)"},
                {"name": "unit", "type": "str", "description": "计价单位"},
                {"name": "category", "type": "str", "example": "commodity"},
            ],
            coverage_text="6 commodities: Gold(GC), Silver(SI), WTI(CL), Brent(BZ), Copper(HG), Natural Gas(NG).",
            source_file_ref="app/data_providers/commodities.py",
        ),
    ],

    # ── Heatmap Provider ──────────────────────────────────────────
    "heatmap_provider": [
        DataSourceDataset(
            dataset_code="heatmap_data",
            dataset_name="市场热力图聚合数据",
            description="跨市场热力图：加密 + 板块ETF + 外汇 + 大宗 + 股指。",
            function_name="generate_heatmap_data()",
            return_type="dict",
            fields_schema=[
                {"name": "crypto", "type": "list[dict]", "description": "加密货币(15个)"},
                {"name": "sectors", "type": "list[dict]", "description": "行业板块ETF(10个), 每个含代表股列表"},
                {"name": "forex", "type": "list[dict]", "description": "货币对(8个)"},
                {"name": "commodities", "type": "list[dict]", "description": "大宗商品(6个)"},
                {"name": "indices", "type": "list[dict]", "description": "股指(10个)"},
            ],
            coverage_text="Sectors: XLK(科技), XLF(金融), XLV(医疗), XLY(消费), XLE(能源), XLI(工业), XLB(材料), XLU(公用), XLRE(房地产), XLC(通信).",
            source_file_ref="app/data_providers/heatmap.py",
        ),
    ],

    # ── News Provider ─────────────────────────────────────────────
    "news_provider": [
        DataSourceDataset(
            dataset_code="financial_news",
            dataset_name="财经新闻",
            description="中英文双语财经新闻，来源为已配置的搜索服务(Tavily/Google/Bing)。",
            function_name="fetch_financial_news(lang)",
            return_type="dict",
            fields_schema=[
                {"name": "cn", "type": "list[dict]", "description": "中文新闻列表"},
                {"name": "en", "type": "list[dict]", "description": "英文新闻列表"},
            ],
            sample_output={
                "cn": [{"title": "美股三大指数集体收涨", "link": "...", "snippet": "摘要", "source": "来源", "published": "2026-04-25", "category": "美股行情", "lang": "cn"}],
                "en": [{"title": "S&P 500 Hits New High", "link": "...", "snippet": "...", "source": "Reuters", "published": "2026-04-25", "category": "US Markets", "lang": "en"}],
            },
            source_file_ref="app/data_providers/news.py",
        ),
        DataSourceDataset(
            dataset_code="economic_calendar",
            dataset_name="经济日历事件",
            description="预设 9 类重大经济事件日历，含预期影响分析。",
            function_name="get_economic_calendar()",
            return_type="list[dict]",
            fields_schema=[
                {"name": "id", "type": "int"},
                {"name": "name", "type": "str", "description": "事件名称(中)"},
                {"name": "name_en", "type": "str"},
                {"name": "country", "type": "str", "example": "US"},
                {"name": "date", "type": "str", "example": "2026-04-25"},
                {"name": "time", "type": "str", "example": "08:30"},
                {"name": "importance", "type": "str", "example": "high"},
                {"name": "actual", "type": "str|null"},
                {"name": "forecast", "type": "str", "example": "180K"},
                {"name": "previous", "type": "str", "example": "175K"},
                {"name": "expected_impact", "type": "str"},
                {"name": "is_released", "type": "bool"},
            ],
            coverage_text="9 event types: NFP, FOMC, CPI, ECB, BoJ, Jobless Claims, BoE, Retail Sales, OPEC.",
            source_file_ref="app/data_providers/news.py",
        ),
    ],

    # ── Sentiment Provider ────────────────────────────────────────
    "sentiment_provider": [
        DataSourceDataset(
            dataset_code="fear_greed_index",
            dataset_name="恐惧贪婪指数",
            description="alternative.me 来源。",
            function_name="fetch_fear_greed_index()",
            return_type="dict",
            fields_schema=[
                {"name": "value", "type": "int", "description": "0~100", "example": 45},
                {"name": "classification", "type": "str", "example": "Fear"},
                {"name": "timestamp", "type": "int"},
                {"name": "source", "type": "str", "example": "alternative.me"},
            ],
            sample_output={"value": 45, "classification": "Fear", "timestamp": 1712620800, "source": "alternative.me"},
            source_file_ref="app/data_providers/sentiment.py",
        ),
        DataSourceDataset(
            dataset_code="vix",
            dataset_name="VIX波动率指数",
            description="CBOE波动率指数，含等级解读。",
            function_name="fetch_vix()",
            return_type="dict",
            fields_schema=[
                {"name": "value", "type": "float"},
                {"name": "change", "type": "float"},
                {"name": "level", "type": "str", "example": "moderate"},
                {"name": "interpretation", "type": "str"},
                {"name": "interpretation_en", "type": "str"},
            ],
            source_file_ref="app/data_providers/sentiment.py",
        ),
        DataSourceDataset(
            dataset_code="dollar_index",
            dataset_name="美元指数 (DXY)",
            description="美元强弱指数，含等级解读。",
            function_name="fetch_dollar_index()",
            return_type="dict",
            fields_schema=[
                {"name": "value", "type": "float"},
                {"name": "change", "type": "float"},
                {"name": "level", "type": "str", "example": "strong"},
                {"name": "interpretation", "type": "str"},
            ],
            source_file_ref="app/data_providers/sentiment.py",
        ),
        DataSourceDataset(
            dataset_code="yield_curve",
            dataset_name="美债收益率曲线",
            description="10Y-2Y利差及信号解读。",
            function_name="fetch_yield_curve()",
            return_type="dict",
            fields_schema=[
                {"name": "yield_10y", "type": "float"}, {"name": "yield_2y", "type": "float"},
                {"name": "spread", "type": "float"}, {"name": "change", "type": "float"},
                {"name": "level", "type": "str"}, {"name": "signal", "type": "str"},
                {"name": "interpretation", "type": "str"},
            ],
            source_file_ref="app/data_providers/sentiment.py",
        ),
        DataSourceDataset(
            dataset_code="vxn",
            dataset_name="NASDAQ波动率 (VXN)",
            description="NASDAQ-100波动率指数。",
            return_type="dict",
            coverage_text="NASDAQ-100波动率指数.",
            source_file_ref="app/data_providers/sentiment.py",
        ),
        DataSourceDataset(
            dataset_code="gvz",
            dataset_name="黄金波动率 (GVZ)",
            description="Gold ETF波动率指数。",
            return_type="dict",
            coverage_text="Gold ETF波动率指数.",
            source_file_ref="app/data_providers/sentiment.py",
        ),
        DataSourceDataset(
            dataset_code="put_call_ratio",
            dataset_name="Put/Call比率",
            description="VIX/VIX3M比率信号。",
            function_name="fetch_put_call_ratio()",
            return_type="dict",
            fields_schema=[
                {"name": "value", "type": "float"},
                {"name": "vix", "type": "float"}, {"name": "vix3m", "type": "float"},
                {"name": "level", "type": "str"}, {"name": "signal", "type": "str"},
            ],
            source_file_ref="app/data_providers/sentiment.py",
        ),
    ],

    # ── Opportunities Provider ────────────────────────────────────
    "opportunities_provider": [
        DataSourceDataset(
            dataset_code="crypto_opportunities",
            dataset_name="加密货币交易机会",
            description="Crypto 超买超卖/动量/盘整信号。",
            function_name="analyze_crypto_opportunities()",
            return_type="list[dict]",
            sample_output=[{
                "symbol": "BTC", "name": "Bitcoin", "price": 65430.5, "change_24h": 0.66, "change_7d": 2.34,
                "signal": "bullish_momentum", "strength": "strong",
                "reason": "BTC 24h上涨0.66%,动量指标偏多",
                "market": "Crypto",
            }],
            source_file_ref="app/data_providers/opportunities.py",
        ),
        DataSourceDataset(
            dataset_code="us_stock_opportunities",
            dataset_name="美股交易机会",
            description="15 只热门美股机会扫描。",
            function_name="analyze_us_stock_opportunities()",
            return_type="list[dict]",
            source_file_ref="app/data_providers/opportunities.py",
        ),
        DataSourceDataset(
            dataset_code="cn_stock_opportunities",
            dataset_name="A股交易机会",
            description="20 只热门A股机会扫描。",
            function_name="analyze_cn_stock_opportunities()",
            return_type="list[dict]",
            source_file_ref="app/data_providers/opportunities.py",
        ),
        DataSourceDataset(
            dataset_code="hk_stock_opportunities",
            dataset_name="港股交易机会",
            description="15 只热门港股机会扫描。",
            function_name="analyze_hk_stock_opportunities()",
            return_type="list[dict]",
            source_file_ref="app/data_providers/opportunities.py",
        ),
        DataSourceDataset(
            dataset_code="forex_opportunities",
            dataset_name="外汇交易机会",
            description="主要货币对机会扫描。",
            function_name="analyze_forex_opportunities()",
            return_type="list[dict]",
            source_file_ref="app/data_providers/opportunities.py",
        ),
        DataSourceDataset(
            dataset_code="polymarket_opportunities",
            dataset_name="预测市场交易机会",
            description="AI 分析的 Polymarket 机会，含预测概率和建议。",
            function_name="analyze_polymarket_opportunities()",
            return_type="list[dict]",
            fields_schema=[
                {"name": "symbol", "type": "str"},
                {"name": "market_id", "type": "str"},
                {"name": "ai_analysis.predicted_probability", "type": "float"},
                {"name": "ai_analysis.recommendation", "type": "str"},
                {"name": "ai_analysis.confidence_score", "type": "float"},
                {"name": "ai_analysis.opportunity_score", "type": "float"},
            ],
            source_file_ref="app/data_providers/opportunities.py",
        ),
    ],

    # ── Adanos Provider ───────────────────────────────────────────
    "adanos_provider": [
        DataSourceDataset(
            dataset_code="adanos_sentiment",
            dataset_name="Adanos 美股情感分析",
            description="Reddit/X/News/Polymarket 多渠道情感分数。无 API Key 时返回 enabled=false。",
            function_name="fetch_adanos_market_sentiment(tickers, source, days)",
            return_type="dict",
            fields_schema=[
                {"name": "enabled", "type": "bool"},
                {"name": "provider", "type": "str", "example": "adanos"},
                {"name": "source", "type": "str", "example": "reddit"},
                {"name": "days", "type": "int"},
                {"name": "tickers", "type": "list[str]"},
                {"name": "stocks[].ticker", "type": "str"},
                {"name": "stocks[].sentiment_score", "type": "float|null"},
                {"name": "stocks[].buzz_score", "type": "float|null"},
                {"name": "stocks[].bullish_pct", "type": "float|null"},
                {"name": "stocks[].bearish_pct", "type": "float|null"},
                {"name": "stocks[].mentions", "type": "int|null"},
            ],
            source_file_ref="app/data_providers/adanos_sentiment.py",
        ),
    ],

    # ── CN/HK Fundamentals ────────────────────────────────────────
    "cn_hk_fundamentals": [
        DataSourceDataset(
            dataset_code="fundamentals",
            dataset_name="A/港股基本面数据",
            description="30+ 基本面指标（估值/财务/增长/分红），TwelveData主源，AkShare备选。",
            function_name="fetch_twelvedata_fundamental(tencent_code, is_hk)",
            return_type="dict",
            fields_schema=[
                {"name": "source", "type": "str"},
                {"name": "market_cap", "type": "float|null"},
                {"name": "pe_ratio", "type": "float|null", "description": "市盈率(TTM)"},
                {"name": "forward_pe", "type": "float|null"},
                {"name": "pb_ratio", "type": "float|null", "description": "市净率(MRQ)"},
                {"name": "ps_ratio", "type": "float|null"},
                {"name": "peg", "type": "float|null"},
                {"name": "enterprise_value", "type": "float|null"},
                {"name": "profit_margin", "type": "float|null"},
                {"name": "gross_margin", "type": "float|null"},
                {"name": "operating_margin", "type": "float|null"},
                {"name": "roe", "type": "float|null"},
                {"name": "roa", "type": "float|null"},
                {"name": "revenue_growth", "type": "float|null"},
                {"name": "earnings_growth", "type": "float|null"},
                {"name": "revenue_ttm", "type": "float|null"},
                {"name": "ebitda", "type": "float|null"},
                {"name": "eps", "type": "float|null"},
                {"name": "debt_to_equity", "type": "float|null"},
                {"name": "current_ratio", "type": "float|null"},
                {"name": "total_debt", "type": "float|null"},
                {"name": "total_cash", "type": "float|null"},
                {"name": "operating_cash_flow", "type": "float|null"},
                {"name": "free_cash_flow", "type": "float|null"},
                {"name": "total_shares", "type": "float|null"},
                {"name": "float_shares", "type": "float|null"},
                {"name": "52w_high", "type": "float|null"},
                {"name": "52w_low", "type": "float|null"},
                {"name": "beta", "type": "float|null"},
                {"name": "dividend_yield", "type": "float|null"},
                {"name": "dividend_rate", "type": "float|null"},
            ],
            coverage_text="A/港股全量基本面。TwelveData (/statistics, /profile, /earnings, /income_statement, /balance_sheet, /cash_flow) -> AkShare(东方财富).",
            source_file_ref="app/data_providers/cn_hk_fundamentals.py",
        ),
        DataSourceDataset(
            dataset_code="cn_fundamentals_akshare",
            dataset_name="A股基本面(AkShare备选)",
            description="东方财富来源的 A 股基本面备选，用于 TwelveData 不可用时的降级。",
            function_name="fetch_cn_fundamental_akshare(tencent_code)",
            return_type="dict",
            fields_schema=[
                {"name": "source", "type": "str", "example": "akshare_em"},
                {"name": "market_cap", "type": "float|null"},
                {"name": "float_market_cap", "type": "float|null"},
                {"name": "industry", "type": "str|null"},
                {"name": "total_shares", "type": "float|null"},
                {"name": "float_shares", "type": "float|null"},
                {"name": "pe_ratio", "type": "float|null"},
                {"name": "pb_ratio", "type": "float|null"},
                {"name": "ps_ratio", "type": "float|null"},
                {"name": "peg", "type": "float|null"},
            ],
            source_file_ref="app/data_sources/cn_hk_fundamentals.py",
        ),
        DataSourceDataset(
            dataset_code="hk_fundamentals_akshare",
            dataset_name="港股基本面(AkShare备选)",
            description="东方财富来源的港股基本面备选。",
            function_name="fetch_hk_fundamental_akshare(tencent_code)",
            return_type="dict",
            fields_schema=[
                {"name": "source", "type": "str", "example": "akshare_em"},
                {"name": "pe_ratio", "type": "float|null"},
                {"name": "pb_ratio", "type": "float|null"},
                {"name": "eps", "type": "float|null"},
                {"name": "roe", "type": "float|null"},
                {"name": "profit_margin", "type": "float|null"},
                {"name": "market_cap", "type": "float|null"},
                {"name": "dividend_yield", "type": "float|null"},
            ],
            source_file_ref="app/data_sources/cn_hk_fundamentals.py",
        ),
    ],

    # ── MarketData Collector ──────────────────────────────────────
    "market_data_collector": [
        DataSourceDataset(
            dataset_code="collected_market_data",
            dataset_name="采集的市场数据",
            description="后台定时采集的聚合市场数据。",
            function_name="collect()",
            return_type="dict",
            fields_schema=[
                {"name": "status", "type": "str"},
                {"name": "collected_at", "type": "str"},
                {"name": "symbols_count", "type": "int"},
            ],
            source_file_ref="app/collectors/registry.py",
        ),
    ],
}


# ──────────────────────────────────────────────────────────────────────
# 3. Default API Key entries  (example public keys referencing env vars)
# ──────────────────────────────────────────────────────────────────────

def build_default_api_keys(source_map: dict[str, int]) -> list[ApiKey]:
    """
    Create placeholder public ApiKey rows for sources that need an API key.
    These entries reference the env-var-based key — actual values still
    come from .env. Admin can later add private keys per-user via UI.
    """
    keys: list[ApiKey] = []

    # Sources that need TwelveData
    td_sources = ["cn_stock", "hk_stock", "forex", "futures", "cn_hk_fundamentals"]
    for code in td_sources:
        sid = source_map.get(code)
        if sid:
            # Encrypted placeholder — will be replaced with real encrypted key via admin UI
            keys.append(ApiKey(
                source_config_id=sid,
                key_type="public",
                user_id=None,
                key_alias="TwelveData 系统密钥 #1",
                encrypted_key_value="__PLACEHOLDER__TWELVE_DATA__",
                key_hint="****env",
                status="active",
                weight=1,
                total_calls=0,
            ))

    # Finnhub for US stock (optional)
    if "us_stock" in source_map:
        keys.append(ApiKey(
            source_config_id=source_map["us_stock"],
            key_type="public",
            user_id=None,
            key_alias="Finnhub 系统密钥 #1",
            encrypted_key_value="__PLACEHOLDER__FINNHUB__",
            key_hint="****env",
            status="active",
            weight=1,
            total_calls=0,
        ))

    return keys


# ──────────────────────────────────────────────────────────────────────
# 4. Main seed runner
# ──────────────────────────────────────────────────────────────────────

def seed():
    logger.info("Seeding data source meta tables …")

    with get_session() as session:
        # ── 4a. Upsert DataSourceConfig ────────────────────────
        source_map: dict[str, int] = {}  # source_code -> id
        for ds in DATA_SOURCES:
            existing = session.execute(
                sa_text(
                    "SELECT id FROM qd_data_source_configs "
                    "WHERE source_code = :code"
                ).bindparams(code=ds.source_code)
            ).scalar_one_or_none()

            if existing:
                # Use SQLAlchemy Core update() so JSONB/list columns are properly adapted
                from app.models.data_source_meta import DataSourceConfig as _DSC
                session.execute(
                    _update(_DSC).where(_DSC.id == existing).values(
                        source_name=ds.source_name,
                        layer=ds.layer,
                        market_categories=ds.market_categories,
                        load_balance_strategy=ds.load_balance_strategy,
                        config_json=ds.config_json,
                        dependencies=ds.dependencies,
                        notes=ds.notes,
                        enabled=True,
                    )
                )
                source_map[ds.source_code] = existing
                logger.info("  Updated: %s", ds.source_code)
            else:
                session.add(ds)
                session.flush()
                source_map[ds.source_code] = ds.id
                logger.info("  Created: %s", ds.source_code)

        # ── 4b. Upsert DataSourceDataset ───────────────────────
        for source_code, datasets in _datasets_by_source.items():
            sid = source_map.get(source_code)
            if not sid:
                logger.warning("  Skipping datasets for unknown source: %s", source_code)
                continue
            for ds in datasets:
                ds.source_id = sid
                existing_ds_id = session.execute(
                    sa_text(
                        "SELECT id FROM qd_data_source_datasets "
                        "WHERE dataset_code = :code"
                    ).bindparams(code=ds.dataset_code)
                ).scalar_one_or_none()

                if existing_ds_id:
                    from app.models.data_source_meta import DataSourceDataset as _DSD
                    session.execute(
                        _update(_DSD).where(_DSD.id == existing_ds_id).values(
                            dataset_name=ds.dataset_name,
                            description=ds.description,
                            function_name=ds.function_name,
                            return_type=ds.return_type,
                            fields_schema=ds.fields_schema,
                            sample_output=ds.sample_output,
                            coverage_text=ds.coverage_text,
                            source_file_ref=ds.source_file_ref,
                            source_id=sid,
                        )
                    )
                    logger.info("  Updated dataset: %s", ds.dataset_code)
                else:
                    session.add(ds)
                    logger.info("  Created dataset: %s", ds.dataset_code)

        # ── 4c. Upsert ApiKey entries ──────────────────────────
        default_keys = build_default_api_keys(source_map)
        for ak in default_keys:
            existing_key = session.execute(
                sa_text("""
                    SELECT id FROM qd_api_keys
                    WHERE source_config_id = :sid
                      AND key_type = :kt
                      AND (user_id IS NULL OR user_id = :uid)
                      AND key_alias = :alias
                """).bindparams(
                    sid=ak.source_config_id, kt=ak.key_type,
                    uid=ak.user_id, alias=ak.key_alias,
                )
            ).scalar_one_or_none()

            if not existing_key:
                session.add(ak)
                logger.info("  Created api_key: %s for source %s", ak.key_alias, ak.source_config_id)

        session.commit()

    logger.info("Seed complete: %d sources, datasets created.", len(source_map))


if __name__ == "__main__":
    seed()
