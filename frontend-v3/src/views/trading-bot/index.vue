<template>
  <div class="trading-bot-page">
    <div class="page-header">
      <h2 class="page-title">
        <RobotOutlined />
        <span>{{ t('menu.tradingBot') }}</span>
      </h2>
      <p class="page-desc">{{ t('trading-bot.pageSubtitle') }}</p>
    </div>

    <!-- KPI Cards -->
    <a-row :gutter="16" class="kpi-row">
      <a-col :span="6">
        <a-card class="kpi-card" :bordered="false">
          <div class="kpi-content">
            <div class="kpi-icon" style="color: #1890ff; background: rgba(24,144,255,0.1)">
              <WalletOutlined />
            </div>
            <div class="kpi-body">
              <div class="kpi-label">{{ t('trading-bot.totalInvestment') }}</div>
              <div class="kpi-value">${{ formatNumber(totalEquity) }}</div>
            </div>
          </div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="kpi-card" :bordered="false">
          <div class="kpi-content">
            <div class="kpi-icon" :style="{ color: totalPnl >= 0 ? '#52c41a' : '#f5222d', background: totalPnl >= 0 ? 'rgba(82,196,26,0.1)' : 'rgba(245,34,45,0.1)' }">
              <StockOutlined />
            </div>
            <div class="kpi-body">
              <div class="kpi-label">{{ t('portfolio.totalPnl') }}</div>
              <div class="kpi-value" :class="totalPnl >= 0 ? 'profit' : 'loss'">
                {{ totalPnl >= 0 ? '+' : '' }}${{ formatNumber(totalPnl) }}
              </div>
            </div>
          </div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="kpi-card" :bordered="false">
          <div class="kpi-content">
            <div class="kpi-icon" style="color: #722ed1; background: rgba(114,46,209,0.1)">
              <PlayCircleOutlined />
            </div>
            <div class="kpi-body">
              <div class="kpi-label">{{ t('status.running') }}</div>
              <div class="kpi-value">{{ runningCount }} / {{ totalCount }}</div>
            </div>
          </div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="kpi-card" :bordered="false">
          <div class="kpi-content">
            <div class="kpi-icon" style="color: #faad14; background: rgba(250,173,20,0.1)">
              <PauseCircleOutlined />
            </div>
            <div class="kpi-body">
              <div class="kpi-label">{{ t('status.stopped') }}</div>
              <div class="kpi-value">{{ stoppedCount }}</div>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <!-- Bot Type Cards -->
    <BotTypeCards
      @select="handleSelectBotType"
      @ai-create="showAiModal = true"
    />

    <!-- Bot List -->
    <div class="section-title" style="margin-top: 24px;">
      <h3>{{ t('trading-bot.myBots') }}</h3>
      <a-button type="primary" size="small" @click="loadBots" :loading="loading">
        <ReloadOutlined />
        {{ t('common.refresh') }}
      </a-button>
    </div>
    <a-table
      :columns="columns"
      :data-source="bots"
      :loading="loading"
      row-key="id"
      class="bot-table"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'name'">
          <div class="bot-name-cell">
            <strong>{{ record.strategy_name || record.name }}</strong>
            <a-tag size="small" color="purple">{{ record.bot_type || record.strategy_type }}</a-tag>
          </div>
        </template>
        <template v-if="column.key === 'status'">
          <a-tag :color="record.status === 'running' ? 'success' : 'default'">
            {{ record.status === 'running' ? t('status.running') : t('status.stopped') }}
          </a-tag>
        </template>
        <template v-if="column.key === 'pnl'">
          <span :class="(record.unrealized_pnl || 0) >= 0 ? 'profit' : 'loss'">
            {{ (record.unrealized_pnl || 0) >= 0 ? '+' : '' }}${{ formatNumber(record.unrealized_pnl || 0) }}
          </span>
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a-button type="link" size="small" @click="viewDetail(record)">{{ t('common.detail') }}</a-button>
            <a-button
              type="link"
              size="small"
              :danger="record.status === 'running'"
              @click="toggleStatus(record)"
            >
              {{ record.status === 'running' ? t('common.stop') : t('common.start') }}
            </a-button>
            <a-button type="link" size="small" @click="editBot(record)" :disabled="record.status === 'running'">
              {{ t('common.edit') }}
            </a-button>
            <a-popconfirm :title="t('common.deleteConfirm')" @confirm="deleteBot(record.id)">
              <a-button type="link" danger size="small" :disabled="record.status === 'running'">
                {{ t('common.delete') }}
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- Create/Edit Modal -->
    <BotCreateModal
      v-model:open="createModalOpen"
      :bot-type="selectedBotType"
      :edit-bot="editingBot"
      @success="loadBots"
    />

    <!-- Detail Modal -->
    <BotDetailModal
      v-model:open="detailModalOpen"
      :bot="selectedBot"
      @start="handleStart"
      @stop="handleStop"
      @edit="editBot"
      @delete="handleDeleteFromDetail"
    />

    <!-- AI Modal -->
    <AiBotModal
      v-model:open="showAiModal"
      @apply="handleAiApply"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  RobotOutlined, WalletOutlined, StockOutlined, PlayCircleOutlined, PauseCircleOutlined, ReloadOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { getStrategyList, startStrategy, stopStrategy, deleteStrategy } from '@/api/strategy'
import BotTypeCards from './components/BotTypeCards.vue'
import BotCreateModal from './components/BotCreateModal.vue'
import BotDetailModal from './components/BotDetailModal.vue'
import AiBotModal from './components/AiBotModal.vue'

const { t } = useI18n()
const loading = ref(false)
const bots = ref<any[]>([])
const createModalOpen = ref(false)
const detailModalOpen = ref(false)
const showAiModal = ref(false)
const selectedBotType = ref('grid')
const editingBot = ref<any>(null)
const selectedBot = ref<any>(null)

const totalEquity = computed(() => {
  return bots.value.reduce((sum, bot) => sum + (bot.trading_config?.initial_capital || 0), 0)
})

const totalPnl = computed(() => {
  return bots.value.reduce((sum, bot) => sum + (bot.unrealized_pnl || 0), 0)
})

const runningCount = computed(() => bots.value.filter(b => b.status === 'running').length)
const totalCount = computed(() => bots.value.length)
const stoppedCount = computed(() => totalCount.value - runningCount.value)

const columns = [
  { title: t('trading-bot.botName'), dataIndex: 'name', key: 'name' },
  { title: t('common.tradingPair'), dataIndex: 'symbol', key: 'symbol' },
  { title: t('common.status'), dataIndex: 'status', key: 'status' },
  { title: t('trading-bot.currentPnl'), dataIndex: 'unrealized_pnl', key: 'pnl' },
  { title: t('trading-bot.lastRun'), dataIndex: 'last_run_at', key: 'last_run_at' },
  { title: t('common.action'), key: 'action', width: 260 }
]

const formatNumber = (num: number) => {
  if (!num && num !== 0) return '0.00'
  return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const loadBots = async () => {
  loading.value = true
  try {
    const res: any = await getStrategyList()
    if (res.code === 1) {
      const all = res.data || []
      bots.value = all.filter((s: any) => s.strategy_mode === 'bot' || s.bot_type)
    }
  } catch (error) {
    message.error(t('common.loadFailed'))
  } finally {
    loading.value = false
  }
}

const handleSelectBotType = (type: string) => {
  selectedBotType.value = type
  editingBot.value = null
  createModalOpen.value = true
}

const viewDetail = (record: any) => {
  selectedBot.value = record
  detailModalOpen.value = true
}

const editBot = (record: any) => {
  selectedBotType.value = record.bot_type || record.strategy_type || 'grid'
  editingBot.value = record
  createModalOpen.value = true
}

const toggleStatus = async (record: any) => {
  try {
    const action = record.status === 'running' ? stopStrategy : startStrategy
    const res: any = await action(record.id)
    if (res.code === 1) {
      message.success(t('common.updateSuccess'))
      loadBots()
    } else {
      message.error(res.msg || t('common.failed'))
    }
  } catch (error) {
    message.error(t('common.failed'))
  }
}

const handleStart = (bot: any) => {
  toggleStatus(bot)
}

const handleStop = (bot: any) => {
  toggleStatus(bot)
}

const deleteBot = async (id: number) => {
  try {
    const res: any = await deleteStrategy(id)
    if (res.code === 1) {
      message.success(t('common.deleted'))
      loadBots()
    } else {
      message.error(res.msg || t('common.deleteFailed'))
    }
  } catch (error) {
    message.error(t('common.deleteFailed'))
  }
}

const handleDeleteFromDetail = (bot: any) => {
  detailModalOpen.value = false
  deleteBot(bot.id)
}

const handleAiApply = (preset: any) => {
  selectedBotType.value = preset.botType || 'grid'
  editingBot.value = null
  createModalOpen.value = true
}

onMounted(() => {
  loadBots()
})
</script>

<style scoped lang="less">
.trading-bot-page {
  padding: 18px;
  background: #f5f7fa;
  min-height: calc(100vh - 64px);
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-desc {
  color: #64748b;
  font-size: 14px;
  margin: 0;
}

.kpi-row {
  margin-bottom: 24px;
}

.kpi-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.kpi-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.kpi-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.kpi-label {
  font-size: 13px;
  color: #8c8c8c;
  margin-bottom: 4px;
}

.kpi-value {
  font-size: 20px;
  font-weight: bold;
  color: #262626;

  &.profit { color: #52c41a; }
  &.loss { color: #f5222d; }
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;

  h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
  }
}

.bot-table {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}

.bot-name-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;

  .ant-tag {
    width: fit-content;
  }
}

.profit { color: #52c41a; }
.loss { color: #f5222d; }
</style>
