<template>
  <a-card :title="title" :loading="loading" size="small" class="graph-context-panel">
    <a-empty v-if="!context && !loading" :description="emptyText" />
    <div v-else-if="context">
      <a-descriptions :column="1" size="small" bordered v-if="showDescriptions">
        <a-descriptions-item :label="t('graphAnalysis.relatedAssets')" v-if="hasRelatedAssets">
          <a-space wrap>
            <a-tag v-for="asset in relatedAssets" :key="asset.symbol" color="blue">
              {{ asset.symbol }}
            </a-tag>
          </a-space>
        </a-descriptions-item>
        <a-descriptions-item :label="t('batch.auto296')" v-if="hasEvents">
          <a-timeline size="small" class="mt-8">
            <a-timeline-item v-for="(evt, idx) in events.slice(0, 5)" :key="idx">
              {{ evt.title || '未知事件' }}
            </a-timeline-item>
          </a-timeline>
        </a-descriptions-item>
        <a-descriptions-item :label="t('batch.auto297')" v-if="hasHolders">
          <a-space wrap>
            <span v-for="(h, idx) in holders.slice(0, 3)" :key="idx">
              {{ h.institution }}<span v-if="idx < holders.slice(0, 3).length - 1">, </span>
            </span>
          </a-space>
        </a-descriptions-item>
        <a-descriptions-item :label="t('batch.auto298')" v-if="context.kol_consensus">
          <pre class="json-pre">{{ JSON.stringify(context.kol_consensus, null, 2) }}</pre>
        </a-descriptions-item>
        <a-descriptions-item :label="t('batch.auto299')" v-if="context.smart_money">
          <pre class="json-pre">{{ JSON.stringify(context.smart_money, null, 2) }}</pre>
        </a-descriptions-item>
        <a-descriptions-item :label="t('market.crypto')" v-if="hasPredictionSignals">
          <div v-for="(pm, idx) in predictionSignals.slice(0, 2)" :key="idx" class="mb-4">
            <strong>{{ pm.question }}</strong> ({{ pm.probability }}%)
          </div>
        </a-descriptions-item>
      </a-descriptions>
      <slot :context="context" />
    </div>
  </a-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const props = defineProps({
  title: {
    type: String,
    default: '图谱上下文'
  },
  context: {
    type: Object as () => any,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  emptyText: {
    type: String,
    default: '暂无数据'
  },
  showDescriptions: {
    type: Boolean,
    default: true
  }
})

const relatedAssets = computed(() => props.context?.related_assets || [])
const hasRelatedAssets = computed(() => relatedAssets.value.length > 0)
const events = computed(() => props.context?.recent_events || [])
const hasEvents = computed(() => events.value.length > 0)
const holders = computed(() => props.context?.top_institutional_holders || [])
const hasHolders = computed(() => holders.value.length > 0)
const predictionSignals = computed(() => props.context?.prediction_market_signals || [])
const hasPredictionSignals = computed(() => predictionSignals.value.length > 0)
</script>

<style scoped lang="less">
.graph-context-panel {
  .json-pre {
    margin: 0;
    font-size: 12px;
    background: #f5f5f5;
    padding: 8px;
    border-radius: 4px;
    max-height: 200px;
    overflow: auto;
  }
  .mt-8 { margin-top: 8px; }
  .mb-4 { margin-bottom: 4px; }
}

:deep(.ant-descriptions-item-label) {
  width: 100px;
}
</style>
