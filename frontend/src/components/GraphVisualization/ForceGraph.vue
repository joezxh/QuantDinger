<template>
  <div ref="chartContainer" :style="{ width: '100%', height: height + 'px' }"></div>
</template>

<script>
import * as echarts from 'echarts'

export default {
  name: 'ForceGraph',
  props: {
    nodes: {
      type: Array,
      default: () => []
    },
    edges: {
      type: Array,
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
  },
  data () {
    return {
      chartInstance: null
    }
  },
  watch: {
    nodes: {
      deep: true,
      handler () {
        this.renderChart()
      }
    },
    edges: {
      deep: true,
      handler () {
        this.renderChart()
      }
    }
  },
  mounted () {
    this.initChart()
    window.addEventListener('resize', this.handleResize)
  },
  beforeDestroy () {
    window.removeEventListener('resize', this.handleResize)
    if (this.chartInstance) {
      this.chartInstance.dispose()
      this.chartInstance = null
    }
  },
  methods: {
    initChart () {
      if (!this.$refs.chartContainer) return
      this.chartInstance = echarts.init(this.$refs.chartContainer)
      this.renderChart()
    },
    handleResize () {
      if (this.chartInstance) {
        this.chartInstance.resize()
      }
    },
    getCategoryColor (category) {
      const colors = {
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
    },
    renderChart () {
      if (!this.chartInstance) return

      const hasData = this.nodes && this.nodes.length > 0
      if (!hasData) {
        this.chartInstance.clear()
        this.chartInstance.setOption({
          title: { text: '暂无图谱数据', left: 'center', top: 'center', textStyle: { color: '#999' } }
        })
        return
      }

      const categories = []
      const categoryMap = {}
      this.nodes.forEach(node => {
        const cat = node.category || 'default'
        if (!categoryMap[cat]) {
          categoryMap[cat] = true
          categories.push({ name: cat })
        }
      })

      const graphNodes = this.nodes.map(n => ({
        id: n.id || n.name,
        name: n.name || n.id,
        symbolSize: n.symbolSize || (n.value ? Math.min(60, Math.max(20, n.value / 2)) : 30),
        category: n.category || 'default',
        value: n.value || 1,
        label: { show: true, formatter: n.name || n.id },
        itemStyle: { color: this.getCategoryColor(n.category) },
        ...n
      }))

      const graphEdges = this.edges.map(e => ({
        source: e.source,
        target: e.target,
        value: e.value || 1,
        label: e.relation ? { show: true, formatter: e.relation } : undefined,
        lineStyle: { curveness: 0.2 },
        ...e
      }))

      const option = {
        tooltip: {
          trigger: 'item',
          formatter: (params) => {
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
          textStyle: { fontSize: 11 }
        },
        series: [
          {
            type: 'graph',
            layout: 'force',
            data: graphNodes,
            links: graphEdges,
            categories: categories,
            roam: true,
            label: { position: 'bottom', fontSize: 11 },
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

      this.chartInstance.setOption(option, true)
    }
  }
}
</script>
