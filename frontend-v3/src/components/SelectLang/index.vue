<template>
  <a-dropdown placement="bottomRight">
    <span class="header-action-item">
      <GlobalOutlined :title="$t('navBar.lang')" />
    </span>
    <template #overlay>
      <a-menu :selected-keys="[currentLang]" @click="handleLangClick">
        <a-menu-item v-for="locale in locales" :key="locale.key">
          <span role="img" :aria-label="locale.label" class="lang-icon">
            {{ locale.icon }}
          </span>
          {{ locale.label }}
        </a-menu-item>
      </a-menu>
    </template>
  </a-dropdown>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { GlobalOutlined } from '@ant-design/icons-vue'
import { type LocaleCode } from '@/locales'
import { useAppStore } from '@/stores/app'

const { locale } = useI18n()
const appStore = useAppStore()

const locales = [
  { key: 'zh-CN', label: '简体中文', icon: '🇨🇳' },
  { key: 'en-US', label: 'English', icon: '🇺🇸' },
  { key: 'ja-JP', label: '日本語', icon: '🇯🇵' },
  { key: 'ko-KR', label: '한국어', icon: '🇰🇷' },
  { key: 'vi-VN', label: 'Tiếng Việt', icon: '🇻🇳' },
  { key: 'th-TH', label: 'ภาษาไทย', icon: '🇹🇭' },
  { key: 'ar-SA', label: 'العربية', icon: '🇸🇦' },
  { key: 'fr-FR', label: 'Français', icon: '🇫🇷' },
  { key: 'de-DE', label: 'Deutsch', icon: '🇩🇪' },
  { key: 'zh-TW', label: '繁體中文', icon: '🇭🇰' },
]

const currentLang = computed(() => locale.value)

const handleLangClick = ({ key }: { key: string }) => {
  const nextLocale = key as LocaleCode
  // Update vue-i18n locale
  locale.value = nextLocale
  // Update app store and persistent storage
  appStore.setLanguage(nextLocale)
  
  // Force update if needed (though locale.value should be reactive)
  console.log('Language changed to:', nextLocale)
}
</script>

<style scoped lang="less">
.header-action-item {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 64px;
  padding: 0 12px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 18px;
  color: rgba(0, 0, 0, 0.45);

  &:hover {
    background: rgba(0, 0, 0, 0.025);
    color: #1890ff;
  }
}

.lang-icon {
  margin-right: 8px;
}

:deep(.ant-dropdown-trigger) {
  display: inline-block;
}

.dark, .realdark {
  .header-action-item {
    color: rgba(255, 255, 255, 0.85);
    
    &:hover {
      background: rgba(255, 255, 255, 0.05);
    }
  }
}
</style>
