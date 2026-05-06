-- QuantDinger Data Source Initialization Script
-- Generated from comprehensive analysis of QuantDinger, FinceptTerminal, TradingAgents-CN, and Dexter projects

-- Clear existing data (for fresh initialization)
TRUNCATE TABLE data_data_source_configs CASCADE;
TRUNCATE TABLE data_api_keys CASCADE;

-- Insert DataSourceConfig records

-- Crypto Data Sources
INSERT INTO data_data_source_configs (
    source_code, 
    source_name, 
    layer, 
    market_categories, 
    enabled, 
    load_balance_strategy, 
    config_json,
    notes
) VALUES (
    'crypto_ccxt',
    'CCXT Cryptocurrency Exchange',
    'data_source',
    ARRAY['Crypto'],
    true,
    'round_robin',
    '{
        "api_key_env": "CCXT_API_KEY",
        "api_key_required": false,
        "base_url": "https://api.coinbase.com/api/v2/",
        "timeout_sec": 10,
        "retry_count": 3,
        "default_exchange": "coinbase",
        "rate_limit_per_min": 8,
        "proxy_supported": true
    }',
    'Primary crypto data source using CCXT library'
), (
    'crypto_coingecko',
    'CoinGecko API',
    'data_source',
    ARRAY['Crypto'],
    true,
    'health_first',
    '{
        "api_key_env": "COINGECKO_API_KEY",
        "api_key_required": false,
        "base_url": "https://api.coingecko.com/api/v3/",
        "timeout_sec": 15,
        "retry_count": 2,
        "rate_limit_per_min": 50,
        "proxy_supported": false
    }',
    'Free cryptocurrency data API - no API key required'
), (
    'crypto_coinmarketcap',
    'CoinMarketCap API',
    'data_source',
    ARRAY['Crypto'],
    true,
    'weighted',
    '{
        "api_key_env": "COINMARKETCAP_API_KEY",
        "api_key_required": true,
        "base_url": "https://pro-api.coinmarketcap.com/v1/",
        "timeout_sec": 20,
        "retry_count": 2,
        "rate_limit_per_min": 100,
        "proxy_supported": true
    }',
    'Professional cryptocurrency data API'
), (
    'crypto_polygon',
    'Polygon.io Crypto API',
    'data_source',
    ARRAY['Crypto'],
    true,
    'round_robin',
    '{
        "api_key_env": "POLYGON_API_KEY",
        "api_key_required": true,
        "base_url": "https://api.polygon.io/v2/",
        "timeout_sec": 15,
        "retry_count": 2,
        "rate_limit_per_min": 5,
        "proxy_supported": true
    }',
    'Real-time and historical crypto tick data'
);

-- US Stock Data Sources
INSERT INTO data_data_source_configs (
    source_code, 
    source_name, 
    layer, 
    market_categories, 
    enabled, 
    load_balance_strategy, 
    config_json,
    notes
) VALUES (
    'usstock_yfinance',
    'Yahoo Finance',
    'data_source',
    ARRAY['USStock'],
    true,
    'health_first',
    '{
        "api_key_env": "YFINANCE_API_KEY",
        "api_key_required": false,
        "base_url": "https://query1.finance.yahoo.com/v7/finance/",
        "timeout_sec": 30,
        "retry_count": 3,
        "rate_limit_per_min": 100,
        "proxy_supported": false
    }',
    'Free stock market data - no API key required'
), (
    'usstock_finnhub',
    'Finnhub API',
    'data_source',
    ARRAY['USStock'],
    true,
    'weighted',
    '{
        "api_key_env": "FINNHUB_API_KEY",
        "api_key_required": true,
        "base_url": "https://finnhub.io/api/v1/",
        "timeout_sec": 10,
        "retry_count": 2,
        "rate_limit_per_min": 60,
        "proxy_supported": true
    }',
    'Real-time stock, forex, and crypto data'
), (
    'usstock_alpha_vantage',
    'Alpha Vantage API',
    'data_source',
    ARRAY['USStock'],
    true,
    'round_robin',
    '{
        "api_key_env": "ALPHA_VANTAGE_API_KEY",
        "api_key_required": true,
        "base_url": "https://www.alphavantage.co/query/",
        "timeout_sec": 20,
        "retry_count": 2,
        "rate_limit_per_min": 5,
        "proxy_supported": false
    }',
    'Stock, forex, and crypto market data API'
), (
    'usstock_iex_cloud',
    'IEX Cloud API',
    'data_source',
    ARRAY['USStock'],
    true,
    'health_first',
    '{
        "api_key_env": "IEX_CLOUD_TOKEN",
        "api_key_required": true,
        "base_url": "https://cloud.iexapis.com/stable/",
        "timeout_sec": 15,
        "retry_count": 2,
        "rate_limit_per_min": 1000,
        "proxy_supported": true
    }',
    'Financial data from IEX Exchange'
);

-- China Stock Data Sources
INSERT INTO data_data_source_configs (
    source_code, 
    source_name, 
    layer, 
    market_categories, 
    enabled, 
    load_balance_strategy, 
    config_json,
    notes
) VALUES (
    'cnstock_tushare',
    'Tushare API',
    'data_source',
    ARRAY['CNStock'],
    true,
    'health_first',
    '{
        "api_key_env": "TUSHARE_TOKEN",
        "api_key_required": false,
        "base_url": "https://tushare.pro/",
        "timeout_sec": 30,
        "retry_count": 3,
        "rate_limit_per_min": 200,
        "proxy_supported": false
    }',
    'Chinese stock data interface - free tier available'
), (
    'cnstock_akshare',
    'AKShare API',
    'data_source',
    ARRAY['CNStock'],
    true,
    'round_robin',
    '{
        "api_key_env": "AKSHARE_API_KEY",
        "api_key_required": false,
        "base_url": "https://akshare.akfamily.xyz/",
        "timeout_sec": 45,
        "retry_count": 3,
        "rate_limit_per_min": 100,
        "proxy_supported": false
    }',
    'Free financial data interface for Chinese markets'
), (
    'cnstock_twelve_data',
    'Twelve Data API',
    'data_source',
    ARRAY['CNStock'],
    true,
    'weighted',
    '{
        "api_key_env": "TWELVE_DATA_API_KEY",
        "api_key_required": true,
        "base_url": "https://api.twelvedata.com/",
        "timeout_sec": 20,
        "retry_count": 2,
        "rate_limit_per_min": 8,
        "proxy_supported": true
    }',
    'Real-time and historical financial data'
);

-- Forex Data Sources
INSERT INTO data_data_source_configs (
    source_code, 
    source_name, 
    layer, 
    market_categories, 
    enabled, 
    load_balance_strategy, 
    config_json,
    notes
) VALUES (
    'forex_twelve_data',
    'Twelve Data Forex API',
    'data_source',
    ARRAY['Forex'],
    true,
    'health_first',
    '{
        "api_key_env": "TWELVE_DATA_API_KEY",
        "api_key_required": true,
        "base_url": "https://api.twelvedata.com/",
        "timeout_sec": 20,
        "retry_count": 2,
        "rate_limit_per_min": 8,
        "proxy_supported": true
    }',
    'Real-time and historical forex data'
), (
    'forex_tiingo',
    'Tiingo Forex API',
    'data_source',
    ARRAY['Forex'],
    true,
    'round_robin',
    '{
        "api_key_env": "TIINGO_API_KEY",
        "api_key_required": true,
        "base_url": "https://api.tiingo.com/tiingo/",
        "timeout_sec": 15,
        "retry_count": 2,
        "rate_limit_per_min": 500,
        "proxy_supported": true
    }',
    'Stock, crypto, and news data'
), (
    'forex_yfinance',
    'Yahoo Finance Forex',
    'data_source',
    ARRAY['Forex'],
    true,
    'health_first',
    '{
        "api_key_env": "YFINANCE_API_KEY",
        "api_key_required": false,
        "base_url": "https://query1.finance.yahoo.com/v7/finance/",
        "timeout_sec": 30,
        "retry_count": 3,
        "rate_limit_per_min": 100,
        "proxy_supported": false
    }',
    'Free forex data - no API key required'
);

-- Futures Data Sources
INSERT INTO data_data_source_configs (
    source_code, 
    source_name, 
    layer, 
    market_categories, 
    enabled, 
    load_balance_strategy, 
    config_json,
    notes
) VALUES (
    'futures_twelve_data',
    'Twelve Data Futures API',
    'data_source',
    ARRAY['Futures'],
    true,
    'health_first',
    '{
        "api_key_env": "TWELVE_DATA_API_KEY",
        "api_key_required": true,
        "base_url": "https://api.twelvedata.com/",
        "timeout_sec": 20,
        "retry_count": 2,
        "rate_limit_per_min": 8,
        "proxy_supported": true
    }',
    'Traditional futures data'
), (
    'futures_yfinance',
    'Yahoo Finance Futures',
    'data_source',
    ARRAY['Futures'],
    true,
    'round_robin',
    '{
        "api_key_env": "YFINANCE_API_KEY",
        "api_key_required": false,
        "base_url": "https://query1.finance.yahoo.com/v7/finance/",
        "timeout_sec": 30,
        "retry_count": 3,
        "rate_limit_per_min": 100,
        "proxy_supported": false
    }',
    'Free futures data - no API key required'
), (
    'futures_crypto_ccxt',
    'CCXT Crypto Futures',
    'data_source',
    ARRAY['Futures'],
    true,
    'weighted',
    '{
        "api_key_env": "CCXT_API_KEY",
        "api_key_required": false,
        "base_url": "https://api.binance.com/",
        "timeout_sec": 10,
        "retry_count": 3,
        "default_exchange": "binance",
        "rate_limit_per_min": 8,
        "proxy_supported": true
    }',
    'Cryptocurrency futures data'
);

-- Market Data Providers (Aggregated Data)
INSERT INTO data_data_source_configs (
    source_code, 
    source_name, 
    layer, 
    market_categories, 
    enabled, 
    load_balance_strategy, 
    config_json,
    notes
) VALUES (
    'market_crypto',
    'Crypto Market Providers',
    'data_provider',
    ARRAY['Crypto'],
    true,
    'health_first',
    '{
        "api_key_env": "CRYPTO_PROVIDER_KEYS",
        "api_key_required": false,
        "base_url": "https://api.crypto-providers.com/",
        "timeout_sec": 15,
        "retry_count": 2,
        "rate_limit_per_min": 100,
        "proxy_supported": true
    }',
    'Crypto market overview and heatmap'
), (
    'market_forex',
    'Forex Market Providers',
    'data_provider',
    ARRAY['Forex'],
    true,
    'round_robin',
    '{
        "api_key_env": "FOREX_PROVIDER_KEYS",
        "api_key_required": false,
        "base_url": "https://api.forex-providers.com/",
        "timeout_sec": 15,
        "retry_count": 2,
        "rate_limit_per_min": 100,
        "proxy_supported": true
    }',
    'Forex market overview'
), (
    'market_indices',
    'Global Indices Providers',
    'data_provider',
    ARRAY['Indices'],
    true,
    'health_first',
    '{
        "api_key_env": "INDICES_PROVIDER_KEYS",
        "api_key_required": false,
        "base_url": "https://api.indices-providers.com/",
        "timeout_sec": 15,
        "retry_count": 2,
        "rate_limit_per_min": 100,
        "proxy_supported": true
    }',
    'Global stock indices data'
), (
    'market_news',
    'Financial News Providers',
    'data_provider',
    ARRAY['News'],
    true,
    'weighted',
    '{
        "api_key_env": "NEWS_PROVIDER_KEYS",
        "api_key_required": false,
        "base_url": "https://api.news-providers.com/",
        "timeout_sec": 20,
        "retry_count": 2,
        "rate_limit_per_min": 50,
        "proxy_supported": true
    }',
    'Financial news and economic calendar'
);

-- Insert API Key records (sample keys - these would be encrypted in production)
INSERT INTO data_api_keys (
    source_config_id,
    key_type,
    key_alias,
    encrypted_key_value,
    key_hint,
    status,
    weight,
    consecutive_errors,
    daily_call_limit,
    current_daily_calls,
    total_calls
) VALUES (
    (SELECT id FROM data_data_source_configs WHERE source_code = 'crypto_ccxt'),
    'public',
    'Default Coinbase Key',
    'encrypted_default_key_for_coinbase',
    '****abcd',
    'active',
    1,
    0,
    0,
    0,
    0
), (
    (SELECT id FROM data_data_source_configs WHERE source_code = 'usstock_finnhub'),
    'public',
    'Default Finnhub Key',
    'encrypted_default_key_for_finnhub',
    '****efgh',
    'active',
    1,
    0,
    0,
    0,
    0
), (
    (SELECT id FROM data_data_source_configs WHERE source_code = 'cnstock_tushare'),
    'public',
    'Default Tushare Key',
    'encrypted_default_key_for_tushare',
    '****ijkl',
    'active',
    1,
    0,
    0,
    0,
    0
), (
    (SELECT id FROM data_data_source_configs WHERE source_code = 'forex_twelve_data'),
    'public',
    'Default Twelve Data Key',
    'encrypted_default_key_for_twelve',
    '****mnop',
    'active',
    1,
    0,
    0,
    0,
    0
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_data_source_configs_source_code ON data_data_source_configs(source_code);
CREATE INDEX IF NOT EXISTS idx_data_source_configs_layer ON data_data_source_configs(layer);
CREATE INDEX IF NOT EXISTS idx_data_api_keys_source_config_id ON data_api_keys(source_config_id);
CREATE INDEX IF NOT EXISTS idx_data_api_keys_status ON data_api_keys(status);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON data_data_source_configs TO quantdinger_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON data_api_keys TO quantdinger_app;
