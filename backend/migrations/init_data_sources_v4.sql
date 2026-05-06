-- ==============================================
-- Data Source Integration Migration v4
-- 新增 FinceptTerminal 集成的数据源配置
-- IMF、OECD、ECB、EIA、WTO、FMP、SEC、Alpha Vantage、NewsAPI
-- ==============================================

-- ==============================================
-- 1. 宏观经济数据源配置
-- ==============================================

-- IMF 国际货币基金组织数据
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'macro_imf', 'IMF (International Monetary Fund)', 'data_source',
    ARRAY['Macro'], true, 'round_robin',
    '{"api_key_required": false, "base_url": "http://dataservices.imf.org/REST/SDMX_JSON.svc", "timeout_sec": 30, "rate_limit_per_min": 30, "indicators": ["GDP", "NGDP_RPCH", "PCPIPCH", "BCA", "LUR", "GGXWDG_NGDP"]}'::jsonb,
    'IMF国际货币基金组织数据，提供GDP增长、通胀率、失业率、经常账户余额、政府债务等关键经济指标'
) ON CONFLICT (source_code) DO NOTHING;

-- OECD 经济合作与发展组织数据
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'macro_oecd', 'OECD Statistics', 'data_source',
    ARRAY['Macro'], true, 'round_robin',
    '{"api_key_required": false, "base_url": "https://stats.oecd.org/SDMX-JSON/data", "timeout_sec": 30, "rate_limit_per_min": 30, "key_datasets": ["MEI", "LABOR_DIST", "SNA_TABLE1", "CPI"]}'::jsonb,
    'OECD统计数据，提供38个成员国和主要新兴市场的GDP、CPI、失业率、生产率等经济指标'
) ON CONFLICT (source_code) DO NOTHING;

-- ECB 欧洲中央银行数据
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'macro_ecb', 'ECB (European Central Bank)', 'data_source',
    ARRAY['Macro', 'Forex'], true, 'round_robin',
    '{"api_key_required": false, "base_url": "https://data.api.ecb.europa.eu/service/data", "timeout_sec": 30, "rate_limit_per_min": 30, "dataflows": ["EXR", "IRS", "FM", "BLS"]}'::jsonb,
    '欧洲央行数据，提供欧元汇率、利率、货币供应量、银行信贷等数据'
) ON CONFLICT (source_code) DO NOTHING;

-- EIA 美国能源信息署数据
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'macro_eia', 'EIA (U.S. Energy Information Administration)', 'data_source',
    ARRAY['Macro', 'Alternative'], true, 'round_robin',
    '{"api_key_required": true, "api_key_env": "EIA_API_KEY", "base_url": "https://api.eia.gov/v2", "timeout_sec": 30, "rate_limit_per_min": 60, "categories": ["petroleum", "natural_gas", "electricity", "renewable"]}'::jsonb,
    '美国能源信息署数据，提供石油、天然气、电力、可再生能源等能源价格和供需数据'
) ON CONFLICT (source_code) DO NOTHING;

-- WTO 世界贸易组织数据
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'macro_wto', 'WTO (World Trade Organization)', 'data_source',
    ARRAY['Macro', 'Alternative'], true, 'round_robin',
    '{"api_key_required": false, "base_url": "https://api.wto.org/timeseries/v1", "timeout_sec": 30, "rate_limit_per_min": 30, "datasets": ["trade_trends", "trade_profits", " trade_balance"]}'::jsonb,
    'WTO世界贸易组织数据，提供全球贸易趋势、区域贸易协定、贸易便利化等统计数据'
) ON CONFLICT (source_code) DO NOTHING;

-- ==============================================
-- 2. 基本面数据源配置
-- ==============================================

-- FMP 金融市场数据平台
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'fundamentals_fmp', 'FMP (Financial Modeling Prep)', 'data_source',
    ARRAY['Fundamentals', 'USStock'], true, 'round_robin',
    '{"api_key_env": "FMP_API_KEY", "api_key_required": true, "base_url": "https://financialmodelingprep.com/api/v4", "timeout_sec": 20, "rate_limit_per_min": 250, "endpoints": ["income_statement", "balance_sheet", "cash_flow", "ratios", "valuation"]}'::jsonb,
    'FMP专业金融数据API，提供财务报表、估值、分析师评级、，内部交易等数据，需付费订阅API Key'
) ON CONFLICT (source_code) DO NOTHING;

-- SEC 美国证券交易委员会 EDGAR
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'fundamentals_sec', 'SEC EDGAR', 'data_source',
    ARRAY['Fundamentals', 'USStock'], true, 'round_robin',
    '{"api_key_required": false, "base_url": "https://data.sec.gov/submissions", "timeout_sec": 30, "rate_limit_per_min": 10, "filings": ["10-K", "10-Q", "8-K", "DEF 14A"]}'::jsonb,
    'SEC EDGAR公开文件数据库，提供美股上市公司年报季报、8-K重大事件、内部交易等监管文件'
) ON CONFLICT (source_code) DO NOTHING;

-- ==============================================
-- 3. 市场数据源配置
-- ==============================================

-- Alpha Vantage 技术指标和情绪数据
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'market_alphavantage', 'Alpha Vantage', 'data_source',
    ARRAY['USStock', 'Forex', 'Crypto'], true, 'round_robin',
    '{"api_key_env": "ALPHA_VANTAGE_API_KEY", "api_key_required": true, "base_url": "https://www.alphavantage.co/query", "timeout_sec": 20, "rate_limit_per_min": 75, "functions": ["TIME_SERIES", "TECHNICAL_INDICATORS", "CURRENCY_EXCHANGE", "CRYPTO_RATIO"]}'::jsonb,
    'Alpha Vantage免费技术指标API，提供技术指标（RSI、MACD等）、情绪数据、外汇和加密货币数据，免费用户每天500次调用'
) ON CONFLICT (source_code) DO NOTHING;

-- ==============================================
-- 4. 新闻舆情数据源配置
-- ==============================================

-- NewsAPI 新闻聚合
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'news_newsapi', 'NewsAPI', 'data_source',
    ARRAY['News'], true, 'round_robin',
    '{"api_key_env": "NEWS_API_KEY", "api_key_required": true, "base_url": "https://newsapi.org/v2", "timeout_sec": 20, "rate_limit_per_min": 100, "domains": ["reuters.com", "bloomberg.com", "wsj.com", "ft.com"]}'::jsonb,
    'NewsAPI新闻聚合服务，聚合全球主流财经媒体新闻，支持按关键词、日期、来源筛选'
) ON CONFLICT (source_code) DO NOTHING;

-- ==============================================
-- 5. 搜索引擎和 AI 数据源配置
-- ==============================================

-- Bocha 博查 AI 搜索
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'search_bocha', 'Bocha AI Search (博查)', 'data_source',
    ARRAY['News', 'Alternative'], true, 'round_robin',
    '{"api_key_env": "BOCHA_API_KEY", "api_key_required": true, "base_url": "https://api.bochaai.com/v1", "timeout_sec": 15, "rate_limit_per_min": 60, "features": ["web_search", "news_search", "knowledge_graph"]}',
    '博查AI搜索引擎，提供网页搜索、新闻搜索、知识图谱等AI搜索服务，支持中文语义理解'
) ON CONFLICT (source_code) DO NOTHING;

-- SHUYAN 数眼智能
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'search_shuyan', 'SHUYAN Intelligence (数眼智能)', 'data_source',
    ARRAY['News', 'Alternative'], true, 'round_robin',
    '{"api_key_env": "SHUYAN_API_KEY", "api_key_required": true, "base_url": "https://api.shuyan.com/v1", "timeout_sec": 15, "rate_limit_per_min": 50, "features": ["financial_news", "data_analysis", "sentiment"]}',
    '数眼智能数据平台，提供财经新闻、数据分析、情感分析等智能数据服务'
) ON CONFLICT (source_code) DO NOTHING;

-- ANSPIRE 安思派配置
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'search_anspire', 'ANSPIRE Data Service (安思派)', 'data_source',
    ARRAY['Fundamentals', 'News', 'Alternative'], true, 'round_robin',
    '{"api_key_env": "ANSPIRE_API_KEY", "api_key_required": true, "base_url": "https://api.anspire.com/v1", "timeout_sec": 20, "rate_limit_per_min": 40, "features": ["company_data", "industry_analysis", "market_research"]}',
    '安思派数据服务，提供企业数据、行业分析、市场调研等专业数据服务'
) ON CONFLICT (source_code) DO NOTHING;

-- Firecrawl 私有化部署（网页抓取）
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'search_firecrawl', 'Firecrawl (私有化部署)', 'data_source',
    ARRAY['News', 'Alternative'], true, 'round_robin',
    '{"api_key_env": "FIRECRAWL_API_KEY", "api_key_required": true, "base_url": "http://localhost:3002", "timeout_sec": 30, "rate_limit_per_min": 30, "features": ["web_scraping", "crawl", "extract", "markdown"], "self_hosted": true}',
    'Firecrawl私有化部署网页抓取服务，支持网页爬取、内容提取、Markdown转换，适合本地化部署'
) ON CONFLICT (source_code) DO NOTHING;

-- Google 搜索
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'search_google', 'Google Search API', 'data_source',
    ARRAY['News', 'Alternative'], true, 'round_robin',
    '{"api_key_env": "GOOGLE_SEARCH_API_KEY", "api_key_required": true, "base_url": "https://www.googleapis.com/customsearch/v1", "timeout_sec": 10, "rate_limit_per_min": 100, "cx_env": "GOOGLE_SEARCH_CX", "features": ["web_search", "news_search"]}',
    'Google自定义搜索API，提供网页搜索和新闻搜索服务，需配置API Key和Search Engine ID (CX)'
) ON CONFLICT (source_code) DO NOTHING;

-- Baidu 百度搜索
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'search_baidu', 'Baidu Search API (百度)', 'data_source',
    ARRAY['News', 'Alternative'], true, 'round_robin',
    '{"api_key_env": "BAIDU_API_KEY", "api_key_required": true, "base_url": "https://aip.baidubce.com/rest/2.0", "timeout_sec": 10, "rate_limit_per_min": 80, "features": ["web_search", "news_search", "chinese_content"]}',
    '百度搜索API，提供中文网页搜索和新闻搜索服务，中文内容覆盖全面'
) ON CONFLICT (source_code) DO NOTHING;

-- Bing 必应搜索
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'search_bing', 'Bing Search API (必应)', 'data_source',
    ARRAY['News', 'Alternative'], true, 'round_robin',
    '{"api_key_env": "BING_SEARCH_API_KEY", "api_key_required": true, "base_url": "https://api.bing.microsoft.com/v7.0", "timeout_sec": 10, "rate_limit_per_min": 100, "features": ["web_search", "news_search", "image_search"]}',
    '微软必应搜索API，提供网页搜索、新闻搜索、图片搜索等服务，全球内容覆盖广'
) ON CONFLICT (source_code) DO NOTHING;

-- ==============================================
-- 6. 健康检查表更新
-- ==============================================

-- 为新增数据源初始化健康检查记录
DO $$
DECLARE
    new_sources TEXT[] := ARRAY[
        'macro_imf', 'macro_oecd', 'macro_ecb', 'macro_eia', 'macro_wto',
        'fundamentals_fmp', 'fundamentals_sec',
        'market_alphavantage', 'news_newsapi',
        'search_bocha', 'search_shuyan', 'search_anspire', 'search_firecrawl',
        'search_google', 'search_baidu', 'search_bing'
    ];
    source_code TEXT;
BEGIN
    FOREACH source_code IN ARRAY new_sources
    LOOP
        IF NOT EXISTS (SELECT 1 FROM data_source_health WHERE source_code = source_code) THEN
            INSERT INTO data_source_health (source_code, category, status)
            VALUES (source_code, 'Search', 'unknown')
            ON CONFLICT (source_code, category) DO NOTHING;
        END IF;
    END LOOP;
END $$;

-- ==============================================
-- 6. 更新说明
-- ==============================================

-- 本次迁移新增 16 个数据源：
-- 宏观经济：IMF、OECD、ECB、EIA、WTO
-- 基本面：FMP、SEC
-- 市场数据：Alpha Vantage
-- 新闻舆情：NewsAPI
-- 搜索引擎和AI：博查(Bocha)、数眼智能(SHUYAN)、安思派(ANSPIRE)、Firecrawl、Google、Baidu、Bing

-- 数据源优先级设置策略：
-- - MACRO类别：EIA(70) > IMF(65) > OECD(60) > BEA(80,已存在) > FRED(100,已存在) > ECB(55) > WorldBank(70,已存在) > WTO(50)
-- - FUNDAMENTALS类别：FMP(60) > SEC(55) > SimFin(20,已存在) > ANSPIRE(45)
-- - US_STOCK类别：Alpha Vantage(40) < Financial Datasets(70,已存在) < yfinance(50,已存在)
-- - NEWS类别：NewsAPI(30) < EastMoney(40,已存在) < Google(30,已存在)
-- - SEARCH类别：Google(80) > Bing(75) > Baidu(70) > Bocha(65) > SHUYAN(60) > Firecrawl(50)

-- 搜索引擎使用场景：
-- - 新闻搜索：Google、Bing、Baidu、Bocha
-- - 中文内容：Baidu、Bocha、SHUYAN
-- - 全球内容：Google、Bing
-- - 专业数据：ANSPIRE、SHUYAN
-- - 网页抓取：Firecrawl（私有化部署）

-- ==============================================
-- 7. 限流配置表 (data_rate_limit_configs)
-- ==============================================

CREATE TABLE IF NOT EXISTS data_rate_limit_configs (
    id SERIAL PRIMARY KEY,
    source_config_id INTEGER NOT NULL REFERENCES data_data_source_configs(id) ON DELETE CASCADE,
    strategy VARCHAR(30) NOT NULL DEFAULT 'token_bucket',
    rate INTEGER NOT NULL DEFAULT 60,
    period INTEGER NOT NULL DEFAULT 60,
    burst INTEGER,
    max_concurrent INTEGER NOT NULL DEFAULT 10,
    window_size INTEGER,
    max_requests_per_window INTEGER,
    enable_adaptive BOOLEAN NOT NULL DEFAULT false,
    min_rate INTEGER,
    max_rate INTEGER,
    reduce_rate_on_error BOOLEAN NOT NULL DEFAULT true,
    error_threshold INTEGER NOT NULL DEFAULT 5,
    priority INTEGER NOT NULL DEFAULT 50,
    weight INTEGER NOT NULL DEFAULT 1,
    total_requests INTEGER NOT NULL DEFAULT 0,
    total_rejected INTEGER NOT NULL DEFAULT 0,
    total_errors INTEGER NOT NULL DEFAULT 0,
    last_request_at TIMESTAMP WITH TIME ZONE,
    last_rejected_at TIMESTAMP WITH TIME ZONE,
    enabled BOOLEAN NOT NULL DEFAULT true,
    config_source VARCHAR(20) NOT NULL DEFAULT 'database',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_rate_limit_per_source UNIQUE (source_config_id)
);

CREATE INDEX IF NOT EXISTS idx_rate_limit_source ON data_rate_limit_configs(source_config_id);
CREATE INDEX IF NOT EXISTS idx_rate_limit_enabled ON data_rate_limit_configs(enabled);

-- ==============================================
-- 8. 初始化限流配置 seed data
-- ==============================================

-- 插入限流配置（关联已插入的数据源配置）
DO $$
DECLARE
    src_macro_imf INTEGER;
    src_macro_oecd INTEGER;
    src_macro_ecb INTEGER;
    src_macro_eia INTEGER;
    src_macro_wto INTEGER;
    src_fundamentals_fmp INTEGER;
    src_fundamentals_sec INTEGER;
    src_market_alphavantage INTEGER;
    src_news_newsapi INTEGER;
    src_search_bocha INTEGER;
    src_search_shuyan INTEGER;
    src_search_anspire INTEGER;
    src_search_firecrawl INTEGER;
    src_search_google INTEGER;
    src_search_baidu INTEGER;
    src_search_bing INTEGER;
BEGIN
    -- 获取数据源配置ID
    SELECT id INTO src_macro_imf FROM data_data_source_configs WHERE source_code = 'macro_imf';
    SELECT id INTO src_macro_oecd FROM data_data_source_configs WHERE source_code = 'macro_oecd';
    SELECT id INTO src_macro_ecb FROM data_data_source_configs WHERE source_code = 'macro_ecb';
    SELECT id INTO src_macro_eia FROM data_data_source_configs WHERE source_code = 'macro_eia';
    SELECT id INTO src_macro_wto FROM data_data_source_configs WHERE source_code = 'macro_wto';
    SELECT id INTO src_fundamentals_fmp FROM data_data_source_configs WHERE source_code = 'fundamentals_fmp';
    SELECT id INTO src_fundamentals_sec FROM data_data_source_configs WHERE source_code = 'fundamentals_sec';
    SELECT id INTO src_market_alphavantage FROM data_data_source_configs WHERE source_code = 'market_alphavantage';
    SELECT id INTO src_news_newsapi FROM data_data_source_configs WHERE source_code = 'news_newsapi';
    SELECT id INTO src_search_bocha FROM data_data_source_configs WHERE source_code = 'search_bocha';
    SELECT id INTO src_search_shuyan FROM data_data_source_configs WHERE source_code = 'search_shuyan';
    SELECT id INTO src_search_anspire FROM data_data_source_configs WHERE source_code = 'search_anspire';
    SELECT id INTO src_search_firecrawl FROM data_data_source_configs WHERE source_code = 'search_firecrawl';
    SELECT id INTO src_search_google FROM data_data_source_configs WHERE source_code = 'search_google';
    SELECT id INTO src_search_baidu FROM data_data_source_configs WHERE source_code = 'search_baidu';
    SELECT id INTO src_search_bing FROM data_data_source_configs WHERE source_code = 'search_bing';

    -- IMF: 免费API，限流宽松
    IF src_macro_imf IS NOT NULL THEN
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (src_macro_imf, 'token_bucket', 30, 60, 30, 10, 'database', 'IMF免费API，每分钟30次请求')
        ON CONFLICT (source_config_id) DO NOTHING;
    END IF;

    -- OECD: 免费API，限流宽松
    IF src_macro_oecd IS NOT NULL THEN
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (src_macro_oecd, 'token_bucket', 30, 60, 30, 10, 'database', 'OECD免费API，每分钟30次请求')
        ON CONFLICT (source_config_id) DO NOTHING;
    END IF;


    -- ECB: 免费API，限流宽松
    IF src_macro_ecb IS NOT NULL THEN
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (src_macro_ecb, 'token_bucket', 30, 60, 30, 10, 'database', 'ECB免费API，每分钟30次请求')
        ON CONFLICT (source_config_id) DO NOTHING;
    END IF;

    -- EIA: 付费API，较高配额
    IF src_macro_eia IS NOT NULL THEN
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (src_macro_eia, 'token_bucket', 60, 60, 60, 15, 'database', 'EIA付费API，每分钟60次请求')
        ON CONFLICT (source_config_id) DO NOTHING;
    END IF;

    -- WTO: 免费API，限流宽松
    IF src_macro_wto IS NOT NULL THEN
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (src_macro_wto, 'token_bucket', 30, 60, 30, 10, 'database', 'WTO免费API，每分钟30次请求')
        ON CONFLICT (source_config_id) DO NOTHING;
    END IF;

    -- FMP: 付费API，高配额
    IF src_fundamentals_fmp IS NOT NULL THEN
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (src_fundamentals_fmp, 'token_bucket', 250, 60, 250, 20, 'database', 'FMP付费API，每分钟250次请求')
        ON CONFLICT (source_config_id) DO NOTHING;
    END IF;

    -- SEC: 免费API，但有严格的爬虫政策
    IF src_fundamentals_sec IS NOT NULL THEN
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, reduce_rate_on_error, error_threshold, config_source, notes)
        VALUES (src_fundamentals_sec, 'token_bucket', 10, 60, 10, 5, true, 3, 'database', 'SEC EDGAR免费但严格，每分钟10次请求')
        ON CONFLICT (source_config_id) DO NOTHING;
    END IF;

    -- Alpha Vantage: 免费用户每天500次，高优先级
    IF src_market_alphavantage IS NOT NULL THEN
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (src_market_alphavantage, 'token_bucket', 75, 60, 75, 15, 'database', 'Alpha Vantage免费API，每分钟75次请求')
        ON CONFLICT (source_config_id) DO NOTHING;
    END IF;


    -- NewsAPI: 付费API，中等配额
    IF src_news_newsapi IS NOT NULL THEN
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (src_news_newsapi, 'token_bucket', 100, 60, 100, 20, 'database', 'NewsAPI付费API，每分钟100次请求')
        ON CONFLICT (source_config_id) DO NOTHING;
    END IF;

    -- ==============================================
    -- 搜索引擎和 AI 数据源限流配置
    -- ==============================================

    -- Bocha 博查: 付费AI搜索，中等配额
    IF src_search_bocha IS NOT NULL THEN
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (src_search_bocha, 'token_bucket', 60, 60, 60, 10, 'database', '博查AI搜索API，每分钟60次请求')
        ON CONFLICT (source_config_id) DO NOTHING;
    END IF;

    -- SHUYAN 数眼智能: 付费数据服务，中等配额
    IF src_search_shuyan IS NOT NULL THEN
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (src_search_shuyan, 'token_bucket', 50, 60, 50, 10, 'database', '数眼智能数据服务API，每分钟50次请求')
        ON CONFLICT (source_config_id) DO NOTHING;
    END IF;

    -- ANSPIRE 安思派: 付费专业服务，较低配额
    IF src_search_anspire IS NOT NULL THEN
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (src_search_anspire, 'token_bucket', 40, 60, 40, 8, 'database', '安思派数据服务API，每分钟40次请求')
        ON CONFLICT (source_config_id) DO NOTHING;
    END IF;

    -- Firecrawl 私有化部署: 自部署，配额根据服务器性能调整
    IF src_search_firecrawl IS NOT NULL THEN
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, reduce_rate_on_error, error_threshold, config_source, notes)
        VALUES (src_search_firecrawl, 'token_bucket', 30, 60, 30, 5, true, 3, 'database', 'Firecrawl私有化部署，每分钟30次请求，网页抓取较重')
        ON CONFLICT (source_config_id) DO NOTHING;
    END IF;

    -- Google Search: 付费API，高配额
    IF src_search_google IS NOT NULL THEN
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (src_search_google, 'token_bucket', 100, 60, 100, 15, 'database', 'Google搜索API，每分钟100次请求')
        ON CONFLICT (source_config_id) DO NOTHING;
    END IF;

    -- Baidu 百度: 付费API，较高配额
    IF src_search_baidu IS NOT NULL THEN
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (src_search_baidu, 'token_bucket', 80, 60, 80, 12, 'database', '百度搜索API，每分钟80次请求')
        ON CONFLICT (source_config_id) DO NOTHING;
    END IF;

    -- Bing 必应: 付费API，高配额
    IF src_search_bing IS NOT NULL THEN
        INSERT INTO data_rate_limit_configs (source_config_id, strategy, rate, period, burst, max_concurrent, config_source, notes)
        VALUES (src_search_bing, 'token_bucket', 100, 60, 100, 15, 'database', '必应搜索API，每分钟100次请求')
        ON CONFLICT (source_config_id) DO NOTHING;
    END IF;
END $$;
