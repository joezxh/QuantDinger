<template>
  <a-form
    ref="formRef"
    :model="form"
    :rules="rules"
    :label-col="{ span: 8 }"
    :wrapper-col="{ span: 14 }"
  >
    <a-form-item :label="t('trading-bot.grid.upperPrice')" name="upperPrice">
      <a-input-number
        v-model:value="form.upperPrice"
        :min="0"
        :step="0.01"
        style="width: 100%"
        :placeholder="t('trading-bot.grid.upperPricePh')"
        @change="emit"
      />
    </a-form-item>
    <a-form-item :label="t('trading-bot.grid.lowerPrice')" name="lowerPrice">
      <a-input-number
        v-model:value="form.lowerPrice"
        :min="0"
        :step="0.01"
        style="width: 100%"
        :placeholder="t('trading-bot.grid.lowerPricePh')"
        @change="emit"
      />
    </a-form-item>
    <a-form-item :label="t('trading-bot.grid.gridCount')" name="gridCount">
      <a-input-number
        v-model:value="form.gridCount"
        :min="2"
        :max="500"
        :step="1"
        style="width: 100%"
        @change="emit"
      />
    </a-form-item>
    <a-form-item :label="t('trading-bot.grid.amountPerGrid')" name="amountPerGrid">
      <a-input-number
        v-model:value="form.amountPerGrid"
        :min="1"
        :step="1"
        style="width: 100%"
        :placeholder="t('trading-bot.grid.amountPerGridPh')"
        @change="handleAmountManualChange"
      />
      <div v-if="capitalLinked && initialCapital" class="direction-hint">
        <LinkOutlined /> {{ t('trading-bot.grid.autoCalcHint') }}
      </div>
    </a-form-item>
    <a-form-item :label="t('trading-bot.grid.mode')">
      <a-radio-group v-model:value="form.gridMode" @change="emit">
        <a-radio value="arithmetic">{{ t('trading-bot.grid.arithmetic') }}</a-radio>
        <a-radio value="geometric">{{ t('trading-bot.grid.geometric') }}</a-radio>
      </a-radio-group>
    </a-form-item>
    <a-form-item :label="t('trading-bot.grid.direction')">
      <a-radio-group v-model:value="form.gridDirection" @change="emit">
        <a-radio value="neutral" :disabled="isSpotMarket">{{ t('trading-bot.grid.neutral') }}</a-radio>
        <a-radio value="long">{{ t('trading-bot.grid.long') }}</a-radio>
        <a-radio value="short" :disabled="isSpotMarket">{{ t('trading-bot.grid.short') }}</a-radio>
      </a-radio-group>
      <div class="direction-hint">{{ directionHint }}</div>
    </a-form-item>
    <a-form-item :label="t('trading-bot.grid.orderType')">
      <a-radio-group v-model:value="form.orderMode" @change="emit">
        <a-radio value="maker">{{ t('trading-bot.grid.limitOrder') }}</a-radio>
        <a-radio value="market">{{ t('trading-bot.grid.marketOrder') }}</a-radio>
      </a-radio-group>
      <div class="direction-hint">{{ orderModeHint }}</div>
    </a-form-item>
    <div
      class="config-summary"
      v-if="form.upperPrice && form.lowerPrice && form.gridCount"
    >
      <div class="summary-item">
        <span class="label">{{ t('trading-bot.grid.gridSpacing') }}</span>
        <span class="value">{{ gridSpacing }}</span>
      </div>
      <div class="summary-item">
        <span class="label">{{ t('trading-bot.grid.totalInvest') }}</span>
        <span class="value">${{ totalInvestment }}</span>
      </div>
    </div>
  </a-form>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { LinkOutlined } from '@ant-design/icons-vue'
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
  upperPrice: props.modelValue?.upperPrice || null,
  lowerPrice: props.modelValue?.lowerPrice || null,
  gridCount: props.modelValue?.gridCount || 10,
  amountPerGrid: props.modelValue?.amountPerGrid || null,
  gridMode: props.modelValue?.gridMode || 'arithmetic',
  gridDirection: props.modelValue?.gridDirection || 'neutral',
  orderMode: props.modelValue?.orderMode || 'maker'
})

const capitalLinked = ref(!props.modelValue?.amountPerGrid)

const rules: Record<string, any[]> = {
  upperPrice: [
    { required: true, message: t('trading-bot.grid.upperPriceReq'), trigger: 'change' },
    { validator: validateUpperPrice, trigger: 'change' }
  ],
  lowerPrice: [
    { required: true, message: t('trading-bot.grid.lowerPriceReq'), trigger: 'change' },
    { validator: validateLowerPrice, trigger: 'change' }
  ],
  gridCount: [{ required: true, message: t('trading-bot.grid.gridCountReq'), trigger: 'change' }],
  amountPerGrid: [
    { required: true, message: t('trading-bot.grid.amountReq'), trigger: 'change' },
    { validator: validateAmountPerGrid, trigger: 'change' }
  ]
}

const isSpotMarket = computed(() => props.marketType === 'spot')

const gridSpacing = computed(() => {
  if (!form.value.upperPrice || !form.value.lowerPrice || !form.value.gridCount) return '-'
  if (form.value.gridMode === 'geometric' && form.value.lowerPrice > 0) {
    const ratio = Math.pow(form.value.upperPrice / form.value.lowerPrice, 1 / form.value.gridCount)
    return `${((ratio - 1) * 100).toFixed(2)}%`
  }
  const spacing = ((form.value.upperPrice - form.value.lowerPrice) / form.value.gridCount).toFixed(4)
  return `$${spacing}`
})

const totalInvestment = computed(() => {
  if (!form.value.amountPerGrid || !form.value.gridCount) return '0'
  return (form.value.amountPerGrid * form.value.gridCount).toLocaleString('en-US', { minimumFractionDigits: 2 })
})

const directionHint = computed(() => {
  if (isSpotMarket.value) return 'Spot grid only supports long mode.'
  const map: Record<string, string> = {
    neutral: t('trading-bot.grid.neutralHint'),
    long: t('trading-bot.grid.longHint'),
    short: t('trading-bot.grid.shortHint')
  }
  return map[form.value.gridDirection] || ''
})

const orderModeHint = computed(() => {
  return form.value.orderMode === 'maker'
    ? t('trading-bot.grid.limitOrderHint')
    : t('trading-bot.grid.marketOrderHint')
})

watch(() => props.initialCapital, (val) => {
  if (val && val > 0 && form.value.gridCount > 0 && capitalLinked.value) {
    form.value.amountPerGrid = Math.floor(val / form.value.gridCount)
    doEmit()
  }
})

watch(() => form.value.gridCount, (val) => {
  if (props.initialCapital && props.initialCapital > 0 && val > 0 && capitalLinked.value) {
    form.value.amountPerGrid = Math.floor(props.initialCapital / val)
    doEmit()
  }
})

watch(() => props.marketType, (val) => {
  if (val === 'spot' && form.value.gridDirection !== 'long') {
    form.value.gridDirection = 'long'
    doEmit()
  }
}, { immediate: true })

function validateUpperPrice(_rule: any, value: any) {
  if (value == null || value === '') return Promise.resolve()
  if (form.value.lowerPrice != null && value <= form.value.lowerPrice) {
    return Promise.reject(new Error(t('trading-bot.grid.upperMustGtLower')))
  }
  return Promise.resolve()
}

function validateLowerPrice(_rule: any, value: any) {
  if (value == null || value === '') return Promise.resolve()
  if (form.value.gridMode === 'geometric' && value <= 0) {
    return Promise.reject(new Error(t('trading-bot.grid.lowerMustGtZero')))
  }
  if (form.value.upperPrice != null && value >= form.value.upperPrice) {
    return Promise.reject(new Error(t('trading-bot.grid.upperMustGtLower')))
  }
  return Promise.resolve()
}

function validateAmountPerGrid(_rule: any, value: any) {
  if (value == null || value === '') return Promise.resolve()
  if (props.initialCapital && form.value.gridCount) {
    const total = value * form.value.gridCount
    if (total > props.initialCapital + 1e-6) {
      return Promise.reject(new Error(t('trading-bot.grid.amountExceedsBudget')))
    }
  }
  return Promise.resolve()
}

function handleAmountManualChange() {
  capitalLinked.value = false
  doEmit()
}

function doEmit() {
  emit('update:modelValue', { ...form.value })
  emit('change', { ...form.value })
}

function emitPayload() {
  doEmit()
}

async function validate() {
  await formRef.value?.validate()
  return { ...form.value }
}

defineExpose({ validate })
</script>

<style scoped lang="less">
.direction-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #8c8c8c;
}

.config-summary {
  margin-top: 8px;
  padding: 12px 16px;
  background: rgba(24, 144, 255, 0.04);
  border: 1px dashed rgba(24, 144, 255, 0.3);
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
