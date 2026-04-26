// eslint-disable-next-line
import { UserLayout, BasicLayout, BlankLayout, RouteView } from '@/layouts'

export const asyncRouterMap = [
  {
    path: '/',
    name: 'index',
    component: BasicLayout,
    meta: { title: 'menu.home' },
    redirect: '/ai-asset-analysis',
    children: [
      // ========== 手风琴菜单：分析工具（第一位）==========
      {
        path: '/analysis-tools',
        name: 'AnalysisTools',
        component: RouteView,
        meta: {
          title: 'menu.analysisTools',
          icon: 'cluster',
          permission: ['dashboard']
        },
        redirect: '/ai-asset-analysis',
        children: [
          // AI资产分析
          {
            path: '/ai-asset-analysis',
            name: 'AIAssetAnalysis',
            component: () => import('@/views/ai-asset-analysis'),
            meta: { title: 'menu.dashboard.aiAssetAnalysis', keepAlive: false, icon: 'appstore', permission: ['dashboard'] }
          },
          // 知识图谱分析
          {
            path: '/graph-analysis',
            name: 'GraphAnalysis',
            component: () => import('@/views/graph-analysis'),
            meta: { title: 'menu.graphAnalysis', keepAlive: false, icon: 'cluster', permission: ['dashboard'] }
          }
        ]
      },
      // 指标 IDE（独立）
      {
        path: '/indicator-ide',
        name: 'IndicatorIDE',
        component: () => import('@/views/indicator-ide'),
        meta: { title: 'menu.dashboard.indicatorIde', keepAlive: true, icon: 'code', permission: ['dashboard'] }
      },
      // ========== 手风琴菜单：交易工具 ==========
      {
        path: '/trading-tools',
        name: 'TradingTools',
        component: RouteView,
        meta: {
          title: 'menu.tradingTools',
          icon: 'dollar',
          permission: ['dashboard']
        },
        redirect: '/trading-bot',
        children: [
          // 交易机器人
          {
            path: '/trading-bot',
            name: 'TradingBot',
            component: () => import('@/views/trading-bot'),
            meta: { title: 'menu.dashboard.tradingBot', keepAlive: true, icon: 'robot', permission: ['dashboard'] }
          },
          // 策略与实盘
          {
            path: '/strategy-live',
            name: 'StrategyLive',
            component: () => import('@/views/trading-assistant'),
            meta: {
              title: 'menu.dashboard.tradingAssistant',
              keepAlive: true,
              icon: 'deployment-unit',
              permission: ['dashboard'],
              indicatorSignalOnly: true
            }
          }
        ]
      },
      // Python 脚本策略（无侧栏入口，从「交易机器人」进入）
      {
        path: '/strategy-script',
        name: 'StrategyScript',
        component: () => import('@/views/trading-assistant'),
        hidden: true,
        meta: {
          title: 'menu.dashboard.tradingBot',
          keepAlive: false,
          scriptStrategiesOnly: true
        }
      },
      {
        path: '/strategy-scripts',
        redirect: '/strategy-live',
        hidden: true
      },
      // 旧路由兼容：图表与指标 → 指标 IDE
      {
        path: '/indicator-analysis',
        name: 'Indicator',
        redirect: '/indicator-ide',
        hidden: true,
        meta: { title: 'menu.dashboard.indicator', keepAlive: false, icon: 'line-chart', permission: ['dashboard'] }
      },
      // 旧路由兼容：回测中心 → 指标 IDE
      {
        path: '/backtest-center',
        name: 'BacktestCenter',
        redirect: '/indicator-ide',
        hidden: true,
        meta: { title: 'menu.dashboard.backtestCenter', keepAlive: false, icon: 'experiment', permission: ['dashboard'] }
      },
      // 旧路由兼容：交易助手 → 策略与实盘
      {
        path: '/trading-assistant',
        name: 'TradingAssistant',
        redirect: '/strategy-live',
        hidden: true,
        meta: { title: 'menu.dashboard.tradingAssistant', keepAlive: false, icon: 'deployment-unit', permission: ['dashboard'] }
      },
      // 原仪表盘路由保留兼容，重定向到交易机器人
      {
        path: '/dashboard',
        name: 'Dashboard',
        redirect: '/trading-bot',
        hidden: true,
        meta: { title: 'menu.dashboard', keepAlive: false, icon: 'dashboard', permission: ['dashboard'] }
      },
      // AI 分析（隐藏）
      {
        path: '/ai-analysis/:pageNo([1-9]\\d*)?',
        name: 'Analysis',
        component: () => import('@/views/ai-analysis'),
        hidden: true,
        meta: { title: 'menu.dashboard.analysis', keepAlive: false, icon: 'thunderbolt', permission: ['dashboard'] }
      },
      // 资产监测（隐藏）
      {
        path: '/portfolio',
        name: 'Portfolio',
        component: () => import('@/views/portfolio'),
        hidden: true,
        meta: { title: 'menu.dashboard.portfolio', keepAlive: true, icon: 'fund', permission: ['dashboard'] }
      },
      // ========== 手风琴菜单：AI 配置 ==========
      {
        path: '/ai-config',
        name: 'AIConfig',
        component: RouteView,
        meta: {
          title: 'menu.aiConfig',
          icon: 'api',
          permission: ['dashboard']
        },
        redirect: '/llm-settings',
        children: [
          // LLM 设置
          {
            path: '/llm-settings',
            name: 'LLMSettings',
            component: () => import('@/views/llm'),
            meta: { title: 'menu.llmSettings', keepAlive: false, icon: 'api', permission: ['dashboard'] }
          },
          // Dify 工作流管理
          {
            path: '/dify-workflow',
            name: 'DifyWorkflow',
            component: () => import('@/views/dify-workflow'),
            meta: { title: 'menu.difyWorkflow', keepAlive: false, icon: 'robot', permission: ['dashboard'] }
          }
        ]
      },
      // ========== 手风琴菜单：数据工具 ==========
      {
        path: '/data-tools',
        name: 'DataTools',
        component: RouteView,
        meta: {
          title: 'menu.dataTools',
          icon: 'database',
          permission: ['dashboard']
        },
        redirect: '/indicator-community',
        children: [
          // 指标市场
          {
            path: '/indicator-community',
            name: 'IndicatorCommunity',
            component: () => import('@/views/indicator-community'),
            meta: { title: 'menu.dashboard.community', keepAlive: false, icon: 'shop', permission: ['dashboard'] }
          },
          // 数据源管理 (admin only)
          {
            path: '/data-source',
            name: 'DataSource',
            component: () => import('@/views/data-source'),
            meta: { title: 'menu.dataSource', keepAlive: false, icon: 'database', permission: ['admin'] }
          }
        ]
      },
      // ========== 手风琴菜单：系统管理 ==========
      {
        path: '/system',
        name: 'System',
        component: RouteView,
        meta: {
          title: 'menu.system',
          icon: 'setting',
          permission: ['admin']
        },
        redirect: '/user-manage',
        children: [
          // 用户管理 (admin only)
          {
            path: '/user-manage',
            name: 'UserManage',
            component: () => import('@/views/user-manage'),
            meta: { title: 'menu.userManage', keepAlive: false, icon: 'team', permission: ['admin'] }
          },
          // 角色管理 (admin only)
          {
            path: '/role-manage',
            name: 'RoleManage',
            component: () => import('@/views/role-manage'),
            meta: { title: 'menu.roleManage', keepAlive: false, icon: 'safety', permission: ['admin'] }
          },
          // 权限管理 (admin only)
          {
            path: '/permission-manage',
            name: 'PermissionManage',
            component: () => import('@/views/permission-manage'),
            meta: { title: 'menu.permissionManage', keepAlive: false, icon: 'lock', permission: ['admin'] }
          },
          // 系统设置 (admin only)
          {
            path: '/settings',
            name: 'Settings',
            component: () => import('@/views/settings'),
            meta: { title: 'menu.settings', keepAlive: false, icon: 'setting', permission: ['admin'] }
          }
        ]
      },
      // 个人中心
      {
        path: '/profile',
        name: 'Profile',
        component: () => import('@/views/profile'),
        meta: { title: 'menu.myProfile', keepAlive: false, icon: 'user', permission: ['dashboard'] }
      },
      // 会员/充值
      {
        path: '/billing',
        name: 'Billing',
        component: () => import('@/views/billing'),
        meta: { title: 'menu.billing', keepAlive: false, icon: 'wallet', permission: ['dashboard'] }
      }

      // other
      /*
      {
        path: '/other',
        name: 'otherPage',
        component: PageView,
        meta: { title: '其他组件', icon: 'slack', permission: [ 'dashboard' ] },
        redirect: '/other/icon-selector',
        children: [
          {
            path: '/other/icon-selector',
            name: 'TestIconSelect',
            component: () => import('@/views/other/IconSelectorView'),
            meta: { title: 'IconSelector', icon: 'tool', keepAlive: true, permission: [ 'dashboard' ] }
          },
          {
            path: '/other/list',
            component: RouteView,
            meta: { title: '业务布局', icon: 'layout', permission: [ 'support' ] },
            redirect: '/other/list/tree-list',
            children: [
              {
                path: '/other/list/tree-list',
                name: 'TreeList',
                component: () => import('@/views/other/TreeList'),
                meta: { title: '树目录表格', keepAlive: true }
              },
              {
                path: '/other/list/edit-table',
                name: 'EditList',
                component: () => import('@/views/other/TableInnerEditList'),
                meta: { title: '内联编辑表格', keepAlive: true }
              },
              {
                path: '/other/list/user-list',
                name: 'UserList',
                component: () => import('@/views/other/UserList'),
                meta: { title: '用户列表', keepAlive: true }
              },
              {
                path: '/other/list/role-list',
                name: 'RoleList',
                component: () => import('@/views/other/RoleList'),
                meta: { title: '角色列表', keepAlive: true }
              },
              {
                path: '/other/list/system-role',
                name: 'SystemRole',
                component: () => import('@/views/role/RoleList'),
                meta: { title: '角色列表2', keepAlive: true }
              },
              {
                path: '/other/list/permission-list',
                name: 'PermissionList',
                component: () => import('@/views/other/PermissionList'),
                meta: { title: '权限列表', keepAlive: true }
              }
            ]
          }
        ]
      }
      */
    ]
  },
  {
    path: '*',
    redirect: '/404',
    hidden: true
  }
]

/**
 * 基础路由
 * @type { *[] }
 */
export const constantRouterMap = [
  {
    path: '/user',
    component: UserLayout,
    redirect: '/user/login',
    hidden: true,
    children: [
      {
        path: 'login',
        name: 'login',
        component: () => import(/* webpackChunkName: "user" */ '@/views/user/Login')
      }
    ]
  },

  {
    path: '/404',
    component: () => import(/* webpackChunkName: "fail" */ '@/views/exception/404')
  }
]
