<template>
  <div class="trading-bot-page">
    <div class="page-header">
      <h2 class="page-title">
        <RobotOutlined />
        <span>{{ $t('menu.tradingBot', '交易机器人') }}</span>
      </h2>
      <p class="page-desc">部署、监控和管理自动化量化交易机器人</p>
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
              <div class="kpi-label">总投资额</div>
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
              <div class="kpi-label">总盈亏</div>
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
              <div class="kpi-label">运行中</div>
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
              <div class="kpi-label">已停止</div>
              <div class="kpi-value">{{ stoppedCount }}</div>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <!-- Bot Types -->
    <div class="section-title">
      <h3>新建机器人</h3>
    </div>
    <a-row :gutter="16" class="bot-types-row">
      <a-col :span="8">
        <a-card class="type-card" hoverable @click="createBot('grid')">
          <div class="type-icon"><AppstoreOutlined /></div>
          <div class="type-info">
            <h4>网格交易</h4>
            <p>在设定价格区间内自动低买高卖</p>
          </div>
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card class="type-card" hoverable @click="createBot('dca')">
          <div class="type-icon"><LineChartOutlined /></div>
          <div class="type-info">
            <h4>DCA定投</h4>
            <p>分批买入摊低成本，达标一次卖出</p>
          </div>
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card class="type-card ai-card" hoverable @click="showAiDialog = true">
          <div class="type-icon"><BulbOutlined /></div>
          <div class="type-info">
            <h4>AI 智能推荐</h4>
            <p>由 AI 根据当前行情分析推荐最佳策略</p>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <!-- Bot List -->
    <div class="section-title" style="margin-top: 24px;">
      <h3>我的机器人</h3>
      <a-button type="primary" size="small" @click="loadBots" :loading="loading">刷新</a-button>
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
            <strong>{{ record.name }}</strong>
            <span class="bot-type-tag">{{ record.bot_type || record.strategy_type }}</span>
          </div>
        </template>
        <template v-if="column.key === 'status'">
          <a-tag :color="record.status === 'running' ? 'success' : 'default'">
            {{ record.status === 'running' ? '运行中' : '已停止' }}
          </a-tag>
        </template>
        <template v-if="column.key === 'pnl'">
          <span :class="record.unrealized_pnl >= 0 ? 'profit' : 'loss'">
            {{ record.unrealized_pnl >= 0 ? '+' : '' }}${{ formatNumber(record.unrealized_pnl) }}
          </span>
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a-button type="link" size="small" @click="viewDetail(record)">详情</a-button>
            <a-button 
              type="link" 
              size="small" 
              :danger="record.status === 'running'"
              @click="toggleStatus(record)"
            >
              {{ record.status === 'running' ? '停止' : '启动' }}
            </a-button>
          </a-space>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { 
  RobotOutlined, WalletOutlined, StockOutlined, PlayCircleOutlined, PauseCircleOutlined,
  AppstoreOutlined, LineChartOutlined, BulbOutlined 
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { getStrategyList, startStrategy, stopStrategy } from '@/api/strategy'

const loading = ref(false)
const bots = ref<any[]>([])
const showAiDialog = ref(false)

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
  { title: '机器人名称', dataIndex: 'name', key: 'name' },
  { title: '交易对', dataIndex: 'symbol', key: 'symbol' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '当前盈亏', dataIndex: 'unrealized_pnl', key: 'pnl' },
  { title: '最后运行', dataIndex: 'last_run_at', key: 'last_run_at' },
  { title: '操作', key: 'action' }
]

const formatNumber = (num: number) => {
  if (!num) return '0.00'
  return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const loadBots = async () => {
  loading.value = true
  try {
    const res: any = await getStrategyList()
    if (res.code === 1) {
      // Filter for bots (assuming bots have bot_type or strategy_mode === 'bot')
      const all = res.data || []
      bots.value = all.filter((s: any) => s.strategy_mode === 'bot' || s.bot_type)
    }
  } catch (error) {
    message.error('Failed to load bots')
  } finally {
    loading.value = false
  }
}

const createBot = (type: string) => {
  message.info(`Creating ${type} bot wizard (Placeholder)`)
}

const viewDetail = (record: any) => {
  message.info(`Viewing details for ${record.name}`)
}

const toggleStatus = async (record: any) => {
  try {
    const action = record.status === 'running' ? stopStrategy : startStrategy
    const res: any = await action(record.id)
    if (res.code === 1) {
      message.success('状态已更新')
      loadBots()
    } else {
      message.error(res.msg || '操作失败')
    }
  } catch (error) {
    message.error('请求失败')
  }
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

.bot-types-row {
  margin-bottom: 32px;
}

.type-card {
  border-radius: 8px;
  cursor: pointer;
  
  &:hover {
    border-color: #1890ff;
    box-shadow: 0 4px 12px rgba(24,144,255,0.1);
  }
  
  :deep(.ant-card-body) {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px;
  }
  
  &.ai-card {
    background: linear-gradient(135deg, #f6f0ff 0%, #ffffff 100%);
    border-color: #d3adf7;
    
    &:hover {
      border-color: #722ed1;
      box-shadow: 0 4px 12px rgba(114,46,209,0.1);
    }
    
    .type-icon {
      color: #722ed1;
      background: rgba(114,46,209,0.1);
    }
  }
}

.type-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #1890ff;
  background: rgba(24,144,255,0.1);
  flex-shrink: 0;
}

.type-info {
  h4 {
    margin: 0 0 4px 0;
    font-size: 16px;
    font-weight: 600;
  }
  p {
    margin: 0;
    font-size: 12px;
    color: #8c8c8c;
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
  
  .bot-type-tag {
    font-size: 12px;
    color: #8c8c8c;
  }
}

.profit { color: #52c41a; }
.loss { color: #f5222d; }
</style>
