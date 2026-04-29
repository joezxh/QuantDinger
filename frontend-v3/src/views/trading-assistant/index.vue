<template>
  <div class="trading-assistant-page">
    <div class="page-header">
      <h2 class="page-title">
        <ThunderboltOutlined />
        <span>{{ t('menu.tradingAssistant') }}</span>
      </h2>
      <p class="page-desc">{{ t('trading-assistant.pageSubtitle') }}</p>
    </div>

    <!-- 策略管理Tab -->
    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane key="strategies" :tab="t('trading-assistant.tabs.strategyManage')">
        <div class="strategies-section">
          <div class="section-header">
            <div class="header-left">
              <a-radio-group v-model:value="groupByMode" size="small">
                <a-radio-button value="strategy">{{ t('trading-assistant.groupByStrategy') }}</a-radio-button>
                <a-radio-button value="symbol">{{ t('trading-assistant.groupBySymbol') }}</a-radio-button>
              </a-radio-group>
            </div>
            <div class="header-right">
              <a-button type="primary" @click="showCreateStrategy">
                <PlusOutlined />
                {{ t('trading-assistant.createStrategy') }}
              </a-button>
            </div>
          </div>

          <a-spin :spinning="loadingStrategies">
            <div v-if="strategies.length === 0" class="empty-state">
              <a-empty :description="t('trading-assistant.empty.title')">
                <a-button type="primary" @click="showCreateStrategy">
                  <PlusOutlined />
                  {{ t('trading-assistant.empty.primary') }}
                </a-button>
              </a-empty>
            </div>
            <div v-else class="strategy-list">
              <div v-for="strategy in strategies" :key="strategy.id" class="strategy-card">
                <div class="strategy-header">
                  <div class="strategy-info">
                    <h3 class="strategy-name">{{ strategy.name }}</h3>
                    <a-tag :color="getStatusColor(strategy.status)">{{ strategy.status }}</a-tag>
                  </div>
                  <div class="strategy-actions">
                    <a-button type="link" size="small" @click="editStrategy(strategy)">
                      <EditOutlined />
                    </a-button>
                    <a-popconfirm :title="t('trading-assistant.deleteConfirm')" @confirm="deleteStrategy(strategy.id)">
                      <a-button type="link" size="small">
                        <DeleteOutlined style="color: #ff4d4f" />
                      </a-button>
                    </a-popconfirm>
                  </div>
                </div>
                <div class="strategy-details">
                  <div class="detail-item">
                    <span class="label">{{ t('common.tradingPair') }}:</span>
                    <span class="value">{{ strategy.symbol }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="label">{{ t('common.timeframe') }}:</span>
                    <span class="value">{{ strategy.interval }}{{ t('common.minute') }}</span>
                  </div>
                  <div class="detail-item" v-if="strategy.last_run_at">
                    <span class="label">{{ t('trading-bot.lastRun') }}:</span>
                    <span class="value">{{ formatTime(strategy.last_run_at) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </a-spin>
        </div>
      </a-tab-pane>

      <a-tab-pane key="trades" :tab="t('trading-assistant.tabs.tradingRecords')">
        <div class="trades-section">
          <div class="section-header">
            <div class="header-left">
              <a-range-picker
                v-model:value="tradeDateRange"
                @change="loadTrades"
              />
            </div>
          </div>

          <a-table
            :columns="tradeColumns"
            :data-source="trades"
            :loading="loadingTrades"
            :pagination="{ pageSize: 20, showTotal: (total: number) => t('common.total', { total }) }"
            :row-key="(record: any) => record.id"
          >
            <template #side="{ record }">
              <a-tag :color="record.side === 'BUY' ? 'green' : 'red'">
                {{ record.side === 'BUY' ? t('quickTrade.buy') : t('quickTrade.sell') }}
              </a-tag>
            </template>

            <template #pnl="{ record }">
              <span :class="record.pnl >= 0 ? 'profit' : 'loss'">
                {{ record.pnl >= 0 ? '+' : '' }}${{ formatNumber(record.pnl) }}
              </span>
            </template>
          </a-table>
        </div>
      </a-tab-pane>

      <a-tab-pane key="performance" :tab="t('trading-assistant.tabs.performance')">
        <div class="performance-section">
          <a-row :gutter="16">
            <a-col :span="6">
              <a-card class="stat-card">
                <div class="stat-label">{{ t('dashboard.totalTrades') }}</div>
                <div class="stat-value">{{ performanceStats.total_trades || 0 }}</div>
              </a-card>
            </a-col>
            <a-col :span="6">
              <a-card class="stat-card">
                <div class="stat-label">{{ t('dashboard.winRate') }}</div>
                <div class="stat-value">{{ performanceStats.win_rate || 0 }}%</div>
              </a-card>
            </a-col>
            <a-col :span="6">
              <a-card class="stat-card">
                <div class="stat-label">{{ t('portfolio.totalPnl') }}</div>
                <div class="stat-value" :class="performanceStats.total_pnl >= 0 ? 'profit' : 'loss'">
                  ${{ formatNumber(performanceStats.total_pnl || 0) }}
                </div>
              </a-card>
            </a-col>
            <a-col :span="6">
              <a-card class="stat-card">
                <div class="stat-label">{{ t('trading-assistant.avgPnl') }}</div>
                <div class="stat-value" :class="performanceStats.avg_pnl >= 0 ? 'profit' : 'loss'">
                  ${{ formatNumber(performanceStats.avg_pnl || 0) }}
                </div>
              </a-card>
            </a-col>
          </a-row>
        </div>
      </a-tab-pane>
    </a-tabs>

    <!-- 创建/编辑策略Modal -->
    <a-modal
      v-model:visible="strategyModalVisible"
      :title="editingStrategy ? t('trading-assistant.editStrategy') : t('trading-assistant.createStrategy')"
      :confirmLoading="savingStrategy"
      @ok="handleSaveStrategy"
      @cancel="closeStrategyModal"
    >
      <a-form :model="strategyForm" layout="vertical">
        <a-form-item :label="t('trading-assistant.form.strategyName')">
          <a-input v-model:value="strategyForm.name" :placeholder="t('validation.strategyNameRequired')" />
        </a-form-item>

        <a-form-item :label="t('aiAnalysis.symbolCode')">
          <a-input v-model:value="strategyForm.symbol" :placeholder="t('aiAnalysis.symbolPlaceholder')" />
        </a-form-item>

        <a-form-item :label="t('trading-assistant.form.strategyType')">
          <a-select v-model:value="strategyForm.strategy_type" :placeholder="t('trading-assistant.form.selectStrategyType')">
            <a-select-option value="ma_cross">{{ t('trading-assistant.strategyType.maCross') }}</a-select-option>
            <a-select-option value="rsi">RSI</a-select-option>
            <a-select-option value="macd">MACD</a-select-option>
            <a-select-option value="bollinger">{{ t('trading-assistant.strategyType.bollinger') }}</a-select-option>
            <a-select-option value="custom">{{ t('trading-assistant.strategyType.custom') }}</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item :label="t('trading-assistant.form.intervalMinutes')">
          <a-input-number
            v-model:value="strategyForm.interval"
            :min="1"
            :max="1440"
            style="width: 100%"
          />
        </a-form-item>

        <a-form-item :label="t('common.status')">
          <a-select v-model:value="strategyForm.status">
            <a-select-option value="active">{{ t('common.enable') }}</a-select-option>
            <a-select-option value="paused">{{ t('common.pause') }}</a-select-option>
            <a-select-option value="stopped">{{ t('common.stop') }}</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item :label="t('trading-assistant.form.strategyCode')">
          <a-textarea
            v-model:value="strategyForm.code"
            :rows="6"
            :placeholder="t('trading-assistant.form.codePlaceholder')"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import {
  ThunderboltOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue'
import { getStrategies, createStrategy, updateStrategy, deleteStrategy, getTrades, getPerformance } from '@/api/trading-assistant'

interface Strategy {
  id: number
  name: string
  symbol: string
  strategy_type: string
  interval: number
  status: string
  code?: string
  last_run_at?: string
}

interface Trade {
  id: number
  strategy_name: string
  symbol: string
  side: string
  quantity: number
  price: number
  pnl: number
  created_at: string
}

const { t } = useI18n()
const activeTab = ref('strategies')
const groupByMode = ref('strategy')
const tradeDateRange = ref<any[]>([])

const loadingStrategies = ref(false)
const loadingTrades = ref(false)
const strategies = ref<Strategy[]>([])
const trades = ref<Trade[]>([])

const performanceStats = reactive({
  total_trades: 0,
  win_rate: 0,
  total_pnl: 0,
  avg_pnl: 0,
})

const strategyModalVisible = ref(false)
const savingStrategy = ref(false)
const editingStrategy = ref<Strategy | null>(null)

const strategyForm = reactive({
  name: '',
  symbol: '',
  strategy_type: '',
  interval: 30,
  status: 'active',
  code: '',
})

const tradeColumns = [
  { title: 'ID', dataIndex: 'id', width: 60 },
  { title: t('trading-assistant.table.strategy'), dataIndex: 'strategy_name', width: 120 },
  { title: t('common.tradingPair'), dataIndex: 'symbol', width: 100 },
  { title: t('indicatorIde.direction'), dataIndex: 'side', width: 80, slots: { customRender: 'side' } },
  { title: t('portfolio.quantity'), dataIndex: 'quantity', width: 100 },
  { title: t('quickTrade.price'), dataIndex: 'price', width: 100 },
  { title: t('portfolio.pnl'), dataIndex: 'pnl', width: 120, slots: { customRender: 'pnl' } },
  { title: t('common.time'), dataIndex: 'created_at', width: 180 },
]

function formatNumber(v: number): string {
  if (!v && v !== 0) return '0'
  return Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatTime(timestamp: string): string {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleString('zh-CN')
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = { active: 'green', paused: 'orange', stopped: 'red' }
  return colors[status] || 'default'
}

async function loadStrategies() {
  loadingStrategies.value = true
  try {
    const res = await getStrategies()
    if (res && res.code === 1 && res.data) {
      strategies.value = Array.isArray(res.data) ? res.data : []
    }
  } catch (e: any) {
    message.error(t('common.loadFailed'))
  }
  loadingStrategies.value = false
}

async function loadTrades() {
  loadingTrades.value = true
  try {
    const params: Record<string, any> = {}
    if (tradeDateRange.value && tradeDateRange.value.length === 2) {
      params.start_date = tradeDateRange.value[0]?.format('YYYY-MM-DD')
      params.end_date = tradeDateRange.value[1]?.format('YYYY-MM-DD')
    }
    const res = await getTrades(params)
    if (res && res.code === 1 && res.data) {
      trades.value = Array.isArray(res.data) ? res.data : []
    }
  } catch (e: any) {
    message.error(t('trading-assistant.loadTradesFailed'))
  }
  loadingTrades.value = false
}

async function loadPerformance() {
  try {
    const res = await getPerformance()
    if (res && res.code === 1 && res.data) {
      Object.assign(performanceStats, res.data)
    }
  } catch (e: any) {
    console.error('加载性能数据失败:', e)
  }
}

function showCreateStrategy() {
  editingStrategy.value = null
  Object.assign(strategyForm, { name: '', symbol: '', strategy_type: '', interval: 30, status: 'active', code: '' })
  strategyModalVisible.value = true
}

function editStrategy(strategy: Strategy) {
  editingStrategy.value = strategy
  Object.assign(strategyForm, {
    name: strategy.name,
    symbol: strategy.symbol,
    strategy_type: strategy.strategy_type,
    interval: strategy.interval,
    status: strategy.status,
    code: strategy.code || '',
  })
  strategyModalVisible.value = true
}

function closeStrategyModal() {
  strategyModalVisible.value = false
}

async function handleSaveStrategy() {
  if (!strategyForm.name || !strategyForm.symbol) {
    message.warning(t('validation.strategyNameRequired'))
    return
  }
  savingStrategy.value = true
  try {
    if (editingStrategy.value) {
      await updateStrategy(editingStrategy.value.id, strategyForm)
      message.success(t('common.updateSuccess'))
    } else {
      await createStrategy(strategyForm)
      message.success(t('common.createSuccess'))
    }
    closeStrategyModal()
    loadStrategies()
  } catch (e: any) {
    message.error(e.response?.data?.msg || t('common.failed'))
  }
  savingStrategy.value = false
}

async function deleteStrategy(id: number) {
  try {
    await deleteStrategy(id)
    message.success(t('common.deleted'))
    loadStrategies()
  } catch (e: any) {
    message.error(t('common.deleteFailed'))
  }
}

onMounted(() => {
  loadStrategies()
  loadTrades()
  loadPerformance()
})

// Watch tab change to reload data
import { watch } from 'vue'
watch(activeTab, (newTab) => {
  if (newTab === 'trades') {
    loadTrades()
  } else if (newTab === 'performance') {
    loadPerformance()
  }
})
</script>

<style scoped>
.trading-assistant-page {
  padding: 18px;
  background: #f5f7fa;
  min-height: calc(100vh - 120px);
}

.page-header {
  margin-bottom: 16px;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: #1e3a5f;
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-title .anticon {
  font-size: 24px;
  color: #1890ff;
}

.page-desc {
  color: #64748b;
  font-size: 14px;
  margin: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.strategy-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.strategy-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.strategy-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.strategy-name {
  font-size: 16px;
  font-weight: 600;
  color: #1e3a5f;
  margin: 0;
}

.strategy-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  font-size: 14px;
}

.detail-item .label {
  color: #64748b;
  margin-right: 6px;
}

.detail-item .value {
  color: #1e3a5f;
  font-weight: 500;
}

.empty-state {
  padding: 40px 0;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  text-align: center;
  padding: 20px;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1e3a5f;
}

.profit {
  color: #52c41a;
}

.loss {
  color: #ff4d4f;
}

@media (max-width: 1200px) {
  .strategy-list {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  }
}

@media (max-width: 768px) {
  .strategy-list {
    grid-template-columns: 1fr;
  }

  .section-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
}
</style>
