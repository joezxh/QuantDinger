# Neo4j + Graphiti 知识图谱基础设施方案

> 版本：v1.1 | 优先级：P0 | 预估工期：4-6 周

---

## 1. 设计目标

- 在现有 Neo4j 图数据库方案上引入 Graphiti，构建时态知识图谱基础设施
- 与 PostgreSQL、Redis 协同，形成“结构化主库 + 图谱关系库 + 实时缓存层”三层架构
- 建立统一 Episode 摄入规范、实体映射规范和关系时间窗规范
- 支持图查询、路径分析、GraphRAG 检索、事件影响链、叙事演化分析
- 为股票、加密货币、预测市场三大领域提供统一的图谱底座

---

## 2. 总体定位

### 2.1 基础设施分工

| 组件 | 角色 | 说明 |
|------|------|------|
| PostgreSQL | 主事实账本 | 存储结构化主数据、时间序列、原始新闻、采集记录、图谱任务元数据 |
| Redis | 实时缓存与热点层 | 缓存热点子图、AI 上下文、图谱查询结果、Episode 去重键、任务状态 |
| Neo4j | 图关系主查询引擎 | 存储实体、关系、事件传播链、跨域桥接关系 |
| Graphiti | 图谱编排与时态记忆层 | 负责 Episode 驱动抽取、关系冲突更新、时间感知事实演化、GraphRAG 检索 |

### 2.2 基础原则

1. **Neo4j 是图数据库主存储，Graphiti 不是替代数据库。**
2. **PostgreSQL 继续存结构化事实，图谱只承载关系、事件、叙事和桥接语义。**
3. **Redis 所有内容均为可重建缓存，不作为唯一事实来源。**
4. **Graphiti 只处理重要事件和状态变化，不接收高频逐笔行情。**

---

## 3. 技术选型

| 组件 | 选型 | 说明 |
|------|------|------|
| 图数据库 | Neo4j 5.x Community | 图查询成熟，足够覆盖当前阶段 |
| Graph 编排 | Graphiti | 负责 Episode、时态图谱、GraphRAG |
| Python 驱动 | neo4j>=5.0 | 官方驱动 |
| 图谱 OGM | neomodel>=5.3 | 可选，用于静态模型封装 |
| 查询语言 | Cypher | Neo4j 原生查询 |
| 缓存 | Redis | 热点子图与上下文缓存 |
| 调度 | APScheduler / 内部 Job Runner | 统一采集与图谱构建任务 |

建议新增依赖：

```txt
neo4j>=5.0.0
neomodel>=5.3.0
graphiti-core>=0.8.0
httpx>=0.27.0
tenacity>=8.3.0
orjson>=3.10.0
```

---

## 4. 架构拓扑

```text
Collector / ETL / Workflow
        ↓
Normalizer / ORM Storage
        ↓
PostgreSQL (事实主库)
        ↓
Episode Builder
        ↓
Graphiti
   ├─ 实体抽取 / 关系抽取 / 冲突消解
   ├─ 时间窗管理（t_valid / t_invalid）
   └─ GraphRAG 子图检索
        ↓
Neo4j
        ↓
Redis (subgraph cache / context cache / task cache)
        ↓
AI Analysis / Strategy / Risk / Backtest
```

---

## 5. Docker Compose 集成

```yaml
services:
  neo4j:
    image: neo4j:5-community
    container_name: quantdinger_neo4j
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD:-quantdinger}
      NEO4J_PLUGINS: '["apoc"]'
      NEO4J_dbms_security_procedures_unrestricted: apoc.*
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    networks:
      - quantdinger_net
    restart: unless-stopped

volumes:
  neo4j_data:
  neo4j_logs:
```

建议环境变量：

```env
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=quantdinger
GRAPHITI_ENABLED=true
GRAPHITI_LLM_MODEL=gpt-4o-mini
GRAPHITI_EPISODE_BATCH_SIZE=50
GRAPH_CACHE_TTL_SECONDS=600
GRAPH_CONTEXT_TTL_SECONDS=300
```

---

## 6. 连接管理与网关封装

### 6.1 Neo4j 连接管理

```python
# app/graph/connection.py
import os
from neo4j import GraphDatabase

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
            auth=(
                os.getenv("NEO4J_USER", "neo4j"),
                os.getenv("NEO4J_PASSWORD", "quantdinger"),
            ),
        )
    return _driver


def run_cypher(query: str, params: dict | None = None):
    with get_driver().session() as session:
        return session.run(query, params or {}).data()
```

### 6.2 Graph Gateway

建议新增统一网关层：
- `GraphStorageGateway`：封装 Neo4j 读写
- `GraphitiGateway`：封装 Episode 写入、GraphRAG 检索、冲突更新
- `GraphCacheGateway`：封装 Redis 子图与上下文缓存

---

## 7. 统一实体与关系规范

### 7.1 通用节点

| 节点标签 | 说明 | 关键属性 |
|---------|------|----------|
| `Asset` | 股票/加密货币/指数/ETF/外汇等资产 | uid, symbol, market, name, type |
| `Company` | 上市公司或发行主体 | uid, ticker, name, industry |
| `Person` | 高管、内部人、KOL、政治人物 | uid, name, role |
| `Institution` | 机构、基金、交易所、监管机构 | uid, name, type |
| `Event` | 财报、政策、黑客攻击、监管处罚等 | uid, title, event_type, event_time |
| `NewsArticle` | 新闻、公告、研报、帖子 | uid, source, published_at |
| `MacroIndicator` | 利率、CPI、非农、DXY 等 | uid, name, series_id |
| `PredictionMarket` | 预测市场 | uid, market_id, question |
| `Outcome` | YES/NO 或其他结果项 | uid, label |
| `CryptoAccount` | 链上地址 / KOL 账号 | uid, address, platform |
| `PolymarketUser` | 预测市场用户 | uid, address |
| `NarrativeTag` | 叙事标签 | uid, name, domain |

### 7.2 公共属性规范

所有节点和关系统一携带：
- `uid`: 全局唯一 ID
- `source`: 来源系统或采集器
- `source_ref`: 原始数据引用（PostgreSQL 主键、URL、hash）
- `confidence`: 置信度
- `created_at`
- `updated_at`
- `t_valid`: 生效时间
- `t_invalid`: 失效时间，可为空

### 7.3 关系类型

| 关系类型 | 起点 | 终点 | 属性 |
|---------|------|------|------|
| `HOLDS_SHARES` | Institution/Person | Company | shares_pct, value_usd |
| `EMPLOYED_BY` | Person | Company | role |
| `SUPPLY_CHAIN_OF` | Company | Company | product_type |
| `MENTIONED_IN` | Asset/Company/Event | NewsArticle | sentiment, relevance |
| `AFFECTS` | Event/MacroIndicator | Asset/Company/Protocol | impact_direction |
| `CORRELATED_WITH` | Asset | Asset | correlation, period |
| `FOLLOWS` | CryptoAccount | CryptoAccount | platform |
| `TRADED_IN` | PolymarketUser | PredictionMarket | direction, amount |
| `PREDICTS` | PredictionMarket | Asset/Event | confidence |
| `HAS_NARRATIVE` | Asset/Protocol/Market | NarrativeTag | score |
| `TRIGGERED_BY` | Event | PredictionMarket | magnitude |
| `LINKED_TO_ASSET` | PredictionMarket | Asset | linkage_type |

---

## 8. Episode 模型与 Graphiti 接入

### 8.1 Episode 统一结构

Graphiti 输入统一封装为 `EpisodeEnvelope`：

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass
class EpisodeEnvelope:
    episode_type: str
    market_domain: str
    title: str
    content: str
    entity_keys: dict[str, str]
    source: str
    source_ref: str
    event_time: datetime | None
    observed_time: datetime
    importance_score: float = 0.5
    dedup_key: str = ""
    metadata: dict[str, Any] | None = None
```

### 8.2 Graphiti 接入流程

1. 采集器数据先落 PostgreSQL。
2. `EpisodeBuilder` 从结构化数据或文本生成 `EpisodeEnvelope`。
3. `GraphitiGateway.add_episode()` 送入 Graphiti。
4. Graphiti 抽取实体与关系，判断与既有事实是否冲突。
5. 冲突时关闭旧关系的 `t_invalid`，创建新的事实边。
6. 写入 Neo4j 并回填 PostgreSQL 中的图谱任务状态。

### 8.3 示例代码

```python
# app/graph/graphiti_gateway.py
class GraphitiGateway:
    def __init__(self, graphiti_client):
        self.client = graphiti_client

    async def add_episode(self, episode):
        return await self.client.add_episode(
            name=episode.title,
            content=episode.content,
            source_description=episode.source,
            reference_time=episode.event_time or episode.observed_time,
        )
```

---

## 9. 索引与约束策略

```cypher
CREATE CONSTRAINT asset_uid IF NOT EXISTS FOR (a:Asset) REQUIRE a.uid IS UNIQUE;
CREATE CONSTRAINT company_uid IF NOT EXISTS FOR (c:Company) REQUIRE c.uid IS UNIQUE;
CREATE CONSTRAINT person_uid IF NOT EXISTS FOR (p:Person) REQUIRE p.uid IS UNIQUE;
CREATE CONSTRAINT event_uid IF NOT EXISTS FOR (e:Event) REQUIRE e.uid IS UNIQUE;
CREATE CONSTRAINT news_uid IF NOT EXISTS FOR (n:NewsArticle) REQUIRE n.uid IS UNIQUE;
CREATE CONSTRAINT pm_uid IF NOT EXISTS FOR (p:PredictionMarket) REQUIRE p.uid IS UNIQUE;

CREATE INDEX asset_symbol IF NOT EXISTS FOR (a:Asset) ON (a.symbol);
CREATE INDEX asset_market IF NOT EXISTS FOR (a:Asset) ON (a.market);
CREATE INDEX company_ticker IF NOT EXISTS FOR (c:Company) ON (c.ticker);
CREATE INDEX event_time IF NOT EXISTS FOR (e:Event) ON (e.event_time);
CREATE INDEX news_published IF NOT EXISTS FOR (n:NewsArticle) ON (n.published_at);
CREATE INDEX narrative_name IF NOT EXISTS FOR (n:NarrativeTag) ON (n.name);
```

---

## 10. PostgreSQL 协同表设计

建议新增：

```sql
CREATE TABLE qd_graph_episodes (
    id SERIAL PRIMARY KEY,
    episode_type VARCHAR(50) NOT NULL,
    market_domain VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    source VARCHAR(100) NOT NULL,
    source_ref VARCHAR(255),
    dedup_key VARCHAR(128) UNIQUE,
    importance_score DECIMAL(6,4) DEFAULT 0.5,
    event_time TIMESTAMP NULL,
    observed_time TIMESTAMP NOT NULL,
    status VARCHAR(30) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE qd_graph_entity_refs (
    id SERIAL PRIMARY KEY,
    entity_uid VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    source_table VARCHAR(100) NOT NULL,
    source_pk VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(entity_type, source_table, source_pk)
);

CREATE TABLE qd_graph_feature_daily (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    market VARCHAR(50) NOT NULL,
    symbol VARCHAR(100) NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    feature_value DECIMAL(24,8) NOT NULL,
    source VARCHAR(50) DEFAULT 'graph',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, market, symbol, feature_name)
);
```

---

## 11. Redis 缓存设计

建议 Key 规划：

```text
graph:subgraph:{domain}:{entity}
graph:context:{market}:{symbol}
graph:query:{hash}
graph:episode:dedup:{hash}
graph:task:status:{job_id}
graph:feature:{market}:{symbol}:{feature_name}
```

缓存策略：
- 子图缓存 TTL：5-15 分钟
- AI 上下文缓存 TTL：3-10 分钟
- 关系评分缓存 TTL：30-60 分钟
- 任务状态缓存 TTL：直到任务结束后 1 小时

---

## 12. 图查询与 GraphRAG API

### 12.1 基础查询能力

- 资产相关实体查询
- 事件影响链查询
- 叙事演化查询
- 跨市场桥接关系查询
- 预测市场先行信号查询

### 12.2 GraphRAG 查询接口

建议封装：
- `get_subgraph_for_asset(market, symbol)`
- `get_recent_event_chain(entity_uid)`
- `get_narrative_drift(entity_uid, window='30d')`
- `get_prediction_market_leading_signals(symbol)`

### 12.3 查询降级策略

- Redis 命中优先返回缓存结果
- Neo4j 可用则执行 Cypher 查询
- Graphiti 不可用时退化为静态图查询
- Neo4j 不可用时返回空上下文，不阻塞主分析流程

---

## 13. 与三大领域图谱的对接方式

### 13.1 股票领域
- Episode 来源：新闻、公告、研报、财报摘要、持股变化
- 重点关系：供应链、持股、高管变更、宏观冲击
- 关键特征：共同股东强度、供应链冲击分数、叙事热度变化

### 13.2 加密领域
- Episode 来源：链上转账、协议更新、黑客事件、KOL 帖子、解锁事件
- 重点关系：持仓、资金转移、协议部署、叙事漂移
- 关键特征：鲸鱼净流向、KOL 共识、协议风险传播得分

### 13.3 预测市场领域
- Episode 来源：赔率异动、用户行为、外部新闻、结算规则变化
- 重点关系：TRIGGERED_BY、PREDICTS、CO_TRADED、LINKED_TO_ASSET
- 关键特征：聪明钱一致性、异动归因分数、先行指标强度

---

## 14. 监控、治理与质量控制

### 14.1 监控指标

- Episode 入图成功率
- Graphiti 抽取耗时
- Neo4j 写入耗时
- 图查询 P95 延迟
- Redis 命中率
- 每日新建/失效关系数量

### 14.2 数据质量控制

- 为关系设置最小置信度阈值
- 对高影响关系提供人工审核入口
- 对跨域实体对齐结果进行 alias 校验
- 对重复 Episode 做幂等去重

### 14.3 审计要求

所有关键关系保留：
- 来源引用
- 抽取时间
- 置信度
- 生效/失效时间
- 原始 Episode ID

---

## 15. 实施计划

| 周次 | 任务 |
|------|------|
| 第 1 周 | Neo4j 接入、Graphiti 依赖评估、基础连接网关 |
| 第 2 周 | Episode 模型、PostgreSQL 元数据表、Redis 缓存键设计 |
| 第 3 周 | Graphiti 写入链路、关系时间窗管理、索引约束 |
| 第 4 周 | 图查询 API、GraphRAG 检索 API、降级机制 |
| 第 5 周 | 三大领域桥接规则、关系质量校验、缓存优化 |
| 第 6 周 | 监控、审计、任务重放与治理能力 |

---

*本方案待确认后方可执行实施。*
