<template>
  <a-config-provider :locale="antdLocale">
    <router-view />
  </a-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import zhCN from 'ant-design-vue/es/locale/zh_CN'
import enUS from 'ant-design-vue/es/locale/en_US'
import jaJP from 'ant-design-vue/es/locale/ja_JP'
import koKR from 'ant-design-vue/es/locale/ko_KR'
import viVN from 'ant-design-vue/es/locale/vi_VN'
import thTH from 'ant-design-vue/es/locale/th_TH'
import arEG from 'ant-design-vue/es/locale/ar_EG'
import frFR from 'ant-design-vue/es/locale/fr_FR'
import deDE from 'ant-design-vue/es/locale/de_DE'
import zhTW from 'ant-design-vue/es/locale/zh_TW'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

const antdLocale = computed(() => {
  switch (appStore.lang) {
    case 'zh-CN': return zhCN
    case 'en-US': return enUS
    case 'ja-JP': return jaJP
    case 'ko-KR': return koKR
    case 'vi-VN': return viVN
    case 'th-TH': return thTH
    case 'ar-SA': return arEG
    case 'fr-FR': return frFR
    case 'de-DE': return deDE
    case 'zh-TW': return zhTW
    default: return zhCN
  }
})
</script>
