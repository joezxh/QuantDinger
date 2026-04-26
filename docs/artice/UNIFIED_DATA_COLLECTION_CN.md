# 统一市场数据采集系统方案

> 版本：v1.1 | 优先级：P0 | 预估工期：4-6 周

---

## 1. 设计目标

- 多源数据采集：加密货币、美股/港股、外汇、宏观经济、金融新闻、预测市场
- 统一接口规范：`BaseCollector` 抽象层，各数据源独立实现
- 去重清洗存储：内容哈希去重 + 数据标准化 + ORM 持久化
- 调度管理：APScheduler 定时采集，支持动态配置频率
- 引入 Episode Builder：将结构化和非结构化数据转为 Graphiti 可消费的 Episode
- 与 PostgreSQL、Redis、Neo4j、Graphiti 协同，而非直接只写 Neo4j

---

## 2. 架构设计

```text
采集器
  -> CollectedItem
  -> DedupEngine
  -> PostgreSQL(结构化事实落库)
  -> Redis(最新快照/去重键/任务状态)
  -> Episode Builder
  -> Graphiti / Dify Workflow
  -> Neo4j
  -> Redis(子图缓存/上下文缓存)
```

建议目录结构：

```text
app/collectors/
  base.py
  registry.py
  scheduler.py
  dedup.py
  storage.py
  episode_builder.py
  graph_pipeline.py
  redis_cache.py
  crypto/price_collector.py
  crypto/onchain_collector.py
  stock/us_collector.py
  stock/hk_collector.py
  stock/shareholder_collector.py
  forex/mt5_collector.py
  macro/fred_collector.py
  macro/sentiment_collector.py
  news/finnhub_collector.py
  polymarket/market_collector.py
  polymarket/user_collector.py
```

---

## 3. 数据分层原则

### 3.1 PostgreSQL 存什么

- 行情快照、K 线、订单簿摘要
- 新闻原文、公告原文、用户交易记录
- 采集记录、去重记录、图谱任务元数据
- 图谱因子日表/小时表

### 3.2 Redis 存什么

- 最新价格快照
- 采集任务状态
- Episode 幂等去重键
- 热点图谱上下文摘要
- 高热点资产子图缓存

### 3.3 Graphiti / Neo4j 存什么

- 实体、关系、事件、叙事标签
- 有时间窗的事实演化
- 跨市场桥接关系
- AI 检索与策略因子生成所需的子图

### 3.4 明确不入图的内容

以下内容原则上不进入图谱主存储：
- 高频逐笔成交
- 全量分钟级价格快照
- 全量订单簿深度
- 无明确语义价值的重复新闻

---

## 4. BaseCollector 接口

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import hashlib
import json


@dataclass
class CollectedItem:
    source: str
    data_type: str
    market: Optional[str]
    symbol: Optional[str]
    raw_data: Dict[str, Any]
    normalized_data: Dict[str, Any]
    collected_at: datetime = field(default_factory=datetime.utcnow)
    content_hash: str = ""
    importance_score: float = 0.5
    should_build_episode: bool = False
    entity_keys: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not self.content_hash:
            payload = json.dumps(self.normalized_data, sort_keys=True, default=str)
            self.content_hash = hashlib.sha256(payload.encode()).hexdigest()[:32]


class BaseCollector(ABC):
    name: str = "base"

    @abstractmethod
    def collect(self, **kwargs) -> List[CollectedItem]:
        ...

    @abstractmethod
    def health_check(self) -> bool:
        ...

    def _safe_collect(self, **kwargs) -> List[CollectedItem]:
        try:
            return self.collect(**kwargs)
        except Exception as e:
            from app.utils.logger import get_logger
            get_logger(self.name).error(f"Collect failed: {e}", exc_info=True)
            return []
```

新增字段说明：
- `importance_score`：用于 Episode 分级处理
- `should_build_episode`：标识是否进入图谱构建链路
- `entity_keys`：用于 Graphiti 实体对齐

---

## 5. Episode Builder

### 5.1 设计目标

将适合图谱化的数据转换为统一的 `EpisodeEnvelope`，避免采集器直接依赖 Graphiti。

### 5.2 核心职责

- 从 `CollectedItem` 生成标准 Episode
- 根据 `data_type` 判断是否触发 Graphiti
- 构建 `title/content/entity_keys/source_ref`
- 统一做事件重要度分级与去重键生成

### 5.3 示例代码

```python
# app/collectors/episode_builder.py
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EpisodeEnvelope:
    episode_type: str
    market_domain: str
    title: str
    content: str
    entity_keys: dict
    source: str
    source_ref: str
    event_time: datetime | None
    observed_time: datetime
    importance_score: float
    dedup_key: str
    metadata: dict


class EpisodeBuilder:
    def build(self, item) -> EpisodeEnvelope | None:
        if not item.should_build_episode:
            return None

        return EpisodeEnvelope(
            episode_type=item.data_type,
            market_domain=(item.market or "unknown").lower(),
            title=f"{item.data_type}:{item.symbol or item.source}",
            content=self._build_content(item),
            entity_keys=item.entity_keys,
            source=item.source,
            source_ref=item.content_hash,
            event_time=item.normalized_data.get("event_time"),
            observed_time=item.collected_at,
            importance_score=item.importance_score,
            dedup_key=f"episode:{item.content_hash}",
            metadata=item.normalized_data,
        )

    def _build_content(self, item) -> str:
        return json.dumps(item.normalized_data, ensure_ascii=False, default=str)
```

---

## 6. Graph Pipeline

### 6.1 数据流

```text
Collector -> Dedup -> ORM Storage -> EpisodeBuilder -> GraphPipeline
                                               ├-> Redis 幂等键
                                               ├-> Graphiti
                                               └-> Dify Workflow(可选)
```

### 6.2 处理原则

1. 先结构化落 PostgreSQL，再异步构建图谱。
2. 图谱失败不影响主采集链路。
3. 图谱任务可重放，可追踪状态。
4. 只有 `importance_score` 达阈值或显式标记的数据才进入 Graphiti。

### 6.3 示例代码

```python
class GraphPipeline:
    def __init__(self, episode_builder, graphiti_gateway, redis_client):
        self.episode_builder = episode_builder
        self.graphiti_gateway = graphiti_gateway
        self.redis = redis_client

    async def process_item(self, item):
        episode = self.episode_builder.build(item)
        if not episode:
            return

        dedup_key = f"graph:episode:dedup:{episode.dedup_key}"
        if self.redis.get(dedup_key):
            return

        self.redis.setex(dedup_key, 86400, "1")
        await self.graphiti_gateway.add_episode(episode)
```

---

## 7. 各数据源采集器说明

### 7.1 加密货币

复用现有 `DataSourceFactory.get_kline()` 和 `kline_service.get_realtime_price()`，
封装为 `CryptoPriceCollector`。

补充建议：
- 价格快照进入 PostgreSQL + Redis
- 重大波动、解锁、协议事件、鲸鱼转账进入 Episode Builder
- Narrative/KOL/链上异常类数据应设置 `should_build_episode=True`

### 7.2 美股/港股/A股

复用现有 `market_data_collector._get_price()`、`_get_fundamental()`、AkShare 数据源。

补充建议：
- 财务快照、行情进入 PostgreSQL
- 新闻、公告、内部人交易、机构持股变化进入 Episode Builder
- 对重要公告设置更高 `importance_score`

### 7.3 外汇与宏观

- 高频报价存 PostgreSQL + Redis
- 利率决议、非农、CPI、央行讲话摘要进入 Episode Builder
- 宏观数据应与股票、加密、预测市场建立桥接实体

### 7.4 金融新闻

复用现有 Finnhub 集成，封装 `FinnhubNewsCollector`。

建议：
- 新闻原文入 PostgreSQL
- 新闻摘要、实体关键词、情绪、目标资产进入 Episode Builder
- 重复转载内容在 DedupEngine 和 GraphPipeline 双重去重

### 7.5 Polymarket

复用现有 `PolymarketDataSource`。

建议：
- 市场元数据、交易、持仓入 PostgreSQL
- 概率显著波动、巨鲸动作、市场解析规则变化进入 Episode Builder
- 与股票/加密资产的映射在图谱层维护

---

## 8. 去重引擎

```python
class DedupEngine:
    def __init__(self):
        self._cache: set = set()

    def filter(self, items):
        new_items = []
        for item in items:
            if item.content_hash not in self._cache:
                if not self._in_db(item.content_hash):
                    new_items.append(item)
                    self._cache.add(item.content_hash)
        return new_items
```

建议扩展：
- 结构化去重：基于 `content_hash`
- Episode 去重：基于 `graph:episode:dedup:{hash}`
- 事件去重：基于 `event_type + entity_keys + event_time` 组合键

---

## 9. 采集调度计划

| 采集器 | 频率 | 采集内容 | 图谱化策略 |
|--------|------|----------|-----------|
| crypto_price | 60s | 价格、K线 | 默认不入图，异动时生成 Episode |
| crypto_onchain | 300s | 鲸鱼转账、地址活动 | 关键事件入图 |
| us_stock | 300s | 价格、基本面 | 公告/持股变化入图 |
| hk_cn_stock | 300s | 价格 | 重大公告/新闻入图 |
| forex_mt5 | 60s | 外汇报价 | 不直接入图 |
| fred_macro | 86400s | 宏观指标 | 重要宏观节点入图 |
| finnhub_news | 300s | 金融新闻 | 默认构造 Episode |
| polymarket_market | 300s | 市场信息、概率 | 异动/规则变化入图 |
| polymarket_user | 300s | 用户交易、持仓 | 聪明钱行为入图 |

---

## 10. 存储与任务元数据表

建议新增或扩展：

```sql
CREATE TABLE qd_collection_records (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50),
    data_type VARCHAR(50),
    market VARCHAR(50),
    symbol VARCHAR(100),
    content_hash VARCHAR(64) NOT NULL UNIQUE,
    collected_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE qd_graph_jobs (
    id SERIAL PRIMARY KEY,
    content_hash VARCHAR(64) NOT NULL,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(30) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 11. Redis 设计

建议新增缓存 Key：

```text
collector:last:{name}
collector:health:{name}
graph:episode:dedup:{hash}
graph:task:status:{job_id}
graph:context:{market}:{symbol}
graph:subgraph:{domain}:{entity}
```

---

## 12. 环境变量

```env
FRED_API_KEY=your_fred_api_key
DIFY_API_BASE=http://dify:3000
DIFY_API_KEY=your_dify_api_key
COLLECTOR_ENABLED=true
GRAPHITI_ENABLED=true
GRAPHITI_IMPORTANCE_THRESHOLD=0.65
GRAPH_PIPELINE_ENABLED=true
REDIS_CACHE_TTL=600
```

---

## 13. 实施计划

| 周次 | 任务 |
|------|------|
| 第 1 周 | BaseCollector、DedupEngine、ORM 持久化层 |
| 第 2 周 | Crypto / Stock / Forex 采集器标准化 |
| 第 3 周 | 新闻 / 宏观 / Polymarket 采集器 + Episode Builder |
| 第 4 周 | GraphPipeline、Redis 幂等、Graphiti / Dify 触发链路 |
| 第 5 周 | 调度、任务状态、失败重试、监控告警 |
| 第 6 周 | 数据质量检查、热点缓存、性能优化 |

---

*本方案待确认后方可执行实施。*
