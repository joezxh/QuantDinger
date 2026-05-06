<template>
  <a-form
    ref="formRef"
    :model="form"
    :rules="rules"
    :label-col="{ span: 8 }"
    :wrapper-col="{ span: 14 }"
  >
    <a-form-item :label="t('trading-bot.dca.amountEach')" name="amountEach">
      <a-input-number
        v-model:value="form.amountEach"
        :min="1"
        :step="10"
        style="width: 100%"
        :placeholder="t('trading-bot.dca.amountEachPh')"
        @change="emitPayload"
      />
    </a-form-item>
    <a-form-item :label="t('trading-bot.dca.frequency')" name="frequency">
      <a-select v-model:value="form.frequency" @change="emitPayload">
        <a-select-option value="every_bar">Every bar</a-select-option>
        <a-select-option value="hourly">{{ t('trading-bot.dca.hourly') }}</a-select-option>
        <a-select-option value="4h">4H</a-select-option>
        <a-select-option value="daily">{{ t('trading-bot.dca.daily') }}</a-select-option>
        <a-select-option value="weekly">{{ t('trading-bot.dca.weekly') }}</a-select-option>
        <a-select-option value="biweekly">{{ t('trading-bot.dca.biweekly') }}</a-select-option>
        <a-select-option value="monthly">{{ t('trading-bot.dca.monthly') }}</a-select-option>
      </a-select>
    </a-form-item>
    <a-form-item :label="t('trading-bot.dca.totalBudget')" name="totalBudget">
      <a-input-number
        v-model:value="form.totalBudget"
        :min="0"
        :step="100"
        style="width: 100%"
        :placeholder="t('trading-bot.dca.totalBudgetPh')"
        @change="emitPayload"
      />
    </a-form-item>
    <a-form-item :label="t('trading-bot.dca.dipBuy')">
      <a-switch v-model:checked="form.dipBuyEnabled" @change="emitPayload" />
      <span class="dip-buy-hint">
        {{ t('trading-bot.dca.dipBuyHint') }}
      </span>
    </a-form-item>
    <a-form-item
      v-if="form.dipBuyEnabled"
      :label="t('trading-bot.dca.dipThreshold')"
    >
      <a-input-number
        v-model:value="form.dipThreshold"
        :min="1"
        :max="50"
        :step="1"
        style="width: 100%"
        :formatter="(v: number) => `${v}%`"
        :parser="(v: string) => v.replace('%', '')"
        @change="emitPayload"
      />
    </a-form-item>
    <div
      class="config-summary"
      v-if="form.amountEach && form.frequency"
    >
      <div class="summary-item">
        <span class="label">{{ t('trading-bot.dca.estimatedRuns') }}</span>
        <span class="value">{{ estimatedRuns }}</span>
      </div>
    </div>
  </a-form>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { FormInstance } from 'ant-design-vue'

const props = defineProps<{
  modelValue?: Record<string, any>
  initialCapital?: number
  marketType?: string
}>()

const emit = defineEmits<['update:modelValue', 'change']>()

const { t } = useI18n()
const formRef = ref<FormInstance>()

const form = ref({
  amountEach: props.modelValue?.amountEach || null,
  frequency: props.modelValue?.frequency || 'daily',
  totalBudget: props.modelValue?.totalBudget || null,
  dipBuyEnabled: props.modelValue?.dipBuyEnabled || false,
  dipThreshold: props.modelValue?.dipThreshold || 5
})

const capitalLinked = ref(!props.modelValue?.totalBudget)

const estimatedRuns = computed(() => {
  if (!form.value.totalBudget || form.value.totalBudget <= 0) return t('trading-bot.dca.unlimited')
  return Math.floor(form.value.totalBudget / form.value.amountEach) + ` ${t('trading-bot.dca.times')}`
})

const rules: Record<string, any[]> = {
  amountEach: [
    { required: true, message: t('trading-bot.dca.amountEachReq'), trigger: 'change' },
    { validator: validateAmountEach, trigger: 'change' }
  ],
  frequency: [{ required: true, message: t('trading-bot.dca.frequencyReq'), trigger: 'change' }]
}

watch(() => props.initialCapital, (val) => {
  if (val && val > 0 && capitalLinked.value) {
    form.value.totalBudget = val
    if (!form.value.amountEach || form.value.amountEach <= 0) {
      form.value.amountEach = Math.max(1, Math.round(val / 30))
    }
    emitPayload()
  }
})

function validateAmountEach(_rule: any, value: any) {
  if (value == null || value === '') return Promise.resolve()
  if (form.value.totalBudget && form.value.totalBudget > 0 && value > form.value.totalBudget + 1e-6) {
    return Promise.reject(new Error(t('trading-bot.dca.amountExceedsBudget')))
  }
  return Promise.resolve()
}

function emitPayload() {
  emit('update:modelValue', { ...form.value })
  emit('change', { ...form.value })
}

async function validate() {
  await formRef.value?.validate()
  return { ...form.value }
}

defineExpose({ validate })
</script>

<style scoped lang="less">
.dip-buy-hint {
  margin-left: 8px;
  color: #8c8c8c;
  font-size: 12px;
}

.config-summary {
  margin-top: 8px;
  padding: 12px 16px;
  background: rgba(82, 196, 26, 0.04);
  border: 1px dashed rgba(82, 196, 26, 0.3);
  border-radius: 8px;

  .summary-item {
    display: flex;
    justify-content: space-between;
    padding: 4px 0;
    font-size: 13px;

    .label { color: #8c8c8c; }
    .value { font-weight: 600; color: #262626; }
  }
}
</style>
