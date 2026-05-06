<template>
  <a-modal
    v-model:open="visible"
    :title="isEdit ? t('trading-bot.editTitle') : t('trading-bot.createTitle', { type: typeName })"
    :width="720"
    :confirm-loading="saving"
    @ok="handleSubmit"
    @cancel="close"
  >
    <a-form :model="form" layout="vertical" ref="formRef" :rules="formRules">
      <!-- 基础信息 -->
      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item :label="t('trading-bot.form.name')" name="strategy_name">
            <a-input v-model:value="form.strategy_name" :placeholder="t('trading-bot.form.namePh')" />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item :label="t('trading-bot.form.symbol')" name="symbol">
            <a-input v-model:value="form.symbol" :placeholder="t('trading-bot.form.symbolPh')" />
          </a-form-item>
        </a-col>
      </a-row>

      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item :label="t('trading-bot.form.credential')" name="credential_id">
            <a-select
              v-model:value="form.credential_id"
              :placeholder="t('trading-bot.form.credentialPh')"
              :loading="loadingCredentials"
              allow-clear
            >
              <a-select-option v-for="c in credentials" :key="c.id" :value="c.id">
                {{ c.name || c.exchange_id }} ({{ c.exchange_id }})
              </a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item :label="t('trading-bot.form.marketType')" name="market_type">
            <a-radio-group v-model:value="form.market_type">
              <a-radio value="swap">{{ t('trading-bot.form.futures') }}</a-radio>
              <a-radio value="spot">{{ t('trading-bot.form.spot') }}</a-radio>
            </a-radio-group>
          </a-form-item>
        </a-col>
      </a-row>

      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item :label="t('trading-bot.form.timeframe')" name="timeframe">
            <a-select v-model:value="form.timeframe">
              <a-select-option value="1m">1m</a-select-option>
              <a-select-option value="5m">5m</a-select-option>
              <a-select-option value="15m">15m</a-select-option>
              <a-select-option value="1h">1h</a-select-option>
              <a-select-option value="4h">4h</a-select-option>
              <a-select-option value="1d">1d</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item :label="t('trading-bot.form.initialCapital')" name="initial_capital">
            <a-input-number v-model:value="form.initial_capital" :min="10" :step="100" style="width: 100%" />
          </a-form-item>
        </a-col>
      </a-row>

      <a-row :gutter="16" v-if="form.market_type === 'swap'">
        <a-col :span="12">
          <a-form-item :label="t('trading-bot.form.leverage')">
            <a-input-number v-model:value="form.leverage" :min="1" :max="125" :step="1" style="width: 100%" />
          </a-form-item>
        </a-col>
      </a-row>

      <!-- 策略参数 -->
      <a-divider orientation="left">{{ t('trading-bot.form.strategyParams') }}</a-divider>

      <component
        :is="configComponent"
        ref="configRef"
        v-model="form.strategy_params"
        :initial-capital="form.initial_capital"
        :market-type="form.market_type"
      />

      <!-- 风控设置 -->
      <a-divider orientation="left">{{ t('trading-bot.form.riskSettings') }}</a-divider>

      <a-row :gutter="16">
        <a-col :span="8">
          <a-form-item :label="t('trading-bot.form.stopLossPct')">
            <a-input-number
              v-model:value="form.stop_loss_pct"
              :min="0"
              :max="100"
              :step="0.5"
              style="width: 100%"
              :formatter="(v: number) => `${v}%`"
              :parser="(v: string) => v.replace('%', '')"
            />
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item :label="t('trading-bot.form.takeProfitPct')">
            <a-input-number
              v-model:value="form.take_profit_pct"
              :min="0"
              :max="1000"
              :step="0.5"
              style="width: 100%"
              :formatter="(v: number) => `${v}%`"
              :parser="(v: string) => v.replace('%', '')"
            />
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item :label="t('trading-bot.form.maxDailyLoss')">
            <a-input-number v-model:value="form.max_daily_loss" :min="0" :step="10" style="width: 100%" />
          </a-form-item>
        </a-col>
      </a-row>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import type { FormInstance } from 'ant-design-vue'
import { listExchangeCredentials } from '@/api/credentials'
import { createStrategy, updateStrategy } from '@/api/strategy'
import GridConfig from './configs/GridConfig.vue'
import DCAConfig from './configs/DCAConfig.vue'
import MartingaleConfig from './configs/MartingaleConfig.vue'
import TrendConfig from './configs/TrendConfig.vue'

const props = defineProps<{
  open: boolean
  botType: string
  editBot?: any
}>()

const emit = defineEmits<['update:open', 'success']>()

const { t } = useI18n()
const formRef = ref<FormInstance>()
const configRef = ref<any>()
const saving = ref(false)
const credentials = ref<any[]>([])
const loadingCredentials = ref(false)

const visible = computed({
  get: () => props.open,
  set: (v) => emit('update:open', v),
})

const isEdit = computed(() => !!props.editBot)

const typeName = computed(() => {
  const map: Record<string, string> = {
    grid: t('trading-bot.type.grid'),
    dca: t('trading-bot.type.dca'),
    martingale: t('trading-bot.type.martingale'),
    trend: t('trading-bot.type.trend'),
  }
  return map[props.botType] || props.botType
})

const configComponent = computed(() => {
  const map: Record<string, any> = {
    grid: GridConfig,
    dca: DCAConfig,
    martingale: MartingaleConfig,
    trend: TrendConfig,
  }
  return map[props.botType] || GridConfig
})

const form = ref({
  strategy_name: '',
  symbol: '',
  credential_id: undefined as number | undefined,
  market_type: 'swap' as 'swap' | 'spot',
  timeframe: '1h',
  initial_capital: 1000 as number | undefined,
  leverage: 1,
  strategy_params: {} as Record<string, any>,
  stop_loss_pct: undefined as number | undefined,
  take_profit_pct: undefined as number | undefined,
  max_daily_loss: undefined as number | undefined,
})

const formRules: Record<string, any[]> = {
  strategy_name: [{ required: true, message: () => t('trading-bot.form.nameRequired') }],
  symbol: [{ required: true, message: () => t('trading-bot.form.symbolRequired') }],
  credential_id: [{ required: true, message: () => t('trading-bot.form.credentialRequired') }],
  market_type: [{ required: true }],
  timeframe: [{ required: true }],
  initial_capital: [{ required: true, message: () => t('trading-bot.form.capitalRequired') }],
}

async function loadCredentials() {
  loadingCredentials.value = true
  try {
    const res: any = await listExchangeCredentials()
    if (res.code === 1) {
      credentials.value = res.data || []
    }
  } catch (e) {
    console.error('加载凭证失败', e)
  } finally {
    loadingCredentials.value = false
  }
}

function resetForm() {
  const bot = props.editBot
  if (bot) {
    const tc = bot.trading_config || {}
    form.value = {
      strategy_name: bot.strategy_name || '',
      symbol: tc.symbol || '',
      credential_id: bot.exchange_config?.credential_id,
      market_type: tc.market_type || 'swap',
      timeframe: tc.timeframe || '1h',
      initial_capital: tc.initial_capital || 1000,
      leverage: tc.leverage || 1,
      strategy_params: bot.strategy_params || tc.strategy_params || {},
      stop_loss_pct: tc.stop_loss_pct,
      take_profit_pct: tc.take_profit_pct,
      max_daily_loss: tc.max_daily_loss,
    }
  } else {
    form.value = {
      strategy_name: '',
      symbol: '',
      credential_id: undefined,
      market_type: 'swap',
      timeframe: '1h',
      initial_capital: 1000,
      leverage: 1,
      strategy_params: {},
      stop_loss_pct: undefined,
      take_profit_pct: undefined,
      max_daily_loss: undefined,
    }
  }
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
    const configValid = configRef.value?.validate
    if (configValid) {
      await configRef.value.validate()
    }
  } catch (e) {
    return
  }

  saving.value = true
  try {
    const payload: any = {
      strategy_name: form.value.strategy_name,
      strategy_type: props.botType,
      strategy_mode: 'bot',
      exchange_config: {
        credential_id: form.value.credential_id,
      },
      trading_config: {
        symbol: form.value.symbol,
        market_type: form.value.market_type,
        timeframe: form.value.timeframe,
        initial_capital: form.value.initial_capital,
        leverage: form.value.leverage,
        stop_loss_pct: form.value.stop_loss_pct,
        take_profit_pct: form.value.take_profit_pct,
        max_daily_loss: form.value.max_daily_loss,
      },
      strategy_params: form.value.strategy_params,
    }

    if (isEdit.value && props.editBot) {
      const res: any = await updateStrategy(props.editBot.id, payload)
      if (res.code === 1) {
        message.success(t('common.updateSuccess'))
        emit('success')
        close()
      } else {
        message.error(res.msg || t('common.updateFailed'))
      }
    } else {
      const res: any = await createStrategy(payload)
      if (res.code === 1) {
        message.success(t('common.createSuccess'))
        emit('success')
        close()
      } else {
        message.error(res.msg || t('common.createFailed'))
      }
    }
  } catch (e: any) {
    message.error(e.response?.data?.msg || t('common.failed'))
  } finally {
    saving.value = false
  }
}

function close() {
  visible.value = false
}

watch(() => props.open, (v) => {
  if (v) {
    resetForm()
    loadCredentials()
  }
})

onMounted(() => {
  if (props.open) loadCredentials()
})
</script>
