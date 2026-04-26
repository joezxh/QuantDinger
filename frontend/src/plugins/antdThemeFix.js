/**
 * Ant Design / Pro-Layout Theme 扩展插件
 *
 * 自定义主题（skyblue/xp）通过 body 类名 + CSS 控制
 * 此插件主要用于主题切换时的样式注入
 */

import { injectThemeStyles, removeThemeStyles } from '@/utils/themeManager'

// 自定义主题列表
const customThemes = ['skyblue', 'xp', 'realSkyblue']

/**
 * 初始化主题扩展
 */
function init () {
  // 获取当前主题
  const savedTheme = localStorage.getItem('qd-theme') || 'skyblue'

  // 如果是自定义主题，注入对应样式
  if (customThemes.includes(savedTheme)) {
    injectThemeStyles(savedTheme)
  }
}

// 导出函数供外部调用
export { customThemes, injectThemeStyles, removeThemeStyles }

export default {
  install () {
    init()
  }
}
