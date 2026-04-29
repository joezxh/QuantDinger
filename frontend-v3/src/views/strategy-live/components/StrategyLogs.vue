<template>
  <div class="strategy-logs">
    <div class="logs-toolbar">
      <div class="status-info">
        <a-badge :status="isConnected ? 'success' : 'error'" :text="isConnected ? '已连接' : '已断开'" />
      </div>
      <div class="actions">
        <a-checkbox v-model:checked="autoScroll">自动滚动</a-checkbox>
        <a-button size="small" @click="clearLogs">清空日志</a-button>
      </div>
    </div>
    
    <div ref="logContainer" class="log-viewer">
      <div v-for="(log, idx) in logs" :key="idx" class="log-line" :class="log.level.toLowerCase()">
        <span class="time">[{{ log.time }}]</span>
        <span class="level">[{{ log.level }}]</span>
        <span class="msg">{{ log.message }}</span>
      </div>
      <div v-if="logs.length === 0" class="empty-logs">等待日志输出...</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const props = defineProps<{
  strategyId: number | null
  logs: any[]
  isConnected: boolean
}>()

const emit = defineEmits(['clear'])

const logContainer = ref<HTMLElement | null>(null)
const autoScroll = ref(true)

watch(() => props.logs.length, () => {
  if (autoScroll.value) {
    scrollToBottom()
  }
})

const scrollToBottom = () => {
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  })
}

const clearLogs = () => {
  emit('clear')
}

onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped lang="less">
.strategy-logs {
  display: flex;
  flex-direction: column;
  height: 500px;
  background: #1e1e1e;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #333;

  .logs-toolbar {
    padding: 8px 16px;
    background: #252526;
    border-bottom: 1px solid #333;
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .status-info { font-size: 12px; }
    .actions {
      display: flex;
      align-items: center;
      gap: 12px;
      :deep(.ant-checkbox-wrapper) { color: #868993; font-size: 12px; }
      .ant-btn { background: transparent; color: #868993; border-color: #444; font-size: 11px; }
    }
  }

  .log-viewer {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
    font-family: 'Cascadia Code', 'Courier New', Courier, monospace;
    font-size: 12px;
    line-height: 1.6;

    .log-line {
      margin-bottom: 2px;
      white-space: pre-wrap;
      word-break: break-all;
      
      .time { color: #569cd6; margin-right: 8px; }
      .level { margin-right: 8px; font-weight: bold; }
      .msg { color: #cccccc; }

      &.info .level { color: #4ec9b0; }
      &.warn .level { color: #ce9178; }
      &.error .level { color: #f44747; }
      &.debug .level { color: #808080; }
    }

    .empty-logs {
      color: #555;
      text-align: center;
      margin-top: 40px;
    }
  }
}
</style>
