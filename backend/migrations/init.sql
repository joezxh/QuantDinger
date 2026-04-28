-- QuantDinger PostgreSQL Schema Initialization
-- This script runs automatically when PostgreSQL container starts for the first time.

-- Level 0: Tables with NO foreign keys
-- =============================================================================

-- AI calibration parameters per market
CREATE TABLE IF NOT EXISTS trade_ai_calibration (
    id SERIAL PRIMARY KEY,
    market VARCHAR(50) NOT NULL,
    buy_threshold NUMERIC(10, 4) NOT NULL,
    sell_threshold NUMERIC(10, 4) NOT NULL,
    min_consensus_abs_override NUMERIC(10, 4) NOT NULL,
    quality_hold_threshold NUMERIC(10, 4) NOT NULL,
    validated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AI analysis results history
CREATE TABLE IF NOT EXISTS trade_analysis_results (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    market VARCHAR(50) NOT NULL,
    symbol VARCHAR(100) NOT NULL,
    decision VARCHAR(30),
    confidence NUMERIC(10, 4),
    summary TEXT,
    payload_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analysis_results_market_symbol ON trade_analysis_results(market, symbol);
CREATE INDEX IF NOT EXISTS idx_analysis_results_user ON trade_analysis_results(user_id);

-- LLM Provider (OpenRouter/OpenAI/Azure/Custom)
CREATE TABLE IF NOT EXISTS sys_llm_provider (
    id SERIAL PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    code VARCHAR(64) UNIQUE NOT NULL,
    base_url VARCHAR(256),
    api_type VARCHAR(32) DEFAULT 'openai',
    status SMALLINT DEFAULT 1,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_llm_provider_code ON sys_llm_provider(code);

-- =============================================================================
-- Level 1: LLM tables (depend on sys_llm_provider)
-- =============================================================================
CREATE TABLE IF NOT EXISTS sys_llm_api_key (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER NOT NULL REFERENCES sys_llm_provider(id) ON DELETE CASCADE,
    name VARCHAR(64),
    api_key_enc TEXT NOT NULL,
    status SMALLINT DEFAULT 1,
    weight INTEGER DEFAULT 1,
    owner_id BIGINT DEFAULT 0,
    is_public SMALLINT DEFAULT 0,
    fail_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sys_llm_api_key_provider ON sys_llm_api_key(provider_id);
CREATE INDEX IF NOT EXISTS idx_sys_llm_api_key_status ON sys_llm_api_key(status);

CREATE TABLE IF NOT EXISTS sys_llm_model (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER NOT NULL REFERENCES sys_llm_provider(id) ON DELETE CASCADE,
    model_name VARCHAR(64) NOT NULL,
    display_name VARCHAR(64),
    lb_strategy VARCHAR(32) DEFAULT 'weighted_round_robin',
    retries INTEGER DEFAULT 3,
    timeout INTEGER DEFAULT 60,
    status SMALLINT DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sys_llm_model_provider ON sys_llm_model(provider_id);

CREATE TABLE IF NOT EXISTS sys_llm_call_log (
    id BIGSERIAL PRIMARY KEY,
    api_key_id INTEGER NOT NULL REFERENCES sys_llm_api_key(id) ON DELETE CASCADE,
    model_id INTEGER NOT NULL REFERENCES sys_llm_model(id) ON DELETE CASCADE,
    user_id BIGINT,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    latency_ms INTEGER,
    status_code INTEGER,
    error_msg TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sys_llm_call_log_created ON sys_llm_call_log(created_at);

-- Market price snapshots (lightweight, ephemeral)
CREATE TABLE IF NOT EXISTS trade_market_prices (
    id SERIAL PRIMARY KEY,
    market VARCHAR(50) NOT NULL,
    symbol VARCHAR(100) NOT NULL,
    price NUMERIC(24, 8) NOT NULL,
    change_percent NUMERIC(10, 4),
    snapshot_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_market_prices_lookup ON trade_market_prices(market, symbol);

-- Market k-line / OHLCV data
CREATE TABLE IF NOT EXISTS trade_market_klines (
    id SERIAL PRIMARY KEY,
    market VARCHAR(50) NOT NULL,
    symbol VARCHAR(100) NOT NULL,
    timeframe VARCHAR(20) NOT NULL,
    open_price NUMERIC(24, 8) NOT NULL,
    high_price NUMERIC(24, 8) NOT NULL,
    low_price NUMERIC(24, 8) NOT NULL,
    close_price NUMERIC(24, 8) NOT NULL,
    volume NUMERIC(24, 8),
    kline_time TIMESTAMP WITH TIME ZONE,
    payload_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_market_klines_lookup ON trade_market_klines(market, symbol, timeframe, kline_time);


-- Strategy metadata (non-trading, just shared strategy definitions)
CREATE TABLE IF NOT EXISTS trade_strategies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    strategy_type VARCHAR(100),
    status VARCHAR(30) DEFAULT 'draft',
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- 1. Users & Authentication
-- =============================================================================

CREATE TABLE IF NOT EXISTS sys_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE,
    nickname VARCHAR(50),
    avatar VARCHAR(255) DEFAULT '/avatar2.jpg',
    phone VARCHAR(50),
    bio TEXT,
    status VARCHAR(20) DEFAULT 'active',
    role VARCHAR(20) DEFAULT 'user',
    credits NUMERIC(20, 2) DEFAULT 0,
    vip_expires_at TIMESTAMP WITH TIME ZONE,
    vip_plan VARCHAR(20) DEFAULT '',
    vip_is_lifetime BOOLEAN DEFAULT FALSE,
    vip_monthly_credits_last_grant TIMESTAMP WITH TIME ZONE,
    email_verified BOOLEAN DEFAULT FALSE,
    is_email_verified BOOLEAN DEFAULT FALSE,
    is_phone_verified BOOLEAN DEFAULT FALSE,
    referred_by INTEGER,
    notification_settings TEXT DEFAULT '',
    chart_templates TEXT DEFAULT '',
    timezone VARCHAR(64) DEFAULT '',
    token_version INTEGER DEFAULT 1,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_referred_by ON sys_users(referred_by);
CREATE INDEX IF NOT EXISTS idx_users_email ON sys_users(email);

CREATE INDEX IF NOT EXISTS idx_users_status ON sys_users(status);

-- Note: Admin user is created automatically by the application on startup
-- using ADMIN_USER and ADMIN_PASSWORD from environment variables

-- =============================================================================
-- 0.1. Super Admin User Initialization
-- =============================================================================
-- Generate password hash: python -c "from passlib.context import CryptContext; pwd_ctx = CryptContext(schemes=['bcrypt'], deprecated='auto'); print(pwd_ctx.hash('your_password'))"
-- Default password: admin123 (hash below) - PLEASE CHANGE THIS IN PRODUCTION!
-- bcrypt hash generated with workfactor=12

INSERT INTO sys_users (
    username,
    password_hash,
    email,
    nickname,
    role,
    status,
    credits,
    vip_plan,
    vip_is_lifetime,
    vip_expires_at,
    email_verified,
    is_email_verified,
    timezone,
    notification_settings,
    chart_templates
) VALUES (
    'admin',
    '$2b$12$g9qknhRhDsnkws5GtmhbeuIIfeZ.Myukxd3X0wQv2CNcAGJk7kwxu',
    'admin@quantdinger.com',
    'Super Administrator',
    'admin',
    'active',
    99999.00,
    'lifetime',
    TRUE,
    '2099-12-31 23:59:59+00',
    TRUE,
    TRUE,
    'Asia/Shanghai',
    '{"email": true, "telegram": true, "sms": false}',
    '{"default": "default_template"}'
) ON CONFLICT (username) DO UPDATE SET
    role = EXCLUDED.role,
    vip_plan = EXCLUDED.vip_plan,
    vip_is_lifetime = EXCLUDED.vip_is_lifetime,
    updated_at = NOW();

-- OAuth CSRF State (多 worker / 多实例共享，避免 Invalid state)
CREATE TABLE IF NOT EXISTS sys_oauth_states (
    state VARCHAR(128) PRIMARY KEY,
    provider VARCHAR(20) NOT NULL,
    redirect TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_oauth_states_expires ON sys_oauth_states(expires_at);


-- Login Attempts (登录尝试记录 - 防爆破)
CREATE TABLE IF NOT EXISTS sys_login_attempts (
    id SERIAL PRIMARY KEY,
    identifier VARCHAR(255) NOT NULL,
    identifier_type VARCHAR(32) NOT NULL,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    ip_address VARCHAR(64),
    user_agent TEXT,
    attempt_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_login_attempts_identifier ON sys_login_attempts(identifier, identifier_type);
CREATE INDEX IF NOT EXISTS idx_login_attempts_time ON sys_login_attempts(attempt_time);

-- Security Audit Log (安全审计日志)
CREATE TABLE IF NOT EXISTS sys_security_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(64) NOT NULL,
    ip_address VARCHAR(64),
    user_agent TEXT,
    details_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_security_logs_user_id ON sys_security_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_security_logs_action ON sys_security_logs(action);
CREATE INDEX IF NOT EXISTS idx_security_logs_created_at ON sys_security_logs(created_at);

-- =============================================================================
-- 1.5. Credits Log (积分变动日志)
-- =============================================================================

CREATE TABLE IF NOT EXISTS sys_credits_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES sys_users(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    amount NUMERIC(20, 2) NOT NULL,
    balance_after NUMERIC(20, 2) NOT NULL,
    feature VARCHAR(50) DEFAULT '',
    reference_id VARCHAR(100) DEFAULT '',
    remark TEXT DEFAULT '',
    operator_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_credits_log_user_id ON sys_credits_log(user_id);
CREATE INDEX IF NOT EXISTS idx_credits_log_action ON sys_credits_log(action);
CREATE INDEX IF NOT EXISTS idx_credits_log_created_at ON sys_credits_log(created_at);

-- =============================================================================
-- 1.55. Membership Orders (会员订单 - Mock支付)
-- =============================================================================

CREATE TABLE IF NOT EXISTS sys_membership_orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES sys_users(id) ON DELETE CASCADE,
    plan VARCHAR(20) NOT NULL,
    price_usd NUMERIC(10, 2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'paid',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    paid_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_membership_orders_user_id ON sys_membership_orders(user_id);

-- =============================================================================
-- 1.56. USDT Orders (USDT 收款订单 - 每单独立地址)
-- =============================================================================

CREATE TABLE IF NOT EXISTS sys_usdt_orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES sys_users(id) ON DELETE CASCADE,
    plan VARCHAR(20) NOT NULL,
    chain VARCHAR(20) NOT NULL DEFAULT 'TRC20',
    amount_usdt NUMERIC(20, 6) NOT NULL DEFAULT 0,
    address_index INTEGER NOT NULL DEFAULT 0,
    address VARCHAR(80) NOT NULL DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    tx_hash VARCHAR(120) DEFAULT '',
    paid_at TIMESTAMP WITH TIME ZONE,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_usdt_orders_address_unique ON sys_usdt_orders(chain, address);
CREATE INDEX IF NOT EXISTS idx_usdt_orders_user_id ON sys_usdt_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_usdt_orders_status ON sys_usdt_orders(status);

-- =============================================================================
-- 1.6. Verification Codes (邮箱验证码)
-- =============================================================================

CREATE TABLE IF NOT EXISTS sys_verification_codes (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100) NOT NULL,
    code VARCHAR(10) NOT NULL,
    type VARCHAR(20) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    ip_address VARCHAR(45),
    attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_verification_codes_email ON sys_verification_codes(email);
CREATE INDEX IF NOT EXISTS idx_verification_codes_type ON sys_verification_codes(type);
CREATE INDEX IF NOT EXISTS idx_verification_codes_expires ON sys_verification_codes(expires_at);

-- =============================================================================
-- 1.8. OAuth Links (第三方账号关联)
-- =============================================================================

CREATE TABLE IF NOT EXISTS sys_oauth_links (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES sys_users(id) ON DELETE CASCADE,
    provider VARCHAR(20) NOT NULL,
    provider_user_id VARCHAR(100) NOT NULL UNIQUE,
    provider_email VARCHAR(100),
    provider_name VARCHAR(100),
    provider_avatar VARCHAR(255),
    access_token TEXT,
    refresh_token TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_oauth_links_user_id ON sys_oauth_links(user_id);
CREATE INDEX IF NOT EXISTS idx_oauth_links_provider ON sys_oauth_links(provider);

-- =============================================================================
-- 1.9. Billing Records (计费记录)
-- =============================================================================

CREATE TABLE IF NOT EXISTS sys_billing_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    feature VARCHAR(100) NOT NULL,
    amount NUMERIC(18, 4) NOT NULL,
    balance_before NUMERIC(18, 4),
    balance_after NUMERIC(18, 4),
    reference_id VARCHAR(100),
    occurred_at TIMESTAMP WITH TIME ZONE,
    payload_json TEXT,
    billing_type VARCHAR(50),
    status VARCHAR(30),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_billing_records_user ON sys_billing_records(user_id);
CREATE INDEX IF NOT EXISTS idx_billing_records_feature ON sys_billing_records(feature);

-- =============================================================================
-- 2. Strategy Trading (核心交易策略表)
-- =============================================================================

CREATE TABLE IF NOT EXISTS trade_strategies_trading (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1 REFERENCES sys_users(id) ON DELETE CASCADE,
    strategy_name VARCHAR(255) NOT NULL,
    strategy_type VARCHAR(50) DEFAULT 'IndicatorStrategy',
    market_category VARCHAR(50) DEFAULT 'Crypto',
    execution_mode VARCHAR(20) DEFAULT 'signal',
    notification_config TEXT DEFAULT '',
    status VARCHAR(20) DEFAULT 'stopped',
    symbol VARCHAR(50),
    timeframe VARCHAR(10),
    initial_capital NUMERIC(20, 8) DEFAULT 1000,
    leverage INTEGER DEFAULT 1,
    market_type VARCHAR(20) DEFAULT 'swap',
    exchange_config TEXT,
    indicator_config TEXT,
    trading_config TEXT,
    ai_model_config TEXT,
    decide_interval INTEGER DEFAULT 300,
    strategy_group_id VARCHAR(100) DEFAULT '',
    group_base_name VARCHAR(255) DEFAULT '',
    strategy_mode VARCHAR(20) DEFAULT 'signal',
    strategy_code TEXT DEFAULT '',
    last_rebalance_at TIMESTAMP WITH TIME ZONE,
    strategy_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_strategies_user_id ON trade_strategies_trading(user_id);
CREATE INDEX IF NOT EXISTS idx_strategies_status ON trade_strategies_trading(status);
CREATE INDEX IF NOT EXISTS idx_strategies_group_id ON trade_strategies_trading(strategy_group_id);

-- =============================================================================
-- 3. Strategy Positions
-- =============================================================================

CREATE TABLE IF NOT EXISTS trade_strategy_positions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1 REFERENCES sys_users(id) ON DELETE CASCADE,
    strategy_id INTEGER REFERENCES trade_strategies_trading(id) ON DELETE CASCADE,
    symbol VARCHAR(50),
    side VARCHAR(10),
    size NUMERIC(20, 8),
    entry_price NUMERIC(20, 8),
    current_price NUMERIC(20, 8),
    highest_price NUMERIC(20, 8) DEFAULT 0,
    lowest_price NUMERIC(20, 8) DEFAULT 0,
    unrealized_pnl NUMERIC(20, 8) DEFAULT 0,
    pnl_percent NUMERIC(10, 4) DEFAULT 0,
    equity NUMERIC(20, 8) DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(strategy_id, symbol, side)
);

CREATE INDEX IF NOT EXISTS idx_positions_user_id ON trade_strategy_positions(user_id);
CREATE INDEX IF NOT EXISTS idx_positions_strategy_id ON trade_strategy_positions(strategy_id);

-- =============================================================================
-- 4. Strategy Trades
-- =============================================================================

CREATE TABLE IF NOT EXISTS trade_strategy_trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1 REFERENCES sys_users(id) ON DELETE CASCADE,
    strategy_id INTEGER REFERENCES trade_strategies_trading(id) ON DELETE CASCADE,
    symbol VARCHAR(50),
    type VARCHAR(30),
    price NUMERIC(20, 8),
    amount NUMERIC(20, 8),
    value NUMERIC(20, 8),
    commission NUMERIC(20, 8) DEFAULT 0,
    commission_ccy VARCHAR(20) DEFAULT '',
    profit NUMERIC(20, 8) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trade_strategy_trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_strategy_id ON trade_strategy_trades(strategy_id);
CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trade_strategy_trades(created_at);

-- =============================================================================
-- 4b. Trade Orders (实际交易订单记录)
-- =============================================================================
CREATE TABLE IF NOT EXISTS trade_trade_orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    strategy_id INTEGER,
    market VARCHAR(50) NOT NULL,
    symbol VARCHAR(100) NOT NULL,
    side VARCHAR(20) NOT NULL,
    order_type VARCHAR(30),
    quantity NUMERIC(24, 8),
    price NUMERIC(24, 8),
    status VARCHAR(30),
    submitted_at TIMESTAMP WITH TIME ZONE,
    payload_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- 5. Pending Orders Queue
-- =============================================================================

CREATE TABLE IF NOT EXISTS trade_pending_orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1 REFERENCES sys_users(id) ON DELETE CASCADE,
    strategy_id INTEGER REFERENCES trade_strategies_trading(id) ON DELETE SET NULL,
    symbol VARCHAR(50) NOT NULL,
    signal_type VARCHAR(30) NOT NULL,
    signal_ts BIGINT,
    market_type VARCHAR(20) DEFAULT 'swap',
    order_type VARCHAR(20) DEFAULT 'market',
    amount NUMERIC(20, 8) DEFAULT 0,
    price NUMERIC(20, 8) DEFAULT 0,
    execution_mode VARCHAR(20) DEFAULT 'signal',
    status VARCHAR(20) DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 10,
    last_error TEXT DEFAULT '',
    payload_json TEXT DEFAULT '',
    dispatch_note TEXT DEFAULT '',
    exchange_id VARCHAR(50) DEFAULT '',
    exchange_order_id VARCHAR(100) DEFAULT '',
    exchange_response_json TEXT DEFAULT '',
    filled NUMERIC(20, 8) DEFAULT 0,
    avg_price NUMERIC(20, 8) DEFAULT 0,
    executed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_trade_pending_orders_user_id ON trade_pending_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_trade_pending_orders_status ON trade_pending_orders(status);
CREATE INDEX IF NOT EXISTS idx_trade_pending_orders_strategy_id ON trade_pending_orders(strategy_id);

-- =============================================================================
-- 6. Strategy Notifications
-- =============================================================================

CREATE TABLE IF NOT EXISTS trade_strategy_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1 REFERENCES sys_users(id) ON DELETE CASCADE,
    strategy_id INTEGER REFERENCES trade_strategies_trading(id) ON DELETE CASCADE,
    symbol VARCHAR(50) DEFAULT '',
    signal_type VARCHAR(30) DEFAULT '',
    channels VARCHAR(255) DEFAULT '',
    title VARCHAR(255) DEFAULT '',
    message TEXT DEFAULT '',
    payload_json TEXT DEFAULT '',
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON trade_strategy_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_strategy_id ON trade_strategy_notifications(strategy_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON trade_strategy_notifications(is_read);

-- =============================================================================
-- 6b. Strategy runtime logs (dashboard / API)
-- =============================================================================

CREATE TABLE IF NOT EXISTS trade_strategy_logs (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER NOT NULL REFERENCES trade_strategies_trading(id) ON DELETE CASCADE,
    level VARCHAR(20) DEFAULT 'info',
    message TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_strategy_logs_strategy_id ON trade_strategy_logs(strategy_id);
CREATE INDEX IF NOT EXISTS idx_strategy_logs_timestamp ON trade_strategy_logs(timestamp);

-- =============================================================================
-- 7. Indicator Codes
-- =============================================================================

CREATE TABLE IF NOT EXISTS ind_indicator_codes (
   id SERIAL PRIMARY KEY,
   user_id INTEGER DEFAULT 1 NOT NULL REFERENCES sys_users(id) ON DELETE CASCADE,
   is_buy INTEGER DEFAULT 0 NOT NULL,
   end_time BIGINT DEFAULT 1 NOT NULL,
   name VARCHAR(255) NOT NULL DEFAULT '',
   code TEXT,
   description TEXT DEFAULT '',
   publish_to_community INTEGER DEFAULT 0 NOT NULL,
   pricing_type VARCHAR(20) NOT NULL DEFAULT 'free',
   price NUMERIC(10, 2) NOT NULL DEFAULT 0,
   is_encrypted INTEGER DEFAULT 0 NOT NULL,
   preview_image VARCHAR(500),
   vip_free BOOLEAN DEFAULT FALSE,
   createtime INTEGER,
   updatetime INTEGER,
   created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
   updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
   purchase_count INTEGER DEFAULT 0,
   avg_rating NUMERIC(3, 2) DEFAULT 0,
   rating_count INTEGER DEFAULT 0,
   view_count INTEGER DEFAULT 0,
   review_status VARCHAR(20) DEFAULT 'approved',
   review_note TEXT DEFAULT '',
   reviewed_at TIMESTAMP WITH TIME ZONE,
   reviewed_by INTEGER,
   source_indicator_id INTEGER
);

CREATE INDEX IF NOT EXISTS idx_indicator_codes_user_id ON ind_indicator_codes(user_id);
CREATE INDEX IF NOT EXISTS idx_indicator_review_status ON ind_indicator_codes(review_status);
CREATE INDEX IF NOT EXISTS idx_indicator_codes_source ON ind_indicator_codes(source_indicator_id);

-- =============================================================================
-- 10. Watchlist
-- =============================================================================

CREATE TABLE IF NOT EXISTS trade_watchlist (
    id SERIAL PRIMARY KEY,
    user_id INTEGER DEFAULT 1 REFERENCES sys_users(id) ON DELETE CASCADE,
    market VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    name VARCHAR(100) DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, market, symbol)
);

CREATE INDEX IF NOT EXISTS idx_watchlist_user_id ON trade_watchlist(user_id);

-- =============================================================================
-- 11. Analysis Tasks
-- =============================================================================

CREATE TABLE IF NOT EXISTS analy_analysis_tasks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER DEFAULT 1 REFERENCES sys_users(id) ON DELETE CASCADE,
    market VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    model VARCHAR(100) DEFAULT '',
    language VARCHAR(20) DEFAULT 'en-US',
    status VARCHAR(20) DEFAULT 'completed',
    result_json TEXT DEFAULT '',
    error_message TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_analysis_tasks_user_id ON analy_analysis_tasks(user_id);

-- =============================================================================
-- 12. Backtest Runs
-- =============================================================================

CREATE TABLE IF NOT EXISTS ind_backtest_runs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1 REFERENCES sys_users(id) ON DELETE CASCADE,
    strategy_id INTEGER,
    indicator_id INTEGER,
    strategy_name VARCHAR(255) DEFAULT '',
    run_type VARCHAR(50) DEFAULT 'indicator',
    engine_version VARCHAR(50) DEFAULT '',
    code_hash VARCHAR(128) DEFAULT '',
    config_snapshot TEXT DEFAULT '',
    total_return NUMERIC(18, 6),
    win_rate NUMERIC(10, 4),
    max_drawdown NUMERIC(10, 4),
    payload_json TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_backtest_runs_user_id ON ind_backtest_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_backtest_runs_indicator_id ON ind_backtest_runs(indicator_id);
CREATE INDEX IF NOT EXISTS idx_backtest_runs_strategy_id ON ind_backtest_runs(strategy_id);
CREATE INDEX IF NOT EXISTS idx_backtest_runs_run_type ON ind_backtest_runs(run_type);

CREATE TABLE IF NOT EXISTS ind_backtest_trades (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL DEFAULT 1 REFERENCES sys_users(id) ON DELETE CASCADE,
    strategy_id INTEGER,
    trade_index INTEGER DEFAULT 0,
    trade_time VARCHAR(64) DEFAULT '',
    trade_type VARCHAR(64) DEFAULT '',
    side VARCHAR(32) DEFAULT '',
    price NUMERIC(24, 8) DEFAULT 0,
    amount NUMERIC(24, 8) DEFAULT 0,
    profit NUMERIC(24, 8) DEFAULT 0,
    balance NUMERIC(24, 8) DEFAULT 0,
    reason VARCHAR(64) DEFAULT '',
    payload_json TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_backtest_trades_run_id ON ind_backtest_trades(run_id);

CREATE TABLE IF NOT EXISTS ind_backtest_equity_points (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL,
    point_index INTEGER DEFAULT 0,
    point_time VARCHAR(64) DEFAULT '',
    point_value NUMERIC(24, 8) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_backtest_equity_points_run_id ON ind_backtest_equity_points(run_id);

-- =============================================================================
-- 13. Exchange Credentials
-- =============================================================================

CREATE TABLE IF NOT EXISTS trade_exchange_credentials (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1 REFERENCES sys_users(id) ON DELETE CASCADE,
    name VARCHAR(100) DEFAULT '',
    exchange_id VARCHAR(50) NOT NULL,
    api_key_hint VARCHAR(50) DEFAULT '',
    encrypted_config TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_exchange_credentials_user_id ON trade_exchange_credentials(user_id);

-- =============================================================================
-- 14. Manual Positions
-- =============================================================================

CREATE TABLE IF NOT EXISTS trade_manual_positions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1 REFERENCES sys_users(id) ON DELETE CASCADE,
    market VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    name VARCHAR(100) DEFAULT '',
    side VARCHAR(10) DEFAULT 'long',
    quantity NUMERIC(20, 8) NOT NULL DEFAULT 0,
    entry_price NUMERIC(20, 8) NOT NULL DEFAULT 0,
    entry_time BIGINT,
    notes TEXT DEFAULT '',
    tags TEXT DEFAULT '',
    group_name VARCHAR(100) DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, market, symbol, side, group_name)
);

CREATE INDEX IF NOT EXISTS idx_manual_positions_user_id ON trade_manual_positions(user_id);

-- =============================================================================
-- 15. Position Alerts
-- =============================================================================

CREATE TABLE IF NOT EXISTS trade_position_alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1 REFERENCES sys_users(id) ON DELETE CASCADE,
    position_id INTEGER,
    market VARCHAR(50) DEFAULT '',
    symbol VARCHAR(50) DEFAULT '',
    alert_type VARCHAR(30) NOT NULL,
    threshold NUMERIC(20, 8) NOT NULL DEFAULT 0,
    notification_config TEXT DEFAULT '',
    is_active INTEGER DEFAULT 1,
    is_triggered INTEGER DEFAULT 0,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,
    repeat_interval INTEGER DEFAULT 0,
    notes TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_position_alerts_user_id ON trade_position_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_position_alerts_position_id ON trade_position_alerts(position_id);

-- =============================================================================
-- 16. Position Monitors
-- =============================================================================

CREATE TABLE IF NOT EXISTS trade_position_monitors (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1 REFERENCES sys_users(id) ON DELETE CASCADE,
    name VARCHAR(100) DEFAULT '',
    position_ids TEXT DEFAULT '',
    monitor_type VARCHAR(20) DEFAULT 'ai',
    config TEXT DEFAULT '',
    notification_config TEXT DEFAULT '',
    is_active INTEGER DEFAULT 1,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    last_result TEXT DEFAULT '',
    run_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_position_monitors_user_id ON trade_position_monitors(user_id);

-- =============================================================================
-- 17. Market Symbols (Seed Data)
-- =============================================================================

CREATE TABLE IF NOT EXISTS trade_market_symbols (
    id SERIAL PRIMARY KEY,
    market VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    name VARCHAR(255) DEFAULT '',
    exchange VARCHAR(50) DEFAULT '',
    currency VARCHAR(10) DEFAULT '',
    is_active INTEGER DEFAULT 1,
    is_hot INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(market, symbol)
);

CREATE INDEX IF NOT EXISTS idx_market_symbols_market ON trade_market_symbols(market);
CREATE INDEX IF NOT EXISTS idx_market_symbols_is_hot ON trade_market_symbols(market, is_hot);

-- Seed data: Hot symbols for each market
INSERT INTO trade_market_symbols (market, symbol, name, exchange, currency, is_active, is_hot, sort_order) VALUES
-- USStock (US Stocks)
('USStock', 'AAPL', 'Apple Inc.', 'NASDAQ', 'USD', 1, 1, 100),
('USStock', 'MSFT', 'Microsoft Corporation', 'NASDAQ', 'USD', 1, 1, 99),
('USStock', 'GOOGL', 'Alphabet Inc.', 'NASDAQ', 'USD', 1, 1, 98),
('USStock', 'AMZN', 'Amazon.com Inc.', 'NASDAQ', 'USD', 1, 1, 97),
('USStock', 'TSLA', 'Tesla, Inc.', 'NASDAQ', 'USD', 1, 1, 96),
('USStock', 'META', 'Meta Platforms Inc.', 'NASDAQ', 'USD', 1, 1, 95),
('USStock', 'NVDA', 'NVIDIA Corporation', 'NASDAQ', 'USD', 1, 1, 94),
('USStock', 'JPM', 'JPMorgan Chase & Co.', 'NYSE', 'USD', 1, 1, 93),
('USStock', 'V', 'Visa Inc.', 'NYSE', 'USD', 1, 1, 92),
('USStock', 'JNJ', 'Johnson & Johnson', 'NYSE', 'USD', 1, 1, 91),
-- Crypto (major + popular altcoins)
('Crypto', 'BTC/USDT', 'Bitcoin', 'Binance', 'USDT', 1, 1, 100),
('Crypto', 'ETH/USDT', 'Ethereum', 'Binance', 'USDT', 1, 1, 99),
('Crypto', 'BNB/USDT', 'BNB', 'Binance', 'USDT', 1, 1, 98),
('Crypto', 'SOL/USDT', 'Solana', 'Binance', 'USDT', 1, 1, 97),
('Crypto', 'XRP/USDT', 'Ripple', 'Binance', 'USDT', 1, 1, 96),
('Crypto', 'ADA/USDT', 'Cardano', 'Binance', 'USDT', 1, 1, 95),
('Crypto', 'DOGE/USDT', 'Dogecoin', 'Binance', 'USDT', 1, 1, 94),
('Crypto', 'DOT/USDT', 'Polkadot', 'Binance', 'USDT', 1, 1, 93),
('Crypto', 'POL/USDT', 'Polygon', 'Binance', 'USDT', 1, 1, 92),
('Crypto', 'AVAX/USDT', 'Avalanche', 'Binance', 'USDT', 1, 1, 91),
-- Layer 1 / Layer 2
('Crypto', 'LINK/USDT', 'Chainlink', 'Binance', 'USDT', 1, 1, 90),
('Crypto', 'UNI/USDT', 'Uniswap', 'Binance', 'USDT', 1, 1, 89),
('Crypto', 'ATOM/USDT', 'Cosmos', 'Binance', 'USDT', 1, 1, 88),
('Crypto', 'LTC/USDT', 'Litecoin', 'Binance', 'USDT', 1, 1, 87),
('Crypto', 'FIL/USDT', 'Filecoin', 'Binance', 'USDT', 1, 1, 86),
('Crypto', 'NEAR/USDT', 'NEAR Protocol', 'Binance', 'USDT', 1, 1, 85),
('Crypto', 'APT/USDT', 'Aptos', 'Binance', 'USDT', 1, 1, 84),
('Crypto', 'SUI/USDT', 'Sui', 'Binance', 'USDT', 1, 1, 83),
('Crypto', 'ARB/USDT', 'Arbitrum', 'Binance', 'USDT', 1, 1, 82),
('Crypto', 'OP/USDT', 'Optimism', 'Binance', 'USDT', 1, 1, 81),
('Crypto', 'SEI/USDT', 'Sei', 'Binance', 'USDT', 1, 1, 80),
('Crypto', 'TIA/USDT', 'Celestia', 'Binance', 'USDT', 1, 1, 79),
('Crypto', 'INJ/USDT', 'Injective', 'Binance', 'USDT', 1, 1, 78),
('Crypto', 'FTM/USDT', 'Fantom', 'Binance', 'USDT', 1, 1, 77),
('Crypto', 'ALGO/USDT', 'Algorand', 'Binance', 'USDT', 1, 1, 76),
('Crypto', 'HBAR/USDT', 'Hedera', 'Binance', 'USDT', 1, 1, 75),
('Crypto', 'ICP/USDT', 'Internet Computer', 'Binance', 'USDT', 1, 1, 74),
('Crypto', 'VET/USDT', 'VeChain', 'Binance', 'USDT', 1, 1, 73),
('Crypto', 'SAND/USDT', 'The Sandbox', 'Binance', 'USDT', 1, 1, 72),
('Crypto', 'MANA/USDT', 'Decentraland', 'Binance', 'USDT', 1, 1, 71),
-- DeFi
('Crypto', 'AAVE/USDT', 'Aave', 'Binance', 'USDT', 1, 1, 70),
('Crypto', 'MKR/USDT', 'Maker', 'Binance', 'USDT', 1, 1, 69),
('Crypto', 'CRV/USDT', 'Curve DAO', 'Binance', 'USDT', 1, 1, 68),
('Crypto', 'COMP/USDT', 'Compound', 'Binance', 'USDT', 1, 1, 67),
('Crypto', 'SNX/USDT', 'Synthetix', 'Binance', 'USDT', 1, 1, 66),
('Crypto', 'SUSHI/USDT', 'SushiSwap', 'Binance', 'USDT', 1, 1, 65),
('Crypto', 'DYDX/USDT', 'dYdX', 'Binance', 'USDT', 1, 1, 64),
('Crypto', 'LDO/USDT', 'Lido DAO', 'Binance', 'USDT', 1, 1, 63),
('Crypto', 'PENDLE/USDT', 'Pendle', 'Binance', 'USDT', 1, 1, 62),
('Crypto', 'JUP/USDT', 'Jupiter', 'Binance', 'USDT', 1, 1, 61),
-- Meme coins
('Crypto', 'SHIB/USDT', 'Shiba Inu', 'Binance', 'USDT', 1, 1, 60),
('Crypto', 'PEPE/USDT', 'Pepe', 'Binance', 'USDT', 1, 1, 59),
('Crypto', 'WIF/USDT', 'dogwifhat', 'Binance', 'USDT', 1, 1, 58),
('Crypto', 'FLOKI/USDT', 'Floki', 'Binance', 'USDT', 1, 1, 57),
('Crypto', 'BONK/USDT', 'Bonk', 'Binance', 'USDT', 1, 1, 56),
('Crypto', 'MEME/USDT', 'Memecoin', 'Binance', 'USDT', 1, 1, 55),
('Crypto', 'TURBO/USDT', 'Turbo', 'Binance', 'USDT', 1, 1, 54),
('Crypto', 'NEIRO/USDT', 'Neiro', 'Binance', 'USDT', 1, 1, 53),
-- AI / Infra
('Crypto', 'RENDER/USDT', 'Render', 'Binance', 'USDT', 1, 1, 52),
('Crypto', 'FET/USDT', 'Fetch.ai', 'Binance', 'USDT', 1, 1, 51),
('Crypto', 'RNDR/USDT', 'Render Network', 'Binance', 'USDT', 1, 1, 50),
('Crypto', 'TAO/USDT', 'Bittensor', 'Binance', 'USDT', 1, 1, 49),
('Crypto', 'WLD/USDT', 'Worldcoin', 'Binance', 'USDT', 1, 1, 48),
('Crypto', 'AR/USDT', 'Arweave', 'Binance', 'USDT', 1, 1, 47),
('Crypto', 'STX/USDT', 'Stacks', 'Binance', 'USDT', 1, 1, 46),
('Crypto', 'ORDI/USDT', 'ORDI', 'Binance', 'USDT', 1, 1, 45),
-- Others
('Crypto', 'TRX/USDT', 'Tron', 'Binance', 'USDT', 1, 1, 44),
('Crypto', 'ETC/USDT', 'Ethereum Classic', 'Binance', 'USDT', 1, 1, 43),
('Crypto', 'THETA/USDT', 'Theta Network', 'Binance', 'USDT', 1, 1, 42),
('Crypto', 'EOS/USDT', 'EOS', 'Binance', 'USDT', 1, 1, 41),
('Crypto', 'XLM/USDT', 'Stellar', 'Binance', 'USDT', 1, 1, 40),
('Crypto', 'GALA/USDT', 'Gala', 'Binance', 'USDT', 1, 1, 39),
('Crypto', 'IMX/USDT', 'Immutable X', 'Binance', 'USDT', 1, 1, 38),
('Crypto', 'CFX/USDT', 'Conflux', 'Binance', 'USDT', 1, 1, 37),
('Crypto', 'JASMY/USDT', 'JasmyCoin', 'Binance', 'USDT', 1, 1, 36),
('Crypto', 'CHZ/USDT', 'Chiliz', 'Binance', 'USDT', 1, 1, 35),
('Crypto', 'GMT/USDT', 'STEPN', 'Binance', 'USDT', 1, 1, 34),
('Crypto', 'CAKE/USDT', 'PancakeSwap', 'Binance', 'USDT', 1, 1, 33),
('Crypto', '1INCH/USDT', '1inch', 'Binance', 'USDT', 1, 1, 32),
('Crypto', 'ENS/USDT', 'Ethereum Name Service', 'Binance', 'USDT', 1, 1, 31),
('Crypto', 'BLUR/USDT', 'Blur', 'Binance', 'USDT', 1, 1, 30),
-- Forex
('Forex', 'XAUUSD', 'Gold/USD', 'Forex', 'USD', 1, 1, 100),
('Forex', 'XAGUSD', 'Silver/USD', 'Forex', 'USD', 1, 1, 99),
('Forex', 'EURUSD', 'Euro/US Dollar', 'Forex', 'USD', 1, 1, 98),
('Forex', 'GBPUSD', 'British Pound/US Dollar', 'Forex', 'USD', 1, 1, 97),
('Forex', 'USDJPY', 'US Dollar/Japanese Yen', 'Forex', 'USD', 1, 1, 96),
('Forex', 'AUDUSD', 'Australian Dollar/US Dollar', 'Forex', 'USD', 1, 1, 95),
('Forex', 'USDCAD', 'US Dollar/Canadian Dollar', 'Forex', 'USD', 1, 1, 94),
('Forex', 'NZDUSD', 'New Zealand Dollar/US Dollar', 'Forex', 'USD', 1, 1, 93),
('Forex', 'USDCHF', 'US Dollar/Swiss Franc', 'Forex', 'EUR', 1, 1, 92),
('Forex', 'EURJPY', 'Euro/Japanese Yen', 'Forex', 'EUR', 1, 1, 91),
-- Futures
('Futures', 'CL', 'WTI Crude Oil', 'NYMEX', 'USD', 1, 1, 100),
('Futures', 'GC', 'Gold', 'COMEX', 'USD', 1, 1, 99),
('Futures', 'SI', 'Silver', 'COMEX', 'USD', 1, 1, 98),
('Futures', 'NG', 'Natural Gas', 'NYMEX', 'USD', 1, 1, 97),
('Futures', 'HG', 'Copper', 'COMEX', 'USD', 1, 1, 96),
('Futures', 'ZC', 'Corn', 'CBOT', 'USD', 1, 1, 95),
('Futures', 'ZS', 'Soybeans', 'CBOT', 'USD', 1, 1, 94),
('Futures', 'ZW', 'Wheat', 'CBOT', 'USD', 1, 1, 93),
('Futures', 'ES', 'S&P 500 E-mini', 'CME', 'USD', 1, 1, 92),
('Futures', 'NQ', 'NASDAQ 100 E-mini', 'CME', 'USD', 1, 1, 91),
-- A股 (CNStock)
('CNStock', '600519', '贵州茅台', 'SSE', 'CNY', 1, 1, 100),
('CNStock', '600036', '招商银行', 'SSE', 'CNY', 1, 1, 99),
('CNStock', '601318', '中国平安', 'SSE', 'CNY', 1, 1, 98),
('CNStock', '600900', '长江电力', 'SSE', 'CNY', 1, 1, 97),
('CNStock', '601899', '紫金矿业', 'SSE', 'CNY', 1, 1, 96),
('CNStock', '000858', '五粮液', 'SZSE', 'CNY', 1, 1, 95),
('CNStock', '000333', '美的集团', 'SZSE', 'CNY', 1, 1, 94),
('CNStock', '002594', '比亚迪', 'SZSE', 'CNY', 1, 1, 93),
('CNStock', '300750', '宁德时代', 'SZSE', 'CNY', 1, 1, 92),
('CNStock', '000001', '平安银行', 'SZSE', 'CNY', 1, 1, 91),
-- 港股/H股 (HKStock)
('HKStock', '00700', '腾讯控股', 'HKEX', 'HKD', 1, 1, 100),
('HKStock', '09988', '阿里巴巴-W', 'HKEX', 'HKD', 1, 1, 99),
('HKStock', '03690', '美团-W', 'HKEX', 'HKD', 1, 1, 98),
('HKStock', '01810', '小米集团-W', 'HKEX', 'HKD', 1, 1, 97),
('HKStock', '00939', '建设银行', 'HKEX', 'HKD', 1, 1, 96),
('HKStock', '01299', '友邦保险', 'HKEX', 'HKD', 1, 1, 95),
('HKStock', '02318', '中国平安', 'HKEX', 'HKD', 1, 1, 94),
('HKStock', '00388', '香港交易所', 'HKEX', 'HKD', 1, 1, 93),
('HKStock', '00883', '中国海洋石油', 'HKEX', 'HKD', 1, 1, 92),
('HKStock', '01398', '工商银行', 'HKEX', 'HKD', 1, 1, 91)
ON CONFLICT (market, symbol) DO NOTHING;

-- =============================================================================
-- 19.5. Analysis Memory (Fast AI Analysis Memory System)
-- =============================================================================
-- Stores AI analysis results for history, feedback, and learning.

CREATE TABLE IF NOT EXISTS analy_analysis_memory (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    market VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    decision VARCHAR(10) NOT NULL,
    confidence INTEGER DEFAULT 50,
    price_at_analysis NUMERIC(24, 8),
    summary TEXT,
    reasons JSONB,
    scores JSONB,
    indicators_snapshot JSONB,
    raw_result JSONB,
    consensus_score NUMERIC(24, 8),
    consensus_abs NUMERIC(24, 8),
    agreement_ratio NUMERIC(10, 6),
    quality_multiplier NUMERIC(10, 6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    validated_at TIMESTAMP WITH TIME ZONE,
    actual_outcome VARCHAR(20),
    actual_return_pct NUMERIC(10, 4),
    was_correct BOOLEAN,
    user_feedback VARCHAR(20),
    feedback_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_analysis_memory_symbol ON analy_analysis_memory(market, symbol);
CREATE INDEX IF NOT EXISTS idx_analysis_memory_created ON analy_analysis_memory(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_memory_validated ON analy_analysis_memory(validated_at) WHERE validated_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_analysis_memory_user ON analy_analysis_memory(user_id);

-- =============================================================================
-- 20. Indicator Community Tables
-- =============================================================================

-- Indicator Purchases (购买记录)
CREATE TABLE IF NOT EXISTS ind_indicator_purchases (
    id SERIAL PRIMARY KEY,
    indicator_id INTEGER NOT NULL REFERENCES ind_indicator_codes(id) ON DELETE CASCADE,
    buyer_id INTEGER NOT NULL REFERENCES sys_users(id) ON DELETE CASCADE,
    seller_id INTEGER NOT NULL REFERENCES sys_users(id),
    price NUMERIC(10, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(indicator_id, buyer_id)
);

CREATE INDEX IF NOT EXISTS idx_purchases_indicator ON ind_indicator_purchases(indicator_id);
CREATE INDEX IF NOT EXISTS idx_purchases_buyer ON ind_indicator_purchases(buyer_id);
CREATE INDEX IF NOT EXISTS idx_purchases_seller ON ind_indicator_purchases(seller_id);

-- Indicator Comments (评论)
CREATE TABLE IF NOT EXISTS ind_indicator_comments (
    id SERIAL PRIMARY KEY,
    indicator_id INTEGER NOT NULL REFERENCES ind_indicator_codes(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES sys_users(id) ON DELETE CASCADE,
    rating INTEGER DEFAULT 5 CHECK (rating >= 1 AND rating <= 5),
    content TEXT DEFAULT '',
    parent_id INTEGER REFERENCES ind_indicator_comments(id) ON DELETE CASCADE,
    is_deleted INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_comments_indicator ON ind_indicator_comments(indicator_id);
CREATE INDEX IF NOT EXISTS idx_comments_user ON ind_indicator_comments(user_id);

-- =============================================================================
-- 22. Quick Trades
CREATE TABLE IF NOT EXISTS trade_quick_trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES sys_users(id) ON DELETE CASCADE,
    credential_id INTEGER DEFAULT 0,
    exchange_id VARCHAR(40) NOT NULL DEFAULT '',
    symbol VARCHAR(60) NOT NULL DEFAULT '',
    side VARCHAR(10) NOT NULL DEFAULT '',
    order_type VARCHAR(20) NOT NULL DEFAULT 'market',
    amount NUMERIC(24, 8) DEFAULT 0,
    price NUMERIC(24, 8) DEFAULT 0,
    leverage INTEGER DEFAULT 1,
    market_type VARCHAR(20) DEFAULT 'swap',
    tp_price NUMERIC(24, 8) DEFAULT 0,
    sl_price NUMERIC(24, 8) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'submitted',
    exchange_order_id VARCHAR(120) DEFAULT '',
    filled_amount NUMERIC(24, 8) DEFAULT 0,
    avg_fill_price NUMERIC(24, 8) DEFAULT 0,
    error_msg TEXT DEFAULT '',
    source VARCHAR(40) DEFAULT 'manual',
    raw_result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quick_trades_user    ON trade_quick_trades(user_id);
CREATE INDEX IF NOT EXISTS idx_quick_trades_created ON trade_quick_trades(created_at DESC);

-- =============================================================================
-- 23. Polymarket Prediction Markets

CREATE TABLE IF NOT EXISTS trade_polymarket_users (
    id SERIAL PRIMARY KEY,
    address VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    win_rate NUMERIC(10, 4),
    volume NUMERIC(24, 8),
    payload_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trade_polymarket_markets (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(255) UNIQUE NOT NULL,
    question TEXT NOT NULL,
    current_probability NUMERIC(10, 4),
    end_date_iso VARCHAR(64),
    active BOOLEAN DEFAULT true,
    category VARCHAR(100),
    last_synced_at TIMESTAMP WITH TIME ZONE,
    payload_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trade_polymarket_ai_analysis (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(255) NOT NULL,
    user_id INTEGER,
    ai_predicted_probability NUMERIC(10, 4),
    market_probability NUMERIC(10, 4),
    divergence NUMERIC(10, 4),
    recommendation VARCHAR(32),
    confidence_score NUMERIC(10, 4),
    opportunity_score NUMERIC(10, 4),
    reasoning TEXT,
    key_factors JSONB,
    related_assets TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trade_polymarket_opportunities (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(255) NOT NULL,
    asset VARCHAR(100) NOT NULL,
    market VARCHAR(50),
    signal VARCHAR(32),
    confidence NUMERIC(10, 4),
    reasoning TEXT,
    payload_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trade_sync_jobs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL DEFAULT 'Data Sync',
    source_type VARCHAR(50) NOT NULL DEFAULT 'polymarket',
    executor_type VARCHAR(50) NOT NULL DEFAULT 'polymarket',
    interval_minutes INTEGER NOT NULL DEFAULT 30,
    enabled BOOLEAN DEFAULT true,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    last_status VARCHAR(32),
    last_error TEXT,
    config_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trade_sync_runs (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL,
    run_type VARCHAR(32) NOT NULL DEFAULT 'incremental',
    status VARCHAR(32) NOT NULL DEFAULT 'running',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    finished_at TIMESTAMP WITH TIME ZONE,
    items_fetched INTEGER DEFAULT 0,
    items_saved INTEGER DEFAULT 0,
    items_failed INTEGER DEFAULT 0,
    error_message TEXT,
    detail_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_polymarket_markets_market_id ON trade_polymarket_markets(market_id);
CREATE INDEX IF NOT EXISTS idx_polymarket_markets_active ON trade_polymarket_markets(active);
CREATE INDEX IF NOT EXISTS idx_polymarket_ai_analysis_market_id ON trade_polymarket_ai_analysis(market_id);
CREATE INDEX IF NOT EXISTS idx_polymarket_opportunities_market_id ON trade_polymarket_opportunities(market_id);
CREATE INDEX IF NOT EXISTS idx_sync_runs_job_id ON trade_sync_runs(job_id);
CREATE INDEX IF NOT EXISTS idx_sync_runs_status ON trade_sync_runs(status);

-- =============================================================================
-- Completion Notice
-- =============================================================================
DO $$
BEGIN
    RAISE NOTICE 'QuantDinger PostgreSQL schema initialized successfully!';
END $$;


-- =============================================================================
-- TABLES FROM 002_add_collection_tables
-- =============================================================================
CREATE TABLE IF NOT EXISTS sys_collection_records (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50),
    data_type VARCHAR(50),
    market VARCHAR(50),
    symbol VARCHAR(100),
    content_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_collection_content_hash UNIQUE (content_hash)
);
CREATE INDEX IF NOT EXISTS idx_collection_lookup ON sys_collection_records(source, data_type, market, symbol);


-- =============================================================================
-- TABLES FROM 003_add_graph_meta_tables
-- =============================================================================
CREATE TABLE IF NOT EXISTS gra_graph_episodes (
    id SERIAL PRIMARY KEY,
    episode_type VARCHAR(50) NOT NULL,
    market_domain VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    source VARCHAR(100) NOT NULL,
    source_ref VARCHAR(255),
    dedup_key VARCHAR(128),
    importance_score NUMERIC(6, 4) DEFAULT 0.5,
    event_time TIMESTAMP WITH TIME ZONE,
    observed_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(30) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_graph_episode_dedup_key UNIQUE (dedup_key)
);

CREATE TABLE IF NOT EXISTS gra_graph_jobs (
    id SERIAL PRIMARY KEY,
    episode_id INTEGER,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(30) DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS gra_graph_entity_refs (
    id SERIAL PRIMARY KEY,
    entity_uid VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    source_table VARCHAR(100) NOT NULL,
    source_pk VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_graph_entity_ref UNIQUE (entity_type, source_table, source_pk)
);

CREATE TABLE IF NOT EXISTS gra_graph_relation_snapshots (
    id SERIAL PRIMARY KEY,
    relation_type VARCHAR(100) NOT NULL,
    from_uid VARCHAR(255) NOT NULL,
    to_uid VARCHAR(255) NOT NULL,
    source_ref VARCHAR(255),
    confidence NUMERIC(6, 4),
    t_valid TIMESTAMP WITH TIME ZONE,
    t_invalid TIMESTAMP WITH TIME ZONE,
    payload_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_graph_relation_lookup ON gra_graph_relation_snapshots(relation_type, from_uid, to_uid);


-- =============================================================================
-- TABLES FROM 004_add_graph_feature_tables
-- =============================================================================
CREATE TABLE IF NOT EXISTS gra_graph_feature_daily (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    market VARCHAR(50) NOT NULL,
    symbol VARCHAR(100) NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    feature_value NUMERIC(24, 8) NOT NULL,
    source VARCHAR(50) DEFAULT 'graph',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_graph_feature_daily UNIQUE (trade_date, market, symbol, feature_name)
);
CREATE INDEX IF NOT EXISTS idx_graph_feature_lookup ON gra_graph_feature_daily(market, symbol, trade_date);

CREATE TABLE IF NOT EXISTS gra_company_narrative_features (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    narrative_name VARCHAR(100) NOT NULL,
    narrative_score NUMERIC(10, 4) NOT NULL,
    source VARCHAR(50) DEFAULT 'graph',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_company_narrative_feature UNIQUE (trade_date, ticker, narrative_name)
);
CREATE INDEX IF NOT EXISTS idx_company_narrative_lookup ON gra_company_narrative_features(ticker, trade_date);

CREATE TABLE IF NOT EXISTS gra_crypto_narrative_features (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    narrative_name VARCHAR(100) NOT NULL,
    narrative_score NUMERIC(10, 4) NOT NULL,
    source VARCHAR(50) DEFAULT 'graph',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_crypto_narrative_feature UNIQUE (trade_date, symbol, narrative_name)
);
CREATE INDEX IF NOT EXISTS idx_crypto_narrative_lookup ON gra_crypto_narrative_features(symbol, trade_date);

CREATE TABLE IF NOT EXISTS gra_polymarket_market_features (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    market_id VARCHAR(255) NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    feature_value NUMERIC(24, 8) NOT NULL,
    source VARCHAR(50) DEFAULT 'graph',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_polymarket_market_feature UNIQUE (trade_date, market_id, feature_name)
);
CREATE INDEX IF NOT EXISTS idx_polymarket_feature_lookup ON gra_polymarket_market_features(market_id, trade_date);


-- =============================================================================
-- TABLES FROM 005_add_dify_workflow_tables
-- =============================================================================
CREATE TABLE IF NOT EXISTS data_dify_workflows (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT DEFAULT '',
    workflow_type VARCHAR(50) NOT NULL DEFAULT 'chat',
    endpoint VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) NOT NULL,
    input_schema JSONB NOT NULL DEFAULT '{}',
    output_schema JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT true,
    max_retries INTEGER NOT NULL DEFAULT 3,
    timeout_seconds INTEGER NOT NULL DEFAULT 120,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS data_dify_workflow_logs (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER NOT NULL REFERENCES data_dify_workflows(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES sys_users(id) ON DELETE SET NULL,
    input_data JSONB,
    output_data JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    call_mode VARCHAR(10) NOT NULL DEFAULT 'batch',
    tokens_used INTEGER NOT NULL DEFAULT 0,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_dify_logs_workflow_id ON data_dify_workflow_logs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_dify_logs_user_id ON data_dify_workflow_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_dify_logs_status ON data_dify_workflow_logs(status);


-- =============================================================================
-- 24. Data Source Metadata Tables

-- data_data_source_configs
CREATE TABLE IF NOT EXISTS data_data_source_configs (
    id SERIAL PRIMARY KEY,
    source_code VARCHAR(80) UNIQUE NOT NULL,
    source_name VARCHAR(150) NOT NULL,
    layer VARCHAR(30) NOT NULL DEFAULT 'data_source',
    market_categories TEXT[],
    enabled BOOLEAN NOT NULL DEFAULT true,
    load_balance_strategy VARCHAR(30) NOT NULL DEFAULT 'round_robin',
    config_json JSONB,
    dependencies TEXT[],
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ds_config_source_code ON data_data_source_configs(source_code);
CREATE INDEX IF NOT EXISTS idx_ds_config_layer ON data_data_source_configs(layer);

-- data_data_source_datasets
CREATE TABLE IF NOT EXISTS data_data_source_datasets (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES data_data_source_configs(id) ON DELETE CASCADE,
    dataset_code VARCHAR(80) UNIQUE NOT NULL,
    dataset_name VARCHAR(150) NOT NULL,
    description TEXT,
    function_name VARCHAR(100),
    return_type VARCHAR(30) NOT NULL DEFAULT 'list[dict]',
    fields_schema JSONB,
    sample_output JSONB,
    coverage_text TEXT,
    source_file_ref VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ds_dataset_source_id ON data_data_source_datasets(source_id);
CREATE INDEX IF NOT EXISTS idx_ds_dataset_code ON data_data_source_datasets(dataset_code);

-- data_api_keys
CREATE TABLE IF NOT EXISTS data_api_keys (
    id SERIAL PRIMARY KEY,
    source_config_id INTEGER NOT NULL REFERENCES data_data_source_configs(id) ON DELETE CASCADE,
    key_type VARCHAR(20) NOT NULL DEFAULT 'public',
    user_id INTEGER REFERENCES sys_users(id) ON DELETE SET NULL,
    key_alias VARCHAR(100),
    encrypted_key_value TEXT NOT NULL,
    key_hint VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    weight INTEGER NOT NULL DEFAULT 1,
    consecutive_errors INTEGER NOT NULL DEFAULT 0,
    last_error_at TIMESTAMP WITH TIME ZONE,
    max_consecutive_errors INTEGER NOT NULL DEFAULT 5,
    daily_call_limit INTEGER NOT NULL DEFAULT 0,
    current_daily_calls INTEGER NOT NULL DEFAULT 0,
    last_reset_at TIMESTAMP WITH TIME ZONE,
    total_calls INTEGER NOT NULL DEFAULT 0,
    created_by INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_api_keys_source ON data_api_keys(source_config_id, key_type, status);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON data_api_keys(user_id);

-- data_query_cache
CREATE TABLE IF NOT EXISTS data_query_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(64) UNIQUE NOT NULL,
    dataset_id INTEGER REFERENCES data_data_source_datasets(id) ON DELETE SET NULL,
    source_code VARCHAR(80) NOT NULL,
    query_params JSONB NOT NULL,
    result_data JSONB,
    result_size_bytes INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    request_count INTEGER NOT NULL DEFAULT 1,
    ttl_seconds INTEGER NOT NULL DEFAULT 300,
    expires_at TIMESTAMP WITH TIME ZONE,
    first_requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_requested_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_query_cache_key ON data_query_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_query_cache_source_status ON data_query_cache(source_code, status);

-- =============================================================================
-- 5.1. Data Source Seed Data
-- =============================================================================

INSERT INTO data_data_source_configs (source_code, source_name, layer, market_categories, enabled, load_balance_strategy, config_json, notes) VALUES
('crypto_ccxt', '加密货币数据 (CCXT)', 'data_provider', '{"Crypto"}', true, 'round_robin', '{"default_exchange": "binance", "timeout_sec": 10, "enable_rate_limit": true, "proxy": ""}', '通过 CCXT 获取加密货币K线和报价'),
('us_stock_finnhub', '美股数据 (Finnhub)', 'data_provider', '{"USStock"}', true, 'round_robin', '{"base_url": "https://finnhub.io/api/v1", "timeout_sec": 10, "rate_limit_per_min": 60}', 'Finnhub 美股实时报价和基本面数据'),
('us_stock_tiingo', '美股数据 (Tiingo)', 'data_provider', '{"USStock"}', true, 'round_robin', '{"base_url": "https://api.tiingo.com/tiingo", "timeout_sec": 10}', 'Tiingo 美股历史数据和报价'),
('forex_twelve_data', '外汇数据 (Twelve Data)', 'data_provider', '{"Forex"}', true, 'round_robin', '{"base_url": "https://api.twelvedata.com", "timeout_sec": 20}', 'Twelve Data 外汇K线和报价'),
('forex_tiingo', '外汇数据 (Tiingo)', 'data_provider', '{"Forex"}', true, 'round_robin', '{"base_url": "https://api.tiingo.com/tiingo", "timeout_sec": 10}', 'Tiingo 外汇数据'),
('futures_twelve_data', '期货数据 (Twelve Data)', 'data_provider', '{"Futures"}', true, 'round_robin', '{"base_url": "https://api.twelvedata.com", "timeout_sec": 20}', 'Twelve Data 期货K线和报价'),
('futures_tiingo', '期货数据 (Tiingo)', 'data_provider', '{"Futures"}', true, 'round_robin', '{"base_url": "https://api.tiingo.com/tiingo", "timeout_sec": 10}', 'Tiingo 期货数据（贵金属现货）'),
('hk_stock_twelve_data', '港股数据 (Twelve Data)', 'data_provider', '{"HKStock"}', true, 'round_robin', '{"base_url": "https://api.twelvedata.com", "timeout_sec": 20}', 'Twelve Data 港股K线'),
('cn_stock_akshare', 'A股数据 (AkShare)', 'data_provider', '{"CNStock"}', true, 'round_robin', '{"timeout_sec": 30}', 'AkShare A股免费数据源')
ON CONFLICT (source_code) DO NOTHING;

-- Seed datasets for crypto_ccxt (id=1)
INSERT INTO data_data_source_datasets (source_id, dataset_code, dataset_name, description, function_name, return_type, fields_schema, sample_output, coverage_text) VALUES
(1, 'crypto_klines', '加密货币K线', '加密货币OHLCV历史K线数据', 'get_kline()', 'list[dict]', '[{"name": "time", "type": "int", "description": "Unix时间戳(秒)"}, {"name": "open", "type": "float"}, {"name": "high", "type": "float"}, {"name": "low", "type": "float"}, {"name": "close", "type": "float"}, {"name": "volume", "type": "float"}]', '[{"time": 1714003200, "open": 65000, "high": 65500, "low": 64800, "close": 65200, "volume": 1200}]', '覆盖主流币种：BTC, ETH, SOL, XRP, ADA等');

-- Seed datasets for us_stock_finnhub (id=2)
INSERT INTO data_data_source_datasets (source_id, dataset_code, dataset_name, description, function_name, return_type, fields_schema, sample_output, coverage_text) VALUES
(2, 'us_stock_quote', '美股实时报价', '美股实时价格和基本行情', 'get_ticker()', 'dict', '[{"name": "last", "type": "float", "description": "最新价"}, {"name": "change", "type": "float"}, {"name": "changePercent", "type": "float"}]', '{"last": 185.5, "change": 2.3, "changePercent": 1.25}', '美股主要上市公司');

-- Seed datasets for forex_twelve_data (id=4)
INSERT INTO data_data_source_datasets (source_id, dataset_code, dataset_name, description, function_name, return_type, fields_schema, sample_output, coverage_text) VALUES
(4, 'forex_klines', '外汇K线', '外汇货币对OHLCV历史K线', 'get_kline()', 'list[dict]', '[{"name": "time", "type": "int"}, {"name": "open", "type": "float"}, {"name": "high", "type": "float"}, {"name": "low", "type": "float"}, {"name": "close", "type": "float"}, {"name": "volume", "type": "float"}]', '[{"time": 1714003200, "open": 1.0850, "high": 1.0870, "low": 1.0840, "close": 1.0860, "volume": 50000}]', '主要货币对：EURUSD, GBPUSD, USDJPY, XAUUSD等');

-- Seed datasets for futures_twelve_data (id=6)
INSERT INTO data_data_source_datasets (source_id, dataset_code, dataset_name, description, function_name, return_type, fields_schema, sample_output, coverage_text) VALUES
(6, 'futures_klines', '期货K线', '传统期货OHLCV历史K线', 'get_kline()', 'list[dict]', '[{"name": "time", "type": "int"}, {"name": "open", "type": "float"}, {"name": "high", "type": "float"}, {"name": "low", "type": "float"}, {"name": "close", "type": "float"}, {"name": "volume", "type": "float"}]', '[{"time": 1714003200, "open": 2300, "high": 2310, "low": 2295, "close": 2305, "volume": 8000}]', '期货品种：GC, SI, CL, ES, NQ等');

-- Note: API keys should be added via the admin UI or API after setup.
-- The encrypted_key_value below is a placeholder encrypted empty string.
-- INSERT INTO data_api_keys (source_config_id, key_type, encrypted_key_value, key_hint, status) VALUES
-- (2, 'public', '<encrypted_value>', '****demo', 'active');

-- =============================================================================
-- TABLE COMMENTS (COMMENT ON)
-- =============================================================================

-- Level 0: 无外键依赖的表
COMMENT ON TABLE trade_ai_calibration IS 'AI 校准参数表 — 存储每个市场的AI信号校准参数（买卖阈值、质量保留阈值等）';
COMMENT ON COLUMN trade_ai_calibration.id IS '主键，自增序列';
COMMENT ON COLUMN trade_ai_calibration.market IS '市场类别，如 Crypto、USStock、Forex 等';
COMMENT ON COLUMN trade_ai_calibration.buy_threshold IS '买入阈值（NUMERIC(10,4)），AI信号大于此值时产生买入建议';
COMMENT ON COLUMN trade_ai_calibration.sell_threshold IS '卖出阈值（NUMERIC(10,4)），AI信号小于此值时产生卖出建议';
COMMENT ON COLUMN trade_ai_calibration.min_consensus_abs_override IS '最小共识绝对值覆盖，当共识绝对值大于此值时强制采用';
COMMENT ON COLUMN trade_ai_calibration.quality_hold_threshold IS '质量保留阈值（NUMERIC(10,4)），AI分析质量分数低于此值时暂停交易';
COMMENT ON COLUMN trade_ai_calibration.validated_at IS '参数验证时间，记录参数通过有效性检验的时间';
COMMENT ON COLUMN trade_ai_calibration.created_at IS '记录创建时间';

COMMENT ON TABLE trade_analysis_results IS 'AI 分析结果表 — 存储AI对市场品种的分析结论和置信度';
COMMENT ON COLUMN trade_analysis_results.id IS '主键，自增序列';
COMMENT ON COLUMN trade_analysis_results.user_id IS '用户ID（INTEGER），关联 sys_users(id)';
COMMENT ON COLUMN trade_analysis_results.market IS '市场类别，如 Crypto、USStock 等';
COMMENT ON COLUMN trade_analysis_results.symbol IS '交易品种代码，如 BTC/USDT、AAPL';
COMMENT ON COLUMN trade_analysis_results.decision IS '决策结论，值为 buy/sell/hold 之一';
COMMENT ON COLUMN trade_analysis_results.confidence IS '置信度评分（NUMERIC(10,4)），0-10000';
COMMENT ON COLUMN trade_analysis_results.summary IS 'AI 分析摘要文本';
COMMENT ON COLUMN trade_analysis_results.payload_json IS '完整分析结果的JSON序列';
COMMENT ON COLUMN trade_analysis_results.created_at IS '记录创建时间';
COMMENT ON COLUMN trade_analysis_results.updated_at IS '记录更新时间';

COMMENT ON TABLE sys_llm_provider IS 'LLM 服务提供商表 — 存储支持 OpenRouter/OpenAI/Azure 等大模型服务的配置信息';
COMMENT ON COLUMN sys_llm_provider.id IS '主键，自增序列';
COMMENT ON COLUMN sys_llm_provider.name IS '提供商名称，如 OpenRouter、OpenAI、Azure';
COMMENT ON COLUMN sys_llm_provider.code IS '唯一编码标识，用于系统内部引用';
COMMENT ON COLUMN sys_llm_provider.base_url IS 'API 基础 URL，OpenAI 兼容端点地址';
COMMENT ON COLUMN sys_llm_provider.api_type IS 'API 类型，默认 openai，支持 custom/azure 等';
COMMENT ON COLUMN sys_llm_provider.status IS '状态标识，1=启用，0=禁用';
COMMENT ON COLUMN sys_llm_provider.config IS '扩展配置参数（JSONB），如组织ID、API版本等';
COMMENT ON COLUMN sys_llm_provider.created_at IS '记录创建时间';
COMMENT ON COLUMN sys_llm_provider.updated_at IS '记录更新时间';

COMMENT ON TABLE trade_market_prices IS '市场行情快照表 — 存储各市场交易品种的实时价格快照（轻量级）';
COMMENT ON COLUMN trade_market_prices.id IS '主键，自增序列';
COMMENT ON COLUMN trade_market_prices.market IS '市场类别，如 Crypto、USStock、Forex';
COMMENT ON COLUMN trade_market_prices.symbol IS '交易品种代码，如 BTC/USDT、AAPL';
COMMENT ON COLUMN trade_market_prices.price IS '当前最新价格（NUMERIC(24,8)）';
COMMENT ON COLUMN trade_market_prices.change_percent IS '涨跌幅百分比（NUMERIC(10,4)）';
COMMENT ON COLUMN trade_market_prices.snapshot_time IS '快照采集时间';
COMMENT ON COLUMN trade_market_prices.created_at IS '记录创建时间';
COMMENT ON COLUMN trade_market_prices.updated_at IS '记录更新时间';

COMMENT ON TABLE trade_market_klines IS 'K线数据表 — 存储各市场交易品种的OHLCV历史K线数据';
COMMENT ON COLUMN trade_market_klines.id IS '主键，自增序列';
COMMENT ON COLUMN trade_market_klines.market IS '市场类别，如 Crypto、USStock';
COMMENT ON COLUMN trade_market_klines.symbol IS '交易品种代码';
COMMENT ON COLUMN trade_market_klines.timeframe IS 'K线周期，如 1m、5m、1h、1d';
COMMENT ON COLUMN trade_market_klines.open_price IS '开盘价（NUMERIC(24,8)）';
COMMENT ON COLUMN trade_market_klines.high_price IS '最高价（NUMERIC(24,8)）';
COMMENT ON COLUMN trade_market_klines.low_price IS '最低价（NUMERIC(24,8)）';
COMMENT ON COLUMN trade_market_klines.close_price IS '收盘价（NUMERIC(24,8)）';
COMMENT ON COLUMN trade_market_klines.volume IS '成交量（NUMERIC(24,8)）';
COMMENT ON COLUMN trade_market_klines.kline_time IS 'K线时间戳';
COMMENT ON COLUMN trade_market_klines.payload_json IS '附加扩展数据（JSON格式）';
COMMENT ON COLUMN trade_market_klines.created_at IS '记录创建时间';
COMMENT ON COLUMN trade_market_klines.updated_at IS '记录更新时间';

COMMENT ON TABLE trade_strategies IS '策略元数据表 — 存储非交易的策略定义信息（共享策略模板）';
COMMENT ON COLUMN trade_strategies.id IS '主键，自增序列';
COMMENT ON COLUMN trade_strategies.user_id IS '所属用户ID（INTEGER），NOT NULL';
COMMENT ON COLUMN trade_strategies.name IS '策略名称';
COMMENT ON COLUMN trade_strategies.description IS '策略描述文本';
COMMENT ON COLUMN trade_strategies.strategy_type IS '策略类型，如 IndicatorStrategy、MLStrategy';
COMMENT ON COLUMN trade_strategies.status IS '策略状态，默认 draft（草稿）';
COMMENT ON COLUMN trade_strategies.is_public IS '是否公开，默认 FALSE';
COMMENT ON COLUMN trade_strategies.created_at IS '记录创建时间';
COMMENT ON COLUMN trade_strategies.updated_at IS '记录更新时间';

-- Level 1: LLM表（依赖 sys_llm_provider）
COMMENT ON TABLE sys_llm_api_key IS 'LLM API密钥表 — 存储各LLM服务提供商的加密API密钥及负载均衡配置';
COMMENT ON COLUMN sys_llm_api_key.id IS '主键，自增序列';
COMMENT ON COLUMN sys_llm_api_key.provider_id IS '关联的LLM服务商ID，外键→ sys_llm_provider(id)，级联删除';
COMMENT ON COLUMN sys_llm_api_key.name IS '密钥名称标识';
COMMENT ON COLUMN sys_llm_api_key.api_key_enc IS 'AES-256-GCM加密后的API密钥明文';
COMMENT ON COLUMN sys_llm_api_key.status IS '密钥状态，1=启用，0=禁用';
COMMENT ON COLUMN sys_llm_api_key.weight IS '负载均衡权重，数值越高被调用概率越大';
COMMENT ON COLUMN sys_llm_api_key.owner_id IS '密钥所有者用户ID（BIGINT），0表示公共密钥';
COMMENT ON COLUMN sys_llm_api_key.is_public IS '是否公共密钥，1=公共，0=私有';
COMMENT ON COLUMN sys_llm_api_key.fail_count IS '连续调用失败次数，达到阈值后自动禁用';
COMMENT ON COLUMN sys_llm_api_key.last_used_at IS '最近一次使用时间';
COMMENT ON COLUMN sys_llm_api_key.metrics IS '使用指标统计（JSONB），如总调用次数、Token消耗等';
COMMENT ON COLUMN sys_llm_api_key.created_at IS '记录创建时间';
COMMENT ON COLUMN sys_llm_api_key.updated_at IS '记录更新时间';

COMMENT ON TABLE sys_llm_model IS 'LLM 模型配置表 — 存储各服务商支持的模型列表及其调用策略';
COMMENT ON COLUMN sys_llm_model.id IS '主键，自增序列';
COMMENT ON COLUMN sys_llm_model.provider_id IS '关联的服务商ID，外键→ sys_llm_provider(id)，级联删除';
COMMENT ON COLUMN sys_llm_model.model_name IS '模型名称，如 gpt-4o、claude-3-opus';
COMMENT ON COLUMN sys_llm_model.display_name IS '界面显示名称';
COMMENT ON COLUMN sys_llm_model.lb_strategy IS '负载均衡策略，默认 weighted_round_robin';
COMMENT ON COLUMN sys_llm_model.retries IS '调用失败重试次数，默认3次';
COMMENT ON COLUMN sys_llm_model.timeout IS '超时秒数，默认60秒';
COMMENT ON COLUMN sys_llm_model.status IS '模型状态，1=启用，0=禁用';
COMMENT ON COLUMN sys_llm_model.created_at IS '记录创建时间';
COMMENT ON COLUMN sys_llm_model.updated_at IS '记录更新时间';

COMMENT ON TABLE sys_llm_call_log IS 'LLM 调用日志表 — 记录每次LLM API调用的Token消耗、延迟和状态（大字段量表）';
COMMENT ON COLUMN sys_llm_call_log.id IS '主键，使用BIGSERIAL支持大数据量';
COMMENT ON COLUMN sys_llm_call_log.api_key_id IS '使用的API密钥ID，外键→ sys_llm_api_key(id)，级联删除';
COMMENT ON COLUMN sys_llm_call_log.model_id IS '调用的模型ID，外键→ sys_llm_model(id)，级联删除';
COMMENT ON COLUMN sys_llm_call_log.user_id IS '发起调用的用户ID（BIGINT）';
COMMENT ON COLUMN sys_llm_call_log.prompt_tokens IS '输入提示词Token数量';
COMMENT ON COLUMN sys_llm_call_log.completion_tokens IS '输出回复Token数量';
COMMENT ON COLUMN sys_llm_call_log.total_tokens IS '总Token数量（prompt + completion）';
COMMENT ON COLUMN sys_llm_call_log.latency_ms IS '调用延迟，单位毫秒';
COMMENT ON COLUMN sys_llm_call_log.status_code IS 'HTTP响应状态码';
COMMENT ON COLUMN sys_llm_call_log.error_msg IS '错误信息文本（调用失败时记录）';
COMMENT ON COLUMN sys_llm_call_log.created_at IS '调用发生时间';

-- Level 2: 用户认证相关表
COMMENT ON TABLE sys_users IS '用户主表 — 存储用户账户信息、VIP状态、积分余额等核心用户数据';
COMMENT ON COLUMN sys_users.id IS '主键，自增序列';
COMMENT ON COLUMN sys_users.username IS '用户名，UNIQUE NOT NULL';
COMMENT ON COLUMN sys_users.password_hash IS '密码哈希值（bcrypt），NOT NULL';
COMMENT ON COLUMN sys_users.email IS '邮箱地址，UNIQUE，可为空';
COMMENT ON COLUMN sys_users.nickname IS '用户昵称';
COMMENT ON COLUMN sys_users.avatar IS '头像URL路径，默认 /avatar2.jpg';
COMMENT ON COLUMN sys_users.phone IS '手机号';
COMMENT ON COLUMN sys_users.bio IS '个人简介文本';
COMMENT ON COLUMN sys_users.status IS '账户状态，默认 active（活跃），可能的值：active/suspended/banned';
COMMENT ON COLUMN sys_users.role IS '用户角色，默认 user，可能的值：admin/user/developer';
COMMENT ON COLUMN sys_users.credits IS '积分余额（NUMERIC(20,2)），默认0';
COMMENT ON COLUMN sys_users.vip_expires_at IS 'VIP到期时间，NULL表示非VIP或已过期';
COMMENT ON COLUMN sys_users.vip_plan IS 'VIP套餐类型，如 monthly/yearly/lifetime';
COMMENT ON COLUMN sys_users.vip_is_lifetime IS '是否永久VIP会员，默认 FALSE';
COMMENT ON COLUMN sys_users.vip_monthly_credits_last_grant IS '上次发放月度积分的时间（用于判断是否应发放新月份积分）';
COMMENT ON COLUMN sys_users.email_verified IS '邮箱是否已验证（旧字段，等效于is_email_verified）';
COMMENT ON COLUMN sys_users.is_email_verified IS '邮箱是否已验证，默认 FALSE';
COMMENT ON COLUMN sys_users.is_phone_verified IS '手机是否已验证，默认 FALSE';
COMMENT ON COLUMN sys_users.referred_by IS '邀请人用户ID，关联 sys_users(id)';
COMMENT ON COLUMN sys_users.notification_settings IS '通知设置JSON配置（邮件/短信/Telegram等渠道偏好）';
COMMENT ON COLUMN sys_users.chart_templates IS '图表模板配置JSON';
COMMENT ON COLUMN sys_users.timezone IS '用户IANA时区字符串，如 Asia/Shanghai、America/New_York';
COMMENT ON COLUMN sys_users.token_version IS 'Token版本号，用于JWT刷新令牌的版本控制';
COMMENT ON COLUMN sys_users.last_login_at IS '最后登录时间';
COMMENT ON COLUMN sys_users.created_at IS '账户创建时间';
COMMENT ON COLUMN sys_users.updated_at IS '记录更新时间';

COMMENT ON TABLE sys_oauth_states IS 'OAuth CSRF状态表 — 存储OAuth授权流程中的CSRF状态令牌，支持多Worker/多实例共享';
COMMENT ON COLUMN sys_oauth_states.state IS 'CSRF状态令牌（PRIMARY KEY），128位随机字符串';
COMMENT ON COLUMN sys_oauth_states.provider IS 'OAuth提供商，如 google、github';
COMMENT ON COLUMN sys_oauth_states.redirect IS '授权完成后的重定向目标URL';
COMMENT ON COLUMN sys_oauth_states.created_at IS '状态令牌创建时间';
COMMENT ON COLUMN sys_oauth_states.expires_at IS '状态令牌过期时间，过期后需重新授权';

COMMENT ON TABLE sys_login_attempts IS '登录尝试记录表 — 记录每次登录行为，用于防暴力破解和安全审计';
COMMENT ON COLUMN sys_login_attempts.id IS '主键，自增序列';
COMMENT ON COLUMN sys_login_attempts.identifier IS '登录标识（IP或用户名），NOT NULL';
COMMENT ON COLUMN sys_login_attempts.identifier_type IS '标识类型，ip=IP地址，account=用户名/邮箱';
COMMENT ON COLUMN sys_login_attempts.success IS '是否成功，NOT NULL DEFAULT FALSE';
COMMENT ON COLUMN sys_login_attempts.ip_address IS '登录来源IP地址（VARCHAR(64)）';
COMMENT ON COLUMN sys_login_attempts.user_agent IS '浏览器/客户端User-Agent字符串';
COMMENT ON COLUMN sys_login_attempts.attempt_time IS '登录尝试时间';
COMMENT ON COLUMN sys_login_attempts.created_at IS '记录创建时间';
COMMENT ON COLUMN sys_login_attempts.updated_at IS '记录更新时间';

COMMENT ON TABLE sys_security_logs IS '安全审计日志表 — 记录所有安全相关操作（登录/登出/密码修改等）';
COMMENT ON COLUMN sys_security_logs.id IS '主键，自增序列';
COMMENT ON COLUMN sys_security_logs.user_id IS '操作用户ID，关联 sys_users(id)';
COMMENT ON COLUMN sys_security_logs.action IS '操作类型，如 login/logout/password_change/api_key_created';
COMMENT ON COLUMN sys_security_logs.ip_address IS '操作来源IP地址';
COMMENT ON COLUMN sys_security_logs.user_agent IS '操作端User-Agent';
COMMENT ON COLUMN sys_security_logs.details_json IS '操作详细信息的JSON序列化';
COMMENT ON COLUMN sys_security_logs.created_at IS '操作发生时间';
COMMENT ON COLUMN sys_security_logs.updated_at IS '记录更新时间';

-- Level 3: 积分/会员/验证码表（依赖 sys_users）
COMMENT ON TABLE sys_credits_log IS '积分变动日志表 — 记录用户积分的每次增删变动，支持余额回溯';
COMMENT ON COLUMN sys_credits_log.id IS '主键，自增序列';
COMMENT ON COLUMN sys_credits_log.user_id IS '关联用户ID，外键→ sys_users(id)，级联删除';
COMMENT ON COLUMN sys_credits_log.action IS '动作类型，如 consume/recharge/vip_grant/refund';
COMMENT ON COLUMN sys_credits_log.amount IS '变动金额（NUMERIC(20,2)），正数=增加，负数=扣减，NOT NULL';
COMMENT ON COLUMN sys_credits_log.balance_after IS '变动后余额（NUMERIC(20,2)），NOT NULL';
COMMENT ON COLUMN sys_credits_log.feature IS '消费功能标识，如 fast_analysis/indicator_purchase/backtest';
COMMENT ON COLUMN sys_credits_log.reference_id IS '关联业务ID，如订单号、任务ID';
COMMENT ON COLUMN sys_credits_log.remark IS '变动备注/说明文本';
COMMENT ON COLUMN sys_credits_log.operator_id IS '操作人ID（如管理员代操），NULL表示用户本人';
COMMENT ON COLUMN sys_credits_log.created_at IS '变动发生时间';

COMMENT ON TABLE sys_membership_orders IS '会员订单表 — 记录用户购买会员套餐的订单（Mock支付场景）';
COMMENT ON COLUMN sys_membership_orders.id IS '主键，自增序列';
COMMENT ON COLUMN sys_membership_orders.user_id IS '购买用户ID，外键→ sys_users(id)，级联删除';
COMMENT ON COLUMN sys_membership_orders.plan IS '套餐类型，monthly=月卡/yearly=年卡/lifetime=永久';
COMMENT ON COLUMN sys_membership_orders.price_usd IS '订单价格（USD），NUMERIC(10,2)';
COMMENT ON COLUMN sys_membership_orders.status IS '订单状态，默认 paid（已支付）';
COMMENT ON COLUMN sys_membership_orders.created_at IS '订单创建时间';
COMMENT ON COLUMN sys_membership_orders.paid_at IS '支付完成时间，NULL表示未支付';

COMMENT ON TABLE sys_usdt_orders IS 'USDT收款订单表 — 记录用户通过USDT（TRC20/ERC20）购买积分/会员的独立地址订单';
COMMENT ON COLUMN sys_usdt_orders.id IS '主键，自增序列';
COMMENT ON COLUMN sys_usdt_orders.user_id IS '下单用户ID，外键→ sys_users(id)，级联删除';
COMMENT ON COLUMN sys_usdt_orders.plan IS '购买的套餐类型';
COMMENT ON COLUMN sys_usdt_orders.chain IS '区块链网络，默认 TRC20（支持 TRC20/ERC20）';
COMMENT ON COLUMN sys_usdt_orders.amount_usdt IS '应支付的USDT金额（NUMERIC(20,6)）';
COMMENT ON COLUMN sys_usdt_orders.address_index IS 'HD钱包派生地址索引（INTEGER），每单使用独立地址便于识别';
COMMENT ON COLUMN sys_usdt_orders.address IS '收款钱包地址（基于address_index派生）';
COMMENT ON COLUMN sys_usdt_orders.status IS '订单状态：pending=待支付/paid=已支付/expired=已过期/cancelled=已取消';
COMMENT ON COLUMN sys_usdt_orders.tx_hash IS '用户转账的交易哈希（区块链TXID）';
COMMENT ON COLUMN sys_usdt_orders.paid_at IS '链上确认支付时间';
COMMENT ON COLUMN sys_usdt_orders.confirmed_at IS '平台确认到账时间';
COMMENT ON COLUMN sys_usdt_orders.expires_at IS '订单过期时间，过期后不可支付';
COMMENT ON COLUMN sys_usdt_orders.created_at IS '订单创建时间';
COMMENT ON COLUMN sys_usdt_orders.updated_at IS '记录更新时间';

COMMENT ON TABLE sys_verification_codes IS '邮箱验证码表 — 存储注册/登录/密码重置等场景的邮箱验证码';
COMMENT ON COLUMN sys_verification_codes.id IS '主键，自增序列';
COMMENT ON COLUMN sys_verification_codes.email IS '目标邮箱地址';
COMMENT ON COLUMN sys_verification_codes.code IS '验证码内容（6位数字）';
COMMENT ON COLUMN sys_verification_codes.type IS '验证码用途类型：register/login/reset_password/change_email';
COMMENT ON COLUMN sys_verification_codes.expires_at IS '验证码过期时间，NOT NULL';
COMMENT ON COLUMN sys_verification_codes.used_at IS '验证码使用时间（使用后不再可用）';
COMMENT ON COLUMN sys_verification_codes.ip_address IS '请求发送验证码的IP地址';
COMMENT ON COLUMN sys_verification_codes.attempts IS '验证尝试次数（防暴力破解）';
COMMENT ON COLUMN sys_verification_codes.last_attempt_at IS '最后验证尝试时间';
COMMENT ON COLUMN sys_verification_codes.created_at IS '记录创建时间';

COMMENT ON TABLE sys_oauth_links IS '第三方OAuth账号关联表 — 存储用户绑定的Google/GitHub等OAuth第三方登录账号';
COMMENT ON COLUMN sys_oauth_links.id IS '主键，自增序列';
COMMENT ON COLUMN sys_oauth_links.user_id IS '关联的本地用户ID，外键→ sys_users(id)，级联删除';
COMMENT ON COLUMN sys_oauth_links.provider IS 'OAuth提供商，如 google/github/wechat';
COMMENT ON COLUMN sys_oauth_links.provider_user_id IS '第三方平台用户唯一ID（UNIQUE），用于登录时匹配';
COMMENT ON COLUMN sys_oauth_links.provider_email IS '第三方返回的邮箱（可能为空）';
COMMENT ON COLUMN sys_oauth_links.provider_name IS '第三方平台用户名/昵称';
COMMENT ON COLUMN sys_oauth_links.provider_avatar IS '第三方平台头像URL';
COMMENT ON COLUMN sys_oauth_links.access_token IS '第三方OAuth Access Token（加密存储）';
COMMENT ON COLUMN sys_oauth_links.refresh_token IS '第三方OAuth Refresh Token（加密存储）';
COMMENT ON COLUMN sys_oauth_links.created_at IS '绑定时间';
COMMENT ON COLUMN sys_oauth_links.updated_at IS '记录更新时间';

COMMENT ON TABLE sys_billing_records IS '计费记录表 — 记录用户使用各功能的扣费流水（积分消费明细）';
COMMENT ON COLUMN sys_billing_records.id IS '主键，自增序列';
COMMENT ON COLUMN sys_billing_records.user_id IS '被扣费用户ID，NOT NULL';
COMMENT ON COLUMN sys_billing_records.feature IS '扣费功能名称，如 fast_analysis/backtest/indicator_purchase';
COMMENT ON COLUMN sys_billing_records.amount IS '扣费金额（NUMERIC(18,4)），NOT NULL';
COMMENT ON COLUMN sys_billing_records.balance_before IS '扣费前积分余额';
COMMENT ON COLUMN sys_billing_records.balance_after IS '扣费后积分余额';
COMMENT ON COLUMN sys_billing_records.reference_id IS '关联业务ID，如分析任务ID';
COMMENT ON COLUMN sys_billing_records.occurred_at IS '扣费发生时间';
COMMENT ON COLUMN sys_billing_records.payload_json IS '扩展业务数据的JSON';
COMMENT ON COLUMN sys_billing_records.billing_type IS '计费类型标识';
COMMENT ON COLUMN sys_billing_records.status IS '计费记录状态';
COMMENT ON COLUMN sys_billing_records.created_at IS '记录创建时间';
COMMENT ON COLUMN sys_billing_records.updated_at IS '记录更新时间';

-- Level 4: 核心交易策略表
COMMENT ON TABLE trade_strategies_trading IS '核心交易策略表 — 存储策略运行时的完整配置（信号模式/AI模式/脚本策略）';
COMMENT ON COLUMN trade_strategies_trading.id IS '主键，自增序列';
COMMENT ON COLUMN trade_strategies_trading.user_id IS '所属用户ID，外键→ sys_users(id)，NOT NULL DEFAULT 1，级联删除';
COMMENT ON COLUMN trade_strategies_trading.strategy_name IS '策略运行名称（区别于策略模板名）';
COMMENT ON COLUMN trade_strategies_trading.strategy_type IS '策略类型，默认 IndicatorStrategy，可能值：IndicatorStrategy/MLStrategy/ScriptStrategy';
COMMENT ON COLUMN trade_strategies_trading.market_category IS '市场分类，默认 Crypto，支持：Crypto/USStock/Forex/Futures/CNStock/HKStock';
COMMENT ON COLUMN trade_strategies_trading.execution_mode IS '执行模式，signal=信号模式，execution=自动执行';
COMMENT ON COLUMN trade_strategies_trading.notification_config IS '通知渠道配置JSON（邮件/Telegram/SMS/Webhook等）';
COMMENT ON COLUMN trade_strategies_trading.status IS '策略状态：stopped=停止/running=运行中/paused=暂停/error=异常';
COMMENT ON COLUMN trade_strategies_trading.symbol IS '交易品种，如 BTC/USDT';
COMMENT ON COLUMN trade_strategies_trading.timeframe IS '决策周期，如 1m/5m/15m/1h/4h/1d';
COMMENT ON COLUMN trade_strategies_trading.initial_capital IS '初始资金（NUMERIC(20,8)），默认1000';
COMMENT ON COLUMN trade_strategies_trading.leverage IS '杠杆倍数，默认1（不支持杠杆则为1）';
COMMENT ON COLUMN trade_strategies_trading.market_type IS '市场类型，swap=永续/spot=现货/futures=交割合约';
COMMENT ON COLUMN trade_strategies_trading.exchange_config IS '交易所连接配置JSON（API密钥/连接参数等）';
COMMENT ON COLUMN trade_strategies_trading.indicator_config IS '指标配置JSON（选用的指标及其参数）';
COMMENT ON COLUMN trade_strategies_trading.trading_config IS '交易执行配置JSON（仓位管理/止损止盈/下单量规则等）';
COMMENT ON COLUMN trade_strategies_trading.ai_model_config IS 'AI模型配置JSON（调用哪个模型/提示词模板等）';
COMMENT ON COLUMN trade_strategies_trading.decide_interval IS '决策间隔秒数，默认300（每5分钟决策一次）';
COMMENT ON COLUMN trade_strategies_trading.strategy_group_id IS '策略组ID，用于批量管理一组相关策略';
COMMENT ON COLUMN trade_strategies_trading.group_base_name IS '策略组基础名称前缀';
COMMENT ON COLUMN trade_strategies_trading.strategy_mode IS '策略模式，等效于execution_mode';
COMMENT ON COLUMN trade_strategies_trading.strategy_code IS '脚本策略的Python代码（ScriptStrategy模式下使用）';
COMMENT ON COLUMN trade_strategies_trading.last_rebalance_at IS '最后调仓时间';
COMMENT ON COLUMN trade_strategies_trading.strategy_id IS '关联的策略模板ID（可选）';
COMMENT ON COLUMN trade_strategies_trading.created_at IS '策略创建时间';
COMMENT ON COLUMN trade_strategies_trading.updated_at IS '记录更新时间';

COMMENT ON TABLE trade_strategy_positions IS '策略持仓表 — 记录各策略当前的持仓情况（多空/数量/入场价/盈亏）';
COMMENT ON COLUMN trade_strategy_positions.id IS '主键，自增序列';
COMMENT ON COLUMN trade_strategy_positions.user_id IS '所属用户ID，外键→ sys_users(id)，NOT NULL DEFAULT 1，级联删除';
COMMENT ON COLUMN trade_strategy_positions.strategy_id IS '关联的策略ID，外键→ trade_strategies_trading(id)，级联删除';
COMMENT ON COLUMN trade_strategy_positions.symbol IS '持仓交易品种';
COMMENT ON COLUMN trade_strategy_positions.side IS '持仓方向，long=多头/short=空头';
COMMENT ON COLUMN trade_strategy_positions.size IS '持仓数量（NUMERIC(20,8)）';
COMMENT ON COLUMN trade_strategy_positions.entry_price IS '开仓入场价格';
COMMENT ON COLUMN trade_strategy_positions.current_price IS '当前市场价格（定时更新）';
COMMENT ON COLUMN trade_strategy_positions.highest_price IS '持仓期间最高价（NUMERIC(20,8)），用于追踪最大浮盈';
COMMENT ON COLUMN trade_strategy_positions.lowest_price IS '持仓期间最低价（NUMERIC(20,8)），用于追踪最大浮亏';
COMMENT ON COLUMN trade_strategy_positions.unrealized_pnl IS '未实现盈亏（NUMERIC(20,8)），正值=浮盈，负值=浮亏';
COMMENT ON COLUMN trade_strategy_positions.pnl_percent IS '盈亏百分比（NUMERIC(10,4)），相对于入场价的涨跌幅';
COMMENT ON COLUMN trade_strategy_positions.equity IS '当前权益（持仓价值+余额）';
COMMENT ON COLUMN trade_strategy_positions.updated_at IS '最后更新时间';

COMMENT ON TABLE trade_strategy_trades IS '策略交易记录表 — 记录策略执行过的所有成交记录（已平仓）';
COMMENT ON COLUMN trade_strategy_trades.id IS '主键，自增序列';
COMMENT ON COLUMN trade_strategy_trades.user_id IS '所属用户ID，外键→ sys_users(id)，NOT NULL DEFAULT 1，级联删除';
COMMENT ON COLUMN trade_strategy_trades.strategy_id IS '关联策略ID，外键→ trade_strategies_trading(id)，级联删除';
COMMENT ON COLUMN trade_strategy_trades.symbol IS '成交品种';
COMMENT ON COLUMN trade_strategy_trades.type IS '成交类型，open=开仓/close=平仓';
COMMENT ON COLUMN trade_strategy_trades.price IS '成交价格（NUMERIC(20,8)）';
COMMENT ON COLUMN trade_strategy_trades.amount IS '成交数量（NUMERIC(20,8)）';
COMMENT ON COLUMN trade_strategy_trades.value IS '成交金额（NUMERIC(20,8)）';
COMMENT ON COLUMN trade_strategy_trades.commission IS '手续费（NUMERIC(20,8)）';
COMMENT ON COLUMN trade_strategy_trades.commission_ccy IS '手续费币种，如 USDT/BTC';
COMMENT ON COLUMN trade_strategy_trades.profit IS '该笔交易盈亏（NUMERIC(20,8)），正值=盈利，负值=亏损';
COMMENT ON COLUMN trade_strategy_trades.created_at IS '成交发生时间';

COMMENT ON TABLE trade_trade_orders IS '交易订单记录表 — 记录所有向交易所提交的订单（submitted/filled/cancelled等）';
COMMENT ON COLUMN trade_trade_orders.id IS '主键，自增序列';
COMMENT ON COLUMN trade_trade_orders.user_id IS '下单用户ID（INTEGER）';
COMMENT ON COLUMN trade_trade_orders.strategy_id IS '关联策略ID（INTEGER），可选';
COMMENT ON COLUMN trade_trade_orders.market IS '市场类别，如 Crypto/USStock，NOT NULL';
COMMENT ON COLUMN trade_trade_orders.symbol IS '交易品种，NOT NULL';
COMMENT ON COLUMN trade_trade_orders.side IS '订单方向，buy=买入/sell=卖出，NOT NULL';
COMMENT ON COLUMN trade_trade_orders.order_type IS '订单类型，market=市价单/limit=限价单/stop=止损单';
COMMENT ON COLUMN trade_trade_orders.quantity IS '委托数量（NUMERIC(24,8)）';
COMMENT ON COLUMN trade_trade_orders.price IS '委托价格（NUMERIC(24,8)），市价单可为空';
COMMENT ON COLUMN trade_trade_orders.status IS '订单状态：submitted=已提交/filled=全部成交/partial=部分成交/cancelled=已取消/rejected=被拒绝';
COMMENT ON COLUMN trade_trade_orders.submitted_at IS '订单提交时间';
COMMENT ON COLUMN trade_trade_orders.payload_json IS '交易所返回的原始订单信息JSON';
COMMENT ON COLUMN trade_trade_orders.created_at IS '记录创建时间';
COMMENT ON COLUMN trade_trade_orders.updated_at IS '记录更新时间';

COMMENT ON TABLE trade_pending_orders IS '待执行订单队列表 — 策略信号产生的待撮合订单，支持优先级调度和重试';
COMMENT ON COLUMN trade_pending_orders.id IS '主键，自增序列';
COMMENT ON COLUMN trade_pending_orders.user_id IS '所属用户ID，外键→ sys_users(id)，NOT NULL DEFAULT 1，级联删除';
COMMENT ON COLUMN trade_pending_orders.strategy_id IS '产生信号的策略ID，外键→ trade_strategies_trading(id)';
COMMENT ON COLUMN trade_pending_orders.symbol IS '交易品种，NOT NULL';
COMMENT ON COLUMN trade_pending_orders.signal_type IS '信号类型，buy/sell/close，NOT NULL';
COMMENT ON COLUMN trade_pending_orders.signal_ts IS '信号原始时间戳（BIGINT）';
COMMENT ON COLUMN trade_pending_orders.market_type IS '市场类型，默认 swap（永续合约）';
COMMENT ON COLUMN trade_pending_orders.order_type IS '下单类型，默认 market（市价），可选 limit/stop';
COMMENT ON COLUMN trade_pending_orders.amount IS '委托数量（NUMERIC(20,8)）';
COMMENT ON COLUMN trade_pending_orders.price IS '委托价格（NUMERIC(20,8)），市价单为0';
COMMENT ON COLUMN trade_pending_orders.execution_mode IS '执行模式，默认 signal';
COMMENT ON COLUMN trade_pending_orders.status IS '订单状态：pending=待处理/processing=处理中/filled=已成交/failed=失败/cancelled=取消';
COMMENT ON COLUMN trade_pending_orders.priority IS '优先级（INTEGER），数值越大越优先处理';
COMMENT ON COLUMN trade_pending_orders.attempts IS '已尝试执行次数';
COMMENT ON COLUMN trade_pending_orders.max_attempts IS '最大尝试次数，默认10次';
COMMENT ON COLUMN trade_pending_orders.last_error IS '最近一次错误信息';
COMMENT ON COLUMN trade_pending_orders.payload_json IS '信号携带的扩展数据JSON';
COMMENT ON COLUMN trade_pending_orders.dispatch_note IS '分发备注（如失败原因说明）';
COMMENT ON COLUMN trade_pending_orders.exchange_id IS '目标交易所ID，如 binance/okx/bybit';
COMMENT ON COLUMN trade_pending_orders.exchange_order_id IS '交易所返回的订单ID';
COMMENT ON COLUMN trade_pending_orders.exchange_response_json IS '交易所原始响应JSON';
COMMENT ON COLUMN trade_pending_orders.filled IS '已成交数量（NUMERIC(20,8)）';
COMMENT ON COLUMN trade_pending_orders.avg_price IS '平均成交价（NUMERIC(20,8)）';
COMMENT ON COLUMN trade_pending_orders.executed_at IS '订单成交时间';
COMMENT ON COLUMN trade_pending_orders.created_at IS '信号产生/订单创建时间';
COMMENT ON COLUMN trade_pending_orders.updated_at IS '记录更新时间';
COMMENT ON COLUMN trade_pending_orders.processed_at IS '订单处理完成时间';
COMMENT ON COLUMN trade_pending_orders.sent_at IS '订单发送到交易所的时间';

COMMENT ON TABLE trade_strategy_notifications IS '策略通知表 — 记录策略运行时产生的各类通知（信号/错误/风控等）';
COMMENT ON COLUMN trade_strategy_notifications.id IS '主键，自增序列';
COMMENT ON COLUMN trade_strategy_notifications.user_id IS '所属用户ID，外键→ sys_users(id)，NOT NULL DEFAULT 1，级联删除';
COMMENT ON COLUMN trade_strategy_notifications.strategy_id IS '关联策略ID，外键→ trade_strategies_trading(id)，级联删除';
COMMENT ON COLUMN trade_strategy_notifications.symbol IS '相关交易品种';
COMMENT ON COLUMN trade_strategy_notifications.signal_type IS '信号类型（buy/sell/close）';
COMMENT ON COLUMN trade_strategy_notifications.channels IS '通知发送渠道，逗号分隔（email/telegram/sms）';
COMMENT ON COLUMN trade_strategy_notifications.title IS '通知标题';
COMMENT ON COLUMN trade_strategy_notifications.message IS '通知正文内容';
COMMENT ON COLUMN trade_strategy_notifications.payload_json IS '通知附加数据JSON';
COMMENT ON COLUMN trade_strategy_notifications.is_read IS '是否已读，0=未读，1=已读';
COMMENT ON COLUMN trade_strategy_notifications.created_at IS '通知创建时间';
COMMENT ON COLUMN trade_strategy_notifications.updated_at IS '记录更新时间';

COMMENT ON TABLE trade_strategy_logs IS '策略运行日志表 — 记录策略运行时的详细日志（Dashboard/API展示）';
COMMENT ON COLUMN trade_strategy_logs.id IS '主键，自增序列';
COMMENT ON COLUMN trade_strategy_logs.strategy_id IS '关联策略ID，外键→ trade_strategies_trading(id)，NOT NULL，级联删除';
COMMENT ON COLUMN trade_strategy_logs.level IS '日志级别：debug/info/warning/error';
COMMENT ON COLUMN trade_strategy_logs.message IS '日志内容，NOT NULL';
COMMENT ON COLUMN trade_strategy_logs.timestamp IS '日志时间戳，默认NOW()';

-- Level 5: 手动持仓/警报表（依赖 sys_users）
COMMENT ON TABLE trade_exchange_credentials IS '交易所凭证表 — 存储用户在各交易所的API密钥加密配置';
COMMENT ON COLUMN trade_exchange_credentials.id IS '主键，自增序列';
COMMENT ON COLUMN trade_exchange_credentials.user_id IS '所属用户ID，外键→ sys_users(id)，NOT NULL DEFAULT 1，级联删除';
COMMENT ON COLUMN trade_exchange_credentials.name IS '凭证名称标识（如 Binance主账户）';
COMMENT ON COLUMN trade_exchange_credentials.exchange_id IS '交易所ID，如 binance/okx/bybit/huobi';
COMMENT ON COLUMN trade_exchange_credentials.api_key_hint IS 'API Key提示（只存头尾字符如 sk***abc）';
COMMENT ON COLUMN trade_exchange_credentials.encrypted_config IS '加密后的交易所配置JSON（包含API Key/Secret/密码等）';
COMMENT ON COLUMN trade_exchange_credentials.created_at IS '记录创建时间';
COMMENT ON COLUMN trade_exchange_credentials.updated_at IS '记录更新时间';

COMMENT ON TABLE trade_manual_positions IS '手动持仓表 — 记录用户手动录入的持仓记录（独立于策略）';
COMMENT ON COLUMN trade_manual_positions.id IS '主键，自增序列';
COMMENT ON COLUMN trade_manual_positions.user_id IS '所属用户ID，外键→ sys_users(id)，NOT NULL DEFAULT 1，级联删除';
COMMENT ON COLUMN trade_manual_positions.market IS '市场类别，如 Crypto/USStock';
COMMENT ON COLUMN trade_manual_positions.symbol IS '交易品种代码，NOT NULL';
COMMENT ON COLUMN trade_manual_positions.name IS '品种显示名称（如 Bitcoin）';
COMMENT ON COLUMN trade_manual_positions.side IS '持仓方向，默认 long（多头），也支持 short（空头）';
COMMENT ON COLUMN trade_manual_positions.quantity IS '持仓数量（NUMERIC(20,8)），NOT NULL DEFAULT 0';
COMMENT ON COLUMN trade_manual_positions.entry_price IS '入场价格（NUMERIC(20,8)），NOT NULL DEFAULT 0';
COMMENT ON COLUMN trade_manual_positions.entry_time IS '入场时间戳（BIGINT，Unix毫秒）';
COMMENT ON COLUMN trade_manual_positions.notes IS '备注文本';
COMMENT ON COLUMN trade_manual_positions.tags IS '标签JSON（自定义分类标签）';
COMMENT ON COLUMN trade_manual_positions.group_name IS '持仓组名称（如 长期仓位/短线仓位）';
COMMENT ON COLUMN trade_manual_positions.created_at IS '记录创建时间';
COMMENT ON COLUMN trade_manual_positions.updated_at IS '记录更新时间';

COMMENT ON TABLE trade_position_alerts IS '持仓警报表 — 设置价格/盈亏/时间等条件的触发告警';
COMMENT ON COLUMN trade_position_alerts.id IS '主键，自增序列';
COMMENT ON COLUMN trade_position_alerts.user_id IS '所属用户ID，外键→ sys_users(id)，NOT NULL DEFAULT 1，级联删除';
COMMENT ON COLUMN trade_position_alerts.position_id IS '关联的持仓ID（关联trade_manual_positions或其他持仓来源）';
COMMENT ON COLUMN trade_position_alerts.market IS '市场类别';
COMMENT ON COLUMN trade_position_alerts.symbol IS '交易品种';
COMMENT ON COLUMN trade_position_alerts.alert_type IS '告警类型：price_above/price_below/pnl_pct/time_reached';
COMMENT ON COLUMN trade_position_alerts.threshold IS '触发阈值（NUMERIC(20,8)），如目标价格或盈亏百分比';
COMMENT ON COLUMN trade_position_alerts.notification_config IS '触发时的通知配置JSON';
COMMENT ON COLUMN trade_position_alerts.is_active IS '是否激活，1=激活，0=停用';
COMMENT ON COLUMN trade_position_alerts.is_triggered IS '是否已触发，1=已触发，0=未触发';
COMMENT ON COLUMN trade_position_alerts.last_triggered_at IS '最后触发时间';
COMMENT ON COLUMN trade_position_alerts.trigger_count IS '累计触发次数';
COMMENT ON COLUMN trade_position_alerts.repeat_interval IS '重复触发间隔秒数，0=仅触发一次';
COMMENT ON COLUMN trade_position_alerts.notes IS '告警备注';
COMMENT ON COLUMN trade_position_alerts.created_at IS '记录创建时间';
COMMENT ON COLUMN trade_position_alerts.updated_at IS '记录更新时间';

COMMENT ON TABLE trade_position_monitors IS '持仓监控表 — AI自动监控持仓并给出调仓建议';
COMMENT ON COLUMN trade_position_monitors.id IS '主键，自增序列';
COMMENT ON COLUMN trade_position_monitors.user_id IS '所属用户ID，外键→ sys_users(id)，NOT NULL DEFAULT 1，级联删除';
COMMENT ON COLUMN trade_position_monitors.name IS '监控任务名称';
COMMENT ON COLUMN trade_position_monitors.position_ids IS '监控的持仓ID列表（JSON格式）';
COMMENT ON COLUMN trade_position_monitors.monitor_type IS '监控模式，默认 ai（AI分析模式）';
COMMENT ON COLUMN trade_position_monitors.config IS '监控配置JSON（分析频率/分析维度等）';
COMMENT ON COLUMN trade_position_monitors.notification_config IS '通知配置JSON';
COMMENT ON COLUMN trade_position_monitors.is_active IS '是否激活，1=激活，0=停用';
COMMENT ON COLUMN trade_position_monitors.last_run_at IS '最近运行时间';
COMMENT ON COLUMN trade_position_monitors.next_run_at IS '计划下次运行时间';
COMMENT ON COLUMN trade_position_monitors.last_result IS '最近运行结果/AI建议';
COMMENT ON COLUMN trade_position_monitors.run_count IS '累计运行次数';
COMMENT ON COLUMN trade_position_monitors.created_at IS '记录创建时间';
COMMENT ON COLUMN trade_position_monitors.updated_at IS '记录更新时间';

-- Level 6: 指标/自选股/分析任务/回测/快捷交易表
COMMENT ON TABLE ind_indicator_codes IS '指标代码表 — 存储用户编写的交易指标代码（支持加密/付费/社区共享）';
COMMENT ON COLUMN ind_indicator_codes.id IS '主键，自增序列';
COMMENT ON COLUMN ind_indicator_codes.user_id IS '创建者用户ID，外键→ sys_users(id)，DEFAULT 1，级联删除';
COMMENT ON COLUMN ind_indicator_codes.is_buy IS '指标类型，0=卖出指标，1=买入指标';
COMMENT ON COLUMN ind_indicator_codes.end_time IS '指标有效期时间戳（BIGINT），1=永不过期';
COMMENT ON COLUMN ind_indicator_codes.name IS '指标名称，NOT NULL DEFAULT空字符串';
COMMENT ON COLUMN ind_indicator_codes.code IS '指标Python源代码（TEXT）';
COMMENT ON COLUMN ind_indicator_codes.description IS '指标描述文本';
COMMENT ON COLUMN ind_indicator_codes.publish_to_community IS '是否发布到社区，0=不发布，1=发布';
COMMENT ON COLUMN ind_indicator_codes.pricing_type IS '定价类型：free=免费/paid=付费/subscription=订阅';
COMMENT ON COLUMN ind_indicator_codes.price IS '价格（NUMERIC(10,2)），NOT NULL DEFAULT 0';
COMMENT ON COLUMN ind_indicator_codes.is_encrypted IS '是否加密，0=明文，1=加密（购买后解密）';
COMMENT ON COLUMN ind_indicator_codes.preview_image IS '指标预览图URL';
COMMENT ON COLUMN ind_indicator_codes.vip_free IS 'VIP用户是否免费，TRUE=免费';
COMMENT ON COLUMN ind_indicator_codes.createtime IS '创建时间戳（BIGINT，Unix秒）';
COMMENT ON COLUMN ind_indicator_codes.updatetime IS '更新时间戳（BIGINT，Unix秒）';
COMMENT ON COLUMN ind_indicator_codes.created_at IS '记录创建时间';
COMMENT ON COLUMN ind_indicator_codes.updated_at IS '记录更新时间';
COMMENT ON COLUMN ind_indicator_codes.purchase_count IS '累计购买次数';
COMMENT ON COLUMN ind_indicator_codes.avg_rating IS '平均评分（NUMERIC(3,2)），范围0-5';
COMMENT ON COLUMN ind_indicator_codes.rating_count IS '评分次数';
COMMENT ON COLUMN ind_indicator_codes.view_count IS '浏览次数';
COMMENT ON COLUMN ind_indicator_codes.review_status IS '审核状态：pending=待审核/approved=已通过/rejected=已拒绝';
COMMENT ON COLUMN ind_indicator_codes.review_note IS '审核备注/拒绝原因';
COMMENT ON COLUMN ind_indicator_codes.reviewed_at IS '审核时间';
COMMENT ON COLUMN ind_indicator_codes.reviewed_by IS '审核人用户ID';
COMMENT ON COLUMN ind_indicator_codes.source_indicator_id IS '源指标ID（用于指标同步/克隆场景）';

COMMENT ON TABLE ind_indicator_purchases IS '指标购买记录表 — 记录用户购买指标的订单（一指标一购买记录）';
COMMENT ON COLUMN ind_indicator_purchases.id IS '主键，自增序列';
COMMENT ON COLUMN ind_indicator_purchases.indicator_id IS '被购买的指标ID，外键→ ind_indicator_codes(id)，级联删除';
COMMENT ON COLUMN ind_indicator_purchases.buyer_id IS '购买者用户ID，外键→ sys_users(id)，级联删除，NOT NULL';
COMMENT ON COLUMN ind_indicator_purchases.seller_id IS '出售者用户ID，外键→ sys_users(id)，NOT NULL';
COMMENT ON COLUMN ind_indicator_purchases.price IS '购买价格（NUMERIC(10,2)），NOT NULL DEFAULT 0';
COMMENT ON COLUMN ind_indicator_purchases.created_at IS '购买时间';

COMMENT ON TABLE ind_indicator_comments IS '指标评论表 — 用户对购买过的指标发表评分和评论';
COMMENT ON COLUMN ind_indicator_comments.id IS '主键，自增序列';
COMMENT ON COLUMN ind_indicator_comments.indicator_id IS '被评论的指标ID，外键→ ind_indicator_codes(id)，级联删除';
COMMENT ON COLUMN ind_indicator_comments.user_id IS '评论用户ID，外键→ sys_users(id)，级联删除，NOT NULL';
COMMENT ON COLUMN ind_indicator_comments.rating IS '评分（INTEGER），范围1-5，CHECK约束';
COMMENT ON COLUMN ind_indicator_comments.content IS '评论内容文本';
COMMENT ON COLUMN ind_indicator_comments.parent_id IS '父评论ID，外键→ ind_indicator_comments(id)，支持嵌套评论';
COMMENT ON COLUMN ind_indicator_comments.is_deleted IS '是否已删除，0=正常，1=已删除（软删除）';
COMMENT ON COLUMN ind_indicator_comments.created_at IS '评论时间';
COMMENT ON COLUMN ind_indicator_comments.updated_at IS '评论更新时间';

COMMENT ON TABLE trade_watchlist IS '自选股表 — 存储用户关注的市场品种（支持多市场）';
COMMENT ON COLUMN trade_watchlist.id IS '主键，自增序列';
COMMENT ON COLUMN trade_watchlist.user_id IS '所属用户ID，外键→ sys_users(id)，DEFAULT 1，级联删除';
COMMENT ON COLUMN trade_watchlist.market IS '市场类别，NOT NULL';
COMMENT ON COLUMN trade_watchlist.symbol IS '交易品种代码，NOT NULL';
COMMENT ON COLUMN trade_watchlist.name IS '品种显示名称';
COMMENT ON COLUMN trade_watchlist.created_at IS '添加时间';
COMMENT ON COLUMN trade_watchlist.updated_at IS '更新时间';

COMMENT ON TABLE analy_analysis_tasks IS 'AI分析任务表 — 记录用户发起的AI市场分析任务';
COMMENT ON COLUMN analy_analysis_tasks.id IS '主键，自增序列';
COMMENT ON COLUMN analy_analysis_tasks.user_id IS '发起用户ID，外键→ sys_users(id)，DEFAULT 1，级联删除';
COMMENT ON COLUMN analy_analysis_tasks.market IS '分析的市场类别，NOT NULL';
COMMENT ON COLUMN analy_analysis_tasks.symbol IS '分析的品种，NOT NULL';
COMMENT ON COLUMN analy_analysis_tasks.model IS '使用的AI模型名称';
COMMENT ON COLUMN analy_analysis_tasks.language IS '分析语言，默认 en-US';
COMMENT ON COLUMN analy_analysis_tasks.status IS '任务状态：pending=排队中/running=分析中/completed=已完成/failed=失败';
COMMENT ON COLUMN analy_analysis_tasks.result_json IS '分析结果的JSON序列化';
COMMENT ON COLUMN analy_analysis_tasks.error_message IS '失败时的错误信息';
COMMENT ON COLUMN analy_analysis_tasks.created_at IS '任务创建时间';
COMMENT ON COLUMN analy_analysis_tasks.completed_at IS '任务完成时间';

COMMENT ON TABLE trade_market_symbols IS '市场品种表 — 存储支持交易的市场和品种元数据（包含种子数据）';
COMMENT ON COLUMN trade_market_symbols.id IS '主键，自增序列';
COMMENT ON COLUMN trade_market_symbols.market IS '市场类别，NOT NULL，如 Crypto/USStock/Forex/Futures/CNStock/HKStock';
COMMENT ON COLUMN trade_market_symbols.symbol IS '品种代码，NOT NULL（如 BTC/USDT、AAPL）';
COMMENT ON COLUMN trade_market_symbols.name IS '品种中文/英文名称（如 Bitcoin、Apple Inc.）';
COMMENT ON COLUMN trade_market_symbols.exchange IS '交易所名称（如 Binance、NASDAQ）';
COMMENT ON COLUMN trade_market_symbols.currency IS '计价货币，如 USDT/USD/CNY/HKD';
COMMENT ON COLUMN trade_market_symbols.is_active IS '是否启用，1=启用，0=禁用';
COMMENT ON COLUMN trade_market_symbols.is_hot IS '是否热门，1=热门（默认显示），0=普通';
COMMENT ON COLUMN trade_market_symbols.sort_order IS '排序权重，数值越大排序越靠前';
COMMENT ON COLUMN trade_market_symbols.created_at IS '记录创建时间';

COMMENT ON TABLE analy_analysis_memory IS 'AI分析记忆表 — 存储AI分析的历史结果、反馈和预测准确性追踪';
COMMENT ON COLUMN analy_analysis_memory.id IS '主键，自增序列';
COMMENT ON COLUMN analy_analysis_memory.user_id IS '用户ID（INTEGER），关联 sys_users(id)';
COMMENT ON COLUMN analy_analysis_memory.market IS '市场类别，NOT NULL';
COMMENT ON COLUMN analy_analysis_memory.symbol IS '交易品种，NOT NULL';
COMMENT ON COLUMN analy_analysis_memory.decision IS 'AI决策结论，NOT NULL（buy/sell/hold）';
COMMENT ON COLUMN analy_analysis_memory.confidence IS '置信度（INTEGER），默认50，范围0-100';
COMMENT ON COLUMN analy_analysis_memory.price_at_analysis IS '分析时的市场快照价格';
COMMENT ON COLUMN analy_analysis_memory.summary IS '分析摘要文本';
COMMENT ON COLUMN analy_analysis_memory.reasons IS '决策理由JSON（各维度分析理由列表）';
COMMENT ON COLUMN analy_analysis_memory.scores IS '各维度评分JSON';
COMMENT ON COLUMN analy_analysis_memory.indicators_snapshot IS '分析时指标快照JSON';
COMMENT ON COLUMN analy_analysis_memory.raw_result IS 'AI完整原始返回JSONB';
COMMENT ON COLUMN analy_analysis_memory.consensus_score IS '共识评分（NUMERIC(24,8)）';
COMMENT ON COLUMN analy_analysis_memory.consensus_abs IS '共识绝对值（NUMERIC(24,8)）';
COMMENT ON COLUMN analy_analysis_memory.agreement_ratio IS '一致性比率（NUMERIC(10,6)）';
COMMENT ON COLUMN analy_analysis_memory.quality_multiplier IS '质量倍数（NUMERIC(10,6)）';
COMMENT ON COLUMN analy_analysis_memory.created_at IS '分析发生时间';
COMMENT ON COLUMN analy_analysis_memory.validated_at IS '预测验证时间（事后填写）';
COMMENT ON COLUMN analy_analysis_memory.actual_outcome IS '实际结果（buy/sell/hold/null）';
COMMENT ON COLUMN analy_analysis_memory.actual_return_pct IS '实际收益率百分比';
COMMENT ON COLUMN analy_analysis_memory.was_correct IS '预测是否正确（事后由系统或用户判定）';
COMMENT ON COLUMN analy_analysis_memory.user_feedback IS '用户反馈（accurate/inaccurate/neutral）';
COMMENT ON COLUMN analy_analysis_memory.feedback_at IS '用户反馈时间';

COMMENT ON TABLE ind_backtest_runs IS '回测结果表 — 存储策略/指标回测运行的完整结果';
COMMENT ON COLUMN ind_backtest_runs.id IS '主键，自增序列';
COMMENT ON COLUMN ind_backtest_runs.user_id IS '所属用户ID，外键→ sys_users(id)，NOT NULL DEFAULT 1，级联删除';
COMMENT ON COLUMN ind_backtest_runs.strategy_id IS '关联的策略ID（INTEGER）';
COMMENT ON COLUMN ind_backtest_runs.indicator_id IS '关联的指标ID（INTEGER）';
COMMENT ON COLUMN ind_backtest_runs.strategy_name IS '策略名称（快照保存）';
COMMENT ON COLUMN ind_backtest_runs.run_type IS '回测类型，默认 indicator，可能值：indicator/backtest/script';
COMMENT ON COLUMN ind_backtest_runs.engine_version IS '回测引擎版本';
COMMENT ON COLUMN ind_backtest_runs.code_hash IS '回测代码哈希（用于缓存/去重）';
COMMENT ON COLUMN ind_backtest_runs.config_snapshot IS '回测配置快照JSON';
COMMENT ON COLUMN ind_backtest_runs.total_return IS '总收益率（NUMERIC(18,6)）';
COMMENT ON COLUMN ind_backtest_runs.win_rate IS '胜率（NUMERIC(10,4)）';
COMMENT ON COLUMN ind_backtest_runs.max_drawdown IS '最大回撤（NUMERIC(10,4)）';
COMMENT ON COLUMN ind_backtest_runs.payload_json IS '扩展数据JSON（夏普比率/波动率等）';
COMMENT ON COLUMN ind_backtest_runs.created_at IS '回测开始时间';
COMMENT ON COLUMN ind_backtest_runs.updated_at IS '记录更新时间';

COMMENT ON TABLE ind_backtest_trades IS '回测交易记录表 — 存储回测引擎模拟的每笔成交';
COMMENT ON COLUMN ind_backtest_trades.id IS '主键，自增序列';
COMMENT ON COLUMN ind_backtest_trades.run_id IS '关联回测ID，NOT NULL，外键→ ind_backtest_runs(id)';
COMMENT ON COLUMN ind_backtest_trades.user_id IS '所属用户ID，外键→ sys_users(id)，NOT NULL DEFAULT 1，级联删除';
COMMENT ON COLUMN ind_backtest_trades.strategy_id IS '关联策略ID（INTEGER）';
COMMENT ON COLUMN ind_backtest_trades.trade_index IS '交易序号（INTEGER），从0开始';
COMMENT ON COLUMN ind_backtest_trades.trade_time IS '交易时间（VARCHAR(64)，ISO8601格式字符串）';
COMMENT ON COLUMN ind_backtest_trades.trade_type IS '交易类型，如 open/close/adjust';
COMMENT ON COLUMN ind_backtest_trades.side IS '方向，long/short';
COMMENT ON COLUMN ind_backtest_trades.price IS '成交价格（NUMERIC(24,8)）';
COMMENT ON COLUMN ind_backtest_trades.amount IS '成交数量（NUMERIC(24,8)）';
COMMENT ON COLUMN ind_backtest_trades.profit IS '该笔盈亏（NUMERIC(24,8)）';
COMMENT ON COLUMN ind_backtest_trades.balance IS '成交后账户余额';
COMMENT ON COLUMN ind_backtest_trades.reason IS '成交原因/备注';
COMMENT ON COLUMN ind_backtest_trades.payload_json IS '扩展数据JSON';
COMMENT ON COLUMN ind_backtest_trades.created_at IS '记录创建时间';
COMMENT ON COLUMN ind_backtest_trades.updated_at IS '记录更新时间';

COMMENT ON TABLE ind_backtest_equity_points IS '回测权益曲线表 — 存储回测期间每个时间点的账户权益快照';
COMMENT ON COLUMN ind_backtest_equity_points.id IS '主键，自增序列';
COMMENT ON COLUMN ind_backtest_equity_points.run_id IS '关联回测ID，NOT NULL，外键→ ind_backtest_runs(id)';
COMMENT ON COLUMN ind_backtest_equity_points.point_index IS '数据点序号（INTEGER），从0开始';
COMMENT ON COLUMN ind_backtest_equity_points.point_time IS '权益快照时间（VARCHAR(64)，ISO8601）';
COMMENT ON COLUMN ind_backtest_equity_points.point_value IS '权益值（NUMERIC(24,8)）';
COMMENT ON COLUMN ind_backtest_equity_points.created_at IS '记录创建时间';
COMMENT ON COLUMN ind_backtest_equity_points.updated_at IS '记录更新时间';

COMMENT ON TABLE trade_quick_trades IS '快捷交易记录表 — 记录用户在UI界面一键下单的交易记录';
COMMENT ON COLUMN trade_quick_trades.id IS '主键，自增序列';
COMMENT ON COLUMN trade_quick_trades.user_id IS '所属用户ID，外键→ sys_users(id)，NOT NULL，级联删除';
COMMENT ON COLUMN trade_quick_trades.credential_id IS '关联的凭证ID（INTEGER）';
COMMENT ON COLUMN trade_quick_trades.exchange_id IS '交易所ID，NOT NULL DEFAULT空字符串';
COMMENT ON COLUMN trade_quick_trades.symbol IS '交易品种，NOT NULL';
COMMENT ON COLUMN trade_quick_trades.side IS '方向，buy=买入/sell=卖出，NOT NULL';
COMMENT ON COLUMN trade_quick_trades.order_type IS '订单类型，market=市价/limit=限价，NOT NULL';
COMMENT ON COLUMN trade_quick_trades.amount IS '委托数量（NUMERIC(24,8)）';
COMMENT ON COLUMN trade_quick_trades.price IS '委托价格（NUMERIC(24,8)），市价单为0';
COMMENT ON COLUMN trade_quick_trades.leverage IS '杠杆倍数，默认1';
COMMENT ON COLUMN trade_quick_trades.market_type IS '市场类型，swap=永续/spot=现货';
COMMENT ON COLUMN trade_quick_trades.tp_price IS '止盈价格（NUMERIC(24,8)）';
COMMENT ON COLUMN trade_quick_trades.sl_price IS '止损价格（NUMERIC(24,8)）';
COMMENT ON COLUMN trade_quick_trades.status IS '订单状态：submitted=已提交/filled=成交/cancelled=取消/failed=失败';
COMMENT ON COLUMN trade_quick_trades.exchange_order_id IS '交易所返回的订单ID';
COMMENT ON COLUMN trade_quick_trades.filled_amount IS '已成交数量（NUMERIC(24,8)）';
COMMENT ON COLUMN trade_quick_trades.avg_fill_price IS '平均成交价（NUMERIC(24,8)）';
COMMENT ON COLUMN trade_quick_trades.error_msg IS '错误信息';
COMMENT ON COLUMN trade_quick_trades.source IS '来源，默认 manual（手动），也可为 strategy/api等';
COMMENT ON COLUMN trade_quick_trades.raw_result IS '交易所原始响应（JSONB）';
COMMENT ON COLUMN trade_quick_trades.created_at IS '下单时间';
COMMENT ON COLUMN trade_quick_trades.updated_at IS '记录更新时间';

-- Level 7: 图谱数据表
COMMENT ON TABLE sys_collection_records IS '数据采集记录表 — 记录采集到的外部数据（新闻/社交媒体等）用于去重和来源追踪';
COMMENT ON COLUMN sys_collection_records.id IS '主键，自增序列';
COMMENT ON COLUMN sys_collection_records.source IS '数据来源，如 news_api/twitter/reddit';
COMMENT ON COLUMN sys_collection_records.data_type IS '数据类型，如 article/social_post/earnings';
COMMENT ON COLUMN sys_collection_records.market IS '关联市场（如 Crypto/USStock）';
COMMENT ON COLUMN sys_collection_records.symbol IS '关联交易品种';
COMMENT ON COLUMN sys_collection_records.content_hash IS '内容哈希（UNIQUE），用于去重检测（SHA256）';
COMMENT ON COLUMN sys_collection_records.created_at IS '采集时间';
COMMENT ON COLUMN sys_collection_records.updated_at IS '更新时间';

COMMENT ON TABLE gra_graph_episodes IS '知识图谱事件表 — 存储从外部数据提取的市场事件/新闻/公告等（Graphiti驱动）';
COMMENT ON COLUMN gra_graph_episodes.id IS '主键，自增序列';
COMMENT ON COLUMN gra_graph_episodes.episode_type IS '事件类型，如 earnings/regulation/partnership/product_launch';
COMMENT ON COLUMN gra_graph_episodes.market_domain IS '市场领域，如 Crypto/USStock/Commodities';
COMMENT ON COLUMN gra_graph_episodes.title IS '事件标题';
COMMENT ON COLUMN gra_graph_episodes.source IS '数据来源，如 Reuters/Bloomberg/Twitter';
COMMENT ON COLUMN gra_graph_episodes.source_ref IS '来源引用URL或ID';
COMMENT ON COLUMN gra_graph_episodes.dedup_key IS '去重键（UNIQUE），避免重复摄入同一事件';
COMMENT ON COLUMN gra_graph_episodes.importance_score IS '重要性评分（NUMERIC(6,4)），0-1范围，默认0.5';
COMMENT ON COLUMN gra_graph_episodes.event_time IS '事件实际发生时间';
COMMENT ON COLUMN gra_graph_episodes.observed_time IS '事件被系统观测到的时间，NOT NULL';
COMMENT ON COLUMN gra_graph_episodes.status IS '处理状态：pending=待处理/processing=处理中/completed=完成/failed=失败';
COMMENT ON COLUMN gra_graph_episodes.error_message IS '处理失败时的错误信息';
COMMENT ON COLUMN gra_graph_episodes.created_at IS '记录创建时间';
COMMENT ON COLUMN gra_graph_episodes.updated_at IS '记录更新时间';

COMMENT ON TABLE gra_graph_jobs IS '知识图谱任务表 — 存储Graphiti图谱构建任务的执行记录（节点抽取/关系建立等）';
COMMENT ON COLUMN gra_graph_jobs.id IS '主键，自增序列';
COMMENT ON COLUMN gra_graph_jobs.episode_id IS '关联的事件ID（INTEGER），关联 gra_graph_episodes(id)';
COMMENT ON COLUMN gra_graph_jobs.job_type IS '任务类型：entity_extraction/relation_extraction/embedding/indexing';
COMMENT ON COLUMN gra_graph_jobs.status IS '任务状态：pending/running/completed/failed';
COMMENT ON COLUMN gra_graph_jobs.retry_count IS '重试次数';
COMMENT ON COLUMN gra_graph_jobs.error_message IS '失败错误信息';
COMMENT ON COLUMN gra_graph_jobs.started_at IS '任务开始时间';
COMMENT ON COLUMN gra_graph_jobs.finished_at IS '任务完成时间';
COMMENT ON COLUMN gra_graph_jobs.created_at IS '记录创建时间';
COMMENT ON COLUMN gra_graph_jobs.updated_at IS '记录更新时间';

COMMENT ON TABLE gra_graph_entity_refs IS '图谱实体引用表 — 存储业务表记录与图谱实体的映射关系（支持业务表→实体双向查询）';
COMMENT ON COLUMN gra_graph_entity_refs.id IS '主键，自增序列';
COMMENT ON COLUMN gra_graph_entity_refs.entity_uid IS '图谱实体UID（Graphiti生成的全局唯一ID）';
COMMENT ON COLUMN gra_graph_entity_refs.entity_type IS '实体类型，如 company/product/person/currency';
COMMENT ON COLUMN gra_graph_entity_refs.source_table IS '来源业务表名，如 sys_news/sys_earnings';
COMMENT ON COLUMN gra_graph_entity_refs.source_pk IS '来源业务表主键值';
COMMENT ON COLUMN gra_graph_entity_refs.created_at IS '创建时间';
COMMENT ON COLUMN gra_graph_entity_refs.updated_at IS '更新时间';

COMMENT ON TABLE gra_graph_relation_snapshots IS '图谱关系快照表 — 存储实体间关系的历史快照（支持关系时序分析）';
COMMENT ON COLUMN gra_graph_relation_snapshots.id IS '主键，自增序列';
COMMENT ON COLUMN gra_graph_relation_snapshots.relation_type IS '关系类型，如 competitor/supplier/partner/regulates';
COMMENT ON COLUMN gra_graph_relation_snapshots.from_uid IS '起始实体UID';
COMMENT ON COLUMN gra_graph_relation_snapshots.to_uid IS '目标实体UID';
COMMENT ON COLUMN gra_graph_relation_snapshots.source_ref IS '关系来源引用URL/文档';
COMMENT ON COLUMN gra_graph_relation_snapshots.confidence IS '关系置信度（NUMERIC(6,4)）';
COMMENT ON COLUMN gra_graph_relation_snapshots.t_valid IS '关系有效起始时间';
COMMENT ON COLUMN gra_graph_relation_snapshots.t_invalid IS '关系失效时间（NULL表示仍有效）';
COMMENT ON COLUMN gra_graph_relation_snapshots.payload_json IS '扩展关系属性JSON';
COMMENT ON COLUMN gra_graph_relation_snapshots.created_at IS '快照创建时间';
COMMENT ON COLUMN gra_graph_relation_snapshots.updated_at IS '快照更新时间';

COMMENT ON TABLE gra_graph_feature_daily IS '图谱特征日表 — 存储从知识图谱提取的市场/品种粒度日频特征（用于AI信号增强）';
COMMENT ON COLUMN gra_graph_feature_daily.id IS '主键，自增序列';
COMMENT ON COLUMN gra_graph_feature_daily.trade_date IS '交易日期（DATE），NOT NULL';
COMMENT ON COLUMN gra_graph_feature_daily.market IS '市场类别，NOT NULL';
COMMENT ON COLUMN gra_graph_feature_daily.symbol IS '交易品种，NOT NULL';
COMMENT ON COLUMN gra_graph_feature_daily.feature_name IS '特征名称，NOT NULL（如 sentiment_score/narrative_strength）';
COMMENT ON COLUMN gra_graph_feature_daily.feature_value IS '特征值（NUMERIC(24,8)），NOT NULL';
COMMENT ON COLUMN gra_graph_feature_daily.source IS '特征来源，默认 graph';
COMMENT ON COLUMN gra_graph_feature_daily.created_at IS '记录创建时间';
COMMENT ON COLUMN gra_graph_feature_daily.updated_at IS '记录更新时间';

COMMENT ON TABLE gra_company_narrative_features IS '公司叙事特征表 — 存储美股/港股公司的市场叙事评分（如财报超预期、产品发布等）';
COMMENT ON COLUMN gra_company_narrative_features.id IS '主键，自增序列';
COMMENT ON COLUMN gra_company_narrative_features.trade_date IS '交易日期（DATE），NOT NULL';
COMMENT ON COLUMN gra_company_narrative_features.ticker IS '股票代码，NOT NULL（如 AAPL、00700）';
COMMENT ON COLUMN gra_company_narrative_features.narrative_name IS '叙事名称，NOT NULL（如 earnings_beat/product_launch/layoff）';
COMMENT ON COLUMN gra_company_narrative_features.narrative_score IS '叙事评分（NUMERIC(10,4)），NOT NULL，-1到1范围';
COMMENT ON COLUMN gra_company_narrative_features.source IS '数据来源，默认 graph';
COMMENT ON COLUMN gra_company_narrative_features.created_at IS '记录创建时间';
COMMENT ON COLUMN gra_company_narrative_features.updated_at IS '记录更新时间';

COMMENT ON TABLE gra_crypto_narrative_features IS '加密货币叙事特征表 — 存储加密货币的市场叙事评分（如ETF批准/监管消息/技术升级等）';
COMMENT ON COLUMN gra_crypto_narrative_features.id IS '主键，自增序列';
COMMENT ON COLUMN gra_crypto_narrative_features.trade_date IS '交易日期（DATE），NOT NULL';
COMMENT ON COLUMN gra_crypto_narrative_features.symbol IS '加密货币符号，NOT NULL（如 BTC、ETH）';
COMMENT ON COLUMN gra_crypto_narrative_features.narrative_name IS '叙事名称，NOT NULL（如 etf_approval/regulation_upgrade）';
COMMENT ON COLUMN gra_crypto_narrative_features.narrative_score IS '叙事评分（NUMERIC(10,4)），NOT NULL';
COMMENT ON COLUMN gra_crypto_narrative_features.source IS '数据来源，默认 graph';
COMMENT ON COLUMN gra_crypto_narrative_features.created_at IS '记录创建时间';
COMMENT ON COLUMN gra_crypto_narrative_features.updated_at IS '记录更新时间';

COMMENT ON TABLE gra_polymarket_market_features IS 'Polymarket市场特征表 — 存储预测市场事件的相关资产特征';
COMMENT ON COLUMN gra_polymarket_market_features.id IS '主键，自增序列';
COMMENT ON COLUMN gra_polymarket_market_features.trade_date IS '交易日期（DATE），NOT NULL';
COMMENT ON COLUMN gra_polymarket_market_features.market_id IS 'Polymarket市场ID，NOT NULL';
COMMENT ON COLUMN gra_polymarket_market_features.feature_name IS '特征名称，NOT NULL';
COMMENT ON COLUMN gra_polymarket_market_features.feature_value IS '特征值（NUMERIC(24,8)），NOT NULL';
COMMENT ON COLUMN gra_polymarket_market_features.source IS '特征来源，默认 graph';
COMMENT ON COLUMN gra_polymarket_market_features.created_at IS '记录创建时间';
COMMENT ON COLUMN gra_polymarket_market_features.updated_at IS '记录更新时间';

-- Level 8: Dify工作流表
COMMENT ON TABLE data_dify_workflows IS 'Dify工作流配置表 — 存储Dify AI工作流的注册配置信息（API端点/密钥/输入输出Schema）';
COMMENT ON COLUMN data_dify_workflows.id IS '主键，自增序列';
COMMENT ON COLUMN data_dify_workflows.code IS '工作流编码（UNIQUE），系统内部标识';
COMMENT ON COLUMN data_dify_workflows.name IS '工作流名称';
COMMENT ON COLUMN data_dify_workflows.description IS '工作流描述';
COMMENT ON COLUMN data_dify_workflows.workflow_type IS '工作流类型，默认 chat（对话型）';
COMMENT ON COLUMN data_dify_workflows.endpoint IS 'Dify API完整端点URL';
COMMENT ON COLUMN data_dify_workflows.api_key IS 'Dify API密钥（加密存储）';
COMMENT ON COLUMN data_dify_workflows.input_schema IS '输入参数Schema（JSONB），定义输入字段名和类型';
COMMENT ON COLUMN data_dify_workflows.output_schema IS '输出结果Schema（JSONB），定义输出字段结构';
COMMENT ON COLUMN data_dify_workflows.is_active IS '是否启用，TRUE=启用，FALSE=禁用';
COMMENT ON COLUMN data_dify_workflows.max_retries IS '调用失败最大重试次数，默认3';
COMMENT ON COLUMN data_dify_workflows.timeout_seconds IS '单次调用超时秒数，默认120秒';
COMMENT ON COLUMN data_dify_workflows.created_at IS '记录创建时间';
COMMENT ON COLUMN data_dify_workflows.updated_at IS '记录更新时间';

COMMENT ON TABLE data_dify_workflow_logs IS 'Dify工作流执行日志表 — 记录每次Dify工作流调用的输入输出和性能数据';
COMMENT ON COLUMN data_dify_workflow_logs.id IS '主键，自增序列';
COMMENT ON COLUMN data_dify_workflow_logs.workflow_id IS '关联的工作流ID，外键→ data_dify_workflows(id)，NOT NULL，级联删除';
COMMENT ON COLUMN data_dify_workflow_logs.user_id IS '发起调用的用户ID，外键→ sys_users(id)';
COMMENT ON COLUMN data_dify_workflow_logs.input_data IS '调用输入数据（JSONB）';
COMMENT ON COLUMN data_dify_workflow_logs.output_data IS '调用输出数据（JSONB）';
COMMENT ON COLUMN data_dify_workflow_logs.status IS '执行状态：pending=排队/running=执行中/completed=成功/failed=失败';
COMMENT ON COLUMN data_dify_workflow_logs.call_mode IS '调用模式：batch=批量/sync=同步/async=异步';
COMMENT ON COLUMN data_dify_workflow_logs.tokens_used IS 'Token消耗数量（INTEGER）';
COMMENT ON COLUMN data_dify_workflow_logs.latency_ms IS '调用延迟（INTEGER，毫秒）';
COMMENT ON COLUMN data_dify_workflow_logs.error_message IS '失败时的错误信息';
COMMENT ON COLUMN data_dify_workflow_logs.started_at IS '调用开始时间';
COMMENT ON COLUMN data_dify_workflow_logs.finished_at IS '调用完成时间';
COMMENT ON COLUMN data_dify_workflow_logs.created_at IS '记录创建时间';
COMMENT ON COLUMN data_dify_workflow_logs.updated_at IS '记录更新时间';

-- Level 9: 数据源元数据表
COMMENT ON TABLE data_data_source_configs IS '数据源配置表 — 存储外部数据服务的访问配置（支持多数据源负载均衡）';
COMMENT ON COLUMN data_data_source_configs.id IS '主键，自增序列';
COMMENT ON COLUMN data_data_source_configs.source_code IS '数据源编码（UNIQUE），如 tencent_cn_stock/openai_news';
COMMENT ON COLUMN data_data_source_configs.source_name IS '数据源显示名称';
COMMENT ON COLUMN data_data_source_configs.layer IS '数据层级，默认 data_source（原始数据层）';
COMMENT ON COLUMN data_data_source_configs.market_categories IS '支持的市场类别数组（TEXT[]），如 {Crypto,USStock}';
COMMENT ON COLUMN data_data_source_configs.enabled IS '是否启用，TRUE=启用，FALSE=禁用';
COMMENT ON COLUMN data_data_source_configs.load_balance_strategy IS '负载均衡策略，默认 round_robin，支持：round_robin/weighted_random/least_errors';
COMMENT ON COLUMN data_data_source_configs.config_json IS '访问参数配置（JSONB），如API端点/认证参数/请求限制';
COMMENT ON COLUMN data_data_source_configs.dependencies IS '依赖的其他数据源数组（TEXT[]），如 {fred/economic_calendar}';
COMMENT ON COLUMN data_data_source_configs.notes IS '备注说明';
COMMENT ON COLUMN data_data_source_configs.created_at IS '记录创建时间';
COMMENT ON COLUMN data_data_source_configs.updated_at IS '记录更新时间';

COMMENT ON TABLE data_data_source_datasets IS '数据集元数据表 — 存储各数据源提供的数据集（函数）元数据信息';
COMMENT ON COLUMN data_data_source_datasets.id IS '主键，自增序列';
COMMENT ON COLUMN data_data_source_datasets.source_id IS '所属数据源ID，外键→ data_data_source_configs(id)，级联删除';
COMMENT ON COLUMN data_data_source_datasets.dataset_code IS '数据集编码（UNIQUE），如 cn_stock_daily_kline/fx_realtime';
COMMENT ON COLUMN data_data_source_datasets.dataset_name IS '数据集显示名称';
COMMENT ON COLUMN data_data_source_datasets.description IS '数据集功能描述';
COMMENT ON COLUMN data_data_source_datasets.function_name IS '对应的Python函数名（如 get_cn_stock_kline）';
COMMENT ON COLUMN data_data_source_datasets.return_type IS '返回类型，默认 list[dict]';
COMMENT ON COLUMN data_data_source_datasets.fields_schema IS '返回字段Schema（JSONB），描述各字段含义和类型';
COMMENT ON COLUMN data_data_source_datasets.sample_output IS '示例输出（JSONB）';
COMMENT ON COLUMN data_data_source_datasets.coverage_text IS '数据覆盖范围描述（如 支持沪深A股全市场，延迟15分钟）';
COMMENT ON COLUMN data_data_source_datasets.source_file_ref IS '源代码引用路径';
COMMENT ON COLUMN data_data_source_datasets.created_at IS '记录创建时间';
COMMENT ON COLUMN data_data_source_datasets.updated_at IS '记录更新时间';

COMMENT ON TABLE data_api_keys IS '数据源API密钥管理表 — 存储各数据源的访问密钥（支持公共/私有密钥和限流）';
COMMENT ON COLUMN data_api_keys.id IS '主键，自增序列';
COMMENT ON COLUMN data_api_keys.source_config_id IS '所属数据源配置ID，外键→ data_data_source_configs(id)，级联删除';
COMMENT ON COLUMN data_api_keys.key_type IS '密钥类型：public=公共密钥/private=私有密钥（用户级别）';
COMMENT ON COLUMN data_api_keys.user_id IS '私有密钥所属用户ID，外键→ sys_users(id)，公共密钥为空';
COMMENT ON COLUMN data_api_keys.key_alias IS '密钥别名/备注';
COMMENT ON COLUMN data_api_keys.encrypted_key_value IS 'AES加密后的密钥值明文';
COMMENT ON COLUMN data_api_keys.key_hint IS '密钥显示提示（如 sk_live_****xyz）';
COMMENT ON COLUMN data_api_keys.status IS '密钥状态：active=正常/rate_limited=限流/disabled=禁用';
COMMENT ON COLUMN data_api_keys.weight IS '负载权重（INTEGER），默认1，数值越高被选用概率越大';
COMMENT ON COLUMN data_api_keys.consecutive_errors IS '连续错误次数（INTEGER）';
COMMENT ON COLUMN data_api_keys.last_error_at IS '最后错误发生时间';
COMMENT ON COLUMN data_api_keys.max_consecutive_errors IS '最大连续错误次数阈值，默认5（超过后自动限流）';
COMMENT ON COLUMN data_api_keys.daily_call_limit IS '日调用次数上限，0=不限';
COMMENT ON COLUMN data_api_keys.current_daily_calls IS '当日已调用次数';
COMMENT ON COLUMN data_api_keys.last_reset_at IS '上次计数器重置时间（每日重置）';
COMMENT ON COLUMN data_api_keys.total_calls IS '累计总调用次数';
COMMENT ON COLUMN data_api_keys.created_by IS '创建者用户ID';
COMMENT ON COLUMN data_api_keys.created_at IS '记录创建时间';
COMMENT ON COLUMN data_api_keys.updated_at IS '记录更新时间';

COMMENT ON TABLE data_query_cache IS '查询结果缓存表 — 缓存数据源查询结果，支持TTL过期和主动失效';
COMMENT ON COLUMN data_query_cache.id IS '主键，自增序列';
COMMENT ON COLUMN data_query_cache.cache_key IS '缓存键（UNIQUE），SHA256哈希值（64字符）';
COMMENT ON COLUMN data_query_cache.dataset_id IS '关联的数据集ID，外键→ data_data_source_datasets(id)';
COMMENT ON COLUMN data_query_cache.source_code IS '数据源编码（VARCHAR(80)）';
COMMENT ON COLUMN data_query_cache.query_params IS '查询参数字典（JSONB），作为缓存key的一部分';
COMMENT ON COLUMN data_query_cache.result_data IS '查询结果数据（JSONB）';
COMMENT ON COLUMN data_query_cache.result_size_bytes IS '结果数据大小（字节）';
COMMENT ON COLUMN data_query_cache.status IS '缓存状态：pending=待处理/hit=命中/miss=未命中/error=异常/expired=已过期';
COMMENT ON COLUMN data_query_cache.error_message IS '查询失败时的错误信息';
COMMENT ON COLUMN data_query_cache.request_count IS '该缓存被请求的次数（INTEGER）';
COMMENT ON COLUMN data_query_cache.ttl_seconds IS 'TTL生存时间秒数，默认300秒（5分钟）';
COMMENT ON COLUMN data_query_cache.expires_at IS '缓存过期时间（由TTL计算得出）';
COMMENT ON COLUMN data_query_cache.first_requested_at IS '首次请求时间';
COMMENT ON COLUMN data_query_cache.last_requested_at IS '最后请求时间';
COMMENT ON COLUMN data_query_cache.completed_at IS '查询完成时间';
COMMENT ON COLUMN data_query_cache.created_at IS '记录创建时间';
COMMENT ON COLUMN data_query_cache.updated_at IS '记录更新时间';

-- Level 10: Polymarket预测市场表
COMMENT ON TABLE trade_polymarket_users IS 'Polymarket用户表 — 存储在Polymarket平台有交易记录的钱包地址用户';
COMMENT ON COLUMN trade_polymarket_users.id IS '主键，自增序列';
COMMENT ON COLUMN trade_polymarket_users.address IS '钱包地址（UNIQUE NOT NULL），以太坊格式地址';
COMMENT ON COLUMN trade_polymarket_users.display_name IS '显示名称/昵称';
COMMENT ON COLUMN trade_polymarket_users.win_rate IS '历史胜率（NUMERIC(10,4)）';
COMMENT ON COLUMN trade_polymarket_users.volume IS '累计交易量（NUMERIC(24,8)）';
COMMENT ON COLUMN trade_polymarket_users.payload_json IS '扩展数据JSON';
COMMENT ON COLUMN trade_polymarket_users.created_at IS '首次同步时间';
COMMENT ON COLUMN trade_polymarket_users.updated_at IS '最后同步时间';

COMMENT ON TABLE trade_polymarket_markets IS 'Polymarket市场表 — 存储Polymarket预测市场的元数据（问题/概率/状态）';
COMMENT ON COLUMN trade_polymarket_markets.id IS '主键，自增序列';
COMMENT ON COLUMN trade_polymarket_markets.market_id IS 'Polymarket市场ID（UNIQUE），如 0x1234...abcd';
COMMENT ON COLUMN trade_polymarket_markets.question IS '市场问题文本（NOT NULL），如 "Bitcoin will exceed $100000 by 2025-12-31?"';
COMMENT ON COLUMN trade_polymarket_markets.current_probability IS '当前成交概率（NUMERIC(10,4)），0.5=50%';
COMMENT ON COLUMN trade_polymarket_markets.end_date_iso IS '市场结束日期ISO字符串';
COMMENT ON COLUMN trade_polymarket_markets.active IS '是否活跃，TRUE=进行中，FALSE=已关闭';
COMMENT ON COLUMN trade_polymarket_markets.category IS '市场分类，如 Politics/Crypto/Economics/Sports';
COMMENT ON COLUMN trade_polymarket_markets.last_synced_at IS '最后同步Polymarket数据的时间';
COMMENT ON COLUMN trade_polymarket_markets.payload_json IS '原始市场数据JSON';
COMMENT ON COLUMN trade_polymarket_markets.created_at IS '记录创建时间';
COMMENT ON COLUMN trade_polymarket_markets.updated_at IS '记录更新时间';

COMMENT ON TABLE trade_polymarket_ai_analysis IS 'Polymarket AI分析表 — 存储AI对Polymarket市场的分析预测（偏差信号）';
COMMENT ON COLUMN trade_polymarket_ai_analysis.id IS '主键，自增序列';
COMMENT ON COLUMN trade_polymarket_ai_analysis.market_id IS 'Polymarket市场ID，NOT NULL';
COMMENT ON COLUMN trade_polymarket_ai_analysis.user_id IS '分析发起用户ID（INTEGER）';
COMMENT ON COLUMN trade_polymarket_ai_analysis.ai_predicted_probability IS 'AI预测概率（NUMERIC(10,4)）';
COMMENT ON COLUMN trade_polymarket_ai_analysis.market_probability IS '市场当前概率（NUMERIC(10,4)）';
COMMENT ON COLUMN trade_polymarket_ai_analysis.divergence IS '偏差值（NUMERIC(10,4)），AI预测-市场概率，正值表示AI认为概率被低估';
COMMENT ON COLUMN trade_polymarket_ai_analysis.recommendation IS '交易建议：buy_yes/buy_no/hold';
COMMENT ON COLUMN trade_polymarket_ai_analysis.confidence_score IS 'AI置信度评分（NUMERIC(10,4)）';
COMMENT ON COLUMN trade_polymarket_ai_analysis.opportunity_score IS '机会评分（NUMERIC(10,4)），综合偏差和置信度';
COMMENT ON COLUMN trade_polymarket_ai_analysis.reasoning IS 'AI推理理由文本';
COMMENT ON COLUMN trade_polymarket_ai_analysis.key_factors IS '关键影响因素JSON数组';
COMMENT ON COLUMN trade_polymarket_ai_analysis.related_assets IS '相关资产列表（TEXT[]），如 [BTC,ETH]';
COMMENT ON COLUMN trade_polymarket_ai_analysis.created_at IS '分析发生时间';

COMMENT ON TABLE trade_polymarket_opportunities IS 'Polymarket机会表 — 存储检测到的高置信度偏差交易机会';
COMMENT ON COLUMN trade_polymarket_opportunities.id IS '主键，自增序列';
COMMENT ON COLUMN trade_polymarket_opportunities.market_id IS 'Polymarket市场ID，NOT NULL';
COMMENT ON COLUMN trade_polymarket_opportunities.asset IS '相关交易资产，NOT NULL（如 BTC/ETH）';
COMMENT ON COLUMN trade_polymarket_opportunities.market IS '所属市场类别（如 Crypto）';
COMMENT ON COLUMN trade_polymarket_opportunities.signal IS '交易信号：buy_yes/buy_no';
COMMENT ON COLUMN trade_polymarket_opportunities.confidence IS '机会置信度（NUMERIC(10,4)）';
COMMENT ON COLUMN trade_polymarket_opportunities.reasoning IS '机会判断理由';
COMMENT ON COLUMN trade_polymarket_opportunities.payload_json IS '扩展数据JSON';
COMMENT ON COLUMN trade_polymarket_opportunities.created_at IS '机会发现时间';
COMMENT ON COLUMN trade_polymarket_opportunities.updated_at IS '记录更新时间';
