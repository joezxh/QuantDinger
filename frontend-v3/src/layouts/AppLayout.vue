<template>
  <a-layout class="app-layout" :class="appStore.theme">
    <a-layout-sider
      :collapsed="appStore.collapsed"
      :trigger="null"
      collapsible
      :width="256"
      :theme="menuTheme"
      class="app-sider"
      @collapse="onCollapse"
    >
      <div class="logo-wrapper" :class="{ 'logo-wrapper--collapsed': appStore.collapsed }">
        <div class="logo">
          <div class="logo-icon">Q</div>
          <h1 v-show="!appStore.collapsed" class="logo-title">QuantDinger</h1>
        </div>
      </div>
      
      <div class="menu-container">
        <a-menu
          v-model:openKeys="openKeys"
          v-model:selectedKeys="selectedKeys"
          mode="inline"
          :theme="menuTheme"
          :inline-indent="24"
          @click="handleMenuClick"
          @openChange="onOpenChange"
        >
          <template v-for="item in menus" :key="item.path">
            <template v-if="!item.hidden">
              <!-- Submenu -->
              <a-sub-menu v-if="item.children && item.children.length > 0" :key="item.path">
                <template #title>
                  <span>
                    <component :is="getIcon(item.icon)" v-if="item.icon" />
                    <span>{{ $t(item.label) }}</span>
                  </span>
                </template>
                <a-menu-item v-for="child in item.children" :key="child.path">
                  <component :is="getIcon(child.icon)" v-if="child.icon" />
                  <span>{{ $t(child.label) }}</span>
                </a-menu-item>
              </a-sub-menu>
              
              <!-- Top-level Item -->
              <a-menu-item v-else :key="item.path">
                <component :is="getIcon(item.icon)" v-if="item.icon" />
                <span>{{ $t(item.label) }}</span>
              </a-menu-item>
            </template>
          </template>
        </a-menu>
      </div>

      <!-- Menu Footer -->
      <div v-if="!appStore.collapsed" class="menu-footer">
        <div class="footer-version">v3.0.2</div>
      </div>
    </a-layout-sider>

    <a-layout class="main-layout">
      <a-layout-header class="app-header">
        <div class="header-left">
          <MenuUnfoldOutlined v-if="appStore.collapsed" class="trigger" @click="toggleCollapsed" />
          <MenuFoldOutlined v-else class="trigger" @click="toggleCollapsed" />
          
          <a-breadcrumb class="header-breadcrumb">
            <a-breadcrumb-item>{{ $t('navBar.home') }}</a-breadcrumb-item>
            <a-breadcrumb-item v-if="currentRouteTitle">{{ $t(currentRouteTitle) }}</a-breadcrumb-item>
          </a-breadcrumb>
        </div>

        <div class="header-right">
          <a-space :size="0">
            <!-- 刷新 -->
            <a-tooltip :title="$t('navBar.refresh')">
              <span class="header-action-item" @click="handleRefresh">
                <ReloadOutlined />
              </span>
            </a-tooltip>
            
            <!-- 消息中心 -->
            <NoticeIcon />
            
            <!-- 国际化 -->
            <SelectLang />
            
            <!-- 页面设置 -->
            <SettingDrawer />

            <!-- 用户信息 -->
            <a-dropdown placement="bottomRight">
              <div class="user-info">
                <a-avatar :src="userInfo?.avatar" size="small">
                  {{ userInfo?.nickname?.charAt(0) || 'U' }}
                </a-avatar>
                <span class="user-name">{{ userInfo?.nickname || userInfo?.username || 'User' }}</span>
              </div>
              <template #overlay>
                <a-menu @click="handleUserMenuClick">
                  <a-menu-item key="profile">
                    <UserOutlined /> {{ $t('menu.profile') }}
                  </a-menu-item>
                  <a-menu-item key="settings">
                    <SettingOutlined /> {{ $t('menu.settings') }}
                  </a-menu-item>
                  <a-menu-divider />
                  <a-menu-item key="logout">
                    <LogoutOutlined /> {{ $t('navBar.logout') }}
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </a-space>
        </div>
      </a-layout-header>

      <a-layout-content class="app-content">
        <div class="content-wrapper">
          <router-view v-if="isRouterAlive" />
        </div>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick, provide } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  MenuUnfoldOutlined,
  MenuFoldOutlined,
  LogoutOutlined,
  UserOutlined,
  SettingOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { useMenuStore } from '@/stores/menu'
import SelectLang from '@/components/SelectLang/index.vue'
import NoticeIcon from '@/components/NoticeIcon/index.vue'
import SettingDrawer from '@/components/SettingDrawer/index.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const appStore = useAppStore()
const menuStore = useMenuStore()

const menuTheme = computed(() => (appStore.theme === 'light' ? 'light' : 'dark'))
const userInfo = computed(() => userStore.userInfo)
const menus = computed(() => menuStore.menus)
const getIcon = menuStore.getIcon

const openKeys = ref<string[]>([])
const selectedKeys = ref<string[]>([])
const isRouterAlive = ref(true)

// Root sub-menu keys for accordion mode
const rootSubmenuKeys = computed(() => menus.value.map(item => item.path))

const currentRouteTitle = computed(() => {
  return (route.meta?.title as string) || ''
})

// Accordion mode handler
const onOpenChange = (keys: string[]) => {
  const latestOpenKey = keys.find(key => !openKeys.value.includes(key))
  if (latestOpenKey && rootSubmenuKeys.value.includes(latestOpenKey)) {
    openKeys.value = [latestOpenKey]
  } else {
    openKeys.value = keys
  }
}

// Sync menu selection with route
watch(
  () => route.path,
  (newPath) => {
    selectedKeys.value = [newPath]
    
    // Auto expand parent group if not collapsed
    if (!appStore.collapsed) {
      const parent = menus.value.find(g => g.children?.some(c => c.path === newPath))
      if (parent && !openKeys.value.includes(parent.path)) {
        openKeys.value = [parent.path]
      }
    }
  },
  { immediate: true }
)

// When sider is collapsed/expanded, we might need to handle openKeys
const onCollapse = (collapsed: boolean) => {
  appStore.collapsed = collapsed
}

function handleMenuClick({ key }: { key: string }) {
  if (key !== route.path) {
    router.push(key)
  }
}

function handleUserMenuClick({ key }: { key: string }) {
  if (key === 'logout') {
    handleLogout()
  } else {
    router.push(`/${key}`)
  }
}

function toggleCollapsed() {
  appStore.toggleCollapsed()
}

function handleRefresh() {
  isRouterAlive.value = false
  nextTick(() => {
    isRouterAlive.value = true
  })
}

async function handleLogout() {
  await userStore.logout()
  router.push('/login')
}

onMounted(async () => {
  if (userStore.token) {
    try {
      await userStore.fetchUserInfo()
    } catch {
      router.push('/login')
    }
  }
})

provide('reload', handleRefresh)
</script>

<style scoped lang="less">
.app-layout {
  min-height: 100vh;
  background: #f0f2f5;

  &.dark, &.realdark {
    background: #000;
  }
}

.app-sider {
  box-shadow: 2px 0 8px 0 rgba(29, 35, 41, 0.05);
  position: relative;
  z-index: 10;
  
  &.ant-layout-sider-dark {
    background: #0a0a0a !important;
    
    :deep(.ant-layout-sider-children) {
      background: #0a0a0a !important;
      display: flex;
      flex-direction: column;
    }
    
    :deep(.ant-menu-dark) {
      background: #0a0a0a !important;
      border-right: 0;
      
      .ant-menu-sub {
        background: #111111 !important;
      }
      
      .ant-menu-item-selected {
        background-color: rgba(24, 144, 255, 0.25) !important;
      }
    }
  }
}

.logo-wrapper {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  overflow: hidden;
  transition: all 0.3s;
  background: transparent;
  flex-shrink: 0;

  &--collapsed {
    padding: 0 24px;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .logo-icon {
      width: 32px;
      height: 32px;
      background: #1890ff;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-weight: bold;
      font-size: 18px;
    }
    
    .logo-title {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      color: #fff;
      white-space: nowrap;
    }
  }
}

.menu-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;

  &::-webkit-scrollbar {
    width: 4px;
  }
  &::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
  }
}

.menu-footer {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.45);
  font-size: 12px;
  text-align: center;
  flex-shrink: 0;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  position: relative;
  z-index: 9;
  flex-shrink: 0;

  .header-left {
    display: flex;
    align-items: center;
    gap: 24px;
  }

  .trigger {
    font-size: 18px;
    cursor: pointer;
    transition: color 0.3s;
    &:hover {
      color: #1890ff;
    }
  }

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

  .header-breadcrumb {
    margin-left: 0;
  }

  .header-action-icon {
    font-size: 18px;
    cursor: pointer;
    color: rgba(0, 0, 0, 0.45);
    transition: all 0.3s;
    
    &:hover {
      color: #1890ff;
    }
  }

  .header-right {
    display: flex;
    align-items: center;
  }

  .user-info {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 12px;
    cursor: pointer;
    transition: all 0.3s;
    border-radius: 4px;

    &:hover {
      background: rgba(0, 0, 0, 0.025);
    }

    .user-name {
      font-size: 14px;
      color: rgba(0, 0, 0, 0.65);
    }
  }

  :deep(.header-action-item) {
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
}

.dark, .realdark {
  .app-header {
    background: #111111;
    border-bottom: 1px solid #1c1c1c;
    box-shadow: none;
    
    .trigger, .header-action-icon, .user-name {
      color: rgba(255, 255, 255, 0.85);
    }

    :deep(.header-action-item) {
      color: rgba(255, 255, 255, 0.85);
      
      &:hover {
        background: rgba(255, 255, 255, 0.05);
      }
    }
    
    .user-info:hover {
      background: rgba(255, 255, 255, 0.05);
    }
  }
}

.app-content {
  margin: 0;
  padding: 24px;
  overflow: auto;
}

.content-wrapper {
  background: #fff;
  min-height: 100%;
  border-radius: 2px;
}

.dark, .realdark {
  .content-wrapper {
    background: #141414;
    color: rgba(255, 255, 255, 0.85);
  }
}
</style>
