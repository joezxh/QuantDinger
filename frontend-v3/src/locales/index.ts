import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN'
import enUS from './en-US'
import jaJP from './ja-JP'
import koKR from './ko-KR'
import viVN from './vi-VN'
import thTH from './th-TH'
import arSA from './ar-SA'
import frFR from './fr-FR'
import deDE from './de-DE'
import zhTW from './zh-TW'

export type LocaleCode = 
  | 'zh-CN' | 'en-US' | 'ja-JP' | 'ko-KR' 
  | 'vi-VN' | 'th-TH' | 'ar-SA' | 'fr-FR' 
  | 'de-DE' | 'zh-TW'

const LOCALE_KEY = 'app_locale'

export function getStoredLocale(): LocaleCode {
  return (localStorage.getItem(LOCALE_KEY) as LocaleCode) || 'zh-CN'
}

export function setStoredLocale(locale: LocaleCode) {
  localStorage.setItem(LOCALE_KEY, locale)
}

const i18n = createI18n({
  legacy: false,
  locale: getStoredLocale(),
  fallbackLocale: 'zh-CN',
  globalInjection: true,
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS,
    'ja-JP': jaJP,
    'ko-KR': koKR,
    'vi-VN': viVN,
    'th-TH': thTH,
    'ar-SA': arSA,
    'fr-FR': frFR,
    'de-DE': deDE,
    'zh-TW': zhTW,
  },
})

export default i18n
