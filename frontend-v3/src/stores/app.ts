import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getStoredLocale, setStoredLocale, type LocaleCode } from '@/locales'
import themeManager, { type ThemeType } from '@/utils/themeManager'

export const useAppStore = defineStore('app', () => {
  const theme = ref<ThemeType>((localStorage.getItem('app_theme') as ThemeType) || 'light')
  const collapsed = ref(false)
  const lang = ref<LocaleCode>(getStoredLocale())

  // Initialize theme on store creation
  themeManager.switchTheme(theme.value)

  function setTheme(t: ThemeType): void {
    theme.value = t
    localStorage.setItem('app_theme', t)
    themeManager.switchTheme(t)
  }

  function toggleCollapsed(): void {
    collapsed.value = !collapsed.value
  }

  function setLanguage(l: LocaleCode): void {
    lang.value = l
    setStoredLocale(l)
  }

  return {
    theme,
    collapsed,
    lang,
    setTheme,
    toggleCollapsed,
    setLanguage
  }
})
