-- QuantDinger RBAC (Role-Based Access Control) Schema
-- Migration 002: Role & Permission Management
-- Run: psql -U quantdinger -c "\i migrations/002_rbac_init.sql"

-- =============================================================================
-- 2. Permissions (权限/菜单表)
-- =============================================================================

CREATE TABLE IF NOT EXISTS sys_permissions (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(50)   NOT NULL,
    permission_code VARCHAR(100)  NOT NULL,
    type            CHAR(10)      NOT NULL DEFAULT 'menu',
    parent_id       INTEGER       REFERENCES sys_permissions(id) ON DELETE CASCADE,
    path            VARCHAR(200),
    component       VARCHAR(200),
    icon            VARCHAR(50)   DEFAULT '',
    sort_order      INTEGER       DEFAULT 0,
    visible         BOOLEAN       DEFAULT TRUE,
    status          VARCHAR(20)   DEFAULT 'active',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_permissions_code ON sys_permissions(permission_code);
CREATE INDEX IF NOT EXISTS idx_permissions_parent ON sys_permissions(parent_id);
CREATE INDEX IF NOT EXISTS idx_permissions_type ON sys_permissions(type);

COMMENT ON TABLE sys_permissions IS '权限/菜单表 — 定义系统所有权限项，包括目录、菜单和按钮三类';
COMMENT ON COLUMN sys_permissions.id IS '主键，自增序列';
COMMENT ON COLUMN sys_permissions.name IS '权限显示名称，如"用户管理""新增用户"';
COMMENT ON COLUMN sys_permissions.permission_code IS '权限编码，唯一，格式 system:module:action，如 system:user:create';
COMMENT ON COLUMN sys_permissions.type IS '权限类型：dir—手风琴目录分组，menu—菜单项/页面，button—按钮/操作';
COMMENT ON COLUMN sys_permissions.parent_id IS '父权限ID，自引用外键，构建树形结构，NULL表示顶级';
COMMENT ON COLUMN sys_permissions.path IS '前端路由路径，menu类型必填，如 /user-manage；dir/button类型可为空';
COMMENT ON COLUMN sys_permissions.component IS '前端组件路径，menu类型必填，如 @/views/user-manage；dir/button类型可为空';
COMMENT ON COLUMN sys_permissions.icon IS '菜单图标，对应 ant-design-vue icon 名称，button类型可为空';
COMMENT ON COLUMN sys_permissions.sort_order IS '排序号，数值越小越靠前';
COMMENT ON COLUMN sys_permissions.visible IS '是否在菜单中可见，button类型始终为TRUE';
COMMENT ON COLUMN sys_permissions.status IS '状态：active—启用，disabled—禁用';
COMMENT ON COLUMN sys_permissions.created_at IS '创建时间';
COMMENT ON COLUMN sys_permissions.updated_at IS '最后更新时间';

-- =============================================================================
-- 3. Roles (角色表)
-- =============================================================================

CREATE TABLE IF NOT EXISTS sys_roles (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(50)   NOT NULL,
    role_code       VARCHAR(50)   NOT NULL,
    description     VARCHAR(200)  DEFAULT '',
    status          VARCHAR(20)   DEFAULT 'active',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_roles_code ON sys_roles(role_code);

COMMENT ON TABLE sys_roles IS '角色表 — 定义系统角色，一个角色可关联多个权限';
COMMENT ON COLUMN sys_roles.id IS '主键，自增序列';
COMMENT ON COLUMN sys_roles.name IS '角色名称，如"超级管理员""交易员"';
COMMENT ON COLUMN sys_roles.role_code IS '角色编码，唯一，如 super_admin / admin / trader / analyst / user';
COMMENT ON COLUMN sys_roles.description IS '角色描述说明';
COMMENT ON COLUMN sys_roles.status IS '状态：active—启用，disabled—禁用';
COMMENT ON COLUMN sys_roles.created_at IS '创建时间';
COMMENT ON COLUMN sys_roles.updated_at IS '最后更新时间';

-- =============================================================================
-- 4. User-Role Association (用户-角色关联表)
-- =============================================================================

CREATE TABLE IF NOT EXISTS sys_user_roles (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER       NOT NULL REFERENCES sys_users(id) ON DELETE CASCADE,
    role_id         INTEGER       NOT NULL REFERENCES sys_roles(id) ON DELETE CASCADE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE (user_id, role_id)
);

CREATE INDEX IF NOT EXISTS idx_ur_user ON sys_user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_ur_role ON sys_user_roles(role_id);

COMMENT ON TABLE sys_user_roles IS '用户-角色关联表 — 多对多关系，一个用户可拥有多个角色';
COMMENT ON COLUMN sys_user_roles.id IS '主键，自增序列';
COMMENT ON COLUMN sys_user_roles.user_id IS '用户ID，外键引用 sys_users(id)，级联删除';
COMMENT ON COLUMN sys_user_roles.role_id IS '角色ID，外键引用 sys_roles(id)，级联删除';
COMMENT ON COLUMN sys_user_roles.created_at IS '关联创建时间';

-- =============================================================================
-- 5. Role-Permission Association (角色-权限关联表)
-- =============================================================================

CREATE TABLE IF NOT EXISTS sys_role_permissions (
    id              SERIAL PRIMARY KEY,
    role_id         INTEGER       NOT NULL REFERENCES sys_roles(id) ON DELETE CASCADE,
    permission_id   INTEGER       NOT NULL REFERENCES sys_permissions(id) ON DELETE CASCADE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE (role_id, permission_id)
);

CREATE INDEX IF NOT EXISTS idx_rp_role ON sys_role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_rp_perm ON sys_role_permissions(permission_id);

COMMENT ON TABLE sys_role_permissions IS '角色-权限关联表 — 多对多关系，定义角色拥有哪些权限';
COMMENT ON COLUMN sys_role_permissions.id IS '主键，自增序列';
COMMENT ON COLUMN sys_role_permissions.role_id IS '角色ID，外键引用 sys_roles(id)，级联删除';
COMMENT ON COLUMN sys_role_permissions.permission_id IS '权限ID，外键引用 sys_permissions(id)，级联删除';
COMMENT ON COLUMN sys_role_permissions.created_at IS '关联创建时间';

-- =============================================================================
-- 6. Seed Data - Roles (种子数据：角色)
-- =============================================================================

INSERT INTO sys_roles (name, role_code, description) VALUES
('超级管理员', 'super_admin', '拥有系统全部权限，无限制访问所有功能和数据'),
('管理员',     'admin',       '系统管理权限 + 数据工具，可管理用户、角色和系统配置'),
('交易员',     'trader',      '交易工具 + 分析工具，可进行实盘交易和策略管理'),
('分析师',     'analyst',     '分析工具 + 数据工具，可查看分析数据和指标'),
('普通用户',   'user',        'AI资产分析 + 个人中心，基础查看权限')
ON CONFLICT (role_code) DO NOTHING;

-- =============================================================================
-- 7. Seed Data - Permissions (种子数据：权限树)
-- =============================================================================

-- ---- 分析工具 (sort 1-3) ----
INSERT INTO sys_permissions (name, permission_code, type, parent_id, path, component, icon, sort_order) VALUES
('分析工具',     'analysis-tools',     'dir',  NULL, NULL, NULL,                            'cluster',  1),
('AI资产分析',   'analysis:asset:view','menu', NULL, '/ai-asset-analysis', '@/views/ai-asset-analysis', 'appstore', 2),
('知识图谱分析', 'analysis:graph:view','menu', NULL, '/graph-analysis',    '@/views/graph-analysis',    'cluster',  3)
ON CONFLICT (permission_code) DO NOTHING;

-- ---- 指标 IDE (sort 4) ----
INSERT INTO sys_permissions (name, permission_code, type, parent_id, path, component, icon, sort_order) VALUES
('指标 IDE',     'indicator:ide:view',  'menu', NULL, '/indicator-ide',     '@/views/indicator-ide',     'code',     4)
ON CONFLICT (permission_code) DO NOTHING;

-- ---- 交易工具 (sort 5-11) ----
INSERT INTO sys_permissions (name, permission_code, type, parent_id, path, component, icon, sort_order) VALUES
('交易工具',     'trading-tools',       'dir',  NULL, NULL, NULL,                            'dollar',          5),
('交易机器人',   'trading:bot:view',    'menu', NULL, '/trading-bot',       '@/views/trading-bot',       'robot',           6),
('策略与实盘',   'trading:strategy:view','menu', NULL, '/strategy-live',    '@/views/trading-assistant','deployment-unit', 7)
ON CONFLICT (permission_code) DO NOTHING;

-- 交易机器人-按钮
DO $$ DECLARE p_id INTEGER; BEGIN
SELECT id INTO p_id FROM sys_permissions WHERE permission_code = 'trading:bot:view';
INSERT INTO sys_permissions (name, permission_code, type, parent_id, path, component, icon, sort_order) VALUES
('启动机器人',   'trading:bot:start',   'button', p_id, NULL, NULL, NULL, 1),
('停止机器人',   'trading:bot:stop',    'button', p_id, NULL, NULL, NULL, 2),
('编辑机器人',   'trading:bot:update',  'button', p_id, NULL, NULL, NULL, 3)
ON CONFLICT (permission_code) DO NOTHING;
END $$;

-- ---- AI 配置 (sort 12-19) ----
INSERT INTO sys_permissions (name, permission_code, type, parent_id, path, component, icon, sort_order) VALUES
('AI 配置',      'ai-config',           'dir',  NULL, NULL, NULL,                            'api',            12),
('LLM 设置',     'ai:llm:view',         'menu', NULL, '/llm-settings',      '@/views/llm',              'api',            13),
('Dify 工作流',  'ai:dify:view',        'menu', NULL, '/dify-workflow',     '@/views/dify-workflow',    'robot',          14)
ON CONFLICT (permission_code) DO NOTHING;

-- LLM 设置-按钮
DO $$ DECLARE p_id INTEGER; BEGIN
SELECT id INTO p_id FROM sys_permissions WHERE permission_code = 'ai:llm:view';
INSERT INTO sys_permissions (name, permission_code, type, parent_id, path, component, icon, sort_order) VALUES
('新增配置',     'ai:llm:create',       'button', p_id, NULL, NULL, NULL, 1),
('编辑配置',     'ai:llm:update',       'button', p_id, NULL, NULL, NULL, 2),
('删除配置',     'ai:llm:delete',       'button', p_id, NULL, NULL, NULL, 3)
ON CONFLICT (permission_code) DO NOTHING;
END $$;

-- Dify 工作流-按钮
DO $$ DECLARE p_id INTEGER; BEGIN
SELECT id INTO p_id FROM sys_permissions WHERE permission_code = 'ai:dify:view';
INSERT INTO sys_permissions (name, permission_code, type, parent_id, path, component, icon, sort_order) VALUES
('创建流程',     'ai:dify:create',       'button', p_id, NULL, NULL, NULL, 1),
('编辑流程',     'ai:dify:update',       'button', p_id, NULL, NULL, NULL, 2),
('执行流程',     'ai:dify:execute',      'button', p_id, NULL, NULL, NULL, 3)
ON CONFLICT (permission_code) DO NOTHING;
END $$;

-- ---- 数据工具 (sort 20-30) ----
INSERT INTO sys_permissions (name, permission_code, type, parent_id, path, component, icon, sort_order) VALUES
('数据工具',     'data-tools',          'dir',  NULL, NULL, NULL,                            'database',       20),
('指标市场',     'data:indicator:view',  'menu', NULL, '/indicator-community','@/views/indicator-community','shop',            21),
('数据源管理',   'data:source:view',     'menu', NULL, '/data-source',        '@/views/data-source',        'database',       22)
ON CONFLICT (permission_code) DO NOTHING;

-- 数据源管理-按钮
DO $$ DECLARE p_id INTEGER; BEGIN
SELECT id INTO p_id FROM sys_permissions WHERE permission_code = 'data:source:view';
INSERT INTO sys_permissions (name, permission_code, type, parent_id, path, component, icon, sort_order) VALUES
('新增数据源',   'data:source:create',   'button', p_id, NULL, NULL, NULL, 1),
('编辑数据源',   'data:source:update',   'button', p_id, NULL, NULL, NULL, 2),
('删除数据源',   'data:source:delete',   'button', p_id, NULL, NULL, NULL, 3)
ON CONFLICT (permission_code) DO NOTHING;
END $$;

-- ---- 系统管理 (sort 31-50) ----
INSERT INTO sys_permissions (name, permission_code, type, parent_id, path, component, icon, sort_order) VALUES
('系统管理',     'system',              'dir',  NULL, NULL, NULL,                            'setting',        31),
('用户管理',     'system:user:view',     'menu', NULL, '/user-manage',        '@/views/user-manage',        'team',           32),
('角色管理',     'system:role:view',     'menu', NULL, '/role-manage',        '@/views/role-manage',        'safety',         33),
('权限管理',     'system:permission:view','menu', NULL, '/permission-manage',  '@/views/permission-manage',  'lock',           34),
('系统设置',     'system:settings:view', 'menu', NULL, '/settings',           '@/views/settings',           'setting',        35)
ON CONFLICT (permission_code) DO NOTHING;

-- 用户管理-按钮
DO $$ DECLARE p_id INTEGER; BEGIN
SELECT id INTO p_id FROM sys_permissions WHERE permission_code = 'system:user:view';
INSERT INTO sys_permissions (name, permission_code, type, parent_id, path, component, icon, sort_order) VALUES
('新增用户',     'system:user:create',          'button', p_id, NULL, NULL, NULL, 1),
('编辑用户',     'system:user:update',          'button', p_id, NULL, NULL, NULL, 2),
('删除用户',     'system:user:delete',          'button', p_id, NULL, NULL, NULL, 3),
('分配角色',     'system:user:assign-role',     'button', p_id, NULL, NULL, NULL, 4),
('重置密码',     'system:user:reset-password',  'button', p_id, NULL, NULL, NULL, 5)
ON CONFLICT (permission_code) DO NOTHING;
END $$;

-- 角色管理-按钮
DO $$ DECLARE p_id INTEGER; BEGIN
SELECT id INTO p_id FROM sys_permissions WHERE permission_code = 'system:role:view';
INSERT INTO sys_permissions (name, permission_code, type, parent_id, path, component, icon, sort_order) VALUES
('新增角色',     'system:role:create',          'button', p_id, NULL, NULL, NULL, 1),
('编辑角色',     'system:role:update',          'button', p_id, NULL, NULL, NULL, 2),
('删除角色',     'system:role:delete',          'button', p_id, NULL, NULL, NULL, 3),
('分配权限',     'system:role:assign-role-menu', 'button', p_id, NULL, NULL, NULL, 4)
ON CONFLICT (permission_code) DO NOTHING;
END $$;

-- 权限管理-按钮
DO $$ DECLARE p_id INTEGER; BEGIN
SELECT id INTO p_id FROM sys_permissions WHERE permission_code = 'system:permission:view';
INSERT INTO sys_permissions (name, permission_code, type, parent_id, path, component, icon, sort_order) VALUES
('新增权限',     'system:permission:create',    'button', p_id, NULL, NULL, NULL, 1),
('编辑权限',     'system:permission:update',    'button', p_id, NULL, NULL, NULL, 2),
('删除权限',     'system:permission:delete',    'button', p_id, NULL, NULL, NULL, 3)
ON CONFLICT (permission_code) DO NOTHING;
END $$;

-- ---- 独立页面 (sort 60-61) ----
INSERT INTO sys_permissions (name, permission_code, type, parent_id, path, component, icon, sort_order) VALUES
('个人中心',     'user:profile:view',    'menu',  NULL, '/profile',           '@/views/profile',      'user',           60),
('会员充值',     'user:billing:view',    'menu',  NULL, '/billing',           '@/views/billing',      'wallet',         61)
ON CONFLICT (permission_code) DO NOTHING;

-- =============================================================================
-- 8. Seed Data - Role-Permission Assignments (种子数据：角色分配权限)
-- =============================================================================

-- super_admin: 拥有全部权限（后续通过代码层面做豁免，此处也分配做备份）
DO $$ DECLARE r_id INTEGER; BEGIN
SELECT id INTO r_id FROM sys_roles WHERE role_code = 'super_admin';
INSERT INTO sys_role_permissions (role_id, permission_id)
SELECT r_id, id FROM sys_permissions
ON CONFLICT (role_id, permission_id) DO NOTHING;
END $$;

-- admin: 系统管理 + 数据工具 + 分析工具 + AI配置 + 个人中心
DO $$ DECLARE r_id INTEGER; BEGIN
SELECT id INTO r_id FROM sys_roles WHERE role_code = 'admin';
INSERT INTO sys_role_permissions (role_id, permission_id)
SELECT r_id, id FROM sys_permissions
WHERE permission_code IN (
    'analysis-tools', 'analysis:asset:view', 'analysis:graph:view',
    'indicator:ide:view',
    'trading-tools', 'trading:bot:view', 'trading:strategy:view',
    'ai-config', 'ai:llm:view', 'ai:llm:create', 'ai:llm:update', 'ai:llm:delete',
    'ai:dify:view', 'ai:dify:create', 'ai:dify:update', 'ai:dify:execute',
    'data-tools', 'data:indicator:view', 'data:source:view',
    'data:source:create', 'data:source:update', 'data:source:delete',
    'system', 'system:user:view', 'system:user:create', 'system:user:update',
    'system:user:delete', 'system:user:assign-role', 'system:user:reset-password',
    'system:role:view', 'system:role:create', 'system:role:update',
    'system:role:delete', 'system:role:assign-role-menu',
    'system:permission:view', 'system:permission:create', 'system:permission:update', 'system:permission:delete',
    'system:settings:view',
    'user:profile:view', 'user:billing:view'
)
ON CONFLICT (role_id, permission_id) DO NOTHING;
END $$;

-- trader: 交易工具 + 分析工具 + 个人中心
DO $$ DECLARE r_id INTEGER; BEGIN
SELECT id INTO r_id FROM sys_roles WHERE role_code = 'trader';
INSERT INTO sys_role_permissions (role_id, permission_id)
SELECT r_id, id FROM sys_permissions
WHERE permission_code IN (
    'analysis-tools', 'analysis:asset:view', 'analysis:graph:view',
    'indicator:ide:view',
    'trading-tools', 'trading:bot:view', 'trading:bot:start', 'trading:bot:stop',
    'trading:bot:update', 'trading:strategy:view',
    'user:profile:view', 'user:billing:view'
)
ON CONFLICT (role_id, permission_id) DO NOTHING;
END $$;

-- analyst: 分析工具 + 数据工具 + AI配置 + 个人中心
DO $$ DECLARE r_id INTEGER; BEGIN
SELECT id INTO r_id FROM sys_roles WHERE role_code = 'analyst';
INSERT INTO sys_role_permissions (role_id, permission_id)
SELECT r_id, id FROM sys_permissions
WHERE permission_code IN (
    'analysis-tools', 'analysis:asset:view', 'analysis:graph:view',
    'indicator:ide:view',
    'ai-config', 'ai:llm:view', 'ai:llm:create', 'ai:llm:update',
    'ai:dify:view', 'ai:dify:create', 'ai:dify:update', 'ai:dify:execute',
    'data-tools', 'data:indicator:view', 'data:source:view',
    'user:profile:view', 'user:billing:view'
)
ON CONFLICT (role_id, permission_id) DO NOTHING;
END $$;

-- user: AI资产分析 + 指标IDE + 指标市场 + 个人中心
DO $$ DECLARE r_id INTEGER; BEGIN
SELECT id INTO r_id FROM sys_roles WHERE role_code = 'user';
INSERT INTO sys_role_permissions (role_id, permission_id)
SELECT r_id, id FROM sys_permissions
WHERE permission_code IN (
    'analysis:asset:view',
    'indicator:ide:view',
    'data:indicator:view',
    'user:profile:view', 'user:billing:view'
)
ON CONFLICT (role_id, permission_id) DO NOTHING;
END $$;

-- =============================================================================
-- 9. Assign super_admin role to existing admin user
-- =============================================================================

DO $$ DECLARE r_id INTEGER; u_id INTEGER; BEGIN
SELECT id INTO r_id FROM sys_roles WHERE role_code = 'super_admin';
SELECT id INTO u_id FROM sys_users WHERE username = 'admin';
IF r_id IS NOT NULL AND u_id IS NOT NULL THEN
    INSERT INTO sys_user_roles (user_id, role_id)
    VALUES (u_id, r_id)
    ON CONFLICT (user_id, role_id) DO NOTHING;
END IF;
END $$;
