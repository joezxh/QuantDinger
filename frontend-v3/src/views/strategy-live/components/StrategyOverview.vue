<template>
  <div class="strategy-overview">
    <!-- Top Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="lbl">累计净值</div>
        <div class="val">{{ stats.equity?.toFixed(4) || '1.0000' }}</div>
        <div class="sub" :class="stats.total_return >= 0 ? 'up' : 'down'">
          {{ stats.total_return >= 0 ? '+' : '' }}{{ stats.total_return?.toFixed(2) }}%
        </div>
      </div>
      <div class="stat-card">
        <div class="lbl">今日收益</div>
        <div class="val" :class="stats.today_return >= 0 ? 'up' : 'down'">
          {{ stats.today_return >= 0 ? '+' : '' }}{{ stats.today_return?.toFixed(2) }}%
        </div>
        <div class="sub">{{ stats.today_pnl >= 0 ? '+' : '' }}${{ stats.today_pnl?.toFixed(2) }}</div>
      </div>
      <div class="stat-card">
        <div class="lbl">最大回撤</div>
        <div class="val loss">{{ stats.max_drawdown?.toFixed(2) }}%</div>
        <div class="sub">历史峰值</div>
      </div>
      <div class="stat-card">
        <div class="lbl">胜率 / 盈亏比</div>
        <div class="val">{{ stats.win_rate?.toFixed(1) }}%</div>
        <div class="sub">{{ stats.profit_loss_ratio?.toFixed(2) }}</div>
      </div>
    </div>

    <!-- Equity Chart -->
    <div class="chart-section">
      <div class="section-title">收益走势 (Equity Curve)</div>
      <div ref="chartContainer" class="chart-box"></div>
    </div>

    <!-- Recent Signals/Activity -->
    <div class="activity-section">
      <div class="section-title">最近信号</div>
      <a-table
        :columns="columns"
        :data-source="recentSignals"
        size="small"
        :pagination="false"
        class="compact-table"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'type'">
            <a-tag :color="record.type === 'buy' ? 'green' : 'red'">{{ record.type.toUpperCase() }}</a-tag>
          </template>
          <template v-if="column.key === 'pnl'">
            <span :class="record.pnl >= 0 ? 'up' : 'down'">{{ record.pnl >= 0 ? '+' : '' }}{{ record.pnl.toFixed(2) }}%</span>
          </template>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { createChart, IChartApi, ILineSeriesApi } from 'lightweight-charts'

const props = defineProps<{
  strategy: any
  stats: any
  recentSignals: any[]
  equityCurve: any[]
}>()

const chartContainer = ref<HTMLElement | null>(null)
let chart: IChartApi | null = null
let lineSeries: ILineSeriesApi<'Line'> | null = null

const columns = [
  { title: '时间', dataIndex: 'time', key: 'time' },
  { title: '信号', key: 'type', width: 80 },
  { title: '价格', dataIndex: 'price', key: 'price', align: 'right' },
  { title: '收益', key: 'pnl', align: 'right' }
]

const initChart = () => {
  if (!chartContainer.value || !props.equityCurve?.length) return

  chart = createChart(chartContainer.value, {
    layout: {
      background: { color: 'transparent' },
      textColor: '#64748b',
    },
    grid: {
      vertLines: { color: '#f1f5f9' },
      horzLines: { color: '#f1f5f9' },
    },
    width: chartContainer.value.clientWidth,
    height: 300,
    timeScale: {
      borderColor: '#e2e8f0',
      timeVisible: true,
    },
    rightPriceScale: {
      borderColor: '#e2e8f0',
    }
  })

  lineSeries = chart.addLineSeries({
    color: '#3b82f6',
    lineWidth: 3,
    crosshairMarkerVisible: true,
  })

  const data = props.equityCurve.map(item => ({
    time: item.time / 1000,
    value: item.value
  }))

  lineSeries.setData(data)
  chart.timeScale().fitContent()
}

watch(() => props.equityCurve, () => {
  if (chart) {
    chart.remove()
    chart = null
  }
  setTimeout(initChart, 50)
}, { deep: true })

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chart) chart.remove()
})

const handleResize = () => {
  if (chart && chartContainer.value) {
    chart.applyOptions({ width: chartContainer.value.clientWidth })
  }
}
</script>

<style scoped lang="less">
.strategy-overview {
  display: flex;
  flex-direction: column;
  gap: 24px;

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;

    .stat-card {
      background: #fff;
      padding: 20px;
      border-radius: 12px;
      border: 1px solid #f1f5f9;
      box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);

      .lbl { font-size: 12px; color: #64748b; margin-bottom: 8px; }
      .val { font-size: 20px; font-weight: 800; color: #1e293b; }
      .sub { font-size: 12px; font-weight: 600; margin-top: 4px; }
      
      .up { color: #10b981; }
      .down { color: #ef4444; }
      .val.loss { color: #ef4444; }
    }
  }

  .section-title {
    font-size: 15px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    &::before {
      content: '';
      width: 4px;
      height: 16px;
      background: #3b82f6;
      border-radius: 2px;
      margin-right: 8px;
    }
  }

  .chart-box {
    background: #fff;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #f1f5f9;
    height: 332px;
  }

  .activity-section {
    background: #fff;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #f1f5f9;
  }

  .compact-table {
    :deep(.ant-table-thead > tr > th) {
      background: #f8fafc;
      font-size: 11px;
    }
    .up { color: #10b981; font-weight: 600; }
    .down { color: #ef4444; font-weight: 600; }
  }
}

@media (max-width: 1000px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
