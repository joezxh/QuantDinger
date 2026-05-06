-- ==============================================
-- Data Source Integration Migration v3
-- 新增 CBOE / BEA 数据源配置
-- 新增 qd_data_cache 多级缓存表
-- 新增 data_source_priority_log 优先级调整日志表
-- ==============================================

-- ==============================================
-- 1. 新增数据源配置 seed data (CBOE / BEA)
-- ==============================================

-- CBOE 波动率数据
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'futures_cboe', 'CBOE Volatility Indices', 'data_source',
    ARRAY['Futures'], true, 'round_robin',
    '{"api_key_required": false, "base_url": "https://cdn.cboe.com/api/global/us_indices/daily_prices", "timeout_sec": 20, "rate_limit_per_min": 30, "indices": ["VIX", "VIX3M", "VVIX", "SKEW", "VXN", "VXO", "GVZ", "OVX", "TYVIX"]}'::jsonb,
    'CBOE波动率指数，免费公开CDN数据，提供VIX/VIX3M/VVIX/SKEW等历史数据，无需API Key'
) ON CONFLICT (source_code) DO NOTHING;

-- BEA 经济分析局数据
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'macro_bea', 'BEA (Bureau of Economic Analysis)', 'data_source',
    ARRAY['Macro'], true, 'round_robin',
    '{"api_key_env": "BEA_API_KEY", "api_key_required": true, "base_url": "https://apps.bea.gov/api/data/", "timeout_sec": 20, "rate_limit_per_min": 60, "nipa_indicators": ["gdp_growth", "nominal_gdp", "real_gdp", "pce", "personal_income", "saving_rate"]}'::jsonb,
    '美国经济分析局，提供GDP、PCE、个人收入等NIPA国民收入与产出账户数据，免费注册API Key'
) ON CONFLICT (source_code) DO NOTHING;

-- SimFin 离线基本面数据
INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes)
VALUES (
    'fundamentals_simfin', 'SimFin 离线基本面数据', 'data_source',
    ARRAY['Fundamentals'], true, 'round_robin',
    '{"api_key_required": false, "data_dir": "data/fundamentals/simfin/", "timeout_sec": 5, "rate_limit_per_min": 120, "supports": ["balance_sheet", "income_statements", "cash_flow"], "markets": ["us", "cn"]}'::jsonb,
    'SimFin免费离线基本面数据，提供美股三表(资产负债表/利润表/现金流量表)，需预下载CSV数据文件到data/fundamentals/simfin/目录'
) ON CONFLICT (source_code) DO NOTHING;

-- ==============================================
-- 2. 多级缓存表 (L2: PostgreSQL)
--    cache_manager.py 中的 L2 层使用此表
-- ==============================================

CREATE TABLE IF NOT EXISTS qd_data_cache (
    id BIGSERIAL PRIMARY KEY,
    cache_key VARCHAR(500) NOT NULL,
    cache_value JSONB NOT NULL,
    data_type VARCHAR(50) DEFAULT 'unknown',  -- kline, ticker, macro, news, fundamentals, etc.
    ttl_seconds INTEGER DEFAULT 300,
    expires_at TIMESTAMP NOT NULL,
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(cache_key)
);

CREATE INDEX IF NOT EXISTS idx_qd_data_cache_expires ON qd_data_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_qd_data_cache_data_type ON qd_data_cache(data_type);
CREATE INDEX IF NOT EXISTS idx_qd_data_cache_key ON qd_data_cache(cache_key);

-- ==============================================
-- 3. 优先级调整日志表
--    priority_adjuster.py 调整记录
-- ==============================================

CREATE TABLE IF NOT EXISTS data_source_priority_log (
    id BIGSERIAL PRIMARY KEY,
    source_code VARCHAR(80) NOT NULL,
    category VARCHAR(50) NOT NULL,
    baseline_priority NUMERIC(10, 2) NOT NULL,
    adjusted_priority NUMERIC(10, 2) NOT NULL,
    health_factor NUMERIC(5, 3) DEFAULT 0.5,
    latency_factor NUMERIC(5, 3) DEFAULT 1.0,
    avg_latency_ms INTEGER DEFAULT 0,
    health_stats JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_priority_log_source ON data_source_priority_log(source_code);
CREATE INDEX IF NOT EXISTS idx_priority_log_created ON data_source_priority_log(created_at);

-- ==============================================
-- 4. 健康检查表补充索引和字段
-- ==============================================

-- 为 data_source_health 添加缺失的字段（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'data_source_health' AND column_name = 'consecutive_failures'
    ) THEN
        ALTER TABLE data_source_health ADD COLUMN consecutive_failures INTEGER DEFAULT 0;
    END IF;
END $$;

-- ==============================================
-- 5. 定期清理任务（缓存过期数据 & 旧日志）
-- ==============================================

-- 清理过期缓存（应定期执行，如每小时）
-- 可由 cron 或 Flask 后台任务触发
-- DELETE FROM qd_data_cache WHERE expires_at < NOW();

-- 清理30天前的优先级日志
-- DELETE FROM data_source_priority_log WHERE created_at < NOW() - INTERVAL '30 days';
