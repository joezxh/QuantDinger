-- ==============================================
-- QuantDinger 数据源统一初始化脚本
-- 将所有数据源配置（API地址、密钥、限流）迁移到数据库管理
-- ==============================================

-- 清理现有数据（首次初始化时使用）
-- TRUNCATE TABLE data_rate_limit_configs CASCADE;
-- TRUNCATE TABLE data_data_source_configs CASCADE;
-- TRUNCATE TABLE data_api_keys CASCADE;

-- ==============================================
-- 1. 数据源配置 (data_data_source_configs)
-- ==============================================

-- ==============================================
-- 1.1 加密货币数据源
-- ==============================================

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'crypto_ccxt', 'CCXT 加密货币交易所', 'data_source',
    ARRAY['Crypto'], true, 'round_robin',
    '{"api_key_env": "CCXT_API_KEY", "api_key_required": false, "base_url": "https://api.coinbase.com/api/v2/", "timeout_sec": 10, "retry_count": 3, "default_exchange": "coinbase", "rate_limit_per_min": 60, "proxy_supported": true}'::jsonb,
    '主要加密货币数据源，使用CCXT库连接多个交易所'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'crypto_coingecko', 'CoinGecko API', 'data_source',
    ARRAY['Crypto'], true, 'health_first',
    '{"api_key_env": "COINGECKO_API_KEY", "api_key_required": false, "base_url": "https://api.coingecko.com/api/v3/", "timeout_sec": 15, "retry_count": 2, "rate_limit_per_min": 30}'::jsonb,
    'CoinGecko加密货币市场数据，提供价格、市值、交易量等'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'crypto_defillama', 'DeFi Llama', 'data_source',
    ARRAY['Crypto', 'Alternative'], true, 'round_robin',
    '{"api_key_required": false, "base_url": "https://api.llama.fi", "timeout_sec": 15, "rate_limit_per_min": 60}'::jsonb,
    'DeFi协议TVL数据、链级TVL、DEX交易量等'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'crypto_coinglass', 'Coinglass', 'data_source',
    ARRAY['Crypto'], true, 'round_robin',
    '{"api_key_env": "COINGLASS_API_KEY", "api_key_required": true, "base_url": "https://open-api.coinglass.com", "timeout_sec": 15, "rate_limit_per_min": 60}'::jsonb,
    'Coinglass衍生品数据，提供合约持仓量、爆仓数据、资金费率等'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'crypto_quant', 'CryptoQuant', 'data_source',
    ARRAY['Crypto', 'Alternative'], true, 'round_robin',
    '{"api_key_env": "CRYPTOQUANT_API_KEY", "api_key_required": true, "base_url": "https://api.cryptoquant.com/v1", "timeout_sec": 15, "rate_limit_per_min": 60}'::jsonb,
    'CryptoQuant链上数据分析，提供交易所流入流出、矿工活动等指标'
) ON CONFLICT (source_code) DO NOTHING;

-- ==============================================
-- 1.2 A股数据源
-- ==============================================

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'cn_stock_akshare', 'AKShare A股数据', 'data_source',
    ARRAY['CNStock'], true, 'round_robin',
    '{"api_key_required": false, "timeout_sec": 30, "rate_limit_per_min": 30}'::jsonb,
    'AKShare免费A股数据接口，提供行情、财务、指标等数据'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'cn_stock_tushare', 'Tushare 专业A股数据', 'data_source',
    ARRAY['CNStock'], true, 'round_robin',
    '{"api_key_env": "TUSHARE_TOKEN", "api_key_required": true, "timeout_sec": 10, "rate_limit_per_min": 500}'::jsonb,
    '专业A股数据接口，需注册获取token，提供高质量历史行情和财务数据'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'cn_stock_baostock', 'BaoStock 免费A股数据', 'data_source',
    ARRAY['CNStock'], true, 'round_robin',
    '{"api_key_required": false, "timeout_sec": 15, "rate_limit_per_min": 120}'::jsonb,
    '免费A股数据接口，无需API Key，提供稳定的历史数据和财务数据'
) ON CONFLICT (source_code) DO NOTHING;

-- ==============================================
-- 1.3 美股数据源
-- ==============================================

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'us_stock_yfinance', 'Yahoo Finance 美股', 'data_source',
    ARRAY['USStock'], true, 'round_robin',
    '{"api_key_required": false, "timeout_sec": 30, "rate_limit_per_min": 60}'::jsonb,
    'Yahoo Finance免费美股数据，提供行情、历史数据、基本面等'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'us_stock_finnhub', 'Finnhub 美股数据', 'data_source',
    ARRAY['USStock'], true, 'round_robin',
    '{"api_key_env": "FINNHUB_API_KEY", "api_key_required": true, "base_url": "https://finnhub.io/api/v1", "timeout_sec": 10, "rate_limit_per_min": 60}'::jsonb,
    'Finnhub专业美股数据，提供实时行情、财报、新闻、情绪分析等'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'us_stock_financial_datasets', 'Financial Datasets API', 'data_source',
    ARRAY['USStock'], true, 'weighted',
    '{"api_key_env": "FINANCIAL_DATASETS_API_KEY", "api_key_required": true, "base_url": "https://api.financialdatasets.ai", "timeout_sec": 20, "rate_limit_per_min": 60}'::jsonb,
    '专业级美股数据API，提供三表、内部交易、分析师预估、SEC文件等'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'market_alphavantage', 'Alpha Vantage', 'data_source',
    ARRAY['USStock', 'Forex', 'Crypto'], true, 'round_robin',
    '{"api_key_env": "ALPHA_VANTAGE_API_KEY", "api_key_required": true, "base_url": "https://www.alphavantage.co/query", "timeout_sec": 20, "rate_limit_per_min": 75, "functions": ["TIME_SERIES", "TECHNICAL_INDICATORS", "CURRENCY_EXCHANGE", "CRYPTO_RATIO"]}'::jsonb,
    'Alpha Vantage免费技术指标API，提供技术指标（RSI、MACD等）、情绪数据、外汇和加密货币数据，免费用户每天500次调用'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'us_stock_tiingo', 'Tiingo 美股数据', 'data_source',
    ARRAY['USStock'], true, 'round_robin',
    '{"api_key_env": "TIINGO_API_KEY", "api_key_required": true, "base_url": "https://api.tiingo.com", "timeout_sec": 30, "rate_limit_per_min": 60}'::jsonb,
    'Tiingo专业美股数据，提供高质量行情、新闻、情绪分析等'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'twelve_data', 'Twelve Data', 'data_source',
    ARRAY['CNStock', 'HKStock', 'USStock'], true, 'round_robin',
    '{"api_key_env": "TWELVE_DATA_API_KEY", "api_key_required": true, "base_url": "https://api.twelvedata.com", "timeout_sec": 15, "rate_limit_per_min": 8}'::jsonb,
    'Twelve Data全球股票数据，覆盖CN/HK/US市场，免费套餐每天800次调用'
) ON CONFLICT (source_code) DO NOTHING;

-- ==============================================
-- 1.4 期货数据源
-- ==============================================

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'futures_akshare', 'AKShare 期货数据', 'data_source',
    ARRAY['Futures'], true, 'round_robin',
    '{"api_key_required": false, "timeout_sec": 30, "rate_limit_per_min": 30}'::jsonb,
    'AKShare免费期货数据接口，提供国内期货行情和持仓数据'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'futures_cftc', 'CFTC Commitment of Traders', 'data_source',
    ARRAY['Futures', 'Alternative'], true, 'round_robin',
    '{"api_key_required": false, "base_url": "https://publicreporting.cftc.gov", "timeout_sec": 20, "rate_limit_per_min": 30}'::jsonb,
    'CFTC持仓报告(COT)，包含大商、投机、套保持仓数据'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'futures_cboe', 'CBOE Volatility Indices', 'data_source',
    ARRAY['Futures'], true, 'round_robin',
    '{"api_key_required": false, "base_url": "https://cdn.cboe.com/api/global/us_indices/daily_prices", "timeout_sec": 20, "rate_limit_per_min": 30, "indices": ["VIX", "VIX3M", "VVIX", "SKEW", "VXN", "VXO", "GVZ", "OVX", "TYVIX"]}'::jsonb,
    'CBOE波动率指数，免费公开CDN数据，提供VIX/VIX3M/VVIX/SKEW等历史数据，无需API Key'
) ON CONFLICT (source_code) DO NOTHING;

-- ==============================================
-- 1.5 宏观经济数据源
-- ==============================================

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'macro_fred', 'FRED (Federal Reserve Economic Data)', 'data_source',
    ARRAY['Macro'], true, 'round_robin',
    '{"api_key_env": "FRED_API_KEY", "api_key_required": true, "base_url": "https://api.stlouisfed.org/fred", "timeout_sec": 15, "rate_limit_per_min": 120, "series_count": 20}'::jsonb,
    '美联储官方经济数据库，提供利率、就业、CPI、GDP等关键宏观指标'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'macro_bls', 'BLS (Bureau of Labor Statistics)', 'data_source',
    ARRAY['Macro'], true, 'round_robin',
    '{"api_key_env": "BLS_API_KEY", "api_key_required": true, "base_url": "https://api.bls.gov/publicAPI/v2", "timeout_sec": 15, "rate_limit_per_min": 60}'::jsonb,
    '美国劳工统计局，提供就业、CPI、薪资等数据'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'macro_worldbank', 'World Bank Open Data', 'data_source',
    ARRAY['Macro'], true, 'round_robin',
    '{"api_key_required": false, "base_url": "https://api.worldbank.org/v2", "timeout_sec": 15, "rate_limit_per_min": 60}'::jsonb,
    '世界银行开放数据，提供全球各国GDP、人口、贸易等指标'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'macro_bea', 'BEA (Bureau of Economic Analysis)', 'data_source',
    ARRAY['Macro'], true, 'round_robin',
    '{"api_key_env": "BEA_API_KEY", "api_key_required": true, "base_url": "https://apps.bea.gov/api/data/", "timeout_sec": 20, "rate_limit_per_min": 60, "nipa_indicators": ["gdp_growth", "nominal_gdp", "real_gdp", "pce", "personal_income", "saving_rate"]}'::jsonb,
    '美国经济分析局，提供GDP、PCE、个人收入等NIPA国民收入与产出账户数据，免费注册API Key'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'macro_imf', 'IMF (International Monetary Fund)', 'data_source',
    ARRAY['Macro'], true, 'round_robin',
    '{"api_key_required": false, "base_url": "http://dataservices.imf.org/REST/SDMX_JSON.svc", "timeout_sec": 30, "rate_limit_per_min": 30, "indicators": ["GDP", "NGDP_RPCH", "PCPIPCH", "BCA", "LUR", "GGXWDG_NGDP"]}'::jsonb,
    'IMF国际货币基金组织数据，提供GDP增长、通胀率、失业率、经常账户余额、政府债务等关键经济指标'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'macro_oecd', 'OECD Statistics', 'data_source',
    ARRAY['Macro'], true, 'round_robin',
    '{"api_key_required": false, "base_url": "https://stats.oecd.org/SDMX-JSON/data", "timeout_sec": 30, "rate_limit_per_min": 30, "key_datasets": ["MEI", "LABOR_DIST", "SNA_TABLE1", "CPI"]}'::jsonb,
    'OECD统计数据，提供38个成员国和主要新兴市场的GDP、CPI、失业率、生产率等经济指标'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'macro_ecb', 'ECB (European Central Bank)', 'data_source',
    ARRAY['Macro', 'Forex'], true, 'round_robin',
    '{"api_key_required": false, "base_url": "https://data.api.ecb.europa.eu/service/data", "timeout_sec": 30, "rate_limit_per_min": 30, "dataflows": ["EXR", "IRS", "FM", "BLS"]}'::jsonb,
    '欧洲央行数据，提供欧元汇率、利率、货币供应量、银行信贷等数据'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'macro_eia', 'EIA (U.S. Energy Information Administration)', 'data_source',
    ARRAY['Macro', 'Alternative'], true, 'round_robin',
    '{"api_key_env": "EIA_API_KEY", "api_key_required": true, "base_url": "https://api.eia.gov/v2", "timeout_sec": 30, "rate_limit_per_min": 60, "categories": ["petroleum", "natural_gas", "electricity", "renewable"]}'::jsonb,
    '美国能源信息署数据，提供石油、天然气、电力、可再生能源等能源价格和供需数据'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'macro_wto', 'WTO (World Trade Organization)', 'data_source',
    ARRAY['Macro', 'Alternative'], true, 'round_robin',
    '{"api_key_required": false, "base_url": "https://api.wto.org/timeseries/v1", "timeout_sec": 30, "rate_limit_per_min": 30, "datasets": ["trade_trends", "trade_profits", " trade_balance"]}'::jsonb,
    'WTO世界贸易组织数据，提供全球贸易趋势、区域贸易协定、贸易便利化等统计数据'
) ON CONFLICT (source_code) DO NOTHING;

-- ==============================================
-- 1.6 基本面数据源
-- ==============================================

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'fundamentals_simfin', 'SimFin 离线基本面数据', 'data_source',
    ARRAY['Fundamentals'], true, 'round_robin',
    '{"api_key_required": false, "data_dir": "data/fundamentals/simfin/", "timeout_sec": 5, "rate_limit_per_min": 120, "supports": ["balance_sheet", "income_statements", "cash_flow"], "markets": ["us", "cn"]}'::jsonb,
    'SimFin免费离线基本面数据，提供美股三表(资产负债表/利润表/现金流量表)，需预下载CSV数据文件到data/fundamentals/simfin/目录'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'fundamentals_fmp', 'FMP (Financial Modeling Prep)', 'data_source',
    ARRAY['Fundamentals', 'USStock'], true, 'round_robin',
    '{"api_key_env": "FMP_API_KEY", "api_key_required": true, "base_url": "https://financialmodelingprep.com/api/v4", "timeout_sec": 20, "rate_limit_per_min": 250, "endpoints": ["income_statement", "balance_sheet", "cash_flow", "ratios", "valuation"]}'::jsonb,
    'FMP专业金融数据API，提供财务报表、估值、分析师评级、，内部交易等数据，需付费订阅API Key'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'fundamentals_sec', 'SEC EDGAR', 'data_source',
    ARRAY['Fundamentals', 'USStock'], true, 'round_robin',
    '{"api_key_required": false, "base_url": "https://data.sec.gov/submissions", "timeout_sec": 30, "rate_limit_per_min": 10, "filings": ["10-K", "10-Q", "8-K", "DEF 14A"]}'::jsonb,
    'SEC EDGAR公开文件数据库，提供美股上市公司年报季报、8-K重大事件、内部交易等监管文件'
) ON CONFLICT (source_code) DO NOTHING;

-- ==============================================
-- 1.7 新闻舆情数据源
-- ==============================================

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'news_google', 'Google News RSS', 'data_source',
    ARRAY['News'], true, 'round_robin',
    '{"api_key_required": false, "timeout_sec": 15, "rate_limit_per_min": 10}'::jsonb,
    'Google News RSS搜索，免费无需API Key，支持中英文新闻'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'news_eastmoney', '东方财富新闻 (via AKShare)', 'data_source',
    ARRAY['CNStock', 'News'], true, 'round_robin',
    '{"api_key_required": false, "timeout_sec": 15, "rate_limit_per_min": 30}'::jsonb,
    '东方财富新闻数据，通过AKShare接口获取A股财经新闻'
) ON CONFLICT (source_code) DO NOTHING;

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'news_newsapi', 'NewsAPI', 'data_source',
    ARRAY['News'], true, 'round_robin',
    '{"api_key_env": "NEWS_API_KEY", "api_key_required": true, "base_url": "https://newsapi.org/v2", "timeout_sec": 20, "rate_limit_per_min": 100, "domains": ["reuters.com", "bloomberg.com", "wsj.com", "ft.com"]}'::jsonb,
    'NewsAPI新闻聚合服务，聚合全球主流财经媒体新闻，支持按关键词、日期、来源筛选'
) ON CONFLICT (source_code) DO NOTHING;

-- ==============================================
-- 1.8 情绪分析数据源
-- ==============================================

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'adanos_sentiment', 'Adanos Market Sentiment', 'data_source',
    ARRAY['USStock', 'Alternative'], true, 'round_robin',
    '{"api_key_env": "ADANOS_API_KEY", "api_key_required": true, "base_url": "https://api.adanos.org", "timeout_sec": 10, "rate_limit_per_min": 60, "sentiment_source": "reddit"}'::jsonb,
    'Adanos市场情绪分析，主要基于Reddit等社交媒体的美股情绪数据'
) ON CONFLICT (source_code) DO NOTHING;

-- ==============================================
-- 2. 限流配置 (data_rate_limit_configs)
-- ==============================================

-- 插入限流配置（关联已插入的数据源配置）
DO $$
DECLARE
    source_id INTEGER;
BEGIN
    -- 加密货币限流配置
    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'crypto_ccxt' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 60, 60, 60, 10, 'database', 'CCXT默认限流配置')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'crypto_coingecko' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 30, 60, 30, 10, 'database', 'CoinGecko免费API限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'crypto_defillama' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 60, 60, 60, 10, 'database', 'DeFi Llama限流配置')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'crypto_coinglass' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 60, 60, 60, 10, 'database', 'Coinglass API限流配置')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'crypto_quant' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 60, 60, 60, 10, 'database', 'CryptoQuant API限流配置')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    -- A股限流配置
    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'cn_stock_akshare' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 30, 60, 30, 10, 'database', 'AKShare免费API限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'cn_stock_tushare' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 500, 60, 500, 20, 'database', 'Tushare专业版限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'cn_stock_baostock' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 120, 60, 120, 15, 'database', 'BaoStock免费API限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    -- 美股限流配置
    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'us_stock_yfinance' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 60, 60, 60, 10, 'database', 'Yahoo Finance限流配置')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'us_stock_finnhub' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 60, 60, 60, 10, 'database', 'Finnhub API限流配置')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'us_stock_financial_datasets' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 60, 60, 60, 15, 'database', 'Financial Datasets API限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'market_alphavantage' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 75, 60, 75, 15, 'database', 'Alpha Vantage免费API限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'us_stock_tiingo' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 60, 60, 60, 15, 'database', 'Tiingo API限流配置')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'twelve_data' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 8, 60, 8, 5, 'database', 'Twelve Data免费套餐限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    -- 期货限流配置
    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'futures_akshare' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 30, 60, 30, 10, 'database', 'AKShare期货限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'futures_cftc' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 30, 60, 30, 10, 'database', 'CFTC API限流配置')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'futures_cboe' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 30, 60, 30, 10, 'database', 'CBOE CDN限流配置')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    -- 宏观经济限流配置
    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'macro_fred' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 120, 60, 120, 20, 'database', 'FRED API限流配置')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'macro_bls' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 60, 60, 60, 10, 'database', 'BLS API限流配置')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'macro_worldbank' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 60, 60, 60, 10, 'database', 'World Bank API限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'macro_bea' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 60, 60, 60, 10, 'database', 'BEA API限流配置')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'macro_imf' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 30, 60, 30, 10, 'database', 'IMF免费API限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'macro_oecd' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 30, 60, 30, 10, 'database', 'OECD免费API限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'macro_ecb' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 30, 60, 30, 10, 'database', 'ECB免费API限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'macro_eia' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 60, 60, 60, 15, 'database', 'EIA付费API限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'macro_wto' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 30, 60, 30, 10, 'database', 'WTO免费API限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    -- 基本面限流配置
    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'fundamentals_simfin' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 120, 60, 120, 15, 'database', 'SimFin离线数据限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'fundamentals_fmp' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 250, 60, 250, 20, 'database', 'FMP付费API限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'fundamentals_sec' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, reduce_rate_on_error, error_threshold, config_source, notes)
        VALUES (source_id, 'token_bucket', 10, 60, 10, 5, true, 3, 'database', 'SEC EDGAR严格限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    -- 新闻限流配置
    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'news_google' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 10, 60, 10, 5, 'database', 'Google News RSS限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'news_eastmoney' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 30, 60, 30, 10, 'database', '东方财富新闻限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'news_newsapi' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 100, 60, 100, 20, 'database', 'NewsAPI付费限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;

    -- 情绪分析限流配置
    FOR source_id IN SELECT id FROM data_data_source_configs WHERE source_code = 'adanos_sentiment' LOOP
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (source_id, 'token_bucket', 60, 60, 60, 10, 'database', 'Adanos情绪API限流')
        ON CONFLICT (source_config_id) DO NOTHING;
    END LOOP;
END $$;

-- ==============================================
-- 3. 完成提示
-- ==============================================

DO $$
BEGIN
    RAISE NOTICE '数据源配置初始化完成！';
    RAISE NOTICE '已初始化 % 个数据源配置', (SELECT COUNT(*) FROM data_data_source_configs);
    RAISE NOTICE '已初始化 % 个限流配置', (SELECT COUNT(*) FROM data_rate_limit_configs);
END $$;
