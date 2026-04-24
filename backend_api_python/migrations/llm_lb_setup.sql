-- LLM 负载均衡表结构 (PostgreSQL)

-- 1. 供应商表
CREATE TABLE IF NOT EXISTS qd_llm_provider (
    id SERIAL PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    code VARCHAR(64) NOT NULL UNIQUE,
    base_url VARCHAR(256),
    api_type VARCHAR(32) DEFAULT 'openai',
    status SMALLINT DEFAULT 1, -- 1: 启用, 0: 禁用
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. API 密钥表
CREATE TABLE IF NOT EXISTS qd_llm_api_key (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER NOT NULL REFERENCES qd_llm_provider(id),
    name VARCHAR(64),
    api_key_enc TEXT NOT NULL,
    status SMALLINT DEFAULT 1, -- 1: 正常, 0: 禁用, 2: 熔断
    weight INTEGER DEFAULT 1,
    owner_id BIGINT DEFAULT 0,
    is_public SMALLINT DEFAULT 0,
    fail_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. 模型表
CREATE TABLE IF NOT EXISTS qd_llm_model (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER NOT NULL REFERENCES qd_llm_provider(id),
    model_name VARCHAR(64) NOT NULL,
    display_name VARCHAR(64),
    lb_strategy VARCHAR(32) DEFAULT 'weighted_round_robin',
    retries INTEGER DEFAULT 3,
    timeout INTEGER DEFAULT 60,
    status SMALLINT DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. 调用日志表
CREATE TABLE IF NOT EXISTS qd_llm_call_log (
    id BIGSERIAL PRIMARY KEY,
    api_key_id INTEGER NOT NULL REFERENCES qd_llm_api_key(id),
    model_id INTEGER NOT NULL REFERENCES qd_llm_model(id),
    user_id BIGINT,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    latency_ms INTEGER,
    status_code INTEGER,
    error_msg TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 增加索引
CREATE INDEX IF NOT EXISTS idx_qd_llm_api_key_provider ON qd_llm_api_key(provider_id);
CREATE INDEX IF NOT EXISTS idx_qd_llm_api_key_status ON qd_llm_api_key(status);
CREATE INDEX IF NOT EXISTS idx_qd_llm_model_provider ON qd_llm_model(provider_id);
CREATE INDEX IF NOT EXISTS idx_qd_llm_call_log_created ON qd_llm_call_log(created_at);
