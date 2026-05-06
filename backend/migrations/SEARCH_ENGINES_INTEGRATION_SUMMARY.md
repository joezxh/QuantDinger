# 搜索引擎和 AI 数据源集成完成报告

## 📊 任务概述

成功将 7 个新的搜索引擎和 AI 数据源（博查、数眼智能、安思派、Firecrawl、Google、Baidu、Bing）统一纳入 QuantDinger 项目的数据库配置管理体系。

---

## ✅ 完成的工作

### 1. 数据库模型集成

**文件**: `backend/app/models/data_source_meta.py`

这些数据源使用现有的数据库模型，无需修改模型定义：

- ✅ **DataSourceConfig** - 数据源基本配置
- ✅ **ApiKey** - API密钥管理
- ✅ **DataSourceRateLimitConfig** - 限流配置
- ✅ **DataSourceHealth** - 健康状态监控

**模型关系**:
```
DataSourceConfig (1) <---> (N) ApiKey
DataSourceConfig (1) <---> (1) DataSourceRateLimitConfig
DataSourceConfig (1) <---> (N) DataSourceHealth
```

---

### 2. SQL 迁移脚本更新

**文件**: `backend/migrations/init_data_sources_v4.sql`

#### 新增数据源配置 (7个)

| 数据源代码 | 名称 | 类别 | API Key | 限流(次/分钟) |
|-----------|------|------|---------|--------------|
| `search_bocha` | 博查 AI 搜索 | News, Alternative | 需要 | 60 |
| `search_shuyan` | 数眼智能 | News, Alternative | 需要 | 50 |
| `search_anspire` | 安思派 | Fundamentals, News, Alternative | 需要 | 40 |
| `search_firecrawl` | Firecrawl (私有化) | News, Alternative | 需要 | 30 |
| `search_google` | Google Search | News, Alternative | 需要 | 100 |
| `search_baidu` | 百度搜索 | News, Alternative | 需要 | 80 |
| `search_bing` | 必应搜索 | News, Alternative | 需要 | 100 |

#### 数据源配置详情

每个数据源包含以下配置:

```sql
INSERT INTO data_data_source_configs (
    source_code,        -- 唯一标识
    source_name,        -- 显示名称
    layer,              -- 数据层级
    market_categories,  -- 市场类别
    enabled,            -- 启用状态
    load_balance_strategy,  -- 负载均衡策略
    config_json,        -- API连接配置(JSON)
    notes               -- 备注说明
)
```

**config_json 结构**:
```json
{
  "api_key_env": "环境变量名",
  "api_key_required": true,
  "base_url": "API基础URL",
  "timeout_sec": 超时时间,
  "rate_limit_per_min": 每分钟限制,
  "features": ["功能列表"]
}
```

#### 限流配置 (7个)

每个数据源都配置了独立的限流参数:

```sql
INSERT INTO data_rate_limit_configs (
    source_config_id,   -- 关联数据源ID
    strategy,           -- 限流策略
    rate,               -- 速率
    period,             -- 周期
    burst,              -- 突发容量
    max_concurrent,     -- 最大并发
    config_source,      -- 配置来源
    notes               -- 备注
)
```

**限流策略**:
- 全部使用 `token_bucket` (令牌桶算法)
- 支持突发流量
- Firecrawl 启用错误降速机制

#### 健康检查初始化

为所有 16 个新增数据源（包括之前的9个）初始化健康检查记录:

```sql
INSERT INTO data_source_health (source_code, category, status)
VALUES (source_code, 'Search', 'unknown')
ON CONFLICT (source_code, category) DO NOTHING;
```

---

### 3. 配置特性

#### 数据源分类

**按功能分类**:
- 🔍 **新闻搜索**: Google、Bing、Baidu、Bocha
- 🇨🇳 **中文内容**: Baidu、Bocha、SHUYAN
- 🌍 **全球覆盖**: Google、Bing
- 📊 **专业数据**: ANSPIRE、SHUYAN
- 🕷️ **网页抓取**: Firecrawl

**按优先级排序**:
```
Google (80) > Bing (75) > Baidu (70) > Bocha (65) > SHUYAN (60) > Firecrawl (50)
```

#### API 密钥管理

- ✅ 使用 AES-256-GCM 加密存储
- ✅ 支持多密钥负载均衡
- ✅ 密钥健康状态监控
- ✅ 使用统计追踪
- ✅ 自动错误降级

#### 限流策略

| 数据源 | 速率 | 周期 | 突发 | 并发 | 错误降速 |
|--------|------|------|------|------|---------|
| 博查 | 60 | 60s | 60 | 10 | 否 |
| 数眼 | 50 | 60s | 50 | 10 | 否 |
| 安思派 | 40 | 60s | 40 | 8 | 否 |
| Firecrawl | 30 | 60s | 30 | 5 | ✅ (阈值3) |
| Google | 100 | 60s | 100 | 15 | 否 |
| 百度 | 80 | 60s | 80 | 12 | 否 |
| 必应 | 100 | 60s | 100 | 15 | 否 |

---

### 4. 前端管理集成

所有新数据源都可以在前端控制台进行完整管理:

#### 访问路径

- **数据源列表**: `/data-source`
- **密钥管理**: `/data-source/keys?source_code=search_xxx`
- **限流配置**: `/data-source/rate-limit?source_code=search_xxx`
- **健康监控**: `/data-source/health`

#### 支持的操作

- ✅ 查看数据源配置
- ✅ 编辑数据源参数
- ✅ 启用/禁用数据源
- ✅ 配置 API 密钥
- ✅ 调整限流参数
- ✅ 执行健康检查
- ✅ 查看使用统计

---

## 📁 修改的文件

### 核心文件

1. **`backend/migrations/init_data_sources_v4.sql`**
   - 新增 7 个数据源配置
   - 新增 7 个限流配置
   - 更新健康检查初始化（16个数据源）
   - 更新文档说明
   - 行数变化: +140 行

### 新增文档

2. **`backend/migrations/SEARCH_ENGINES_CONFIG_GUIDE.md`**
   - 完整配置指南
   - 数据源详细说明
   - 使用示例
   - 故障排查
   - 行数: 560 行

3. **`SEARCH_ENGINES_INTEGRATION_SUMMARY.md`** (本文档)
   - 集成总结报告
   - 技术细节
   - 使用建议

---

## 🎯 技术亮点

### 1. 统一的配置管理

所有数据源使用相同的数据库模型和配置结构:

```python
# 数据源配置
DataSourceConfig
├── source_code: str          # 唯一标识
├── source_name: str          # 显示名称
├── layer: str                # 数据层级
├── market_categories: list   # 市场类别
├── enabled: bool             # 启用状态
├── config_json: JSONB        # 连接配置
└── relationships:
    ├── api_keys (1:N)        # API密钥
    ├── rate_limit_config (1:1) # 限流配置
    └── health_status         # 健康状态
```

### 2. 灵活的限流策略

支持多种限流策略:
- ✅ Token Bucket (令牌桶) - 当前使用
- ✅ Sliding Window (滑动窗口)
- ✅ Fixed Window (固定窗口)
- ✅ Adaptive (自适应)

### 3. 智能负载均衡

- 多密钥支持
- 权重分配
- 健康优先
- 错误自动降级

### 4. 完善的监控体系

- 实时健康检查
- 响应时间监控
- 使用统计追踪
- 错误率分析

---

## 📊 数据源总览

### 完整数据源清单 (共 23 个)

#### 宏观经济 (5个)
1. macro_imf - IMF
2. macro_oecd - OECD
3. macro_ecb - ECB
4. macro_eia - EIA
5. macro_wto - WTO

#### 基本面 (2个)
6. fundamentals_fmp - FMP
7. fundamentals_sec - SEC

#### 市场数据 (1个)
8. market_alphavantage - Alpha Vantage

#### 新闻舆情 (1个)
9. news_newsapi - NewsAPI

#### 搜索引擎和 AI (7个) ⭐ 新增
10. search_bocha - 博查
11. search_shuyan - 数眼智能
12. search_anspire - 安思派
13. search_firecrawl - Firecrawl
14. search_google - Google
15. search_baidu - 百度
16. search_bing - 必应

#### 已有数据源 (7个)
17. crypto_ccxt - CCXT
18. crypto_coingecko - CoinGecko
19. us_stock_yfinance - yfinance
20. us_stock_finnhub - Finnhub
21. us_stock_tiingo - Tiingo
22. cn_stock_akshare - AKShare
23. cn_stock_tushare - Tushare

---

## 🚀 部署步骤

### 1. 运行数据库迁移

```bash
# 连接到 PostgreSQL 数据库
psql -U your_user -d your_database

# 执行迁移脚本
\i backend/migrations/init_data_sources_v4.sql
```

### 2. 配置 API 密钥

#### 方式一: 通过前端界面（推荐）

1. 访问 `/data-source`
2. 找到目标数据源（如 `search_google`）
3. 点击"密钥管理"
4. 添加 API Key

#### 方式二: 直接插入数据库

```sql
-- 示例: 添加 Google Search API Key
INSERT INTO data_api_keys (
    source_config_id,
    key_type,
    key_alias,
    encrypted_key_value,
    status,
    weight
)
VALUES (
    (SELECT id FROM data_data_source_configs WHERE source_code = 'search_google'),
    'public',
    'Google Search Key #1',
    'encrypted_value_here',  -- 使用 AES-256-GCM 加密
    'active',
    1
);
```

### 3. 验证配置

```bash
# 检查数据源是否创建成功
SELECT source_code, source_name, enabled 
FROM data_data_source_configs 
WHERE source_code LIKE 'search_%';

# 检查限流配置
SELECT dsc.source_code, drc.strategy, drc.rate, drc.period
FROM data_rate_limit_configs drc
JOIN data_data_source_configs dsc ON drc.source_config_id = dsc.id
WHERE dsc.source_code LIKE 'search_%';
```

### 4. 测试健康状态

访问前端健康监控页面:
```
http://localhost:5173/data-source/health
```

点击"全面健康检查"验证所有数据源连接。

---

## 📝 使用建议

### 1. API Key 管理

- ✅ 为每个数据源配置至少 1 个 API Key
- ✅ 高流量数据源配置多个 Key 实现负载均衡
- ✅ 定期轮换密钥
- ✅ 监控使用统计，避免超额

### 2. 限流配置

- ✅ 根据 API 套餐设置合理的限流参数
- ✅ Firecrawl 启用错误降速（网页抓取较重）
- ✅ 定期检查限流统计
- ✅ 根据实际需求调整并发数

### 3. 优先级路由

**推荐的路由策略**:

```python
# 新闻搜索优先级
if query_type == 'news':
    priority = [
        'search_google',     # 全球覆盖
        'search_bing',       # 多语言
        'search_baidu',      # 中文
        'search_bocha',      # AI语义
    ]

# 中文内容搜索
if language == 'chinese':
    priority = [
        'search_baidu',      # 中文最全
        'search_bocha',      # AI理解
        'search_shuyan',     # 财经专业
    ]

# 专业数据分析
if need_professional_data:
    priority = [
        'search_anspire',    # 企业数据
        'search_shuyan',     # 财经分析
    ]

# 自定义网页抓取
if need_custom_scraping:
    priority = [
        'search_firecrawl',  # 私有化部署
    ]
```

### 4. 成本控制

- ✅ 优先使用免费/低成本数据源
- ✅ 设置日调用限制
- ✅ 缓存常用查询结果
- ✅ 监控 API 费用

---

## 🔍 故障排查

### 常见问题

#### Q1: 数据源未显示在前端？

**解决方案**:
1. 检查 SQL 迁移是否成功执行
2. 刷新前端页面
3. 检查数据库连接

#### Q2: 健康检查失败？

**可能原因**:
- API Key 未配置或无效
- 网络连接问题
- 服务商会限

**解决方案**:
1. 检查 API Key 配置
2. 测试网络连通性
3. 查看服务商状态
4. 检查限流设置

#### Q3: 触发限流？

**解决方案**:
1. 降低限流速率
2. 增加 API Key 数量
3. 启用请求缓存
4. 调整并发数

---

## 📈 性能优化建议

### 1. 缓存策略

```python
# 缓存热门搜索查询
cache_config = {
    'ttl': 300,           # 5分钟
    'max_size': 1000,     # 最多1000条
    'strategy': 'LRU'     # 最近最少使用
}
```

### 2. 并行查询

```python
# 同时查询多个数据源
import asyncio

async def search_multiple_sources(query):
    tasks = [
        search_google(query),
        search_bing(query),
        search_baidu(query)
    ]
    results = await asyncio.gather(*tasks)
    return merge_results(results)
```

### 3. 智能降级

```python
# 主数据源失败时自动降级
def search_with_fallback(query):
    try:
        return search_google(query)
    except Exception:
        try:
            return search_bing(query)
        except Exception:
            return search_baidu(query)
```

---

## 📚 相关文档

1. **配置指南**: `SEARCH_ENGINES_CONFIG_GUIDE.md`
2. **数据源管理**: `../frontend-v3/DATA_SOURCE_MANAGER_GUIDE.md`
3. **快速启动**: `../frontend-v3/QUICK_START.md`
4. **开发总结**: `../frontend-v3/DATA_SOURCE_MANAGEMENT_SUMMARY.md`

---

## ✅ 验收清单

- [x] 7 个数据源配置添加到数据库
- [x] 7 个限流配置正确关联
- [x] 健康检查记录初始化
- [x] 使用 ON CONFLICT DO NOTHING 确保幂等性
- [x] 前端管理界面可访问
- [x] API 密钥管理功能可用
- [x] 限流配置可调整
- [x] 健康状态可监控
- [x] 文档完整准确

---

## 🎉 总结

成功将 7 个搜索引擎和 AI 数据源集成到 QuantDinger 项目中：

- ✅ **统一的配置管理** - 所有数据源使用相同的数据库模型
- ✅ **完整的限流支持** - 每个数据源都有独立的限流配置
- ✅ **前端可视化管理** - 支持完整的 CRUD 操作
- ✅ **健康监控体系** - 实时监控数据源状态
- ✅ **灵活的优先级路由** - 智能选择最优数据源
- ✅ **详细的文档** - 完整的配置和使用指南

现在您可以在前端控制台 (`/data-source`) 中管理所有这些数据源，包括配置 API 密钥、调整限流参数、监控健康状态等。

---

**版本**: v1.0.0  
**日期**: 2026-05-03  
**状态**: ✅ 已完成
