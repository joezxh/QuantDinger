# SQLAlchemy ORM 重构方案

> 版本：v1.1 | 优先级：P0 | 预估工期：4-6 周

---

## 1. 现状与问题

### 1.1 当前数据库访问模式

```python
with get_db_connection() as db:
    cur = db.cursor()
    cur.execute("SELECT id, username FROM qd_users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
```

| 问题 | 描述 | 影响 |
|------|------|------|
| 类型不安全 | 返回 dict，字段名拼错运行时才报错 | 高 |
| 兼容层黑科技 | `?` 转 `%s`、SAVEPOINT + RETURNING id 变通 | 高技术债 |
| 无 Schema 约束 | SQL 字符串分散在各 Service | 中 |
| 迁移混乱 | `init.sql` 含大量 `DO $$ IF NOT EXISTS $$` 补丁块 | 高 |
| 图谱元数据缺失 | 无统一图谱任务表、Episode 表、映射表 | 高 |
| 回测特征碎片化 | 图谱因子与结构化行情因子未统一建模 | 中 |

### 1.2 规模评估

- 含裸 SQL 的文件：约 25 个
- `init.sql` 行数：约 600 行
- 需要重构的 Service：约 40 个
- 新增图谱元数据与特征表：约 8-12 张

---

## 2. 目标架构

### 2.1 目录结构

```text
app/
├── models/
│   ├── base.py
│   ├── user.py
│   ├── strategy.py
│   ├── market.py
│   ├── analysis.py
│   ├── backtest.py
│   ├── trading.py
│   ├── community.py
│   ├── billing.py
│   ├── polymarket.py
│   ├── collection.py
│   ├── graph_meta.py      # 新增：图谱 Episode / Job / EntityRef / Feature
│   └── graph_domain.py    # 新增：股票/加密/预测市场图谱特征表
├── database/
│   ├── engine.py
│   ├── session.py
│   └── repositories/
│       ├── base.py
│       ├── market_repository.py
│       └── graph_repository.py
└── utils/
    ├── db.py
    └── db_postgres.py

migrations/
├── alembic.ini
├── env.py
└── versions/
    ├── 001_initial_schema.py
    ├── 002_add_collection_tables.py
    ├── 003_add_graph_meta_tables.py
    └── 004_add_graph_feature_tables.py
```

### 2.2 双轨并行策略

```text
Phase 1：模型层与旧兼容层共存
Phase 2：逐步迁移 Service 到 ORM Repository
Phase 3：采集、图谱、分析、回测模块统一切换到 ORM
Phase 4：保留必要兼容层，清理历史 SQL
```

---

## 3. 模型层设计

### 3.1 Base（`app/models/base.py`）

```python
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

### 3.2 现有核心模型保持不变

- `User`
- `Strategy`
- `MarketPrice`
- `MarketKline`
- `BacktestResult`
- `TradeOrder`
- `PolymarketUser`

本次重点是在现有 ORM 设计中补齐图谱相关元数据与特征表。

---

## 4. 图谱元数据模型设计

### 4.1 GraphEpisode（`app/models/graph_meta.py`）

```python
from datetime import datetime
from sqlalchemy import String, Text, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin


class GraphEpisode(Base, TimestampMixin):
    __tablename__ = "qd_graph_episodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    episode_type: Mapped[str] = mapped_column(String(50), nullable=False)
    market_domain: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(255))
    dedup_key: Mapped[str | None] = mapped_column(String(128), unique=True)
    importance_score: Mapped[float] = mapped_column(Numeric(6, 4), default=0.5)
    event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    observed_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    error_message: Mapped[str | None] = mapped_column(Text)
```

### 4.2 GraphJob

```python
class GraphJob(Base, TimestampMixin):
    __tablename__ = "qd_graph_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    episode_id: Mapped[int | None] = mapped_column(nullable=True)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    retry_count: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

### 4.3 GraphEntityRef

```python
class GraphEntityRef(Base, TimestampMixin):
    __tablename__ = "qd_graph_entity_refs"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_uid: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_table: Mapped[str] = mapped_column(String(100), nullable=False)
    source_pk: Mapped[str] = mapped_column(String(100), nullable=False)
```

### 4.4 GraphRelationSnapshot

```python
class GraphRelationSnapshot(Base, TimestampMixin):
    __tablename__ = "qd_graph_relation_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    relation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    from_uid: Mapped[str] = mapped_column(String(255), nullable=False)
    to_uid: Mapped[str] = mapped_column(String(255), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(255))
    confidence: Mapped[float | None] = mapped_column(Numeric(6, 4))
    t_valid: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    t_invalid: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payload_json: Mapped[str | None] = mapped_column(Text)
```

---

## 5. 图谱特征模型设计

### 5.1 通用特征表

```python
from sqlalchemy import String, Numeric, Date


class GraphFeatureDaily(Base, TimestampMixin):
    __tablename__ = "qd_graph_feature_daily"

    id: Mapped[int] = mapped_column(primary_key=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    market: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_value: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="graph")
```

### 5.2 领域扩展特征表

可根据三大领域新增明细表：
- `qd_company_narrative_features`
- `qd_crypto_narrative_features`
- `qd_polymarket_market_features`

如果希望控制表数量，也可统一折叠为 `qd_graph_feature_daily + feature_group`。

---

## 6. 采集与图谱协同模型

### 6.1 CollectionRecord

建议在 ORM 中保留统一采集记录模型，用于：
- 幂等去重
- 原始记录追踪
- 反查 Episode 来源

### 6.2 与 GraphEpisode 的关系

推荐逻辑关系：
- `CollectionRecord` 记录“采集到什么”
- `GraphEpisode` 记录“哪些采集结果被送入图谱”
- `GraphJob` 记录“图谱任务执行结果”
- `GraphEntityRef` 记录“数据库主键如何映射到图谱实体”

---

## 7. Repository 设计建议

### 7.1 GraphRepository

建议新增：
- `save_episode()`
- `mark_episode_status()`
- `create_graph_job()`
- `update_graph_job()`
- `upsert_entity_ref()`
- `insert_feature_batch()`
- `get_features_by_symbol()`

### 7.2 MarketRepository

统一承接：
- 行情快照
- K 线
- 新闻
- 宏观指标
- Polymarket 市场与交易

---

## 8. Alembic 迁移策略

### 8.1 建议迁移顺序

1. `001_initial_schema.py`
2. `002_add_collection_tables.py`
3. `003_add_graph_meta_tables.py`
4. `004_add_graph_feature_tables.py`
5. `005_add_domain_feature_indexes.py`

### 8.2 迁移原则

- 所有新增表通过 Alembic 管理，禁止继续将结构补丁直接写回 `init.sql`
- 为高频查询列加索引
- 为幂等键、实体映射键、特征唯一键建立唯一约束

---

## 9. SQLAlchemy Session 管理策略

### 9.1 Engine 配置

保留原方案中的 QueuePool 设计，并补充建议：
- 图谱写入任务与主业务请求使用独立 Session 生命周期
- 批量入库场景使用 `bulk_save_objects` 或分批 commit
- 图谱特征批量落表单独开事务，避免污染主分析事务

### 9.2 Session 上下文约束

- API 请求：短事务
- 采集器任务：批量事务，分批提交
- GraphPipeline：Episode、Job、Feature 各自事务隔离

---

## 10. PostgreSQL 表建议

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

CREATE TABLE qd_graph_jobs (
    id SERIAL PRIMARY KEY,
    episode_id INTEGER,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(30) DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP NULL,
    finished_at TIMESTAMP NULL,
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
    updated_at TIMESTAMP DEFAULT NOW(),
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
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, market, symbol, feature_name)
);
```

---

## 11. 与 AI、策略、回测模块的 ORM 协同

### 11.1 AI 分析
- 通过 ORM Repository 读取结构化行情、新闻、图谱特征
- 不要求 AI 服务直接操作裸 SQL

### 11.2 策略引擎
- 从 `qd_graph_feature_daily` 批量读取因子
- 与传统技术因子统一输入策略框架

### 11.3 回测系统
- 通过日期切片批量读取历史图谱因子
- 避免直接访问 Neo4j，保证回测可复现性

---

## 12. 实施计划

| 周次 | 任务 |
|------|------|
| 第 1 周 | Base / Session / Engine 稳定化 |
| 第 2 周 | 市场、采集、新闻、Polymarket ORM 模型 |
| 第 3 周 | 图谱元数据模型（Episode / Job / EntityRef / Snapshot） |
| 第 4 周 | 图谱特征表、Repository、Alembic 迁移 |
| 第 5 周 | 采集链路和 GraphPipeline 接入 ORM |
| 第 6 周 | AI、策略、回测模块切换与兼容层收敛 |

---

*本方案待确认后方可执行实施。*
