# QuantDinger 架构改造总体技术方案

> 版本：v1.1  
> 日期：2026-04  
> 状态：待评审确认

---

## 目录

1. [改造背景与目标](#1-改造背景与目标)
2. [现状分析](#2-现状分析)
3. [目标架构全景](#3-目标架构全景)
4. [Graphiti 图谱化改造原则](#4-graphiti-图谱化改造原则)
5. [九大改造模块概览](#5-九大改造模块概览)
6. [技术选型汇总](#6-技术选型汇总)
7. [领域图谱化整合设计](#7-领域图谱化整合设计)
8. [数据协同与存储分层](#8-数据协同与存储分层)
9. [AI 分析、策略引擎与知识图谱集成](#9-ai-分析策略引擎与知识图谱集成)
10. [实施路线图](#10-实施路线图)
11. [风险评估与应对](#11-风险评估与应对)
12. [性能指标要求](#12-性能指标要求)
13. [安全设计原则](#13-安全设计原则)

---

## 1. 改造背景与目标

### 1.1 现有系统定位

QuantDinger 目前是一个以"指标 IDE + 回测 + 快捷交易"为核心的量化交易平台，支持：
- 加密货币、美股、港股、外汇、期货等多市场 K 线数据
- AI 驱动的快速技术分析
- Polymarket 预测市场数据采集与 AI 分析
- 多交易所实盘交易执行（Binance、OKX、Bybit 等）
- 策略回测与实验进化框架

### 1.2 改造动机

| 维度 | 当前问题 | 改造目标 |
|------|---------|---------|
| 数据库层 | 裸 psycopg2 + 手写 SQL，维护困难 | SQLAlchemy ORM，类型安全，迁移规范 |
| 数据采集 | 各模块分散采集，无统一规范 | 统一采集框架，去重清洗标准化 |
| 知识沉淀 | 数据孤岛，实体关系隐式 | Neo4j + Graphiti 时态知识图谱，显式关系建模 |
| AI 分析 | 依赖单一数据上下文 | 图谱驱动，多跳关联推理 |
| 策略研究 | 事件、关系、叙事难以量化 | 将图谱特征注入信号、回测与风控 |

### 1.3 核心改造目标

```
市场原始数据 / 新闻 / 链上事件 / 预测市场行为
    ↓ [统一采集层]
标准化数据仓库（PostgreSQL） + 实时缓存（Redis）
    ↓ [Graphiti 图谱编排]
Neo4j 时态关系图谱 + 图谱快照/Embedding 索引
    ↓ [AI 增强分析 / 策略研究 / 风险传播分析]
智能投资洞察 + 图谱驱动推荐 + 图谱因子回测
```

### 1.4 本次改造总原则

1. **增强而非替换**：保留现有市场数据采集器、AI 分析服务、策略引擎、回测框架，只在关键节点接入 Graphiti 图谱能力。
2. **结构化与图谱双写**：结构化主数据和数值型时间序列仍以 PostgreSQL 为主，Graphiti/Neo4j 承载关系、事件、叙事和时间感知事实。
3. **Redis 继续承担实时层职责**：图谱查询结果、热点子图、关系评分、AI 增强上下文摘要进入 Redis 缓存，避免放大 Neo4j 查询压力。
4. **面向三大领域统一抽象**：股票、加密货币、预测市场遵循统一的 Episode → Entity/Relation → Subgraph → AI/Strategy Consumption 流程。
5. **兼容现有知识图谱基础设施**：在已有 Neo4j 基础设施方案之上引入 Graphiti 作为图谱构建与时态记忆编排层，而不是再建设一套平行图谱系统。

---

## 2. 现状分析

### 2.1 当前技术栈

```
后端：Flask + psycopg2 (裸 SQL) + Redis
数据源：CCXT / yfinance / Finnhub / AkShare / MT5 / IBKR
AI：LLM 负载均衡（多模型）
缓存：Redis
部署：Docker Compose
图谱：Neo4j（规划中）
```

### 2.2 数据库现状

- **连接方式**：`psycopg2.pool.ThreadedConnectionPool`，手工管理连接生命周期
- **SQL 编写**：各 Service 直接拼接 SQL 字符串，无 ORM 抽象
- **迁移管理**：单一 `init.sql` 文件，含大量 `DO $$ ... $$` 补丁块，历史混乱
- **问题**：占位符兼容层（`?` → `%s`）、RETURNING id 的 SAVEPOINT 黑科技，技术债严重

### 2.3 数据采集与分析现状

- 各数据源（Polymarket、Crypto、Stock、Forex）分散在独立模块
- 无统一的采集调度、去重、清洗、归档机制
- AI 分析以价格、指标、新闻摘要为主，图谱多跳推理能力不足
- 策略引擎与回测系统以行情因子为主，尚未纳入事件关系、资金传播、叙事演化等图谱特征

### 2.4 Graphiti 引入前的关键缺口

| 能力 | 当前缺口 | Graphiti 引入后的补强方向 |
|------|---------|---------------------------|
| 时态事实管理 | 关系变化主要靠覆盖更新 | 用有效时间/失效时间维护历史关系演化 |
| 非结构化知识沉淀 | 新闻、研报、推文难持续结构化 | 将文本作为 Episode 增量抽取实体与关系 |
| 跨域推理 | 股票/加密/预测市场联动弱 | 建立跨市场事件、人物、机构、叙事桥接关系 |
| AI 长期记忆 | 分析上下文短、易丢失 | 基于 Graphiti 维护可检索的长期时态记忆 |
| 策略解释性 | 信号溯源不足 | 输出图谱路径、影响链和证据子图 |

### 2.5 关键文件分布

```
backend_api_python/
├── app/utils/db.py              # 数据库统一入口（转发到 db_postgres.py）
├── app/utils/db_postgres.py     # psycopg2 连接池 + 兼容层（核心改造对象）
├── app/config/database.py       # Redis 配置
├── migrations/init.sql          # Schema 定义（需要迁移到 Alembic）
├── app/data_sources/            # 各市场数据源
├── app/services/market_data_collector.py  # 市场数据采集（AI 分析专用）
└── app/data_sources/polymarket.py         # Polymarket 数据源
```

---

## 3. 目标架构全景

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            QuantDinger 目标架构                               │
├──────────────────────────────────────────────────────────────────────────────┤
│ 前端 (Vue.js) / 管理后台 / 分析工作台                                         │
├──────────────────────────────────────────────────────────────────────────────┤
│ API 层 (Flask Routes / Gateway)                                               │
├──────────┬──────────┬──────────┬────────────┬────────────┬──────────────────┤
│ 策略服务 │ 回测服务 │ 交易服务 │ AI 分析服务 │ 图谱查询服务 │ 采集调度/工作流服务 │
├──────────┴──────────┴──────────┴────────────┴────────────┴──────────────────┤
│                数据访问层（SQLAlchemy ORM + Repository + Graph Gateway）      │
├───────────────────────────┬──────────────────────────┬──────────────────────┤
│ PostgreSQL                │ Redis                    │ Neo4j + Graphiti     │
│ 结构化主数据/时序快照/回测 │ 热点行情/图谱摘要缓存/任务状态 │ 时态关系图谱/事件记忆/子图检索 │
├───────────────────────────┴──────────────────────────┴──────────────────────┤
│                       统一市场数据采集与标准化层                               │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┤
│ Crypto   │ Stock    │ Forex    │ Macro    │ News     │ Polymkt  │ On-chain │
│ CCXT等   │ yfinance │ MT5/IBKR │ FRED等   │ Finnhub等│ Gamma等  │ Etherscan│
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
                                ↓
                 Graphiti Episode Builder / Dify Workflow / ETL Jobs
```

---

## 4. Graphiti 图谱化改造原则

### 4.1 Graphiti 在现有架构中的定位

Graphiti 不直接替代 PostgreSQL、Neo4j 或现有采集器，而是承担以下职责：

1. **Episode 摄入编排层**：把新闻、公告、推文、链上事件、市场状态变化转化为统一 Episode。
2. **时态知识抽取层**：借助 LLM + 本体约束，从 Episode 中抽取实体、关系、事件，并为关系维护有效时间窗口。
3. **冲突与演化管理层**：当新事实与旧事实冲突时，Graphiti 负责失效旧关系并生成新关系，保留历史可追溯性。
4. **GraphRAG 检索层**：为 AI 分析、图谱查询 API、策略研究提供相关子图、关系路径和叙事上下文。

### 4.2 引入方式

- 保留现有 Neo4j 作为图数据库后端。
- 在 `统一采集系统` 和 `知识图谱基础设施` 之间新增 `Graphiti 编排层`。
- 对结构化数据不重复建模：证券价格、K 线、订单簿、回测结果仍存于 PostgreSQL。
- 对高频数值更新不直接写图：图谱只保留状态变化、事件标签、关键价格区间、关系变化和置信度。

### 4.3 统一 Episode 规范

统一定义 `EpisodeEnvelope`，覆盖三大领域：
- `episode_type`: news / filing / onchain_event / prediction_market_tick / research / social_post
- `market_domain`: stock / crypto / polymarket
- `entity_keys`: ticker / contract / wallet / market_id / person / institution
- `event_time`: 事件发生时间
- `observed_time`: 系统采集时间
- `raw_payload_ref`: PostgreSQL 原始记录 ID 或对象存储引用
- `importance_score`: 事件重要度
- `dedup_key`: 内容或事件去重键

---

## 5. 九大改造模块概览

| 序号 | 模块 | 详细方案文档 | 优先级 | 预估工期 |
|------|------|-------------|--------|---------|
| 1 | SQLAlchemy ORM 重构 | [ORM_MIGRATION_PLAN_CN.md](./ORM_MIGRATION_PLAN_CN.md) | P0 | 3-4 周 |
| 2 | 统一市场数据采集系统 | [UNIFIED_DATA_COLLECTION_CN.md](./UNIFIED_DATA_COLLECTION_CN.md) | P0 | 4-5 周 |
| 3 | Neo4j + Graphiti 图谱基础设施 | [KNOWLEDGE_GRAPH_INFRA_CN.md](./KNOWLEDGE_GRAPH_INFRA_CN.md) | P0 | 4-6 周 |
| 4 | 股票市场实体关系图谱化 | [GRAPH_FINANCIAL_MARKET_CN.md](./GRAPH_FINANCIAL_MARKET_CN.md) + [graphiti-stock.md](./graphiti-stock.md) | P1 | 3-4 周 |
| 5 | 加密货币图谱化 | [GRAPH_CRYPTO_ACCOUNT_CN.md](./GRAPH_CRYPTO_ACCOUNT_CN.md) + [graphiti-crypto.md](./graphiti-crypto.md) | P1 | 3-4 周 |
| 6 | 预测市场图谱化 | [GRAPH_POLYMARKET_CN.md](./GRAPH_POLYMARKET_CN.md) + [graphiti-polymarket.md](./graphiti-polymarket.md) | P1 | 2-3 周 |
| 7 | AI 分析增强 | [AI_ANALYSIS_ENHANCEMENT_CN.md](./AI_ANALYSIS_ENHANCEMENT_CN.md) | P1 | 3-4 周 |
| 8 | 图谱因子与策略回测增强 | 与策略/回测模块联动 | P1 | 2-4 周 |
| 9 | 图谱缓存、治理与监控 | 与基础设施模块联动 | P1 | 2-3 周 |

---

## 6. 技术选型汇总

### 6.1 核心技术栈

| 类别 | 选型 | 版本要求 | 理由 |
|------|------|---------|------|
| ORM | SQLAlchemy | ≥ 2.0 | 统一数据访问层，支持迁移治理 |
| 数据库迁移 | Alembic | ≥ 1.13 | SQLAlchemy 官方配套 |
| 图数据库 | Neo4j | ≥ 5.x | 关系查询成熟，适合作为 Graphiti 后端 |
| Graphiti 编排 | Graphiti | 与 Python 运行时兼容的稳定版本 | 提供 Episode 驱动、时态图谱、GraphRAG 能力 |
| Neo4j 驱动 | neo4j-driver | ≥ 5.x | 官方驱动 |
| 调度 | APScheduler | ≥ 3.10 | 统一采集与图谱构建调度 |
| 工作流引擎 | Dify | 最新 | 编排 LLM 与图谱工作流 |
| 数据清洗 | pandas | ≥ 1.5 | 标准化处理 |
| HTTP 客户端 | httpx / aiohttp | ≥ 0.27 / ≥ 3.9 | 异步采集 |
| 缓存 | Redis | 现有版本体系 | 承担热点图谱摘要、任务状态、临时结果缓存 |

### 6.2 新增依赖清单

```txt
# ORM & 迁移
alembic>=1.13.0
SQLAlchemy>=2.0.0

# Graph / Neo4j / Graphiti
neo4j>=5.0.0
neomodel>=5.3.0
graphiti-core>=0.8.0

# 调度与异步采集
APScheduler>=3.10.0
httpx>=0.27.0
aiohttp>=3.9.0
tenacity>=8.3.0

# 宏观与抽取增强
fredapi>=0.5.0
spacy>=3.7.0
```

### 6.3 关键技术决策

| 问题 | 决策 |
|------|------|
| 图谱主存储 | Neo4j 负责图存储，Graphiti 负责图谱构建与时态管理 |
| 实时行情存储 | PostgreSQL + Redis，不进入 Graphiti 主图 |
| 图谱查询加速 | 热点子图、AI 上下文摘要、关系分数缓存到 Redis |
| 关系来源追溯 | 关系边统一携带 `source_ref`、`confidence`、`t_valid`、`t_invalid` |
| 跨域统一键 | 采用 `global_entity_id` 与 `canonical_symbol` 机制 |

---

## 7. 领域图谱化整合设计

### 7.1 股票市场图谱化改造

结合 `graphiti-stock.md` 与现有 `GRAPH_FINANCIAL_MARKET_CN.md`，股票市场图谱由“公司-人物-机构-事件-新闻-宏观因子”升级为时态知识图谱。

#### 7.1.1 核心实体
- `Company`：上市公司、ETF 发行人、指数成分主体
- `Executive` / `Person`：高管、内部人、关键分析师
- `Institution`：基金、券商、股东、做市商
- `MacroIndicator`：利率、CPI、就业、汇率指数
- `Event`：财报、并购、监管处罚、产品发布、指数调仓
- `Asset`：股票、ETF、行业指数
- `NarrativeTag`：AI、半导体、降息交易、供给紧张等

#### 7.1.2 关键关系
- `EMPLOYED_BY`
- `HOLDS_SHARES`
- `SUPPLY_CHAIN_OF`
- `MENTIONED_IN`
- `AFFECTED_BY`
- `CORRELATED_WITH`
- `HAS_NARRATIVE`

#### 7.1.3 与现有采集系统整合
- 复用 `yfinance / Finnhub / AkShare / 新闻采集器` 获取结构化基础面、持股、公告、新闻。
- 将公告、新闻、研报摘要转为 Episode 输入 Graphiti，增量抽取并更新：
  - 公司上下游关系
  - 高管变更
  - 机构持股变化
  - 宏观事件冲击链
- 对价格、K 线和财务指标不在图谱中逐条存储，只抽取“关键状态变化”与“事件标签”。

#### 7.1.4 图谱增强价值
- 提升新闻到公司到板块的多跳推理能力。
- 支持“供应链冲击 → 二级市场受影响标的”路径分析。
- 在 AI 研判中加入时间敏感的叙事变迁，例如“AI 服务器概念热度增强”。

### 7.2 加密货币图谱化改造

结合 `graphiti-crypto.md` 与现有 `GRAPH_CRYPTO_ACCOUNT_CN.md`，将原有账号关系图谱扩展为“资产-协议-账户-链上行为-叙事-事件”时态图谱。

#### 7.2.1 核心实体
- `Asset`：BTC、ETH、SOL、稳定币、Meme 币
- `Protocol`：DEX、借贷、跨链桥、L2、质押协议
- `CryptoAccount`：鲸鱼地址、KOL、基金地址、交易所热钱包
- `MarketEvent`：被攻击、上线、解锁、治理投票、ETF 通过
- `Chain`：Ethereum、Solana、Base、Arbitrum
- `NarrativeTag`：Restaking、AI Agent、Meme、RWA

#### 7.2.2 关键关系
- `DEPLOYED_ON`
- `HOLDS`
- `TRANSFERRED_TO`
- `PAIRED_WITH`
- `IMPACTED_BY`
- `PROMOTED_BY`
- `HAS_NARRATIVE`

#### 7.2.3 与现有采集系统整合
- 复用现有 `CCXT / CoinGecko / 链上地址采集器 / 新闻采集器`。
- 新增链上异常事件、鲸鱼转账、协议 TVL 变化等 Episode Builder。
- Graphiti 仅保留：
  - 协议部署关系
  - 地址持仓与资金流变化摘要
  - 重大链上事件及影响路径
  - 叙事热度标签的时间演化
- 高频盘口、逐笔成交、分钟级全量价格仍存 PostgreSQL/Redis。

#### 7.2.4 图谱增强价值
- 为 AI 提供“叙事漂移”“风险传染”“KOL 共识”分析能力。
- 让策略引擎可构建鲸鱼跟随、解锁风险、事件扩散等图谱因子。
- 将链上事件与中心化交易所价格表现建立更强的解释链。

### 7.3 预测市场图谱化改造

结合 `graphiti-polymarket.md` 与现有 `GRAPH_POLYMARKET_CN.md`，将预测市场从用户社交图谱升级为“市场-结果-账户-外部事件-现实资产”的时态因果图谱。

#### 7.3.1 核心实体
- `PredictionMarket`
- `Outcome`
- `PolymarketUser`
- `ExternalEvent`
- `ResolutionSource`
- `LinkedAsset`：与预测主题强相关的股票、币种、行业指数

#### 7.3.2 关键关系
- `HAS_ODDS`
- `TRADED_IN`
- `CO_TRADED`
- `TRIGGERED_BY`
- `CORRELATED_WITH`
- `PREDICTS`
- `LINKED_TO_ASSET`

#### 7.3.3 与现有采集系统整合
- 复用 Gamma/Data API 采集市场、持仓、交易、用户画像。
- 将突发新闻、政策、选举、监管、体育结果进展构造成 Episode。
- 用 Graphiti 管理概率演化背后的事件路径，而不是单纯记录最新赔率。
- 将预测市场与股票/加密资产建立跨市场桥接节点，用于先行指标分析。

#### 7.3.4 图谱增强价值
- 支持“赔率异动归因”。
- 支持“预测市场概率变化 → 股票/加密资产联动交易”的图谱推理。
- 支持聪明钱行为图谱与事件驱动信号融合。

### 7.4 跨域桥接设计

三大领域最终不是三套孤立图谱，而是共享以下桥接层：
- `Person / Institution`：同一人物、基金、KOL 跨市场参与
- `Event / ExternalEvent`：宏观政策、监管裁决、ETF 审批、战争选举等事件跨市场传播
- `NarrativeTag`：AI、通胀、降息、监管宽松、Meme 热点等叙事可跨股票/加密/预测市场传播
- `AssetLink`：Polymarket 市场问题可以映射到股票或加密资产集合

---

## 8. 数据协同与存储分层

### 8.1 PostgreSQL、Redis、Neo4j、Graphiti 协同职责

| 组件 | 主要职责 | 适合存储内容 | 不适合存储内容 |
|------|---------|-------------|---------------|
| PostgreSQL | 结构化主数据与事实台账 | K线、价格快照、新闻原文、用户交易、回测结果、采集记录 | 深层关系遍历 |
| Redis | 实时层与热点缓存 | 最新价格、热点子图摘要、图谱查询缓存、AI 上下文缓存、任务状态 | 长期主存储 |
| Neo4j | 图关系主查询引擎 | 实体、关系、事件路径、影响链、跨域链接 | 高频数值时间序列 |
| Graphiti | 图谱构建与时态记忆编排 | Episode、关系演化、冲突解决、GraphRAG 检索 | 独立替代所有业务库 |

### 8.2 推荐数据流

```text
Collector -> Normalizer -> PostgreSQL
                         -> Redis(最新快照/去重键/调度状态)
                         -> Episode Builder -> Graphiti -> Neo4j
                                                   -> Redis(子图缓存/上下文摘要)
                                                   -> AI / Strategy / Backtest Consumer
```

### 8.3 PostgreSQL 新增分层建议

新增或扩展以下表族：
- `qd_graph_episodes`：保存 Episode 元数据、来源、状态、重试信息
- `qd_graph_entity_refs`：维护 PostgreSQL 主键与图谱实体 UID 映射
- `qd_graph_relation_snapshots`：对关键关系做快照留存，便于审计与回放
- `qd_graph_feature_daily`：将图谱特征落表供策略/回测使用
- `qd_graph_jobs`：图谱构建任务、失败重试、耗时统计

### 8.4 Redis 使用建议

Redis 除行情缓存外，新增以下用途：
- `graph:subgraph:{domain}:{entity}`：热点子图缓存
- `graph:context:{market}:{symbol}`：AI 分析上下文缓存
- `graph:feature:{market}:{symbol}`：图谱因子短期缓存
- `graph:episode:dedup:{hash}`：Episode 去重与幂等控制
- `graph:task:status:{job_id}`：图谱构建与 AI 工作流状态

### 8.5 一致性策略

- PostgreSQL 为主事实账本，Neo4j 为关系视图，允许秒级至分钟级最终一致。
- Graphiti 写图采用异步流水线，失败可基于 `qd_graph_episodes` 重放。
- Redis 全部视为派生缓存，可随时失效重建。

---

## 9. AI 分析、策略引擎与知识图谱集成

### 9.1 AI 分析增强

在现有 `fast_analysis.py`、`market_data_collector.py` 基础上，新增 `GraphContextBuilder + EpisodeRetriever`：

1. 根据 `market + symbol` 检索 Redis 热缓存。
2. 未命中时由 Graphiti/Neo4j 生成相关子图。
3. 将以下上下文拼装进 LLM Prompt：
   - 关联实体与关系路径
   - 最近关键事件及时间顺序
   - 叙事变化摘要
   - 置信度最高的影响链
4. 保持失败降级：图谱不可用时，AI 分析自动退回原有分析路径。

### 9.2 策略引擎增强

现有策略引擎、回测框架保留不变，只新增图谱因子输入层：
- 股票：共同股东强度、供应链冲击分数、事件情感扩散分数
- 加密：鲸鱼净流向、KOL 共识度、协议风险传播分数、Narrative Drift 指数
- 预测市场：聪明钱一致性、市场异动归因分数、跨市场先行信号分数

图谱因子以日频/小时频落入 PostgreSQL，供回测系统读取，不要求回测引擎直接实时访问 Neo4j。

### 9.3 回测系统增强

- 新增 `GraphFeatureLoader`，在回测前批量拉取 `qd_graph_feature_daily`。
- 保证历史回测使用的是“历史时点可见图谱”，避免未来函数污染。
- 对 Graphiti 的时态关系按 `t_valid/t_invalid` 做历史切片，生成当时可见子图。

### 9.4 风控与解释性增强

- 当策略发出信号时，同时保留触发该信号的图谱证据摘要。
- 在风控模块中增加“事件冲击链”“主体关联风险”“跨市场传染路径”校验。
- 在 AI 输出中展示可解释的关系链，而不是只有结论。

---

## 10. 实施路线图

### Phase 0：基础设施准备（第 1-2 周）

- [ ] Docker Compose 添加 Neo4j 容器
- [ ] 评估并引入 Graphiti 运行时依赖
- [ ] 配置 Neo4j / Graphiti / Redis 连接参数
- [ ] 添加 Alembic 配置文件
- [ ] 将现有 `init.sql` 转换为 Alembic 初始 Migration

### Phase 1：ORM 与图谱元数据层（第 3-6 周）

- [ ] 创建 SQLAlchemy 模型层（含 graph episode / feature / mapping 表）
- [ ] 实现 Session 工厂与上下文管理
- [ ] 保持旧兼容层共存，逐步替换裸 SQL
- [ ] 建立结构化主键到图谱 UID 的映射规范

### Phase 2：统一采集 + Episode Builder（第 5-9 周）

- [ ] 设计统一采集器接口（`BaseCollector`）
- [ ] 实现三大领域采集器标准化输出
- [ ] 实现去重 + 清洗 + PostgreSQL 落库
- [ ] 新增 Episode Builder，将新闻/公告/链上事件/赔率异动转为 Graphiti 输入
- [ ] APScheduler 调度任务配置
- [ ] Dify/内部工作流触发器集成

### Phase 3：Graphiti 图谱基础设施（第 7-11 周）

- [ ] 设计统一实体、本体、关系与时间字段规范
- [ ] 实现 Graphiti -> Neo4j 写入与冲突更新逻辑
- [ ] 建立图谱查询 API、GraphRAG 检索 API
- [ ] 增加 Redis 子图缓存与上下文缓存

### Phase 4：三大专项图谱（第 9-14 周）

- [ ] 股票市场图谱化：公司/机构/人物/宏观/供应链
- [ ] 加密货币图谱化：资产/协议/地址/链上事件/叙事
- [ ] 预测市场图谱化：市场/用户/结果/外部事件/跨市场映射
- [ ] 打通跨域桥接实体与统一标签体系

### Phase 5：AI 与策略回测增强（第 13-17 周）

- [ ] 图谱上下文注入 AI 分析
- [ ] 多跳关联推理与事件影响链输出
- [ ] 图谱因子生成、落表与回测接入
- [ ] 图谱驱动风险预警、异常归因与信号解释

### Phase 6：治理、监控与优化（第 16-18 周）

- [ ] 图谱质量评分、关系置信度校验、人工审核入口
- [ ] 图谱任务监控、失败重试、延迟观测
- [ ] 高热点资产/市场的缓存策略优化
- [ ] 成本评估与模型调用预算控制

---

## 11. 风险评估与应对

| 风险 | 概率 | 影响 | 应对策略 |
|------|------|------|---------|
| Graphiti 抽取结果不稳定 | 中 | 高 | 本体约束 + 置信度阈值 + 人工审核 + 可重放 Episode |
| ORM 迁移中断线上服务 | 中 | 高 | 双轨并行，逐模块替换 |
| Neo4j / Graph 查询压力升高 | 中 | 中 | Redis 缓存热点子图 + 限制查询深度 + 预计算关系分数 |
| 高频数据误入图谱导致膨胀 | 高 | 高 | 图谱只存状态变化与关键事件，不存逐笔与全量 ticker |
| 跨域实体对齐错误 | 中 | 高 | 引入 canonical id / alias / source_ref 机制，保留人工修正 |
| 外部 API 限流影响采集 | 高 | 中 | 多源备用 + 限速 + 指数退避 |
| LLM 成本与时延增加 | 中 | 中 | Episode 分级处理，重要事件走 Graphiti，低价值数据仅结构化存储 |

---

## 12. 性能指标要求

| 指标 | 当前 | 目标 |
|------|------|------|
| API 响应时间（P95） | ~2s | <1s |
| 数据采集延迟（实时数据） | ~30s | <10s |
| 图谱查询延迟（2 跳） | N/A | <200ms |
| GraphRAG 上下文构建（缓存命中） | N/A | <80ms |
| GraphRAG 上下文构建（未命中） | N/A | <800ms |
| 图谱任务成功率 | N/A | >98% |
| 图谱因子日生成成功率 | N/A | >99% |
| 数据库连接池利用率 | 峰值 80%+ | 稳定 <60% |
| 采集数据去重率 | 0%（无机制） | >99% |

---

## 13. 安全设计原则

1. **数据库凭证**：所有密钥通过环境变量注入，禁止硬编码。
2. **Neo4j / Graphiti 访问**：仅内网访问，不暴露外部端口（除非明确需要）。
3. **API 密钥轮转**：采集器 API Key 支持多 Key 轮转，避免单点失效。
4. **数据脱敏**：用户相关的图谱节点不存储敏感个人信息，地址/账号按需求脱敏展示。
5. **SQL 注入防护**：ORM 参数化查询，消除手拼 SQL 风险。
6. **图谱审计**：所有重要关系保留 `source_ref`、`confidence`、时间戳与回放能力。
7. **速率限制**：对外部 API 调用实施速率限制，避免被封禁。
8. **权限隔离**：图谱写入、图谱查询、AI 推理调用使用不同凭证与权限边界。

---

*子模块详细方案见各独立文档，所有方案待确认后方可执行实施。*
