<template>
  <div ref="chartContainer" class="kline-chart-container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, shallowRef } from 'vue'
import { useI18n } from 'vue-i18n'
import { createChart, IChartApi, ISeriesApi, CandlestickData, LineData } from 'lightweight-charts'

export interface KlineData extends CandlestickData {
  time: string | number
  open: number
  high: number
  low: number
  close: number
  volume?: number
}

const { t } = useI18n()
const props = withDefaults(defineProps<{
  data?: KlineData[]
  theme?: 'dark' | 'light'
  width?: number
  height?: number
}>(), {
  data: () => [],
  theme: 'dark',
  height: 400
})

const chartContainer = ref<HTMLElement | null>(null)
const chart = shallowRef<IChartApi | null>(null)
const candleSeries = shallowRef<ISeriesApi<"Candlestick"> | null>(null)

const initChart = () => {
  if (!chartContainer.value) return

  const isDark = props.theme === 'dark'

  const chartOptions = {
    layout: {
      textColor: isDark ? '#D9D9D9' : '#191919',
      background: { type: 'solid' as const, color: isDark ? '#141414' : '#FFFFFF' },
    },
    grid: {
      vertLines: { color: isDark ? '#2B2B43' : '#e1ecf2' },
      horzLines: { color: isDark ? '#2B2B43' : '#e1ecf2' },
    },
    crosshair: {
      mode: 0,
    },
    rightPriceScale: {
      borderColor: isDark ? '#2B2B43' : '#e1ecf2',
    },
    timeScale: {
      borderColor: isDark ? '#2B2B43' : '#e1ecf2',
      timeVisible: true,
    },
    width: props.width || chartContainer.value.clientWidth,
    height: props.height,
  }

  chart.value = createChart(chartContainer.value, chartOptions)

  candleSeries.value = chart.value.addCandlestickSeries({
    upColor: '#26a69a',
    downColor: '#ef5350',
    borderVisible: false,
    wickUpColor: '#26a69a',
    wickDownColor: '#ef5350',
  })

  if (props.data && props.data.length > 0) {
    candleSeries.value.setData(props.data as CandlestickData[])
  }
}

watch(() => props.data, (newData) => {
  if (candleSeries.value && newData) {
    candleSeries.value.setData(newData as CandlestickData[])
  }
}, { deep: true })

watch(() => props.theme, (newTheme) => {
  if (!chart.value) return
  const isDark = newTheme === 'dark'
  chart.value.applyOptions({
    layout: {
      textColor: isDark ? '#D9D9D9' : '#191919',
      background: { type: 'solid' as const, color: isDark ? '#141414' : '#FFFFFF' },
    },
    grid: {
      vertLines: { color: isDark ? '#2B2B43' : '#e1ecf2' },
      horzLines: { color: isDark ? '#2B2B43' : '#e1ecf2' },
    },
    rightPriceScale: {
      borderColor: isDark ? '#2B2B43' : '#e1ecf2',
    },
    timeScale: {
      borderColor: isDark ? '#2B2B43' : '#e1ecf2',
    },
  })
})

const handleResize = () => {
  if (chartContainer.value && chart.value) {
    chart.value.applyOptions({
      width: props.width || chartContainer.value.clientWidth,
      height: props.height || chartContainer.value.clientHeight
    })
  }
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chart.value) {
    chart.value.remove()
  }
})

defineExpose({
  chart,
  candleSeries
})
</script>

<style scoped>
.kline-chart-container {
  width: 100%;
  height: 100%;
}
</style>
