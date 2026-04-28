<template>
  <a-modal
    :visible="visible"
    :title="editingMonitor ? '编辑监控任务' : '新建监控任务'"
    @ok="handleOk"
    @cancel="$emit('close')"
    :confirmLoading="loading"
    width="580px"
  >
    <a-form layout="vertical">
      <a-form-item label="任务名称" required>
        <a-input v-model:value="form.name" placeholder="例如: 每日资产分析" />
      </a-form-item>

      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="执行间隔" required>
            <a-select v-model:value="form.config.interval_minutes">
              <a-select-option :value="5">5 分钟</a-select-option>
              <a-select-option :value="15">15 分钟</a-select-option>
              <a-select-option :value="60">1 小时</a-select-option>
              <a-select-option :value="240">4 小时</a-select-option>
              <a-select-option :value="1440">每天 (24小时)</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="监控范围" required>
            <a-radio-group v-model:value="scopeType" button-style="solid" style="width: 100%">
              <a-radio-button value="all" style="width: 50%; text-align: center">全部持仓</a-radio-button>
              <a-radio-button value="selected" style="width: 50%; text-align: center">指定持仓</a-radio-button>
            </a-radio-group>
          </a-form-item>
        </a-col>
      </a-row>

      <a-form-item v-if="scopeType === 'selected'" label="选择监控持仓" required>
        <a-select
          v-model:value="form.position_ids"
          mode="multiple"
          placeholder="搜索并选择持仓"
          style="width: 100%"
        >
          <a-select-option v-for="p in positions" :key="p.id" :value="p.id">
            {{ p.symbol }} ({{ p.name }})
          </a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="AI 分析提示词 (Prompt)">
        <a-textarea
          v-model:value="form.config.prompt"
          :rows="4"
          placeholder="可选: 输入特定的分析指令，AI 将根据此指令对持仓进行深度评估..."
        />
        <div class="hint">留空则使用系统默认的资产评估模板</div>
      </a-form-item>

      <a-form-item label="通知渠道">
        <a-checkbox-group v-model:value="form.notification_config.channels">
          <a-checkbox value="browser">浏览器推送</a-checkbox>
          <a-checkbox value="telegram">Telegram</a-checkbox>
          <a-checkbox value="email">邮件通知</a-checkbox>
        </a-checkbox-group>
      </a-form-item>

      <a-form-item label="激活状态">
        <a-switch v-model:checked="form.is_active" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { message } from 'ant-design-vue'

const props = defineProps<{
  visible: boolean
  editingMonitor: any
  positions: any[]
}>()

const emit = defineEmits(['close', 'save'])

const loading = ref(false)
const scopeType = ref('all')

const form = reactive({
  name: '',
  monitor_type: 'ai',
  position_ids: [] as number[],
  config: {
    interval_minutes: 60,
    prompt: '',
    language: 'zh-CN'
  },
  notification_config: {
    channels: ['browser']
  },
  is_active: true
})

watch(() => props.visible, (val) => {
  if (val) {
    if (props.editingMonitor) {
      // Clone monitor data
      const m = props.editingMonitor
      form.name = m.name
      form.is_active = m.is_active
      form.config = { ...m.config }
      form.notification_config = { ...m.notification_config }
      
      const pids = getPositionIds(m)
      form.position_ids = pids
      scopeType.value = pids.length > 0 ? 'selected' : 'all'
    } else {
      resetForm()
    }
  }
})

const getPositionIds = (monitor: any) => {
  const ids = monitor.position_ids
  if (!ids) return []
  if (typeof ids === 'string') {
    try { return JSON.parse(ids) } catch (e) { return [] }
  }
  return Array.isArray(ids) ? ids : []
}

const resetForm = () => {
  form.name = ''
  form.position_ids = []
  form.config = { interval_minutes: 60, prompt: '', language: 'zh-CN' }
  form.notification_config = { channels: ['browser'] }
  form.is_active = true
  scopeType.value = 'all'
}

const handleOk = () => {
  if (!form.name) {
    message.warning('请输入任务名称')
    return
  }
  if (scopeType.value === 'selected' && form.position_ids.length === 0) {
    message.warning('请至少选择一个监控持仓')
    return
  }

  const submitData = {
    ...form,
    position_ids: scopeType.value === 'all' ? [] : form.position_ids
  }
  emit('save', submitData)
}
</script>

<style scoped lang="less">
.hint {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
}
</style>
