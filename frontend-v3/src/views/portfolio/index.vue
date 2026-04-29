<template>
  <div class="portfolio-page">
    <div class="page-header">
      <div class="title-area">
        <h1>{{ t('portfolio.myPortfolio') }}</h1>
        <p>{{ t('portfolio.subtitle') }}</p>
      </div>
      <div class="header-actions">
        <a-button @click="refreshAll" :loading="isSyncing">
          <SyncOutlined :spin="isSyncing" /> {{ t('portfolio.refreshPricesBtn') }}
        </a-button>
        <a-button type="primary" @click="openAddPosition">
          <PlusOutlined /> {{ t('portfolio.addAssetBtn') }}
        </a-button>
      </div>
    </div>

    <div class="portfolio-content">
      <!-- Summary Section -->
      <SummaryCards :summary="summary" :profit-loss-stats="profitLossStats" />

      <div class="main-layout">
        <!-- Left Column: Positions -->
        <div class="left-col">
          <PositionList
            :positions="positions"
            :groups="groups"
            :alerts="alerts"
            @add-position="openAddPosition"
            @edit-position="openEditPosition"
            @delete-position="handleDeletePosition"
            @add-alert="openAddAlert"
            @filter-group="handleGroupFilter"
          />
        </div>

        <!-- Right Column: Monitors -->
        <div class="right-col">
          <MonitorTask
            :monitors="monitors"
            :positions="positions"
            :running-id="runningMonitorId"
            @add-monitor="openAddMonitor"
            @edit-monitor="openEditMonitor"
            @delete-monitor="handleDeleteMonitor"
            @toggle-monitor="handleToggleMonitor"
            @run-monitor="handleRunMonitor"
          />
          
          <a-card class="market-dist-card" :title="t('portfolio.assetDistribution')">
            <div v-if="summary.market_distribution?.length > 0" class="dist-list">
              <div v-for="item in summary.market_distribution" :key="item.market" class="dist-item">
                <div class="info">
                  <span class="dot" :style="{ background: getMarketColor(item.market) }"></span>
                  <span class="lbl">{{ item.market }}</span>
                </div>
                <div class="val">{{ (item.weight * 100).toFixed(1) }}%</div>
              </div>
            </div>
            <a-empty v-else :image="simpleImage" />
          </a-card>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <PositionModal
      :visible="posModalVisible"
      :editing-position="editingPosition"
      :groups="groups"
      :market-types="marketTypes"
      @close="posModalVisible = false"
      @save="handleSavePosition"
    />

    <AlertModal
      :visible="alertModalVisible"
      :editing-alert="editingAlert"
      :target-position="selectedPosition"
      @close="alertModalVisible = false"
      @save="handleSaveAlert"
    />

    <MonitorModal
      :visible="monitorModalVisible"
      :editing-monitor="editingMonitor"
      :positions="positions"
      @close="monitorModalVisible = false"
      @save="handleSaveMonitor"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { message, Modal, Empty, notification } from 'ant-design-vue'
import { SyncOutlined, PlusOutlined } from '@ant-design/icons-vue'
import SummaryCards from './components/SummaryCards.vue'
import PositionList from './components/PositionList.vue'
import MonitorTask from './components/MonitorTask.vue'
import PositionModal from './components/PositionModal.vue'
import AlertModal from './components/AlertModal.vue'
import MonitorModal from './components/MonitorModal.vue'

import {
  getPositions, createPosition, updatePosition, deletePosition,
  getPortfolioSummary,
  getMonitors, createMonitor, updateMonitor, deleteMonitor, toggleMonitor, runMonitor,
  getAlerts, addAlert, updateAlert, deleteAlert as deleteAlertApi,
  getGroups, getMarketTypes
} from '@/api/portfolio'

const { t } = useI18n()
const simpleImage = Empty.PRESENTED_IMAGE_SIMPLE

// State
const loading = ref(false)
const isSyncing = ref(false)
const positions = ref<any[]>([])
const allPositions = ref<any[]>([])
const summary = ref<any>({ total_market_value: 0, total_cost: 0, total_pnl: 0, position_count: 0 })
const monitors = ref<any[]>([])
const alerts = ref<any[]>([])
const groups = ref<any[]>([])
const marketTypes = ref<any[]>([])
const runningMonitorId = ref<number | null>(null)
const refreshTimer = ref<any>(null)

// Modal State
const posModalVisible = ref(false)
const editingPosition = ref<any>(null)
const alertModalVisible = ref(false)
const editingAlert = ref<any>(null)
const selectedPosition = ref<any>(null)
const monitorModalVisible = ref(false)
const editingMonitor = ref<any>(null)

onMounted(() => {
  loadAllData()
  loadMeta()
  
  // Auto refresh price every 60s
  refreshTimer.value = setInterval(() => {
    refreshPrices()
  }, 60000)
})

onBeforeUnmount(() => {
  if (refreshTimer.value) clearInterval(refreshTimer.value)
})

const loadAllData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadPositions(),
      loadSummary(),
      loadMonitors(),
      loadAlerts(),
      loadGroups()
    ])
  } finally {
    loading.value = false
  }
}

const loadMeta = async () => {
  try {
    const res = await getMarketTypes()
    if (res.code === 1) {
      marketTypes.value = res.data.map((m: any) => ({ label: m.label || m.value, value: m.value }))
    }
  } catch (e) {}
}

const loadPositions = async (refresh = false) => {
  const res = await getPositions(refresh ? { refresh: '1' } : {})
  if (res.code === 1) {
    allPositions.value = res.data
    positions.value = res.data
  }
}

const loadSummary = async (refresh = false) => {
  const res = await getPortfolioSummary(refresh ? { refresh: '1' } : {})
  if (res.code === 1) summary.value = res.data
}

const loadMonitors = async () => {
  const res = await getMonitors()
  if (res.code === 1) monitors.value = res.data
}

const loadAlerts = async () => {
  const res = await getAlerts()
  if (res.code === 1) alerts.value = res.data
}

const loadGroups = async () => {
  const res = await getGroups()
  if (res.code === 1) groups.value = res.data.groups || []
}

const refreshPrices = async () => {
  if (isSyncing.value) return
  isSyncing.value = true
  try {
    await Promise.all([loadPositions(true), loadSummary(true)])
    message.success(t('portfolio.priceUpdated'))
  } finally {
    isSyncing.value = false
  }
}

const refreshAll = () => {
  refreshPrices()
}

// Actions
const openAddPosition = () => {
  editingPosition.value = null
  posModalVisible.value = true
}

const openEditPosition = (pos: any) => {
  editingPosition.value = pos
  posModalVisible.value = true
}

const handleSavePosition = async (data: any) => {
  try {
    let res
    if (editingPosition.value) {
      res = await updatePosition(editingPosition.value.id, data)
    } else {
      res = await createPosition(data)
    }
    if (res.code === 1) {
      message.success(t('common.saveSuccess'))
      posModalVisible.value = false
      loadAllData()
    } else {
      message.error(res.msg || t('common.saveFailed'))
    }
  } catch (e) {
    message.error(t('portfolio.requestFailed'))
  }
}

const handleDeletePosition = async (id: number) => {
  try {
    const res = await deletePosition(id)
    if (res.code === 1) {
      message.success(t('common.deleted'))
      loadAllData()
    }
  } catch (e) {
    message.error(t('common.deleteFailed'))
  }
}

const openAddAlert = (pos: any) => {
  selectedPosition.value = pos
  const existing = alerts.value.find(a => a.position_id === pos.id)
  editingAlert.value = existing || null
  alertModalVisible.value = true
}

const handleSaveAlert = async (data: any) => {
  try {
    let res
    if (editingAlert.value) {
      res = await updateAlert(editingAlert.value.id, data)
    } else {
      res = await addAlert(data)
    }
    if (res.code === 1) {
      message.success(t('common.saveSuccess'))
      alertModalVisible.value = false
      loadAlerts()
    }
  } catch (e) {
    message.error(t('common.saveFailed'))
  }
}

const openAddMonitor = () => {
  editingMonitor.value = null
  monitorModalVisible.value = true
}

const openEditMonitor = (m: any) => {
  editingMonitor.value = m
  monitorModalVisible.value = true
}

const handleSaveMonitor = async (data: any) => {
  try {
    let res
    if (editingMonitor.value) {
      res = await updateMonitor(editingMonitor.value.id, data)
    } else {
      res = await createMonitor(data)
    }
    if (res.code === 1) {
      message.success(t('common.updateSuccess'))
      monitorModalVisible.value = false
      loadMonitors()
    }
  } catch (e) {
    message.error(t('common.updateFailed'))
  }
}

const handleDeleteMonitor = async (id: number) => {
  try {
    const res = await deleteMonitor(id)
    if (res.code === 1) {
      message.success(t('common.deleted'))
      loadMonitors()
    }
  } catch (e) {}
}

const handleToggleMonitor = async (id: number, active: boolean) => {
  try {
    const res = await toggleMonitor(id, active)
    if (res.code === 1) {
      message.success(active ? t('portfolio.monitorEnabled') : t('portfolio.monitorDisabled'))
      loadMonitors()
    }
  } catch (e) {}
}

const handleRunMonitor = async (id: number) => {
  runningMonitorId.value = id
  try {
    const res = await runMonitor(id, { async: true })
    if (res.code === 1) {
      notification.info({
        message: t('portfolio.monitorTaskRunning'),
        description: t('portfolio.monitorTaskDesc')
      })
      loadMonitors()
    }
  } finally {
    runningMonitorId.value = null
  }
}

const handleGroupFilter = (groupName: string) => {
  if (!groupName) {
    positions.value = allPositions.value
  } else if (groupName === '__ungrouped__') {
    positions.value = allPositions.value.filter(p => !p.group_name)
  } else {
    positions.value = allPositions.value.filter(p => p.group_name === groupName)
  }
}

const profitLossStats = computed(() => {
  const profit = allPositions.value.filter(p => p.pnl >= 0).length
  const loss = allPositions.value.filter(p => p.pnl < 0).length
  return { profit, loss }
})

const getMarketColor = (market: string) => {
  const colors: Record<string, string> = {
    'USStock': '#10b981',
    'Crypto': '#8b5cf6',
    'Forex': '#f59e0b',
    'Futures': '#06b6d4'
  }
  return colors[market] || '#64748b'
}
</script>

<style scoped lang="less">
.portfolio-page {
  padding: 32px;
  background: #f8fafc;
  min-height: 100vh;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 32px;

    .title-area {
      h1 { font-size: 28px; font-weight: 800; color: #1e293b; margin-bottom: 8px; }
      p { font-size: 15px; color: #64748b; margin: 0; }
    }

    .header-actions {
      display: flex;
      gap: 12px;
      .ant-btn { height: 40px; border-radius: 10px; font-weight: 600; }
    }
  }

  .main-layout {
    display: grid;
    grid-template-columns: 1fr 340px;
    gap: 24px;
    align-items: start;
  }

  .right-col {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .market-dist-card {
    border-radius: 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    
    .dist-list {
      .dist-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid #f1f5f9;
        &:last-child { border-bottom: none; }
        
        .info {
          display: flex;
          align-items: center;
          gap: 10px;
          .dot { width: 10px; height: 10px; border-radius: 50%; }
          .lbl { font-size: 13px; color: #475569; font-weight: 600; }
        }
        .val { font-size: 14px; font-weight: 700; color: #1e293b; }
      }
    }
  }
}

// Responsive
@media (max-width: 1200px) {
  .main-layout {
    grid-template-columns: 1fr;
  }
}
</style>
