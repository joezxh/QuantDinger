/**
 * 主题管理工具
 * Theme Management Utility
 *
 * 用于管理特殊主题的动态注入和切换
 */

const themeStyles = {
  skyblue: `
    /* 天空蓝极简主题 - 渐变浅蓝风格 */
    body.skyblue .ant-layout-sider,
    body.skyblue .ant-pro-sider-menu-sider {
      background: linear-gradient(180deg, #F0F7FC 0%, #B8D8F0 100%) !important;
      border-right: 1px solid #A8CCE8 !important;
    }
    
    body.skyblue .ant-pro-sider-menu-logo {
      background: linear-gradient(180deg, #87CEEB 0%, #5CACEE 100%) !important;
      border-bottom: 1px solid #4A9ED8 !important;
    }
    
    body.skyblue .ant-menu-light .ant-menu-submenu-title {
      border-radius: 6px;
      margin: 4px 8px;
      padding-left: 16px !important;
      color: #5CACEE !important;
      font-weight: 600;
    }
    
    body.skyblue .ant-menu-light .ant-menu-item {
      border-radius: 6px;
      margin: 2px 8px;
      padding-left: 32px !important;
    }
    
    body.skyblue .ant-menu-light .ant-menu-item:hover {
      background: linear-gradient(180deg, #E0F0FA 0%, #D0E8F5 100%) !important;
      color: #4A9ED8 !important;
    }
    
    body.skyblue .ant-menu-light .ant-menu-item.ant-menu-item-selected,
    body.skyblue .ant-menu-light .ant-menu-item.ant-menu-submenu-selected {
      background: linear-gradient(180deg, #87CEEB 0%, #5CACEE 100%) !important;
      color: #fff !important;
    }
    
    body.skyblue .ant-layout-sider-trigger {
      background: linear-gradient(180deg, #B8D8F0 0%, #A8CCE8 100%) !important;
      color: #4A9ED8 !important;
    }
    
    body.skyblue .ant-layout-header,
    body.skyblue .ant-pro-global-header {
      background: linear-gradient(180deg, #C8E4F8 0%, #B8D8F0 100%) !important;
      border-bottom: 1px solid #A8CCE8 !important;
    }
    
    body.skyblue .ant-card {
      background: #FFFFFF !important;
      border: 1px solid #A8CCE8 !important;
      border-radius: 8px !important;
      box-shadow: 0 2px 8px rgba(92, 172, 238, 0.08) !important;
    }
    
    body.skyblue .ant-card-head {
      background: linear-gradient(180deg, #87CEEB 0%, #5CACEE 100%) !important;
      color: #FFFFFF !important;
      border-radius: 8px 8px 0 0;
    }
    
    body.skyblue .ant-table .ant-table-thead > tr > th {
      background: linear-gradient(180deg, #E8F4FC 0%, #D8EEF8 100%) !important;
      border-bottom: 2px solid #87CEEB !important;
    }
    
    body.skyblue .ant-btn-primary {
      background: linear-gradient(180deg, #87CEEB 0%, #5CACEE 100%) !important;
      border-color: #5CACEE !important;
      box-shadow: 0 2px 4px rgba(135, 206, 235, 0.3) !important;
    }
    
    body.skyblue .ant-input,
    body.skyblue .ant-input-number,
    body.skyblue .ant-select-selection {
      border-radius: 6px !important;
      border-color: #A8CCE8 !important;
    }
    
    body.skyblue .ant-modal-content {
      border-radius: 12px !important;
      overflow: hidden;
    }
    
    body.skyblue .ant-modal-header {
      background: linear-gradient(180deg, #87CEEB 0%, #5CACEE 100%) !important;
      border-radius: 12px 12px 0 0 !important;
    }
    
    body.skyblue .ant-modal-title {
      color: #FFFFFF !important;
    }
    
    body.skyblue .ant-modal-close {
      color: #FFFFFF !important;
    }
    
    body.skyblue .ant-drawer-header {
      background: linear-gradient(180deg, #87CEEB 0%, #5CACEE 100%) !important;
    }
    
    body.skyblue .ant-drawer-title {
      color: #FFFFFF !important;
    }
    
    body.skyblue .ant-drawer-close {
      color: #FFFFFF !important;
    }
    
    body.skyblue .ant-tabs-tab-active {
      background: linear-gradient(180deg, #87CEEB 0%, #5CACEE 100%) !important;
      color: #FFFFFF !important;
    }
    
    body.skyblue .ant-page-header {
      background: linear-gradient(180deg, #F8FCFE 0%, #F0F7FC 100%) !important;
      border-bottom: 2px solid #87CEEB !important;
    }
    
    body.skyblue .ant-page-header-heading-title {
      color: #5CACEE !important;
    }
    
    body.skyblue .ant-switch-checked {
      background: linear-gradient(180deg, #87CEEB 0%, #5CACEE 100%) !important;
    }
    
    body.skyblue .ant-tag-blue {
      background: linear-gradient(180deg, #87CEEB 0%, #5CACEE 100%) !important;
      color: #FFFFFF !important;
    }
  `,

  xp: `
    /* Windows XP 经典主题 - 内联样式 */
    body.xp .ant-layout-sider,
    body.xp .ant-pro-sider-menu-sider {
      background: linear-gradient(180deg, #ECE9D8 0%, #DDD8C8 100%) !important;
      border-right: 2px solid #C4C0B8 !important;
    }
    
    body.xp .ant-pro-sider-menu-logo {
      background: linear-gradient(180deg, #0973DF 0%, #0054E3 100%) !important;
      border-bottom: 2px solid #003087 !important;
    }
    
    body.xp .ant-menu-light .ant-menu-item {
      border-radius: 0;
      font-size: 12px;
    }
    
    body.xp .ant-menu-light .ant-menu-item:hover,
    body.xp .ant-menu-light .ant-menu-item.ant-menu-item-selected {
      background: linear-gradient(180deg, #316AC5 0%, #1F5BB8 100%) !important;
      color: #FFFFFF !important;
    }
    
    body.xp .ant-layout-header,
    body.xp .ant-pro-global-header {
      background: linear-gradient(180deg, #0973DF 0%, #0054E3 100%) !important;
      border-bottom: 2px solid #003087 !important;
    }
    
    body.xp .ant-card {
      background: #E8EDF5 !important;
      border: 1px solid #C4C0B8 !important;
      border-radius: 0 !important;
      box-shadow: 2px 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    body.xp .ant-card-head {
      background: linear-gradient(180deg, #1A5CB8 0%, #0D4590 100%) !important;
      color: #FFFFFF !important;
    }
    
    body.xp .ant-table {
      border: 1px solid #C4C0B8 !important;
    }
    
    body.xp .ant-table .ant-table-thead > tr > th {
      background: linear-gradient(180deg, #D8DFE8 0%, #C6D0E0 100%) !important;
      border-bottom: 2px solid #C4C0B8 !important;
    }
    
    body.xp .ant-table .ant-table-tbody > tr > td {
      background: #FFFFFF !important;
    }
    
    body.xp .ant-btn {
      border-radius: 0;
      font-size: 12px;
      background: linear-gradient(180deg, #FFFFFF 0%, #E8EDF5 50%, #C6D0E0 100%) !important;
      border: 1px solid;
      border-color: #FFFFFF #808080 #808080 #FFFFFF;
    }
    
    body.xp .ant-btn-primary {
      background: linear-gradient(180deg, #316AC5 0%, #1F5BB8 100%) !important;
      border-color: #0D328F !important;
      color: #FFFFFF !important;
    }
    
    body.xp .ant-modal-content {
      border: 1px solid #C4C0B8 !important;
      border-radius: 0 !important;
    }
    
    body.xp .ant-modal-header {
      background: linear-gradient(180deg, #0973DF 0%, #0054E3 100%) !important;
    }
    
    body.xp .ant-input,
    body.xp .ant-input-number,
    body.xp .ant-select-selection {
      border: 2px solid;
      border-color: #717171 #DFE3EB #DFE3EB #717171 !important;
      border-radius: 0 !important;
    }
  `
}

const injectedStyleId = 'qd-custom-theme-styles'
let injectedStyle = null

/**
 * 注入自定义主题样式
 * @param {string} theme - 主题名称 'skyblue' | 'xp'
 */
export function injectThemeStyles (theme) {
  // 移除之前的样式
  removeThemeStyles()

  // 如果不是特殊主题，不注入
  if (!themeStyles[theme]) {
    return
  }

  // 创建 style 元素
  injectedStyle = document.createElement('style')
  injectedStyle.id = injectedStyleId
  injectedStyle.textContent = themeStyles[theme]
  document.head.appendChild(injectedStyle)
}

/**
 * 移除已注入的主题样式
 */
export function removeThemeStyles () {
  const existingStyle = document.getElementById(injectedStyleId)
  if (existingStyle) {
    existingStyle.remove()
  }
  injectedStyle = null
}

/**
 * 初始化主题
 * @param {string} theme - 当前主题
 */
export function initTheme (theme) {
  injectThemeStyles(theme)
}

/**
 * 切换主题
 * @param {string} theme - 新主题名称
 */
export function switchTheme (theme) {
  injectThemeStyles(theme)
}

export default {
  injectThemeStyles,
  removeThemeStyles,
  initTheme,
  switchTheme
}
