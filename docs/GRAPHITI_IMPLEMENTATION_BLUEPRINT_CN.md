# QuantDinger Graphiti 统一实施清单

> 版本：v1.0  
> 日期：2026-04  
> 状态：执行蓝图 / 落地清单

---

## 1. 文档目标

本清单用于把当前所有 Graphiti 改造相关方案统一收口，形成一份可直接指导研发落地的执行蓝图。

覆盖范围：
- 总体架构改造
- ORM / 迁移
- 统一采集
- Neo4j + Graphiti 基础设施
- AI 分析增强
- 股票 / 加密货币 / 预测市场三大专项图谱
- 图谱缓存、任务、因子与回测接入

本清单重点汇总：
- 实施阶段
- 模块拆分
- 依赖清单
- 数据表清单
- API 清单
- Redis Key 清单
- 图谱因子清单
- 执行顺序
- 交付物清单

---

## 2. 总体实施原则

1. **增强而非替换**：保留现有 Flask、psycopg2、市场采集器、AI 分析服务、策略回测框架，优先增量引入 ORM、Graphiti、Neo4j、Redis 图谱缓存。
2. **先结构化、后图谱化**：采集数据先入 PostgreSQL，再异步进入 Episode Builder 和 Graphiti。
3. **高频数据不直接入图**：价格快照、K线、订单簿等保留在 PostgreSQL / Redis；图谱只存事件、关系、状态变化、叙事与桥接语义。
4. **缓存优先**：AI 与分析接口先查 Redis，再查 Neo4j，必要时再走 Graphiti 时态检索。
5. **回测不直接查图数据库**：图谱特征统一落入 PostgreSQL，回测读取特征表。
6. **全链路可降级**：Graphiti / Neo4j 不可用时，主采集和 AI 主分析流程仍需可运行。

---

## 3. 实施阶段总览

## Phase 0：基础准备
- 目标：完成依赖、环境、目录、容器、配置预备
- 预估：1-2 周
- 输出：基础运行环境与配置模板

## Phase 1：ORM 与元数据底座
- 目标：建立 SQLAlchemy 基础设施和图谱元数据模型
- 预估：2-3 周
- 输出：`Base`、`Engine`、`Session`、Graph 元数据模型、Alembic 骨架

## Phase 2：统一采集与 Episode 链路
- 目标：打通 `Collector -> PostgreSQL -> EpisodeBuilder -> GraphPipeline`
- 预估：2-4 周
- 输出：采集标准对象、EpisodeBuilder、GraphPipeline、去重机制

## Phase 3：Neo4j + Graphiti 图谱基础设施
- 目标：搭建图数据库、图谱网关、统一实体关系规范
- 预估：2-3 周
- 输出：Graph Gateway、Neo4j 索引、Graphiti 接入、Redis 子图缓存

## Phase 4：三大领域图谱化
- 目标：完成股票 / 加密 / 预测市场专项图谱建模与入图
- 预估：3-5 周
- 输出：专项实体关系模型、领域查询、领域特征生成

## Phase 5：AI / 风控 / 策略 / 回测增强
- 目标：将图谱上下文和图谱因子接入现有分析与策略链路
- 预估：2-4 周
- 输出：GraphContextBuilder、Prompt Assembler、图谱因子落表、回测接入

## Phase 6：治理、监控、审计与优化
- 目标：完成质量治理、任务监控、缓存调优、审计能力
- 预估：1-2 周
- 输出：监控指标、重试机制、图谱质量评分、审核入口

---

## 4. 模块拆分与负责人视角

| 模块 | 核心内容 | 依赖前置 | 主要产出 |
|------|----------|----------|----------|
| ORM 基础设施 | SQLAlchemy engine/session/base | 无 | `app/database/*`, `app/models/base.py` |
| 图谱元数据层 | Episode / Job / EntityRef / Feature | ORM 基础设施 | `app/models/graph_meta.py` |
| 采集统一层 | CollectedItem / Dedup / Storage | ORM 基础设施 | `app/collectors/*` |
| Episode Builder | 标准化图谱输入 | 采集统一层 | `app/collectors/episode_builder.py` |
| Graph Pipeline | Graphiti 调度链路 | Episode Builder | `app/collectors/graph_pipeline.py` |
| Graph Gateway | Neo4j / Graphiti / Cache 封装 | 基础设施 | `app/graph/*` |
| 领域图谱 | 股票/加密/预测市场建模 | Graph Gateway | 各领域查询与入图逻辑 |
| AI 增强 | GraphContextBuilder / Prompt 注入 | Graph Gateway | `app/graph/context_builder.py` |
| 图谱因子 | 因子生成与落表 | 领域图谱 | `qd_graph_feature_daily` 等 |
| 回测接入 | FeatureLoader / 时间切片 | 图谱因子 | 回测增强模块 |

---

## 5. 依赖清单

### 5.1 Python 依赖

```txt
SQLAlchemy>=2.0.0
alembic>=1.13.0
neo4j>=5.0.0
neomodel>=5.3.0
graphiti-core>=0.8.0
redis>=5.0.0
APScheduler>=3.10.0
httpx>=0.27.0
aiohttp>=3.9.0
tenacity>=8.3.0
orjson>=3.10.0
pandas>=1.5.0
fredapi>=0.5.0
spacy>=3.7.0
psycopg2-binary>=2.9.9
```

### 5.2 外部数据源依赖

- CCXT
- CoinGecko / CMC
- Finnhub
- yfinance
- AkShare
- Etherscan / BSCScan / Solscan
- Polymarket Gamma / Data API
- FRED
- X / Telegram / 新闻搜索源（可选）

### 5.3 基础设施依赖

- PostgreSQL
- Redis
- Neo4j 5.x
- Docker Compose
- Dify（可选工作流编排）

---

## 6. 环境变量清单

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
DB_POOL_MIN=5
DB_POOL_MAX=50
DB_POOL_ACQUIRE_TIMEOUT=10

REDIS_ENABLED=true
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=quantdinger

GRAPHITI_ENABLED=true
GRAPHITI_LLM_MODEL=gpt-4o-mini
GRAPHITI_EPISODE_BATCH_SIZE=50
GRAPHITI_IMPORTANCE_THRESHOLD=0.65
GRAPH_PIPELINE_ENABLED=true

GRAPH_CACHE_TTL_SECONDS=600
GRAPH_CONTEXT_TTL_SECONDS=300
REDIS_CACHE_TTL=600

DIFY_API_BASE=http://dify:3000
DIFY_API_KEY=your_dify_api_key

FRED_API_KEY=your_fred_api_key
FINNHUB_API_KEY=your_finnhub_key
ETHERSCAN_API_KEY=your_etherscan_key
COLLECTOR_ENABLED=true
```

---

## 7. 目录与代码骨架清单

```text
backend_api_python/
├── app/
│   ├── models/
│   │   ├── base.py
│   │   ├── collection.py
│   │   ├── graph_meta.py
│   │   └── graph_domain.py
│   ├── database/
│   │   ├── engine.py
│   │   ├── session.py
│   │   └── repositories/
│   │       ├── base.py
│   │       ├── market_repository.py
│   │       └── graph_repository.py
│   ├── collectors/
│   │   ├── base.py
│   │   ├── dedup.py
│   │   ├── storage.py
│   │   ├── episode_builder.py
│   │   ├── graph_pipeline.py
│   │   └── scheduler.py
│   ├── graph/
│   │   ├── connection.py
│   │   ├── graphiti_gateway.py
│   │   ├── context_builder.py
│   │   ├── queries.py
│   │   └── cache_gateway.py
│   └── services/
│       ├── market_data_collector.py
│       ├── fast_analysis.py
│       ├── event_impact_analyzer.py
│       └── smart_money_signal.py
└── migrations/
    ├── alembic.ini
    ├── env.py
    └── versions/
```

---

## 8. 数据表总清单

### 8.1 采集与基础市场表

| 表名 | 用途 |
|------|------|
| `qd_market_prices` | 标准化价格快照 |
| `qd_market_klines` | 标准化 K 线 |
| `qd_collection_records` | 统一采集记录 |
| `qd_macro_indicators` | 宏观指标 |
| `qd_financial_news` | 金融新闻原文与元数据 |

### 8.2 图谱元数据表

| 表名 | 用途 |
|------|------|
| `qd_graph_episodes` | Episode 元数据与状态 |
| `qd_graph_jobs` | 图谱任务与重试状态 |
| `qd_graph_entity_refs` | 结构化记录与图实体映射 |
| `qd_graph_relation_snapshots` | 关键关系快照 |
| `qd_graph_feature_daily` | 统一图谱因子日表 |

### 8.3 股票领域表

| 表名 | 用途 |
|------|------|
| `qd_shareholdings` | 机构/股东持股 |
| `qd_insider_trades` | 内部人交易 |
| `qd_company_narrative_features` | 股票叙事特征 |

### 8.4 加密领域表

| 表名 | 用途 |
|------|------|
| `qd_crypto_accounts` | 链上地址 / KOL 账号 |
| `qd_crypto_transfers` | 链上转账 |
| `qd_crypto_narrative_features` | 加密叙事特征 |

### 8.5 预测市场领域表

| 表名 | 用途 |
|------|------|
| `qd_polymarket_users` | 预测市场用户 |
| `qd_polymarket_user_trades` | 用户交易记录 |
| `qd_polymarket_market_features` | 预测市场图谱特征 |

---

## 9. Alembic / Migration 执行顺序

1. `001_initial_schema.py`
2. `002_add_collection_tables.py`
3. `003_add_graph_meta_tables.py`
4. `004_add_graph_feature_tables.py`
5. `005_add_domain_feature_indexes.py`

执行要求：
- 新增表必须全部进入 Alembic 管理
- 不再继续把补丁逻辑堆到 `init.sql`
- 关键唯一键、查询键、幂等键必须显式建约束和索引

---

## 10. Graphiti / Neo4j 实体与关系总表

### 10.1 通用实体
- `Asset`
- `Company`
- `Person`
- `Institution`
- `Event`
- `NewsArticle`
- `MacroIndicator`
- `PredictionMarket`
- `Outcome`
- `CryptoAccount`
- `PolymarketUser`
- `NarrativeTag`
- `Protocol`
- `ExternalEvent`
- `ResolutionSource`

### 10.2 通用关系
- `HOLDS_SHARES`
- `EMPLOYED_BY`
- `TRADED_STOCK`
- `SUPPLY_CHAIN_OF`
- `MENTIONED_IN`
- `AFFECTS`
- `CORRELATED_WITH`
- `HAS_NARRATIVE`
- `ISSUED`
- `HOLDS`
- `TRANSFERRED_TO`
- `DEPLOYED_ON`
- `PAIRED_WITH`
- `IMPACTED_BY`
- `PROMOTED_BY`
- `TRADED_IN`
- `CO_TRADED`
- `HAS_ODDS`
- `TRIGGERED_BY`
- `PREDICTS`
- `LINKED_TO_ASSET`

### 10.3 所有关系统一字段
- `source_ref`
- `confidence`
- `t_valid`
- `t_invalid`
- `updated_at`

---

## 11. Redis Key 总清单

### 11.1 通用图谱缓存
```text
graph:subgraph:{domain}:{entity}
graph:context:{market}:{symbol}
graph:query:{hash}
graph:episode:dedup:{hash}
graph:task:status:{job_id}
graph:feature:{market}:{symbol}:{feature_name}
```

### 11.2 采集与任务缓存
```text
collector:last:{name}
collector:health:{name}
```

### 11.3 股票专项缓存
```text
graph:context:stock:{ticker}
graph:subgraph:stock:{ticker}
graph:feature:stock:{ticker}:narrative
graph:event-chain:{event_uid}
```

### 11.4 加密专项缓存
```text
graph:context:crypto:{symbol}
graph:subgraph:crypto:{symbol}
graph:account:{address}
graph:risk-chain:crypto:{symbol}
```

### 11.5 预测市场专项缓存
```text
graph:context:polymarket:{market_id}
graph:subgraph:polymarket:{market_id}
graph:smart-money:{market_id}
graph:prediction-leading:{symbol}
```

### 11.6 TTL 建议
- 子图缓存：5-15 分钟
- AI 上下文缓存：3-10 分钟
- 关系评分缓存：30-60 分钟
- 任务状态缓存：任务结束后保留 1 小时
- Episode 去重键：24 小时起

---

## 12. API 总清单

### 12.1 图谱通用接口
| 接口 | 说明 |
|------|------|
| `GET /api/graph/related-assets` | 相关资产查询 |
| `GET /api/graph-analysis/enhanced-context` | 图谱增强上下文 |
| `GET /api/graph-analysis/contagion-path` | 资产/事件传播路径 |
| `GET /api/graph-analysis/narrative-drift` | 叙事演化分析 |

### 12.2 股票接口
| 接口 | 说明 |
|------|------|
| `GET /api/graph/stock/company/{ticker}` | 公司图谱详情 |
| `GET /api/graph/stock/common-holders` | 共同股东分析 |
| `GET /api/graph/stock/supply-chain/{ticker}` | 供应链路径分析 |
| `GET /api/graph/stock/narrative-drift/{ticker}` | 股票叙事演化 |
| `GET /api/graph/stock/event-impact/{event_uid}` | 事件影响链 |

### 12.3 加密接口
| 接口 | 说明 |
|------|------|
| `GET /api/graph/crypto/account/{address}` | 地址图谱详情 |
| `GET /api/graph/crypto/whale-flow/{symbol}` | 鲸鱼流向 |
| `GET /api/graph/crypto/kol-consensus/{symbol}` | KOL 共识 |
| `GET /api/graph/crypto/narrative-drift/{symbol}` | 加密叙事演化 |
| `GET /api/graph/crypto/risk-spread/{symbol}` | 风险扩散路径 |

### 12.4 预测市场接口
| 接口 | 说明 |
|------|------|
| `GET /api/graph/polymarket/smart-money` | 聪明钱排行 |
| `GET /api/graph/polymarket/user/{addr}` | 用户交易图谱 |
| `GET /api/graph/polymarket/co-traders/{addr}` | 同向交易者 |
| `GET /api/graph/polymarket/market-sentiment/{id}` | 市场情绪 |
| `GET /api/graph/polymarket/odds-attribution/{id}` | 赔率异动归因 |
| `GET /api/graph/polymarket/linked-assets/{id}` | 关联资产映射 |

### 12.5 AI / 信号接口
| 接口 | 说明 |
|------|------|
| `GET /api/graph-analysis/smart-money/{symbol}` | 聪明钱信号 |
| `GET /api/graph-analysis/prediction-leading/{symbol}` | 预测市场先行指标 |

---

## 13. 图谱因子总清单

### 13.1 股票因子
- `shared_holder_strength`
- `insider_buy_signal_score`
- `supply_chain_risk_score`
- `macro_impact_score`
- `narrative_heat_score`

### 13.2 加密因子
- `whale_accumulation_score`
- `kol_consensus_score`
- `protocol_risk_spread_score`
- `narrative_drift_score`
- `stablecoin_stress_score`

### 13.3 预测市场因子
- `pm_smart_money_consensus_score`
- `pm_odds_jump_score`
- `pm_event_trigger_score`
- `pm_leading_signal_score`
- `pm_resolution_risk_score`

### 13.4 通用落表策略
- 主表：`qd_graph_feature_daily`
- 领域补充表：
  - `qd_company_narrative_features`
  - `qd_crypto_narrative_features`
  - `qd_polymarket_market_features`
- 回测统一按日期切片读取

---

## 14. AI 上下文标准结构

```python
{
  "related_assets": [],
  "recent_events": [],
  "impact_chain": [],
  "narrative_drift": {},
  "top_institutional_holders": [],
  "kol_consensus": {},
  "prediction_market_signals": [],
  "smart_money": {},
  "subgraph_summary": ""
}
```

Prompt 组装顺序建议：
1. 市场结构化数据摘要
2. 技术指标摘要
3. 新闻与公告摘要
4. 图谱增强信息
5. 输出要求

---

## 15. 执行顺序建议

### 第一步：基础设施先行
- 补全 requirements
- 落地 ORM engine/session/base
- 新建图谱元数据模型
- 引入 Alembic

### 第二步：采集链路标准化
- 改造 `CollectedItem`
- 补全 `collection.py`
- 落地 `EpisodeBuilder`
- 落地 `GraphPipeline`
- 建立 `qd_collection_records`、`qd_graph_episodes`、`qd_graph_jobs`

### 第三步：图谱底座
- Neo4j 容器与连接
- `GraphitiGateway`
- `GraphStorageGateway`
- Redis 图谱缓存层
- 通用节点/关系规范与索引

### 第四步：领域图谱分域落地
- 股票：持股 / 高管 / 供应链 / 宏观 / 叙事
- 加密：地址 / 转账 / 协议 / 风险 / 叙事
- 预测市场：赔率 / 聪明钱 / 外部事件 / 桥接资产

### 第五步：AI 与策略增强
- `GraphContextBuilder`
- Prompt 注入
- 事件影响链服务
- 图谱因子生成与落表
- 回测接入图谱因子

### 第六步：治理与优化
- 任务重试
- 图谱质量评分
- 热点缓存优化
- 审计与人工修正入口

---

## 16. 里程碑交付物

### M1：基础设施可运行
- SQLAlchemy 基础设施
- Graph 元数据模型
- Neo4j 容器可连接
- Redis 图谱缓存策略上线

### M2：采集到 Episode 可跑通
- CollectedItem 标准化
- EpisodeBuilder 可运行
- GraphPipeline 可写图谱任务状态

### M3：三大领域图谱基础能力可用
- 股票、加密、预测市场各至少 1 条主链路可入图
- 基础查询接口可返回子图结果

### M4：AI 增强可用
- FastAnalysis 可注入图谱上下文
- 支持缓存命中、查询降级

### M5：策略与回测可用
- 图谱因子日表产出
- 回测可读取至少一组股票/加密/预测市场图谱因子

### M6：治理与监控完成
- 失败重试、耗时监控、关系审计、缓存观测齐备

---

## 17. 风险与应对速查表

| 风险 | 应对 |
|------|------|
| 高频数据误入图谱 | 强制在采集层做 `should_build_episode` 分流 |
| Graphiti 抽取不稳定 | 本体约束 + 置信度阈值 + 人工审核 |
| 图查询过重 | Redis 缓存 + 限制跳数 + 预计算特征 |
| 回测未来函数污染 | 统一使用 `t_valid/t_invalid` 历史切片 |
| 迁移打断现网 | ORM 与旧 SQL 双轨并行 |
| API 限流 | 多源备用 + 重试 + 限速 |

---

## 18. 推荐下一步落地任务

建议按照以下顺序立即进入开发：

1. 完成 `collection.py`、`graph_pipeline.py`、`graph_repository.py`
2. 建第一版 Alembic migration：
   - `qd_collection_records`
   - `qd_graph_episodes`
   - `qd_graph_jobs`
   - `qd_graph_entity_refs`
   - `qd_graph_feature_daily`
3. 在 `MarketDataCollector` 中引入统一 `CollectedItem` 输出适配层
4. 在 `FastAnalysisService` 中接入标准 `GraphContextBuilder`
5. 先落地一个股票链路 PoC：新闻 -> Episode -> Graphiti -> Neo4j -> AI 上下文

---

*本清单用于执行收口，后续如方案继续演进，应优先更新本文件，再回写各子文档。*
