# QuantDinger 数据字典 / Data Dictionary

> 本文档描述 QuantDinger 后端 PostgreSQL 数据库中所有数据表的字段定义，按外键依赖层次组织。

---

## 层级 0：无外键依赖的表

### qd_ai_calibration — AI 校准参数表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| market | VARCHAR(50) | NOT NULL | 市场类别 |
| buy_threshold | NUMERIC(10,4) | NOT NULL | 买入阈值 |
| sell_threshold | NUMERIC(10,4) | NOT NULL | 卖出阈值 |
| min_consensus_abs_override | NUMERIC(10,4) | NOT NULL | 最小共识绝对值覆盖 |
| quality_hold_threshold | NUMERIC(10,4) | NOT NULL | 质量保留阈值 |
| validated_at | TIMESTAMP WITH TIME ZONE | | 验证时间 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |

### qd_analysis_results — AI 分析结果表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | | 用户ID |
| market | VARCHAR(50) | NOT NULL | 市场 |
| symbol | VARCHAR(100) | NOT NULL | 交易品种 |
| decision | VARCHAR(30) | | 决策结论（buy/sell/hold） |
| confidence | NUMERIC(10,4) | | 置信度 |
| summary | TEXT | | 分析摘要 |
| payload_json | TEXT | | 完整结果的JSON |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_llm_provider — LLM 服务提供商表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| name | VARCHAR(64) | NOT NULL | 提供商名称 |
| code | VARCHAR(64) | UNIQUE NOT NULL | 编码标识 |
| base_url | VARCHAR(256) | | API基础URL |
| api_type | VARCHAR(32) | DEFAULT 'openai' | API类型 |
| status | SMALLINT | DEFAULT 1 | 状态（1=启用） |
| config | JSONB | DEFAULT '{}' | 扩展配置 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_market_prices — 市场行情快照表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| market | VARCHAR(50) | NOT NULL | 市场 |
| symbol | VARCHAR(100) | NOT NULL | 品种 |
| price | NUMERIC(24,8) | NOT NULL | 当前价格 |
| change_percent | NUMERIC(10,4) | | 涨跌幅 |
| snapshot_time | TIMESTAMP WITH TIME ZONE | | 快照时间 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_market_klines — K线数据表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| market | VARCHAR(50) | NOT NULL | 市场 |
| symbol | VARCHAR(100) | NOT NULL | 品种 |
| timeframe | VARCHAR(20) | NOT NULL | 周期（1m/5m/1h等） |
| open_price | NUMERIC(24,8) | NOT NULL | 开盘价 |
| high_price | NUMERIC(24,8) | NOT NULL | 最高价 |
| low_price | NUMERIC(24,8) | NOT NULL | 最低价 |
| close_price | NUMERIC(24,8) | NOT NULL | 收盘价 |
| volume | NUMERIC(24,8) | | 成交量 |
| kline_time | TIMESTAMP WITH TIME ZONE | | K线时间 |
| payload_json | TEXT | | 扩展数据JSON |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_strategies — 策略元数据表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | NOT NULL | 所属用户 |
| name | VARCHAR(255) | NOT NULL | 策略名称 |
| description | TEXT | | 策略描述 |
| strategy_type | VARCHAR(100) | | 策略类型 |
| status | VARCHAR(30) | DEFAULT 'draft' | 状态 |
| is_public | BOOLEAN | DEFAULT FALSE | 是否公开 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

---

## 层级 1：依赖 qd_llm_provider 的LLM表

### qd_llm_api_key — LLM API密钥表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| provider_id | INTEGER | NOT NULL → qd_llm_provider(id) | 关联提供商 |
| name | VARCHAR(64) | | 密钥名称 |
| api_key_enc | TEXT | NOT NULL | AES-256-GCM加密后的密钥 |
| status | SMALLINT | DEFAULT 1 | 状态 |
| weight | INTEGER | DEFAULT 1 | 负载均衡权重 |
| owner_id | BIGINT | DEFAULT 0 | 所有者用户ID |
| is_public | SMALLINT | DEFAULT 0 | 是否公共密钥 |
| fail_count | INTEGER | DEFAULT 0 | 连续失败次数 |
| last_used_at | TIMESTAMP WITH TIME ZONE | | 最近使用时间 |
| metrics | JSONB | DEFAULT '{}' | 使用指标 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_llm_model — LLM 模型配置表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| provider_id | INTEGER | NOT NULL → qd_llm_provider(id) | 关联提供商 |
| model_name | VARCHAR(64) | NOT NULL | 模型名称（如 gpt-4o） |
| display_name | VARCHAR(64) | | 显示名称 |
| lb_strategy | VARCHAR(32) | DEFAULT 'weighted_round_robin' | 负载策略 |
| retries | INTEGER | DEFAULT 3 | 重试次数 |
| timeout | INTEGER | DEFAULT 60 | 超时秒数 |
| status | SMALLINT | DEFAULT 1 | 状态 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_llm_call_log — LLM 调用日志表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | BIGSERIAL | PRIMARY KEY | 主键（大数据量用BIGSERIAL） |
| api_key_id | INTEGER | NOT NULL → qd_llm_api_key(id) | 关联API密钥 |
| model_id | INTEGER | NOT NULL → qd_llm_model(id) | 关联模型 |
| user_id | BIGINT | | 用户ID |
| prompt_tokens | INTEGER | | 提示词Token数 |
| completion_tokens | INTEGER | | 回复Token数 |
| total_tokens | INTEGER | | 总Token数 |
| latency_ms | INTEGER | | 延迟（毫秒） |
| status_code | INTEGER | | HTTP状态码 |
| error_msg | TEXT | | 错误信息 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |

---

## 层级 2：用户认证相关表

### qd_users — 用户主表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| username | VARCHAR(50) | UNIQUE NOT NULL | 用户名 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希 |
| email | VARCHAR(100) | UNIQUE | 邮箱 |
| nickname | VARCHAR(50) | | 昵称 |
| avatar | VARCHAR(255) | DEFAULT '/avatar2.jpg' | 头像URL |
| phone | VARCHAR(50) | | 手机号 |
| bio | TEXT | | 个人简介 |
| status | VARCHAR(20) | DEFAULT 'active' | 状态 |
| role | VARCHAR(20) | DEFAULT 'user' | 角色 |
| credits | NUMERIC(20,2) | DEFAULT 0 | 积分余额 |
| vip_expires_at | TIMESTAMP WITH TIME ZONE | | VIP到期时间 |
| vip_plan | VARCHAR(20) | DEFAULT '' | VIP套餐 |
| vip_is_lifetime | BOOLEAN | DEFAULT FALSE | 是否永久会员 |
| vip_monthly_credits_last_grant | TIMESTAMP WITH TIME ZONE | | 上次发放月度积分时间 |
| email_verified | BOOLEAN | DEFAULT FALSE | 邮箱是否验证 |
| is_email_verified | BOOLEAN | DEFAULT FALSE | 是否邮箱验证 |
| is_phone_verified | BOOLEAN | DEFAULT FALSE | 是否手机验证 |
| referred_by | INTEGER | | 邀请人ID |
| notification_settings | TEXT | DEFAULT '' | 通知配置JSON |
| chart_templates | TEXT | DEFAULT '' | 图表模板JSON |
| timezone | VARCHAR(64) | DEFAULT '' | IANA时区 |
| token_version | INTEGER | DEFAULT 1 | Token版本号 |
| last_login_at | TIMESTAMP WITH TIME ZONE | | 最后登录时间 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_oauth_states — OAuth状态表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| state | VARCHAR(128) | PRIMARY KEY | CSRF状态令牌 |
| provider | VARCHAR(20) | NOT NULL | OAuth提供商（google/github） |
| redirect | TEXT | | 重定向URL |
| created_at | TIMESTAMP WITH TIME ZONE | | 创建时间 |
| expires_at | TIMESTAMP WITH TIME ZONE | NOT NULL | 过期时间 |

### qd_login_attempts — 登录尝试记录表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| identifier | VARCHAR(255) | NOT NULL | 标识（IP或用户名） |
| identifier_type | VARCHAR(32) | NOT NULL | 标识类型（ip/account） |
| success | BOOLEAN | NOT NULL DEFAULT FALSE | 是否成功 |
| ip_address | VARCHAR(64) | | IP地址 |
| user_agent | TEXT | | 用户代理 |
| attempt_time | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 尝试时间 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_security_logs — 安全审计日志表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | | 用户ID |
| action | VARCHAR(64) | NOT NULL | 操作类型 |
| ip_address | VARCHAR(64) | | IP地址 |
| user_agent | TEXT | | 用户代理 |
| details_json | TEXT | | 详细信息JSON |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

---

## 层级 3：积分/会员/验证码表（依赖 qd_users）

### qd_credits_log — 积分变动日志表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | NOT NULL → qd_users(id) | 关联用户 |
| action | VARCHAR(50) | NOT NULL | 动作类型 |
| amount | NUMERIC(20,2) | NOT NULL | 变动金额 |
| balance_after | NUMERIC(20,2) | NOT NULL | 变动后余额 |
| feature | VARCHAR(50) | DEFAULT '' | 消费功能 |
| reference_id | VARCHAR(100) | DEFAULT '' | 关联ID |
| remark | TEXT | DEFAULT '' | 备注 |
| operator_id | INTEGER | | 操作人ID |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |

### qd_membership_orders — 会员订单表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | NOT NULL → qd_users(id) | 关联用户 |
| plan | VARCHAR(20) | NOT NULL | 套餐（monthly/yearly/lifetime） |
| price_usd | NUMERIC(10,2) | DEFAULT 0 | 价格（USD） |
| status | VARCHAR(20) | DEFAULT 'paid' | 状态 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| paid_at | TIMESTAMP WITH TIME ZONE | | 支付时间 |

### qd_usdt_orders — USDT收款订单表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | NOT NULL → qd_users(id) | 关联用户 |
| plan | VARCHAR(20) | NOT NULL | 套餐类型 |
| chain | VARCHAR(20) | NOT NULL DEFAULT 'TRC20' | 区块链 |
| amount_usdt | NUMERIC(20,6) | NOT NULL | USDT金额 |
| address_index | INTEGER | NOT NULL DEFAULT 0 | HD派生索引 |
| address | VARCHAR(80) | NOT NULL DEFAULT '' | 收款地址 |
| status | VARCHAR(20) | NOT NULL DEFAULT 'pending' | 状态 |
| tx_hash | VARCHAR(120) | DEFAULT '' | 交易哈希 |
| paid_at | TIMESTAMP WITH TIME ZONE | | 支付时间 |
| confirmed_at | TIMESTAMP WITH TIME ZONE | | 确认时间 |
| expires_at | TIMESTAMP WITH TIME ZONE | | 过期时间 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_verification_codes — 验证码表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| email | VARCHAR(100) | NOT NULL | 邮箱 |
| code | VARCHAR(10) | NOT NULL | 验证码 |
| type | VARCHAR(20) | NOT NULL | 类型 |
| expires_at | TIMESTAMP WITH TIME ZONE | NOT NULL | 过期时间 |
| used_at | TIMESTAMP WITH TIME ZONE | | 使用时间 |
| ip_address | VARCHAR(45) | | IP地址 |
| attempts | INTEGER | DEFAULT 0 | 尝试次数 |
| last_attempt_at | TIMESTAMP WITH TIME ZONE | | 最后尝试时间 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |

### qd_oauth_links — 第三方账号关联表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | → qd_users(id) | 关联用户 |
| provider | VARCHAR(20) | NOT NULL | OAuth提供商 |
| provider_user_id | VARCHAR(100) | NOT NULL UNIQUE | 第三方用户ID |
| provider_email | VARCHAR(100) | | 第三方邮箱 |
| provider_name | VARCHAR(100) | | 第三方用户名 |
| provider_avatar | VARCHAR(255) | | 第三方头像 |
| access_token | TEXT | | Access Token |
| refresh_token | TEXT | | Refresh Token |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_billing_records — 计费记录表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | NOT NULL | 用户ID |
| feature | VARCHAR(100) | NOT NULL | 功能名称 |
| amount | NUMERIC(18,4) | NOT NULL | 扣费金额 |
| balance_before | NUMERIC(18,4) | | 扣费前余额 |
| balance_after | NUMERIC(18,4) | | 扣费后余额 |
| reference_id | VARCHAR(100) | | 关联业务ID |
| occurred_at | TIMESTAMP WITH TIME ZONE | | 发生时间 |
| payload_json | TEXT | | 扩展数据 |
| billing_type | VARCHAR(50) | | 计费类型 |
| status | VARCHAR(30) | | 状态 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

---

## 层级 4：交易策略表（依赖 qd_users）

### qd_strategies_trading — 核心交易策略表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | NOT NULL DEFAULT 1 → qd_users(id) | 所属用户 |
| strategy_name | VARCHAR(255) | NOT NULL | 策略名称 |
| strategy_type | VARCHAR(50) | DEFAULT 'IndicatorStrategy' | 策略类型 |
| market_category | VARCHAR(50) | DEFAULT 'Crypto' | 市场分类 |
| execution_mode | VARCHAR(20) | DEFAULT 'signal' | 执行模式 |
| notification_config | TEXT | DEFAULT '' | 通知配置 |
| status | VARCHAR(20) | DEFAULT 'stopped' | 状态 |
| symbol | VARCHAR(50) | | 交易品种 |
| timeframe | VARCHAR(10) | | 周期 |
| initial_capital | NUMERIC(20,8) | DEFAULT 1000 | 初始资金 |
| leverage | INTEGER | DEFAULT 1 | 杠杆倍数 |
| market_type | VARCHAR(20) | DEFAULT 'swap' | 市场类型 |
| exchange_config | TEXT | | 交易所配置 |
| indicator_config | TEXT | | 指标配置 |
| trading_config | TEXT | | 交易配置 |
| ai_model_config | TEXT | | AI模型配置 |
| decide_interval | INTEGER | DEFAULT 300 | 决策间隔（秒） |
| strategy_group_id | VARCHAR(100) | DEFAULT '' | 策略组ID |
| group_base_name | VARCHAR(255) | DEFAULT '' | 策略组基础名称 |
| strategy_mode | VARCHAR(20) | DEFAULT 'signal' | 策略模式 |
| strategy_code | TEXT | DEFAULT '' | 策略代码（脚本策略） |
| last_rebalance_at | TIMESTAMP WITH TIME ZONE | | 最后调仓时间 |
| strategy_id | INTEGER | | 关联策略ID |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_strategy_positions — 策略持仓表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | NOT NULL → qd_users(id) | 所属用户 |
| strategy_id | INTEGER | → qd_strategies_trading(id) | 关联策略 |
| symbol | VARCHAR(50) | | 交易品种 |
| side | VARCHAR(10) | | 方向（long/short） |
| size | NUMERIC(20,8) | | 持仓数量 |
| entry_price | NUMERIC(20,8) | | 入场价格 |
| current_price | NUMERIC(20,8) | | 当前价格 |
| highest_price | NUMERIC(20,8) | DEFAULT 0 | 最高价 |
| lowest_price | NUMERIC(20,8) | DEFAULT 0 | 最低价 |
| unrealized_pnl | NUMERIC(20,8) | DEFAULT 0 | 未实现盈亏 |
| pnl_percent | NUMERIC(10,4) | DEFAULT 0 | 盈亏百分比 |
| equity | NUMERIC(20,8) | DEFAULT 0 | 权益 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_strategy_trades — 策略交易记录表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | NOT NULL → qd_users(id) | 所属用户 |
| strategy_id | INTEGER | → qd_strategies_trading(id) | 关联策略 |
| symbol | VARCHAR(50) | | 交易品种 |
| type | VARCHAR(30) | | 交易类型 |
| price | NUMERIC(20,8) | | 成交价格 |
| amount | NUMERIC(20,8) | | 成交数量 |
| value | NUMERIC(20,8) | | 成交金额 |
| commission | NUMERIC(20,8) | DEFAULT 0 | 手续费 |
| commission_ccy | VARCHAR(20) | DEFAULT '' | 手续费币种 |
| profit | NUMERIC(20,8) | DEFAULT 0 | 盈亏 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |

### pending_orders — 待执行订单队列

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | NOT NULL → qd_users(id) | 所属用户 |
| strategy_id | INTEGER | → qd_strategies_trading(id) | 关联策略 |
| symbol | VARCHAR(50) | NOT NULL | 交易品种 |
| signal_type | VARCHAR(30) | NOT NULL | 信号类型 |
| signal_ts | BIGINT | | 信号时间戳 |
| market_type | VARCHAR(20) | DEFAULT 'swap' | 市场类型 |
| order_type | VARCHAR(20) | DEFAULT 'market' | 订单类型 |
| amount | NUMERIC(20,8) | DEFAULT 0 | 数量 |
| price | NUMERIC(20,8) | DEFAULT 0 | 价格 |
| execution_mode | VARCHAR(20) | DEFAULT 'signal' | 执行模式 |
| status | VARCHAR(20) | DEFAULT 'pending' | 状态 |
| priority | INTEGER | DEFAULT 0 | 优先级 |
| attempts | INTEGER | DEFAULT 0 | 已尝试次数 |
| max_attempts | INTEGER | DEFAULT 10 | 最大尝试次数 |
| last_error | TEXT | DEFAULT '' | 最后错误信息 |
| payload_json | TEXT | DEFAULT '' | 附加数据 |
| dispatch_note | TEXT | DEFAULT '' | 分发备注 |
| exchange_id | VARCHAR(50) | DEFAULT '' | 交易所ID |
| exchange_order_id | VARCHAR(100) | DEFAULT '' | 交易所订单ID |
| exchange_response_json | TEXT | DEFAULT '' | 交易所响应 |
| filled | NUMERIC(20,8) | DEFAULT 0 | 已成交数量 |
| avg_price | NUMERIC(20,8) | DEFAULT 0 | 平均成交价 |
| executed_at | TIMESTAMP WITH TIME ZONE | | 成交时间 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |
| processed_at | TIMESTAMP WITH TIME ZONE | | 处理时间 |
| sent_at | TIMESTAMP WITH TIME ZONE | | 发送时间 |

### qd_strategy_notifications — 策略通知表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | NOT NULL → qd_users(id) | 所属用户 |
| strategy_id | INTEGER | → qd_strategies_trading(id) | 关联策略 |
| symbol | VARCHAR(50) | DEFAULT '' | 交易品种 |
| signal_type | VARCHAR(30) | DEFAULT '' | 信号类型 |
| channels | VARCHAR(255) | DEFAULT '' | 通知渠道 |
| title | VARCHAR(255) | DEFAULT '' | 通知标题 |
| message | TEXT | DEFAULT '' | 通知内容 |
| payload_json | TEXT | DEFAULT '' | 附加数据 |
| is_read | INTEGER | DEFAULT 0 | 是否已读 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |

### qd_strategy_logs — 策略运行日志表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| strategy_id | INTEGER | NOT NULL → qd_strategies_trading(id) | 关联策略 |
| level | VARCHAR(20) | DEFAULT 'info' | 日志级别 |
| message | TEXT | NOT NULL | 日志内容 |
| timestamp | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 时间戳 |

### qd_trade_orders — 交易订单记录表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | | 用户ID |
| strategy_id | INTEGER | | 策略ID |
| market | VARCHAR(50) | NOT NULL | 市场 |
| symbol | VARCHAR(100) | NOT NULL | 品种 |
| side | VARCHAR(20) | NOT NULL | 方向 |
| order_type | VARCHAR(30) | | 订单类型 |
| quantity | NUMERIC(24,8) | | 数量 |
| price | NUMERIC(24,8) | | 价格 |
| status | VARCHAR(30) | | 状态 |
| submitted_at | TIMESTAMP WITH TIME ZONE | | 提交时间 |
| payload_json | TEXT | | 扩展数据 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

---

## 层级 5：手动持仓/警报表（依赖 qd_users）

### qd_manual_positions — 手动持仓表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | NOT NULL → qd_users(id) | 所属用户 |
| market | VARCHAR(50) | NOT NULL | 市场 |
| symbol | VARCHAR(50) | NOT NULL | 交易品种 |
| name | VARCHAR(100) | DEFAULT '' | 名称 |
| side | VARCHAR(10) | DEFAULT 'long' | 方向 |
| quantity | NUMERIC(20,8) | NOT NULL DEFAULT 0 | 数量 |
| entry_price | NUMERIC(20,8) | NOT NULL DEFAULT 0 | 入场价格 |
| entry_time | BIGINT | | 入场时间戳 |
| notes | TEXT | DEFAULT '' | 备注 |
| tags | TEXT | DEFAULT '' | 标签 |
| group_name | VARCHAR(100) | DEFAULT '' | 持仓组名称 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_position_alerts — 持仓警报表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | NOT NULL → qd_users(id) | 所属用户 |
| position_id | INTEGER | | 关联持仓ID |
| market | VARCHAR(50) | DEFAULT '' | 市场 |
| symbol | VARCHAR(50) | DEFAULT '' | 交易品种 |
| alert_type | VARCHAR(30) | NOT NULL | 警报类型 |
| threshold | NUMERIC(20,8) | NOT NULL DEFAULT 0 | 触发阈值 |
| notification_config | TEXT | DEFAULT '' | 通知配置 |
| is_active | INTEGER | DEFAULT 1 | 是否激活 |
| is_triggered | INTEGER | DEFAULT 0 | 是否已触发 |
| last_triggered_at | TIMESTAMP WITH TIME ZONE | | 最后触发时间 |
| trigger_count | INTEGER | DEFAULT 0 | 触发次数 |
| repeat_interval | INTEGER | DEFAULT 0 | 重复间隔（秒） |
| notes | TEXT | DEFAULT '' | 备注 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_position_monitors — 持仓监控表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | NOT NULL → qd_users(id) | 所属用户 |
| name | VARCHAR(100) | DEFAULT '' | 监控名称 |
| position_ids | TEXT | DEFAULT '' | 持仓ID列表JSON |
| monitor_type | VARCHAR(20) | DEFAULT 'ai' | 监控类型 |
| config | TEXT | DEFAULT '' | 监控配置 |
| notification_config | TEXT | DEFAULT '' | 通知配置 |
| is_active | INTEGER | DEFAULT 1 | 是否激活 |
| last_run_at | TIMESTAMP WITH TIME ZONE | | 最后运行时间 |
| next_run_at | TIMESTAMP WITH TIME ZONE | | 下次运行时间 |
| last_result | TEXT | DEFAULT '' | 最后运行结果 |
| run_count | INTEGER | DEFAULT 0 | 运行次数 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_exchange_credentials — 交易所凭证表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | NOT NULL → qd_users(id) | 所属用户 |
| name | VARCHAR(100) | DEFAULT '' | 凭证名称 |
| exchange_id | VARCHAR(50) | NOT NULL | 交易所ID |
| api_key_hint | VARCHAR(50) | DEFAULT '' | API密钥提示 |
| encrypted_config | TEXT | NOT NULL | 加密后的配置 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

---

## 层级 6：指标/自选股/分析任务表（依赖 qd_users）

### qd_indicator_codes — 指标代码表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | DEFAULT 1 → qd_users(id) | 所属用户 |
| is_buy | INTEGER | DEFAULT 0 | 是否买入指标 |
| end_time | BIGINT | DEFAULT 1 | 结束时间 |
| name | VARCHAR(255) | NOT NULL DEFAULT '' | 指标名称 |
| code | TEXT | | 指标代码 |
| description | TEXT | DEFAULT '' | 指标描述 |
| publish_to_community | INTEGER | DEFAULT 0 | 是否发布到社区 |
| pricing_type | VARCHAR(20) | NOT NULL DEFAULT 'free' | 定价类型 |
| price | NUMERIC(10,2) | NOT NULL DEFAULT 0 | 价格 |
| is_encrypted | INTEGER | DEFAULT 0 | 是否加密 |
| preview_image | VARCHAR(500) | | 预览图URL |
| vip_free | BOOLEAN | DEFAULT FALSE | VIP免费 |
| createtime | INTEGER | | 创建时间戳 |
| updatetime | INTEGER | | 更新时间戳 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |
| purchase_count | INTEGER | DEFAULT 0 | 购买次数 |
| avg_rating | NUMERIC(3,2) | DEFAULT 0 | 平均评分 |
| rating_count | INTEGER | DEFAULT 0 | 评分次数 |
| view_count | INTEGER | DEFAULT 0 | 浏览次数 |
| review_status | VARCHAR(20) | DEFAULT 'approved' | 审核状态 |
| review_note | TEXT | DEFAULT '' | 审核备注 |
| reviewed_at | TIMESTAMP WITH TIME ZONE | | 审核时间 |
| reviewed_by | INTEGER | | 审核人ID |
| source_indicator_id | INTEGER | | 源指标ID（用于同步） |

### qd_indicator_purchases — 指标购买记录表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| indicator_id | INTEGER | NOT NULL → qd_indicator_codes(id) | 指标ID |
| buyer_id | INTEGER | NOT NULL → qd_users(id) | 购买者ID |
| seller_id | INTEGER | NOT NULL → qd_users(id) | 出售者ID |
| price | NUMERIC(10,2) | NOT NULL DEFAULT 0 | 购买价格 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |

### qd_indicator_comments — 指标评论表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| indicator_id | INTEGER | NOT NULL → qd_indicator_codes(id) | 指标ID |
| user_id | INTEGER | NOT NULL → qd_users(id) | 用户ID |
| rating | INTEGER | DEFAULT 5 CHECK(rating>=1 AND rating<=5) | 评分 |
| content | TEXT | DEFAULT '' | 评论内容 |
| parent_id | INTEGER | → qd_indicator_comments(id) | 父评论ID |
| is_deleted | INTEGER | DEFAULT 0 | 是否已删除 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_watchlist — 自选股表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | DEFAULT 1 → qd_users(id) | 所属用户 |
| market | VARCHAR(50) | NOT NULL | 市场 |
| symbol | VARCHAR(50) | NOT NULL | 交易品种 |
| name | VARCHAR(100) | DEFAULT '' | 名称 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_analysis_tasks — AI分析任务表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | DEFAULT 1 → qd_users(id) | 所属用户 |
| market | VARCHAR(50) | NOT NULL | 市场 |
| symbol | VARCHAR(50) | NOT NULL | 交易品种 |
| model | VARCHAR(100) | DEFAULT '' | 使用模型 |
| language | VARCHAR(20) | DEFAULT 'en-US' | 语言 |
| status | VARCHAR(20) | DEFAULT 'completed' | 状态 |
| result_json | TEXT | DEFAULT '' | 分析结果JSON |
| error_message | TEXT | DEFAULT '' | 错误信息 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| completed_at | TIMESTAMP WITH TIME ZONE | | 完成时间 |

### qd_market_symbols — 市场品种表（含种子数据）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| market | VARCHAR(50) | NOT NULL | 市场 |
| symbol | VARCHAR(50) | NOT NULL | 交易品种 |
| name | VARCHAR(255) | DEFAULT '' | 品种名称 |
| exchange | VARCHAR(50) | DEFAULT '' | 交易所 |
| currency | VARCHAR(10) | DEFAULT '' | 计价货币 |
| is_active | INTEGER | DEFAULT 1 | 是否启用 |
| is_hot | INTEGER | DEFAULT 0 | 是否热门 |
| sort_order | INTEGER | DEFAULT 0 | 排序 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |

### qd_analysis_memory — AI分析记忆表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | | 用户ID |
| market | VARCHAR(50) | NOT NULL | 市场 |
| symbol | VARCHAR(50) | NOT NULL | 交易品种 |
| decision | VARCHAR(10) | NOT NULL | 决策（buy/sell/hold） |
| confidence | INTEGER | DEFAULT 50 | 置信度 |
| price_at_analysis | NUMERIC(24,8) | | 分析时价格 |
| summary | TEXT | | 摘要 |
| reasons | JSONB | | 决策理由 |
| scores | JSONB | | 各维度评分 |
| indicators_snapshot | JSONB | | 指标快照 |
| raw_result | JSONB | | 完整原始结果 |
| consensus_score | NUMERIC(24,8) | | 共识评分 |
| consensus_abs | NUMERIC(24,8) | | 共识绝对值 |
| agreement_ratio | NUMERIC(10,6) | | 一致率 |
| quality_multiplier | NUMERIC(10,6) | | 质量倍数 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| validated_at | TIMESTAMP WITH TIME ZONE | | 验证时间 |
| actual_outcome | VARCHAR(20) | | 实际结果 |
| actual_return_pct | NUMERIC(10,4) | | 实际收益率 |
| was_correct | BOOLEAN | | 是否正确 |
| user_feedback | VARCHAR(20) | | 用户反馈 |
| feedback_at | TIMESTAMP WITH TIME ZONE | | 反馈时间 |

### qd_backtest_runs — 回测结果表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | NOT NULL → qd_users(id) | 所属用户 |
| strategy_id | INTEGER | | 关联策略ID |
| indicator_id | INTEGER | | 关联指标ID |
| strategy_name | VARCHAR(255) | DEFAULT '' | 策略名称 |
| run_type | VARCHAR(50) | DEFAULT 'indicator' | 回测类型 |
| engine_version | VARCHAR(50) | DEFAULT '' | 引擎版本 |
| code_hash | VARCHAR(128) | DEFAULT '' | 代码哈希 |
| config_snapshot | TEXT | DEFAULT '' | 配置快照 |
| total_return | NUMERIC(18,6) | | 总收益率 |
| win_rate | NUMERIC(10,4) | | 胜率 |
| max_drawdown | NUMERIC(10,4) | | 最大回撤 |
| payload_json | TEXT | DEFAULT '' | 扩展数据 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_backtest_trades — 回测交易记录表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| run_id | INTEGER | NOT NULL | 关联回测ID |
| user_id | INTEGER | NOT NULL → qd_users(id) | 所属用户 |
| strategy_id | INTEGER | | 关联策略ID |
| trade_index | INTEGER | DEFAULT 0 | 交易序号 |
| trade_time | VARCHAR(64) | DEFAULT '' | 交易时间 |
| trade_type | VARCHAR(64) | DEFAULT '' | 交易类型 |
| side | VARCHAR(32) | DEFAULT '' | 方向 |
| price | NUMERIC(24,8) | DEFAULT 0 | 成交价格 |
| amount | NUMERIC(24,8) | DEFAULT 0 | 成交数量 |
| profit | NUMERIC(24,8) | DEFAULT 0 | 盈亏 |
| balance | NUMERIC(24,8) | DEFAULT 0 | 余额 |
| reason | VARCHAR(64) | DEFAULT '' | 原因 |
| payload_json | TEXT | DEFAULT '' | 扩展数据 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_backtest_equity_points — 回测权益曲线表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| run_id | INTEGER | NOT NULL | 关联回测ID |
| point_index | INTEGER | DEFAULT 0 | 数据点序号 |
| point_time | VARCHAR(64) | DEFAULT '' | 时间 |
| point_value | NUMERIC(24,8) | DEFAULT 0 | 权益值 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_quick_trades — 快捷交易记录表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| user_id | INTEGER | NOT NULL → qd_users(id) | 所属用户 |
| credential_id | INTEGER | DEFAULT 0 | 凭证ID |
| exchange_id | VARCHAR(40) | NOT NULL DEFAULT '' | 交易所ID |
| symbol | VARCHAR(60) | NOT NULL DEFAULT '' | 交易品种 |
| side | VARCHAR(10) | NOT NULL DEFAULT '' | 方向（buy/sell） |
| order_type | VARCHAR(20) | NOT NULL DEFAULT 'market' | 订单类型 |
| amount | NUMERIC(24,8) | DEFAULT 0 | 数量 |
| price | NUMERIC(24,8) | DEFAULT 0 | 价格 |
| leverage | INTEGER | DEFAULT 1 | 杠杆 |
| market_type | VARCHAR(20) | DEFAULT 'swap' | 市场类型 |
| tp_price | NUMERIC(24,8) | DEFAULT 0 | 止盈价格 |
| sl_price | NUMERIC(24,8) | DEFAULT 0 | 止损价格 |
| status | VARCHAR(20) | DEFAULT 'submitted' | 状态 |
| exchange_order_id | VARCHAR(120) | DEFAULT '' | 交易所订单ID |
| filled_amount | NUMERIC(24,8) | DEFAULT 0 | 已成交数量 |
| avg_fill_price | NUMERIC(24,8) | DEFAULT 0 | 平均成交价 |
| error_msg | TEXT | DEFAULT '' | 错误信息 |
| source | VARCHAR(40) | DEFAULT 'manual' | 来源 |
| raw_result | JSONB | | 交易所原始响应 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |

---

## 层级 7：图谱数据表

### qd_collection_records — 数据采集记录表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| source | VARCHAR(50) | | 数据来源 |
| data_type | VARCHAR(50) | | 数据类型 |
| market | VARCHAR(50) | | 市场 |
| symbol | VARCHAR(100) | | 交易品种 |
| content_hash | VARCHAR(64) | NOT NULL UNIQUE | 内容哈希 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_graph_episodes — 知识图谱事件表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| episode_type | VARCHAR(50) | NOT NULL | 事件类型 |
| market_domain | VARCHAR(50) | NOT NULL | 市场领域 |
| title | VARCHAR(255) | | 标题 |
| source | VARCHAR(100) | NOT NULL | 来源 |
| source_ref | VARCHAR(255) | | 来源引用 |
| dedup_key | VARCHAR(128) | UNIQUE | 去重键 |
| importance_score | NUMERIC(6,4) | DEFAULT 0.5 | 重要性评分 |
| event_time | TIMESTAMP WITH TIME ZONE | | 事件时间 |
| observed_time | TIMESTAMP WITH TIME ZONE | NOT NULL | 观测时间 |
| status | VARCHAR(30) | DEFAULT 'pending' | 状态 |
| error_message | TEXT | | 错误信息 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_graph_jobs — 知识图谱任务表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| episode_id | INTEGER | | 关联事件ID |
| job_type | VARCHAR(50) | NOT NULL | 任务类型 |
| status | VARCHAR(30) | DEFAULT 'pending' | 状态 |
| retry_count | INTEGER | DEFAULT 0 | 重试次数 |
| error_message | TEXT | | 错误信息 |
| started_at | TIMESTAMP WITH TIME ZONE | | 开始时间 |
| finished_at | TIMESTAMP WITH TIME ZONE | | 结束时间 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_graph_entity_refs — 图谱实体引用表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| entity_uid | VARCHAR(255) | NOT NULL | 实体UID |
| entity_type | VARCHAR(50) | NOT NULL | 实体类型 |
| source_table | VARCHAR(100) | NOT NULL | 源表名 |
| source_pk | VARCHAR(100) | NOT NULL | 源主键 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_graph_relation_snapshots — 图谱关系快照表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| relation_type | VARCHAR(100) | NOT NULL | 关系类型 |
| from_uid | VARCHAR(255) | NOT NULL | 起始实体UID |
| to_uid | VARCHAR(255) | NOT NULL | 目标实体UID |
| source_ref | VARCHAR(255) | | 来源引用 |
| confidence | NUMERIC(6,4) | | 置信度 |
| t_valid | TIMESTAMP WITH TIME ZONE | | 有效时间 |
| t_invalid | TIMESTAMP WITH TIME ZONE | | 失效时间 |
| payload_json | TEXT | | 扩展数据 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_graph_feature_daily — 图谱特征日表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| trade_date | DATE | NOT NULL | 交易日期 |
| market | VARCHAR(50) | NOT NULL | 市场 |
| symbol | VARCHAR(100) | NOT NULL | 交易品种 |
| feature_name | VARCHAR(100) | NOT NULL | 特征名称 |
| feature_value | NUMERIC(24,8) | NOT NULL | 特征值 |
| source | VARCHAR(50) | DEFAULT 'graph' | 数据来源 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_company_narrative_features — 公司叙事特征表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| trade_date | DATE | NOT NULL | 交易日期 |
| ticker | VARCHAR(20) | NOT NULL | 股票代码 |
| narrative_name | VARCHAR(100) | NOT NULL | 叙事名称 |
| narrative_score | NUMERIC(10,4) | NOT NULL | 叙事评分 |
| source | VARCHAR(50) | DEFAULT 'graph' | 数据来源 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_crypto_narrative_features — 加密货币叙事特征表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| trade_date | DATE | NOT NULL | 交易日期 |
| symbol | VARCHAR(50) | NOT NULL | 加密货币符号 |
| narrative_name | VARCHAR(100) | NOT NULL | 叙事名称 |
| narrative_score | NUMERIC(10,4) | NOT NULL | 叙事评分 |
| source | VARCHAR(50) | DEFAULT 'graph' | 数据来源 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_polymarket_market_features — Polymarket市场特征表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| trade_date | DATE | NOT NULL | 交易日期 |
| market_id | VARCHAR(255) | NOT NULL | 市场ID |
| feature_name | VARCHAR(100) | NOT NULL | 特征名称 |
| feature_value | NUMERIC(24,8) | NOT NULL | 特征值 |
| source | VARCHAR(50) | DEFAULT 'graph' | 数据来源 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

---

## 层级 8：Dify工作流表

### qd_dify_workflows — Dify工作流配置表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| code | VARCHAR(50) | UNIQUE NOT NULL | 工作流编码 |
| name | VARCHAR(100) | NOT NULL | 工作流名称 |
| description | TEXT | DEFAULT '' | 描述 |
| workflow_type | VARCHAR(50) | NOT NULL DEFAULT 'chat' | 工作流类型 |
| endpoint | VARCHAR(255) | NOT NULL | API端点 |
| api_key | VARCHAR(255) | NOT NULL | API密钥 |
| input_schema | JSONB | NOT NULL DEFAULT '{}' | 输入Schema |
| output_schema | JSONB | NOT NULL DEFAULT '{}' | 输出Schema |
| is_active | BOOLEAN | NOT NULL DEFAULT TRUE | 是否启用 |
| max_retries | INTEGER | NOT NULL DEFAULT 3 | 最大重试次数 |
| timeout_seconds | INTEGER | NOT NULL DEFAULT 120 | 超时秒数 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_dify_workflow_logs — Dify工作流执行日志表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| workflow_id | INTEGER | NOT NULL → qd_dify_workflows(id) | 关联工作流 |
| user_id | INTEGER | → qd_users(id) | 用户ID |
| input_data | JSONB | | 输入数据 |
| output_data | JSONB | | 输出数据 |
| status | VARCHAR(20) | NOT NULL DEFAULT 'pending' | 状态 |
| call_mode | VARCHAR(10) | NOT NULL DEFAULT 'batch' | 调用模式 |
| tokens_used | INTEGER | NOT NULL DEFAULT 0 | Token消耗 |
| latency_ms | INTEGER | NOT NULL DEFAULT 0 | 延迟（毫秒） |
| error_message | TEXT | | 错误信息 |
| started_at | TIMESTAMP WITH TIME ZONE | | 开始时间 |
| finished_at | TIMESTAMP WITH TIME ZONE | | 结束时间 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

---

## 层级 9：数据源元数据表

### qd_data_source_configs — 数据源配置表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| source_code | VARCHAR(80) | UNIQUE NOT NULL | 数据源编码 |
| source_name | VARCHAR(150) | NOT NULL | 数据源名称 |
| layer | VARCHAR(30) | NOT NULL DEFAULT 'data_source' | 层级 |
| market_categories | TEXT[] | | 支持的市场类别 |
| enabled | BOOLEAN | NOT NULL DEFAULT TRUE | 是否启用 |
| load_balance_strategy | VARCHAR(30) | NOT NULL DEFAULT 'round_robin' | 负载策略 |
| config_json | JSONB | | 访问参数配置 |
| dependencies | TEXT[] | | 依赖的数据源 |
| notes | TEXT | | 备注 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_data_source_datasets — 数据集元数据表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| source_id | INTEGER | NOT NULL → qd_data_source_configs(id) | 关联数据源 |
| dataset_code | VARCHAR(80) | UNIQUE NOT NULL | 数据集编码 |
| dataset_name | VARCHAR(150) | NOT NULL | 数据集名称 |
| description | TEXT | | 描述 |
| function_name | VARCHAR(100) | | 函数名称 |
| return_type | VARCHAR(30) | NOT NULL DEFAULT 'list[dict]' | 返回类型 |
| fields_schema | JSONB | | 字段Schema |
| sample_output | JSONB | | 示例输出 |
| coverage_text | TEXT | | 覆盖范围描述 |
| source_file_ref | VARCHAR(255) | | 源代码引用 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_api_keys — API密钥管理表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| source_config_id | INTEGER | NOT NULL → qd_data_source_configs(id) | 关联数据源 |
| key_type | VARCHAR(20) | NOT NULL DEFAULT 'public' | 密钥类型（public/private） |
| user_id | INTEGER | → qd_users(id) | 私有密钥所有者 |
| key_alias | VARCHAR(100) | | 密钥别名 |
| encrypted_key_value | TEXT | NOT NULL | AES加密的密钥值 |
| key_hint | VARCHAR(50) | | 显示提示 |
| status | VARCHAR(20) | NOT NULL DEFAULT 'active' | 状态 |
| weight | INTEGER | NOT NULL DEFAULT 1 | 负载权重 |
| consecutive_errors | INTEGER | NOT NULL DEFAULT 0 | 连续错误次数 |
| last_error_at | TIMESTAMP WITH TIME ZONE | | 最后错误时间 |
| max_consecutive_errors | INTEGER | NOT NULL DEFAULT 5 | 最大连续错误数 |
| daily_call_limit | INTEGER | NOT NULL DEFAULT 0 | 日调用限额 |
| current_daily_calls | INTEGER | NOT NULL DEFAULT 0 | 当日已调用次数 |
| last_reset_at | TIMESTAMP WITH TIME ZONE | | 最后重置时间 |
| total_calls | INTEGER | NOT NULL DEFAULT 0 | 总调用次数 |
| created_by | INTEGER | | 创建者ID |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_query_cache — 查询结果缓存表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| cache_key | VARCHAR(64) | UNIQUE NOT NULL | 缓存键（SHA256哈希） |
| dataset_id | INTEGER | → qd_data_source_datasets(id) | 关联数据集 |
| source_code | VARCHAR(80) | NOT NULL | 数据源编码 |
| query_params | JSONB | NOT NULL | 查询参数 |
| result_data | JSONB | | 结果数据 |
| result_size_bytes | INTEGER | | 结果大小（字节） |
| status | VARCHAR(20) | NOT NULL DEFAULT 'pending' | 状态 |
| error_message | TEXT | | 错误信息 |
| request_count | INTEGER | NOT NULL DEFAULT 1 | 请求次数 |
| ttl_seconds | INTEGER | NOT NULL DEFAULT 300 | TTL（秒） |
| expires_at | TIMESTAMP WITH TIME ZONE | | 过期时间 |
| first_requested_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 首次请求时间 |
| last_requested_at | TIMESTAMP WITH TIME ZONE | | 最后请求时间 |
| completed_at | TIMESTAMP WITH TIME ZONE | | 完成时间 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

---

## 层级 10：Polymarket预测市场表

### qd_polymarket_users — Polymarket用户表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| address | VARCHAR(255) | UNIQUE NOT NULL | 钱包地址 |
| display_name | VARCHAR(255) | | 显示名称 |
| win_rate | NUMERIC(10,4) | | 胜率 |
| volume | NUMERIC(24,8) | | 交易量 |
| payload_json | TEXT | | 扩展数据 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_polymarket_markets — Polymarket市场表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| market_id | VARCHAR(255) | UNIQUE NOT NULL | 市场ID |
| question | TEXT | NOT NULL | 市场问题 |
| current_probability | NUMERIC(10,4) | | 当前概率 |
| end_date_iso | VARCHAR(64) | | 结束日期ISO |
| active | BOOLEAN | DEFAULT TRUE | 是否活跃 |
| category | VARCHAR(100) | | 分类 |
| last_synced_at | TIMESTAMP WITH TIME ZONE | | 最后同步时间 |
| payload_json | TEXT | | 扩展数据 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

### qd_polymarket_ai_analysis — Polymarket AI分析表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| market_id | VARCHAR(255) | NOT NULL | 市场ID |
| user_id | INTEGER | | 用户ID |
| ai_predicted_probability | NUMERIC(10,4) | | AI预测概率 |
| market_probability | NUMERIC(10,4) | | 市场概率 |
| divergence | NUMERIC(10,4) | | 偏差 |
| recommendation | VARCHAR(32) | | 建议 |
| confidence_score | NUMERIC(10,4) | | 置信度评分 |
| opportunity_score | NUMERIC(10,4) | | 机会评分 |
| reasoning | TEXT | | 推理理由 |
| key_factors | JSONB | | 关键因素 |
| related_assets | TEXT[] | | 相关资产 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |

### qd_polymarket_opportunities — Polymarket机会表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 主键 |
| market_id | VARCHAR(255) | NOT NULL | 市场ID |
| asset | VARCHAR(100) | NOT NULL | 关联资产 |
| market | VARCHAR(50) | | 市场 |
| signal | VARCHAR(32) | | 信号 |
| confidence | NUMERIC(10,4) | | 置信度 |
| reasoning | TEXT | | 推理理由 |
| payload_json | TEXT | | 扩展数据 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |

---

## 索引汇总

| 索引名 | 表名 | 列 | 类型 |
|--------|------|-----|------|
| idx_users_referred_by | qd_users | referred_by | 普通 |
| idx_users_email | qd_users | email | 普通 |
| idx_users_status | qd_users | status | 普通 |
| idx_oauth_states_expires | qd_oauth_states | expires_at | 普通 |
| idx_login_attempts_identifier | qd_login_attempts | identifier, identifier_type | 普通 |
| idx_login_attempts_time | qd_login_attempts | attempt_time | 普通 |
| idx_security_logs_user_id | qd_security_logs | user_id | 普通 |
| idx_security_logs_action | qd_security_logs | action | 普通 |
| idx_security_logs_created_at | qd_security_logs | created_at | 普通 |
| idx_credits_log_user_id | qd_credits_log | user_id | 普通 |
| idx_credits_log_action | qd_credits_log | action | 普通 |
| idx_credits_log_created_at | qd_credits_log | created_at | 普通 |
| idx_membership_orders_user_id | qd_membership_orders | user_id | 普通 |
| idx_usdt_orders_address_unique | qd_usdt_orders | chain, address | UNIQUE |
| idx_usdt_orders_user_id | qd_usdt_orders | user_id | 普通 |
| idx_usdt_orders_status | qd_usdt_orders | status | 普通 |
| idx_verification_codes_email | qd_verification_codes | email | 普通 |
| idx_verification_codes_type | qd_verification_codes | type | 普通 |
| idx_verification_codes_expires | qd_verification_codes | expires_at | 普通 |
| idx_oauth_links_user_id | qd_oauth_links | user_id | 普通 |
| idx_oauth_links_provider | qd_oauth_links | provider | 普通 |
| idx_billing_records_user | qd_billing_records | user_id | 普通 |
| idx_billing_records_feature | qd_billing_records | feature | 普通 |
| idx_strategies_user_id | qd_strategies_trading | user_id | 普通 |
| idx_strategies_status | qd_strategies_trading | status | 普通 |
| idx_strategies_group_id | qd_strategies_trading | strategy_group_id | 普通 |
| idx_positions_user_id | qd_strategy_positions | user_id | 普通 |
| idx_positions_strategy_id | qd_strategy_positions | strategy_id | 普通 |
| idx_trades_user_id | qd_strategy_trades | user_id | 普通 |
| idx_trades_strategy_id | qd_strategy_trades | strategy_id | 普通 |
| idx_trades_created_at | qd_strategy_trades | created_at | 普通 |
| idx_pending_orders_user_id | pending_orders | user_id | 普通 |
| idx_pending_orders_status | pending_orders | status | 普通 |
| idx_pending_orders_strategy_id | pending_orders | strategy_id | 普通 |
| idx_notifications_user_id | qd_strategy_notifications | user_id | 普通 |
| idx_notifications_strategy_id | qd_strategy_notifications | strategy_id | 普通 |
| idx_notifications_is_read | qd_strategy_notifications | is_read | 普通 |
| idx_strategy_logs_strategy_id | qd_strategy_logs | strategy_id | 普通 |
| idx_strategy_logs_timestamp | qd_strategy_logs | timestamp | 普通 |
| idx_trade_orders_lookup | qd_trade_orders | user_id, market, symbol | 普通 |
| idx_manual_positions_user_id | qd_manual_positions | user_id | 普通 |
| idx_position_alerts_user_id | qd_position_alerts | user_id | 普通 |
| idx_position_alerts_position_id | qd_position_alerts | position_id | 普通 |
| idx_position_monitors_user_id | qd_position_monitors | user_id | 普通 |
| idx_exchange_credentials_user_id | qd_exchange_credentials | user_id | 普通 |
| idx_indicator_codes_user_id | qd_indicator_codes | user_id | 普通 |
| idx_indicator_review_status | qd_indicator_codes | review_status | 普通 |
| idx_indicator_codes_source | qd_indicator_codes | source_indicator_id | 普通 |
| idx_purchases_indicator | qd_indicator_purchases | indicator_id | 普通 |
| idx_purchases_buyer | qd_indicator_purchases | buyer_id | 普通 |
| idx_purchases_seller | qd_indicator_purchases | seller_id | 普通 |
| idx_comments_indicator | qd_indicator_comments | indicator_id | 普通 |
| idx_comments_user | qd_indicator_comments | user_id | 普通 |
| idx_watchlist_user_id | qd_watchlist | user_id | 普通 |
| idx_analysis_tasks_user_id | qd_analysis_tasks | user_id | 普通 |
| idx_analysis_results_market_symbol | qd_analysis_results | market, symbol | 普通 |
| idx_analysis_results_user | qd_analysis_results | user_id | 普通 |
| idx_market_symbols_market | qd_market_symbols | market | 普通 |
| idx_market_symbols_is_hot | qd_market_symbols | market, is_hot | 普通 |
| idx_analysis_memory_symbol | qd_analysis_memory | market, symbol | 普通 |
| idx_analysis_memory_created | qd_analysis_memory | created_at DESC | 普通 |
| idx_analysis_memory_validated | qd_analysis_memory | validated_at | 条件索引 |
| idx_analysis_memory_user | qd_analysis_memory | user_id | 普通 |
| idx_backtest_runs_user_id | qd_backtest_runs | user_id | 普通 |
| idx_backtest_runs_indicator_id | qd_backtest_runs | indicator_id | 普通 |
| idx_backtest_runs_strategy_id | qd_backtest_runs | strategy_id | 普通 |
| idx_backtest_runs_run_type | qd_backtest_runs | run_type | 普通 |
| idx_backtest_trades_run_id | qd_backtest_trades | run_id | 普通 |
| idx_backtest_equity_points_run_id | qd_backtest_equity_points | run_id | 普通 |
| idx_quick_trades_user | qd_quick_trades | user_id | 普通 |
| idx_quick_trades_created | qd_quick_trades | created_at DESC | 普通 |
| idx_market_prices_lookup | qd_market_prices | market, symbol | 普通 |
| idx_market_klines_lookup | qd_market_klines | market, symbol, timeframe, kline_time | 普通 |
| idx_llm_provider_code | qd_llm_provider | code | UNIQUE |
| idx_qd_llm_api_key_provider | qd_llm_api_key | provider_id | 普通 |
| idx_qd_llm_api_key_status | qd_llm_api_key | status | 普通 |
| idx_qd_llm_model_provider | qd_llm_model | provider_id | 普通 |
| idx_qd_llm_call_log_created | qd_llm_call_log | created_at | 普通 |
| idx_collection_lookup | qd_collection_records | source, data_type, market, symbol | 普通 |
| idx_graph_relation_lookup | qd_graph_relation_snapshots | relation_type, from_uid, to_uid | 普通 |
| idx_graph_feature_lookup | qd_graph_feature_daily | market, symbol, trade_date | 普通 |
| idx_company_narrative_lookup | qd_company_narrative_features | ticker, trade_date | 普通 |
| idx_crypto_narrative_lookup | qd_crypto_narrative_features | symbol, trade_date | 普通 |
| idx_polymarket_feature_lookup | qd_polymarket_market_features | market_id, trade_date | 普通 |
| idx_polymarket_markets_market_id | qd_polymarket_markets | market_id | 普通 |
| idx_polymarket_markets_active | qd_polymarket_markets | active | 普通 |
| idx_polymarket_ai_analysis_market_id | qd_polymarket_ai_analysis | market_id | 普通 |
| idx_polymarket_opportunities_market_id | qd_polymarket_opportunities | market_id | 普通 |
| idx_dify_logs_workflow_id | qd_dify_workflow_logs | workflow_id | 普通 |
| idx_dify_logs_user_id | qd_dify_workflow_logs | user_id | 普通 |
| idx_dify_logs_status | qd_dify_workflow_logs | status | 普通 |
| idx_ds_config_source_code | qd_data_source_configs | source_code | 普通 |
| idx_ds_config_layer | qd_data_source_configs | layer | 普通 |
| idx_ds_dataset_source_id | qd_data_source_datasets | source_id | 普通 |
| idx_ds_dataset_code | qd_data_source_datasets | dataset_code | 普通 |
| idx_api_keys_source | qd_api_keys | source_config_id, key_type, status | 普通 |
| idx_api_keys_user | qd_api_keys | user_id | 普通 |
| idx_query_cache_key | qd_query_cache | cache_key | 普通 |
| idx_query_cache_source_status | qd_query_cache | source_code, status | 普通 |

---

*文档生成日期：2026-04-25*
