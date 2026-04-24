<template>
  <div class="llm-index-page">
    <page-header-wrapper :title="$t('llm.pageTitle')" :content="$t('llm.pageSubtitle')">
      <a-card :bordered="false">
        <a-tabs default-active-key="providers">
          <a-tab-pane key="providers" :tab="$t('llm.provider')">
            <provider-list />
          </a-tab-pane>
          <a-tab-pane key="keys" :tab="$t('llm.apiKey')">
            <key-list />
          </a-tab-pane>
          <a-tab-pane key="models" :tab="$t('llm.model')">
            <model-list />
          </a-tab-pane>
          <a-tab-pane key="stats" :tab="$t('common.stats') || 'Stats'">
            <llm-stats />
          </a-tab-pane>
        </a-tabs>
      </a-card>
    </page-header-wrapper>
  </div>
</template>

<script>
import ProviderList from './ProviderList'
import KeyList from './KeyList'
import ModelList from './ModelList'
import LlmStats from './LLMStats'

export default {
  name: 'LLMIndex',
  components: {
    ProviderList,
    KeyList,
    ModelList,
    LlmStats
  }
}
</script>

<style lang="less" scoped>
.llm-index-page {
  // Fix for page header background in dark mode
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
