<template>
  <div class="llm-manage-page">
    <div class="page-header">
      <h1 class="page-title">AI 配置管理</h1>
      <p class="page-subtitle">管理大语言模型供应商、API Key、模型路由及负载均衡策略</p>
    </div>

    <a-card :bordered="false" class="content-card">
      <a-tabs v-model:activeKey="activeTab" class="custom-tabs">
        <a-tab-pane key="providers" tab="供应商管理">
          <provider-list />
        </a-tab-pane>
        <a-tab-pane key="keys" tab="API Key 管理">
          <key-list />
        </a-tab-pane>
        <a-tab-pane key="models" tab="模型管理">
          <model-list />
        </a-tab-pane>
        <a-tab-pane key="stats" tab="调用统计">
          <llm-stats />
        </a-tab-pane>
        <a-tab-pane key="workflow" tab="工作流集成">
          <div class="workflow-integration">
            <a-row :gutter="24">
              <a-col :span="12">
                <a-card :title="t('menu.difyWorkflow')" hoverable @click="$router.push('/dify-workflow')">
                  <template #extra><ArrowRightOutlined /></template>
                  <div class="card-content">
                    <p>配置和管理 AI 分析工作流，对接 Dify 平台实现自定义分析 Pipeline。</p>
                    <div class="status-tag">已连接</div>
                  </div>
                </a-card>
              </a-col>
              <a-col :span="12">
                <a-card :title="t('menu.graphAnalysis')" hoverable @click="$router.push('/graph-analysis')">
                  <template #extra><ArrowRightOutlined /></template>
                  <div class="card-content">
                    <p>基于图谱的跨域关联推理与事件影响分析，支持多市场资产关联查询。</p>
                    <div class="status-tag">实时同步</div>
                  </div>
                </a-card>
              </a-col>
            </a-row>
          </div>
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowRightOutlined } from '@ant-design/icons-vue'
import ProviderList from './ProviderList.vue'
import KeyList from './KeyList.vue'
import ModelList from './ModelList.vue'
import LlmStats from './LLMStats.vue'

const { t } = useI18n()
const activeTab = ref('providers')
</script>

<style scoped lang="less">
.llm-manage-page {
  padding: 24px;
  background: #f8fafc;
  min-height: calc(100vh - 64px);
}

.page-header {
  margin-bottom: 24px;
  
  .page-title {
    font-size: 24px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 4px;
  }
  
  .page-subtitle {
    color: #64748b;
    font-size: 14px;
  }
}

.content-card {
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
  
  :deep(.ant-card-body) {
    padding: 12px 24px 24px;
  }
}

.custom-tabs {
  :deep(.ant-tabs-nav) {
    margin-bottom: 20px;
    &::before { border-bottom: 1px solid #f1f5f9; }
  }
  
  :deep(.ant-tabs-tab) {
    font-weight: 600;
    padding: 12px 0;
    margin: 0 32px 0 0;
  }
}

.workflow-integration {
  padding: 12px 0;
  
  .card-content {
    p {
      color: #64748b;
      margin-bottom: 16px;
      height: 44px;
      overflow: hidden;
    }
    
    .status-tag {
      display: inline-block;
      padding: 2px 8px;
      background: #f1f5f9;
      color: #6366f1;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 600;
    }
  }
}
</style>
