<template>
  <div class="strategy-list-container">
    <div class="list-header">
      <div class="search-box">
        <a-input-search
          v-model:value="searchText"
          placeholder="搜索策略或标的..."
          size="small"
          allow-clear
        />
      </div>
      <div class="group-toggle">
        <a-radio-group v-model:value="groupBy" size="small" button-style="solid">
          <a-radio-button value="strategy">按策略</a-radio-button>
          <a-radio-button value="symbol">按标的</a-radio-button>
        </a-radio-group>
      </div>
    </div>

    <div class="list-content">
      <template v-if="loading">
        <div class="loading-wrap">
          <a-spin />
        </div>
      </template>
      <template v-else-if="groupedStrategies.length === 0">
        <a-empty description="暂无策略" />
      </template>
      <template v-else>
        <div v-for="group in groupedStrategies" :key="group.name" class="group-section">
          <div class="group-title">
            <span class="name">{{ group.name }}</span>
            <span class="count">{{ group.items.length }}</span>
          </div>
          <div 
            v-for="item in group.items" 
            :key="item.id" 
            class="strategy-item"
            :class="{ active: selectedId === item.id }"
            @click="$emit('select', item)"
          >
            <div class="item-main">
              <div class="item-info">
                <span class="symbol">{{ item.symbol }}</span>
                <span class="strategy-name">{{ item.name }}</span>
              </div>
              <div class="item-status">
                <a-badge :status="item.status === 'running' ? 'processing' : 'default'" />
                <span class="status-text">{{ item.status === 'running' ? '运行中' : '已停止' }}</span>
              </div>
            </div>
            <div class="item-meta">
              <span class="market">{{ item.market }}</span>
              <span class="pnl" :class="item.today_pnl >= 0 ? 'up' : 'down'">
                {{ item.today_pnl >= 0 ? '+' : '' }}{{ item.today_pnl.toFixed(2) }}%
              </span>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  strategies: any[]
  selectedId: number | null
  loading: boolean
}>()

const emit = defineEmits(['select'])

const searchText = ref('')
const groupBy = ref('strategy')

const filteredStrategies = computed(() => {
  if (!searchText.value) return props.strategies
  const query = searchText.value.toLowerCase()
  return props.strategies.filter(s => 
    s.name.toLowerCase().includes(query) || 
    s.symbol.toLowerCase().includes(query)
  )
})

const groupedStrategies = computed(() => {
  const groups: Record<string, any[]> = {}
  
  filteredStrategies.value.forEach(s => {
    const key = groupBy.value === 'strategy' ? (s.strategy_type || '其他') : (s.market || '其他')
    if (!groups[key]) groups[key] = []
    groups[key].push(s)
  })

  return Object.keys(groups).sort().map(name => ({
    name,
    items: groups[name]
  }))
})
</script>

<style scoped lang="less">
.strategy-list-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);

  .list-header {
    padding: 16px;
    border-bottom: 1px solid #f1f5f9;
    
    .search-box { margin-bottom: 12px; }
    .group-toggle {
      :deep(.ant-radio-group) { width: 100%; display: flex; }
      :deep(.ant-radio-button-wrapper) { flex: 1; text-align: center; }
    }
  }

  .list-content {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;

    .loading-wrap {
      height: 100px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  }

  .group-section {
    margin-bottom: 8px;

    .group-title {
      padding: 8px 16px;
      background: #f8fafc;
      font-size: 11px;
      font-weight: 700;
      color: #64748b;
      display: flex;
      justify-content: space-between;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
  }

  .strategy-item {
    padding: 12px 16px;
    cursor: pointer;
    transition: all 0.2s;
    border-left: 3px solid transparent;

    &:hover { background: #f1f5f9; }
    &.active {
      background: #eff6ff;
      border-left-color: #3b82f6;
      .symbol { color: #3b82f6; }
    }

    .item-main {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 4px;

      .item-info {
        display: flex;
        flex-direction: column;
        .symbol { font-weight: 800; font-size: 14px; color: #1e293b; }
        .strategy-name { font-size: 12px; color: #64748b; }
      }

      .item-status {
        display: flex;
        align-items: center;
        gap: 4px;
        .status-text { font-size: 11px; color: #94a3b8; }
      }
    }

    .item-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
      
      .market { color: #94a3b8; }
      .pnl {
        font-weight: 700;
        &.up { color: #10b981; }
        &.down { color: #ef4444; }
      }
    }
  }
}
</style>
