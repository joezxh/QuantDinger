<template>
  <div class="positions-section">
    <div class="section-header">
      <div class="title">
        <StockOutlined />
        <span>{{ t('batch.auto239') }}</span>
      </div>
      <div class="actions">
        <a-radio-group v-model:value="viewMode" size="small" class="view-toggle">
          <a-radio-button value="grid"><AppstoreOutlined /></a-radio-button>
          <a-radio-button value="table"><BarsOutlined /></a-radio-button>
        </a-radio-group>
        
        <a-select
          v-model:value="selectedGroup"
          :placeholder="t('batch.auto236')"
          style="width: 140px"
          allow-clear
          @change="$emit('filter-group', selectedGroup)"
        >
          <a-select-option value="">{{ t('batch.auto236') }}</a-select-option>
          <a-select-option value="__ungrouped__">{{ t('batch.auto240') }}</a-select-option>
          <a-select-option v-for="g in groups" :key="g.name" :value="g.name">
            {{ g.name }}
          </a-select-option>
        </a-select>
        
        <a-button type="primary" @click="$emit('add-position')">
          <PlusOutlined /> 添加持仓
        </a-button>
      </div>
    </div>

    <div class="positions-content">
      <template v-if="positions.length === 0">
        <a-empty description="暂无持仓数据">
          <a-button type="primary" @click="$emit('add-position')">{{ t('batch.auto238') }}</a-button>
        </a-empty>
      </template>

      <!-- Grid View -->
      <div v-else-if="viewMode === 'grid'" class="position-grid">
        <div
          v-for="pos in positions"
          :key="pos.id"
          class="position-card"
          :class="pos.pnl >= 0 ? 'profit' : 'loss'"
        >
          <div class="card-header">
            <div class="symbol-info">
              <a-tag :color="getMarketColor(pos.market)">{{ pos.market }}</a-tag>
              <span class="symbol">{{ pos.symbol }}</span>
              <span class="name">{{ pos.name }}</span>
            </div>
            <div class="ops">
              <a-tooltip :title="hasAlert(pos.id) ? '编辑预警' : '添加预警'">
                <a-button type="link" size="small" @click="$emit('add-alert', pos)" :class="{ active: hasAlert(pos.id) }">
                  <BellOutlined v-if="!hasAlert(pos.id)" />
                  <BellFilled v-else />
                </a-button>
              </a-tooltip>
              <a-button type="link" size="small" @click="$emit('edit-position', pos)">
                <EditOutlined />
              </a-button>
              <a-popconfirm :title="t('batch.auto237')" @confirm="$emit('delete-position', pos.id)">
                <a-button type="link" size="small" danger>
                  <DeleteOutlined />
                </a-button>
              </a-popconfirm>
            </div>
          </div>
          
          <div class="card-body">
            <div class="main-stats">
              <div class="stat">
                <div class="lbl">当前价</div>
                <div class="val">{{ getCurrencySymbol(pos.market) }}{{ formatPrice(pos.current_price) }}</div>
                <div class="change" :class="pos.price_change >= 0 ? 'up' : 'down'">
                  {{ pos.price_change >= 0 ? '▲' : '▼' }}{{ Math.abs(pos.price_change_percent).toFixed(2) }}%
                </div>
              </div>
              <div class="stat">
                <div class="lbl">持有盈亏</div>
                <div class="val pnl" :class="pos.pnl >= 0 ? 'up' : 'down'">
                  {{ pos.pnl >= 0 ? '+' : '' }}{{ formatNumber(pos.pnl) }}
                </div>
                <div class="pnl-percent" :class="pos.pnl >= 0 ? 'up' : 'down'">
                  {{ pos.pnl_percent >= 0 ? '+' : '' }}{{ pos.pnl_percent }}%
                </div>
              </div>
            </div>
            
            <div class="secondary-stats">
              <div class="item">
                <span class="lbl">持有数量</span>
                <span class="val">{{ pos.quantity }}</span>
              </div>
              <div class="item">
                <span class="lbl">持仓成本</span>
                <span class="val">{{ getCurrencySymbol(pos.market) }}{{ formatPrice(pos.entry_price) }}</span>
              </div>
              <div class="item">
                <span class="lbl">市值</span>
                <span class="val">{{ getCurrencySymbol(pos.market) }}{{ formatNumber(pos.market_value) }}</span>
              </div>
            </div>
          </div>
          
          <div v-if="pos.group_name" class="card-footer">
            <FolderOutlined /> {{ pos.group_name }}
          </div>
        </div>
      </div>

      <!-- Table View -->
      <a-table
        v-else
        :columns="columns"
        :data-source="positions"
        :pagination="false"
        size="middle"
        class="position-table"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'symbol'">
            <div class="symbol-cell">
              <div class="symbol">{{ record.symbol }}</div>
              <div class="name">{{ record.name }}</div>
            </div>
          </template>
          <template v-if="column.key === 'market'">
            <a-tag :color="getMarketColor(record.market)">{{ record.market }}</a-tag>
          </template>
          <template v-if="column.key === 'price'">
            <div class="price-cell">
              <div class="val">{{ getCurrencySymbol(record.market) }}{{ formatPrice(record.current_price) }}</div>
              <div class="change" :class="record.price_change >= 0 ? 'up' : 'down'">
                {{ record.price_change >= 0 ? '+' : '' }}{{ record.price_change_percent }}%
              </div>
            </div>
          </template>
          <template v-if="column.key === 'pnl'">
            <div class="pnl-cell" :class="record.pnl >= 0 ? 'up' : 'down'">
              <div class="val">{{ record.pnl >= 0 ? '+' : '' }}{{ formatNumber(record.pnl) }}</div>
              <div class="percent">({{ record.pnl_percent >= 0 ? '+' : '' }}{{ record.pnl_percent }}%)</div>
            </div>
          </template>
          <template v-if="column.key === 'actions'">
            <div class="table-ops">
              <a-button type="link" size="small" @click="$emit('edit-position', record)">{{ t('common.edit') }}</a-button>
              <a-popconfirm :title="t('batch.auto113')" @confirm="$emit('delete-position', record.id)">
                <a-button type="link" size="small" danger>{{ t('common.delete') }}</a-button>
              </a-popconfirm>
            </div>
          </template>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { 
  StockOutlined, PlusOutlined, AppstoreOutlined, BarsOutlined, 
  BellOutlined, BellFilled, EditOutlined, DeleteOutlined, 
  FolderOutlined 
} from '@ant-design/icons-vue'

const { t } = useI18n()
const props = defineProps<{
  positions: any[]
  groups: any[]
  alerts: any[]
}>()

const emit = defineEmits(['add-position', 'edit-position', 'delete-position', 'add-alert', 'filter-group'])

const viewMode = ref('grid')
const selectedGroup = ref('')

const columns = [
  { title: t('batch.auto241'), key: 'symbol', fixed: 'left' },
  { title: t('common.market'), key: 'market' },
  { title: t('portfolio.quantity'), dataIndex: 'quantity', align: 'right' },
  { title: t('portfolio.avgCost'), dataIndex: 'entry_price', align: 'right' },
  { title: t('portfolio.currentPrice'), key: 'price', align: 'right' },
  { title: t('portfolio.pnl'), key: 'pnl', align: 'right' },
  { title: t('batch.auto242'), dataIndex: 'market_value', align: 'right' },
  { title: t('common.action'), key: 'actions', width: 120, fixed: 'right' }
]

const getMarketColor = (market: string) => {
  const colors: Record<string, string> = {
    'USStock': 'green',
    'Crypto': 'purple',
    'Forex': 'gold',
    'Futures': 'cyan'
  }
  return colors[market] || 'default'
}

const getCurrencySymbol = (market: string) => {
  const dollarMarkets = ['USStock', 'Crypto', 'Forex', 'Futures']
  return dollarMarkets.includes(market) ? '$' : '¥'
}

const formatNumber = (num: number) => {
  if (num === undefined || num === null) return '0.00'
  return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const formatPrice = (price: number) => {
  if (!price) return '0.00'
  if (price >= 1000) return formatNumber(price)
  if (price >= 1) return price.toFixed(4)
  return price.toFixed(6)
}

const hasAlert = (posId: number) => {
  return props.alerts.some(a => a.position_id === posId)
}
</script>

<style scoped lang="less">
.positions-section {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);

  .section-header {
    padding: 16px 24px;
    border-bottom: 1px solid #f1f5f9;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .title {
      font-size: 16px;
      font-weight: 700;
      color: #1e293b;
      display: flex;
      align-items: center;
      gap: 10px;
      .anticon { color: #3b82f6; }
    }

    .actions {
      display: flex;
      gap: 12px;
      align-items: center;
    }
  }

  .positions-content {
    padding: 24px;
  }

  .position-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
  }

  .position-card {
    background: #f8fafc;
    border: 1px solid #f1f5f9;
    border-radius: 14px;
    overflow: hidden;
    transition: all 0.3s ease;

    &:hover {
      border-color: #3b82f6;
      box-shadow: 0 8px 16px -4px rgba(0, 0, 0, 0.1);
    }

    &.profit { border-left: 4px solid #10b981; }
    &.loss { border-left: 4px solid #ef4444; }

    .card-header {
      padding: 12px 16px;
      border-bottom: 1px solid #f1f5f9;
      display: flex;
      justify-content: space-between;
      align-items: center;

      .symbol-info {
        display: flex;
        align-items: center;
        gap: 8px;
        .symbol { font-weight: 700; color: #1e293b; }
        .name { font-size: 11px; color: #64748b; }
      }

      .ops {
        display: flex;
        .ant-btn { color: #64748b; &.active { color: #f59e0b; } }
      }
    }

    .card-body {
      padding: 16px;

      .main-stats {
        display: flex;
        justify-content: space-between;
        margin-bottom: 16px;

        .stat {
          .lbl { font-size: 11px; color: #64748b; margin-bottom: 4px; }
          .val { font-size: 18px; font-weight: 800; color: #1e293b; }
          .val.pnl { font-size: 20px; }
          .change, .pnl-percent { 
            font-size: 12px; font-weight: 600; margin-top: 2px;
            &.up { color: #10b981; }
            &.down { color: #ef4444; }
          }
        }
      }

      .secondary-stats {
        display: flex;
        justify-content: space-between;
        background: #fff;
        padding: 10px;
        border-radius: 8px;
        .item {
          text-align: center;
          .lbl { display: block; font-size: 10px; color: #94a3b8; margin-bottom: 2px; }
          .val { font-size: 12px; font-weight: 700; color: #475569; }
        }
      }
    }

    .card-footer {
      padding: 8px 16px;
      background: #f1f5f9;
      font-size: 11px;
      color: #64748b;
      display: flex;
      align-items: center;
      gap: 4px;
    }
  }

  .symbol-cell {
    .symbol { font-weight: 700; color: #1e293b; }
    .name { font-size: 11px; color: #64748b; }
  }

  .price-cell, .pnl-cell {
    .val { font-weight: 700; color: #1e293b; }
    .change, .percent { font-size: 12px; font-weight: 600; }
    &.up { .val, .change, .percent { color: #10b981; } }
    &.down { .val, .change, .percent { color: #ef4444; } }
  }
}
</style>
