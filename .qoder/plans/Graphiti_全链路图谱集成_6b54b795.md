# Graphiti 全链路知识图谱集成方案

## 方案概述

本方案将 Graphiti 时态知识图谱框架与 QuantDinger 现有系统全链路集成,实现:
- 股票/加密/预测市场三大领域的图谱化
- 图谱上下文增强现有 AI 分析流程
- 保留并优化现有 PostgreSQL + Redis 架构
- 通过 Neo4j 提供图查询与多跳推理能力

---

## 第一阶段:基础设施搭建(1-2周)

### 1.1 Docker Compose 集成 Neo4j

**文件**: `docker-compose.yml`

在现有 postgres、redis 服务后新增 neo4j 服务:

```yaml
services:
  # ... 现有 postgres, redis, backend, frontend ...
  
  neo4j:
    image: neo4j:5-community
    container_name: quantdinger-neo4j
    ports:
      - "7474:7474"   # HTTP Browser
      - "7687:7687"   # Bolt Protocol
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD:-quantdinger}
      NEO4J_PLUGINS: '["apoc"]'
      NEO4J_dbms_security_procedures_unrestricted: apoc.*
      NEO4J_dbms_memory_heap_max__size: 2G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    networks:
      - quantdinger-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:7474"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  # ... 现有 volumes ...
  neo4j_data:
  neo4j_logs:
```

### 1.2 环境变量配置

**文件**: `backend_api_python/.env` 和 `backend_api_python/env.example`

新增环境变量:
```env
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=quantdinger
GRAPHITI_ENABLED=true
```

### 1.3 依赖包安装

**文件**: `backend_api_python/requirements.txt`

新增依赖:
```
neo4j>=5.0
graphiti-core>=0.2.0
pydantic>=2.0
```

### 1.4 Graphiti 连接管理模块

**新建文件**: `backend_api_python/app/graph/__init__.py`

**新建文件**: `backend_api_python/app/graph/connection.py`

实现内容:
- `get_graphiti_instance()`: 初始化 Graphiti 实例(绑定 Neo4j)
- `run_cypher(query, params)`: 执行 Cypher 查询的便捷函数
- `close_graphiti()`: 优雅关闭连接
- 全局单例模式,避免重复创建连接

关键代码结构:
```python
from graphiti_core import Graphiti
from neo4j import GraphDatabase
import os

_graphiti_instance = None
_neo4j_driver = None

def get_graphiti():
    global _graphiti_instance
    if _graphiti_instance is None:
        uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "quantdinger")
        _graphiti_instance = Graphiti(uri, user, password)
    return _graphiti_instance

def run_cypher(query: str, params: dict = None):
    """直接执行 Cypher 查询(适用于非 Graphiti 管理的查询)"""
    # 实现...
```

### 1.5 Neo4j 索引与约束初始化

**新建文件**: `backend_api_python/migrations/neo4j_init.cypher`

创建内容:
```cypher
-- 唯一性约束
CREATE CONSTRAINT asset_uid IF NOT EXISTS FOR (a:Asset) REQUIRE a.uid IS UNIQUE;
CREATE CONSTRAINT company_ticker IF NOT EXISTS FOR (c:Company) REQUIRE c.ticker IS UNIQUE;
CREATE CONSTRAINT crypto_asset_symbol IF NOT EXISTS FOR (a:Asset) REQUIRE a.symbol IS UNIQUE;
CREATE CONSTRAINT market_id IF NOT EXISTS FOR (m:Market) REQUIRE m.market_id IS UNIQUE;

-- 查询加速索引
CREATE INDEX asset_symbol IF NOT EXISTS FOR (a:Asset) ON (a.symbol);
CREATE INDEX asset_market IF NOT EXISTS FOR (a:Asset) ON (a.market);
CREATE INDEX news_published_at IF NOT EXISTS FOR (n:NewsArticle) ON (n.published_at);
CREATE INDEX event_date IF NOT EXISTS FOR (e:Event) ON (e.date);
```

**修改文件**: `backend_api_python/app/__init__.py`

在 Flask 应用初始化时调用索引创建脚本。

---

## 第二阶段:本体定义与数据导入(2-3周)

### 2.1 股票市场本体定义

**新建文件**: `backend_api_python/app/graph/ontologies/stock.py`

使用 Pydantic 定义股票市场的实体和关系:

```python
from pydantic import Field
from graphiti_core.nodes import Entity

class Company(Entity):
    ticker: str = Field(..., description="证券代码")
    name: str = Field(None, description="公司名称")
    sector: str = Field(None, description="所属行业")
    market_cap: float = Field(None, description="市值")
    exchange: str = Field(None, description="交易所")

class Executive(Entity):
    name: str = Field(..., description="姓名")
    role: str = Field(None, description="职位")

class Institution(Entity):
    name: str = Field(..., description="机构名称")
    type: str = Field(None, description="机构类型")

# 关系通过 Graphiti 的 add_episode 自动提取,无需显式定义
```

### 2.2 加密货币市场本体定义

**新建文件**: `backend_api_python/app/graph/ontologies/crypto.py`

```python
class CryptoAsset(Entity):
    symbol: str = Field(..., description="代币符号,如 BTC/USDT")
    consensus: str = Field(None, description="共识机制")
    market: str = Field(default="Crypto")

class Protocol(Entity):
    name: str = Field(..., description="协议名称")
    category: str = Field(None, description="类别(DEX/Lending等)")
    chain: str = Field(None, description="所属链")

class CryptoAccount(Entity):
    address: str = Field(None, description="钱包地址")
    handle: str = Field(None, description="社交媒体账号")
    followers: int = Field(None, description="粉丝数")
```

### 2.3 Polymarket 预测市场本体定义

**新建文件**: `backend_api_python/app/graph/ontologies/polymarket.py`

```python
class PredictionMarket(Entity):
    market_id: str = Field(..., description="市场唯一ID")
    question: str = Field(..., description="预测问题")
    resolution_source: str = Field(None, description="结算依据")
    category: str = Field(None, description="分类")

class MarketOutcome(Entity):
    label: str = Field(..., description="选项(YES/NO)")
    probability: float = Field(None, description="当前概率")
```

### 2.4 数据导入 Pipeline

**新建目录**: `backend_api_python/app/graph/importers/`

#### 2.4.1 股票数据导入器

**新建文件**: `backend_api_python/app/graph/importers/stock_importer.py`

实现内容:
- `StockImporter.import_companies()`: 从 PostgreSQL 的上市公司表导入 Company 节点
- `StockImporter.import_news()`: 将现有新闻数据导入为 NewsArticle 节点,并建立 MENTIONED_IN 关系
- `StockImporter.import_institutional_holders()`: 导入机构持股关系

关键逻辑:
```python
from app.graph.connection import get_graphiti
from app.database.session import get_session
from app.models.stock import StockCompany, StockNews

class StockImporter:
    async def import_companies(self):
        graphiti = get_graphiti()
        with get_session() as s:
            companies = s.query(StockCompany).all()
        
        for company in companies:
            await graphiti.add_episode(
                name=f"Company:{company.ticker}",
                content=f"{company.name} ({company.ticker}) is a {company.sector} company listed on {company.exchange}",
                source_description="PostgreSQL Stock Data",
                reference_time=datetime.now()
            )
```

#### 2.4.2 加密货币数据导入器

**新建文件**: `backend_api_python/app/graph/importers/crypto_importer.py`

实现内容:
- `CryptoImporter.import_assets()`: 从现有资产表导入 CryptoAsset 节点
- `CryptoImporter.import_social_signals()`: 从市场情绪数据导入 KOL/社交关系
- `CryptoImporter.import_protocol_data()`: 导入 DeFi 协议信息

#### 2.4.3 Polymarket 数据导入器

**新建文件**: `backend_api_python/app/graph/importers/polymarket_importer.py`

实现内容:
- `PolymarketImporter.import_markets()`: 从 Polymarket API 导入预测市场
- `PolymarketImporter.import_price_history()`: 导入历史概率数据(带时间戳)
- `PolymarketImporter.import_external_events()`: 导入关联的外部新闻事件

### 2.5 数据导入调度器

**新建文件**: `backend_api_python/app/graph/import_scheduler.py`

实现内容:
- 定时任务:每小时增量导入新闻/事件
- 每日全量同步:公司基本信息、资产元数据
- 与现有 `market_data_collector.py` 解耦,独立运行

---

## 第三阶段:图谱查询与分析服务(2-3周)

### 3.1 图谱上下文构建器

**新建文件**: `backend_api_python/app/graph/context_builder.py`

实现 `GraphContextBuilder` 类(参考 AI_ANALYSIS_ENHANCEMENT_CN.md):

```python
class GraphContextBuilder:
    """为 AI 分析构建知识图谱上下文"""
    
    def build(self, market: str, symbol: str) -> dict:
        ctx = {}
        
        # 1. 关联资产查询
        ctx["related_assets"] = self._find_related_assets(symbol, market)
        
        # 2. 新闻情感分布
        ctx["news_sentiment"] = self._get_news_sentiment(symbol, days=7)
        
        # 3. 根据市场类型查询特定信息
        if market in ("USStock", "HKStock"):
            ctx["institutional_holders"] = self._get_stock_holders(symbol)
        elif market == "Crypto":
            ctx["kol_consensus"] = self._get_kol_consensus(symbol)
            ctx["whale_activity"] = self._get_whale_activity(symbol)
        elif market == "Polymarket":
            ctx["correlated_markets"] = self._get_correlated_markets(symbol)
            ctx["event_triggers"] = self._get_event_triggers(symbol)
        
        return ctx
    
    def _find_related_assets(self, symbol: str, market: str, depth: int = 2):
        # Cypher 查询实现...
```

### 3.2 事件影响链分析器

**新建文件**: `backend_api_python/app/graph/event_impact_analyzer.py`

实现内容:
- `EventImpactAnalyzer.get_contagion_path(from_symbol, to_symbol)`: 查找资产间传染路径
- `EventImpactAnalyzer.trace_event_impact(event_uid)`: 追踪事件影响链
- `EventImpactAnalyzer.find_cascade_risk(symbol)`: 级联风险评估(特别适用于加密市场)

### 3.3 聪明钱信号聚合器

**新建文件**: `backend_api_python/app/graph/smart_money_signal.py`

实现内容:
- `SmartMoneySignal.get_polymarket_smart_money(symbol)`: 预测市场聪明钱方向
- `SmartMoneySignal.get_whale_accumulation(symbol)`: 鲸鱼地址积累检测
- `SmartMoneySignal.get_institutional_flow(symbol)`: 机构资金流向(股票市场)

### 3.4 图谱查询函数封装

**新建文件**: `backend_api_python/app/graph/queries.py`

封装常用图查询:
```python
def find_related_assets(symbol: str, market: str, depth: int = 2):
    """查找关联资产"""
    return run_cypher("""
        MATCH (a:Asset {symbol: $symbol, market: $market})
        MATCH (a)-[r*1..$depth]-(related:Asset)
        RETURN related.symbol, related.market, type(r[0]) AS relation
        ORDER BY length(r)
    """, {"symbol": symbol, "market": market, "depth": depth})

def get_asset_news_sentiment(symbol: str, days: int = 7):
    """获取新闻情感分布"""
    # 实现...
```

---

## 第四阶段:与现有系统集成(2周)

### 4.1 集成到 FastAnalysis 服务

**修改文件**: `backend_api_python/app/services/fast_analysis.py`

在 `FastAnalysisService.analyze()` 方法中注入图谱上下文:

```python
from app.graph.context_builder import GraphContextBuilder, format_graph_context_for_llm

class FastAnalysisService:
    def __init__(self):
        self.kline_service = KlineService()
        self.llm_service = LLMService()
        self._graph_builder = None  # 新增
    
    def _get_graph_builder(self):
        """懒加载图谱上下文构建器"""
        if self._graph_builder is None:
            try:
                if os.getenv("GRAPHITI_ENABLED", "false").lower() == "true":
                    self._graph_builder = GraphContextBuilder()
            except Exception as e:
                logger.warning(f"Graphiti init failed: {e}")
        return self._graph_builder
    
    def analyze(self, market: str, symbol: str, **kwargs):
        # 1. 现有数据采集
        data = get_market_data_collector().collect_all(market, symbol, **kwargs)
        
        # 2. 新增:图谱上下文增强
        graph_ctx_text = ""
        try:
            builder = self._get_graph_builder()
            if builder:
                graph_ctx = builder.build(market, symbol)
                graph_ctx_text = format_graph_context_for_llm(graph_ctx)
                data["graph_context"] = graph_ctx
        except Exception as e:
            logger.debug(f"Graph context build failed (non-critical): {e}")
        
        # 3. 生成增强提示词
        prompt = self._build_prompt(data, graph_ctx_text=graph_ctx_text)
        
        # 4. 调用 LLM
        result = self.llm_service.call_llm(prompt, **kwargs)
        return result
    
    def _build_prompt(self, data: dict, graph_ctx_text: str = "") -> str:
        base_prompt = self._build_base_prompt(data)
        if graph_ctx_text:
            base_prompt += f"\n\n{graph_ctx_text}"
        return base_prompt
```

### 4.2 集成到市场数据采集器

**修改文件**: `backend_api_python/app/services/market_data_collector.py`

在 `MarketDataCollector.collect_all()` 方法中增加图谱数据选项:

```python
def collect_all(
    self,
    market: str,
    symbol: str,
    timeframe: str = "1D",
    include_macro: bool = True,
    include_news: bool = True,
    include_polymarket: bool = True,
    include_graph_context: bool = False,  # 新增参数
    timeout: int = 30
) -> Dict[str, Any]:
    # 现有逻辑...
    
    # 新增:图谱上下文采集
    if include_graph_context:
        try:
            from app.graph.context_builder import GraphContextBuilder
            builder = GraphContextBuilder()
            data["graph_context"] = builder.build(market, symbol)
        except Exception as e:
            logger.debug(f"Graph context collection failed: {e}")
            data["graph_context"] = {}
    
    return data
```

### 4.3 Redis 缓存图查询结果

**修改文件**: `backend_api_python/app/config/database.py`

新增图谱缓存配置:
```python
class MetaCacheConfig(type):
    @property
    def GRAPH_CONTEXT_TTL(cls):
        return 900  # 图谱上下文缓存15分钟
    
    @property
    def RELATED_ASSETS_TTL(cls):
        return 1800  # 关联资产缓存30分钟
```

**修改文件**: `backend_api_python/app/graph/context_builder.py`

在 `GraphContextBuilder.build()` 中加入 Redis 缓存:
```python
from app.utils.cache import get_cache

class GraphContextBuilder:
    def build(self, market: str, symbol: str) -> dict:
        cache_key = f"graph:context:{market}:{symbol}"
        cache = get_cache()
        
        # 尝试从缓存读取
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # 缓存未命中,执行查询
        ctx = self._query_graph(market, symbol)
        
        # 写入缓存
        ttl = cache.GRAPH_CONTEXT_TTL
        cache.set(cache_key, ctx, ttl)
        
        return ctx
```

### 4.4 新增 API 路由

**新建文件**: `backend_api_python/app/routes/graph_analysis.py`

提供图谱分析端点:
```python
from flask import Blueprint, request, jsonify
from app.graph.context_builder import GraphContextBuilder
from app.graph.event_impact_analyzer import EventImpactAnalyzer
from app.graph.smart_money_signal import SmartMoneySignal

bp = Blueprint('graph_analysis', __name__, url_prefix='/api/graph-analysis')

@bp.route('/enhanced-context')
def enhanced_context():
    """获取资产的图谱增强上下文"""
    market = request.args.get('market', 'Crypto')
    symbol = request.args.get('symbol', 'BTC/USDT')
    ctx = GraphContextBuilder().build(market, symbol)
    return jsonify({"data": ctx})

@bp.route('/contagion-path')
def contagion_path():
    """查询两个资产间的传染路径"""
    from_sym = request.args.get('from', '')
    to_sym = request.args.get('to', '')
    path = EventImpactAnalyzer().get_contagion_path(from_sym, to_sym)
    return jsonify({"data": path})

@bp.route('/smart-money/<symbol>')
def smart_money(symbol):
    """获取聪明钱信号"""
    sms = SmartMoneySignal()
    return jsonify({
        "polymarket_direction": sms.get_polymarket_smart_money(symbol),
        "whale_accumulation": sms.get_whale_accumulation(symbol),
    })
```

**修改文件**: `backend_api_python/app/__init__.py`

注册新的 Blueprint:
```python
from app.routes.graph_analysis import graph_analysis_bp
app.register_blueprint(graph_analysis_bp)
```

---

## 第五阶段:前端展示与优化(1周)

### 5.1 前端 API 调用封装

**修改文件**: `frontend/src/api/` (在 Vue 源码仓库中)

新增图谱分析 API 封装:
```javascript
export function getGraphContext(market, symbol) {
  return request({
    url: '/api/graph-analysis/enhanced-context',
    method: 'get',
    params: { market, symbol }
  })
}

export function getContagionPath(fromSymbol, toSymbol) {
  return request({
    url: '/api/graph-analysis/contagion-path',
    method: 'get',
    params: { from: fromSymbol, to: toSymbol }
  })
}
```

### 5.2 AI 分析结果增强展示

在现有 AI 分析结果页面中,增加"图谱增强信息"板块,展示:
- 关联资产列表
- 新闻情感分布
- KOL/机构信号
- 事件影响链

### 5.3 性能优化

实施以下优化措施:

| 优化项 | 实现方式 |
|--------|----------|
| 图查询缓存 | Redis 缓存,TTL 5-15分钟 |
| 异步图查询 | 图谱上下文与主数据采集并行执行 |
| 降级机制 | Neo4j 不可用时自动跳过,不影响主流程 |
| 查询超时 | 所有 Cypher 查询设置 3s 超时 |
| 结果限制 | 所有图查询添加 LIMIT 子句 |

---

## 第六阶段:测试与文档(1周)

### 6.1 单元测试

**新建文件**: `backend_api_python/tests/test_graph_integration.py`

测试内容:
- Graphiti 连接初始化
- 数据导入 Pipeline
- 图谱上下文构建
- AI 分析集成降级处理

### 6.2 集成测试

测试场景:
1. 完整流程:数据采集 → 图谱构建 → AI 分析 → 结果输出
2. 降级测试:Neo4j 不可用时,系统仍能正常运行
3. 性能测试:图谱查询延迟 < 3秒

### 6.3 文档更新

**新建文件**: `docs/GRAPHITI_INTEGRATION_CN.md`

包含:
- 部署指南
- 数据导入说明
- API 使用示例
- 故障排除

---

## 关键设计决策

### 1. 为何选择全链路集成而非渐进式

根据用户反馈,三个市场领域同时推进,一次性完成全链路集成。这样可以:
- 避免多次重构
- 保持架构一致性
- 快速验证图谱价值

### 2. PostgreSQL 与 Neo4j 的分工

| 数据类型 | 存储位置 | 原因 |
|----------|----------|------|
| 用户/订单/策略 | PostgreSQL | 关系型数据,需要 ACID |
| K线/行情时序数据 | PostgreSQL + Redis | 高频读写,需要缓存 |
| 实体关系/知识图谱 | Neo4j (via Graphiti) | 图遍历/多跳查询 |
| 图谱上下文缓存 | Redis | 降低 Neo4j 查询压力 |

### 3. Graphiti vs 纯 Neo4j Cypher

Graphiti 提供:
- 时态感知(自动处理事实的时间有效性)
- LLM 自动提取实体和关系
- Episode 驱动的数据摄入流程

纯 Cypher 查询用于:
- 已有的固定查询模式
- 性能敏感的简单查询
- 不需要 LLM 提取的场景

### 4. 降级安全机制

所有图谱相关操作都包裹在 try-except 中:
```python
try:
    graph_ctx = builder.build(market, symbol)
except Exception as e:
    logger.debug(f"Graph context failed (non-critical): {e}")
    graph_ctx = {}
```

确保 Neo4j 不可用时,现有 AI 分析流程不受影响。

---

## 实施时间线

| 阶段 | 工期 | 关键交付物 |
|------|------|------------|
| 基础设施搭建 | 1-2周 | Neo4j Docker、连接管理、索引初始化 |
| 本体定义与数据导入 | 2-3周 | 三大本体、导入 Pipeline、调度器 |
| 图谱查询与分析服务 | 2-3周 | ContextBuilder、EventAnalyzer、SmartMoney |
| 与现有系统集成 | 2周 | FastAnalysis 集成、MarketDataCollector 增强、API 路由 |
| 前端展示与优化 | 1周 | 前端组件、性能优化、缓存策略 |
| 测试与文档 | 1周 | 单元测试、集成测试、用户文档 |

**总计**: 9-12 周

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Graphiti 依赖 LLM 调用 | 成本高、速度慢 | 设置 Episode 过滤阈值,仅记录重要事件 |
| Neo4j 内存消耗大 | 服务器资源不足 | 限制堆内存 2G,实施图谱剪枝策略 |
| 数据导入冲突 | 图谱数据不一致 | 使用 Graphiti 的时态融合机制 |
| 查询性能下降 | AI 分析延迟增加 | Redis 缓存 + 3s 超时 + 降级机制 |

---

## 后续优化方向

1. **向量数据库集成**: 为 Graphiti 添加 Milvus/Pinecone 支持语义搜索
2. **实时流处理**: 使用 Kafka + Graphiti 实现实时图谱更新
3. **图谱可视化**: 前端集成 Neo4j Bloom 或自定义 D3.js 图谱展示
4. **策略引擎增强**: 在 ScriptStrategy 中暴露图谱查询接口,支持策略基于图谱关系生成信号