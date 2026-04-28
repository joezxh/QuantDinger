# QuantDinger Frontend 迁移计划：Vue 2 → Vue 3

## 背景

本项目拥有两套前端代码库：
- **`frontend/`**（旧版）：基于 Vue 2 + Vuex + Vue Router 3 + Ant Design Vue 1.x，功能完整但技术栈老旧
- **`frontend-v3/`**（新版）：基于 Vue 3 + Pinia + Vue Router 4 + Ant Design Vue 4.x + TypeScript，功能大量缺失，多数页面为占位页面

目标：将旧版的所有功能模块完整迁移至新版技术栈，同时保持 API 兼容性和 UX 一致性。

---

## 一、技术栈对比

| 维度 | frontend（旧） | frontend-v3（新） | 迁移要点 |
|------|----------------|-------------------|----------|
| 框架 | Vue 2.6 | Vue 3.5 | Options API → Composition API + `<script setup>` |
| 状态管理 | Vuex 3.x | Pinia 3.x | `store.commit/dispatch` → `defineStore` + `storeToRefs` |
| 路由 | Vue Router 3.5 | Vue Router 4.6 | `router/index.js` → `router/index.ts`（已存在） |
| UI 组件库 | Ant Design Vue 1.7.x | Ant Design Vue 4.2.x | `a-icon` 废弃、slot 语法变更、form API 重构 |
| 图标 | `<a-icon type="xxx">` | `@ant-design/icons-vue` 独立引入 | 全量替换图标写法 |
| 语言 | JavaScript | TypeScript | 添加类型定义 |
| 构建工具 | Webpack (Vue CLI) | Vite 8 | 无需迁移，配置已存在 |
| 图表 | ECharts 6 + klinecharts 9 + lightweight-charts 5 | ECharts 5 + vue-echarts 6 | klinecharts/lightweight-charts 需重新集成 |
| 代码编辑器 | CodeMirror 5 | 未集成 | 需集成 CodeMirror 6 或 Monaco Editor |
| 国际化 | vue-i18n 8，支持10种语言 | vue-i18n 9（空目录） | 需迁移全部 i18n key |
| HTTP 客户端 | axios 0.26 | axios 1.15 | API 兼容，request.ts 需重构 |
| 日期库 | moment.js | dayjs | API 部分差异 |
| 加密 | crypto-js | 未集成 | 若登录需要，需要添加 |

---

## 二、功能模块现状对比

### 已完成迁移的模块 ✅

| 模块 | 旧版文件大小 | 新版文件大小 | 状态说明 |
|------|-------------|-------------|----------|
| Dashboard（总体态势） | 83KB | 79KB | 功能基本完整 |
| AI 智能分析 | 133KB + 组件 | 21KB | **部分迁移，大量功能缺失** |
| 投资组合 | 97KB | 20KB | **部分迁移，大量功能缺失** |
| 用户管理 | 旧版存在 | 新版存在 | 待验证完整性 |
| 角色管理 | 旧版存在 | 新版存在 | 待验证完整性 |
| 权限管理 | 旧版存在 | 新版存在 | 待验证完整性 |
| 账单管理 | 26KB | 22KB | 基本完整 |
| Dify 工作流 | 10KB | 10KB | 基本完整 |
| 个人中心 | 83KB | 20KB | **功能大量缺失** |
| 系统设置 | 26KB | 13KB | **功能缺失** |
| 交易助手 | 253KB + 组件 | 15KB | **严重缺失** |

### 完全未迁移的模块（占位页面）❌

| 模块 | 旧版规模 | 新版状态 | 优先级 |
|------|----------|----------|--------|
| **指标 IDE** | 224KB（5755行）| 占位页面（4行） | P0 核心功能 |
| **交易机器人** | 21KB + 5个组件 | 占位页面（12行） | P0 核心功能 |
| **知识图谱分析** | 20KB | 占位页面（12行） | P1 |
| **数据源管理** | 多文件（ConfigList/DatasetList/KeyList/SyncTask） | 占位页面（4行） | P1 |
| **策略与实盘**（新路由）| 对应旧版交易助手部分功能 | 占位页面（4行） | P1 |
| **AI 资产分析** | 26KB | 占位页面（23行） | P1 |

### 旧版存在但新版路由不包含的模块 ⚠️

| 模块 | 旧版路径 | 说明 |
|------|----------|------|
| **指标社区（Indicator Community）** | `views/indicator-community/` | 旧版有完整的指标市场/社区功能 |
| **用户登录（完整版）** | `views/user/Login.vue`（57KB） | 新版仅 3KB，功能严重简化 |
| **LLM 管理** | `views/llm/`（5个文件） | 新版路由中不存在此模块 |

### API 层缺失的接口文件

新版 `src/api/` 相比旧版缺失以下 API 模块：

| 缺失 API | 旧版文件 | 服务 |
|----------|----------|------|
| `ai-trading.ts` | ai-trading.js（2KB） | AI 交易相关 |
| `credentials.ts` | credentials.js（979B） | 交易所凭证管理 |
| `llm.ts` | llm.js（1.9KB） | LLM 提供商管理 |
| `manage.ts` | manage.js（1.2KB） | 通用管理 |
| `polymarket.ts` | polymarket.js（855B） | 预测市场 |
| `quick-trade.ts` | quick-trade.js（935B） | 快速交易 |
| `strategy.ts` | strategy.js（7.3KB！）| **最关键：策略全量 API** |
| `sync.ts` | sync.js（1.8KB） | 数据同步 |

---

## 三、各模块详细功能差距

### 3.1 指标 IDE（最复杂）
旧版（224KB，5755行）包含：
- **代码编辑器**：CodeMirror 5 集成，支持 Python 语法高亮
- **K 线图面板**：klinecharts 9 集成，支持实时行情
- **回测引擎**：参数配置（日期范围、资金、杠杆、方向）、运行、结果展示（equity curve、交易明细表格）
- **AI 代码生成**：基于 LLM 的指标代码生成
- **AI 代码质检**：代码质量检查 + AI 调试报告
- **AI 参数调优**：Grid/Random + LLM 实验（多轮优化）
- **历史记录抽屉**：回测历史查看
- **自选股列表**：观察列表管理

新版（438字节）：纯占位页面

### 3.2 交易助手（最关键业务）
旧版（253KB，7332行 + 8个组件文件）包含：
- **策略列表**（左面板）：按策略/品种分组、折叠、状态显示
- **策略详情**（右面板）：关键统计（投资额、当前权益、PnL）、状态控制
- **策略详情标签页**：持仓记录、交易记录、业绩分析、策略日志
- **策略创建/编辑向导**（多步骤）：指标选择 → 交易参数 → 信号配置
- **策略类型**：指标策略、AI 策略（Prompt-based）、脚本策略
- **交易总览**：Dashboard Overview 嵌入
- **脚本编辑器**：StrategyEditor 组件（39KB）
- **AI 决策记录**：AIDecisionRecords 组件（13KB）

新版（15KB）：仅基础占位，远未完整

### 3.3 交易机器人
旧版（21KB + 组件）包含：
- BotList（机器人列表）
- BotCreateWizard（创建向导，35KB）
- BotDetail（详情，40KB）
- BotTypeCards（类型选择）
- AiBotDialog（AI 对话）

新版：纯占位页面

### 3.4 数据源管理
旧版（多文件）包含：
- ConfigList（数据源配置列表）
- DatasetList（数据集管理）
- KeyList（API Key 管理）
- SyncTaskTab（同步任务管理）

新版：纯占位页面

### 3.5 知识图谱分析
旧版（20KB）包含：完整图谱可视化（GraphVisualization 组件）
新版：纯占位页面

### 3.6 AI 智能分析（部分缺失）
旧版（133KB + FastAnalysisReport 73KB + index.vue 120KB）
新版（21KB）：大量功能缺失，需对比具体功能点

### 3.7 国际化（完全缺失）
旧版：10种语言，每个文件 ~300KB，覆盖所有模块
新版：locales 目录为空

---

## 四、迁移实施计划

### 第一阶段：基础设施（P0，约3天）

#### 1.1 国际化体系搭建
- 迁移 `frontend/src/locales/lang/zh-CN.js` → `frontend-v3/src/locales/zh-CN.ts`
- 优先迁移：en-US、zh-CN（必须），其他语言视需求
- 在 `main.ts` 中注册 vue-i18n 9

#### 1.2 全局 API 请求层
- 完善 `frontend-v3/src/utils/request.ts`（添加拦截器、错误处理、刷新 token）
- 补全缺失的 API 文件（strategy.ts 最关键）

#### 1.3 Pinia Store 扩展
- 目前只有 `app.ts` 和 `user.ts`
- 新增：`strategy.ts`、`market.ts`、`indicator.ts`

#### 1.4 全局组件注册
- 迁移旧版 `components/` 的公共组件（QuickTradePanel、GraphVisualization 等）
- 适配 ADV4 的 API 变更

---

### 第二阶段：P0 核心功能（约2周）

#### 2.1 指标 IDE（优先级最高）

**技术方案：**
```
frontend-v3/src/views/indicator-ide/
├── index.vue              # 主容器（Composition API）
├── components/
│   ├── CodeEditor.vue     # CodeMirror 6 集成
│   ├── KlineChart.vue     # klinecharts 9 集成（需重新添加依赖）
│   ├── BacktestPanel.vue  # 回测参数 + 结果
│   ├── AiGenPanel.vue     # AI 代码生成
│   ├── AiQualityPanel.vue # 代码质检 + AI 调试
│   ├── ExperimentPanel.vue# AI 参数调优实验
│   └── BacktestHistoryDrawer.vue
```

**ADV4 适配要点：**
- `v-model` 替换 `v-decorator`（form 已废弃 decorator API）
- `<a-icon type="xxx">` → `<CodeOutlined />` 等
- slot 语法：`slot="xxx"` → `#xxx`
- `a-table` 的 columns 中 `scopedSlots` → `customRender`

**新增依赖：**
```bash
pnpm add klinecharts codemirror @codemirror/lang-python
```

#### 2.2 交易助手（策略管理）

**技术方案：**
```
frontend-v3/src/views/trading-assistant/
├── index.vue              # 主容器 + 顶层 Tabs
├── components/
│   ├── StrategyList.vue   # 左侧策略列表（分组）
│   ├── StrategyDetail.vue # 右侧详情面板
│   ├── PositionRecords.vue
│   ├── TradingRecords.vue
│   ├── PerformanceAnalysis.vue
│   ├── StrategyLogs.vue
│   ├── StrategyEditor.vue # 脚本编辑器（CodeMirror 6）
│   ├── StrategyForm.vue   # 创建/编辑向导
│   ├── StrategyTypeSelector.vue
│   └── AIDecisionRecords.vue
```

**新增 API（strategy.ts）：**
参照 `frontend/src/api/strategy.js`（7.3KB）完整迁移

---

### 第三阶段：P1 关键功能（约1.5周）

#### 3.1 交易机器人

**技术方案：**
```
frontend-v3/src/views/trading-bot/
├── index.vue
└── components/
    ├── BotList.vue
    ├── BotCreateWizard.vue
    ├── BotDetail.vue
    ├── BotTypeCards.vue
    └── AiBotDialog.vue
```

#### 3.2 数据源管理

**技术方案：**
```
frontend-v3/src/views/data-source/
├── index.vue              # Tabs 容器
└── components/
    ├── ConfigList.vue     # 数据源配置
    ├── DatasetList.vue    # 数据集
    ├── KeyList.vue        # API Key
    └── SyncTaskTab.vue    # 同步任务
```

#### 3.3 知识图谱分析

**技术方案：**
- 迁移 `frontend/src/components/GraphVisualization/` 到新版
- 适配 ECharts 5 graph 系列配置变化

#### 3.4 AI 资产分析（完善）

对比旧版 `views/ai-asset-analysis/index.vue`（26KB）和新版（509B，占位），补全缺失功能

---

### 第四阶段：P2 管理功能完善（约1周）

#### 4.1 LLM 管理（新增到路由）
旧版有完整的 LLM 管理（ProviderList、ModelList、KeyList、LLMStats）
新版路由中完全缺失，需：
1. 新增路由 `/llm`
2. 迁移 4 个子组件

#### 4.2 指标社区
旧版 `views/indicator-community/`（指标市场/社区功能）
新版路由中不存在，需决策是否纳入

#### 4.3 个人中心（完善）
旧版（83KB）vs 新版（20KB），差距大，需补全：
- 头像修改
- 安全设置
- API Key 管理
- 绑定信息

#### 4.4 国际化完整迁移
将旧版 10 种语言文件完整迁移并适配新版所有模块

---

## 五、优先级排序总表

```
P0（立即开始，阻塞用户核心使用）
├── 1. 国际化基础设施（zh-CN + en-US）
├── 2. strategy.ts API 文件
├── 3. 指标 IDE（完整功能）
└── 4. 交易助手（完整功能）

P1（第二批，核心业务功能）
├── 5. 交易机器人
├── 6. 数据源管理
├── 7. AI 资产分析（完整）
├── 8. 知识图谱分析
└── 9. 策略与实盘（路由整合）

P2（第三批，管理功能）
├── 10. LLM 管理（新增路由）
├── 11. 个人中心（完善）
├── 12. 系统设置（完善）
├── 13. 指标社区
└── 14. 全量国际化（10种语言）
```

---

## 六、关键技术迁移对照表

### ADV1 → ADV4 常见变更

| 旧语法（ADV1） | 新语法（ADV4） |
|----------------|----------------|
| `<a-icon type="plus" />` | `<PlusOutlined />` |
| `v-decorator` | `v-model` + `a-form` |
| `slot="xxx"` | `#xxx` |
| `slot-scope="text"` | `#xxx="{ text }"` |
| `this.$form.createForm(this)` | `useForm()` composable |
| `a-select-option` | `a-select-option`（保留）|
| `dataSource` | `dataSource`（保留）|
| `:getPopupContainer` | `:getPopupContainer`（保留）|

### Vue 2 → Vue 3 Composition API

| 旧语法（Vue 2 Options） | 新语法（Vue 3 Composition） |
|-------------------------|------------------------------|
| `data() { return {} }` | `const x = ref()` / `reactive()` |
| `computed: {}` | `computed(() => ...)` |
| `watch: {}` | `watch()` / `watchEffect()` |
| `methods: {}` | 直接在 `<script setup>` 中定义函数 |
| `mounted()` | `onMounted(() => ...)` |
| `this.$route` | `useRoute()` |
| `this.$router` | `useRouter()` |
| `this.$store` | `useXxxStore()` |
| `this.$t('key')` | `const { t } = useI18n(); t('key')` |

---

## 七、验证计划

### 每个模块迁移后需验证
1. **功能覆盖**：对照旧版每个功能点逐一验证
2. **API 联通**：确保所有 API 调用正常返回数据
3. **主题适配**：暗色模式下无样式异常
4. **响应式**：移动端布局正常
5. **i18n**：语言切换后文案正常

### 自动化测试（可选）
- 使用 Playwright 对关键用户流程进行 E2E 测试

---

## 八、开放问题

> [!IMPORTANT]
> **问题1：指标社区是否迁移？**
> 旧版有完整的指标社区（用户分享、购买、评论功能），新版路由中不存在。请确认是否纳入迁移范围。

> [!IMPORTANT]
> **问题2：CodeMirror 版本选择？**
> 旧版用 CodeMirror 5，建议新版直接用 CodeMirror 6（更现代，性能更好），但 API 差异较大。或使用 Monaco Editor（VS Code 同款）？

> [!IMPORTANT]
> **问题3：K 线图组件优先级？**
> klinecharts 是旧版的核心依赖（指标 IDE 的主图），新版 package.json 中没有此依赖。lightweight-charts 也缺失。请确认保留哪个。

> [!WARNING]
> **问题4：策略与实盘（strategy-live）路由定义？**
> 新版有 `/strategy-live` 路由，旧版没有此路由（交易助手包含了策略管理）。请确认 `strategy-live` 和 `trading-assistant` 的功能边界划分。

> [!NOTE]
> **问题5：迁移粒度？**
> 建议优先迁移核心功能，复杂的样式微调和动画效果可后续迭代，您是否同意这种策略？
