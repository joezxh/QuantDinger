<template>
  <div class="trading-assistant-page">
    <div class="page-header">
      <h2 class="page-title">
        <ThunderboltOutlined />
        <span>交易助手</span>
      </h2>
      <p class="page-desc">管理策略、监控交易记录和分析性能</p>
    </div>

    <!-- 策略管理Tab -->
    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane key="strategies" tab="策略管理">
        <div class="strategies-section">
          <div class="section-header">
            <div class="header-left">
              <a-radio-group v-model:value="groupByMode" size="small">
                <a-radio-button value="strategy">按策略</a-radio-button>
                <a-radio-button value="symbol">按标的</a-radio-button>
              </a-radio-group>
            </div>
            <div class="header-right">
              <a-button type="primary" @click="showCreateStrategy">
                <PlusOutlined />
                创建策略
              </a-button>
            </div>
          </div>

          <a-spin :spinning="loadingStrategies">
            <div v-if="strategies.length === 0" class="empty-state">
              <a-empty description="暂无策略">
                <a-button type="primary" @click="showCreateStrategy">
                  <PlusOutlined />
                  创建第一个策略
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
                    <a-popconfirm title="确定删除此策略？" @confirm="deleteStrategy(strategy.id)">
                      <a-button type="link" size="small">
                        <DeleteOutlined style="color: #ff4d4f" />
                      </a-button>
                    </a-popconfirm>
                  </div>
                </div>
                <div class="strategy-details">
                  <div class="detail-item">
                    <span class="label">标的:</span>
                    <span class="value">{{ strategy.symbol }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="label">周期:</span>
                    <span class="value">{{ strategy.interval }}分钟</span>
                  </div>
                  <div class="detail-item" v-if="strategy.last_run_at">
                    <span class="label">最后运行:</span>
                    <span class="value">{{ formatTime(strategy.last_run_at) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </a-spin>
        </div>
      </a-tab-pane>

      <a-tab-pane key="trades" tab="交易记录">
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
            :pagination="{ pageSize: 20, showTotal: (total: number) => `共 ${total} 条` }"
            :row-key="(record: any) => record.id"
          >
            <template #side="{ record }">
              <a-tag :color="record.side === 'BUY' ? 'green' : 'red'">
                {{ record.side === 'BUY' ? '买入' : '卖出' }}
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

      <a-tab-pane key="performance" tab="性能分析">
        <div class="performance-section">
          <a-row :gutter="16">
            <a-col :span="6">
              <a-card class="stat-card">
                <div class="stat-label">总交易次数</div>
                <div class="stat-value">{{ performanceStats.total_trades || 0 }}</div>
              </a-card>
            </a-col>
            <a-col :span="6">
              <a-card class="stat-card">
                <div class="stat-label">胜率</div>
                <div class="stat-value">{{ performanceStats.win_rate || 0 }}%</div>
              </a-card>
            </a-col>
            <a-col :span="6">
              <a-card class="stat-card">
                <div class="stat-label">总盈亏</div>
                <div class="stat-value" :class="performanceStats.total_pnl >= 0 ? 'profit' : 'loss'">
                  ${{ formatNumber(performanceStats.total_pnl || 0) }}
                </div>
              </a-card>
            </a-col>
            <a-col :span="6">
              <a-card class="stat-card">
                <div class="stat-label">平均盈亏</div>
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
      :title="editingStrategy ? '编辑策略' : '创建策略'"
      :confirmLoading="savingStrategy"
      @ok="handleSaveStrategy"
      @cancel="closeStrategyModal"
    >
      <a-form :model="strategyForm" layout="vertical">
        <a-form-item label="策略名称">
          <a-input v-model:value="strategyForm.name" placeholder="请输入策略名称" />
        </a-form-item>

        <a-form-item label="标的代码">
          <a-input v-model:value="strategyForm.symbol" placeholder="例如: AAPL, BTC/USD" />
        </a-form-item>

        <a-form-item label="策略类型">
          <a-select v-model:value="strategyForm.strategy_type" placeholder="选择策略类型">
            <a-select-option value="ma_cross">均线交叉</a-select-option>
            <a-select-option value="rsi">RSI</a-select-option>
            <a-select-option value="macd">MACD</a-select-option>
            <a-select-option value="bollinger">布林带</a-select-option>
            <a-select-option value="custom">自定义</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="运行间隔(分钟)">
          <a-input-number
            v-model:value="strategyForm.interval"
            :min="1"
            :max="1440"
            style="width: 100%"
          />
        </a-form-item>

        <a-form-item label="状态">
          <a-select v-model:value="strategyForm.status">
            <a-select-option value="active">启用</a-select-option>
            <a-select-option value="paused">暂停</a-select-option>
            <a-select-option value="stopped">停止</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="策略代码">
          <a-textarea
            v-model:value="strategyForm.code"
            :rows="6"
            placeholder="输入策略代码（可选）"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
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
  { title: '策略', dataIndex: 'strategy_name', width: 120 },
  { title: '标的', dataIndex: 'symbol', width: 100 },
  { title: '方向', dataIndex: 'side', width: 80, slots: { customRender: 'side' } },
  { title: '数量', dataIndex: 'quantity', width: 100 },
  { title: '价格', dataIndex: 'price', width: 100 },
  { title: '盈亏', dataIndex: 'pnl', width: 120, slots: { customRender: 'pnl' } },
  { title: '时间', dataIndex: 'created_at', width: 180 },
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
    message.error('加载策略失败')
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
    message.error('加载交易记录失败')
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
    message.warning('请填写必要信息')
    return
  }
  savingStrategy.value = true
  try {
    if (editingStrategy.value) {
      await updateStrategy(editingStrategy.value.id, strategyForm)
      message.success('更新成功')
    } else {
      await createStrategy(strategyForm)
      message.success('创建成功')
    }
    closeStrategyModal()
    loadStrategies()
  } catch (e: any) {
    message.error(e.response?.data?.msg || '操作失败')
  }
  savingStrategy.value = false
}

async function deleteStrategy(id: number) {
  try {
    await deleteStrategy(id)
    message.success('已删除')
    loadStrategies()
  } catch (e: any) {
    message.error('删除失败')
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
