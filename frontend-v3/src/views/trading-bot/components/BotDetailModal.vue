<template>
  <a-modal
    v-model:open="visible"
    :title="bot?.strategy_name"
    :width="800"
    :footer="null"
    @cancel="close"
  >
    <div v-if="bot" class="bot-detail">
      <!-- Header tags -->
      <div class="detail-tags">
        <a-tag :color="bot.status === 'running' ? 'success' : 'default'">
          {{ bot.status === 'running' ? t('status.running') : t('status.stopped') }}
        </a-tag>
        <a-tag color="purple">{{ botTypeName }}</a-tag>
        <a-tag color="blue">{{ tc.symbol }}</a-tag>
        <a-tag>{{ tc.market_type === 'swap' ? t('trading-bot.form.futures') : t('trading-bot.form.spot') }}</a-tag>
      </div>

      <!-- KPIs -->
      <a-row :gutter="12" class="detail-kpis">
        <a-col :span="6">
          <a-card size="small">
            <div class="kpi-label">{{ t('trading-bot.detail.unrealizedPnl') }}</div>
            <div class="kpi-value" :class="(bot.unrealized_pnl || 0) >= 0 ? 'profit' : 'loss'">
              {{ (bot.unrealized_pnl || 0) >= 0 ? '+' : '' }}${{ formatNum(bot.unrealized_pnl || 0) }}
            </div>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card size="small">
            <div class="kpi-label">{{ t('trading-bot.detail.initialCapital') }}</div>
            <div class="kpi-value">${{ formatNum(tc.initial_capital || 0) }}</div>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card size="small">
            <div class="kpi-label">{{ t('trading-bot.detail.leverage') }}</div>
            <div class="kpi-value">{{ tc.leverage || 1 }}x</div>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card size="small">
            <div class="kpi-label">{{ t('trading-bot.detail.timeframe') }}</div>
            <div class="kpi-value">{{ tc.timeframe || '-' }}</div>
          </a-card>
        </a-col>
      </a-row>

      <!-- Tabs -->
      <a-tabs v-model:activeKey="activeTab" class="detail-tabs">
        <a-tab-pane key="params" :tab="t('trading-bot.tab.params')">
          <a-descriptions :column="2" size="small" bordered>
            <a-descriptions-item :label="t('trading-bot.form.symbol')">{{ tc.symbol }}</a-descriptions-item>
            <a-descriptions-item :label="t('trading-bot.form.marketType')">{{ tc.market_type }}</a-descriptions-item>
            <a-descriptions-item :label="t('trading-bot.form.timeframe')">{{ tc.timeframe }}</a-descriptions-item>
            <a-descriptions-item :label="t('trading-bot.form.initialCapital')">${{ formatNum(tc.initial_capital) }}</a-descriptions-item>
            <a-descriptions-item :label="t('trading-bot.form.leverage')">{{ tc.leverage }}x</a-descriptions-item>
            <a-descriptions-item :label="t('trading-bot.form.stopLossPct')">{{ tc.stop_loss_pct ? tc.stop_loss_pct + '%' : '-' }}</a-descriptions-item>
            <a-descriptions-item :label="t('trading-bot.form.takeProfitPct')">{{ tc.take_profit_pct ? tc.take_profit_pct + '%' : '-' }}</a-descriptions-item>
            <a-descriptions-item :label="t('trading-bot.form.maxDailyLoss')">{{ tc.max_daily_loss ? '$' + formatNum(tc.max_daily_loss) : '-' }}</a-descriptions-item>
          </a-descriptions>

          <div v-if="bot.strategy_params && Object.keys(bot.strategy_params).length" class="params-section">
            <h4>{{ t('trading-bot.form.strategyParams') }}</h4>
            <a-descriptions :column="2" size="small" bordered>
              <a-descriptions-item
                v-for="(value, key) in bot.strategy_params"
                :key="key"
                :label="key"
              >
                {{ value }}
              </a-descriptions-item>
            </a-descriptions>
          </div>
        </a-tab-pane>

        <a-tab-pane key="trades" :tab="t('trading-assistant.tabs.tradingRecords')">
          <a-table
            :columns="tradeColumns"
            :data-source="trades"
            :loading="loadingTrades"
            :pagination="{ pageSize: 10 }"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'side'">
                <a-tag :color="record.side === 'BUY' ? 'green' : 'red'">{{ record.side }}</a-tag>
              </template>
              <template v-if="column.key === 'pnl'">
                <span :class="(record.pnl || 0) >= 0 ? 'profit' : 'loss'">
                  {{ (record.pnl || 0) >= 0 ? '+' : '' }}${{ formatNum(record.pnl || 0) }}
                </span>
              </template>
            </template>
          </a-table>
        </a-tab-pane>

        <a-tab-pane key="performance" :tab="t('trading-assistant.tabs.performance')">
          <a-row :gutter="12">
            <a-col :span="8" v-for="item in performanceItems" :key="item.label">
              <a-card size="small" class="perf-card">
                <div class="perf-label">{{ item.label }}</div>
                <div class="perf-value" :class="item.class">{{ item.value }}</div>
              </a-card>
            </a-col>
          </a-row>
        </a-tab-pane>
      </a-tabs>

      <!-- Footer actions -->
      <div class="detail-actions">
        <a-space>
          <a-button
            v-if="bot.status !== 'running'"
            type="primary"
            @click="$emit('start', bot)"
          >
            {{ t('common.start') }}
          </a-button>
          <a-button
            v-else
            danger
            @click="$emit('stop', bot)"
          >
            {{ t('common.stop') }}
          </a-button>
          <a-button @click="$emit('edit', bot)" :disabled="bot.status === 'running'">
            {{ t('common.edit') }}
          </a-button>
          <a-button danger @click="$emit('delete', bot)" :disabled="bot.status === 'running'">
            {{ t('common.delete') }}
          </a-button>
        </a-space>
      </div>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getStrategyTrades, getStrategyPerformance } from '@/api/strategy'

const props = defineProps<{
  open: boolean
  bot?: any
}>()

const emit = defineEmits<['update:open', 'start', 'stop', 'edit', 'delete']>()

const { t } = useI18n()
const activeTab = ref('params')
const trades = ref<any[]>([])
const loadingTrades = ref(false)
const performance = ref<any>({})

const visible = computed({
  get: () => props.open,
  set: (v) => emit('update:open', v),
})

const tc = computed(() => props.bot?.trading_config || {})

const botTypeName = computed(() => {
  const type = props.bot?.bot_type || props.bot?.strategy_type
  const map: Record<string, string> = {
    grid: t('trading-bot.type.grid'),
    dca: t('trading-bot.type.dca'),
    martingale: t('trading-bot.type.martingale'),
    trend: t('trading-bot.type.trend'),
  }
  return map[type] || type
})

const tradeColumns = [
  { title: 'ID', dataIndex: 'id', width: 60 },
  { title: t('indicatorIde.direction'), key: 'side', width: 80 },
  { title: t('quickTrade.price'), dataIndex: 'price', width: 120 },
  { title: t('portfolio.quantity'), dataIndex: 'quantity', width: 100 },
  { title: t('portfolio.pnl'), key: 'pnl', width: 120 },
  { title: t('common.time'), dataIndex: 'created_at' },
]

const performanceItems = computed(() => {
  const p = performance.value || {}
  return [
    { label: t('dashboard.totalTrades'), value: p.total_trades || 0, class: '' },
    { label: t('dashboard.winRate'), value: (p.win_rate || 0) + '%', class: '' },
    { label: t('portfolio.totalPnl'), value: '$' + formatNum(p.total_pnl || 0), class: (p.total_pnl || 0) >= 0 ? 'profit' : 'loss' },
    { label: t('trading-assistant.avgPnl'), value: '$' + formatNum(p.avg_pnl || 0), class: (p.avg_pnl || 0) >= 0 ? 'profit' : 'loss' },
  ]
})

function formatNum(v: number): string {
  if (!v && v !== 0) return '0.00'
  return Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function loadTrades() {
  if (!props.bot?.id) return
  loadingTrades.value = true
  try {
    const res: any = await getStrategyTrades(props.bot.id)
    if (res.code === 1) trades.value = res.data || []
  } catch (e) {
    console.error('加载交易记录失败', e)
  } finally {
    loadingTrades.value = false
  }
}

async function loadPerformance() {
  if (!props.bot?.id) return
  try {
    const res: any = await getStrategyPerformance(props.bot.id)
    if (res.code === 1) performance.value = res.data || {}
  } catch (e) {
    console.error('加载绩效失败', e)
  }
}

watch(() => props.open, (v) => {
  if (v && props.bot) {
    activeTab.value = 'params'
    loadTrades()
    loadPerformance()
  }
})

watch(activeTab, (tab) => {
  if (tab === 'trades') loadTrades()
  if (tab === 'performance') loadPerformance()
})
</script>

<style scoped>
.bot-detail {
  padding: 8px 0;
}
.detail-tags {
  margin-bottom: 16px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.detail-kpis {
  margin-bottom: 16px;
}
.kpi-label {
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 4px;
}
.kpi-value {
  font-size: 18px;
  font-weight: 700;
}
.params-section {
  margin-top: 16px;
}
.params-section h4 {
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 600;
}
.detail-tabs {
  margin-bottom: 16px;
}
.detail-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}
.perf-card {
  text-align: center;
  margin-bottom: 12px;
}
.perf-label {
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 4px;
}
.perf-value {
  font-size: 20px;
  font-weight: 700;
}
.profit { color: #52c41a; }
.loss { color: #ff4d4f; }
</style>
