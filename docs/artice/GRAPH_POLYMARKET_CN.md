# 预测市场 Graphiti 时态图谱方案

> 版本：v1.1 | 优先级：P1 | 预估工期：2-3 周

---

## 1. 目标

- 采集 Polymarket 用户、交易、持仓、市场元数据、赔率变化与外部事件数据
- 在原有用户社交关系图谱基础上，升级为“市场-结果-用户-外部事件-现实资产”的 Graphiti 时态图谱
- 支持聪明钱识别、赔率异动归因、跨市场先行指标和 AI 增强分析

---

## 2. 方案定位

本方案保留现有 Polymarket 数据采集与用户图谱建模，并增强以下能力：
- 概率变化的时态记录
- 市场与外部事件的因果关系建模
- 市场与股票/加密资产的桥接关系
- GraphRAG 查询和热点市场缓存

组件分工：
- **PostgreSQL**：用户交易、持仓、市场快照、外部事件原始记录、图谱因子
- **Neo4j**：用户、市场、结果、事件、桥接资产关系
- **Graphiti**：赔率异动、外部新闻、现实事件进展的时态关系管理
- **Redis**：热点市场子图、聪明钱上下文、先行信号缓存

---

## 3. 数据来源

| 数据类型 | 来源 |
|---------|------|
| 用户活动 | Polymarket Data API |
| 用户持仓 | Polymarket Data API |
| 市场元数据 | Gamma API |
| 历史价格 / 概率变化 | Gamma API / 历史快照 |
| 外部新闻与现实事件 | News API / 搜索 / 自建采集 |
| 结算规则 / Resolution Source | 市场详情 / Oracle 来源 |
| Graph 抽取 | Graphiti + LLM |

---

## 4. Episode 设计

### 4.1 应进入 Graphiti 的事件

- 市场赔率大幅波动
- 头部账户集中建仓或平仓
- 与市场主题强相关的现实世界事件进展
- 结算规则变化或 Oracle 风险变化
- 多个预测市场出现同步共振

### 4.2 示例

```python
CollectedItem(
    source="polymarket_market_api",
    data_type="pm_odds_jump",
    market="Polymarket",
    symbol="market:12345",
    raw_data=market,
    normalized_data={
        "market_id": "12345",
        "question": market.get("question"),
        "old_probability": 0.42,
        "new_probability": 0.61,
        "change": 0.19,
        "event_time": market.get("updated_at"),
    },
    importance_score=0.88,
    should_build_episode=True,
    entity_keys={"market_id": "12345"},
)
```

---

## 5. Graphiti 本体设计

### 5.1 核心实体

- `PredictionMarket`：预测市场
- `Outcome`：YES/NO 或其他选项
- `PolymarketUser`：交易用户
- `ExternalEvent`：外部现实事件
- `ResolutionSource`：结算依据
- `Asset`：相关股票、币种、指数
- `NarrativeTag`：选举、监管、AI、宏观等

### 5.2 关键关系

| 关系 | 含义 | 时态性 |
|------|------|------|
| `TRADED_IN` | 用户参与市场 | 强 |
| `CO_TRADED` | 用户同向交易关系 | 中 |
| `HAS_ODDS` | 市场对结果的概率关系 | 强 |
| `TRIGGERED_BY` | 外部事件触发市场变化 | 强 |
| `PREDICTS` | 市场预测某资产/事件结果 | 中 |
| `LINKED_TO_ASSET` | 市场与现实资产桥接 | 中 |
| `HAS_NARRATIVE` | 市场叙事标签 | 强 |

### 5.3 时间属性

建议统一携带：
- `t_valid`
- `t_invalid`
- `source_ref`
- `confidence`
- `updated_at`

---

## 6. Neo4j 图谱模型

### 6.1 节点

```cypher
MERGE (u:PolymarketUser {uid: $user_uid})
SET u.address = $address,
    u.trade_count = $trade_count,
    u.win_rate = $win_rate,
    u.total_volume = $total_volume,
    u.influence_score = $influence_score,
    u.updated_at = datetime()

MERGE (pm:PredictionMarket {uid: $market_uid})
SET pm.market_id = $market_id,
    pm.question = $question,
    pm.category = $category,
    pm.updated_at = datetime()

MERGE (o:Outcome {uid: $outcome_uid})
SET o.label = $label,
    o.updated_at = datetime()
```

### 6.2 时态关系

```cypher
MATCH (u:PolymarketUser {uid: $user_uid})
MATCH (pm:PredictionMarket {uid: $market_uid})
MERGE (u)-[r:TRADED_IN {source_ref: $source_ref, t_valid: $t_valid}]->(pm)
SET r.direction = $direction,
    r.amount = $amount,
    r.price = $price,
    r.t_invalid = $t_invalid,
    r.updated_at = datetime()

MATCH (pm:PredictionMarket {uid: $market_uid})
MATCH (o:Outcome {uid: $outcome_uid})
MERGE (pm)-[r:HAS_ODDS {source_ref: $source_ref, t_valid: $t_valid}]->(o)
SET r.probability = $probability,
    r.volume = $volume,
    r.t_invalid = $t_invalid,
    r.updated_at = datetime()
```

---

## 7. Graphiti 处理流程

### 7.1 核心流程

1. 市场、交易、持仓、新闻先进入 PostgreSQL。
2. 赔率异动、重大新闻、外部事件经 Episode Builder 转为 Episode。
3. Graphiti 抽取外部事件、市场叙事和桥接资产。
4. Graphiti 管理概率变化和事件触发关系的时态演化。
5. Redis 缓存热点市场增强上下文。

### 7.2 典型场景

#### 场景 1：赔率异动归因
- 市场 5 分钟内概率变化超 15%
- Graphiti 追溯最新外部事件
- 建立 `ExternalEvent -> PredictionMarket` 路径

#### 场景 2：先行指标映射
- 某科技公司诉讼胜诉概率上升
- 市场与公司股票建立 `LINKED_TO_ASSET`
- AI 与策略系统可将其作为股票先行信号

#### 场景 3：聪明钱共振
- 多个高胜率用户短时间集中建仓
- 建立 `CO_TRADED`、`TRADED_IN` 聚合特征
- 输出一致性信号给分析服务

---

## 8. 关键分析查询

```cypher
// 聪明钱排行
MATCH (u:PolymarketUser)
OPTIONAL MATCH (follower:PolymarketUser)-[:CO_TRADED]->(u)
WITH u, count(DISTINCT follower) AS follower_count
RETURN u.address, u.win_rate, u.total_volume,
       follower_count,
       u.win_rate * 0.4 + (log(u.total_volume + 1) / 20.0) * 0.3 + (follower_count / 100.0) * 0.3 AS influence
ORDER BY influence DESC LIMIT 100

// 市场异动归因
MATCH (e:ExternalEvent)-[:TRIGGERED_BY]->(pm:PredictionMarket {market_id: $market_id})
RETURN e.event_type, e.title, e.event_time
ORDER BY e.event_time DESC LIMIT 10

// 市场桥接资产
MATCH (pm:PredictionMarket {market_id: $market_id})-[r:LINKED_TO_ASSET]->(a:Asset)
RETURN a.symbol, a.market, r.linkage_type

// 概率演化
MATCH (pm:PredictionMarket {market_id: $market_id})-[r:HAS_ODDS]->(o:Outcome)
RETURN o.label, r.probability, r.t_valid, r.t_invalid
ORDER BY r.t_valid DESC
```

---

## 9. PostgreSQL 表设计

```sql
CREATE TABLE qd_polymarket_users (
    id SERIAL PRIMARY KEY,
    address VARCHAR(100) UNIQUE NOT NULL,
    trade_count INTEGER DEFAULT 0,
    win_rate DECIMAL(5,4) DEFAULT 0,
    total_volume DECIMAL(20,2) DEFAULT 0,
    influence_score DECIMAL(10,4) DEFAULT 0,
    collected_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE qd_polymarket_user_trades (
    id SERIAL PRIMARY KEY,
    user_address VARCHAR(100) NOT NULL,
    market_id VARCHAR(255) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    size DECIMAL(20,6),
    price DECIMAL(10,6),
    profit DECIMAL(20,6),
    traded_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE qd_polymarket_market_features (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    market_id VARCHAR(255) NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    feature_value DECIMAL(24,8) NOT NULL,
    source VARCHAR(50) DEFAULT 'graph',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, market_id, feature_name)
);
```

---

## 10. AI、策略与回测集成

### 10.1 AI 分析增强
- 聪明钱方向一致性
- 赔率异动归因
- 外部事件触发链
- 关联股票/加密资产的桥接信号

### 10.2 图谱因子建议
- `pm_smart_money_consensus_score`
- `pm_odds_jump_score`
- `pm_event_trigger_score`
- `pm_leading_signal_score`
- `pm_resolution_risk_score`

### 10.3 回测与风控
- 图谱因子落 PostgreSQL 供回测使用
- 预测市场作为先行指标接入股票/加密策略
- 对高争议市场或高结算风险市场做风控提示

---

## 11. Redis 缓存建议

```text
graph:context:polymarket:{market_id}
graph:subgraph:polymarket:{market_id}
graph:smart-money:{market_id}
graph:prediction-leading:{symbol}
```

---

## 12. API 接口建议

| 接口 | 说明 |
|------|------|
| `GET /api/graph/polymarket/smart-money` | 聪明钱排行 |
| `GET /api/graph/polymarket/user/{addr}` | 用户交易图谱 |
| `GET /api/graph/polymarket/co-traders/{addr}` | 同向交易者 |
| `GET /api/graph/polymarket/market-sentiment/{id}` | 头部用户方向分布 |
| `GET /api/graph/polymarket/odds-attribution/{id}` | 赔率异动归因 |
| `GET /api/graph/polymarket/linked-assets/{id}` | 关联现实资产 |

---

## 13. 实施计划

| 周次 | 任务 |
|------|------|
| 第 1 周 | 用户/市场/交易结构化表与基础图模型 |
| 第 2 周 | Episode Builder、Graphiti 时态关系、概率演化建模 |
| 第 3 周 | 聪明钱、异动归因、桥接资产、AI/策略增强 |

---

*本方案待确认后方可执行实施。*
