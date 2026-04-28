/**
 * 主题管理工具
 * Theme Management Utility
 */

export type ThemeType = 'light' | 'dark' | 'realdark' | 'skyblue' | 'xp'

const themeStyles: Partial<Record<ThemeType, string>> = {
  skyblue: `
    /* 天空蓝极简主题 - 渐变浅蓝风格 */
    body.skyblue .ant-layout-sider {
      background: linear-gradient(180deg, #F0F7FC 0%, #B8D8F0 100%) !important;
      border-right: 1px solid #A8CCE8 !important;
    }
    
    body.skyblue .logo-container {
      background: linear-gradient(180deg, #87CEEB 0%, #5CACEE 100%) !important;
      border-bottom: 1px solid #4A9ED8 !important;
    }
    
    body.skyblue .ant-menu {
      background: transparent !important;
    }
    
    body.skyblue .ant-menu-item:hover {
      background: linear-gradient(180deg, #E0F0FA 0%, #D0E8F5 100%) !important;
      color: #4A9ED8 !important;
    }
    
    body.skyblue .ant-menu-item-selected {
      background: linear-gradient(180deg, #87CEEB 0%, #5CACEE 100%) !important;
      color: #fff !important;
    }
    
    body.skyblue .app-header {
      background: linear-gradient(180deg, #C8E4F8 0%, #B8D8F0 100%) !important;
      border-bottom: 1px solid #A8CCE8 !important;
    }
    
    body.skyblue .ant-card {
      background: #FFFFFF !important;
      border: 1px solid #A8CCE8 !important;
      border-radius: 8px !important;
    }
    
    body.skyblue .ant-card-head {
      background: linear-gradient(180deg, #87CEEB 0%, #5CACEE 100%) !important;
      color: #FFFFFF !important;
    }
    
    body.skyblue .ant-btn-primary {
      background: linear-gradient(180deg, #87CEEB 0%, #5CACEE 100%) !important;
      border-color: #5CACEE !important;
    }
  `,

  xp: `
    /* Windows XP 经典主题 */
    body.xp .ant-layout-sider {
      background: linear-gradient(180deg, #ECE9D8 0%, #DDD8C8 100%) !important;
      border-right: 2px solid #C4C0B8 !important;
    }
    
    body.xp .logo-container {
      background: linear-gradient(180deg, #0973DF 0%, #0054E3 100%) !important;
      border-bottom: 2px solid #003087 !important;
    }
    
    body.xp .ant-menu-item:hover,
    body.xp .ant-menu-item-selected {
      background: linear-gradient(180deg, #316AC5 0%, #1F5BB8 100%) !important;
      color: #FFFFFF !important;
      border-radius: 0 !important;
    }
    
    body.xp .app-header {
      background: linear-gradient(180deg, #0973DF 0%, #0054E3 100%) !important;
      border-bottom: 2px solid #003087 !important;
    }
    
    body.xp .ant-card {
      background: #E8EDF5 !important;
      border: 1px solid #C4C0B8 !important;
      border-radius: 0 !important;
    }
    
    body.xp .ant-card-head {
      background: linear-gradient(180deg, #1A5CB8 0%, #0D4590 100%) !important;
      color: #FFFFFF !important;
    }
    
    body.xp .ant-btn-primary {
      background: linear-gradient(180deg, #316AC5 0%, #1F5BB8 100%) !important;
      border-color: #0D328F !important;
      border-radius: 0 !important;
    }
  `
}

const injectedStyleId = 'qd-custom-theme-styles'

export function injectThemeStyles(theme: ThemeType) {
  removeThemeStyles()

  const style = themeStyles[theme]
  if (!style) return

  const styleElement = document.createElement('style')
  styleElement.id = injectedStyleId
  styleElement.textContent = style
  document.head.appendChild(styleElement)
}

export function removeThemeStyles() {
  const existingStyle = document.getElementById(injectedStyleId)
  if (existingStyle) {
    existingStyle.remove()
  }
}

export function switchTheme(theme: ThemeType) {
  // Update body class
  document.body.classList.remove('light', 'dark', 'realdark', 'skyblue', 'xp')
  document.body.classList.add(theme)
  
  // Inject custom styles if necessary
  injectThemeStyles(theme)
}

export default {
  injectThemeStyles,
  removeThemeStyles,
  switchTheme
}
