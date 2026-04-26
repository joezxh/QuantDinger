# 生成完整 init.sql + 数据字典文档

## 第一步：生成 `migrations/init.sql`

基于已读取的 29 个模型文件，按 FK 依赖顺序（无FK → qd_users → qd_indicator_codes → qd_llm_provider → ...）重写 init.sql，包含：

### 1.1 基础层（无外键依赖）
- `qd_users` — 用户主表，新增列：`phone`, `bio`, `is_email_verified`, `is_phone_verified`
- `qd_oauth_states` — OAuth CSRF 状态（无 FK）
- `qd_login_attempts` — 登录尝试记录（无 FK）
- `qd_security_logs` — 安全审计日志，字段名对齐 model：`details_json`

### 1.2 用户关联层（依赖 qd_users）
- `qd_verification_codes` — 邮箱验证码
- `qd_oauth_links` — 第三方登录关联，新增 `provider_name`, `provider_avatar`
- `qd_credits_log` — 积分变动日志
- `qd_membership_orders` — 会员订单
- `qd_usdt_orders` — USDT 收款订单
- `qd_watchlist` — 自选列表
- `qd_analysis_tasks` — AI 分析任务
- `qd_analysis_memory` — 分析记忆（新增索引：`idx_analysis_memory_symbol`）
- `qd_analysis_results` — AI 分析结果（从 init.sql 缺失）
- `qd_ai_calibration` — AI 校准参数（从 init.sql 缺失）

### 1.3 策略交易层
- `qd_strategies` — 策略基础表（from strategy.py，init.sql 缺失）
- `qd_strategies_trading` — 交易策略，`last_rebalance_at` 对齐 model（INT8 → TIMESTAMP）

### 1.4 持仓/订单层（依赖 qd_users + qd_strategies_trading）
- `qd_strategy_positions` — 策略持仓
- `qd_manual_positions` — 手动持仓
- `qd_position_alerts` — 持仓预警
- `qd_position_monitors` — 持仓监控
- `pending_orders` — 待执行订单
- `qd_quick_trades` — 快捷交易
- `qd_strategy_notifications` — 策略通知
- `qd_strategy_logs` — 策略运行日志
- `qd_strategy_trades` — 策略成交记录
- `qd_trade_orders` — 交易订单

### 1.5 市场数据层（无 FK）
- `qd_market_prices` — 市场价格（init.sql 缺失）
- `qd_market_klines` — K线数据（init.sql 缺失）

### 1.6 指标社区层（依赖 qd_users）
- `qd_indicator_codes` — 指标代码，新增 `vip_free`, `source_indicator_id`
- `qd_indicator_purchases` — 指标购买记录
- `qd_indicator_comments` — 指标评论

### 1.7 LLM 层（依赖 qd_llm_provider）
- `qd_llm_provider` — LLM 服务商（init.sql 缺失）
- `qd_llm_api_key` — LLM API 密钥（FK 列名对齐 model）
- `qd_llm_model` — LLM 模型定义
- `qd_llm_call_log` — LLM 调用日志（FK 列名对齐 model：`api_key_id`/`model_id`）

### 1.8 账务层（无 FK）
- `qd_billing_records` — 积分消费记录

### 1.9 采集/图谱层
- `qd_collection_records` — 采集记录
- `qd_graph_episodes` — 图谱事件
- `qd_graph_jobs` — 图谱任务
- `qd_graph_entity_refs` — 实体引用
- `qd_graph_relation_snapshots` — 关系快照
- `qd_graph_feature_daily` — 图谱日特征
- `qd_company_narrative_features` — 公司叙事特征
- `qd_crypto_narrative_features` — 加密货币叙事特征
- `qd_polymarket_market_features` — 预测市场特征

### 1.10 数据源元数据层
- `qd_data_source_configs` — 数据源配置
- `qd_data_source_datasets` — 数据集定义
- `qd_api_keys` — API 密钥
- `qd_query_cache` — 查询缓存

### 1.11 Dify 工作流层（依赖 qd_users）
- `qd_dify_workflows` — 工作流定义（`input_schema`/`output_schema` 为 JSONB）
- `qd_dify_workflow_logs` — 工作流执行日志

### 1.12 Polymarket 层（依赖 qd_users）
- `qd_polymarket_users` — Polymarket 用户（新增 `updated_at`）
- `qd_polymarket_markets` — 预测市场（列名对齐 polymarket.py）
- `qd_polymarket_ai_analysis` — AI 分析记录
- `qd_polymarket_opportunities` — 交易机会（从 `asset_opportunities` 改名）
- `qd_polymarket_market_features` — Polymarket 特征（已在 1.9）

### 1.13 品种种子数据
保留 `qd_market_symbols` 的 `INSERT` 种子数据

---

## 第二步：创建 Alembic 同步迁移 `002_sync_timestamp_columns.py`

已有（本次会话创建），补全已有数据库缺失的列和表。

---

## 第三步：生成数据字典 `docs/data_dictionary.md`

Markdown 表格，包含：
- 表名（中英文）、表功能说明
- 字段名、类型、是否可空、默认值、约束、外键关系
- 索引列表
- 参照模型文件路径

文档结构：
```
# QuantDinger 数据字典

## 一、用户与认证模块
## 二、积分与账务模块
## 三、策略与交易模块
## 四、市场数据模块
## 五、指标社区模块
## 六、LLM 服务模块
## 七、图谱与事件模块
## 八、数据源元数据模块
## 九、Dify 工作流模块
## 十、预测市场模块
```

---

## 关键设计决策

1. **所有 TIMESTAMP 统一用 `TIMESTAMP WITH TIME ZONE`**（对齐 `DateTime(timezone=True)`）
2. **所有 `BOOLEAN` 列默认值用 `BOOLEAN DEFAULT FALSE`**（对齐 ORM `Boolean`）
3. **JSONB 用于**：`analysis_memory.reasons/scores/indicators_snapshot`、`quick_trades.raw_result`、`llm_provider/api_key.metrics`
4. **TEXT[] 用于**：`data_source_meta.market_categories/dependencies`、`polymarket_ai_analysis.related_assets`
5. **表创建顺序**：按外键拓扑排序，无 FK 先创建
6. **所有表均 `CREATE TABLE IF NOT EXISTS`**：幂等安全