<template>
  <div class="graph-analysis-page">
    <div class="page-header">
      <h2 class="page-title">
        <NodeIndexOutlined />
        <span>{{ t('graphAnalysis.title') }}</span>
      </h2>
      <p class="page-desc">{{ t('graphAnalysis.subtitle') }}</p>
    </div>

    <a-card class="search-card" :bordered="false">
      <a-form layout="inline">
        <a-form-item :label="t('common.market')">
          <a-select v-model:value="market" style="width: 140px">
            <a-select-option value="crypto">{{ t('market.crypto') }}</a-select-option>
            <a-select-option value="usstock">{{ t('graphAnalysis.usStock') }}</a-select-option>
            <a-select-option value="hkstock">{{ t('graphAnalysis.hkStock') }}</a-select-option>
            <a-select-option value="cnstock">{{ t('graphAnalysis.cnStock') }}</a-select-option>
            <a-select-option value="polymarket">{{ t('graphAnalysis.predictMarket') }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('common.symbol')">
          <a-input v-model:value="symbol" :placeholder="t('graphAnalysis.symbolPlaceholder')" style="width: 180px" />
        </a-form-item>
        <a-form-item :label="t('graphAnalysis.analysisType')">
          <a-select v-model:value="analysisType" style="width: 140px">
            <a-select-option value="context">{{ t('graphAnalysis.contextOption') }}</a-select-option>
            <a-select-option value="contagion">{{ t('graphAnalysis.contagionOption') }}</a-select-option>
            <a-select-option value="smartMoney">{{ t('graphAnalysis.smartMoneyOption') }}</a-select-option>
            <a-select-option value="eventImpact">{{ t('graphAnalysis.eventImpactOption') }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item v-if="analysisType === 'contagion'" :label="t('graphAnalysis.targetSymbol')">
          <a-input v-model:value="toSymbol" :placeholder="t('graphAnalysis.symbolPlaceholder')" style="width: 140px" />
        </a-form-item>
        <a-form-item v-if="analysisType === 'eventImpact'" :label="t('graphAnalysis.eventUid')">
          <a-input v-model:value="eventUid" :placeholder="t('graphAnalysis.eventUidPlaceholder')" style="width: 180px" />
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" @click="onQuery" :loading="loading">
              <SearchOutlined /> {{ t('graphAnalysis.queryGraphBtn') }}
            </a-button>
            <a-button @click="loadQuality" :loading="qualityLoading">
              <BarChartOutlined /> {{ t('graphAnalysis.qualityMonitorBtn') }}
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>

    <a-row :gutter="16" class="mt-16">
      <a-col :span="24">
        <a-card :title="t('graphAnalysis.relationGraph')" :bordered="false" class="graph-card">
          <template #extra>
            <a-tag color="blue">{{ t('graphAnalysis.currentSymbol') }}: {{ symbol }}</a-tag>
          </template>
          <ForceGraph
            :nodes="graphNodes"
            :edges="graphEdges"
            :height="500"
            :loading="loading"
          />
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" class="mt-16">
      <a-col :span="16">
        <GraphContextPanel
          :title="t('graphAnalysis.contextAnalysis')"
          :context="context"
          :loading="loading"
          :empty-text="t('graphAnalysis.emptyContextHint')"
          :bordered="false"
        />
      </a-col>
      <a-col :span="8">
        <a-card :title="t('graphAnalysis.qualityMonitorTitle')" :loading="qualityLoading" :bordered="false">
          <div v-if="quality">
            <a-row :gutter="16">
              <a-col :span="12">
                <a-statistic :title="t('graphAnalysis.episodeCount')" :value="quality.episode_count" />
              </a-col>
              <a-col :span="12">
                <a-statistic :title="t('graphAnalysis.entityCount')" :value="quality.entity_count" />
              </a-col>
            </a-row>
            <a-statistic :title="t('graphAnalysis.relationCount')" :value="quality.relation_count" class="mt-16" />
            <a-divider />
            <a-alert
              :message="quality.is_ready ? t('graphAnalysis.dataQualityReady') : t('graphAnalysis.dataBuilding')"
              :type="quality.is_ready ? 'success' : 'info'"
              show-icon
            >
              <template #description>
                <div style="font-size: 12px">
                  {{ t('graphAnalysis.thresholdRequirement') }}: episodes ≥ {{ quality.thresholds?.min_episodes }}, 
                  entities ≥ {{ quality.thresholds?.min_entities }}, 
                  relations ≥ {{ quality.thresholds?.min_relations }}
                </div>
              </template>
            </a-alert>
          </div>
          <a-empty v-else :description="t('graphAnalysis.qualityEmpty')" />
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" class="mt-16">
      <a-col :span="12">
        <a-card :title="t('graphAnalysis.relatedAssets')" :loading="relatedLoading" :bordered="false">
          <a-list :data-source="relatedAssets" size="small">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta :title="item.symbol" :description="item.name || t('graphAnalysis.affectedAssetDefault')" />
                <template #extra>
                  <a-tag :color="item.correlation_score > 70 ? 'red' : 'blue'">
                    {{ t('graphAnalysis.correlationLabel') }}: {{ item.correlation_score || 0 }}
                  </a-tag>
                </template>
              </a-list-item>
            </template>
          </a-list>
          <a-empty v-if="!relatedAssets.length && !relatedLoading" />
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card :title="t('graphAnalysis.recentEvents')" :loading="eventsLoading" :bordered="false">
          <a-timeline v-if="recentEvents.length">
            <a-timeline-item v-for="(evt, idx) in recentEvents" :key="idx" :color="idx === 0 ? 'blue' : 'gray'">
              <p><strong>{{ evt.title }}</strong> <small style="color:#999; margin-left:8px">{{ evt.timestamp }}</small></p>
              <p class="text-muted">{{ evt.description || '' }}</p>
            </a-timeline-item>
          </a-timeline>
          <a-empty v-else-if="!eventsLoading" />
        </a-card>
      </a-col>
    </a-row>

    <!-- 传染路径分析 -->
    <a-row v-if="analysisType === 'contagion'" :gutter="16" class="mt-16">
      <a-col :span="24">
        <a-card :title="t('graphAnalysis.contagionAnalysis')" :loading="contagionLoading" :bordered="false">
          <div v-if="contagionPath">
            <div class="contagion-header">
              <a-space size="large">
                <span><strong>{{ contagionPath.from }}</strong> <ArrowRightOutlined /> <strong>{{ contagionPath.to }}</strong></span>
                <a-tag :color="contagionPath.risk_score > 60 ? 'error' : contagionPath.risk_score > 30 ? 'warning' : 'success'">
                  {{ t('graphAnalysis.riskAssessmentScore') }}: {{ contagionPath.risk_score }}
                </a-tag>
                <span class="text-muted">{{ t('graphAnalysis.foundPaths') }}: {{ contagionPath.path_count }}</span>
              </a-space>
            </div>
            <div v-if="contagionPath.paths && contagionPath.paths.length" class="mt-16">
              <a-collapse v-model:activeKey="activePathKeys">
                <a-collapse-panel v-for="(path, idx) in contagionPath.paths" :key="String(idx)" :header="t('graphAnalysis.pathTemplate', { n: Number(idx) + 1, m: path.length })">
                  <a-steps size="small" :current="path.length - 1" direction="horizontal" class="path-steps">
                    <a-step v-for="(step, sidx) in path" :key="sidx">
                      <template #title>{{ step.node?.symbol || step.node?.name || t('graphAnalysis.nodeLabel') }}</template>
                      <template #description>{{ step.relation?.type || '' }}</template>
                    </a-step>
                  </a-steps>
                </a-collapse-panel>
              </a-collapse>
            </div>
            <a-empty v-else :description="t('graphAnalysis.noContagionPath')" />
          </div>
          <a-empty v-else :description="t('graphAnalysis.contagionHint')" />
        </a-card>
      </a-col>
    </a-row>

    <!-- 聪明钱信号 -->
    <a-row v-if="analysisType === 'smartMoney'" :gutter="16" class="mt-16">
      <a-col :span="24">
        <a-card :title="t('graphAnalysis.smartMoneyTitle')" :loading="smartMoneyLoading" :bordered="false">
          <div v-if="smartMoney">
            <a-row :gutter="16">
              <a-col :span="8">
                <a-statistic :title="t('graphAnalysis.consensus')" :value="smartMoney.consensus || 'Neutral'" />
              </a-col>
              <a-col :span="8">
                <a-statistic :title="t('graphAnalysis.confidenceScore')" :value="smartMoney.confidence || 0" :precision="2" suffix="%" />
              </a-col>
              <a-col :span="8">
                <a-statistic :title="t('graphAnalysis.whaleCount')" :value="smartMoney.whale_count || 0" />
              </a-col>
            </a-row>
            <a-divider />
            <a-table
              v-if="smartMoney.top_users && smartMoney.top_users.length"
              :columns="smartMoneyColumns"
              :data-source="smartMoney.top_users"
              size="small"
              :pagination="{ pageSize: 5 }"
            />
            <a-table
              v-else-if="smartMoney.top_whales && smartMoney.top_whales.length"
              :columns="whaleColumns"
              :data-source="smartMoney.top_whales"
              size="small"
              :pagination="{ pageSize: 5 }"
            />
          </div>
          <a-empty v-else :description="t('graphAnalysis.smartMoneyHint')" />
        </a-card>
      </a-col>
    </a-row>

    <!-- 事件影响链 -->
    <a-row v-if="analysisType === 'eventImpact'" :gutter="16" class="mt-16">
      <a-col :span="24">
        <a-card :title="t('graphAnalysis.eventImpactAnalysis')" :loading="eventImpactLoading" :bordered="false">
          <div v-if="eventImpact">
            <a-descriptions size="small" bordered :column="3">
              <a-descriptions-item :label="t('graphAnalysis.eventUidLabel')">{{ eventImpact.event_uid }}</a-descriptions-item>
              <a-descriptions-item :label="t('graphAnalysis.impactRadius')">{{ eventImpact.impact_radius }}</a-descriptions-item>
              <a-descriptions-item :label="t('graphAnalysis.maxDepth')">{{ eventImpact.max_depth }}</a-descriptions-item>
            </a-descriptions>
            <a-divider />
            <a-row :gutter="24">
              <a-col :span="12">
                <div class="sub-title">{{ t('graphAnalysis.affectedAssetsLabel') }} ({{ eventImpact.affected_assets.length }})</div>
                <div class="asset-tags mt-8">
                  <a-tag v-for="asset in eventImpact.affected_assets" :key="asset.uid" color="blue" class="mb-8">
                    {{ asset.symbol || asset.uid }}
                  </a-tag>
                </div>
                <a-empty v-if="!eventImpact.affected_assets.length" />
              </a-col>
              <a-col :span="12">
                <div class="sub-title">{{ t('graphAnalysis.affectedEventsLabel') }} ({{ eventImpact.affected_events.length }})</div>
                <a-timeline class="mt-8">
                  <a-timeline-item v-for="(evt, idx) in eventImpact.affected_events" :key="idx">
                    {{ evt.title || t('graphAnalysis.relatedEventLabel') }}
                  </a-timeline-item>
                </a-timeline>
                <a-empty v-if="!eventImpact.affected_events.length" />
              </a-col>
            </a-row>
          </div>
          <a-empty v-else :description="t('graphAnalysis.eventImpactHint')" />
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { 
  NodeIndexOutlined, SearchOutlined, BarChartOutlined, 
  ArrowRightOutlined 
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { 
  getGraphContext, getRelatedAssets, getRecentEvents, 
  getGraphQuality, getContagionPath, getSmartMoney, getEventImpact 
} from '@/api/graph'
import { ForceGraph, GraphContextPanel } from '@/components/GraphVisualization'

const { t } = useI18n()

// State
const market = ref('crypto')
const symbol = ref('BTC/USDT')
const toSymbol = ref('ETH/USDT')
const eventUid = ref('')
const analysisType = ref('context')
const loading = ref(false)
const context = ref<any>(null)
const relatedAssets = ref<any[]>([])
const recentEvents = ref<any[]>([])
const relatedLoading = ref(false)
const eventsLoading = ref(false)
const quality = ref<any>(null)
const qualityLoading = ref(false)
const contagionPath = ref<any>(null)
const contagionLoading = ref(false)
const smartMoney = ref<any>(null)
const smartMoneyLoading = ref(false)
const eventImpact = ref<any>(null)
const eventImpactLoading = ref(false)
const activePathKeys = ref<string[]>(['0'])

// Table Columns
const smartMoneyColumns = [
  { title: t('common.address'), dataIndex: 'address', key: 'address' },
  { title: t('common.name'), dataIndex: 'name', key: 'name' },
  { title: t('common.winRate'), dataIndex: 'win_rate', key: 'win_rate', customRender: ({ text }: any) => `${text}%` },
  { title: t('common.volume'), dataIndex: 'volume', key: 'volume' }
]

const whaleColumns = [
  { title: t('common.addressAccount'), dataIndex: 'address', key: 'address' },
  { title: 'Handle', dataIndex: 'handle', key: 'handle' },
  { title: t('common.balance'), dataIndex: 'balance', key: 'balance' },
  { title: t('common.change7d'), dataIndex: 'change_7d', key: 'change_7d' }
]

// Computed for Graph
const graphNodes = computed(() => {
  const nodes: any[] = []
  if (!context.value) return nodes

  // Center node
  nodes.push({
    id: symbol.value,
    name: symbol.value,
    category: 'asset',
    value: 100,
    symbolSize: 50
  })

  // Related assets
  const related = context.value.related_assets || []
  related.forEach((a: any) => {
    nodes.push({
      id: a.symbol,
      name: a.symbol,
      category: 'asset',
      value: a.correlation_score || 50,
      symbolSize: Math.max(20, (a.correlation_score || 50) / 2)
    })
  })

  // Events
  const eventsList = context.value.recent_events || []
  eventsList.forEach((e: any, i: number) => {
    nodes.push({
      id: `evt_${i}`,
      name: e.title || t('common.event'),
      category: 'event',
      value: 40,
      symbolSize: 30
    })
  })

  // Institutions
  const holders = context.value.top_institutional_holders || []
  holders.forEach((h: any, i: number) => {
    nodes.push({
      id: `inst_${i}`,
      name: h.institution || t('common.institution'),
      category: 'institution',
      value: 35,
      symbolSize: 28
    })
  })

  return nodes
})

const graphEdges = computed(() => {
  const edges: any[] = []
  if (!context.value) return edges

  const center = symbol.value

  // Asset links
  const related = context.value.related_assets || []
  related.forEach((a: any) => {
    edges.push({
      source: center,
      target: a.symbol,
      relation: t('common.relation'),
      value: a.correlation_score || 50
    })
  })

  // Event links
  const eventsList = context.value.recent_events || []
  eventsList.forEach((e: any, i: number) => {
    edges.push({
      source: center,
      target: `evt_${i}`,
      relation: t('common.influence'),
      value: 30
    })
  })

  // Institution links
  const holders = context.value.top_institutional_holders || []
  holders.forEach((h: any, i: number) => {
    edges.push({
      source: center,
      target: `inst_${i}`,
      relation: t('common.holdings'),
      value: 25
    })
  })

  return edges
})

// Methods
const onQuery = async () => {
  if (!symbol.value) {
    message.warning(t('validation.symbolRequired'))
    return
  }
  
  switch (analysisType.value) {
    case 'context':
      await loadGraphData()
      break
    case 'contagion':
      await loadContagionPath()
      break
    case 'smartMoney':
      await loadSmartMoney()
      break
    case 'eventImpact':
      await loadEventImpact()
      break
  }
}

const loadGraphData = async () => {
  loading.value = true
  relatedLoading.value = true
  eventsLoading.value = true
  
  try {
    const [ctxRes, relRes, evtRes] = await Promise.all([
      getGraphContext({ market: market.value, symbol: symbol.value }),
      getRelatedAssets({ market: market.value, symbol: symbol.value }),
      getRecentEvents({ symbol: symbol.value, limit: 10 })
    ])
    
    if (ctxRes.code === 1) context.value = ctxRes.data
    else message.error(ctxRes.msg || t('graphAnalysis.queryContextFailed'))
    
    if (relRes.code === 1) relatedAssets.value = relRes.data || []
    if (evtRes.code === 1) recentEvents.value = evtRes.data || []
    
  } catch (e: any) {
    message.error(t('graphAnalysis.queryGraphFailed') + ': ' + e.message)
  } finally {
    loading.value = false
    relatedLoading.value = false
    eventsLoading.value = false
  }
}

const loadQuality = async () => {
  qualityLoading.value = true
  try {
    const res = await getGraphQuality()
    if (res.code === 1) quality.value = res.data
  } catch (e) {
    message.error(t('graphAnalysis.qualityLoadFailed'))
  } finally {
    qualityLoading.value = false
  }
}

const loadContagionPath = async () => {
  if (!toSymbol.value) {
    message.warning(t('validation.targetSymbolRequired'))
    return
  }
  contagionLoading.value = true
  try {
    const res = await getContagionPath({
      from: symbol.value,
      to: toSymbol.value,
      market: market.value
    })
    if (res.code === 1) contagionPath.value = res.data
    else message.warning(res.msg || t('graphAnalysis.contagionQueryFailed'))
  } catch (e: any) {
    message.error(t('graphAnalysis.contagionQueryFailed') + ': ' + e.message)
  } finally {
    contagionLoading.value = false
  }
}

const loadSmartMoney = async () => {
  smartMoneyLoading.value = true
  try {
    const res = await getSmartMoney(symbol.value, { domain: 'auto' })
    if (res.code === 1) smartMoney.value = res.data
    else message.warning(res.msg || t('graphAnalysis.smartMoneyQueryFailed'))
  } catch (e: any) {
    message.error(t('graphAnalysis.smartMoneyQueryFailed') + ': ' + e.message)
  } finally {
    smartMoneyLoading.value = false
  }
}

const loadEventImpact = async () => {
  if (!eventUid.value) {
    message.warning(t('validation.eventUidRequired'))
    return
  }
  eventImpactLoading.value = true
  try {
    const res = await getEventImpact(eventUid.value, { max_depth: 3 })
    if (res.code === 1) eventImpact.value = res.data
    else message.warning(res.msg || t('graphAnalysis.eventImpactQueryFailed'))
  } catch (e: any) {
    message.error(t('graphAnalysis.eventImpactQueryFailed') + ': ' + e.message)
  } finally {
    eventImpactLoading.value = false
  }
}

onMounted(() => {
  loadGraphData()
})
</script>

<style scoped lang="less">
.graph-analysis-page {
  padding: 18px;
  background: #f0f2f5;
  min-height: calc(100vh - 64px);
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-desc {
  color: #64748b;
  font-size: 14px;
  margin: 0;
}

.search-card {
  margin-bottom: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.mt-16 { margin-top: 16px; }
.mb-8 { margin-bottom: 8px; }

.graph-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.text-muted {
  color: #8c8c8c;
  font-size: 13px;
}

.sub-title {
  font-weight: 600;
  font-size: 14px;
  color: #262626;
}

.contagion-header {
  background: #fafafa;
  padding: 12px 16px;
  border-radius: 4px;
}

.path-steps {
  padding: 20px 0;
}

:deep(.ant-card-head-title) {
  font-weight: 600;
}
</style>
