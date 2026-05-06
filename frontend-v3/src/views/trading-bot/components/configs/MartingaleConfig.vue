<template>
  <a-form
    ref="formRef"
    :model="form"
    :rules="rules"
    :label-col="{ span: 8 }"
    :wrapper-col="{ span: 14 }"
  >
    <a-form-item :label="budgetLabel">
      <a-input-number
        :value="initialCapital"
        disabled
        style="width: 100%"
        placeholder="USDT"
      />
      <div class="capital-hint">{{ budgetHint }}</div>
    </a-form-item>
    <a-form-item :label="firstOrderLabel">
      <a-input-number
        :value="firstOrderAmount"
        disabled
        style="width: 100%"
        placeholder="USDT"
      />
      <div class="capital-hint">{{ firstOrderHint }}</div>
    </a-form-item>
    <a-form-item :label="t('trading-bot.martingale.multiplier')" name="multiplier">
      <a-input-number
        v-model:value="form.multiplier"
        :min="1.1"
        :max="10"
        :step="0.1"
        style="width: 100%"
        @change="emitPayload"
      />
    </a-form-item>
    <a-form-item :label="t('trading-bot.martingale.maxLayers')" name="maxLayers">
      <a-input-number
        v-model:value="form.maxLayers"
        :min="1"
        :max="20"
        :step="1"
        style="width: 100%"
        @change="emitPayload"
      />
      <div class="field-hint">{{ maxLayersHint }}</div>
    </a-form-item>
    <a-form-item :label="t('trading-bot.martingale.priceDropPct')" name="priceDropPct">
      <a-input-number
        v-model:value="form.priceDropPct"
        :min="0.1"
        :max="50"
        :step="0.5"
        style="width: 100%"
        :formatter="(v: number) => `${v}%`"
        :parser="(v: string) => v.replace('%', '')"
        @change="emitPayload"
      />
    </a-form-item>
    <a-form-item :label="takeProfitLabel" name="takeProfitPct">
      <a-input-number
        v-model:value="form.takeProfitPct"
        :min="0.1"
        :max="100"
        :step="0.5"
        style="width: 100%"
        :formatter="(v: number) => `${v}%`"
        :parser="(v: string) => v.replace('%', '')"
        @change="emitPayload"
      />
      <div class="field-hint">{{ takeProfitHint }}</div>
    </a-form-item>
    <a-form-item :label="stopLossLabel" name="stopLossPct">
      <a-input-number
        v-model:value="form.stopLossPct"
        :min="0.1"
        :max="100"
        :step="0.5"
        style="width: 100%"
        :formatter="(v: number) => `${v}%`"
        :parser="(v: string) => v.replace('%', '')"
        @change="emitPayload"
      />
      <div class="field-hint">{{ stopLossHint }}</div>
    </a-form-item>
    <a-form-item :label="t('trading-bot.martingale.direction')">
      <a-radio-group v-model:value="form.direction" @change="emitPayload">
        <a-radio value="long">{{ t('trading-bot.martingale.long') }}</a-radio>
        <a-radio value="short" :disabled="isSpotMarket">{{ t('trading-bot.martingale.short') }}</a-radio>
      </a-radio-group>
      <div class="direction-hint">{{ directionHint }}</div>
    </a-form-item>
    <div
      class="config-summary"
      v-if="firstOrderRaw > 0 && form.multiplier && form.maxLayers"
    >
      <div class="summary-item">
        <span class="label">{{ budgetLabel }}</span>
        <span class="value">${{ maxInvestment }}</span>
      </div>
      <div class="summary-item">
        <span class="label">{{ firstOrderLabel }}</span>
        <span class="value">${{ firstOrderAmount }}</span>
      </div>
      <div class="summary-item">
        <span class="label">{{ t('trading-bot.martingale.lastLayerAmt') }}</span>
        <span class="value">${{ lastLayerAmount }}</span>
      </div>
    </div>
  </a-form>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import type { FormInstance } from 'ant-design-vue'

const props = defineProps<{
  modelValue?: Record<string, any>
  initialCapital?: number
  marketType?: string
}>()

const emit = defineEmits<['update:modelValue', 'change']>()

const { t, locale } = useI18n()
const formRef = ref<FormInstance>()

const form = ref({
  multiplier: props.modelValue?.multiplier || 2,
  maxLayers: props.modelValue?.maxLayers || 5,
  priceDropPct: props.modelValue?.priceDropPct || 3,
  takeProfitPct: props.modelValue?.takeProfitPct || 2,
  stopLossPct: props.modelValue?.stopLossPct || 12,
  direction: props.modelValue?.direction || 'long'
})

const isZhLocale = computed(() => String(locale.value || '').toLowerCase().startsWith('zh'))
const isSpotMarket = computed(() => props.marketType === 'spot')

const budgetLabel = computed(() => isZhLocale.value ? '总投入金额' : 'Total Budget')
const firstOrderLabel = computed(() => isZhLocale.value ? '首单金额（自动计算）' : 'First Order Amount (Auto)')
const takeProfitLabel = computed(() => isZhLocale.value ? '相对持仓均价止盈%' : 'Take Profit vs Avg Entry %')
const stopLossLabel = computed(() => isZhLocale.value ? '相对持仓均价止损%' : 'Stop Loss vs Avg Entry %')

const budgetHint = computed(() => isZhLocale.value
  ? '这里表示这一轮马丁允许投入的总预算，不是首单金额。'
  : 'This is the total budget for one martingale cycle, not the first order size.')

const firstOrderRaw = computed(() => {
  const capital = Number(props.initialCapital || 0)
  if (capital <= 0) return 0
  let geoSum = 0
  for (let i = 0; i < form.value.maxLayers; i++) {
    geoSum += Math.pow(form.value.multiplier, i)
  }
  if (geoSum <= 0) return 0
  return Math.max(0, Math.floor((capital / geoSum) * 100) / 100)
})

const firstOrderAmount = computed(() => {
  return firstOrderRaw.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
})

const maxLayersHint = computed(() => isZhLocale.value
  ? '控制最多允许补仓的层数；系统会按总投入金额自动反推首单金额。'
  : 'Controls how many add-on entries are allowed; first order size is derived from total budget.')

const maxInvestment = computed(() => {
  let total = 0
  let amt = firstOrderRaw.value
  for (let i = 0; i < form.value.maxLayers; i++) {
    total += amt
    amt *= form.value.multiplier
  }
  return total.toLocaleString('en-US', { minimumFractionDigits: 2 })
})

const lastLayerAmount = computed(() => {
  const amt = firstOrderRaw.value * Math.pow(form.value.multiplier, form.value.maxLayers - 1)
  return amt.toLocaleString('en-US', { minimumFractionDigits: 2 })
})

const firstOrderHint = computed(() => isZhLocale.value
  ? '根据总投入金额、加仓倍数和最大层数自动推导，避免重复设置。'
  : 'Derived automatically from total budget, multiplier, and max layers.')

const takeProfitHint = computed(() => isZhLocale.value
  ? '当价格相对持仓均价达到这个盈利比例时，脚本自动平仓并重置马丁状态。'
  : 'When average entry profit reaches this %, the script closes the position and resets martingale state.')

const stopLossHint = computed(() => isZhLocale.value
  ? '当价格相对持仓均价反向达到这个比例时，整轮马丁强制止损。'
  : 'Force close the whole martingale cycle when price moves this % against average entry.')

const directionHint = computed(() => {
  if (isSpotMarket.value) return 'Spot only supports long martingale bots.'
  return form.value.direction === 'long'
    ? t('trading-bot.martingale.longHint')
    : t('trading-bot.martingale.shortHint')
})

const rules: Record<string, any[]> = {
  multiplier: [{ required: true, message: t('trading-bot.martingale.multiplierReq'), trigger: 'change' }],
  maxLayers: [{ required: true, message: t('trading-bot.martingale.maxLayersReq'), trigger: 'change' }],
  priceDropPct: [{ required: true, message: t('trading-bot.martingale.priceDropReq'), trigger: 'change' }],
  takeProfitPct: [{ required: true, message: t('trading-bot.martingale.takeProfitReq'), trigger: 'change' }],
  stopLossPct: [{ required: true, message: isZhLocale.value ? '请输入止损比例' : 'Please enter stop loss %', trigger: 'change' }]
}

onMounted(() => {
  emitPayload()
})

watch(() => props.initialCapital, () => {
  emitPayload()
})

watch(() => props.marketType, (val) => {
  if (val === 'spot' && form.value.direction !== 'long') {
    form.value.direction = 'long'
    emitPayload()
  }
}, { immediate: true })

function emitPayload() {
  const payload = {
    ...form.value,
    initialAmount: firstOrderRaw.value
  }
  emit('update:modelValue', payload)
  emit('change', payload)
}

async function validate() {
  await formRef.value?.validate()
  return { ...form.value, initialAmount: firstOrderRaw.value }
}

defineExpose({ validate })
</script>

<style scoped lang="less">
.capital-hint,
.direction-hint,
.field-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #8c8c8c;
}

.config-summary {
  margin-top: 8px;
  padding: 12px 16px;
  background: rgba(245, 34, 45, 0.04);
  border: 1px dashed rgba(245, 34, 45, 0.3);
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
