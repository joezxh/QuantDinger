<template>
  <a-modal
    :visible="visible"
    :title="editingAlert ? '编辑价格预警' : '添加价格预警'"
    @ok="handleOk"
    @cancel="$emit('close')"
    :confirmLoading="loading"
    width="500px"
  >
    <a-form layout="vertical">
      <div class="alert-info-banner">
        <div class="symbol">{{ targetPosition?.symbol }}</div>
        <div class="price">当前价格: ${{ formatPrice(targetPosition?.current_price) }}</div>
      </div>

      <a-form-item :label="t('batch.auto206')" required>
        <a-select v-model:value="form.alert_type">
          <a-select-option value="price_above">{{ t('batch.auto211') }}</a-select-option>
          <a-select-option value="price_below">{{ t('batch.auto212') }}</a-select-option>
          <a-select-option value="pnl_above">{{ t('batch.auto213') }}</a-select-option>
          <a-select-option value="pnl_below">{{ t('batch.auto214') }}</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item :label="isPriceAlert ? '目标价格' : '目标收益率 (%)'" required>
        <a-input-number v-model:value="form.threshold" style="width: 100%" :precision="isPriceAlert ? 4 : 2" />
      </a-form-item>

      <a-form-item :label="t('batch.auto207')">
        <a-select v-model:value="form.repeat_interval">
          <a-select-option :value="0">{{ t('batch.auto215') }}</a-select-option>
          <a-select-option :value="5">{{ t('batch.auto216') }}</a-select-option>
          <a-select-option :value="15">{{ t('batch.auto217') }}</a-select-option>
          <a-select-option :value="60">{{ t('batch.auto218') }}</a-select-option>
          <a-select-option :value="1440">{{ t('batch.auto219') }}</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item :label="t('batch.auto208')">
        <a-checkbox-group v-model:value="form.notification_config.channels">
          <a-checkbox value="browser">浏览器推送</a-checkbox>
          <a-checkbox value="telegram">Telegram</a-checkbox>
          <a-checkbox value="email">邮件通知</a-checkbox>
        </a-checkbox-group>
      </a-form-item>

      <a-form-item :label="t('batch.auto209')">
        <a-textarea v-model:value="form.notes" :rows="2" :placeholder="t('batch.auto205')" />
      </a-form-item>

      <a-form-item :label="t('batch.auto210')">
        <a-switch v-model:checked="form.is_active" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'

const { t } = useI18n()
const props = defineProps<{
  visible: boolean
  editingAlert: any
  targetPosition: any
}>()

const emit = defineEmits(['close', 'save'])

const loading = ref(false)

const form = reactive({
  alert_type: 'price_above',
  threshold: 0,
  repeat_interval: 0,
  notification_config: {
    channels: ['browser']
  },
  is_active: true,
  notes: ''
})

const isPriceAlert = computed(() => form.alert_type.startsWith('price_'))

watch(() => props.visible, (val) => {
  if (val) {
    if (props.editingAlert) {
      Object.assign(form, props.editingAlert)
      if (typeof form.notification_config === 'string') {
        try { form.notification_config = JSON.parse(form.notification_config) } catch (e) {
           form.notification_config = { channels: ['browser'] }
        }
      }
    } else {
      resetForm()
      form.threshold = props.targetPosition?.current_price || 0
    }
  }
})

const resetForm = () => {
  form.alert_type = 'price_above'
  form.threshold = 0
  form.repeat_interval = 0
  form.notification_config = { channels: ['browser'] }
  form.is_active = true
  form.notes = ''
}

const formatPrice = (price: number) => {
  if (!price) return '0.00'
  return price >= 1 ? price.toFixed(4) : price.toFixed(6)
}

const handleOk = () => {
  if (form.threshold === 0) {
    message.warning(t('batch.auto204'))
    return
  }
  emit('save', {
    ...form,
    position_id: props.targetPosition?.id,
    symbol: props.targetPosition?.symbol,
    market: props.targetPosition?.market
  })
}
</script>

<style scoped lang="less">
.alert-info-banner {
  background: #f0f9ff;
  border: 1px solid #e0f2fe;
  border-radius: 8px;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;

  .symbol { font-weight: 800; font-size: 16px; color: #0369a1; }
  .price { font-size: 13px; color: #0c4a6e; }
}
</style>
