<template>
  <div class="setting-drawer">
    <a-drawer
      v-model:visible="visible"
      width="300"
      placement="right"
      :closable="true"
      class="app-setting-drawer"
    >
      <div class="setting-content">
        <div class="setting-section">
          <h3 class="setting-title">{{ $t('app.setting.pagestyle') }}</h3>
          <div class="style-checkbox-list">
            <a-tooltip :title="$t('app.setting.pagestyle.light')">
              <div class="style-item" :class="{ active: localTheme === 'light' }" @click="localTheme = 'light'">
                <img src="https://gw.alipayobjects.com/zos/rmsportal/jpRkZQMyYRryryPNtyIC.svg" alt="light" />
                <CheckOutlined v-if="localTheme === 'light'" class="select-icon" />
              </div>
            </a-tooltip>
            
            <a-tooltip :title="$t('app.setting.pagestyle.dark')">
              <div class="style-item" :class="{ active: localTheme === 'dark' }" @click="localTheme = 'dark'">
                <img src="https://gw.alipayobjects.com/zos/rmsportal/LCkqqYNmvBEbokSDscrm.svg" alt="dark" />
                <CheckOutlined v-if="localTheme === 'dark'" class="select-icon" />
              </div>
            </a-tooltip>

            <a-tooltip :title="$t('app.setting.pagestyle.skyblue')">
              <div class="style-item skyblue" :class="{ active: localTheme === 'skyblue' }" @click="localTheme = 'skyblue'">
                <img src="https://gw.alipayobjects.com/zos/rmsportal/LCkqqYNmvBEbokSDscrm.svg" alt="skyblue" style="filter: hue-rotate(-10deg) saturate(0.8);" />
                <CheckOutlined v-if="localTheme === 'skyblue'" class="select-icon" />
              </div>
            </a-tooltip>

            <a-tooltip :title="$t('app.setting.pagestyle.xp')">
              <div class="style-item xp" :class="{ active: localTheme === 'xp' }" @click="localTheme = 'xp'">
                <img src="https://gw.alipayobjects.com/zos/rmsportal/jpRkZQMyYRryryPNtyIC.svg" alt="xp" style="filter: sepia(0.5) hue-rotate(-40deg);" />
                <CheckOutlined v-if="localTheme === 'xp'" class="select-icon" />
              </div>
            </a-tooltip>
          </div>
        </div>

        <a-divider />

        <div class="setting-section">
          <h3 class="setting-title">{{ $t('app.setting.themecolor') }}</h3>
          <div class="theme-color-list">
            <div
              v-for="color in colorList"
              :key="color.key"
              class="color-block"
              :style="{ backgroundColor: color.color }"
              @click="localPrimaryColor = color.color"
            >
              <CheckOutlined v-if="localPrimaryColor === color.color" />
            </div>
          </div>
        </div>

        <a-divider />

        <div class="setting-section">
          <h3 class="setting-title">{{ $t('app.setting.othersettings') }}</h3>
          <a-list :split="false">
            <a-list-item>
              <span>{{ $t('app.setting.weakmode') }}</span>
              <template #actions>
                <a-switch size="small" v-model:checked="localColorWeak" />
              </template>
            </a-list-item>
            <a-list-item>
              <span>{{ $t('app.setting.multitab') }}</span>
              <template #actions>
                <a-switch size="small" v-model:checked="localMultiTab" />
              </template>
            </a-list-item>
          </a-list>
        </div>

        <div class="apply-section">
          <a-button type="primary" block @click="handleApply">
            {{ $t('app.setting.apply') }}
          </a-button>
        </div>
      </div>

      <template #handle>
        <div class="drawer-handle" @click="visible = !visible">
          <SettingOutlined v-if="!visible" />
          <CloseOutlined v-else />
        </div>
      </template>
    </a-drawer>
    
    <span class="header-action-item" @click="openDrawer">
      <SettingOutlined />
    </span>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { SettingOutlined, CloseOutlined, CheckOutlined } from '@ant-design/icons-vue'
import { useAppStore } from '@/stores/app'
import { message } from 'ant-design-vue'
import type { ThemeType } from '@/utils/themeManager'

const appStore = useAppStore()
const visible = ref(false)

// Local state for configuration
const localTheme = ref<ThemeType>(appStore.theme)
const localPrimaryColor = ref('#1890ff')
const localColorWeak = ref(false)
const localMultiTab = ref(true)

const colorList = [
  { key: 'dust', color: '#F5222D' },
  { key: 'volcano', color: '#FA541C' },
  { key: 'sunset', color: '#FAAD14' },
  { key: 'cyan', color: '#13C2C2' },
  { key: 'green', color: '#52C41A' },
  { key: 'daybreak', color: '#1890FF' },
  { key: 'geekblue', color: '#2F54EB' },
  { key: 'purple', color: '#722ED1' },
]

const openDrawer = () => {
  // Sync local state with store when opening
  localTheme.value = appStore.theme
  visible.value = true
}

const handleApply = () => {
  // Update App Store
  appStore.setTheme(localTheme.value)
  
  // Update Color Weak
  if (localColorWeak.value) {
    document.body.classList.add('colorWeak')
  } else {
    document.body.classList.remove('colorWeak')
  }
  
  message.success('Settings applied successfully')
  visible.value = false
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

.setting-content {
  padding: 12px 0;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.setting-section {
  margin-bottom: 24px;
}

.setting-title {
  margin-bottom: 12px;
  color: rgba(0, 0, 0, 0.85);
  font-size: 14px;
  font-weight: 500;
}

.style-checkbox-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;

  .style-item {
    position: relative;
    width: 48px;
    height: 38px;
    border-radius: 4px;
    cursor: pointer;
    overflow: hidden;
    background: #f0f2f5;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    &.active {
      box-shadow: 0 0 0 2px #1890ff;
    }

    .select-icon {
      position: absolute;
      right: 4px;
      bottom: 4px;
      color: #1890ff;
      font-size: 14px;
      font-weight: bold;
    }
  }
}

.theme-color-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;

  .color-block {
    width: 20px;
    height: 20px;
    border-radius: 2px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 12px;
  }
}

.apply-section {
  margin-top: auto;
  padding: 24px 0;
}

.dark, .realdark {
  .header-action-item {
    color: rgba(255, 255, 255, 0.85);
    &:hover { background: rgba(255, 255, 255, 0.05); }
  }
  .setting-title { color: rgba(255, 255, 255, 0.85); }
  :deep(.ant-list-item) { color: rgba(255, 255, 255, 0.65); }
}
</style>
