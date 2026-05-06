<template>
  <div class="data-source-container">
    <div class="page-header">
      <div class="header-left">
        <h1>数据源管理</h1>
        <p class="subtitle">配置 API 密钥、管理同步任务以及维护数据集元数据</p>
      </div>
      <div class="header-right">
        <a-space>
          <a-button type="primary" @click="$router.push('/data-source/health')">
            健康监控
          </a-button>
          <a-tag color="blue">Admin Only</a-tag>
        </a-space>
      </div>
    </div>

    <div class="main-content">
      <a-card :bordered="false" class="tabs-card">
        <a-tabs v-model:activeKey="activeTab" type="line" size="large">
          <a-tab-pane key="configs" :tab="t('dataSource.tabs.config')">
            <div class="tab-content">
              <ConfigList />
            </div>
          </a-tab-pane>
          <a-tab-pane key="test-query" tab="测试查询">
            <div class="tab-content">
              <TestQuery />
            </div>
          </a-tab-pane>
          <a-tab-pane key="import-export" tab="导入/导出">
            <div class="tab-content">
              <ImportExport />
            </div>
          </a-tab-pane>
          <a-tab-pane key="sync-tasks" :tab="t('batch.auto59')">
            <div class="tab-content">
              <SyncTaskTab />
            </div>
          </a-tab-pane>
          <a-tab-pane key="keys" :tab="t('batch.auto60')">
            <div class="tab-content">
              <KeyList />
            </div>
          </a-tab-pane>
          <a-tab-pane key="datasets" :tab="t('batch.auto61')">
            <div class="tab-content">
              <DatasetList />
            </div>
          </a-tab-pane>
        </a-tabs>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ConfigList from './components/ConfigList.vue'
import TestQuery from './components/TestQuery.vue'
import ImportExport from './components/ImportExport.vue'
import SyncTaskTab from './components/SyncTaskTab.vue'
import KeyList from './components/KeyList.vue'
import DatasetList from './components/DatasetList.vue'

const { t } = useI18n()
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
