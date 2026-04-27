# LLM 负载均衡调用系统设计方案

## 1. 数据库设计 (Database Design)

基于现有的 `docs/ai_api_key.sql` 进行演进，建立规范的供应商、密钥、模型关系。

### 1.1 供应商表 `llm_provider`
存储 LLM 供应商基础信息。
- `id`: BIGINT (PK)
- `name`: VARCHAR(64) - 供应商名称 (如: OpenAI, Anthropic, DeepSeek)
- `base_url`: VARCHAR(256) - 基础 API 地址
- `api_type`: VARCHAR(32) - 接口协议类型 (openai, google, ollama 等)
- `status`: TINYINT - 状态 (1: 启用, 0: 禁用)
- `config`: JSON - 扩展配置 (如代理设置、自定义 Header)

### 1.2 API 密钥表 `llm_api_key`
存储加密的 API Key。
- `id`: BIGINT (PK)
- `provider_id`: BIGINT (FK) - 关联供应商
- `name`: VARCHAR(64) - 密钥备注名
- `api_key_enc`: TEXT - **加密存储**的 API Key
- `status`: TINYINT - 状态 (1: 正常, 0: 禁用, 2: 熔断中)
- `weight`: INT - 负载均衡权重 (默认 1)
- `owner_id`: BIGINT - 所有者 ID (用于权限控制)
- `is_public`: TINYINT - 是否公共 (1: 是, 0: 否)
- `fail_count`: INT - 连续失败次数 (用于熔断)
- `last_used_time`: DATETIME - 最后调用时间
- `metrics`: JSON - 性能统计 (成功率、平均耗时)

### 1.3 模型配置表 `llm_model`
存储模型级别的负载均衡和重试策略。
- `id`: BIGINT (PK)
- `provider_id`: BIGINT (FK)
- `model_name`: VARCHAR(64) - 真实模型 ID (如: gpt-4o)
- `display_name`: VARCHAR(64) - 显示名称
- `lb_strategy`: VARCHAR(32) - 负载均衡策略 (`weighted_round_robin`, `random`, `consistent_hash`, `least_connections`, `round_robin`)
- `retries`: INT - 重试次数 (默认 3)
- `timeout`: INT - 超时时间 (秒)
- `status`: TINYINT - 状态

---

## 2. 后端负载均衡实现 (Backend Implementation)

在 `backend_api_python/app/services/llm.py` 中重构 `LLMService`。

### 2.1 负载均衡算法
- **Weighted Round Robin (加权轮询)**: 根据密钥配置的 `weight` 进行平滑轮询。
- **Random (随机)**: 基于权重的随机选择。
- **Consistent Hash (一致性哈希)**: 根据请求上下文 (如 UserID) 进行哈希，确保同一用户请求相对固定在某个 Key，有利于缓存和追踪。
- **Least Connections (最少连接数)**: 记录内存中各 Key 的活跃请求数，优先选负担最轻的。
- **Round Robin (轮询)**: 简单均匀分发。

### 2.2 熔断与健康检查 (Circuit Breaker & Health Check)
- **熔断机制**: 连续失败达到阈值后，Key 标记为“熔断”，暂停使用 N 分钟。
- **自动恢复**: 熔断时间结束后，尝试一次调用，成功则恢复。
- **重试机制**: 调用失败后，自动根据 `retries` 配置，切换到另一个可用 Key 进行重试，最多 3 次。

### 2.3 安全性
- **加密**: 使用 `cryptography.fernet` 或 `AES-256-GCM` 对 `api_key` 进行加密存储。密钥保存在系统环境变量。

---

## 3. 前端实现 (Frontend Implementation)

### 3.1 菜单与国际化
- **新菜单**: 在系统设置下增加 “LLM 配置 (LLM Settings)” 子菜单。
- **多语言支持**: 
  - 修改 `frontend/src/locales/lang/*.js`，增加模型名称、负载均衡策略、状态、密钥管理等文案。
  - 自动跟随系统当前 `i18n` 语言。

### 3.2 功能页面
- **供应商管理**: 配置 BaseURL。
- **API 密钥管理**: 包含密钥的添加、加密展示(Masked)、权重修改、公私有切换。
- **模型管理**: 动态配置负载均衡策略、重试次数。
- **节点监控**: 实时展示各 API Key 的健康状态、调用次数、成功率、当前延迟。

---

## 4. 实施步骤

1.  **数据库初始化**: 执行 DDL 脚本，创建新表并迁移旧数据。
2.  **后端核心开发**:
    - 实现 `LBCallableLLM` 装饰器或包装类。
    - 实现 5 种算法策略。
    - 增加 `/api/llm/monitor` 接口。
3.  **前端页面开发**:
    - 增加配置页面和监控页面。
    - 补全所有语言包。
4.  **联调测试**: 模拟 API 故障触发熔断和重试。
