# 多存储引擎架构 - 快速启动指南

## 📋 架构概览

本项目采用**四层存储架构**：

```
┌─────────────────────────────────────────────────────────┐
│  【热数据层】Redis (内存)                                  │
│  - 实时价格、最新新闻、会话缓存                             │
│  - TTL: 1分钟 - 24小时                                    │
├─────────────────────────────────────────────────────────┤
│  【温数据层】PostgreSQL (关系型)                            │
│  - 结构化业务数据、关系数据、事务数据                        │
│  - 保留: 1-3年                                            │
├─────────────────────────────────────────────────────────┤
│  【全文检索层】Elasticsearch (搜索引擎)                      │
│  - 新闻全文检索、公司信息搜索、聚合分析                       │
│  - 保留: 2-5年                                            │
├─────────────────────────────────────────────────────────┤
│  【冷数据层】S3/MinIO (对象存储)                            │
│  - 历史K线数据、原始API响应                                │
│  - 保留: 5-10年+                                          │
└─────────────────────────────────────────────────────────┘
```

## 🚀 快速部署

### 1. 安装依赖

```bash
pip install elasticsearch
```

### 2. 一键部署

```bash
python scripts/deploy_multi_storage.py
```

该脚本会自动完成：
- ✅ 部署 Elasticsearch 和 Kibana (Docker)
- ✅ 初始化数据库表 (Alembic)
- ✅ 创建 ES 索引

### 3. 手动部署（可选）

```bash
# 启动 Elasticsearch
docker-compose -f docker-compose.elasticsearch.yml up -d

# 等待就绪
curl http://localhost:9200/_cluster/health

# 初始化数据库
cd backend
alembic upgrade head

# 初始化 ES 索引
python scripts/init_es_indices.py
```

## 📊 数据模型

### 新增核心模型

#### 新闻数据
- `NewsArticle` - 新闻文章表

#### 宏观经济
- `MacroEconomicIndicator` - 宏观经济指标
- `EconomicCalendarEvent` - 财经日历事件

#### 市场情绪
- `SentimentMarketIndicator` - 市场情绪指标
- `SocialSentiment` - 社交舆情
- `AlternativeSocialSentiment` - 社交舆情聚合

#### 证券基础数据
- `SecurityCompany` - 上市公司基本信息
- `SecurityShareholder` - 股东信息
- `SecurityInstitutionalHolding` - 机构持仓明细
- `SecurityInsiderTrade` - 内部人交易

#### 实体去重
- `EntityFinancialInstitution` - 全局金融机构实体
- `EntityInstitutionAlias` - 机构名称别名
- `EntityIndividualShareholder` - 个人股东实体
- `EntityPolymarketUser` - Polymarket 用户实体
- `EntityPolymarketWalletLink` - 钱包关联
- `EntityRelationship` - 实体关系图
- `PolymarketTradingNetwork` - 交易关系网络

#### Polymarket 扩展
- `PolymarketAccount` - 用户账号
- `PolymarketOrder` - 市场订单
- `PolymarketPosition` - 持仓
- `PolymarketTradeHistory` - 交易历史

## 🔍 API 使用示例

### 1. 全文检索

```bash
POST http://localhost:5000/api/v1/search/fulltext
Content-Type: application/json

{
    "keyword": "BlackRock",
    "index": "news_articles",
    "symbols": ["AAPL", "GOOGL"],
    "size": 10
}
```

### 2. 公司搜索

```bash
POST http://localhost:5000/api/v1/search/company
Content-Type: application/json

{
    "keyword": "Apple",
    "sector": "Technology",
    "size": 20
}
```

### 3. 机构搜索

```bash
POST http://localhost:5000/api/v1/search/institution
Content-Type: application/json

{
    "keyword": "Vanguard",
    "institution_type": "fund"
}
```

### 4. 混合搜索

```bash
POST http://localhost:5000/api/v1/search/hybrid
Content-Type: application/json

{
    "keyword": "Tesla",
    "table": "news_articles",
    "size": 10
}
```

### 5. 聚合分析

```bash
POST http://localhost:5000/api/v1/search/aggregation
Content-Type: application/json

{
    "index": "security_companies",
    "custom_aggs": {
        "avg_market_cap": {"avg": {"field": "market_cap"}}
    }
}
```

## ⚙️ 配置

### 环境变量 (.env)

```bash
# Elasticsearch
ELASTICSEARCH_HOSTS=http://localhost:9200

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost:5432/quantdinger
```

## 📈 数据同步

### 自动同步

数据写入 PostgreSQL 后，会自动同步到 Elasticsearch：

```python
from app.services.data_sync_orchestrator import sync_orchestrator

# 单条同步
sync_orchestrator.sync_record('news_articles', 123, 'index')

# 批量同步
sync_orchestrator.bulk_sync('news_articles', [123, 124, 125])

# 增量同步
sync_orchestrator.incremental_sync('news_articles')

# 全量同步
sync_orchestrator.full_sync('news_articles', hours=24)
```

### 手动同步

```bash
# 增量同步最近5分钟数据
curl -X POST http://localhost:5000/api/v1/sync/incremental \
  -H "Content-Type: application/json" \
  -d '{"table": "news_articles"}'

# 全量同步最近24小时数据
curl -X POST http://localhost:5000/api/v1/sync/full \
  -H "Content-Type: application/json" \
  -d '{"table": "news_articles", "hours": 24}'
```

## 🎯 性能优化

### 缓存策略

```python
from app.utils.cache import cache_strategy

# 设置缓存
cache_strategy.set_cached('search_results', 'query_123', result)

# 获取缓存
result = cache_strategy.get_cached('search_results', 'query_123')

# 清除缓存
cache_strategy.invalidate_cache('search_results', 'query_123')
```

### 查询路由

系统会根据查询类型自动选择最佳存储引擎：

| 查询类型 | 存储引擎 | 延迟 |
|---------|---------|------|
| 精确查询 | PostgreSQL | 1-5ms |
| 全文检索 | Elasticsearch | 10-50ms |
| 实时数据 | Redis | <1ms |
| 聚合分析 | Elasticsearch | 50-200ms |
| 混合搜索 | ES + PG | 20-100ms |

## 📊 Kibana 可视化

访问 http://localhost:5601 可以使用 Kibana 进行：
- 数据探索
- 仪表板创建
- 日志分析
- 告警配置

## 🔧 故障排除

### Elasticsearch 未启动

```bash
# 查看日志
docker logs quantdinger-es

# 重启
docker-compose -f docker-compose.elasticsearch.yml restart
```

### 索引创建失败

```bash
# 删除旧索引
curl -X DELETE http://localhost:9200/news_articles

# 重新创建
python scripts/init_es_indices.py
```

### 同步失败

```bash
# 查看 Redis 重试队列
redis-cli LRANGE sync:retry_queue 0 -1

# 手动重试
python scripts/retry_sync.py
```

## 📚 更多信息

- [完整架构设计文档](../docs/architecture/multi-storage.md)
- [API 文档](http://localhost:5000/apidocs)
- [Elasticsearch 官方文档](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
