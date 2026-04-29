<template>
  <div ref="chartContainer" :style="{ width: '100%', height: height + 'px' }"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'

interface Node {
  id: string
  name?: string
  category?: string
  value?: number
  symbolSize?: number
  [key: string]: any
}

interface Edge {
  source: string
  target: string
  relation?: string
  value?: number
  [key: string]: any
}

const { t } = useI18n()
const props = defineProps({
  nodes: {
    type: Array as () => Node[],
    default: () => []
  },
  edges: {
    type: Array as () => Edge[],
    default: () => []
  },
  height: {
    type: Number,
    default: 400
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const chartContainer = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const getCategoryColor = (category: string) => {
  const colors: Record<string, string> = {
    asset: '#5470c6',
    company: '#91cc75',
    person: '#fac858',
    event: '#ee6666',
    institution: '#73c0de',
    protocol: '#3ba272',
    market: '#fc8452',
    default: '#9a60b4'
  }
  return colors[category] || colors.default
}

const renderChart = () => {
  if (!chartInstance) return

  const hasData = props.nodes && props.nodes.length > 0
  if (!hasData) {
    chartInstance.clear()
    chartInstance.setOption({
      title: { 
        text: '暂无图谱数据', 
        left: 'center', 
        top: 'center', 
        textStyle: { color: '#999', fontSize: 14 } 
      }
    })
    return
  }

  const categories: { name: string }[] = []
  const categoryMap: Record<string, boolean> = {}
  
  props.nodes.forEach(node => {
    const cat = node.category || 'default'
    if (!categoryMap[cat]) {
      categoryMap[cat] = true
      categories.push({ name: cat })
    }
  })

  const graphNodes = props.nodes.map(n => ({
    id: n.id || n.name,
    name: n.name || n.id,
    symbolSize: n.symbolSize || (n.value ? Math.min(60, Math.max(20, n.value / 2)) : 30),
    category: n.category || 'default',
    value: n.value || 1,
    label: { show: true, formatter: n.name || n.id },
    itemStyle: { color: getCategoryColor(n.category || 'default') },
    ...n
  }))

  const graphEdges = props.edges.map(e => ({
    source: e.source,
    target: e.target,
    value: e.value || 1,
    label: e.relation ? { show: true, formatter: e.relation, fontSize: 10 } : undefined,
    lineStyle: { curveness: 0.2, color: '#aaa' },
    ...e
  }))

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        if (params.dataType === 'node') {
          const d = params.data
          return `<strong>${d.name}</strong><br/>类型: ${d.category || '未知'}<br/>权重: ${d.value || 1}`
        }
        const d = params.data
        return `${d.source} → ${d.target}<br/>关系: ${d.relation || '关联'}`
      }
    },
    legend: {
      data: categories.map(c => c.name),
      bottom: 0,
      textStyle: { fontSize: 11, color: '#666' }
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        data: graphNodes,
        links: graphEdges,
        categories: categories,
        roam: true,
        label: { position: 'bottom', fontSize: 11, color: '#333' },
        force: {
          repulsion: 300,
          edgeLength: [60, 150],
          gravity: 0.1
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: { width: 4 }
        }
      }
    ]
  }

  chartInstance.setOption(option, true)
}

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

onMounted(() => {
  if (chartContainer.value) {
    chartInstance = echarts.init(chartContainer.value)
    renderChart()
    window.addEventListener('resize', handleResize)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

watch(() => [props.nodes, props.edges], () => {
  nextTick(() => {
    renderChart()
  })
}, { deep: true })
</script>

<style scoped>
/* ForceGraph specific styles if any */
</style>
