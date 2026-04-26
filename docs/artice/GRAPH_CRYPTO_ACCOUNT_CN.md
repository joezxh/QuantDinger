# 加密货币 Graphiti 时态图谱方案

> 版本：v1.1 | 优先级：P1 | 预估工期：3-4 周

---

## 1. 目标

- 采集加密货币排行榜、链上地址、KOL、协议、叙事与链上事件数据
- 在原有账号关系图谱基础上，升级为“资产-协议-账户-事件-叙事”的 Graphiti 时态图谱
- 支持 KOL 影响力评估、鲸鱼资金追踪、风险传播、Narrative Drift 和策略因子构建

---

## 2. 方案定位

本方案基于现有加密账号关系图谱扩展，不替代当前采集器和结构化数据库。

分工如下：
- **PostgreSQL**：链上地址、转账、价格、排行榜、协议状态、图谱因子
- **Neo4j**：账户、资产、协议、转账关系、叙事关系
- **Graphiti**：处理链上事件、新闻、社交帖子、协议状态变更和叙事演化
- **Redis**：缓存热点币种、鲸鱼子图、风险传播子图、AI 上下文

---

## 3. 数据来源

| 数据类型 | 来源 |
|---------|------|
| 加密 KOL 列表 | Lunarcrush / 手工维护 |
| Twitter/X 关注关系 | Twitter API v2（可选） |
| 链上地址 | Etherscan / BSCScan / Solscan API |
| 链上转账记录 | 各链 RPC / Etherscan API |
| 持仓快照 | Nansen / DeBank API（可选） |
| 排行榜 / 价格 | CMC / CoinGecko / CCXT |
| 协议数据 | Dune / DefiLlama / 自建接口 |
| 社交叙事 | X / Telegram / 新闻源 |
| 事件抽取 | Graphiti + LLM |

---

## 4. Episode 设计

### 4.1 应进入 Graphiti 的事件

- 鲸鱼大额转账
- 资金集中流入或流出某币种/协议
- 协议升级、漏洞、被攻击、停机
- 代币解锁、上所、下架、治理投票
- KOL 高影响帖子与叙事转向
- 稳定币脱锚、跨链桥异常

### 4.2 示例

```python
CollectedItem(
    source="etherscan",
    data_type="whale_transfer",
    market="Crypto",
    symbol="ETH/USDT",
    raw_data=tx,
    normalized_data={
        "chain": "ethereum",
        "from_addr": tx["from"],
        "to_addr": tx["to"],
        "value_usd": 2500000,
        "token": "ETH",
        "event_time": tx["timestamp"],
    },
    importance_score=0.91,
    should_build_episode=True,
    entity_keys={"asset": "ETH/USDT", "from": tx["from"], "to": tx["to"]},
)
```

---

## 5. Graphiti 本体设计

### 5.1 核心实体

- `Asset`：BTC、ETH、SOL、稳定币、Meme 币
- `Protocol`：DEX、借贷、L2、跨链桥、质押协议
- `CryptoAccount`：鲸鱼地址、KOL、基金钱包、交易所热钱包
- `Transfer`：重要转账事件
- `MarketEvent`：被攻击、解锁、上线、下架、治理结果
- `Chain`：Ethereum、Solana、Base、Arbitrum
- `NarrativeTag`：AI Agent、Meme、Restaking、RWA 等

### 5.2 关键关系

| 关系 | 含义 | 时态性 |
|------|------|------|
| `HOLDS` | 地址持有资产 | 强 |
| `FOLLOWS` | 社交关注关系 | 中 |
| `TRANSFERRED_TO` | 地址资金流向 | 强 |
| `DEPLOYED_ON` | 协议部署在某链 | 强 |
| `PAIRED_WITH` | 流动性配对 | 中 |
| `IMPACTED_BY` | 事件影响资产/协议 | 中 |
| `HAS_NARRATIVE` | 叙事标签 | 强 |
| `PROMOTED_BY` | 项目被 KOL 推动 | 中 |

### 5.3 时间字段

所有关键关系边建议携带：
- `t_valid`
- `t_invalid`
- `source_ref`
- `confidence`
- `updated_at`

---

## 6. Neo4j 图谱模型

### 6.1 节点

```cypher
MERGE (ca:CryptoAccount {uid: $uid})
SET ca.address = $address,
    ca.chain = $chain,
    ca.handle = $handle,
    ca.platform = $platform,
    ca.followers = $followers,
    ca.balance_usd = $balance_usd,
    ca.updated_at = datetime()

MERGE (a:Asset {uid: $asset_uid})
SET a.symbol = $symbol,
    a.market = 'Crypto',
    a.name = $name,
    a.updated_at = datetime()

MERGE (p:Protocol {uid: $protocol_uid})
SET p.name = $name,
    p.category = $category,
    p.updated_at = datetime()
```

### 6.2 时态关系

```cypher
MATCH (ca:CryptoAccount {uid: $account_uid})
MATCH (a:Asset {uid: $asset_uid})
MERGE (ca)-[r:HOLDS {source_ref: $source_ref, t_valid: $t_valid}]->(a)
SET r.amount = $amount,
    r.value_usd = $value_usd,
    r.confidence = $confidence,
    r.t_invalid = $t_invalid,
    r.updated_at = datetime()

MATCH (src:CryptoAccount {uid: $src_uid})
MATCH (dst:CryptoAccount {uid: $dst_uid})
MERGE (src)-[r:TRANSFERRED_TO {source_ref: $source_ref, t_valid: $t_valid}]->(dst)
SET r.asset_symbol = $asset_symbol,
    r.value_usd = $value_usd,
    r.tx_hash = $tx_hash,
    r.t_invalid = $t_invalid,
    r.updated_at = datetime()
```

---

## 7. Graphiti 处理流程

### 7.1 主要链路

1. 链上地址、社交、协议事件先写入 PostgreSQL。
2. `EpisodeBuilder` 对重要事件生成 Episode。
3. Graphiti 抽取地址、协议、资产、叙事、事件关系。
4. 对持仓、叙事、协议状态变化执行时态更新。
5. Neo4j 保存关系，Redis 缓存热点子图。

### 7.2 典型场景

#### 场景 1：鲸鱼大额转出
- Graphiti 识别这是流动性风险或抛压信号
- 更新 `TRANSFERRED_TO`、`HOLDS` 和 `IMPACTED_BY`
- AI 与策略层可读取鲸鱼减仓分数

#### 场景 2：协议被攻击
- 建立 `MarketEvent -> Protocol`
- 进一步链接到受影响资产、相关地址、稳定币、桥接协议
- 风险扩散路径可用于预警和策略止损

#### 场景 3：叙事切换
- 某资产从“高性能公链”转向“Meme 生态”
- 通过 `HAS_NARRATIVE` 的时间变化分析 Narrative Drift

---

## 8. 关键分析查询

```cypher
// KOL 影响力排行
MATCH (ca:CryptoAccount)
OPTIONAL MATCH (follower:CryptoAccount)-[:FOLLOWS]->(ca)
RETURN ca.handle AS account,
       count(DISTINCT follower) AS followers,
       ca.balance_usd AS balance,
       ca.followers * 0.5 + log(ca.balance_usd + 1) * 0.5 AS influence
ORDER BY influence DESC LIMIT 50

// 鲸鱼资金流向
MATCH (src:CryptoAccount)-[r:TRANSFERRED_TO]->(dst:CryptoAccount)
WHERE r.value_usd > 10000 AND r.asset_symbol = $symbol
RETURN src.address, dst.address, r.value_usd, r.t_valid
ORDER BY r.value_usd DESC

// KOL 共识持仓
MATCH (ca:CryptoAccount)-[:HOLDS]->(a:Asset {symbol: $symbol})
WHERE ca.followers > 10000
RETURN count(DISTINCT ca) AS kol_count,
       sum(ca.followers) AS total_reach

// 叙事演化
MATCH (a:Asset {symbol: $symbol})-[r:HAS_NARRATIVE]->(n:NarrativeTag)
RETURN n.name, r.score, r.t_valid, r.t_invalid
ORDER BY r.t_valid DESC
```

---

## 9. PostgreSQL 表设计

```sql
CREATE TABLE qd_crypto_accounts (
    id SERIAL PRIMARY KEY,
    address VARCHAR(100),
    chain VARCHAR(20) DEFAULT 'ethereum',
    handle VARCHAR(100),
    platform VARCHAR(30),
    followers INTEGER DEFAULT 0,
    balance_usd DECIMAL(20,2) DEFAULT 0,
    is_kol BOOLEAN DEFAULT FALSE,
    is_whale BOOLEAN DEFAULT FALSE,
    source VARCHAR(50),
    collected_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(chain, address)
);

CREATE TABLE qd_crypto_transfers (
    id SERIAL PRIMARY KEY,
    tx_hash VARCHAR(100) UNIQUE NOT NULL,
    chain VARCHAR(20) DEFAULT 'ethereum',
    from_addr VARCHAR(100),
    to_addr VARCHAR(100),
    asset_symbol VARCHAR(50),
    value_usd DECIMAL(20,2),
    transferred_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE qd_crypto_narrative_features (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    narrative_name VARCHAR(100) NOT NULL,
    narrative_score DECIMAL(10,4) NOT NULL,
    source VARCHAR(50) DEFAULT 'graph',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, symbol, narrative_name)
);
```

---

## 10. AI、策略与回测集成

### 10.1 AI 分析增强
- KOL 共识与影响力摘要
- 鲸鱼净流入/流出摘要
- 协议风险扩散链
- 叙事变化摘要

### 10.2 图谱因子建议
- `whale_accumulation_score`
- `kol_consensus_score`
- `protocol_risk_spread_score`
- `narrative_drift_score`
- `stablecoin_stress_score`

### 10.3 回测协同
- 图谱因子落 PostgreSQL
- 回测系统读取历史因子快照
- 通过时态关系回放确保无未来函数污染

---

## 11. Redis 缓存建议

```text
graph:context:crypto:{symbol}
graph:subgraph:crypto:{symbol}
graph:account:{address}
graph:risk-chain:crypto:{symbol}
```

---

## 12. API 接口建议

| 接口 | 说明 |
|------|------|
| `GET /api/graph/crypto/account/{address}` | 地址图谱详情 |
| `GET /api/graph/crypto/whale-flow/{symbol}` | 鲸鱼流向分析 |
| `GET /api/graph/crypto/kol-consensus/{symbol}` | KOL 共识分析 |
| `GET /api/graph/crypto/narrative-drift/{symbol}` | 叙事演化 |
| `GET /api/graph/crypto/risk-spread/{symbol}` | 风险扩散路径 |

---

## 13. 实施计划

| 周次 | 任务 |
|------|------|
| 第 1 周 | 地址/资产/协议结构化表与基础图模型 |
| 第 2 周 | Episode Builder、Graphiti 时态关系写入 |
| 第 3 周 | 鲸鱼/KOL/协议/叙事建模与分析接口 |
| 第 4 周 | 图谱因子、AI 增强、缓存与风险传播优化 |

---

*本方案待确认后方可执行实施。*
