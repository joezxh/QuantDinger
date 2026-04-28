<template>
  <div class="backtest-params">
    <div class="params-header">
      <ControlOutlined />
      <span>回测参数配置</span>
    </div>
    
    <a-form layout="vertical" size="small">
      <div class="param-group">
        <div class="group-title">时间范围</div>
        <div class="date-presets">
          <a-radio-group v-model:value="datePreset" size="small" @change="applyPreset">
            <a-radio-button value="1m">1个月</a-radio-button>
            <a-radio-button value="3m">3个月</a-radio-button>
            <a-radio-button value="6m">6个月</a-radio-button>
            <a-radio-button value="1y">1年</a-radio-button>
            <a-radio-button value="all">全部</a-radio-button>
          </a-radio-group>
        </div>
        <a-range-picker 
          v-model:value="dateRange" 
          style="width: 100%; margin-top: 8px" 
          :show-time="false"
        />
      </div>

      <div class="param-group">
        <div class="group-title">资金与风控</div>
        <a-row :gutter="8">
          <a-col :span="12">
            <a-form-item label="初始资金 ($)">
              <a-input-number v-model:value="params.initial_capital" style="width: 100%" :min="100" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="杠杆倍数 (x)">
              <a-input-number v-model:value="params.leverage" style="width: 100%" :min="1" :max="125" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="8">
          <a-col :span="12">
            <a-form-item label="手续费 (%)">
              <a-input-number v-model:value="params.commission" style="width: 100%" :min="0" :max="1" :step="0.01" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="滑点 (%)">
              <a-input-number v-model:value="params.slippage" style="width: 100%" :min="0" :max="5" :step="0.01" />
            </a-form-item>
          </a-col>
        </a-row>
      </div>

      <div class="param-group">
        <div class="group-title">交易方向</div>
        <a-radio-group v-model:value="params.trade_direction" button-style="solid" style="width: 100%">
          <a-radio-button value="long" style="width: 33.3%; text-align: center">仅做多</a-radio-button>
          <a-radio-button value="short" style="width: 33.3%; text-align: center">仅做空</a-radio-button>
          <a-radio-button value="both" style="width: 33.4%; text-align: center">双向</a-radio-button>
        </a-radio-group>
      </div>

      <div class="run-actions">
        <a-button 
          type="primary" 
          block 
          size="large" 
          :loading="loading" 
          @click="$emit('run', params)"
        >
          <template #icon><ThunderboltFilled /></template>
          开始回测
        </a-button>
        <a-button block style="margin-top: 8px" @click="$emit('show-history')">
          <template #icon><HistoryOutlined /></template>
          历史记录
        </a-button>
      </div>
    </a-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ControlOutlined, ThunderboltFilled, HistoryOutlined } from '@ant-design/icons-vue'
import dayjs, { Dayjs } from 'dayjs'

const props = defineProps<{
  loading: boolean
}>()

const emit = defineEmits(['run', 'show-history'])

const datePreset = ref('3m')
const dateRange = ref<[Dayjs, Dayjs]>([dayjs().subtract(3, 'month'), dayjs()])

const params = reactive({
  initial_capital: 10000,
  leverage: 1,
  commission: 0.04,
  slippage: 0.05,
  trade_direction: 'both',
  start_date: '',
  end_date: ''
})

watch(dateRange, (val) => {
  if (val && val[0] && val[1]) {
    params.start_date = val[0].format('YYYY-MM-DD')
    params.end_date = val[1].format('YYYY-MM-DD')
  }
}, { immediate: true })

const applyPreset = (e: any) => {
  const val = e.target.value
  const end = dayjs()
  let start = dayjs().subtract(10, 'year')
  
  if (val === '1m') start = dayjs().subtract(1, 'month')
  else if (val === '3m') start = dayjs().subtract(3, 'month')
  else if (val === '6m') start = dayjs().subtract(6, 'month')
  else if (val === '1y') start = dayjs().subtract(1, 'year')
  
  dateRange.value = [start, end]
}
</script>

<style scoped lang="less">
.backtest-params {
  padding: 16px;
  background: #1f1f1f;
  height: 100%;
  color: #d1d4dc;

  .params-header {
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 8px;
    color: #3b82f6;
  }

  .param-group {
    margin-bottom: 20px;
    
    .group-title {
      font-size: 12px;
      font-weight: 600;
      color: #868993;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
  }

  .run-actions {
    margin-top: 24px;
    
    .ant-btn-primary {
      background: #3b82f6;
      border: none;
      height: 44px;
      font-weight: 700;
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
  }

  :deep(.ant-form-item-label > label) {
    color: #868993;
    font-size: 11px;
  }

  :deep(.ant-input-number), :deep(.ant-picker), :deep(.ant-select-selector) {
    background: #2a2e39 !important;
    border-color: #363c4e !important;
    color: #d1d4dc !important;
  }
}
</style>
