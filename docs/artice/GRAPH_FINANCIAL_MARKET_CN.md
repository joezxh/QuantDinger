# 金融市场 Graphiti 时态图谱方案

> 版本：v1.1 | 优先级：P1 | 预估工期：3-4 周

---

## 1. 目标

- 采集上市公司、股东、机构投资者、内部人、新闻、公告、宏观因子等数据
- 在现有企业/股东/新闻图谱基础上，引入 Graphiti 构建时态知识图谱
- 将企业关系、持股变化、管理层变更、供应链和叙事演化纳入统一图谱模型
- 支持 AI 分析、策略回测、风险传导和事件归因等场景

---

## 2. 方案定位

本方案不是替换现有 `GRAPH_FINANCIAL_MARKET_CN.md` 中的 Neo4j 设计，而是在其基础上增加：
- Episode 驱动的数据入图机制
- 时间感知的关系演化管理
- GraphRAG 子图检索能力
- 与 PostgreSQL、Redis、AI 分析和回测引擎的协同

图谱职责边界：
- **PostgreSQL**：价格、财务、公告原文、持股原始记录、图谱特征
- **Neo4j**：实体关系、影响链、桥接关系
- **Graphiti**：对新闻/公告/研报/事件进行时态抽取与冲突更新
- **Redis**：缓存热点公司子图和增强上下文

---

## 3. 数据来源

| 数据类型 | 来源 |
|---------|------|
| 美股公司基本面 | Finnhub company_profile2（已集成） |
| 美股机构持股 | Finnhub ownership API |
| 美股内部人交易 | Finnhub insider-transactions |
| A股/港股基本面 | AkShare（已集成） |
| A股股东数据 | AkShare stock_holder_* |
| 新闻与情感 | Finnhub + 搜索引擎（已集成） |
| 公告 / 财报摘要 | 交易所公告 / 第三方接口 |
| 宏观事件 | FRED / 政策新闻 / 央行公告 |
| 关系抽取 | Graphiti + LLM |

---

## 4. Episode 驱动采集设计

### 4.1 需要进入 Graphiti 的事件类型

- 机构持股显著变化
- 高管变更 / 内部人大额交易
- 公司并购、合作、诉讼、产品发布
- 财报、指引、盈利预警
- 宏观事件对行业或个股的冲击
- 新闻中出现的重要供应链、竞争、投资关系

### 4.2 Episode 示例

```python
CollectedItem(
    source="finnhub_news",
    data_type="stock_news",
    market="USStock",
    symbol="NVDA",
    raw_data=news,
    normalized_data={
        "ticker": "NVDA",
        "headline": news.get("headline"),
        "summary": news.get("summary"),
        "published_at": news.get("datetime"),
        "sentiment": "positive",
    },
    importance_score=0.82,
    should_build_episode=True,
    entity_keys={"ticker": "NVDA"},
)
```

### 4.3 Episode 内容来源

- 新闻正文
- 公告摘要
- 财报重点段落
- 内部人交易说明
- 宏观事件摘要

---

## 5. Graphiti 本体设计

### 5.1 核心实体

- `Company`：上市公司、ETF 发行主体、指数成分主体
- `Person`：CEO、CFO、董事、内部人、分析师
- `Institution`：基金、券商、股东、投行、监管机构
- `Asset`：股票、ETF、行业指数
- `MacroIndicator`：CPI、利率、就业、DXY
- `Event`：财报、政策、诉讼、并购、产品发布、指数调仓
- `NewsArticle`：新闻、公告、研报
- `NarrativeTag`：AI、半导体、降息交易、供应链修复等

### 5.2 关键关系

| 关系 | 含义 | 时态性 |
|------|------|------|
| `HOLDS_SHARES` | 机构/个人持股 | 强 |
| `EMPLOYED_BY` | 高管任职 | 强 |
| `TRADED_STOCK` | 内部人买卖 | 中 |
| `SUPPLY_CHAIN_OF` | 上下游关系 | 强 |
| `MENTIONED_IN` | 新闻提及 | 弱 |
| `AFFECTS` | 事件影响公司/资产 | 中 |
| `CORRELATED_WITH` | 相关性关系 | 中 |
| `HAS_NARRATIVE` | 叙事标签 | 强 |
| `ISSUED` | 公司对应资产 | 弱 |

### 5.3 时间字段规范

所有时态关系统一携带：
- `t_valid`
- `t_invalid`
- `source_ref`
- `confidence`
- `updated_at`

---

## 6. Neo4j 图谱模型

### 6.1 节点

```cypher
MERGE (c:Company {uid: $uid})
SET c.ticker = $ticker,
    c.name = $name,
    c.industry = $industry,
    c.country = $country,
    c.exchange = $exchange,
    c.market_cap = $market_cap,
    c.updated_at = datetime()

MERGE (inst:Institution {uid: $inst_uid})
SET inst.name = $name,
    inst.type = $type,
    inst.updated_at = datetime()

MERGE (p:Person {uid: $person_uid})
SET p.name = $name,
    p.role = $role,
    p.updated_at = datetime()

MERGE (a:Asset {uid: $asset_uid})
SET a.symbol = $ticker,
    a.market = $market,
    a.name = $name,
    a.updated_at = datetime()
```

### 6.2 时态关系

```cypher
MATCH (inst:Institution {uid: $inst_uid})
MATCH (co:Company {uid: $company_uid})
MERGE (inst)-[r:HOLDS_SHARES {source_ref: $source_ref, t_valid: $t_valid}]->(co)
SET r.shares_pct = $shares_pct,
    r.value_usd = $value_usd,
    r.confidence = $confidence,
    r.t_invalid = $t_invalid,
    r.updated_at = datetime()

MATCH (p:Person {uid: $person_uid})
MATCH (co:Company {uid: $company_uid})
MERGE (p)-[r:EMPLOYED_BY {source_ref: $source_ref, t_valid: $t_valid}]->(co)
SET r.role = $role,
    r.t_invalid = $t_invalid,
    r.confidence = $confidence,
    r.updated_at = datetime()
```

---

## 7. Graphiti 处理流程

### 7.1 处理步骤

1. 采集器将新闻、公告、持股变化写入 PostgreSQL。
2. `EpisodeBuilder` 将文本/事件转换为 Episode。
3. Graphiti 抽取公司、人物、机构、事件和叙事标签。
4. 若发现旧事实冲突，则关闭旧边 `t_invalid`，写入新边。
5. 结果写入 Neo4j，并更新 Redis 热点上下文缓存。

### 7.2 示例场景

#### 场景 1：CEO 更换
- 旧关系：`Alice -[:EMPLOYED_BY]-> CompanyA`
- 新公告：`Bob 出任 CEO`
- Graphiti 动作：
  - 失效 Alice 的 `EMPLOYED_BY`
  - 建立 Bob 的新任职关系
  - 保留历史时间窗

#### 场景 2：供应链变化
- 新闻显示某芯片厂切换核心供应商
- Graphiti 更新 `SUPPLY_CHAIN_OF` 的有效时间
- AI 分析可查询切换前后的风险影响链

---

## 8. 关键分析查询

```cypher
// 两公司共同股东
MATCH (co1:Company {ticker: $t1})<-[:HOLDS_SHARES]-(inst:Institution)
      -[:HOLDS_SHARES]->(co2:Company {ticker: $t2})
RETURN inst.name AS common_holder, inst.type AS type

// 事件 -> 公司 -> 资产影响链
MATCH (e:Event {uid: $event_uid})-[:AFFECTS]->(co:Company)-[:ISSUED]->(a:Asset)
RETURN e.title, co.ticker, a.symbol

// 同行业共同持股网络
MATCH (co:Company {industry: $ind})
MATCH (co)<-[:HOLDS_SHARES]-(inst)-[:HOLDS_SHARES]->(other:Company)
WHERE other.industry = $ind AND co <> other
RETURN co.ticker, other.ticker, count(DISTINCT inst) AS shared_holders
ORDER BY shared_holders DESC LIMIT 20

// 叙事演化查询
MATCH (co:Company {ticker: $ticker})-[r:HAS_NARRATIVE]->(n:NarrativeTag)
RETURN n.name, r.score, r.t_valid, r.t_invalid
ORDER BY r.t_valid DESC
```

---

## 9. LLM / Graphiti 实体关系抽取

Graphiti 替代原先的“纯 LLM 一次性抽取”模式，优势在于：
- 支持时态关系更新
- 支持实体消歧
- 支持关系冲突处理
- 支持后续 GraphRAG 检索

仍可保留轻量级 JSON 抽取器用于预处理，但最终关系以 Graphiti 写图为准。

---

## 10. PostgreSQL 表设计

```sql
CREATE TABLE qd_shareholdings (
    id SERIAL PRIMARY KEY,
    company_ticker VARCHAR(20) NOT NULL,
    holder_name VARCHAR(255) NOT NULL,
    holder_type VARCHAR(50),
    shares_pct DECIMAL(10, 4),
    shares_count BIGINT,
    value_usd DECIMAL(20, 2),
    source VARCHAR(50) DEFAULT 'finnhub',
    collected_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(company_ticker, holder_name)
);

CREATE TABLE qd_insider_trades (
    id SERIAL PRIMARY KEY,
    company_ticker VARCHAR(20) NOT NULL,
    insider_name VARCHAR(255),
    transaction_type VARCHAR(10),
    shares BIGINT,
    price DECIMAL(20, 4),
    trade_date DATE,
    source VARCHAR(50) DEFAULT 'finnhub',
    collected_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE qd_company_narrative_features (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    narrative_name VARCHAR(100) NOT NULL,
    narrative_score DECIMAL(10, 4) NOT NULL,
    source VARCHAR(50) DEFAULT 'graph',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, ticker, narrative_name)
);
```

---

## 11. AI 与回测集成

### 11.1 AI 分析增强
- 注入共同股东信息
- 注入供应链关联和冲击路径
- 注入近 30 天叙事变化摘要
- 注入宏观影响链

### 11.2 策略与回测增强
建议生成以下图谱因子：
- `shared_holder_strength`
- `insider_buy_signal_score`
- `supply_chain_risk_score`
- `macro_impact_score`
- `narrative_heat_score`

这些因子落入 PostgreSQL，供回测引擎使用。

---

## 12. Redis 缓存建议

```text
graph:context:stock:{ticker}
graph:subgraph:stock:{ticker}
graph:feature:stock:{ticker}:narrative
graph:event-chain:{event_uid}
```

---

## 13. API 接口建议

| 接口 | 说明 |
|------|------|
| `GET /api/graph/stock/company/{ticker}` | 公司图谱详情 |
| `GET /api/graph/stock/common-holders` | 共同股东分析 |
| `GET /api/graph/stock/supply-chain/{ticker}` | 供应链路径分析 |
| `GET /api/graph/stock/narrative-drift/{ticker}` | 叙事演化分析 |
| `GET /api/graph/stock/event-impact/{event_uid}` | 事件影响链 |

---

## 14. 实施计划

| 周次 | 任务 |
|------|------|
| 第 1 周 | 公司/机构/人物基础模型与 PostgreSQL 落表 |
| 第 2 周 | Episode Builder、Graphiti 抽取与时态关系写入 |
| 第 3 周 | 供应链/持股/内部人/宏观事件关系建模 |
| 第 4 周 | AI 上下文、图谱因子、分析 API、缓存优化 |

---

*本方案待确认后方可执行实施。*
