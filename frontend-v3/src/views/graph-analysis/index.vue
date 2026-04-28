<template>
  <div class="graph-analysis-page">
    <div class="page-header">
      <h2 class="page-title">
        <NodeIndexOutlined />
        <span>知识图谱分析</span>
      </h2>
      <p class="page-desc">基于图谱的跨域关联推理与事件影响分析</p>
    </div>

    <a-card class="search-card" :bordered="false">
      <a-form layout="inline">
        <a-form-item label="市场">
          <a-select v-model:value="market" style="width: 140px">
            <a-select-option value="crypto">加密货币</a-select-option>
            <a-select-option value="usstock">美股</a-select-option>
            <a-select-option value="hkstock">港股</a-select-option>
            <a-select-option value="cnstock">A股</a-select-option>
            <a-select-option value="polymarket">预测市场</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="品种">
          <a-input v-model:value="symbol" placeholder="如 BTC/USDT 或 AAPL" style="width: 180px" />
        </a-form-item>
        <a-form-item label="分析类型">
          <a-select v-model:value="analysisType" style="width: 140px">
            <a-select-option value="context">图谱上下文</a-select-option>
            <a-select-option value="contagion">传染路径</a-select-option>
            <a-select-option value="smartMoney">聪明钱信号</a-select-option>
            <a-select-option value="eventImpact">事件影响链</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item v-if="analysisType === 'contagion'" label="目标品种">
          <a-input v-model:value="toSymbol" placeholder="如 ETH/USDT" style="width: 140px" />
        </a-form-item>
        <a-form-item v-if="analysisType === 'eventImpact'" label="事件UID">
          <a-input v-model:value="eventUid" placeholder="事件唯一标识" style="width: 180px" />
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" @click="onQuery" :loading="loading">
              <SearchOutlined /> 查询图谱
            </a-button>
            <a-button @click="loadQuality" :loading="qualityLoading">
              <BarChartOutlined /> 质量监控
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>

    <a-row :gutter="16" class="mt-16">
      <a-col :span="24">
        <a-card title="关系图谱" :bordered="false" class="graph-card">
          <template #extra>
            <a-tag color="blue">当前品种: {{ symbol }}</a-tag>
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
          title="图谱上下文分析"
          :context="context"
          :loading="loading"
          :empty-text="'请输入市场与品种后查询'"
          :bordered="false"
        />
      </a-col>
      <a-col :span="8">
        <a-card title="图谱质量监控" :loading="qualityLoading" :bordered="false">
          <div v-if="quality">
            <a-row :gutter="16">
              <a-col :span="12">
                <a-statistic title="Episode 数量" :value="quality.episode_count" />
              </a-col>
              <a-col :span="12">
                <a-statistic title="实体数量" :value="quality.entity_count" />
              </a-col>
            </a-row>
            <a-statistic title="关系数量" :value="quality.relation_count" class="mt-16" />
            <a-divider />
            <a-alert
              :message="quality.is_ready ? '数据质量达标' : '数据积累中'"
              :type="quality.is_ready ? 'success' : 'info'"
              show-icon
            >
              <template #description>
                <div style="font-size: 12px">
                  阈值要求: episodes ≥ {{ quality.thresholds?.min_episodes }}, 
                  entities ≥ {{ quality.thresholds?.min_entities }}, 
                  relations ≥ {{ quality.thresholds?.min_relations }}
                </div>
              </template>
            </a-alert>
          </div>
          <a-empty v-else description="点击质量监控按钮查看" />
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" class="mt-16">
      <a-col :span="12">
        <a-card title="关联资产" :loading="relatedLoading" :bordered="false">
          <a-list :data-source="relatedAssets" size="small">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta :title="item.symbol" :description="item.name || '关联资产'" />
                <template #extra>
                  <a-tag :color="item.correlation_score > 70 ? 'red' : 'blue'">
                    相关度: {{ item.correlation_score || 0 }}
                  </a-tag>
                </template>
              </a-list-item>
            </template>
          </a-list>
          <a-empty v-if="!relatedAssets.length && !relatedLoading" />
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card title="近期重大事件" :loading="eventsLoading" :bordered="false">
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
        <a-card title="传染路径分析" :loading="contagionLoading" :bordered="false">
          <div v-if="contagionPath">
            <div class="contagion-header">
              <a-space size="large">
                <span><strong>{{ contagionPath.from }}</strong> <ArrowRightOutlined /> <strong>{{ contagionPath.to }}</strong></span>
                <a-tag :color="contagionPath.risk_score > 60 ? 'error' : contagionPath.risk_score > 30 ? 'warning' : 'success'">
                  风险评估得分: {{ contagionPath.risk_score }}
                </a-tag>
                <span class="text-muted">发现路径数: {{ contagionPath.path_count }}</span>
              </a-space>
            </div>
            <div v-if="contagionPath.paths && contagionPath.paths.length" class="mt-16">
              <a-collapse v-model:activeKey="activePathKeys">
                <a-collapse-panel v-for="(path, idx) in contagionPath.paths" :key="String(idx)" :header="`路径 ${idx + 1} (深度 ${path.length})`">
                  <a-steps size="small" :current="path.length - 1" direction="horizontal" class="path-steps">
                    <a-step v-for="(step, sidx) in path" :key="sidx">
                      <template #title>{{ step.node?.symbol || step.node?.name || '节点' }}</template>
                      <template #description>{{ step.relation?.type || '' }}</template>
                    </a-step>
                  </a-steps>
                </a-collapse-panel>
              </a-collapse>
            </div>
            <a-empty v-else description="未找到传播路径" />
          </div>
          <a-empty v-else description="请选择两个品种后查询传染路径" />
        </a-card>
      </a-col>
    </a-row>

    <!-- 聪明钱信号 -->
    <a-row v-if="analysisType === 'smartMoney'" :gutter="16" class="mt-16">
      <a-col :span="24">
        <a-card title="聪明钱 (Smart Money) 信号" :loading="smartMoneyLoading" :bordered="false">
          <div v-if="smartMoney">
            <a-row :gutter="16">
              <a-col :span="8">
                <a-statistic title="共识方向" :value="smartMoney.consensus || 'Neutral'" />
              </a-col>
              <a-col :span="8">
                <a-statistic title="置信度分数" :value="smartMoney.confidence || 0" :precision="2" suffix="%" />
              </a-col>
              <a-col :span="8">
                <a-statistic title="大户参与数" :value="smartMoney.whale_count || 0" />
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
          <a-empty v-else description="请选择品种后查询聪明钱信号" />
        </a-card>
      </a-col>
    </a-row>

    <!-- 事件影响链 -->
    <a-row v-if="analysisType === 'eventImpact'" :gutter="16" class="mt-16">
      <a-col :span="24">
        <a-card title="事件影响链分析" :loading="eventImpactLoading" :bordered="false">
          <div v-if="eventImpact">
            <a-descriptions size="small" bordered :column="3">
              <a-descriptions-item label="事件 UID">{{ eventImpact.event_uid }}</a-descriptions-item>
              <a-descriptions-item label="影响半径">{{ eventImpact.impact_radius }}</a-descriptions-item>
              <a-descriptions-item label="最大分析深度">{{ eventImpact.max_depth }}</a-descriptions-item>
            </a-descriptions>
            <a-divider />
            <a-row :gutter="24">
              <a-col :span="12">
                <div class="sub-title">受影响资产 ({{ eventImpact.affected_assets.length }})</div>
                <div class="asset-tags mt-8">
                  <a-tag v-for="asset in eventImpact.affected_assets" :key="asset.uid" color="blue" class="mb-8">
                    {{ asset.symbol || asset.uid }}
                  </a-tag>
                </div>
                <a-empty v-if="!eventImpact.affected_assets.length" />
              </a-col>
              <a-col :span="12">
                <div class="sub-title">受影响/关联事件 ({{ eventImpact.affected_events.length }})</div>
                <a-timeline class="mt-8">
                  <a-timeline-item v-for="(evt, idx) in eventImpact.affected_events" :key="idx">
                    {{ evt.title || '关联事件' }}
                  </a-timeline-item>
                </a-timeline>
                <a-empty v-if="!eventImpact.affected_events.length" />
              </a-col>
            </a-row>
          </div>
          <a-empty v-else description="请输入事件 UID 后查询影响链" />
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
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
  { title: '地址', dataIndex: 'address', key: 'address' },
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '胜率', dataIndex: 'win_rate', key: 'win_rate', customRender: ({ text }: any) => `${text}%` },
  { title: '交易量', dataIndex: 'volume', key: 'volume' }
]

const whaleColumns = [
  { title: '地址/账号', dataIndex: 'address', key: 'address' },
  { title: 'Handle', dataIndex: 'handle', key: 'handle' },
  { title: '余额', dataIndex: 'balance', key: 'balance' },
  { title: '7日变动', dataIndex: 'change_7d', key: 'change_7d' }
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
      name: e.title || '事件',
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
      name: h.institution || '机构',
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
      relation: '关联',
      value: a.correlation_score || 50
    })
  })

  // Event links
  const eventsList = context.value.recent_events || []
  eventsList.forEach((e: any, i: number) => {
    edges.push({
      source: center,
      target: `evt_${i}`,
      relation: '影响',
      value: 30
    })
  })

  // Institution links
  const holders = context.value.top_institutional_holders || []
  holders.forEach((h: any, i: number) => {
    edges.push({
      source: center,
      target: `inst_${i}`,
      relation: '持仓',
      value: 25
    })
  })

  return edges
})

// Methods
const onQuery = async () => {
  if (!symbol.value) {
    message.warning('请输入品种代码')
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
    else message.error(ctxRes.msg || '查询上下文失败')
    
    if (relRes.code === 1) relatedAssets.value = relRes.data || []
    if (evtRes.code === 1) recentEvents.value = evtRes.data || []
    
  } catch (e: any) {
    message.error('图谱查询失败: ' + e.message)
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
    message.error('质量监控加载失败')
  } finally {
    qualityLoading.value = false
  }
}

const loadContagionPath = async () => {
  if (!toSymbol.value) {
    message.warning('请输入目标品种')
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
    else message.warning(res.msg || '传染路径查询失败')
  } catch (e: any) {
    message.error('传染路径查询失败: ' + e.message)
  } finally {
    contagionLoading.value = false
  }
}

const loadSmartMoney = async () => {
  smartMoneyLoading.value = true
  try {
    const res = await getSmartMoney(symbol.value, { domain: 'auto' })
    if (res.code === 1) smartMoney.value = res.data
    else message.warning(res.msg || '聪明钱信号查询失败')
  } catch (e: any) {
    message.error('聪明钱信号查询失败: ' + e.message)
  } finally {
    smartMoneyLoading.value = false
  }
}

const loadEventImpact = async () => {
  if (!eventUid.value) {
    message.warning('请输入事件 UID')
    return
  }
  eventImpactLoading.value = true
  try {
    const res = await getEventImpact(eventUid.value, { max_depth: 3 })
    if (res.code === 1) eventImpact.value = res.data
    else message.warning(res.msg || '事件影响链查询失败')
  } catch (e: any) {
    message.error('事件影响链查询失败: ' + e.message)
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
