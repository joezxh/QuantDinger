# QuantDinger 统一技术改造实施方案

> 版本：v2.0 | 日期：2026-04 | 状态：基于11份技术文档与工程代码深度分析综合制定

---

## 一、现状分析

### 1.1 代码库规模与分布

| 层级 | 文件/模块数 | 备注 |
|------|-----------|------|
| 后端 Python 文件 | ~120+ | 分布在 app/services、app/routes、app/data_sources 等 |
| 使用裸 SQL 文件 | 22个 | 通过 `get_db_connection()` 直接操作 psycopg2 |
| SQLAlchemy 模型 | 15个文件 | 涵盖 User/Strategy/Market/Graph 等基础模型 |
| Repository 文件 | 18个 | 已有基础封装，但大部分 Service 未使用 |
| 现有 Alembic 迁移 | 4个版本文件 | 缺少 001_initial_schema，存在冗余版本 |
| init.sql 行数 | 1026行 | 含所有表定义 + DO $$ 补丁块 |
| 前端页面模块 | 17个视图目录 | Vue.js 2/3 项目 |

### 1.2 数据库访问层现状

**核心问题文件：**

```
backend_api_python/app/utils/db_postgres.py   ← psycopg2 连接池 + PostgresCursor 兼容层（495行）
backend_api_python/app/utils/db.py             ← 统一入口，转发到 db_postgres.py
backend_api_python/app/database/engine.py      ← SQLAlchemy Engine（已建，但未全面使用）
backend_api_python/app/database/session.py     ← SQLAlchemy Session 工厂（已建）
```

**裸 SQL 使用分布（22个文件）：**

| 模块分类 | 文件 | SQL 操作类型 | 迁移优先级 |
|---------|------|-------------|-----------|
| Routes层 | `routes/llm.py` | CRUD + 复杂查询 | P0 |
| Routes层 | `routes/indicator.py` | CRUD + DDL补丁 | P0 |
| Routes层 | `routes/dashboard.py` | 聚合查询 | P1 |
| Routes层 | `routes/quick_trade.py` | CRUD | P1 |
| Services层 | `services/trading_executor.py` | CRUD + 事务 | P0 |
| Services层 | `services/fast_analysis.py` | CRUD + 批量写入 | P0 |
| Services层 | `services/signal_notifier.py` | 批量查询 | P1 |
| Services层 | `services/backtest.py` | DDL补丁 + CRUD | P1 |
| Services层 | `services/llm_registry.py` | CRUD + 状态管理 | P0 |
| Services层 | `services/ai_calibration.py` | CRUD | P1 |
| Services层 | `services/billing_service.py` | CRUD | P1 |
| Services层 | `services/community_service.py` | DDL补丁 + CRUD | P1 |
| Services层 | `services/indicator_params.py` | CRUD | P1 |
| Services层 | `services/strategy_snapshot.py` | CRUD | P1 |
| Services层 | `services/polymarket_worker.py` | CRUD | P1 |
| Services层 | `services/polymarket_batch_analyzer.py` | 批量写入 | P1 |
| Services层 | `services/email_service.py` | CRUD | P2 |
| Services层 | `services/strategy.py` | CRUD | P2 |
| Data层 | `data_sources/polymarket.py` | CRUD | P1 |
| Data层 | `data/market_symbols_seed.py` | 种子数据 | P2 |

### 1.3 现有模型覆盖情况

**已定义 SQLAlchemy 模型：**
- `User` (user.py) — 部分字段，缺少 credits_log、membership 等关联
- `StrategyTrading` (strategy.py) — 基础字段
- `MarketPrice`, `MarketKline` (market.py)
- `BacktestResult`, `BacktestTrade`, `BacktestEquityPoint` (backtest.py)
- `TradeOrder` (trading.py)
- `AnalysisResult` (analysis.py)
- `BillingRecord` (billing.py)
- `CommunityIndicator` (community.py)
- `CollectionRecord` (collection.py)
- `PolymarketMarket`, `PolymarketAnalysis`, `PolymarketOpportunity`, `PolymarketUser` (polymarket.py)
- `LoginAttempt`, `OAuthState`, `SecurityLog` (auth_security.py)
- `GraphEpisode`, `GraphJob`, `GraphEntityRef`, `GraphRelationSnapshot`, `GraphFeatureDaily` (graph_meta.py)
- `CompanyNarrativeFeature`, `CryptoNarrativeFeature`, `PolymarketMarketFeature` (graph_domain.py)

**缺失的模型（需新建）：**
- `CreditsLog` — qd_credits_log
- `MembershipOrder` — qd_membership_orders
- `UsdtOrder` — qd_usdt_orders
- `VerificationCode` — qd_verification_codes
- `IndicatorCode` — qd_indicator_codes（community.py 中仅有 CommunityIndicator 简化版）
- `IndicatorPurchase` — qd_indicator_purchases
- `IndicatorComment` — qd_indicator_comments
- `Watchlist` — qd_watchlist
- `AnalysisTask` — qd_analysis_tasks
- `AnalysisMemory` — qd_analysis_memory
- `StrategyPosition` — qd_strategy_positions
- `PendingOrder` — pending_orders
- `StrategyNotification` — qd_strategy_notifications
- `StrategyLog` — qd_strategy_logs
- `ExchangeCredential` — qd_exchange_credentials
- `ManualPosition` — qd_manual_positions
- `PositionAlert` — qd_position_alerts
- `PositionMonitor` — qd_position_monitors
- `MarketSymbol` — qd_market_symbols
- `QuickTrade` — qd_quick_trades

### 1.4 Alembic 迁移现状

```
migrations/
├── alembic.ini                    ← 配置正确，但仅4行
├── env.py                         ← 已配置，但 Model 导入不完整
└── versions/
    ├── （缺失 001_initial_schema.py）
    ├── 002_add_collection_tables.py
    ├── 003_add_graph_meta_tables.py
    ├── 003_graphiti_phase1.py     ← 冗余文件，需清理
    └── 004_add_graph_feature_tables.py
```

**关键问题：**
- 没有 001_initial_schema.py 作为初始基准
- `003_graphiti_phase1.py` 是冗余版本，与 003 冲突
- `env.py` 中仅导入了部分模型（collection、graph_meta、graph_domain），未导入 user、strategy、market 等核心模型
- 所有表实际通过 `init.sql` 创建，Alembic 未参与现有表的版本管理

### 1.5 图谱模块现状

**已实现：**
- `app/graph/connection.py` — Neo4j 驱动连接，含优雅降级
- `app/graph/queries.py` — 5个领域 Cypher 查询封装
- `app/graph/context_builder.py` — GraphContextBuilder + format_graph_context_for_llm
- `app/graph/graphiti_gateway.py` — GraphitiGateway，已含 `GRAPHITI_ENABLED` 开关
- `app/graph/cache_gateway.py` — Redis 缓存网关
- `app/services/fast_analysis_graph_patch.py` — AI 分析图谱增强补丁
- `app/services/graph_prompt_bridge.py` — Prompt 注入桥接

**待实现：**
- Graphiti 实体代码未从源码复制到项目中
- Dify 工作流集成模块未开发
- 前端图谱可视化页面未开发

### 1.6 前端现状

- 技术栈：Vue.js + Ant Design Vue
- 17个视图模块：ai-analysis、trading-bot、llm、dashboard、indicator-community 等
- API 层已分离在 `/api/` 目录
- 缺少：图谱可视化、Dify 工作流管理、图谱因子展示等页面

---

## 二、改造目标

### 2.1 总体目标

将 QuantDinger 从"psycopg2 裸 SQL + 单体 init.sql"架构升级为"SQLAlchemy ORM + Alembic 版本迁移 + Neo4j 图查询 + Graphiti 时态编排 + Dify 工作流增强"的现代化架构。

### 2.2 九大改造模块

| 序号 | 模块 | 优先级 | 预估工期 |
|------|------|--------|---------|
| 1 | SQLAlchemy ORM 全量迁移 | P0 | 5-6周 |
| 2 | Alembic 统一初始迁移 + 清理 | P0 | 1周 |
| 3 | Dify 工作流集成 | P0 | 2-3周 |
| 4 | Graphiti 源码内嵌集成 | P1 | 1-2周 |
| 5 | Neo4j 基础设施完善 | P0 | 2周 |
| 6 | 统一直连Cypher查询优先策略 | P1 | 2周 |
| 7 | AI 分析增强（图谱上下文注入） | P1 | 2-3周 |
| 8 | 图谱因子与策略回测增强 | P1 | 2-3周 |
| 9 | 前端同步改造 | P1 | 4-5周 |

---

## 三、详细实施方案

### 模块一：SQLAlchemy ORM 全量迁移（P0，5-6周）

#### 3.1 迁移策略：三阶段双轨并行

```
Phase A（第1-2周）：补齐模型层
  ├─ 新建缺失的 20 个模型文件
  ├─ 完善现有模型字段（如 User 表补充所有列）
  └─ 更新 models/__init__.py 注册所有模型

Phase B（第2-5周）：逐模块替换裸SQL
  ├─ P0模块优先：llm.py → indicator.py → fast_analysis.py → trading_executor.py
  ├─ P1模块次之：dashboard.py → backtest.py → signal_notifier.py → ai_calibration.py
  ├─ P2模块收尾：email_service.py → strategy.py → market_symbols_seed.py
  └─ 淘汰所有 DDL 补丁代码（DO $$ ALTER TABLE 模式）

Phase C（第5-6周）：清理兼容层
  ├─ 删除 db_postgres.py 中的 PostgresCursor 兼容层
  ├─ 保留 db.py 作为 Facade，但底层转发到 SQLAlchemy Session
  └─ 清理所有 `?` 占位符转换逻辑
```

#### 3.2 具体文件改造清单

**新建模型文件（共7个新文件）：**

| 新文件 | 包含模型 | 对应表 |
|-------|---------|--------|
| `models/credits.py` | CreditsLog | qd_credits_log |
| `models/membership.py` | MembershipOrder, UsdtOrder | qd_membership_orders, qd_usdt_orders |
| `models/verification.py` | VerificationCode, OAuthLink | qd_verification_codes, qd_oauth_links |
| `models/indicator_full.py` | IndicatorCode, IndicatorPurchase, IndicatorComment | qd_indicator_codes, qd_indicator_purchases, qd_indicator_comments |
| `models/watchlist.py` | Watchlist | qd_watchlist |
| `models/analysis_task.py` | AnalysisTask, AnalysisMemory | qd_analysis_tasks, qd_analysis_memory |
| `models/position.py` | StrategyPosition, ManualPosition, PositionAlert, PositionMonitor | qd_strategy_positions, qd_manual_positions, qd_position_alerts, qd_position_monitors |
| `models/order.py` | PendingOrder, QuickTrade | pending_orders, qd_quick_trades |
| `models/exchange.py` | ExchangeCredential | qd_exchange_credentials |
| `models/notification.py` | StrategyNotification, StrategyLog | qd_strategy_notifications, qd_strategy_logs |
| `models/market_symbol.py` | MarketSymbol | qd_market_symbols |

**改造现有模型文件：**
- `models/user.py` — 补充 vip_plan, vip_is_lifetime, vip_monthly_credits_last_grant, email_verified, referred_by, notification_settings, chart_templates 字段
- `models/strategy.py` — 补充所有 strategy_config 字段、strategy_code、last_rebalance_at
- `models/auth_security.py` — 确认 OAuthState PK 为 state 字段（非 id 自增）

**路由/服务层改造（22个文件）：**

| 文件 | 改造要点 | 预估变更行数 |
|------|---------|------------|
| `routes/llm.py` | 所有 CURD 改为 Repository 调用 | ~200行 SQL → ~80行 ORM |
| `routes/indicator.py` | DDL补丁移除 + CRUD迁移 | ~150行 SQL → ~60行 ORM |
| `routes/dashboard.py` | 聚合查询改为 ORM | ~100行 SQL → ~50行 ORM |
| `routes/quick_trade.py` | CRUD迁移 | ~80行 SQL → ~40行 ORM |
| `services/trading_executor.py` | 大量 CRUD + 事务迁移 | ~500行 SQL → ~200行 ORM |
| `services/fast_analysis.py` | CRUD + 批量写入迁移 | ~100行 SQL → ~50行 ORM |
| `services/signal_notifier.py` | 批量查询迁移 | ~150行 SQL → ~70行 ORM |
| `services/backtest.py` | DDL补丁移除 + CRUD迁移 | ~50行 SQL → ~20行 ORM |
| `services/llm_registry.py` | CRUD + 状态管理迁移 | ~100行 SQL → ~50行 ORM |
| `services/ai_calibration.py` | CRUD迁移 | ~80行 SQL → ~40行 ORM |
| 其他12个文件 | 各文件CRUD迁移 | ~600行 SQL → ~300行 ORM |

#### 3.3 Repository 扩展

在现有 18 个 Repository 基础上新增：

```
database/repositories/
├── credits_repository.py         ← 积分日志
├── membership_repository.py      ← 会员订单
├── verification_repository.py    ← 验证码
├── indicator_repository.py       ← 指标社区完整版
├── watchlist_repository.py       ← 自选列表
├── analysis_task_repository.py   ← 分析任务
├── analysis_memory_repository.py ← 分析记忆
├── notification_repository.py    ← 通知日志
├── order_repository.py           ← 订单队列
├── position_repository.py        ← 仓位管理
├── exchange_repository.py        ← 交易所凭证
└── market_symbol_repository.py   ← 市场品种
```

#### 3.4 兼容层过渡方案

```python
# app/utils/db.py — 改造为双模 Facade
from app.database.session import get_session
from app.utils.db_postgres import get_pg_connection  # 保留旧实现

def get_db_connection():
    """
    优先返回 SQLAlchemy Session 适配器；
    若 ORM 不可用则回退到 psycopg2 连接。
    """
    use_orm = os.getenv("DB_USE_ORM", "false").lower() == "true"
    if use_orm:
        return SQLAlchemySessionAdapter(get_session())
    return get_pg_connection()  # 旧行为
```

**切换策略：** 通过环境变量 `DB_USE_ORM=true` 逐模块灰度切换，验证通过后再设为默认。

---

### 模块二：Alembic 统一初始迁移（P0，1周）

#### 3.5 操作步骤

1. **导出 init.sql 所有表结构为 ORM 模型** —— 确保每个表都有对应的 SQLAlchemy 模型
2. **生成 001_initial_schema.py：**
   ```bash
   cd backend_api_python
   alembic revision --autogenerate -m "001_initial_schema"
   ```
   此时 autogenerate 会基于 `Base.metadata` 自动检测所有模型并生成完整建表语句

3. **更新 env.py 导入所有模型：**
   ```python
   # 确保所有模型被导入以注册到 Base.metadata
   from app.models.user import User
   from app.models.strategy import Strategy, StrategyTrading
   from app.models.market import MarketPrice, MarketKline
   from app.models.backtest import BacktestResult, BacktestTrade, BacktestEquityPoint
   from app.models.trading import TradeOrder
   from app.models.analysis import AnalysisResult
   from app.models.billing import BillingRecord
   from app.models.community import CommunityIndicator
   from app.models.collection import CollectionRecord
   from app.models.polymarket import PolymarketMarket, PolymarketAnalysis, PolymarketOpportunity, PolymarketUser
   from app.models.auth_security import LoginAttempt, OAuthState, SecurityLog
   from app.models.graph_meta import GraphEpisode, GraphJob, GraphEntityRef, GraphRelationSnapshot, GraphFeatureDaily
   from app.models.graph_domain import CompanyNarrativeFeature, CryptoNarrativeFeature, PolymarketMarketFeature
   # 新增模型
   from app.models.credits import CreditsLog
   from app.models.membership import MembershipOrder, UsdtOrder
   # ... 所有其他新模型
   ```

4. **清理冗余迁移文件：**
   - 删除 `versions/003_graphiti_phase1.py`（与 003 重复）
   - 验证 002/003/004 的依赖链正确

5. **更新 docker-compose.yml 移除 init.sql 自动执行：**
   ```yaml
   postgres:
     volumes:
       # 移除: - ./migrations/init.sql:/docker-entrypoint-initdb.d/init.sql
       - postgres_data:/var/lib/postgresql/data
   ```
   改为在应用启动时自动执行 `alembic upgrade head`

6. **在 run.py 中添加自动迁移：**
   ```python
   def init_db():
       from alembic.config import Config
       from alembic import command
       alembic_cfg = Config("migrations/alembic.ini")
       command.upgrade(alembic_cfg, "head")
   ```

#### 3.6 迁移版本最终结构

```
migrations/versions/
├── 001_initial_schema.py          ← 新：包含所有现有表结构
├── 002_add_collection_tables.py   ← 保留
├── 003_add_graph_meta_tables.py   ← 保留（合并原003_graphiti_phase1内容）
├── 004_add_graph_feature_tables.py← 保留
└── （之后新增的迁移）
```

---

### 模块三：Dify 工作流集成（P0，2-3周）

#### 3.7 设计原则

- **不在 Graphiti 数据生成阶段使用 Dify**，仅在 AI 分析模块中集成
- **保留现有分析 pipeline**（fast_analysis.py 的直接 LLM 调用链路）
- **新增可选的 Dify 工作流分析选项**，通过前端切换选择

#### 3.8 工作流管理模块设计

**目录结构：**
```
backend_api_python/app/services/dify/
├── __init__.py
├── workflow_manager.py      ← 工作流配置管理 CRUD
├── workflow_executor.py     ← 流式/段式调用执行器
├── workflow_registry.py     ← 工作流注册与 code 编码表
└── dify_client.py           ← Dify API 客户端封装
```

**数据模型（新表）：**
```sql
CREATE TABLE qd_dify_workflows (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,      -- 工作流编码（如 'ai_stock_analysis_v1'）
    name VARCHAR(100) NOT NULL,             -- 工作流名称
    description TEXT DEFAULT '',
    workflow_type VARCHAR(50) DEFAULT 'chat', -- chat/workflow/completion
    endpoint VARCHAR(255) NOT NULL,         -- Dify API endpoint
    api_key VARCHAR(255) NOT NULL,          -- Dify API Key（加密存储）
    input_schema JSONB DEFAULT '{}',        -- 输入参数 schema
    output_schema JSONB DEFAULT '{}',       -- 输出参数 schema
    is_active BOOLEAN DEFAULT TRUE,
    max_retries INT DEFAULT 3,
    timeout_seconds INT DEFAULT 120,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE qd_dify_workflow_logs (
    id SERIAL PRIMARY KEY,
    workflow_id INT REFERENCES qd_dify_workflows(id),
    user_id INT REFERENCES qd_users(id),
    input_data JSONB,
    output_data JSONB,
    status VARCHAR(20) DEFAULT 'pending',   -- pending/running/success/failed
    call_mode VARCHAR(10) DEFAULT 'batch',   -- streaming/batch
    tokens_used INT DEFAULT 0,
    latency_ms INT DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 3.9 调用方式

**方式一：流式调用（Streaming）**
```python
# app/services/dify/workflow_executor.py
class DifyWorkflowExecutor:
    async def run_streaming(self, workflow_code: str, inputs: dict, user_id: int):
        """
        流式调用 Dify 工作流，通过 SSE 逐步返回结果。
        适用于需要实时展示分析过程的场景。
        """
        workflow = self.registry.get_by_code(workflow_code)
        async for chunk in self.client.chat_stream(
            endpoint=workflow.endpoint,
            api_key=workflow.api_key,
            inputs=inputs,
            user=str(user_id),
        ):
            yield chunk
```

**方式二：段式调用（Batch）**
```python
    def run_batch(self, workflow_code: str, inputs: dict, user_id: int) -> dict:
        """
        段式调用 Dify 工作流，等待完整结果返回。
        适用于批量分析、定时任务场景。
        """
        workflow = self.registry.get_by_code(workflow_code)
        return self.client.chat_blocking(
            endpoint=workflow.endpoint,
            api_key=workflow.api_key,
            inputs=inputs,
            user=str(user_id),
        )
```

#### 3.10 与现有分析 Pipeline 的集成

```python
# app/services/fast_analysis.py — 改造点
class FastAnalysisService:
    # 新增属性
    dify_executor: DifyWorkflowExecutor | None = None
    
    def analyze(self, market, symbol, **kwargs):
        use_dify = kwargs.get('use_dify', False)
        workflow_code = kwargs.get('workflow_code', '')
        
        if use_dify and workflow_code:
            return self._run_dify_analysis(market, symbol, workflow_code, **kwargs)
        else:
            return self._run_direct_llm_analysis(market, symbol, **kwargs)  # 现有逻辑
    
    def _run_dify_analysis(self, market, symbol, workflow_code, **kwargs):
        inputs = self._build_dify_inputs(market, symbol, **kwargs)
        if kwargs.get('streaming', False):
            return self.dify_executor.run_streaming(workflow_code, inputs, kwargs.get('user_id'))
        return self.dify_executor.run_batch(workflow_code, inputs, kwargs.get('user_id'))
    
    def _run_direct_llm_analysis(self, market, symbol, **kwargs):
        # 保留现有完整分析逻辑
        pass
```

#### 3.11 API 路由

```python
# routes/dify_workflow.py（新建）
@dify_bp.route('/workflows', methods=['GET'])         # 列出所有工作流
@dify_bp.route('/workflows', methods=['POST'])        # 创建/注册工作流
@dify_bp.route('/workflows/<code>', methods=['PUT'])  # 更新工作流配置
@dify_bp.route('/workflows/<code>', methods=['DELETE'])# 删除工作流
@dify_bp.route('/workflows/<code>/run', methods=['POST'])  # 执行工作流（支持 streaming/batch）
@dify_bp.route('/workflows/<code>/logs', methods=['GET'])  # 查询执行日志
```

---

### 模块四：Graphiti 源码内嵌集成（P1，1-2周）

#### 3.12 集成方式

**要点：不独立启动 Graphiti 服务，而是作为 QuantDinger 应用的一部分**

```bash
# 步骤1：复制 Graphiti 实体代码
cp -r d:\projects\github\graphiti\graphiti_core backend_api_python/graphiti_core/

# 步骤2：复制依赖配置
# 将 graphiti_core 的依赖加入 requirements.txt
```

**目录结构（复制后）：**
```
backend_api_python/
├── graphiti_core/              ← 从 d:\projects\github\graphiti 复制
│   ├── __init__.py
│   ├── graphiti.py
│   ├── nodes.py
│   ├── edges.py
│   ├── helpers.py
│   ├── cross_encoder/
│   ├── driver/
│   ├── embedder/
│   ├── llm_client/
│   ├── models/
│   ├── prompts/
│   ├── search/
│   ├── telemetry/
│   └── utils/
```

#### 3.13 自有 Model Import 机制

```python
# app/graph/graphiti_adapter.py（新建）
"""
Graphiti 适配层：使用自有 model import 机制进行实体注册和调用。
不依赖 neomodel，直接通过 neo4j-driver + Cypher 操作。
"""
from graphiti_core import Graphiti
from graphiti_core.nodes import Entity
from graphiti_core.edges import Edge
from pydantic import Field
import os


class QuantDingerGraphiti:
    """
    QuantDinger 定制的 Graphiti 封装。
    实体类型由项目中定义的 Pydantic 模型通过 import 机制注册。
    """
    
    def __init__(self):
        self._instance = None
        self._enabled = os.getenv("GRAPHITI_ENABLED", "false").lower() == "true"
    
    def _get_instance(self):
        if not self._instance and self._enabled:
            self._instance = Graphiti(
                neo4j_uri=os.getenv("NEO4J_URI"),
                neo4j_user=os.getenv("NEO4J_USER"),
                neo4j_password=os.getenv("NEO4J_PASSWORD"),
            )
        return self._instance
    
    # 实体注册通过 Python import 自动完成
    # 使用时 from app.graph.entities import StockEntity, CryptoEntity, ...
```

#### 3.14 实体定义（自有模型）

```python
# app/graph/entities.py（新建）
"""
定义 QuantDinger 自有 Graphiti 实体模型。
使用 Python import 机制注册到 Graphiti 运行时。
"""
from graphiti_core.nodes import Entity
from pydantic import Field
from typing import Optional


class StockCompany(Entity):
    ticker: str = Field(..., description="股票代码")
    name: str = Field(..., description="公司名称")
    industry: Optional[str] = Field(None, description="行业")
    market_cap: Optional[float] = Field(None, description="市值")

class CryptoAsset(Entity):
    symbol: str = Field(..., description="交易对符号")
    chain: Optional[str] = Field(None, description="公链")
    category: Optional[str] = Field(None, description="类别")

class PolymarketEvent(Entity):
    market_id: str = Field(..., description="市场ID")
    question: str = Field(..., description="预测问题")
    category: Optional[str] = Field(None, description="分类")
```

---

### 模块五：Graphiti 启用策略（P0，配置开关）

#### 3.15 两阶段启用策略

**阶段一：纯 Cypher 直连查询（当前 → 数据质量达标）**
- 所有图谱查询直接通过 `app/graph/queries.py` 的 Cypher 语句执行
- Graphiti 的 `add_episode`、`search` 等功能处于禁用状态
- 环境变量：`GRAPHITI_ENABLED=false`

**阶段二：Graphiti 增强模式（数据量+质量达标后）**
- 开启 Graphiti 叙事抽取（narrative extraction）
- 开启冲突消解（conflict resolution）
- 开启 GraphRAG 时态检索
- 环境变量：`GRAPHITI_ENABLED=true`

#### 3.16 配置开关实现

```python
# app/config/graph_config.py（新建）
class GraphConfig:
    # 主开关
    GRAPHITI_ENABLED: bool = os.getenv("GRAPHITI_ENABLED", "false").lower() == "true"
    
    # 细粒度开关（阶段二启用时有效）
    GRAPHITI_NARRATIVE_EXTRACTION: bool = os.getenv("GRAPHITI_NARRATIVE", "false").lower() == "true"
    GRAPHITI_CONFLICT_RESOLUTION: bool = os.getenv("GRAPHITI_CONFLICT", "false").lower() == "true"
    GRAPHITI_GRAPHRAG_SEARCH: bool = os.getenv("GRAPHITI_GRAPHRAG", "false").lower() == "true"
    
    # 质量阈值（触发阶段二的条件）
    MIN_EPISODE_COUNT: int = int(os.getenv("GRAPH_MIN_EPISODES", "1000"))
    MIN_ENTITY_COUNT: int = int(os.getenv("GRAPH_MIN_ENTITIES", "500"))
    MIN_RELATION_COUNT: int = int(os.getenv("GRAPH_MIN_RELATIONS", "2000"))
```

#### 3.17 数据质量达标监控

```python
# app/graph/quality_monitor.py（新建）
class GraphQualityMonitor:
    def check_readiness(self) -> dict:
        """
        检查图谱数据是否达到开启 Graphiti 的质量标准。
        返回各指标状态及总体就绪判断。
        """
        return {
            "episode_count": self._count_episodes(),
            "entity_count": self._count_entities(),
            "relation_count": self._count_relations(),
            "min_confidence_avg": self._avg_confidence(),
            "is_ready": all([...]),
        }
```

---

### 模块六：前端同步改造（P1，4-5周）

#### 3.18 前端改造范围

| 模块 | 改造内容 | 预估工时 |
|------|---------|---------|
| AI分析页面 | Dify 工作流模式切换、图谱上下文可视化、流式输出展示 | 1.5周 |
| LLM管理页面 | Dify 工作流配置管理 UI（CRUD、日志查看） | 1周 |
| 图谱可视化 | 新增图关系可视化组件（ECharts/D3.js 力导向图） | 1.5周 |
| 图谱分析页面 | 聪明钱/KOL/叙事漂移/事件链展示 | 1周 |
| API 适配层 | 新增 `api/dify.js`、`api/graph.js`、更新现有 API | 0.5周 |
| 全局布局 | 新增图谱分析菜单入口 | 0.5周 |

#### 3.19 前端文件改造清单

**新增文件：**
```
frontend/src/
├── api/
│   ├── dify.js                  ← Dify 工作流 API 封装
│   └── graph.js                 ← 图谱查询 API 封装
├── views/
│   ├── graph-analysis/          ← 图谱分析页面（新增）
│   │   ├── index.vue            ← 图谱分析主页（聪明钱/叙事漂移/事件链）
│   │   └── components/
│   │       ├── SmartMoney.vue   ← 聪明钱信号展示
│   │       ├── NarrativeDrift.vue← 叙事漂移时间线
│   │       └── EventChain.vue   ← 事件影响链路图
│   └── dify-workflow/           ← Dify 工作流管理页面（新增）
│       ├── index.vue            ← 工作流列表管理
│       ├── WorkflowForm.vue     ← 工作流创建/编辑表单
│       └── WorkflowLogs.vue     ← 执行日志查看
├── components/
│   └── GraphVisualization/      ← 图可视化组件（新增）
│       ├── ForceGraph.vue       ← 力导向图组件
│       ├── RelationGraph.vue    ← 关系图组件
│       └── GraphContextPanel.vue← 图谱上下文面板
```

**修改文件：**
```
frontend/src/
├── api/
│   └── fast-analysis.js         ← 新增 useDify 参数支持
├── views/
│   ├── ai-analysis/
│   │   └── index.vue            ← 新增 Dify 工作流选择器、图谱上下文展示区
│   ├── llm/
│   │   └── index.vue            ← 新增 Dify 工作流管理入口
│   └── dashboard/
│       └── index.vue            ← 新增图谱状态概览卡片
├── router/
│   └── index.js                 ← 新增 /graph-analysis、/dify-workflow 路由
└── store/
    └── modules/
        └── graph.js             ← 新增图谱状态管理（Vuex）
```

---

## 四、分阶段实施路线图

### Phase 0：环境与基础设施准备（第1-2周）

| 任务 | 责任人 | 产出 |
|------|--------|------|
| Docker Compose 添加 Neo4j 容器 | 后端 | 可运行的 Neo4j 实例 |
| 安装 neo4j、graphiti-core 等新依赖 | 后端 | 更新的 requirements.txt |
| 配置 NEO4J_URI/USER/PASSWORD 环境变量 | 后端 | .env 更新 |
| 复制 Graphiti 源码到项目中 | 后端 | graphiti_core/ 目录 |
| 前端项目依赖更新 | 前端 | package.json 更新 |

### Phase 1：ORM 模型层补齐（第2-4周）

| 任务 | 产出 |
|------|------|
| 新建 11 个缺失的模型文件 | 20+ SQLAlchemy 模型完全覆盖 init.sql 所有表 |
| 完善现有模型字段 | User/Strategy 等模型字段完整 |
| 更新 models/__init__.py | 所有模型统一注册到 Base.metadata |
| 创建 12 个新 Repository | 完整的 Repository 层 |
| 更新 alembic env.py 导入所有模型 | autogenerate 可检测所有表 |

### Phase 2：Alembic 迁移统一 + 核心模块 ORM 切换（第4-6周）

| 任务 | 产出 |
|------|------|
| 生成 001_initial_schema.py | 包含所有现有表结构的初始迁移 |
| 清理冗余迁移文件 | 迁移版本链清晰 |
| 移除 init.sql 自动执行 | Alembic 接管 Schema 管理 |
| routes/llm.py ORM 迁移 | LLM 管理接口全部切换到 ORM |
| services/llm_registry.py ORM 迁移 | LLM 注册表切换到 ORM |
| routes/indicator.py ORM 迁移 | 指标管理接口切换到 ORM |
| services/fast_analysis.py ORM 迁移 | AI 分析核心切换到 ORM |
| services/trading_executor.py ORM 迁移 | 交易执行器切换到 ORM（重点） |

### Phase 3：图谱基础设施 + Dify 集成（第6-9周）

| 任务 | 产出 |
|------|------|
| Neo4j 索引约束初始化 | 所有节点/关系约束就绪 |
| 图查询 API 完善 | 5个领域查询 API 可调用 |
| Dify 工作流管理 CRUD | 前后端工作流配置功能完整 |
| Dify 流式/段式调用 | 两种调用方式均可工作 |
| AI 分析 Dify 可选集成 | FastAnalysis 可切换 Dify 模式 |
| 前端图谱页面开发 | 图谱可视化页面可用 |

### Phase 4：三大领域图谱 + 剩余 ORM 迁移（第9-13周）

| 任务 | 产出 |
|------|------|
| 股票市场图谱化 | 公司/机构/人物/事件入图 |
| 加密货币图谱化 | 资产/协议/鲸鱼/KOL 入图 |
| 预测市场图谱化 | 市场/用户/外部事件入图 |
| 跨域桥接实体建立 | 统一实体 ID 映射就绪 |
| 剩余 Service ORM 迁移 | 所有 22 个文件迁移完成 |
| API 路由层 ORM 迁移收尾 | 全项目零裸 SQL |

### Phase 5：AI 增强 + 前端集成（第13-16周）

| 任务 | 产出 |
|------|------|
| 图谱上下文注入 AI 分析 | 多跳关联推理可用 |
| 图谱因子落表 | qd_graph_feature_daily 有数据 |
| 回测引擎接入图谱因子 | 回测可使用图谱特征 |
| 前端图谱分析页面 | 聪明钱/叙事漂移/事件链可视化 |
| 前端 Dify 工作流管理 | 完整工作流管理 UI |
| 兼容层清理 | 删除 PostgresCursor 兼容代码 |

### Phase 6：治理、优化与稳定（第16-18周）

| 任务 | 产出 |
|------|------|
| 图谱质量监控 | 质量看板上线 |
| Graphiti 阶段二启用评估 | 数据质量达标判断 |
| 性能压测与优化 | P95 延迟达标 |
| 安全审计 | 凭证脱敏、SQL注入防护验证 |
| 文档与部署指南 | 完整运维文档 |

---

## 五、风险评估与应对

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| ORM 迁移导致线上业务中断 | 中 | 高 | 双轨并行，DB_USE_ORM 逐模块灰度切换，每步可回滚 |
| Alembic 自动生成迁移遗漏表 | 中 | 高 | 人工逐表校验 init.sql vs Base.metadata，CI 中加 schema diff 检测 |
| Graphiti 抽取结果不稳定 | 高 | 中 | 纯Cypher先行的两阶段策略，阶段二有质量阈值保护 |
| Dify 调用超时影响分析体验 | 中 | 中 | 设置 timeout + 自动降级到直接 LLM 调用 |
| Neo4j 查询压力导致延迟 | 中 | 中 | Redis 缓存热点子图，限制跳数深度 |
| 跨域实体对齐错误 | 中 | 高 | 保留 dual-alias 机制，人工审核入口 |
| Graphiti 源码兼容性问题 | 低 | 高 | 复制后先在独立分支验证导入和基础功能 |
| 前端改造导致用户体验下降 | 低 | 中 | 渐进式UI增强，保留旧界面作为 fallback |

---

## 六、测试验证方案

### 6.1 单元测试
- ORM 模型字段完整性测试 → 验证所有表字段与 init.sql 一致
- Repository CRUD 测试 → 每个 Repository 的增删改查全覆盖
- Alembic 迁移测试 → upgrade/downgrade 往返验证

### 6.2 集成测试
- 双轨兼容性测试 → 同一接口分别用 ORM 和裸 SQL 调用，结果一致
- 图谱查询降级测试 → Neo4j 不可用时返回空上下文不阻塞分析
- Dify 工作流执行测试 → streaming/batch 两种模式完整链路

### 6.3 性能测试
- ORM vs 裸 SQL 性能对比（P95 延迟）
- 图谱查询缓存命中率验证
- 并发采集 + 图写入压力测试

### 6.4 端到端测试
- AI 分析完整链路：采集 → 入图 → 上下文构建 → LLM 分析 → 前端展示
- Dify 工作流链路：配置 → 调用 → 流式输出 → 前端实时渲染
- 回测链路：图谱因子落表 → 回测读取 → 策略信号生成

---

## 七、环境变量与配置

```env
# === 数据库 ===
DATABASE_URL=postgresql://user:password@postgres:5432/quantdinger
DB_USE_ORM=true                   # 控制双轨切换（Phase 2 后默认 true）
DB_POOL_MIN=5
DB_POOL_MAX=50

# === Neo4j ===
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=quantdinger

# === Graphiti ===
GRAPHITI_ENABLED=false             # Phase 5 前保持 false（纯Cypher模式）
GRAPHITI_NARRATIVE=false           # 叙事抽取开关
GRAPHITI_CONFLICT=false            # 冲突消解开关
GRAPHITI_GRAPHRAG=false            # GraphRAG 检索开关
GRAPHITI_LLM_MODEL=gpt-4o-mini
GRAPHITI_IMPORTANCE_THRESHOLD=0.65
GRAPH_MIN_EPISODES=1000            # 触发阶段二的最低 Episode 数
GRAPH_MIN_ENTITIES=500
GRAPH_MIN_RELATIONS=2000

# === Dify ===
DIFY_API_BASE=http://dify:3000
DIFY_DEFAULT_API_KEY=app-xxxxxxxx  # 默认 API Key（可被工作流级别覆盖）

# === Redis ===
REDIS_URL=redis://redis:6379
GRAPH_CACHE_TTL=600
GRAPH_CONTEXT_TTL=300

# === 采集 ===
COLLECTOR_ENABLED=true
GRAPH_PIPELINE_ENABLED=true
```

---

## 八、关键决策记录

| 决策 | 结论 | 理由 |
|------|------|------|
| neomodel OGM | 不引入 | 保持技术栈一致性，直接使用 neo4j-driver + Cypher |
| Graphiti 服务模式 | 内嵌集成 | 不独立启动服务，作为应用一部分随 QuantDinger 启动 |
| 图谱查询策略 | 纯 Cypher 先行 | 数据量不足时 Graphiti 效果差，先积累数据再开启 |
| ORM 迁移策略 | 双轨并行灰度切换 | 零风险逐模块替换，每步可独立回滚 |
| PSQL 兼容层 | 逐步淘汰 | PostgresCursor 的 `?` 转 `%s` 和 SAVEPOINT 黑科技技术债需清理 |
| init.sql | 退役 | Alembic 接管所有 Schema 管理，init.sql 仅保留作为文档参考 |
