<template>
  <div class="ai-asset-analysis-page">
    <!-- AI Trading Radar -->
    <div class="radar-section">
      <div class="radar-header">
        <div class="header-left">
          <h2 class="radar-title">
            <ThunderboltOutlined class="icon-pulse" />
            AI 交易雷达
          </h2>
          <p class="radar-subtitle">基于全市场扫描的实时投资机会识别</p>
        </div>
        <a-button type="text" class="refresh-btn" :loading="oppLoading" @click="loadOpportunities(true)">
          <template #icon><SyncOutlined /></template>
          刷新机会
        </a-button>
      </div>

      <div class="radar-container" @mouseenter="isPaused = true" @mouseleave="isPaused = false">
        <div class="radar-track" :class="{ paused: isPaused }" :style="trackStyle">
          <div
            v-for="(opp, idx) in carouselItems"
            :key="idx"
            class="opportunity-card"
            :class="[opp.market?.toLowerCase()]"
            @click="handleOppClick(opp)"
          >
            <div class="card-glow"></div>
            <div class="card-header">
              <span class="symbol">{{ opp.symbol }}</span>
              <a-tag :color="getMarketColor(opp.market)" class="market-tag">{{ opp.market }}</a-tag>
            </div>
            
            <div class="card-metrics">
              <div class="metric">
                <span>{{ t('quickTrade.price') }}</span>
                <span class="value">${{ formatPrice(opp.price) }}</span>
              </div>
              <div class="metric">
                <span class="label">24h 涨跌</span>
                <span class="value" :class="opp.change_24h >= 0 ? 'up' : 'down'">
                  {{ opp.change_24h >= 0 ? '+' : '' }}{{ opp.change_24h?.toFixed(2) }}%
                </span>
              </div>
            </div>

            <div class="card-footer">
              <div class="signal-badge" :class="opp.signal">
                {{ getSignalLabel(opp.signal) }}
              </div>
              <div class="reason">{{ opp.reason }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Workspace -->
    <a-card :bordered="false" class="workspace-card">
      <a-tabs v-model:activeKey="activeTab" class="custom-tabs">
        <a-tab-pane key="analysis">
          <template #tab>
            <ExperimentOutlined />
            智能分析
          </template>
          <div class="tab-content">
            <AIAnalysisView :embedded="true" :preset-symbol="presetSymbol" />
          </div>
        </a-tab-pane>
        <a-tab-pane key="graph">
          <template #tab>
            <NodeIndexOutlined />
            关联图谱
          </template>
          <div class="tab-content">
            <GraphAnalysisView />
          </div>
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { 
  ThunderboltOutlined, SyncOutlined, ExperimentOutlined, 
  NodeIndexOutlined 
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { getTradingOpportunities } from '@/api/global-market'
import AIAnalysisView from '../ai-analysis/index.vue'
import GraphAnalysisView from '../graph-analysis/index.vue'

// State
const { t } = useI18n()
const activeTab = ref('analysis')
const opportunities = ref<any[]>([])
const oppLoading = ref(false)
const isPaused = ref(false)
const presetSymbol = ref('')

// Carousel items (duplicated for infinite scroll)
const carouselItems = computed(() => {
  if (opportunities.value.length === 0) return []
  return [...opportunities.value, ...opportunities.value]
})

const trackStyle = computed(() => {
  const duration = opportunities.value.length * 5 // 5 seconds per card
  return {
    animationDuration: `${duration}s`
  }
})

// Methods
const loadOpportunities = async (force = false) => {
  oppLoading.value = true
  try {
    const res: any = await getTradingOpportunities(force ? { force: true } : {})
    if (res.code === 1) {
      opportunities.value = res.data || []
    }
  } catch (error) {
    console.error('Failed to load opportunities:', error)
  } finally {
    oppLoading.value = false
  }
}

const getMarketColor = (market: string) => {
  const map: Record<string, string> = {
    'Crypto': 'purple',
    'USStock': 'green',
    'CNStock': 'blue',
    'Forex': 'gold'
  }
  return map[market] || 'default'
}

const getSignalLabel = (signal: string) => {
  const map: Record<string, string> = {
    'bullish_momentum': '看涨动能',
    'bearish_momentum': '看跌动能',
    'oversold': '超卖反弹',
    'overbought': '超买回调'
  }
  return map[signal] || signal
}

const formatPrice = (price: number) => {
  if (!price) return '--'
  if (price < 1) return price.toFixed(4)
  if (price > 1000) return price.toLocaleString()
  return price.toFixed(2)
}

const handleOppClick = (opp: any) => {
  presetSymbol.value = opp.symbol
  message.info(t('batch.auto2'))
}

onMounted(() => {
  loadOpportunities()
})
</script>

<style scoped lang="less">
.ai-asset-analysis-page {
  padding: 24px;
  background: #f8fafc;
  min-height: calc(100vh - 64px);
  overflow-x: hidden;
}

.radar-section {
  margin-bottom: 32px;
}

.radar-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 16px;

  .radar-title {
    margin: 0;
    font-size: 22px;
    font-weight: 800;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 12px;

    .icon-pulse {
      color: #6366f1;
      animation: pulse 2s infinite;
    }
  }

  .radar-subtitle {
    margin: 4px 0 0;
    color: #64748b;
    font-size: 14px;
  }

  .refresh-btn {
    color: #6366f1;
    font-weight: 600;
    &:hover { background: rgba(99, 102, 241, 0.05); }
  }
}

.radar-container {
  overflow: hidden;
  position: relative;
  padding: 10px 0;
  
  &::before, &::after {
    content: '';
    position: absolute;
    top: 0;
    bottom: 0;
    width: 100px;
    z-index: 2;
    pointer-events: none;
  }
  &::before { left: 0; background: linear-gradient(to right, #f8fafc, transparent); }
  &::after { right: 0; background: linear-gradient(to left, #f8fafc, transparent); }
}

.radar-track {
  display: flex;
  gap: 20px;
  width: max-content;
  animation: scroll linear infinite;
  
  &.paused {
    animation-play-state: paused;
  }
}

@keyframes scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.8; }
  100% { transform: scale(1); opacity: 1; }
}

.opportunity-card {
  width: 280px;
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  border: 1px solid #e2e8f0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;

  &:hover {
    transform: translateY(-5px);
    border-color: #6366f1;
    box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.1), 0 8px 10px -6px rgba(99, 102, 241, 0.1);
    
    .card-glow { opacity: 1; }
  }

  .card-glow {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #6366f1, #a855f7);
    opacity: 0;
    transition: opacity 0.3s;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    .symbol {
      font-size: 18px;
      font-weight: 800;
      color: #1e293b;
    }
    
    .market-tag {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      border: none;
    }
  }

  .card-metrics {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 16px;

    .metric {
      display: flex;
      flex-direction: column;
      
      .label {
        font-size: 11px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }
      
      .value {
        font-size: 15px;
        font-weight: 700;
        color: #334155;
        
        &.up { color: #10b981; }
        &.down { color: #ef4444; }
      }
    }
  }

  .card-footer {
    .signal-badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 700;
      margin-bottom: 8px;
      
      &.bullish_momentum { background: rgba(16, 185, 129, 0.1); color: #10b981; }
      &.bearish_momentum { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
      &.oversold { background: rgba(14, 165, 233, 0.1); color: #0ea5e9; }
      &.overbought { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
    }
    
    .reason {
      font-size: 12px;
      color: #64748b;
      line-height: 1.5;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
  }
}

.workspace-card {
  border-radius: 20px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
  overflow: hidden;

  :deep(.ant-card-body) {
    padding: 0;
  }
}

.custom-tabs {
  :deep(.ant-tabs-nav) {
    margin-bottom: 0;
    padding: 0 24px;
    background: #fff;
    border-bottom: 1px solid #f1f5f9;
    
    &::before { border: none; }
  }
  
  :deep(.ant-tabs-tab) {
    padding: 16px 8px;
    font-weight: 600;
    color: #64748b;
    
    &.ant-tabs-tab-active {
      .ant-tabs-tab-btn { color: #6366f1; }
    }
  }
  
  :deep(.ant-tabs-ink-bar) {
    height: 3px;
    background: #6366f1;
    border-radius: 3px 3px 0 0;
  }
}

.tab-content {
  background: #fff;
  min-height: 600px;
}
</style>
