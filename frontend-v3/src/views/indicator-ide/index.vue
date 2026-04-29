<template>
  <div class="ide-container">
    <!-- Toolbar -->
    <div class="ide-header">
      <div class="header-left">
        <a-button type="primary" size="small" @click="createNewIndicator">
          <template #icon><PlusOutlined /></template>
          新建指标
        </a-button>
        <div class="divider"></div>
        <a-select
          v-model:value="selectedSymbol"
          size="small"
          style="width: 160px"
          show-search
          @change="fetchKlineData"
        >
          <a-select-option value="BINANCE:BTC-USDT">BTC-USDT (Binance)</a-select-option>
          <a-select-option value="BINANCE:ETH-USDT">ETH-USDT (Binance)</a-select-option>
          <a-select-option value="BINANCE:SOL-USDT">SOL-USDT (Binance)</a-select-option>
        </a-select>
        <a-radio-group v-model:value="timeframe" size="small" button-style="solid" @change="fetchKlineData">
          <a-radio-button value="15m">15m</a-radio-button>
          <a-radio-button value="1H">1H</a-radio-button>
          <a-radio-button value="4H">4H</a-radio-button>
          <a-radio-button value="1D">1D</a-radio-button>
        </a-radio-group>
      </div>
      
      <div class="header-right">
        <a-button-group size="small">
          <a-button @click="saveCurrentCode" :disabled="!isDirty">
            <template #icon><SaveOutlined /></template>
            保存
          </a-button>
          <a-button @click="handleVerifyCode">
            <template #icon><CheckCircleOutlined /></template>
            校验
          </a-button>
        </a-button-group>
        <div class="divider"></div>
        <a-button type="primary" size="small" :loading="backtesting" @click="runBacktest">
          <template #icon><ThunderboltOutlined /></template>
          回测
        </a-button>
      </div>
    </div>

    <div class="ide-main">
      <!-- Left Sidebar: Explorer -->
      <div class="ide-sidebar" :class="{ collapsed: sidebarCollapsed }">
        <div class="sidebar-header" @click="sidebarCollapsed = !sidebarCollapsed">
          <FileTextOutlined />
          <span v-if="!sidebarCollapsed">指标列表</span>
          <LeftOutlined v-if="!sidebarCollapsed" class="toggle" />
          <RightOutlined v-else class="toggle" />
        </div>
        <div v-if="!sidebarCollapsed" class="indicator-list">
          <div 
            v-for="ind in indicators" 
            :key="ind.id" 
            class="indicator-item"
            :class="{ active: selectedIndicator?.id === ind.id }"
            @click="selectIndicator(ind)"
          >
            <span class="name">{{ ind.name }}</span>
            <div class="actions">
              <DeleteOutlined @click.stop="handleDeleteIndicator(ind)" />
            </div>
          </div>
        </div>
      </div>

      <!-- Center: Editor and Tabs -->
      <div class="ide-content">
        <div class="editor-pane" :style="{ height: editorHeight + '%' }">
          <CodeEditor v-model="code" />
        </div>
        
        <div class="resize-handle" @mousedown="startResize"></div>

        <div class="bottom-pane" :style="{ height: (100 - editorHeight) + '%' }">
          <a-tabs v-model:activeKey="activeTab" size="small" class="ide-tabs">
            <a-tab-pane key="chart" :tab="t('batch.auto139')">
              <div class="pane-content chart-pane">
                <KlineChart :data="klineData" theme="dark" />
              </div>
            </a-tab-pane>
            <a-tab-pane key="backtest" :tab="t('indicatorIde.backtestResults')">
              <div class="pane-content results-pane">
                <div class="results-layout">
                  <div class="params-side">
                    <IdeBacktestParams :loading="backtesting" @run="runBacktest" />
                  </div>
                  <div class="results-main">
                    <IdeBacktestResults :result="backtestResult" :loading="backtesting" />
                  </div>
                </div>
              </div>
            </a-tab-pane>
            <a-tab-pane key="ai" :tab="t('batch.auto140')">
              <div class="pane-content ai-pane">
                <div class="ai-empty">
                  <RobotOutlined style="font-size: 48px; color: #363c4e; margin-bottom: 16px;" />
                  <p>AI 调参功能正在集成中...</p>
                </div>
              </div>
            </a-tab-pane>
          </a-tabs>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { 
  PlusOutlined, SaveOutlined, CheckCircleOutlined, ThunderboltOutlined,
  FileTextOutlined, DeleteOutlined, LeftOutlined, RightOutlined,
  RobotOutlined
} from '@ant-design/icons-vue'
import { message, Modal } from 'ant-design-vue'
import CodeEditor from '@/components/CodeEditor/index.vue'
import KlineChart from '@/components/KlineChart/index.vue'
import IdeBacktestParams from './components/IdeBacktestParams.vue'
import IdeBacktestResults from './components/IdeBacktestResults.vue'

import { 
  getIndicators, saveIndicator, deleteIndicator, getKline, 
  runBacktest as runBacktestApi, verifyCode 
} from '@/api/indicator'

// IDE State
const { t } = useI18n()
const code = ref('')
const isDirty = ref(false)
const indicators = ref<any[]>([])
const selectedIndicator = ref<any>(null)
const sidebarCollapsed = ref(false)
const editorHeight = ref(60)
const activeTab = ref('chart')

// Chart/Data State
const selectedSymbol = ref('BINANCE:BTC-USDT')
const timeframe = ref('1H')
const klineData = ref<any[]>([])

// Backtest State
const backtesting = ref(false)
const backtestResult = ref<any>(null)

watch(code, () => {
  if (selectedIndicator.value) isDirty.value = true
})

onMounted(() => {
  fetchIndicators()
  fetchKlineData()
})

const fetchIndicators = async () => {
  const res = await getIndicators()
  if (res.code === 1) {
    indicators.value = res.data || []
    if (indicators.value.length > 0 && !selectedIndicator.value) {
      selectIndicator(indicators.value[0])
    }
  }
}

const fetchKlineData = async () => {
  const res = await getKline({ symbol: selectedSymbol.value, timeframe: timeframe.value, limit: 1000 })
  if (res.code === 1) {
    klineData.value = (res.data || []).map((item: any) => ({
      time: item.timestamp / 1000,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
      volume: item.volume
    })).sort((a: any, b: any) => a.time - b.time)
  }
}

const selectIndicator = (ind: any) => {
  selectedIndicator.value = ind
  code.value = ind.code || ''
  setTimeout(() => isDirty.value = false, 50)
}

const createNewIndicator = () => {
  selectedIndicator.value = null
  code.value = '# New Indicator Code\n\n'
  isDirty.value = true
}

const saveCurrentCode = async () => {
  if (!code.value) return
  
  if (!selectedIndicator.value) {
    // Show prompt for name
    let name = ''
    Modal.confirm({
      title: '新建指标',
      content: (h: any) => h('div', [
        h('p', '请输入指标名称:'),
        h('input', { 
          style: 'width: 100%; padding: 4px 8px;',
          onInput: (e: any) => { name = e.target.value }
        })
      ]),
      onOk: async () => {
        if (!name) return message.warning(t('batch.auto134'))
        const res = await saveIndicator({ name, code: code.value })
        if (res.code === 1) {
          message.success(t('batch.auto135'))
          fetchIndicators()
        }
      }
    })
    return
  }

  const res = await saveIndicator({ id: selectedIndicator.value.id, code: code.value })
  if (res.code === 1) {
    message.success(t('batch.auto135'))
    isDirty.value = false
    fetchIndicators()
  }
}

const handleVerifyCode = async () => {
  const res = await verifyCode({ code: code.value })
  if (res.code === 1) {
    message.success(t('batch.auto136'))
  } else {
    message.error('代码存在错误: ' + res.msg)
  }
}

const handleDeleteIndicator = (ind: any) => {
  Modal.confirm({
    title: '删除指标',
    content: `确定删除指标 "${ind.name}" 吗？`,
    okType: 'danger',
    onOk: async () => {
      const res = await deleteIndicator({ id: ind.id })
      if (res.code === 1) {
        message.success(t('common.deleted'))
        if (selectedIndicator.value?.id === ind.id) {
          selectedIndicator.value = null
          code.value = ''
        }
        fetchIndicators()
      }
    }
  })
}

const runBacktest = async (params = {}) => {
  if (!code.value) return message.warning(t('batch.auto137'))
  
  activeTab.value = 'backtest'
  backtesting.value = true
  try {
    const res = await runBacktestApi({
      code: code.value,
      symbol: selectedSymbol.value,
      timeframe: timeframe.value,
      ...params
    })
    if (res.code === 1) {
      backtestResult.value = res.data
      message.success(t('batch.auto138'))
    }
  } finally {
    backtesting.value = false
  }
}

// Resizing logic
const startResize = (e: MouseEvent) => {
  const startY = e.clientY
  const startHeight = editorHeight.value
  
  const moveHandler = (moveEvent: MouseEvent) => {
    const delta = ((moveEvent.clientY - startY) / window.innerHeight) * 100
    editorHeight.value = Math.max(20, Math.min(80, startHeight + delta))
  }
  
  const upHandler = () => {
    window.removeEventListener('mousemove', moveHandler)
    window.removeEventListener('mouseup', upHandler)
  }
  
  window.addEventListener('mousemove', moveHandler)
  window.addEventListener('mouseup', upHandler)
}
</script>

<style scoped lang="less">
.ide-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 64px);
  background: #141414;
  color: #d1d4dc;
}

.ide-header {
  height: 48px;
  background: #1f1f1f;
  border-bottom: 1px solid #303030;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 16px;
  z-index: 10;

  .header-left, .header-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .divider {
    width: 1px;
    height: 20px;
    background: #363c4e;
  }

  :deep(.ant-btn) {
    border-radius: 6px;
    font-size: 12px;
    &.ant-btn-primary { background: #3b82f6; border: none; }
  }
}

.ide-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.ide-sidebar {
  width: 240px;
  background: #1e1e1e;
  border-right: 1px solid #303030;
  transition: width 0.3s;
  display: flex;
  flex-direction: column;

  &.collapsed { width: 48px; }

  .sidebar-header {
    height: 40px;
    padding: 0 16px;
    display: flex;
    align-items: center;
    gap: 10px;
    background: #252526;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
    
    .toggle { margin-left: auto; font-size: 10px; color: #868993; }
  }

  .indicator-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;

    .indicator-item {
      padding: 8px 16px;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 13px;
      color: #969696;

      &:hover { background: #2a2d2e; color: #cccccc; }
      &.active { background: #37373d; color: #ffffff; }

      .actions {
        opacity: 0;
        transition: opacity 0.2s;
        font-size: 12px;
        &:hover { color: #ef4444; }
      }
      &:hover .actions { opacity: 1; }
    }
  }
}

.ide-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.editor-pane {
  background: #1e1e1e;
}

.resize-handle {
  height: 4px;
  background: #303030;
  cursor: row-resize;
  &:hover { background: #3b82f6; }
}

.bottom-pane {
  background: #1f1f1f;
  display: flex;
  flex-direction: column;

  .ide-tabs {
    flex: 1;
    display: flex;
    flex-direction: column;
    
    :deep(.ant-tabs-nav) {
      margin: 0;
      padding: 0 16px;
      background: #252526;
      border-bottom: 1px solid #303030;
    }
    
    :deep(.ant-tabs-content-holder) {
      flex: 1;
      overflow: hidden;
    }

    .pane-content {
      height: 100%;
      overflow-y: auto;
    }
  }
}

.results-layout {
  display: flex;
  height: 100%;
  
  .params-side {
    width: 280px;
    border-right: 1px solid #303030;
    height: 100%;
  }
  
  .results-main {
    flex: 1;
    height: 100%;
  }
}

.ai-empty {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #868993;
}
</style>
