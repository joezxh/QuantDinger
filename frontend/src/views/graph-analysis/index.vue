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
        <a-form-item label="分析类型">
          <a-select v-model="analysisType" style="width: 140px">
            <a-select-option value="context">图谱上下文</a-select-option>
            <a-select-option value="contagion">传染路径</a-select-option>
            <a-select-option value="smartMoney">聪明钱信号</a-select-option>
            <a-select-option value="eventImpact">事件影响链</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item v-if="analysisType === 'contagion'" label="目标品种">
          <a-input v-model="toSymbol" placeholder="如 ETH/USDT" style="width: 140px" />
        </a-form-item>
        <a-form-item v-if="analysisType === 'eventImpact'" label="事件UID">
          <a-input v-model="eventUid" placeholder="事件唯一标识" style="width: 180px" />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" @click="onQuery" :loading="loading">
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

    <!-- 传染路径分析 -->
    <a-row v-if="analysisType === 'contagion'" :gutter="16" class="mt-16">
      <a-col :span="24">
        <a-card title="传染路径分析" :loading="contagionLoading">
          <div v-if="contagionPath">
            <p>
              <strong>{{ contagionPath.from }}</strong>
              <a-icon type="arrow-right" />
              <strong>{{ contagionPath.to }}</strong>
              <a-tag :color="contagionPath.risk_score > 60 ? 'red' : contagionPath.risk_score > 30 ? 'orange' : 'green'" class="ml-8">
                风险分 {{ contagionPath.risk_score }}
              </a-tag>
            </p>
            <p class="text-muted">路径数: {{ contagionPath.path_count }}</p>
            <div v-if="contagionPath.paths && contagionPath.paths.length">
              <a-collapse>
                <a-collapse-panel v-for="(path, idx) in contagionPath.paths" :key="idx" :header="`路径 ${idx + 1} (深度 ${path.length})`">
                  <a-steps size="small" :current="path.length - 1" direction="horizontal">
                    <a-step v-for="(step, sidx) in path" :key="sidx" :title="step.node?.symbol || step.node?.name || '节点'" :description="step.relation?.type || ''" />
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
        <a-card title="聪明钱信号" :loading="smartMoneyLoading">
          <div v-if="smartMoney">
            <a-row :gutter="16">
              <a-col :span="8">
                <a-statistic title="信号方向" :value="smartMoney.consensus || smartMoney.trend || smartMoney.flow_direction || 'neutral'" />
              </a-col>
              <a-col :span="8">
                <a-statistic title="置信度 / 分数" :value="smartMoney.confidence || smartMoney.accumulation_score || smartMoney.flow_score || 0" />
              </a-col>
              <a-col :span="8">
                <a-statistic title="参与账户数" :value="smartMoney.user_count || smartMoney.whale_count || smartMoney.holder_count || 0" />
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
            <a-table
              v-else-if="smartMoney.top_holders && smartMoney.top_holders.length"
              :columns="holderColumns"
              :data-source="smartMoney.top_holders"
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
        <a-card title="事件影响链" :loading="eventImpactLoading">
          <div v-if="eventImpact">
            <p><strong>事件 UID:</strong> {{ eventImpact.event_uid }}</p>
            <p><strong>影响半径:</strong> {{ eventImpact.impact_radius }}</p>
            <p><strong>最大深度:</strong> {{ eventImpact.max_depth }}</p>
            <a-divider />
            <a-row :gutter="16">
              <a-col :span="12">
                <h4>受影响资产 ({{ eventImpact.affected_assets.length }})</h4>
                <a-list :data-source="eventImpact.affected_assets" size="small">
                  <a-list-item slot="renderItem" slot-scope="item">
                    <a-tag color="blue">{{ item.uid || item.symbol || 'asset' }}</a-tag>
                  </a-list-item>
                </a-list>
                <a-empty v-if="!eventImpact.affected_assets.length" />
              </a-col>
              <a-col :span="12">
                <h4>关联事件 ({{ eventImpact.affected_events.length }})</h4>
                <a-timeline>
                  <a-timeline-item v-for="(evt, idx) in eventImpact.affected_events" :key="idx">
                    <p><strong>{{ evt.title || '事件' }}</strong></p>
                  </a-timeline-item>
                </a-timeline>
                <a-empty v-if="!eventImpact.affected_events.length" />
              </a-col>
            </a-row>
          </div>
          <a-empty v-else description="请输入事件UID后查询影响链" />
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
  getGraphQuality,
  getContagionPath,
  getSmartMoney,
  getEventImpact
} from '@/api/graph'
import { ForceGraph } from '@/components/GraphVisualization'

export default {
  name: 'GraphAnalysis',
  components: { ForceGraph },
  data () {
    return {
      market: 'crypto',
      symbol: 'BTC/USDT',
      toSymbol: 'ETH/USDT',
      eventUid: '',
      analysisType: 'context',
      loading: false,
      context: null,
      contextError: '',
      relatedAssets: [],
      recentEvents: [],
      relatedLoading: false,
      eventsLoading: false,
      quality: null,
      qualityLoading: false,
      contagionPath: null,
      contagionLoading: false,
      smartMoney: null,
      smartMoneyLoading: false,
      eventImpact: null,
      eventImpactLoading: false,
      smartMoneyColumns: [
        { title: '地址', dataIndex: 'address', key: 'address' },
        { title: '名称', dataIndex: 'name', key: 'name' },
        { title: '胜率', dataIndex: 'win_rate', key: 'win_rate' },
        { title: '交易量', dataIndex: 'volume', key: 'volume' }
      ],
      whaleColumns: [
        { title: '地址/账号', dataIndex: 'address', key: 'address' },
        { title: 'Handle', dataIndex: 'handle', key: 'handle' },
        { title: '余额', dataIndex: 'balance', key: 'balance' },
        { title: '7日变动', dataIndex: 'change_7d', key: 'change_7d' }
      ],
      holderColumns: [
        { title: '机构', dataIndex: 'institution', key: 'institution' },
        { title: '类型', dataIndex: 'type', key: 'type' },
        { title: '持股数', dataIndex: 'shares', key: 'shares' },
        { title: 'QoQ变动', dataIndex: 'change_qoq', key: 'change_qoq' }
      ]
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
    async onQuery () {
      if (!this.symbol) {
        this.$message.warning('请输入品种代码')
        return
      }
      switch (this.analysisType) {
        case 'context':
          await this.loadGraphData()
          break
        case 'contagion':
          await this.loadContagionPath()
          break
        case 'smartMoney':
          await this.loadSmartMoney()
          break
        case 'eventImpact':
          await this.loadEventImpact()
          break
      }
    },

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
    },

    async loadContagionPath () {
      if (!this.toSymbol) {
        this.$message.warning('请输入目标品种')
        return
      }
      this.contagionLoading = true
      try {
        const res = await getContagionPath({
          from: this.symbol,
          to: this.toSymbol,
          market: this.market
        })
        if (res.code === 1) {
          this.contagionPath = res.data
        } else {
          this.$message.warning(res.msg || '传染路径查询失败')
        }
      } catch (e) {
        this.$message.error('传染路径查询失败: ' + e.message)
      } finally {
        this.contagionLoading = false
      }
    },

    async loadSmartMoney () {
      this.smartMoneyLoading = true
      try {
        const res = await getSmartMoney(this.symbol, { domain: 'auto' })
        if (res.code === 1) {
          this.smartMoney = res.data
        } else {
          this.$message.warning(res.msg || '聪明钱信号查询失败')
        }
      } catch (e) {
        this.$message.error('聪明钱信号查询失败: ' + e.message)
      } finally {
        this.smartMoneyLoading = false
      }
    },

    async loadEventImpact () {
      if (!this.eventUid) {
        this.$message.warning('请输入事件UID')
        return
      }
      this.eventImpactLoading = true
      try {
        const res = await getEventImpact(this.eventUid, { max_depth: 3 })
        if (res.code === 1) {
          this.eventImpact = res.data
        } else {
          this.$message.warning(res.msg || '事件影响链查询失败')
        }
      } catch (e) {
        this.$message.error('事件影响链查询失败: ' + e.message)
      } finally {
        this.eventImpactLoading = false
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
