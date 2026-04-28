<template>
  <div class="notice-icon-wrapper">
    <a-popover
      v-model:visible="visible"
      trigger="click"
      placement="bottomRight"
      overlay-class-name="header-notice-popover"
      :overlay-style="{ width: '380px' }"
    >
      <template #content>
        <div class="notice-header">
          <span class="notice-title">{{ $t('notice.title') }}</span>
          <a v-if="notifications.length > 0" class="notice-action" @click="handleMarkAllRead">
            {{ $t('notice.markAllRead') }}
          </a>
        </div>
        
        <a-spin :spinning="loading">
          <div v-if="notifications.length > 0" class="notice-list">
            <div
              v-for="item in notifications"
              :key="item.id"
              class="notice-item"
              :class="{ unread: !item.is_read }"
              @click="handleNoticeClick(item)"
            >
              <div class="notice-item-icon">
                <component 
                  :is="getNoticeIcon(item.signal_type)" 
                  :style="{ color: getNoticeColor(item.signal_type) }" 
                />
              </div>
              <div class="notice-item-content">
                <div class="notice-item-title">{{ item.title }}</div>
                <div class="notice-item-desc">{{ truncateMessage(item.message) }}</div>
                <div class="notice-item-time">{{ formatTime(item.created_at) }}</div>
              </div>
            </div>
          </div>
          <div v-else class="notice-empty">
            <a-empty :description="$t('notice.empty')" />
          </div>
        </a-spin>
        
        <div v-if="notifications.length > 0" class="notice-footer">
          <a @click="handleClearNotifications">{{ $t('notice.clear') }}</a>
        </div>
      </template>
      
      <span class="header-action-item" @click="fetchNotifications">
        <a-badge :count="unreadTotal" :overflow-count="99">
          <BellOutlined />
        </a-badge>
      </span>
    </a-popover>

    <!-- Notification Detail Modal -->
    <a-modal
      v-model:visible="detailVisible"
      :title="detailNotice?.title"
      :footer="null"
      :width="isHtmlReport ? 900 : 600"
      centered
      class="notice-detail-modal"
    >
      <div v-if="detailNotice" class="notice-detail">
        <div class="notice-detail-meta">
          <div class="notice-detail-type">
            <component 
              :is="getNoticeIcon(detailNotice.signal_type)" 
              :style="{ color: getNoticeColor(detailNotice.signal_type) }" 
            />
            <span class="type-label">{{ getNoticeTypeLabel(detailNotice.signal_type) }}</span>
          </div>
          <div class="notice-detail-time">
            <ClockCircleOutlined />
            <span>{{ formatFullTime(detailNotice.created_at) }}</span>
          </div>
        </div>

        <a-divider />

        <div class="notice-detail-content" :class="{ 'html-report': isHtmlReport }">
          <div class="message-body" v-html="formatMessageHtml(detailNotice.message)"></div>
        </div>

        <template v-if="!isHtmlReport && detailNotice.payload && Object.keys(detailNotice.payload).length > 0">
          <a-divider />
          <div class="notice-detail-extra">
            <div class="extra-title">{{ $t('notice.detailInfo') }}</div>
            
            <!-- AI Analysis -->
            <template v-if="detailNotice.signal_type === 'ai_monitor'">
              <div v-if="detailNotice.payload.final_decision" class="extra-item decision">
                <span class="label">{{ $t('notice.aiDecision') }}:</span>
                <a-tag :color="getDecisionColor(detailNotice.payload.final_decision)">
                  {{ detailNotice.payload.final_decision }}
                </a-tag>
                <span v-if="detailNotice.payload.confidence" class="confidence">
                  ({{ $t('notice.confidence') }}: {{ detailNotice.payload.confidence }}%)
                </span>
              </div>
              <div v-if="detailNotice.payload.reasoning" class="extra-item">
                <span class="label">{{ $t('notice.reasoning') }}:</span>
                <span class="value">{{ detailNotice.payload.reasoning }}</span>
              </div>
            </template>

            <!-- Price Alert -->
            <template v-if="detailNotice.signal_type === 'price_alert'">
              <div v-if="detailNotice.payload.symbol" class="extra-item">
                <span class="label">{{ $t('notice.symbol') }}:</span>
                <span class="value">{{ detailNotice.payload.symbol }}</span>
              </div>
              <div v-if="detailNotice.payload.price" class="extra-item">
                <span class="label">{{ $t('notice.currentPrice') }}:</span>
                <span class="value">${{ detailNotice.payload.price }}</span>
              </div>
              <div v-if="detailNotice.payload.trigger_price" class="extra-item">
                <span class="label">{{ $t('notice.triggerPrice') }}:</span>
                <span class="value">${{ detailNotice.payload.trigger_price }}</span>
              </div>
            </template>
          </div>
        </template>

        <div class="notice-detail-actions">
          <a-button v-if="detailNotice.payload?.monitor_id" type="primary" @click="goToPortfolio">
            <FundOutlined />
            {{ $t('notice.viewPortfolio') }}
          </a-button>
          <a-button @click="detailVisible = false">{{ $t('notice.close') }}</a-button>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  BellOutlined,
  RobotOutlined,
  ThunderboltOutlined,
  RiseOutlined,
  FallOutlined,
  PauseCircleOutlined,
  SwapOutlined,
  NotificationOutlined,
  ClockCircleOutlined,
  FundOutlined,
} from '@ant-design/icons-vue'
import { getStrategyNotifications, getUnreadNotificationCount } from '@/api/strategy'
import request from '@/utils/request'

const router = useRouter()
const { t } = useI18n()

const loading = ref(false)
const visible = ref(false)
const detailVisible = ref(false)
const detailNotice = ref<any>(null)
const notifications = ref<any[]>([])
const unreadTotal = ref(0)
let pollingTimer: any = null

const unreadCount = computed(() => Number(unreadTotal.value || 0))

const isHtmlReport = computed(() => {
  if (!detailNotice.value?.message) return false
  return detailNotice.value.message.includes('<div class="qd-report">') ||
         detailNotice.value.message.includes('<style>')
})

const fetchUnreadCount = async (silent = false) => {
  try {
    const res: any = await getUnreadNotificationCount()
    if (res?.code === 1 && res.data) {
      unreadTotal.value = Number(res.data.unread || 0)
    }
  } catch (e) {
    if (!silent) console.error(e)
  }
}

const fetchNotifications = async (silent = false) => {
  if (!silent) loading.ref = true
  try {
    const res: any = await getStrategyNotifications({ limit: 50 })
    if (res?.code === 1 && res.data?.items) {
      notifications.value = res.data.items.map((item: any) => {
        let payload = item.payload_json
        if (typeof payload === 'string') {
          try {
            payload = JSON.parse(payload)
          } catch {
            payload = {}
          }
        }
        return {
          ...item,
          payload,
          is_read: item.is_read === 1 || item.is_read === true
        }
      })
    }
  } catch (e) {
    console.error('Failed to fetch notifications:', e)
  } finally {
    loading.value = false
  }
}

const handleNoticeClick = (item: any) => {
  markAsRead(item.id)
  detailNotice.value = item
  detailVisible.value = true
  visible.value = false
}

const markAsRead = async (id: number) => {
  const item = notifications.value.find(n => n.id === id)
  if (item && !item.is_read) {
    item.is_read = true
    try {
      await request.post('/api/strategies/notifications/read', { id })
      fetchUnreadCount(true)
    } catch (e) {
      console.error(e)
    }
  }
}

const handleMarkAllRead = async () => {
  notifications.value.forEach(n => { n.is_read = true })
  try {
    await request.post('/api/strategies/notifications/read-all')
    fetchUnreadCount(true)
  } catch (e) {
    console.error(e)
  }
}

const handleClearNotifications = async () => {
  notifications.value = []
  try {
    await request.delete('/api/strategies/notifications/clear')
    fetchUnreadCount(true)
  } catch (e) {
    console.error(e)
  }
  visible.value = false
}

const getNoticeIcon = (type: string) => {
  const iconMap: Record<string, any> = {
    'ai_monitor': RobotOutlined,
    'price_alert': BellOutlined,
    'signal': ThunderboltOutlined,
    'buy': RiseOutlined,
    'sell': FallOutlined,
    'hold': PauseCircleOutlined,
    'trade': SwapOutlined
  }
  return iconMap[type] || NotificationOutlined
}

const getNoticeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    'ai_monitor': '#722ed1',
    'price_alert': '#faad14',
    'signal': '#1890ff',
    'buy': '#52c41a',
    'sell': '#f5222d',
    'hold': '#faad14',
    'trade': '#13c2c2'
  }
  return colorMap[type] || '#1890ff'
}

const getNoticeTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    'ai_monitor': t('notice.type.aiMonitor'),
    'price_alert': t('notice.type.priceAlert'),
    'signal': t('notice.type.signal'),
    'buy': t('notice.type.buy'),
    'sell': t('notice.type.sell'),
    'hold': t('notice.type.hold'),
    'trade': t('notice.type.trade')
  }
  return labelMap[type] || t('notice.type.notification')
}

const getDecisionColor = (decision: string) => {
  const colorMap: Record<string, string> = {
    'BUY': 'green',
    'SELL': 'red',
    'HOLD': 'orange'
  }
  return colorMap[decision] || 'blue'
}

const truncateMessage = (msg: string) => {
  if (!msg) return ''
  return msg.length > 80 ? msg.substring(0, 80) + '...' : msg
}

const formatTime = (time: string | number) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return t('notice.justNow')
  if (minutes < 60) return `${minutes}${t('notice.minutesAgo')}`
  if (hours < 24) return `${hours}${t('notice.hoursAgo')}`
  if (days < 7) return `${days}${t('notice.daysAgo')}`
  return date.toLocaleDateString()
}

const formatFullTime = (time: string | number) => {
  if (!time) return ''
  return new Date(time).toLocaleString()
}

const formatMessageHtml = (msg: string) => {
  if (!msg) return ''
  if (msg.includes('<div class="qd-report">') || msg.includes('<style>')) return msg
  
  return msg
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/^### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^# (.+)$/gm, '<h2>$1</h2>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/\n/g, '<br>')
}

const goToPortfolio = () => {
  detailVisible.value = false
  router.push('/portfolio')
}

const startPolling = () => {
  stopPolling()
  pollingTimer = setInterval(() => {
    fetchUnreadCount(true)
    if (visible.value) fetchNotifications(true)
  }, 30000)
}

const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

onMounted(() => {
  fetchUnreadCount()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped lang="less">
.header-action-item {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 48px;
  padding: 0 12px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 18px;
  color: rgba(0, 0, 0, 0.45);

  &:hover {
    background: rgba(0, 0, 0, 0.025);
    color: #1890ff;
  }
}

.notice-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;

  .notice-title {
    font-weight: 500;
    font-size: 14px;
  }

  .notice-action {
    font-size: 12px;
    color: #1890ff;
    cursor: pointer;

    &:hover {
      color: #40a9ff;
    }
  }
}

.notice-list {
  max-height: 400px;
  overflow-y: auto;
}

.notice-item {
  display: flex;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.3s;

  &:hover {
    background: #f5f5f5;
  }

  &.unread {
    background: #e6f7ff;
    &:hover {
      background: #bae7ff;
    }
  }

  .notice-item-icon {
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f0f0f0;
    border-radius: 50%;
    margin-right: 12px;
    font-size: 16px;
  }

  .notice-item-content {
    flex: 1;
    min-width: 0;

    .notice-item-title {
      font-weight: 500;
      font-size: 13px;
      color: rgba(0, 0, 0, 0.85);
      margin-bottom: 4px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .notice-item-desc {
      font-size: 12px;
      color: rgba(0, 0, 0, 0.45);
      line-height: 1.5;
      margin-bottom: 4px;
    }

    .notice-item-time {
      font-size: 11px;
      color: rgba(0, 0, 0, 0.25);
    }
  }
}

.notice-empty {
  padding: 48px 0;
}

.notice-footer {
  text-align: center;
  padding: 12px;
  border-top: 1px solid #f0f0f0;
  a {
    color: #1890ff;
    &:hover { color: #40a9ff; }
  }
}

.notice-detail {
  .notice-detail-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    .notice-detail-type {
      display: flex;
      align-items: center;
      gap: 8px;
      .type-label { font-size: 14px; color: rgba(0, 0, 0, 0.65); }
    }
    .notice-detail-time {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      color: rgba(0, 0, 0, 0.45);
    }
  }

  .notice-detail-content {
    .message-body {
      font-size: 14px;
      line-height: 1.8;
      color: rgba(0, 0, 0, 0.85);
      max-height: 400px;
      overflow-y: auto;
      padding: 8px 0;
      :deep(h2), :deep(h3), :deep(h4) { margin: 12px 0 8px; font-weight: 600; }
      :deep(li) { margin-left: 20px; list-style: disc; }
    }
    &.html-report {
      .message-body { max-height: 70vh; margin: -16px -24px; }
    }
  }

  .notice-detail-extra {
    .extra-title { font-weight: 500; font-size: 14px; margin-bottom: 12px; }
    .extra-item {
      display: flex;
      margin-bottom: 8px;
      font-size: 13px;
      .label { color: rgba(0, 0, 0, 0.45); margin-right: 8px; }
      &.decision { align-items: center; .confidence { margin-left: 8px; color: rgba(0, 0, 0, 0.45); } }
    }
  }

  .notice-detail-actions {
    margin-top: 24px;
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
}

.dark, .realdark {
  .header-action-item {
    color: rgba(255, 255, 255, 0.85);
    &:hover { background: rgba(255, 255, 255, 0.05); }
  }
  .notice-header, .notice-footer, .notice-item-icon { border-color: #303030; background: transparent; }
  .notice-item {
    &:hover { background: #303030; }
    &.unread { background: rgba(24, 144, 255, 0.15); &:hover { background: rgba(24, 144, 255, 0.25); } }
    .notice-item-title { color: rgba(255, 255, 255, 0.85); }
    .notice-item-icon { background: #303030; }
  }
}
</style>
