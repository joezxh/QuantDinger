<template>
  <div class="data-source-container">
    <div class="page-header">
      <div class="header-left">
        <h1>数据源管理</h1>
        <p class="subtitle">配置 API 密钥、管理同步任务以及维护数据集元数据</p>
      </div>
      <div class="header-right">
        <a-tag color="blue">Admin Only</a-tag>
      </div>
    </div>

    <div class="main-content">
      <a-card :bordered="false" class="tabs-card">
        <a-tabs v-model:activeKey="activeTab" type="line" size="large">
          <a-tab-pane key="configs" tab="数据源配置">
            <div class="tab-content">
              <ConfigList />
            </div>
          </a-tab-pane>
          <a-tab-pane key="sync-tasks" tab="调度任务管理">
            <div class="tab-content">
              <SyncTaskTab />
            </div>
          </a-tab-pane>
          <a-tab-pane key="keys" tab="API 密钥">
            <div class="tab-content empty-content">
              <a-empty description="密钥管理模块正在迁移中..." />
            </div>
          </a-tab-pane>
          <a-tab-pane key="datasets" tab="数据集元数据">
            <div class="tab-content empty-content">
              <a-empty description="数据集管理模块正在迁移中..." />
            </div>
          </a-tab-pane>
        </a-tabs>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ConfigList from './components/ConfigList.vue'
import SyncTaskTab from './components/SyncTaskTab.vue'

const activeTab = ref('configs')
</script>

<style scoped lang="less">
.data-source-container {
  padding: 32px;
  background: #f8fafc;
  min-height: 100vh;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 32px;

    h1 { font-size: 28px; font-weight: 800; color: #1e293b; margin-bottom: 8px; }
    .subtitle { color: #64748b; font-size: 15px; margin: 0; }
  }

  .tabs-card {
    border-radius: 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    
    :deep(.ant-card-body) {
      padding: 0 24px 24px;
    }

    :deep(.ant-tabs-nav) {
      margin-bottom: 24px;
      &::before { border-bottom: 1px solid #f1f5f9; }
    }

    :deep(.ant-tabs-tab) {
      font-weight: 600;
      color: #64748b;
      padding: 16px 0;
      &.ant-tabs-tab-active .ant-tabs-tab-btn { color: #3b82f6; }
    }
  }

  .tab-content {
    min-height: 400px;
    &.empty-content {
      display: flex;
      align-items: center;
      justify-content: center;
    }
  }
}
</style>
