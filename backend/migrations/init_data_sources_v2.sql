-- ==============================================
-- Data Source Integration Migration
-- 新增数据源配置和健康监控表
-- ==============================================

-- 数据源健康状态表
CREATE TABLE IF NOT EXISTS data_source_health (
    id SERIAL PRIMARY KEY,
    source_code VARCHAR(80) NOT NULL,
    category VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'unknown',
    latency_ms INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    last_error TEXT DEFAULT '',
    last_check_at TIMESTAMP,
    last_success_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_code, category)
);

CREATE INDEX IF NOT EXISTS idx_data_source_health_category ON data_source_health(category);
CREATE INDEX IF NOT EXISTS idx_data_source_health_status ON data_source_health(status);

-- ==============================================
-- 新增数据源配置 seed data
-- ==============================================

-- FRED 宏观数据
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'macro_fred', 'FRED (Federal Reserve Economic Data)', 'data_source',
    ARRAY['Macro'], true, 'round_robin',
    '{"api_key_env": "FRED_API_KEY", "api_key_required": true, "base_url": "https://api.stlouisfed.org/fred", "timeout_sec": 15, "rate_limit_per_min": 120, "series_count": 20}'::jsonb,
    '美联储官方经济数据库，提供利率、就业、CPI、GDP等关键宏观指标'
) ON CONFLICT (source_code) DO NOTHING;

-- BLS 宏观数据
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'macro_bls', 'BLS (Bureau of Labor Statistics)', 'data_source',
    ARRAY['Macro'], true, 'round_robin',
    '{"api_key_env": "BLS_API_KEY", "api_key_required": true, "base_url": "https://api.bls.gov/publicAPI/v2", "timeout_sec": 15, "rate_limit_per_min": 60}'::jsonb,
    '美国劳工统计局，提供就业、CPI、薪资等数据'
) ON CONFLICT (source_code) DO NOTHING;

-- 世界银行宏观数据
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'macro_worldbank', 'World Bank Open Data', 'data_source',
    ARRAY['Macro'], true, 'round_robin',
    '{"api_key_required": false, "base_url": "https://api.worldbank.org/v2", "timeout_sec": 15, "rate_limit_per_min": 60}'::jsonb,
    '世界银行开放数据，提供全球各国GDP、人口、贸易等指标'
) ON CONFLICT (source_code) DO NOTHING;

-- Tushare A股数据
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'cn_stock_tushare', 'Tushare 专业A股数据', 'data_source',
    ARRAY['CNStock'], true, 'round_robin',
    '{"api_key_env": "TUSHARE_TOKEN", "api_key_required": true, "timeout_sec": 10, "rate_limit_per_min": 500}'::jsonb,
    '专业A股数据接口，需注册获取token，提供高质量历史行情和财务数据'
) ON CONFLICT (source_code) DO NOTHING;

-- BaoStock A股数据
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'cn_stock_baostock', 'BaoStock 免费A股数据', 'data_source',
    ARRAY['CNStock'], true, 'round_robin',
    '{"api_key_required": false, "timeout_sec": 15, "rate_limit_per_min": 120}'::jsonb,
    '免费A股数据接口，无需API Key，提供稳定的历史数据和财务数据'
) ON CONFLICT (source_code) DO NOTHING;

-- CoinGecko 加密数据
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'crypto_coingecko', 'CoinGecko 加密聚合数据', 'data_source',
    ARRAY['Crypto'], true, 'round_robin',
    '{"api_key_required": false, "base_url": "https://api.coingecko.com/api/v3", "timeout_sec": 15, "rate_limit_per_min": 30}'::jsonb,
    '免费加密货币聚合数据，提供市值排行、价格、DeFi TVL等'
) ON CONFLICT (source_code) DO NOTHING;

-- DeFi Llama 数据
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'crypto_defillama', 'DeFi Llama TVL数据', 'data_source',
    ARRAY['Crypto', 'Alternative'], true, 'round_robin',
    '{"api_key_required": false, "base_url": "https://api.llama.fi", "timeout_sec": 15, "rate_limit_per_min": 60}'::jsonb,
    'DeFi协议TVL数据、链级TVL、DEX交易量等'
) ON CONFLICT (source_code) DO NOTHING;

-- Financial Datasets API
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'us_stock_financial_datasets', 'Financial Datasets API', 'data_source',
    ARRAY['USStock'], true, 'weighted',
    '{"api_key_env": "FINANCIAL_DATASETS_API_KEY", "api_key_required": true, "base_url": "https://api.financialdatasets.ai", "timeout_sec": 20, "rate_limit_per_min": 60}'::jsonb,
    '专业级美股数据API，提供三表、内部交易、分析师预估、SEC文件等'
) ON CONFLICT (source_code) DO NOTHING;

-- CFTC 期货持仓数据
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'futures_cftc', 'CFTC Commitment of Traders', 'data_source',
    ARRAY['Futures', 'Alternative'], true, 'round_robin',
    '{"api_key_required": false, "base_url": "https://publicreporting.cftc.gov", "timeout_sec": 20, "rate_limit_per_min": 30}'::jsonb,
    'CFTC持仓报告(COT)，包含大商、投机、套保持仓数据'
) ON CONFLICT (source_code) DO NOTHING;

-- Google News
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'news_google', 'Google News RSS', 'data_source',
    ARRAY['News'], true, 'round_robin',
    '{"api_key_required": false, "timeout_sec": 15, "rate_limit_per_min": 10}'::jsonb,
    'Google News RSS搜索，免费无需API Key，支持中英文新闻'
) ON CONFLICT (source_code) DO NOTHING;

-- 东方财富新闻
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'news_eastmoney', '东方财富新闻 (via AKShare)', 'data_source',
    ARRAY['CNStock', 'News'], true, 'round_robin',
    '{"api_key_required": false, "timeout_sec": 15, "rate_limit_per_min": 30}'::jsonb,
    '东方财富新闻数据，通过AKShare接口获取A股财经新闻'
) ON CONFLICT (source_code) DO NOTHING;
