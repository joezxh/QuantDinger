# AI 分析增强方案

> 版本：v1.1 | 优先级：P1 | 预估工期：3-5 周

---

## 1. 目标

- 将 Neo4j + Graphiti 知识图谱上下文注入现有 AI 分析流程
- 实现图谱驱动的多跳关联推理、事件影响链和叙事演化分析
- 与现有 `fast_analysis.py`、`market_data_collector.py`、策略引擎、风控模块协同工作
- 利用 Redis 缓存热点图谱上下文，避免重复图查询
- 保持降级安全：图谱不可用时，不影响主分析流程

---

## 2. 增强架构

```text
现有流程：
  市场数据采集 -> AI 提示词生成 -> LLM 分析 -> 结果输出

增强后：
  市场数据采集 ----------┐
  PostgreSQL 结构化数据 ---┤
  Redis 热缓存 -----------┤-> GraphContextBuilder -> Prompt Assembler -> LLM -> 结果输出
  Neo4j / Graphiti -------┤
  聪明钱/图谱因子 ---------┘
```

### 2.1 关键原则

1. **先保留现有 AI 分析链路，再叠加图谱上下文。**
2. **图谱上下文是增强项，不是硬依赖项。**
3. **优先命中 Redis 缓存，减少 Neo4j/Graphiti 查询压力。**
4. **AI 输出需尽量附带关系链和证据摘要，增强可解释性。**

---

## 3. 核心组件设计

### 3.1 GraphContextBuilder

职责：
- 从 Redis / Neo4j / Graphiti 中获取资产相关子图
- 生成统一结构化上下文
- 对不同市场返回定制信息

建议上下文结构：

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
    "subgraph_summary": "...",
}
```

### 3.2 GraphContextCache

职责：
- 优先读取 `graph:context:{market}:{symbol}`
- 若缓存未命中，执行图查询后回填缓存
- 支持 TTL 和手动失效

### 3.3 Prompt Assembler

职责：
- 将结构化行情数据、新闻摘要、图谱上下文合并
- 控制 Prompt 长度，避免图谱上下文过大
- 优先保留高置信度关系、近时效事件、关键传播链

### 3.4 Feature Bridge

职责：
- 从图谱中提取可量化特征
- 同步给策略引擎、回测引擎、风险引擎复用

---

## 4. 图谱上下文构建策略

### 4.1 查询优先级

1. 先查 Redis `graph:context:{market}:{symbol}`
2. 若无缓存，查 Neo4j 子图
3. 若需要时态事件演化或叙事漂移，再走 Graphiti 检索
4. 将结果摘要后写回 Redis

### 4.2 上下文内容分层

#### 通用层
- 相关资产
- 近期关键事件
- 新闻情绪
- 影响链
- 叙事标签

#### 股票层
- 机构持股变化
- 供应链关联
- 宏观传导路径
- 共同股东网络

#### 加密层
- 鲸鱼净流向
- KOL 共识
- 协议风险传播
- Narrative Drift

#### 预测市场层
- 聪明钱一致性
- 概率异动归因
- 与现实资产桥接信号
- 外部事件触发链

---

## 5. GraphContextBuilder 示例

```python
# app/graph/context_builder.py
from app.graph.queries import (
    find_related_assets,
    get_asset_news_sentiment,
    find_impact_chain,
)
from app.graph.connection import run_cypher
from app.cache.redis_client import get_redis
from app.utils.logger import get_logger
import json

logger = get_logger(__name__)


class GraphContextBuilder:
    def __init__(self):
        self.redis = get_redis()

    def build(self, market: str, symbol: str) -> dict:
        cache_key = f"graph:context:{market}:{symbol}"
        try:
            cached = self.redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

        ctx = self._build_fresh(market, symbol)

        try:
            self.redis.setex(cache_key, 300, json.dumps(ctx, ensure_ascii=False, default=str))
        except Exception:
            pass

        return ctx

    def _build_fresh(self, market: str, symbol: str) -> dict:
        ctx = {
            "related_assets": [],
            "recent_events": [],
            "impact_chain": [],
            "narrative_drift": {},
            "top_institutional_holders": [],
            "kol_consensus": {},
            "prediction_market_signals": [],
            "smart_money": {},
            "subgraph_summary": "",
        }

        try:
            ctx["related_assets"] = find_related_assets(symbol, market, depth=2)[:5]
        except Exception as e:
            logger.debug(f"related_assets failed: {e}")

        try:
            ctx["news_sentiment_distribution"] = get_asset_news_sentiment(symbol, days=7)
        except Exception as e:
            logger.debug(f"news_sentiment failed: {e}")

        if market in ("USStock", "HKStock", "CNStock"):
            try:
                ctx["top_institutional_holders"] = run_cypher("""
                    MATCH (co:Company {ticker: $symbol})
                    MATCH (inst:Institution)-[r:HOLDS_SHARES]->(co)
                    RETURN inst.name AS institution,
                           r.shares_pct AS pct
                    ORDER BY r.shares_pct DESC LIMIT 5
                """, {"symbol": symbol})
            except Exception as e:
                logger.debug(f"holders failed: {e}")

        if market == "Crypto":
            try:
                base = symbol.split("/")[0] if "/" in symbol else symbol
                result = run_cypher("""
                    MATCH (ca:CryptoAccount)-[:HOLDS]->(a:Asset {symbol: $sym, market: 'Crypto'})
                    WHERE ca.followers > 5000
                    RETURN count(ca) AS kol_count,
                           sum(ca.followers) AS total_reach,
                           avg(ca.balance_usd) AS avg_balance
                """, {"sym": base + "/USDT"})
                if result:
                    ctx["kol_consensus"] = result[0]
            except Exception as e:
                logger.debug(f"kol_consensus failed: {e}")

        try:
            ctx["prediction_market_signals"] = run_cypher("""
                MATCH (a:Asset {symbol: $symbol})<-[:PREDICTS]-(pm:PredictionMarket)
                WHERE pm.volume > 1000
                RETURN pm.question AS question,
                       pm.probability AS probability,
                       pm.volume AS volume
                ORDER BY pm.volume DESC LIMIT 3
            """, {"symbol": symbol})
        except Exception as e:
            logger.debug(f"prediction_market failed: {e}")

        return ctx
```

---

## 6. GraphRAG 与时态检索增强

### 6.1 使用场景

当仅靠静态 Cypher 查询无法满足需求时，调用 Graphiti 做时态检索：
- 最近 30 天叙事如何变化
- 旧事实与新事实的冲突演进
- 特定事件链在不同时间节点的传播路径

### 6.2 典型问题

- “过去三个月，NVDA 的主要叙事从 AI 算力扩张转向供应链约束了吗？”
- “某 Polymarket 市场的概率大跳变是由哪类外部事件触发的？”
- “某 DeFi 协议被攻击后，风险如何扩散到相关资产和地址？”

### 6.3 返回形式

Graphiti 返回的结果不直接全量拼 Prompt，应先摘要为：
- 关键实体
- 时间序列事件列表
- 关系变化摘要
- 最可信影响链

---

## 7. Prompt 组装策略

### 7.1 建议结构

```text
1. 市场结构化数据摘要
2. 技术指标摘要
3. 新闻与公告摘要
4. 图谱增强信息
   - 相关资产
   - 关键事件
   - 叙事变化
   - 聪明钱/机构/鲸鱼信号
5. 输出要求
```

### 7.2 控制策略

- 子图深度限制在 2-3 跳
- 事件数量限制在最近 5-10 条
- 每类图谱信息只保留 top-k
- 图谱字段统一转成自然语言摘要，避免原始 JSON 全量注入

### 7.3 摘要格式建议

```python
def format_graph_context_for_llm(ctx: dict) -> str:
    if not ctx:
        return ""

    parts = ["【知识图谱增强信息】"]

    if ctx.get("related_assets"):
        parts.append("关联资产：" + ", ".join(
            [x.get("symbol", "") for x in ctx["related_assets"][:5]]
        ))

    if ctx.get("top_institutional_holders"):
        holders = [x.get("institution", "") for x in ctx["top_institutional_holders"][:3]]
        parts.append("主要机构股东：" + ", ".join(holders))

    if ctx.get("kol_consensus"):
        kc = ctx["kol_consensus"]
        parts.append(
            f"KOL 共识：{kc.get('kol_count', 0)} 位 KOL 持有，总覆盖粉丝 {kc.get('total_reach', 0):,}"
        )

    if ctx.get("prediction_market_signals"):
        for pm in ctx["prediction_market_signals"][:2]:
            parts.append(
                f"预测市场：{pm.get('question', '')[:60]}（概率 {pm.get('probability', 50):.1f}%）"
            )

    return "\n".join(parts)
```

---

## 8. 集成到现有分析服务

```python
# app/services/fast_analysis.py
from app.graph.context_builder import GraphContextBuilder, format_graph_context_for_llm


class FastAnalysisService:
    def __init__(self):
        self._graph_builder = GraphContextBuilder()

    def analyze(self, market: str, symbol: str, **kwargs) -> dict:
        data = get_market_data_collector().collect_all(market, symbol, **kwargs)

        graph_ctx = {}
        graph_ctx_text = ""
        try:
            graph_ctx = self._graph_builder.build(market, symbol)
            graph_ctx_text = format_graph_context_for_llm(graph_ctx)
            data["graph_context"] = graph_ctx
        except Exception as e:
            logger.debug(f"graph context build failed: {e}")

        prompt = self._build_prompt(data, graph_ctx_text=graph_ctx_text)
        return call_llm(prompt, model=kwargs.get("model", "gpt-4o"))
```

---

## 9. 新增分析功能

### 9.1 事件影响链分析

- 从事件到资产/公司/协议的传播链
- 输出最短路径与 top-k 影响节点
- 用于 AI 分析、风控和异动归因

### 9.2 聪明钱信号聚合

- Polymarket 用户胜率与交易方向
- 加密鲸鱼地址净流向
- 股票共同机构持股变化

### 9.3 Narrative Drift 分析

- 分析过去一段时间叙事标签如何迁移
- 输出当前主叙事、前一阶段叙事、切换时间点

### 9.4 跨市场先行指标

- Polymarket 概率变化作为股票/加密先行信号
- 宏观事件对股票与加密的共同冲击
- 加密风险事件向相关股票或 ETF 的映射

---

## 10. 策略引擎与回测协同

### 10.1 图谱因子输出

建议将以下图谱特征落表：
- `shared_holder_strength`
- `supply_chain_risk_score`
- `narrative_drift_score`
- `whale_accumulation_score`
- `smart_money_consensus_score`
- `pm_leading_signal_score`

### 10.2 与回测系统协同

- 图谱因子按日频/小时频写入 PostgreSQL
- 回测只读取落表后的图谱因子
- 使用 Graphiti 的时间窗切片避免未来函数污染

### 10.3 与风控系统协同

- 当触发交易建议时，附带证据子图摘要
- 对高风险冲击链进行预警打分
- 对关联资产和主体做扩散监测

---

## 11. API 接口建议

| 接口 | 说明 |
|------|------|
| `GET /api/graph-analysis/enhanced-context` | 获取图谱增强上下文 |
| `GET /api/graph-analysis/contagion-path` | 查询事件/资产传播路径 |
| `GET /api/graph-analysis/narrative-drift` | 查询叙事演化 |
| `GET /api/graph-analysis/smart-money/{symbol}` | 获取聪明钱信号 |
| `GET /api/graph-analysis/prediction-leading/{symbol}` | 获取预测市场先行信号 |

---

## 12. 性能优化

| 措施 | 说明 |
|------|------|
| 图查询缓存 | Redis 缓存结果，TTL 5-15 分钟 |
| 查询分级 | 静态查询走 Neo4j，时态查询走 Graphiti |
| 异步查询 | 图谱查询与主数据采集并行执行 |
| Prompt 摘要化 | 只注入高价值上下文，限制 token |
| 降级机制 | Neo4j/Graphiti 异常时自动回退 |
| 查询限制 | 限制跳数、节点数、事件数 |

---

## 13. 实施计划

| 周次 | 任务 |
|------|------|
| 第 1 周 | GraphContextBuilder、Redis 缓存、基础图查询封装 |
| 第 2 周 | 集成到 FastAnalysis，完成降级与超时机制 |
| 第 3 周 | 事件影响链、聪明钱、预测市场先行信号服务 |
| 第 4 周 | Narrative Drift、GraphRAG 查询、Prompt 摘要器 |
| 第 5 周 | 图谱因子落表、回测接入、前端展示优化 |

---

*本方案待确认后方可执行实施。*
