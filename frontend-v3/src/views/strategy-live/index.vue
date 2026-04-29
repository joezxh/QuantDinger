<template>
  <div class="strategy-live-container">
    <div class="page-header">
      <div class="header-left">
        <h1>策略与实盘</h1>
        <div class="stats-overview">
          <div class="stat">
            <span>{{ t('status.running') }}</span>
            <span class="val">{{ runningCount }}</span>
          </div>
          <div class="stat">
            <span class="lbl">今日收益</span>
            <span class="val" :class="totalTodayPnl >= 0 ? 'up' : 'down'">
              {{ totalTodayPnl >= 0 ? '+' : '' }}{{ totalTodayPnl.toFixed(2) }}%
            </span>
          </div>
        </div>
      </div>
      <div class="header-right">
        <a-button type="primary" size="large" @click="openCreateModal">
          <PlusOutlined /> 新建策略
        </a-button>
      </div>
    </div>

    <div class="main-layout">
      <!-- Left Sidebar: Strategy List -->
      <div class="sidebar">
        <StrategyList
          :strategies="strategies"
          :selected-id="selectedId"
          :loading="loading"
          @select="handleSelect"
        />
      </div>

      <!-- Right Detail Area -->
      <div class="detail-area">
        <template v-if="selectedId && selectedStrategy">
          <div class="detail-header">
            <div class="strategy-title">
              <div class="name-row">
                <h2>{{ selectedStrategy.name }}</h2>
                <a-tag :color="selectedStrategy.status === 'running' ? 'green' : 'default'">
                  {{ selectedStrategy.status === 'running' ? '运行中' : '已停止' }}
                </a-tag>
              </div>
              <div class="symbol-row">
                <span class="symbol">{{ selectedStrategy.symbol }}</span>
                <span class="sep">/</span>
                <span class="market">{{ selectedStrategy.market }}</span>
                <span class="sep">/</span>
                <span class="type">{{ selectedStrategy.strategy_type }}</span>
              </div>
            </div>
            <div class="strategy-actions">
              <a-button v-if="selectedStrategy.status !== 'running'" type="primary" @click="handleStart">
                <CaretRightOutlined /> 启动
              </a-button>
              <a-button v-else danger @click="handleStop">
                <PauseOutlined /> 停止
              </a-button>
              <a-button @click="openEditModal">
                <EditOutlined /> 设置
              </a-button>
              <a-popconfirm title="确定删除该策略吗？" @confirm="handleDelete">
                <a-button danger ghost>
                  <DeleteOutlined />
                </a-button>
              </a-popconfirm>
            </div>
          </div>

          <div class="detail-tabs">
            <a-tabs v-model:activeKey="activeTab">
              <a-tab-pane key="overview" tab="概览">
                <StrategyOverview
                  :strategy="selectedStrategy"
                  :stats="strategyStats"
                  :recent-signals="recentSignals"
                  :equity-curve="equityCurve"
                />
              </a-tab-pane>
              <a-tab-pane key="trades" tab="交易历史">
                <!-- Trading Records would go here -->
                <div class="tab-card">
                  <a-empty description="交易历史加载中..." />
                </div>
              </a-tab-pane>
              <a-tab-pane key="logs" :tab="t('trading-assistant.tabs.logs')">
                <StrategyLogs
                  :strategy-id="selectedId"
                  :logs="logs"
                  :is-connected="wsConnected"
                  @clear="logs = []"
                />
              </a-tab-pane>
            </a-tabs>
          </div>
        </template>
        <template v-else>
          <div class="empty-selection">
            <div class="empty-box">
              <img src="https://gw.alipayobjects.com/zos/antfincdn/ZHrcdLPrvN/empty.svg" />
              <h3>请从左侧选择一个策略</h3>
              <p>查看实时运行状态、性能分析和成交历史</p>
              <a-button type="primary" @click="openCreateModal">立即创建</a-button>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { message, Modal } from 'ant-design-vue'
import { 
  PlusOutlined, CaretRightOutlined, PauseOutlined, 
  EditOutlined, DeleteOutlined 
} from '@ant-design/icons-vue'
import StrategyList from './components/StrategyList.vue'
import StrategyOverview from './components/StrategyOverview.vue'
import StrategyLogs from './components/StrategyLogs.vue'

import { 
  getStrategyList, startStrategy, stopStrategy, deleteStrategy,
  getStrategyDetail, getStrategyLogs
} from '@/api/strategy'

// State
const { t } = useI18n()
const loading = ref(false)
const strategies = ref<any[]>([])
const selectedId = ref<number | null>(null)
const selectedStrategy = ref<any>(null)
const activeTab = ref('overview')

// Detail Data
const strategyStats = ref<any>({})
const recentSignals = ref<any[]>([])
const equityCurve = ref<any[]>([])
const logs = ref<any[]>([])
const wsConnected = ref(false)

onMounted(() => {
  loadStrategies()
})

const loadStrategies = async () => {
  loading.value = true
  try {
    const res = await getStrategyList()
    if (res.code === 1) {
      strategies.value = res.data
      if (strategies.value.length > 0 && !selectedId.value) {
        handleSelect(strategies.value[0])
      }
    }
  } finally {
    loading.value = false
  }
}

const handleSelect = async (item: any) => {
  selectedId.value = item.id
  selectedStrategy.value = item
  loadDetail(item.id)
  loadLogs(item.id)
}

const loadDetail = async (id: number) => {
  try {
    const res = await getStrategyDetail(id)
    if (res.code === 1) {
      strategyStats.value = res.data.stats || {}
      recentSignals.value = res.data.recent_signals || []
      equityCurve.value = res.data.equity_curve || []
    }
  } catch (e) {}
}

const loadLogs = async (id: number) => {
  try {
    const res = await getStrategyLogs(id)
    if (res.code === 1) {
      logs.value = res.data || []
      wsConnected.value = true
    }
  } catch (e) {}
}

const handleStart = async () => {
  if (!selectedId.value) return
  const res = await startStrategy(selectedId.value)
  if (res.code === 1) {
    message.success('策略已启动')
    loadStrategies()
    if (selectedStrategy.value) selectedStrategy.value.status = 'running'
  }
}

const handleStop = async () => {
  if (!selectedId.value) return
  const res = await stopStrategy(selectedId.value)
  if (res.code === 1) {
    message.success('策略已停止')
    loadStrategies()
    if (selectedStrategy.value) selectedStrategy.value.status = 'stopped'
  }
}

const handleDelete = async () => {
  if (!selectedId.value) return
  const res = await deleteStrategy(selectedId.value)
  if (res.code === 1) {
    message.success(t('common.deleted'))
    selectedId.value = null
    selectedStrategy.value = null
    loadStrategies()
  }
}

const openCreateModal = () => message.info('新建策略功能开发中')
const openEditModal = () => message.info('编辑策略功能开发中')

// Computed
const runningCount = computed(() => strategies.value.filter(s => s.status === 'running').length)
const totalTodayPnl = computed(() => {
  const running = strategies.value.filter(s => s.status === 'running')
  if (running.length === 0) return 0
  return running.reduce((sum, s) => sum + (s.today_pnl || 0), 0) / running.length
})
</script>

<style scoped lang="less">
.strategy-live-container {
  padding: 32px;
  background: #f8fafc;
  min-height: 100vh;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 24px;

    .header-left {
      h1 { font-size: 24px; font-weight: 800; color: #1e293b; margin-bottom: 8px; }
      .stats-overview {
        display: flex;
        gap: 20px;
        .stat {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 13px;
          .lbl { color: #64748b; }
          .val { font-weight: 700; color: #1e293b; }
          .up { color: #10b981; }
          .down { color: #ef4444; }
        }
      }
    }
  }

  .main-layout {
    display: grid;
    grid-template-columns: 280px 1fr;
    gap: 24px;
    height: calc(100vh - 180px);
  }

  .sidebar { height: 100%; }

  .detail-area {
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    display: flex;
    flex-direction: column;
    overflow: hidden;

    .detail-header {
      padding: 20px 24px;
      border-bottom: 1px solid #f1f5f9;
      display: flex;
      justify-content: space-between;
      align-items: center;

      .strategy-title {
        .name-row {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 4px;
          h2 { margin: 0; font-size: 18px; font-weight: 800; color: #1e293b; }
        }
        .symbol-row {
          font-size: 12px;
          color: #64748b;
          display: flex;
          align-items: center;
          gap: 6px;
          .symbol { font-weight: 700; color: #334155; }
          .sep { color: #cbd5e1; }
        }
      }

      .strategy-actions {
        display: flex;
        gap: 8px;
        .ant-btn { display: flex; align-items: center; gap: 4px; font-weight: 600; }
      }
    }

    .detail-tabs {
      flex: 1;
      overflow-y: auto;
      padding: 0 24px 24px;

      :deep(.ant-tabs-nav) {
        margin-bottom: 24px;
      }
    }

    .empty-selection {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      text-align: center;
      
      .empty-box {
        max-width: 400px;
        img { width: 160px; margin-bottom: 24px; opacity: 0.8; }
        h3 { font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 12px; }
        p { color: #64748b; margin-bottom: 24px; }
      }
    }
  }
}

.tab-card {
  background: #f8fafc;
  padding: 40px;
  border-radius: 8px;
  border: 1px dashed #e2e8f0;
}
</style>
