# 量化模块 — 前端开发规则

> 本规则基于 `frontend/src/` 目录实际代码结构、组件组织、API调用方式、状态管理模式提炼而成，供 Qoder AI 助手遵循。

---

## 1. 项目概览与技术栈约束

### 1.1 核心技术栈
- **框架**: Vue 3.4.21 + Composition API（`<script setup lang="ts">`）
- **构建工具**: Vite 5.1.5
- **语言**: TypeScript 5.4.2（`strict: true`, `noUnusedLocals: true`, `noUnusedParameters: true`）
- **UI 组件库**: Ant Design Vue 4.1.2
- **状态管理**: Pinia 2.1.7（Composition API 风格）
- **路由**: Vue Router 4.3.0（`createWebHistory`）
- **HTTP 客户端**: Axios 1.6.7
- **图表**: ECharts 5.5.0 + `vue-echarts`
- **日期处理**: dayjs（locale: zh-cn）
- **样式预处理器**: Less / Sass 均可用
- **Markdown 渲染**: `markdown-it`, `marked`, `highlight.js`

### 1.2 关键约束
- **必须使用 `<script setup lang="ts">`**，禁止 Options API
- **路径别名**: `@/` 指向 `src/`
- **类型文件**: `.d.ts` 扩展名（如 `types/api.d.ts`）
- **模块类型**: `"type": "module"`（ES Modules）

---

## 2. 目录结构与模块组织规范

```
frontend/src/
├── main.ts              # 应用入口：创建 app、挂载 Pinia/Router/Antd/指令
├── App.vue              # 根组件：a-config-provider + router-view
├── api/                 # API 接口层，按业务模块分文件
├── assets/              # 静态资源（图片等）
├── components/          # 全局公共组件
├── composables/         # 组合式函数（单例模式字典、权限、日期范围等）
├── directives/          # 自定义指令（permission、autoScale）
├── layouts/             # 布局组件（AppLayout.vue）
├── router/              # 路由配置
├── stores/              # Pinia 状态管理
├── styles/              # 全局样式（global.css）
├── types/               # TypeScript 类型定义（.d.ts 文件）
├── utils/               # 工具函数（request、auth、dateFormat 等）
└── views/               # 页面级组件，按模块分子目录
```

### 2.1 目录规范
- `api/`：每个业务模块独立文件（如 `auth.ts`, `admin.ts`, `disposal.ts`），禁止将所有接口放在一个文件
- `views/`：每个页面一个子目录，内含 `index.vue` 和局部组件（如 `views/overview/components/TopStatsBar.vue`）
- `types/`：按领域分 `.d.ts` 文件，禁止在 `.ts` 文件中重复定义相同类型
- `composables/`：功能单一、可复用的组合式函数，命名以 `use` 开头

---

## 3. API 接口层（api/）规范

### 3.1 统一请求实例
- 所有 API 必须从 `@/utils/request` 导入封装后的 axios 实例：
  ```typescript
  import request from '@/utils/request'
  ```
- 禁止直接引入 `axios` 发起业务请求

### 3.2 API 文件组织
```typescript
// api/auth.ts
import request from '@/utils/request'

const BASE_URL = '/api/v1/auth'

/**
 * 登录
 */
export function login(data: { username: string; password: string }) {
  return request.post(`${BASE_URL}/login`, data)
}

/**
 * 获取当前用户信息
 */
export function getUserInfo() {
  return request.get(`${BASE_URL}/me`)
}
```

### 3.3 请求方法封装
```typescript
request.get<T>(url, config?)
request.post<T>(url, data?, config?)
request.put<T>(url, data?, config?)
request.delete<T>(url, config?)
```

### 3.4 类型定义
- 请求/响应相关的 `interface` 定义在 api 文件内（就近原则）：
  ```typescript
  export interface RiskEventForm {
    event_title: string
    event_content?: string
    risk_level?: string
  }
  ```
- 通用类型（如分页）从 `types/` 导入：
  ```typescript
  import type { ApiResponse, PageParams, PageData } from '@/types/api'
  ```

### 3.5 响应类型处理
- 管理端列表接口泛型：
  ```typescript
  export function getUserList(params: PageParams) {
    return request.get<ApiResponse<PageData<UserListItem>>>('/api/v1/admin/users', { params })
  }
  ```
- 注意：部分后端接口返回格式不一致（有的直接返回数据，有的包装在 `ApiResponse` 中），需根据实际情况选择是否带泛型

### 3.6 API 环境基地址
- `request.ts` 中通过 `import.meta.env.VITE_API_BASE_URL` 获取基地址
- 默认回退：`http://localhost:8000`

---

## 4. HTTP 请求封装（utils/request.ts）规范

### 4.1 Axios 实例配置
```typescript
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json;charset=utf-8'
  }
})
```

### 4.2 请求拦截器
- 自动从 `localStorage` 读取 Token
- 添加 `Authorization: Bearer <token>` Header
- 过滤无效的 `'undefined'` 字符串

### 4.3 响应拦截器（强制）
- **直接返回 `response.data`**，剥离 axios 包装层
- 状态码处理：
  - `401`：`message.error('登录已过期，请重新登录')` + 清除 Token + 跳转 `/login`
  - `403`：`message.error('没有权限访问该资源')`
  - `404`：`message.error('请求的资源不存在')`
  - `500`：`message.error('服务器错误')`
  - 其他：`message.error(error.message || '请求失败')`
- 网络断开：`message.error('网络连接失败')`

### 4.4 错误处理原则
- 所有请求错误统一通过 `message` 组件提示用户
- 业务层一般不再重复处理 HTTP 状态码错误（除非需要特殊逻辑）

---

## 5. 状态管理（stores/）规范

### 5.1 Pinia + Composition API 风格
```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(getToken() || '')
  const userInfo = ref<UserInfo | null>(null)

  async function login(username: string, password: string) {
    const res = await loginApi({ username, password })
    const accessToken = res?.token ?? res?.access_token
    if (!accessToken) throw new Error('登录成功但未返回有效 token')
    token.value = accessToken
    setToken(accessToken)
    await fetchUserInfo()
    return res
  }

  return { token, userInfo, login }
})
```

### 5.2 Store 命名规范
- 文件名：`user.ts`, `app.ts`, `permission.ts`
- Store ID：与文件名一致（如 `'user'`, `'app'`）
- 使用函数：`useXxxStore()`（use + PascalCase + Store）

### 5.3 状态持久化
- Token 通过 `localStorage` 手动存取（`utils/auth.ts`）
- 字典缓存通过 `localStorage` 存取（`api/common.ts`）
- 其他状态原则上不持久化到 localStorage

### 5.4 登录后初始化流程
```typescript
// userStore.login() 中：
// 1. 调用登录 API
// 2. 存储 Token
// 3. 获取用户信息
// 4. 批量拉取字典数据并写入 localStorage
```

---

## 6. 路由（router/）规范

### 6.1 路由配置
```typescript
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', requiresAuth: false, hideHeader: true }
  },
  {
    path: '/',
    component: () => import('@/layouts/AppLayout.vue'),
    redirect: '/overview',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'overview',
        name: 'Overview',
        component: () => import('@/views/overview/index.vue'),
        meta: { title: '总体态势分析', icon: 'DashboardOutlined' }
      }
    ]
  }
]
```

### 6.2 路由懒加载
- 所有页面组件必须使用懒加载：`() => import('@/views/xxx/index.vue')`

### 6.3 路由元信息（meta）
| 字段 | 说明 |
|------|------|
| `title` | 页面标题 |
| `icon` | Ant Design Vue 图标名 |
| `requiresAuth` | 是否需要登录（默认 true） |
| `requiresAdmin` | 是否需要管理员权限 |
| `hidden` | 是否在导航菜单隐藏 |
| `hideHeader` | 是否隐藏顶部导航栏 |

### 6.4 路由守卫
- `router.beforeEach` 检查 `requiresAuth` 和 `isAuthenticated()`
- 未登录自动跳转 `/login`，已登录访问登录页自动跳转首页

---

## 7. 组件规范

### 7.1 SFC 结构
```vue
<template>
  <div class="xxx-container">...</div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useUserStore } from '@/stores/user'
// 导入顺序：vue > 第三方库 > 项目内部
</script>

<style scoped lang="less">
.xxx-container { ... }
</style>
```

### 7.2 组件命名
- 文件名：PascalCase（如 `TopStatsBar.vue`, `DataModal.vue`）
- 引用时保持 PascalCase

### 7.3 Props / Emits
- 使用类型安全的 defineProps / defineEmits
- 优先使用 `v-model:open` 控制弹窗显隐

### 7.4 样式规范
- 页面级组件：`scoped lang="less"`
- 全局样式覆盖：使用 `:deep()` 穿透
- 滚动条统一在 `AppLayout.vue` 中定义
- CSS 变量：在 `styles/global.css` 中定义主题色（如 `--bg-page`）

### 7.5 Ant Design Vue 使用
- 组件按需全局注册（`app.use(Antd)`）
- 图标单独导入：`import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'`
- 消息提示：使用 `message.success/error/warning/info()`
- 表单验证：使用 `a-form` 的 `:rules` + `@finish`
- 日期选择器：配合 `dayjs` 使用

---

## 8. 类型系统规范

### 8.1 类型文件
- 通用类型放在 `types/` 目录下，使用 `.d.ts` 扩展名
- 关键类型：
  ```typescript
  // types/api.d.ts
  export interface ApiResponse<T = any> {
    code: number
    message: string
    data: T
  }

  export interface PageParams {
    page: number
    pageSize: number
    [key: string]: any
  }

  export interface PageData<T = any> {
    list: T[]
    total: number
    page: number
    pageSize: number
  }
  ```

### 8.2 字段命名
- **前端类型定义使用 camelCase**：`userId`, `realName`, `createdAt`
- 注意：后端接口部分字段仍为 snake_case（如 `event_title`），API 层不做转换，类型定义需与后端实际返回保持一致

### 8.3 类型导出
- 所有类型必须显式导出：`export interface`
- 在 api 文件中同时导出 Form/Params 类型，供页面组件使用

---

## 9. 权限与访问控制规范

### 9.1 权限检查 Composable
```typescript
import { usePermission } from '@/composables/usePermission'

const { hasPermission } = usePermission()
hasPermission('risk_event:view')           // OR 模式（默认）
hasPermission(['admin:users:read', 'admin:users:write'], 'AND')
```

### 9.2 权限指令
```vue
<button v-permission="'risk_event:delete'">删除</button>
<button v-permission:and="['admin:read', 'admin:write']">管理</button>
```
- 无权限时元素会被隐藏（`display: none`）
- 超级管理员 `*:*` 拥有所有权限

### 9.3 路由权限
- `meta.requiresAdmin` 标记管理员专属页面
- 前端路由守卫只做登录检查，细粒度权限由后端接口控制

---

## 10. 字典数据管理规范

### 10.1 字典加载策略
- **单例模式**：`useDictionary()` composable 内部使用模块级全局 ref
- **懒加载**：首次使用时加载，通过 `loadedStates` 防止重复请求
- **并发控制**：通过 `loadingStates` 防止同一字典并发加载

### 10.2 字典缓存
- 登录成功后批量拉取常用字典并写入 `localStorage`
- Storage Key：`app_dict_cache`
- 登出时清除字典缓存

### 10.3 兜底映射（关键）
- 字典数据可能未落库或旧数据使用英文编码
- 必须在计算属性中提供 **legacy fallback 映射**，确保任何情况下都能显示中文：
  ```typescript
  const disposalStatusMap = computed(() => {
    const map: Record<string, DictionaryItem> = {}
    // 1. 先写入兜底数据
    const legacyFallback = {
      pending: { item_name: '待审核', color: '#faad14' },
      processing: { item_name: '处置中', color: '#4096ff' },
      // ...
    }
    // 2. 字典实际数据覆盖兜底（优先级更高）
    disposalStatus.value.forEach(item => { map[item.item_code] = item })
    return map
  })
  ```

### 10.4 常用字典类型
- `risk_level`：风险等级
- `disposal_status`：处置状态
- `event_type`：事件类型
- `person_type`：人员类型
- `person_manage_status`：人员管控状态

---

## 11. 代码风格与命名约定

### 11.1 命名规范
| 类型 | 规范 | 示例 |
|------|------|------|
| 组件名 | PascalCase | `TopStatsBar.vue`, `DataModal.vue` |
| 组合式函数 | camelCase，use 前缀 | `useDictionary`, `usePermission` |
| 变量/函数 | camelCase | `getUserInfo`, `loading` |
| 常量 | UPPER_CASE | `BASE_URL`, `TOKEN_KEY` |
| 类型/接口 | PascalCase | `UserInfo`, `ApiResponse` |
| 文件/目录 | camelCase 或 kebab-case | `useDictionary.ts`, `ai-assistant/` |

### 11.2 注释规范
- 所有 API 函数必须有中文 JSDoc 注释
- 复杂逻辑必须有中文行注释
- Composable 文件顶部必须有模块说明注释

### 11.3 导入顺序
```typescript
// 1. Vue 核心
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

// 2. 第三方库
import { message } from 'ant-design-vue'
import { UserOutlined } from '@ant-design/icons-vue'

// 3. 项目内部（按类别分组）
import { useUserStore } from '@/stores/user'
import { getUserInfo } from '@/api/auth'
import type { UserInfo } from '@/types/user'
```

### 11.4 字符串格式化
- 优先使用模板字符串：`` `url/${id}` ``
- API URL 使用常量拼接：`${BASE_URL}/login`

---

## 12. 异常处理规范

### 12.1 API 错误
- 由 `request.ts` 拦截器统一处理 HTTP 错误并弹窗提示
- 业务层只需处理业务逻辑错误（如 `if (res.code !== 0)`）

### 12.2 业务错误
```typescript
try {
  await userStore.login(username, password)
  message.success('登录成功')
} catch (error: any) {
  message.error(error.message || '登录失败')
}
```

### 12.3 异步函数
- async/await 为主，禁止使用回调地狱
- 并行请求使用 `Promise.all()`

---

## 13. 性能优化最佳实践

### 13.1 组件加载
- 页面组件必须使用路由懒加载
- 大型弹窗/子组件可考虑异步导入

### 13.2 数据加载
- 字典数据全局单例缓存，避免重复请求
- 列表分页加载，避免一次性加载大量数据
- 使用 `loading` 状态控制按钮/表格的加载动画

### 13.3 响应式优化
- 大数据列表使用虚拟滚动（Ant Design Vue Table 自带）
- 避免在模板中直接调用函数（使用 computed 缓存）

### 13.4 图表渲染
- ECharts 实例在组件卸载时销毁
- 大数据量图表启用 `animation: false`

---

## 14. 构建与部署

### 14.1 构建命令
```bash
pnpm dev          # 开发环境
pnpm dev:daily    # 日常环境
pnpm build        # 生产构建（vue-tsc + vite build）
pnpm build:daily  # 日常构建
```

### 14.2 环境变量
- `.env.local`：本地开发
- `.env.daily`：日常环境
- `.env.production`：生产环境
- 前缀必须为 `VITE_` 才能在客户端代码中使用

### 14.3 代理配置
- 开发环境通过 `vite.config.ts` 配置代理转发到后端

---

## 附录：常用代码模板

### A.1 新增 API 模块模板
```typescript
/**
 * XXX模块API
 */
import request from '@/utils/request'

const BASE_URL = '/api/v1/xxx'

export interface XxxForm {
  name: string
  description?: string
}

export function getXxxList(params: { page?: number; pageSize?: number }) {
  return request.get(`${BASE_URL}/list`, { params })
}

export function createXxx(data: XxxForm) {
  return request.post(`${BASE_URL}`, data)
}

export function updateXxx(id: string, data: XxxForm) {
  return request.put(`${BASE_URL}/${id}`, data)
}

export function deleteXxx(id: string) {
  return request.delete(`${BASE_URL}/${id}`)
}
```

### A.2 新增页面组件模板
```vue
<template>
  <div class="xxx-page">
    <a-card title="页面标题">
      <!-- 内容区 -->
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getXxxList } from '@/api/xxx'

const loading = ref(false)
const dataList = ref<any[]>([])

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getXxxList({ page: 1, pageSize: 20 })
    dataList.value = res.data || []
  } catch (e: any) {
    message.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped lang="less">
.xxx-page {
  padding: 16px;
}
</style>
```

### A.3 新增 Store 模板
```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useXxxStore = defineStore('xxx', () => {
  const data = ref<any[]>([])
  const loading = ref(false)

  async function fetchData() {
    loading.value = true
    try {
      // ...
    } finally {
      loading.value = false
    }
  }

  return { data, loading, fetchData }
})
```

### A.4 新增 Composable 模板
```typescript
/**
 * XXX Composable
 */
import { ref } from 'vue'

export function useXxx() {
  const state = ref('')

  const doSomething = () => {
    // ...
  }

  return { state, doSomething }
}
```
