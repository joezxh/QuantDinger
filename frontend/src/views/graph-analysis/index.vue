<template>
  <div class="graph-analysis-page">
    <a-page-header
      title="知识图谱分析"
      sub-title="基于图谱的跨域关联推理与事件影响分析"
    />

    <a-card class="search-card" :bordered="false">
      <a-form layout="inline">
        <a-form-item label="市场">
          <a-select v-model="market" style="width: 140px">
            <a-select-option value="crypto">加密货币</a-select-option>
            <a-select-option value="usstock">美股</a-select-option>
            <a-select-option value="hkstock">港股</a-select-option>
            <a-select-option value="cnstock">A股</a-select-option>
            <a-select-option value="polymarket">预测市场</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="品种">
          <a-input v-model="symbol" placeholder="如 BTC/USDT 或 AAPL" style="width: 180px" />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" @click="loadGraphData" :loading="loading">
            查询图谱
          </a-button>
        </a-form-item>
        <a-form-item>
          <a-button @click="loadQuality">质量监控</a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <a-row :gutter="16" class="mt-16">
      <a-col :span="24">
        <a-card title="关系图谱" :loading="loading">
          <ForceGraph
            :nodes="graphNodes"
            :edges="graphEdges"
            :height="420"
            :loading="loading"
          />
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" class="mt-16">
      <a-col :span="16">
        <a-card title="图谱上下文" :loading="loading">
          <div v-if="contextError" class="error-text">{{ contextError }}</div>
          <div v-else-if="context">
            <a-descriptions :column="1" size="small" bordered>
              <a-descriptions-item label="关联资产">
                <a-tag v-for="asset in context.related_assets || []" :key="asset.symbol">
                  {{ asset.symbol }}
                </a-tag>
                <span v-if="!(context.related_assets || []).length">无数据</span>
              </a-descriptions-item>
              <a-descriptions-item label="近期事件">
                <div v-for="(evt, idx) in (context.recent_events || []).slice(0, 5)" :key="idx" class="event-item">
                  {{ evt.title || '未知事件' }}
                </div>
                <span v-if="!(context.recent_events || []).length">无数据</span>
              </a-descriptions-item>
              <a-descriptions-item label="主要机构股东">
                <span v-for="(h, idx) in (context.top_institutional_holders || []).slice(0, 3)" :key="idx">
                  {{ h.institution }}<span v-if="idx < 2">, </span>
                </span>
                <span v-if="!(context.top_institutional_holders || []).length">无数据</span>
              </a-descriptions-item>
              <a-descriptions-item label="KOL 共识">
                <pre v-if="context.kol_consensus" style="margin:0">{{ JSON.stringify(context.kol_consensus, null, 2) }}</pre>
                <span v-else>无数据</span>
              </a-descriptions-item>
              <a-descriptions-item label="聪明钱">
                <pre v-if="context.smart_money" style="margin:0">{{ JSON.stringify(context.smart_money, null, 2) }}</pre>
                <span v-else>无数据</span>
              </a-descriptions-item>
              <a-descriptions-item label="预测市场信号">
                <div v-for="(pm, idx) in (context.prediction_market_signals || []).slice(0, 2)" :key="idx">
                  {{ pm.question }} ({{ pm.probability }}%)
                </div>
                <span v-if="!(context.prediction_market_signals || []).length">无数据</span>
              </a-descriptions-item>
            </a-descriptions>
          </div>
          <a-empty v-else description="请输入市场与品种后查询" />
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card title="图谱质量监控" :loading="qualityLoading">
          <div v-if="quality">
            <a-statistic title="Episode 数量" :value="quality.episode_count" />
            <a-statistic title="实体数量" :value="quality.entity_count" class="mt-8" />
            <a-statistic title="关系数量" :value="quality.relation_count" class="mt-8" />
            <a-divider />
            <a-alert
              :message="quality.is_ready ? '数据质量达标' : '数据积累中'"
              :type="quality.is_ready ? 'success' : 'info'"
              :description="`阈值: episodes≥${quality.thresholds?.min_episodes}, entities≥${quality.thresholds?.min_entities}, relations≥${quality.thresholds?.min_relations}`"
            />
          </div>
          <a-empty v-else description="点击质量监控按钮查看" />
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" class="mt-16">
      <a-col :span="12">
        <a-card title="关联资产" :loading="relatedLoading">
          <a-list :data-source="relatedAssets" size="small">
            <a-list-item slot="renderItem" slot-scope="item">
              <a-list-item-meta :title="item.symbol" :description="item.name || ''" />
            </a-list-item>
          </a-list>
          <a-empty v-if="!relatedAssets.length && !relatedLoading" />
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card title="近期事件" :loading="eventsLoading">
          <a-timeline>
            <a-timeline-item v-for="(evt, idx) in recentEvents" :key="idx">
              <p><strong>{{ evt.title }}</strong></p>
              <p class="text-muted">{{ evt.description || '' }}</p>
            </a-timeline-item>
          </a-timeline>
          <a-empty v-if="!recentEvents.length && !eventsLoading" />
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script>
import {
  getGraphContext,
  getRelatedAssets,
  getRecentEvents,
  getGraphQuality
} from '@/api/graph'
import { ForceGraph } from '@/components/GraphVisualization'

export default {
  name: 'GraphAnalysis',
  components: { ForceGraph },
  data () {
    return {
      market: 'crypto',
      symbol: 'BTC/USDT',
      loading: false,
      context: null,
      contextError: '',
      relatedAssets: [],
      recentEvents: [],
      relatedLoading: false,
      eventsLoading: false,
      quality: null,
      qualityLoading: false
    }
  },
  computed: {
    graphNodes () {
      const nodes = []
      const ctx = this.context
      if (!ctx) return nodes

      // 中心节点
      nodes.push({
        id: this.symbol,
        name: this.symbol,
        category: 'asset',
        value: 100,
        symbolSize: 50
      })

      // 关联资产
      const relatedAssets = ctx.related_assets || []
      relatedAssets.forEach(a => {
        nodes.push({
          id: a.symbol,
          name: a.symbol,
          category: 'asset',
          value: a.correlation_score || 50,
          symbolSize: Math.max(20, (a.correlation_score || 50) / 2)
        })
      })

      // 事件
      const recentEvents = ctx.recent_events || []
      recentEvents.forEach((e, i) => {
        nodes.push({
          id: `evt_${i}`,
          name: e.title || '事件',
          category: 'event',
          value: 40,
          symbolSize: 30
        })
      })

      // 机构
      const holders = ctx.top_institutional_holders || []
      holders.forEach((h, i) => {
        nodes.push({
          id: `inst_${i}`,
          name: h.institution || '机构',
          category: 'institution',
          value: 35,
          symbolSize: 28
        })
      })

      return nodes
    },
    graphEdges () {
      const edges = []
      const ctx = this.context
      if (!ctx) return edges

      const center = this.symbol

      // 关联资产边
      const relatedAssets2 = ctx.related_assets || []
      relatedAssets2.forEach(a => {
        edges.push({
          source: center,
          target: a.symbol,
          relation: '关联',
          value: a.correlation_score || 50
        })
      })

      // 事件边
      const recentEvents2 = ctx.recent_events || []
      recentEvents2.forEach((e, i) => {
        edges.push({
          source: center,
          target: `evt_${i}`,
          relation: '影响',
          value: 30
        })
      })

      // 机构边
      const holders2 = ctx.top_institutional_holders || []
      holders2.forEach((h, i) => {
        edges.push({
          source: center,
          target: `inst_${i}`,
          relation: '持仓',
          value: 25
        })
      })

      return edges
    }
  },
  methods: {
    async loadGraphData () {
      if (!this.symbol) {
        this.$message.warning('请输入品种代码')
        return
      }
      this.loading = true
      this.relatedLoading = true
      this.eventsLoading = true
      this.contextError = ''
      try {
        const [ctxRes, relRes, evtRes] = await Promise.all([
          getGraphContext({ market: this.market, symbol: this.symbol }),
          getRelatedAssets({ market: this.market, symbol: this.symbol }),
          getRecentEvents({ symbol: this.symbol, limit: 10 })
        ])
        if (ctxRes.code === 1) {
          this.context = ctxRes.data
        } else {
          this.contextError = ctxRes.msg || '查询失败'
          this.context = null
        }
        if (relRes.code === 1) {
          this.relatedAssets = relRes.data || []
        }
        if (evtRes.code === 1) {
          this.recentEvents = evtRes.data || []
        }
      } catch (e) {
        this.$message.error('图谱查询失败: ' + e.message)
        this.contextError = e.message
      } finally {
        this.loading = false
        this.relatedLoading = false
        this.eventsLoading = false
      }
    },
    async loadQuality () {
      this.qualityLoading = true
      try {
        const res = await getGraphQuality()
        if (res.code === 1) {
          this.quality = res.data
        }
      } catch (e) {
        this.$message.error('质量监控加载失败')
      } finally {
        this.qualityLoading = false
      }
    }
  }
}
</script>

<style scoped>
.graph-analysis-page {
  padding: 0 12px;
}
.search-card {
  margin-bottom: 16px;
}
.mt-8 {
  margin-top: 8px;
}
.mt-16 {
  margin-top: 16px;
}
.event-item {
  padding: 4px 0;
  border-bottom: 1px solid #f0f0f0;
}
.text-muted {
  color: rgba(0, 0, 0, 0.45);
}
.error-text {
  color: #ff4d4f;
}
</style>
