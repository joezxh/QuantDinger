<template>
  <div class="backtest-results">
    <div v-if="loading" class="loading-state">
      <a-spin size="large" tip="回测计算中..." />
    </div>

    <template v-else-if="result">
      <!-- Summary Metrics -->
      <div class="metrics-grid">
        <div class="metric-item" :class="result.total_return >= 0 ? 'profit' : 'loss'">
          <div class="lbl">累计收益</div>
          <div class="val">{{ result.total_return >= 0 ? '+' : '' }}{{ result.total_return.toFixed(2) }}%</div>
        </div>
        <div class="metric-item">
          <div class="lbl">最大回撤</div>
          <div class="val loss">{{ result.max_drawdown.toFixed(2) }}%</div>
        </div>
        <div class="metric-item">
          <div class="lbl">夏普比率</div>
          <div class="val">{{ result.sharpe_ratio.toFixed(2) }}</div>
        </div>
        <div class="metric-item">
          <div class="lbl">胜率</div>
          <div class="val">{{ result.win_rate.toFixed(2) }}%</div>
        </div>
      </div>

      <!-- Equity Chart -->
      <div class="chart-container">
        <div class="chart-title">权益曲线</div>
        <div ref="chartContainer" class="equity-chart"></div>
      </div>

      <!-- Trades Table -->
      <div class="trades-container">
        <div class="chart-title">交易明细 ({{ result.trades?.length || 0 }})</div>
        <a-table
          :columns="columns"
          :data-source="result.trades"
          size="small"
          :pagination="{ pageSize: 5 }"
          :scroll="{ y: 200 }"
          class="trades-table"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'side'">
              <a-tag :color="record.side === 'long' ? 'green' : 'red'">
                {{ record.side === 'long' ? '多' : '空' }}
              </a-tag>
            </template>
            <template v-if="column.key === 'pnl'">
              <span :class="record.pnl >= 0 ? 'up' : 'down'">
                {{ record.pnl >= 0 ? '+' : '' }}{{ record.pnl.toFixed(2) }}
              </span>
            </template>
          </template>
        </a-table>
      </div>
    </template>

    <div v-else class="empty-state">
      <a-empty description="运行回测以查看结果" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { createChart, IChartApi, ILineSeriesApi } from 'lightweight-charts'

const props = defineProps<{
  result: any
  loading: boolean
}>()

const chartContainer = ref<HTMLElement | null>(null)
let chart: IChartApi | null = null
let lineSeries: ILineSeriesApi<'Line'> | null = null

const columns = [
  { title: '时间', dataIndex: 'time', key: 'time', width: 140 },
  { title: '类型', key: 'side', width: 60 },
  { title: '价格', dataIndex: 'price', key: 'price', align: 'right' },
  { title: '盈亏', key: 'pnl', align: 'right' }
]

const initChart = () => {
  if (!chartContainer.value || !props.result?.equity_curve) return

  chart = createChart(chartContainer.value, {
    layout: {
      background: { color: '#1f1f1f' },
      textColor: '#d1d4dc',
    },
    grid: {
      vertLines: { color: 'rgba(42, 46, 57, 0.5)' },
      horzLines: { color: 'rgba(42, 46, 57, 0.5)' },
    },
    width: chartContainer.value.clientWidth,
    height: 200,
    timeScale: {
      borderColor: '#363c4e',
      timeVisible: true,
    },
    rightPriceScale: {
      borderColor: '#363c4e',
    }
  })

  lineSeries = chart.addLineSeries({
    color: '#3b82f6',
    lineWidth: 2,
    crosshairMarkerVisible: true,
  })

  const data = props.result.equity_curve.map((item: any) => ({
    time: item.time / 1000,
    value: item.value
  }))

  lineSeries.setData(data)
  chart.timeScale().fitContent()
}

watch(() => props.result, (newVal) => {
  if (newVal && chartContainer.value) {
    if (chart) {
      chart.remove()
      chart = null
    }
    setTimeout(initChart, 50)
  }
})

onMounted(() => {
  if (props.result) initChart()
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
.backtest-results {
  padding: 16px;
  background: #1f1f1f;
  color: #d1d4dc;
  height: 100%;
  overflow-y: auto;

  .loading-state, .empty-state {
    height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 24px;

    .metric-item {
      background: #2a2e39;
      padding: 12px;
      border-radius: 8px;
      border: 1px solid #363c4e;

      .lbl { font-size: 11px; color: #868993; margin-bottom: 4px; }
      .val { font-size: 16px; font-weight: 700; }
      
      &.profit .val { color: #10b981; }
      &.loss .val { color: #ef4444; }
      .val.loss { color: #ef4444; }
    }
  }

  .chart-title {
    font-size: 12px;
    font-weight: 600;
    color: #868993;
    margin-bottom: 12px;
    text-transform: uppercase;
  }

  .equity-chart {
    height: 200px;
    margin-bottom: 24px;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #363c4e;
  }

  .trades-table {
    :deep(.ant-table) {
      background: #1f1f1f;
      color: #d1d4dc;
    }
    :deep(.ant-table-thead > tr > th) {
      background: #2a2e39;
      color: #868993;
      border-bottom: 1px solid #363c4e;
    }
    :deep(.ant-table-tbody > tr > td) {
      border-bottom: 1px solid #363c4e;
    }
    :deep(.ant-table-row:hover > td) {
      background: #2a2e39 !important;
    }
    
    .up { color: #10b981; }
    .down { color: #ef4444; }
  }
}
</style>
