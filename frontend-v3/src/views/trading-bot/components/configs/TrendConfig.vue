<template>
  <a-form
    ref="formRef"
    :model="form"
    :rules="rules"
    :label-col="{ span: 8 }"
    :wrapper-col="{ span: 14 }"
  >
    <a-form-item :label="t('trading-bot.trend.maPeriod')" name="maPeriod">
      <a-input-number
        v-model:value="form.maPeriod"
        :min="5"
        :max="500"
        :step="1"
        style="width: 100%"
        @change="emitPayload"
      />
    </a-form-item>
    <a-form-item :label="t('trading-bot.trend.maType')">
      <a-select v-model:value="form.maType" @change="emitPayload">
        <a-select-option value="EMA">EMA</a-select-option>
        <a-select-option value="SMA">SMA</a-select-option>
        <a-select-option value="WMA">WMA</a-select-option>
      </a-select>
    </a-form-item>
    <a-form-item :label="t('trading-bot.trend.confirmBars')" name="confirmBars">
      <a-input-number
        v-model:value="form.confirmBars"
        :min="1"
        :max="10"
        :step="1"
        style="width: 100%"
        @change="emitPayload"
      />
    </a-form-item>
    <a-form-item :label="t('trading-bot.trend.positionPct')" name="positionPct">
      <a-slider
        v-model:value="form.positionPct"
        :min="5"
        :max="100"
        :step="5"
        :tipFormatter="(v: number) => `${v}%`"
        @change="emitPayload"
      />
    </a-form-item>
    <a-form-item :label="t('trading-bot.trend.direction')">
      <a-radio-group v-model:value="form.direction" @change="emitPayload">
        <a-radio value="long">{{ t('trading-bot.trend.longOnly') }}</a-radio>
        <a-radio value="short" :disabled="isSpotMarket">{{ t('trading-bot.trend.shortOnly') }}</a-radio>
        <a-radio value="both" :disabled="isSpotMarket">{{ t('trading-bot.trend.bothSides') }}</a-radio>
      </a-radio-group>
      <div v-if="isSpotMarket" class="direction-hint">Spot only supports long trend bots.</div>
    </a-form-item>
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
  maPeriod: props.modelValue?.maPeriod || 20,
  maType: props.modelValue?.maType || 'EMA',
  confirmBars: props.modelValue?.confirmBars || 2,
  positionPct: props.modelValue?.positionPct || 50,
  direction: props.modelValue?.direction || 'long'
})

const isSpotMarket = computed(() => props.marketType === 'spot')

const rules: Record<string, any[]> = {
  maPeriod: [{ required: true, message: t('trading-bot.trend.maPeriodReq'), trigger: 'change' }],
  confirmBars: [{ required: true, message: t('trading-bot.trend.confirmBarsReq'), trigger: 'change' }],
  positionPct: [{ required: true, message: t('trading-bot.trend.positionPctReq'), trigger: 'change' }]
}

watch(() => props.marketType, (val) => {
  if (val === 'spot' && form.value.direction !== 'long') {
    form.value.direction = 'long'
    emitPayload()
  }
}, { immediate: true })

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
.direction-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #8c8c8c;
}
</style>
