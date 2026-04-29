<template>
  <div class="monitors-section">
    <div class="section-header">
      <div class="title">
        <EyeOutlined />
        <span>{{ t('batch.auto235') }}</span>
      </div>
      <a-button type="primary" size="small" @click="$emit('add-monitor')">
        <PlusOutlined /> 新建监控
      </a-button>
    </div>

    <div class="monitors-content">
      <div v-if="monitors.length === 0" class="empty-state">
        <a-empty description="暂无监控任务" />
      </div>

      <div v-else class="monitor-list">
        <div v-for="monitor in monitors" :key="monitor.id" class="monitor-card">
          <div class="card-header">
            <div class="name-info">
              <RobotOutlined />
              <span class="name">{{ monitor.name }}</span>
            </div>
            <a-switch
              :checked="monitor.is_active"
              size="small"
              @change="(val: boolean) => $emit('toggle-monitor', monitor.id, val)"
            />
          </div>

          <div class="card-body">
            <div class="info-row">
              <span class="lbl">执行间隔:</span>
              <span class="val">{{ getIntervalText(monitor.config.interval_minutes) }}</span>
            </div>
            <div class="info-row">
              <span class="lbl">监控范围:</span>
              <span class="val">
                <template v-if="getMonitorPositionIds(monitor).length > 0">
                  <a-tooltip>
                    <template #title>
                      <div v-for="posId in getMonitorPositionIds(monitor)" :key="posId">
                        {{ getPositionName(posId) }}
                      </div>
                    </template>
                    <span class="scope-link">部分持仓 ({{ getMonitorPositionIds(monitor).length }})</span>
                  </a-tooltip>
                </template>
                <span v-else class="scope-all">全部持仓</span>
              </span>
            </div>
            <div class="info-row" v-if="monitor.last_run_at">
              <span class="lbl">上次运行:</span>
              <span class="val">{{ formatDate(monitor.last_run_at) }}</span>
            </div>
          </div>

          <div class="card-actions">
            <a-button type="link" size="small" @click="$emit('run-monitor', monitor.id)" :loading="runningId === monitor.id">
              <PlayCircleOutlined /> 立即运行
            </a-button>
            <a-button type="link" size="small" @click="$emit('edit-monitor', monitor)">
              <EditOutlined />
            </a-button>
            <a-popconfirm :title="t('batch.auto234')" @confirm="$emit('delete-monitor', monitor.id)">
              <a-button type="link" size="small" danger>
                <DeleteOutlined />
              </a-button>
            </a-popconfirm>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { 
  EyeOutlined, PlusOutlined, RobotOutlined, 
  PlayCircleOutlined, EditOutlined, DeleteOutlined 
} from '@ant-design/icons-vue'

const { t } = useI18n()
const props = defineProps<{
  monitors: any[]
  positions: any[]
  runningId: number | null
}>()

defineEmits(['add-monitor', 'edit-monitor', 'delete-monitor', 'toggle-monitor', 'run-monitor'])

const getIntervalText = (minutes: number) => {
  if (!minutes) return '-'
  if (minutes < 60) return `${minutes}分钟`
  return `${minutes / 60}小时`
}

const getMonitorPositionIds = (monitor: any) => {
  const ids = monitor.position_ids
  if (!ids) return []
  if (typeof ids === 'string') {
    try { return JSON.parse(ids) } catch (e) { return [] }
  }
  return Array.isArray(ids) ? ids : []
}

const getPositionName = (id: number) => {
  const pos = props.positions.find(p => p.id === id)
  return pos ? `${pos.symbol} (${pos.name})` : `#${id}`
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString()
}
</script>

<style scoped lang="less">
.monitors-section {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);

  .section-header {
    padding: 16px 20px;
    border-bottom: 1px solid #f1f5f9;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .title {
      font-size: 15px;
      font-weight: 700;
      color: #1e293b;
      display: flex;
      align-items: center;
      gap: 8px;
      .anticon { color: #8b5cf6; }
    }
  }

  .monitors-content {
    padding: 16px;
  }

  .monitor-card {
    background: #f8fafc;
    border: 1px solid #f1f5f9;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;

    &:last-child { margin-bottom: 0; }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;

      .name-info {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 700;
        color: #1e293b;
        .anticon { color: #8b5cf6; font-size: 16px; }
      }
    }

    .card-body {
      .info-row {
        font-size: 12px;
        margin-bottom: 4px;
        display: flex;
        gap: 8px;
        .lbl { color: #64748b; }
        .val { color: #334155; font-weight: 600; }
        .scope-link { color: #3b82f6; cursor: help; border-bottom: 1px dashed #3b82f6; }
        .scope-all { color: #10b981; font-weight: 700; }
      }
    }

    .card-actions {
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid #f1f5f9;
      display: flex;
      gap: 8px;
      
      .ant-btn { 
        padding: 0; height: auto; font-size: 12px; 
        display: flex; align-items: center; gap: 4px;
      }
    }
  }
}
</style>
