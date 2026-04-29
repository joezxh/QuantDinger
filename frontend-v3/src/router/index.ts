import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { isAuthenticated } from '@/utils/request'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: 'user.login.title', requiresAuth: false, hideHeader: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/AppLayout.vue'),
    redirect: '/ai-asset-analysis',
    meta: { requiresAuth: true },
    children: [
      // --- Core AI & Analysis ---
      {
        path: 'ai-asset-analysis',
        name: 'AIAssetAnalysis',
        component: () => import('@/views/ai-asset-analysis/index.vue'),
        meta: { title: 'menu.aiAssetAnalysis', icon: 'RobotOutlined' },
      },
      {
        path: 'ai-analysis',
        name: 'AIAnalysis',
        component: () => import('@/views/ai-analysis/index.vue'),
        meta: { title: 'menu.aiAnalysis', icon: 'ExperimentOutlined' },
      },
      {
        path: 'graph-analysis',
        name: 'GraphAnalysis',
        component: () => import('@/views/graph-analysis/index.vue'),
        meta: { title: 'menu.graphAnalysis', icon: 'ClusterOutlined' },
      },
      {
        path: 'dify-workflow',
        name: 'DifyWorkflow',
        component: () => import('@/views/dify-workflow/index.vue'),
        meta: { title: 'menu.difyWorkflow', icon: 'ApiOutlined', requiresAdmin: true },
      },

      // --- Trading & Bot ---
      {
        path: 'trading-bot',
        name: 'TradingBot',
        component: () => import('@/views/trading-bot/index.vue'),
        meta: { title: 'menu.tradingBot', icon: 'ThunderboltOutlined' },
      },
      {
        path: 'strategy-live',
        name: 'StrategyLive',
        component: () => import('@/views/strategy-live/index.vue'),
        meta: { title: 'menu.strategyLive', icon: 'SwapOutlined' },
      },
      {
        path: 'trading-assistant',
        name: 'TradingAssistant',
        component: () => import('@/views/trading-assistant/index.vue'),
        meta: { title: 'menu.tradingAssistant', icon: 'RobotOutlined' },
      },

      // --- Indicators ---
      {
        path: 'indicator-ide',
        name: 'IndicatorIDE',
        component: () => import('@/views/indicator-ide/index.vue'),
        meta: { title: 'menu.indicatorIde', icon: 'CodeOutlined' },
      },
      {
        path: 'indicator-community',
        name: 'IndicatorCommunity',
        component: () => import('@/views/indicator-community/index.vue'),
        meta: { title: 'menu.indicatorMarket', icon: 'ShopOutlined' },
      },

      // --- Data & Portfolio ---
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: 'menu.dashboard', icon: 'DashboardOutlined' },
      },
      {
        path: 'portfolio',
        name: 'Portfolio',
        component: () => import('@/views/portfolio/index.vue'),
        meta: { title: 'menu.portfolio', icon: 'FundOutlined' },
      },
      {
        path: 'data-source',
        name: 'DataSource',
        component: () => import('@/views/data-source/index.vue'),
        meta: { title: 'menu.dataSource', icon: 'DatabaseOutlined', requiresAdmin: true },
      },

      // --- System & Management ---
      {
        path: 'llm',
        name: 'LLMManage',
        component: () => import('@/views/llm/index.vue'),
        meta: { title: 'menu.llm', icon: 'RobotOutlined', requiresAdmin: true },
      },
      {
        path: 'user-manage',
        name: 'UserManage',
        component: () => import('@/views/user-manage/index.vue'),
        meta: { title: 'menu.userManage', icon: 'UserOutlined', requiresAdmin: true },
      },
      {
        path: 'role-manage',
        name: 'RoleManage',
        component: () => import('@/views/role-manage/index.vue'),
        meta: { title: 'menu.roleManage', icon: 'TeamOutlined', requiresAdmin: true },
      },
      {
        path: 'permission-manage',
        name: 'PermissionManage',
        component: () => import('@/views/permission-manage/index.vue'),
        meta: { title: 'menu.permissionManage', icon: 'LockOutlined', requiresAdmin: true },
      },
      {
        path: 'menu-manage',
        name: 'MenuManage',
        component: () => import('@/views/menu-manage/index.vue'),
        meta: { title: 'menu.menuManage', icon: 'MenuOutlined', requiresAdmin: true },
      },
      {
        path: 'billing',
        name: 'Billing',
        component: () => import('@/views/billing/index.vue'),
        meta: { title: 'menu.billing', icon: 'WalletOutlined' },
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/index.vue'),
        meta: { title: 'menu.profile', icon: 'UserOutlined' },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/index.vue'),
        meta: { title: 'menu.settings', icon: 'SettingOutlined' },
      },
    ],
  },
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('@/views/exception/403.vue'),
    meta: { title: '403', requiresAuth: false },
  },
  {
    path: '/500',
    name: 'ServerError',
    component: () => import('@/views/exception/500.vue'),
    meta: { title: '500', requiresAuth: false },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/exception/404.vue'),
    meta: { title: '404' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

/**
 * Global navigation guard
 */
router.beforeEach((to, _from, next) => {
  const requiresAuth = to.meta.requiresAuth !== false

  if (requiresAuth && !isAuthenticated()) {
    next({
      path: '/login',
      query: { redirect: to.fullPath },
    })
    return
  }

  // Redirect to home if already logged in and visiting login
  if (to.path === '/login' && isAuthenticated()) {
    next({ path: '/' })
    return
  }

  next()
})

export default router
