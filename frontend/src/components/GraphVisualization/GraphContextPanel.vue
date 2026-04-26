<template>
  <a-card :title="title" :loading="loading" size="small">
    <a-empty v-if="!context && !loading" :description="emptyText" />
    <div v-else>
      <a-descriptions :column="1" size="small" bordered v-if="showDescriptions">
        <a-descriptions-item label="关联资产" v-if="hasRelatedAssets">
          <a-tag v-for="asset in relatedAssets" :key="asset.symbol">
            {{ asset.symbol }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="近期事件" v-if="hasEvents">
          <a-timeline>
            <a-timeline-item v-for="(evt, idx) in events.slice(0, 5)" :key="idx">
              {{ evt.title || '未知事件' }}
            </a-timeline-item>
          </a-timeline>
        </a-descriptions-item>
        <a-descriptions-item label="主要股东" v-if="hasHolders">
          <span v-for="(h, idx) in holders.slice(0, 3)" :key="idx">
            {{ h.institution }}<span v-if="idx < 2">, </span>
          </span>
        </a-descriptions-item>
        <a-descriptions-item label="KOL 共识" v-if="context.kol_consensus">
          <pre style="margin:0; font-size:12px">{{ JSON.stringify(context.kol_consensus, null, 2) }}</pre>
        </a-descriptions-item>
        <a-descriptions-item label="聪明钱" v-if="context.smart_money">
          <pre style="margin:0; font-size:12px">{{ JSON.stringify(context.smart_money, null, 2) }}</pre>
        </a-descriptions-item>
        <a-descriptions-item label="预测市场" v-if="hasPredictionSignals">
          <div v-for="(pm, idx) in predictionSignals.slice(0, 2)" :key="idx">
            {{ pm.question }} ({{ pm.probability }}%)
          </div>
        </a-descriptions-item>
      </a-descriptions>
      <slot :context="context" />
    </div>
  </a-card>
</template>

<script>
export default {
  name: 'GraphContextPanel',
  props: {
    title: {
      type: String,
      default: '图谱上下文'
    },
    context: {
      type: Object,
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
  },
  computed: {
    relatedAssets () {
      return this.context?.related_assets || []
    },
    hasRelatedAssets () {
      return this.relatedAssets.length > 0
    },
    events () {
      return this.context?.recent_events || []
    },
    hasEvents () {
      return this.events.length > 0
    },
    holders () {
      return this.context?.top_institutional_holders || []
    },
    hasHolders () {
      return this.holders.length > 0
    },
    predictionSignals () {
      return this.context?.prediction_market_signals || []
    },
    hasPredictionSignals () {
      return this.predictionSignals.length > 0
    }
  }
}
</script>
