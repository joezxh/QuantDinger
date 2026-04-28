import { defineStore } from 'pinia'
import { ref, h, type Component } from 'vue'
import * as Icons from '@ant-design/icons-vue'

export interface MenuItem {
  path: string
  label: string
  icon?: string | Component
  hidden?: boolean
  children?: MenuItem[]
  permission?: string[]
}

export const useMenuStore = defineStore('menu', () => {
  // Default menu structure from old version
  const defaultMenus: MenuItem[] = [
    {
      path: '/analysis-tools',
      label: 'menu.analysisTools',
      icon: 'ClusterOutlined',
      children: [
        { path: '/ai-asset-analysis', label: 'menu.aiAssetAnalysis', icon: 'AppstoreOutlined' },
        { path: '/graph-analysis', label: 'menu.graphAnalysis', icon: 'ClusterOutlined' },
      ],
    },
    {
      path: '/trading-tools',
      label: 'menu.tradingTools',
      icon: 'DollarOutlined',
      children: [
        { path: '/trading-bot', label: 'menu.tradingBot', icon: 'RobotOutlined' },
        { path: '/strategy-live', label: 'menu.strategyLive', icon: 'DeploymentUnitOutlined' },
      ],
    },
    {
      path: '/ai-config',
      label: 'menu.aiConfig',
      icon: 'ApiOutlined',
      children: [
        { path: '/llm', label: 'menu.llm', icon: 'ApiOutlined' },
        { path: '/dify-workflow', label: 'menu.difyWorkflow', icon: 'RobotOutlined' },
      ],
    },
    {
      path: '/data-tools',
      label: 'menu.dataTools',
      icon: 'DatabaseOutlined',
      children: [
        { path: '/indicator-ide', label: 'menu.indicatorIde', icon: 'CodeOutlined' },
        { path: '/indicator-community', label: 'menu.indicatorMarket', icon: 'ShopOutlined' },
        { path: '/data-source', label: 'menu.dataSource', icon: 'DatabaseOutlined' },
      ],
    },
    {
      path: '/system',
      label: 'menu.systemManage',
      icon: 'SettingOutlined',
      children: [
        { path: '/user-manage', label: 'menu.userManage', icon: 'TeamOutlined' },
        { path: '/role-manage', label: 'menu.roleManage', icon: 'SafetyOutlined' },
        { path: '/permission-manage', label: 'menu.permissionManage', icon: 'LockOutlined' },
        { path: '/menu-manage', label: 'menu.menuManage', icon: 'MenuOutlined' },
        { path: '/settings', label: 'menu.settings', icon: 'SettingOutlined' },
        { path: '/profile', label: 'menu.profile', icon: 'UserOutlined' },
        { path: '/billing', label: 'menu.billing', icon: 'WalletOutlined' },
      ],
    },
  ]

  const menus = ref<MenuItem[]>(JSON.parse(localStorage.getItem('custom_menus') || JSON.stringify(defaultMenus)))

  function saveMenus() {
    localStorage.setItem('custom_menus', JSON.stringify(menus.value))
  }

  function updateMenus(newMenus: MenuItem[]) {
    menus.value = newMenus
    saveMenus()
  }

  function resetMenus() {
    menus.value = JSON.parse(JSON.stringify(defaultMenus))
    saveMenus()
  }

  // Helper to get icon component by name
  function getIcon(name: string | Component | undefined): Component | null {
    if (!name) return null
    if (typeof name !== 'string') return name
    return (Icons as any)[name] || Icons.QuestionOutlined
  }

  return {
    menus,
    updateMenus,
    resetMenus,
    getIcon,
  }
})
