<template>
  <div class="data-source-page">
    <page-header-wrapper title="数据源管理" content="管理系统数据源配置、API密钥和数据集元数据">
      <a-card :bordered="false">
        <a-tabs default-active-key="configs">
          <a-tab-pane key="configs" tab="数据源配置">
            <config-list />
          </a-tab-pane>
          <a-tab-pane key="keys" tab="API 密钥">
            <key-list />
          </a-tab-pane>
          <a-tab-pane key="datasets" tab="数据集元数据">
            <dataset-list />
          </a-tab-pane>
          <a-tab-pane key="sync-tasks" tab="调度任务管理">
            <sync-task-tab />
          </a-tab-pane>
        </a-tabs>
      </a-card>
    </page-header-wrapper>
  </div>
</template>

<script>
import ConfigList from './ConfigList'
import KeyList from './KeyList'
import DatasetList from './DatasetList'
import SyncTaskTab from './SyncTaskTab'

export default {
  name: 'DataSourceIndex',
  components: {
    ConfigList,
    KeyList,
    DatasetList,
    SyncTaskTab
  }
}
</script>

<style lang="less" scoped>
.data-source-page {
  /deep/ .ant-page-header {
    background: transparent !important;
  }

  :global(body.dark) &, :global(body.realdark) & {
    /deep/ .ant-page-header-heading-title {
      color: rgba(255, 255, 255, 0.85) !important;
    }
    /deep/ .ant-page-header-content {
      color: rgba(255, 255, 255, 0.65) !important;
    }
  }
}
</style>
