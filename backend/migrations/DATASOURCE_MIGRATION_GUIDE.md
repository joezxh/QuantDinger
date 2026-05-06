# 数据源配置迁移指南

## 概述

QuantDinger 现在将所有数据源配置（API地址、API密钥、限流配置等）统一迁移到数据库管理，替代原来的 `.env` 环境变量方式。

## 迁移内容

### 已迁移到数据库的配置

以下配置项已从 `.env` 文件迁移到数据库表：

| 数据源 | 原环境变量 | 数据库 source_code |
|--------|-----------|-------------------|
| Finnhub 美股 | FINNHUB_API_KEY | us_stock_finnhub |
| Tiingo 美股 | TIINGO_API_KEY | us_stock_tiingo |
| Twelve Data | TWELVE_DATA_API_KEY | twelve_data |
| Coinglass | COINGLASS_API_KEY | crypto_coinglass |
| CryptoQuant | CRYPTOQUANT_API_KEY | crypto_quant |
| Adanos 情绪 | ADANOS_API_KEY | adanos_sentiment |

### 保留在 `.env` 的配置

以下配置仍保留在 `.env` 文件中（全局配置，不特定于某个数据源）：

- `DATA_SOURCE_TIMEOUT` - 全局超时配置
- `DATA_SOURCE_RETRY` - 全局重试次数
- `DATA_SOURCE_RETRY_BACKOFF` - 全局重试退避系数
- `CCXT_DEFAULT_EXCHANGE` - CCXT默认交易所

## 初始化步骤

### 1. 运行数据库迁移脚本

```bash
# 连接到 PostgreSQL 数据库
cd backend

# 运行初始化脚本
psql -U postgres -d quantdinger -f migrations/data_source_init.sql
```

### 2. 配置 API Key

运行初始化脚本后，需要在数据库中配置实际的 API Key：

```sql
-- 示例：配置 Finnhub API Key
INSERT INTO data_api_keys (
    source_config_id,
    key_type,
    key_alias,
    encrypted_key_value,
    key_hint,
    status
)
SELECT
    id,
    'public',
    'Finnhub API Key #1',
    -- 需要使用 CryptoUtils.encrypt() 加密密钥
    'ENCRYPTED_KEY_VALUE_HERE',
    '****d5ure',
    'active'
FROM data_data_source_configs
WHERE source_code = 'us_stock_finnhub'
ON CONFLICT DO NOTHING;
```

### 3. 使用 Python 脚本加密 API Key

推荐使用以下 Python 脚本加密 API Key：

```python
from app.utils.crypto import CryptoUtils
from app import create_app, db
from app.models.data_source_meta import DataSourceConfig, ApiKey

app = create_app()
with app.app_context():
    # 加密 API Key
    encrypted = CryptoUtils.encrypt('your_api_key_here')
    
    # 查找数据源配置
    source = db.session.query(DataSourceConfig).filter(
        DataSourceConfig.source_code == 'us_stock_finnhub'
    ).first()
    
    # 插入 API Key
    api_key = ApiKey(
        source_config_id=source.id,
        key_type='public',
        key_alias='Finnhub API Key #1',
        encrypted_key_value=encrypted,
        key_hint='****d5ure',
        status='active'
    )
    
    db.session.add(api_key)
    db.session.commit()
```

## 配置加载逻辑

### 优先级

1. **数据库配置** (优先)
   - 从 `data_data_source_configs` 表读取基本配置
   - 从 `data_rate_limit_configs` 表读取限流配置
   - 从 `data_api_keys` 表读取加密的 API Key

2. **环境变量** (回退)
   - 如果数据库中没有配置，回退到环境变量
   - 保持向后兼容性

### 代码示例

```python
from app.data_sources.config_loader import get_config_loader
from app import db

# 加载数据源配置
loader = get_config_loader(db.session)
config = loader.load_source_config('us_stock_finnhub')

# 获取 API Key
api_key = loader.get_api_key('us_stock_finnhub', key_type='public')

# 加载所有启用的数据源
all_sources = loader.load_all_enabled_sources()
crypto_sources = loader.load_all_enabled_sources(category='Crypto')
```

## 限流配置

限流配置存储在 `data_rate_limit_configs` 表中，支持以下策略：

- **token_bucket** - 令牌桶算法（推荐）
- **sliding_window** - 滑动窗口
- **fixed_window** - 固定窗口
- **adaptive** - 自适应限流

### 限流参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| rate | 每周期请求数 | 60 |
| period | 周期长度（秒） | 60 |
| burst | 突发容量 | rate |
| max_concurrent | 最大并发数 | 10 |
| enable_adaptive | 启用自适应 | false |
| reduce_rate_on_error | 错误时降速 | true |
| error_threshold | 触发降速的错误数 | 5 |

## 数据源清单

### 加密货币 (Crypto)
- crypto_ccxt - CCXT 加密货币交易所
- crypto_coingecko - CoinGecko API
- crypto_defillama - DeFi Llama
- crypto_coinglass - Coinglass
- crypto_quant - CryptoQuant

### A股 (CNStock)
- cn_stock_akshare - AKShare A股数据
- cn_stock_tushare - Tushare 专业A股数据
- cn_stock_baostock - BaoStock 免费A股数据

### 美股 (USStock)
- us_stock_yfinance - Yahoo Finance 美股
- us_stock_finnhub - Finnhub 美股数据
- us_stock_financial_datasets - Financial Datasets API
- market_alphavantage - Alpha Vantage
- us_stock_tiingo - Tiingo 美股数据
- twelve_data - Twelve Data

### 期货 (Futures)
- futures_akshare - AKShare 期货数据
- futures_cftc - CFTC Commitment of Traders
- futures_cboe - CBOE Volatility Indices

### 宏观经济 (Macro)
- macro_fred - FRED (Federal Reserve Economic Data)
- macro_bls - BLS (Bureau of Labor Statistics)
- macro_worldbank - World Bank Open Data
- macro_bea - BEA (Bureau of Economic Analysis)
- macro_imf - IMF (International Monetary Fund)
- macro_oecd - OECD Statistics
- macro_ecb - ECB (European Central Bank)
- macro_eia - EIA (U.S. Energy Information Administration)
- macro_wto - WTO (World Trade Organization)

### 基本面 (Fundamentals)
- fundamentals_simfin - SimFin 离线基本面数据
- fundamentals_fmp - FMP (Financial Modeling Prep)
- fundamentals_sec - SEC EDGAR

### 新闻 (News)
- news_google - Google News RSS
- news_eastmoney - 东方财富新闻
- news_newsapi - NewsAPI

### 情绪分析 (Alternative)
- adanos_sentiment - Adanos Market Sentiment

## 常见问题

### Q: 迁移后系统启动失败？

A: 确保已运行 `migrations/data_source_init.sql` 初始化数据库配置。

### Q: 如何修改数据源的 API Key？

A: 使用 Python 脚本更新 `data_api_keys` 表中的 `encrypted_key_value` 字段。

### Q: 如何调整限流参数？

A: 直接更新 `data_rate_limit_configs` 表中的对应字段，修改实时生效。

### Q: 是否还支持环境变量方式？

A: 支持。如果数据库中没有配置，系统会回退到环境变量读取，保持向后兼容。

## 注意事项

1. **API Key 加密**：所有 API Key 在数据库中都是 AES-256-GCM 加密存储
2. **实时生效**：修改数据库配置后，新请求会立即使用新配置
3. **多 Key 负载均衡**：一个数据源可以配置多个 API Key，系统会自动负载均衡
4. **健康监控**：系统会记录每个 API Key 的使用统计和健康状态

## 后续优化建议

1. 添加前端管理界面，可视化配置数据源
2. 实现配置热加载，无需重启服务
3. 添加配置版本管理，支持回滚
4. 集成配置审计日志
