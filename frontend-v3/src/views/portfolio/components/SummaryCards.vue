<template>
  <div class="summary-grid">
    <a-card class="stat-card primary">
      <div class="card-inner">
        <div class="icon-box">
          <WalletOutlined />
        </div>
        <div class="content">
          <div class="label">资产总市值</div>
          <div class="value">
            <span class="currency">$</span>
            <span class="amount">{{ formatNumber(summary.total_market_value) }}</span>
          </div>
          <div class="sub-value" v-if="summary.today_change !== undefined">
            <span :class="summary.today_change >= 0 ? 'up' : 'down'">
              今日: {{ summary.today_change >= 0 ? '+' : '' }}${{ formatNumber(summary.today_change) }}
            </span>
          </div>
        </div>
      </div>
    </a-card>

    <a-card class="stat-card">
      <div class="card-inner">
        <div class="icon-box cost">
          <DollarOutlined />
        </div>
        <div class="content">
          <div class="label">持有成本</div>
          <div class="value">${{ formatNumber(summary.total_cost) }}</div>
        </div>
      </div>
    </a-card>

    <a-card class="stat-card">
      <div class="card-inner">
        <div class="icon-box" :class="summary.total_pnl >= 0 ? 'profit' : 'loss'">
          <component :is="summary.total_pnl >= 0 ? 'RiseOutlined' : 'FallOutlined'" />
        </div>
        <div class="content">
          <div class="label">累计盈亏</div>
          <div class="value" :class="summary.total_pnl >= 0 ? 'up' : 'down'">
            {{ summary.total_pnl >= 0 ? '+' : '' }}${{ formatNumber(summary.total_pnl) }}
            <small class="percent">({{ summary.total_pnl_percent >= 0 ? '+' : '' }}{{ summary.total_pnl_percent }}%)</small>
          </div>
        </div>
      </div>
    </a-card>

    <a-card class="stat-card">
      <div class="card-inner">
        <div class="icon-box positions">
          <FundOutlined />
        </div>
        <div class="content">
          <div class="label">持仓数量</div>
          <div class="value">{{ summary.position_count }}</div>
          <div class="sub-value" v-if="profitLossStats.profit > 0 || profitLossStats.loss > 0">
            <span class="up">{{ profitLossStats.profit }} 盈</span>
            <span class="divider">/</span>
            <span class="down">{{ profitLossStats.loss }} 亏</span>
          </div>
        </div>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { WalletOutlined, DollarOutlined, RiseOutlined, FallOutlined, FundOutlined } from '@ant-design/icons-vue'

defineProps<{
  summary: any
  profitLossStats: any
}>()

const formatNumber = (num: number) => {
  if (num === undefined || num === null) return '0.00'
  return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>

<style scoped lang="less">
.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;

  .stat-card {
    border-radius: 16px;
    border: none;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    overflow: hidden;
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }

    &.primary {
      background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
      color: #fff;
      .label { color: rgba(255, 255, 255, 0.7); }
      .icon-box { background: rgba(255, 255, 255, 0.1); color: #fff; }
    }

    .card-inner {
      display: flex;
      gap: 16px;
      align-items: center;
    }

    .icon-box {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      background: #f1f5f9;
      color: #64748b;
      
      &.cost { background: #ecfdf5; color: #10b981; }
      &.profit { background: #f0fdf4; color: #22c55e; }
      &.loss { background: #fef2f2; color: #ef4444; }
      &.positions { background: #eff6ff; color: #3b82f6; }
    }

    .content {
      .label { font-size: 13px; color: #64748b; margin-bottom: 4px; font-weight: 600; }
      .value { 
        font-size: 22px; font-weight: 800; color: #1e293b;
        display: flex; align-items: baseline; gap: 4px;
        .currency { font-size: 14px; opacity: 0.6; }
        .percent { font-size: 13px; font-weight: 600; margin-left: 4px; }
        &.up { color: #10b981; }
        &.down { color: #ef4444; }
      }
      .sub-value {
        font-size: 12px; font-weight: 600; margin-top: 4px;
        .up { color: #10b981; }
        .down { color: #ef4444; }
        .divider { margin: 0 4px; opacity: 0.3; }
      }
    }
  }
}

// Dark mode overrides
:deep(.ant-card) {
  &.primary { color: #fff; }
}
</style>
