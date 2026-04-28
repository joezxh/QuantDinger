<template>
  <a-modal
    :visible="visible"
    :title="editingPosition ? '编辑持仓' : '添加持仓'"
    @ok="handleOk"
    @cancel="$emit('close')"
    :confirmLoading="loading"
    width="560px"
  >
    <a-form layout="vertical">
      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="市场类型" required>
            <a-select v-model:value="form.market" placeholder="选择市场" @change="handleMarketChange" :disabled="!!editingPosition">
              <a-select-option v-for="m in marketTypes" :key="m.value" :value="m.value">
                {{ m.label }}
              </a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="交易标的" required>
            <a-select
              v-model:value="form.symbol"
              show-search
              placeholder="搜索代码"
              :filter-option="false"
              @search="handleSymbolSearch"
              @change="handleSymbolSelect"
              :disabled="!!editingPosition"
            >
              <a-select-option v-for="s in symbolOptions" :key="s.symbol" :value="s.symbol">
                {{ s.symbol }} - {{ s.name }}
              </a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
      </a-row>

      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="方向" required>
            <a-radio-group v-model:value="form.side" button-style="solid" :disabled="!!editingPosition">
              <a-radio-button value="long">做多</a-radio-button>
              <a-radio-button value="short">做空</a-radio-button>
            </a-radio-group>
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="持仓数量" required>
            <a-input-number v-model:value="form.quantity" style="width: 100%" :min="0" />
          </a-form-item>
        </a-col>
      </a-row>

      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="入场价格" required>
            <a-input-number v-model:value="form.entry_price" style="width: 100%" :min="0" />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="所属分组">
            <a-auto-complete v-model:value="form.group_name" :options="groupOptions" placeholder="输入或选择分组" />
          </a-form-item>
        </a-col>
      </a-row>

      <a-form-item label="备注说明">
        <a-textarea v-model:value="form.notes" :rows="3" placeholder="添加备注信息..." />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { message } from 'ant-design-vue'
import { searchSymbols } from '@/api/portfolio'

const props = defineProps<{
  visible: boolean
  editingPosition: any
  groups: any[]
  marketTypes: any[]
}>()

const emit = defineEmits(['close', 'save'])

const loading = ref(false)
const symbolOptions = ref<any[]>([])
const searchTimer = ref<any>(null)

const form = reactive({
  market: 'Crypto',
  symbol: '',
  name: '',
  side: 'long',
  quantity: 0,
  entry_price: 0,
  group_name: '',
  notes: ''
})

const groupOptions = ref<{ value: string }[]>([])

watch(() => props.visible, (val) => {
  if (val) {
    if (props.editingPosition) {
      Object.assign(form, props.editingPosition)
    } else {
      resetForm()
    }
    groupOptions.value = props.groups.map(g => ({ value: g.name }))
  }
})

const resetForm = () => {
  form.market = 'Crypto'
  form.symbol = ''
  form.name = ''
  form.side = 'long'
  form.quantity = 0
  form.entry_price = 0
  form.group_name = ''
  form.notes = ''
}

const handleMarketChange = () => {
  form.symbol = ''
  form.name = ''
  symbolOptions.value = []
}

const handleSymbolSearch = (val: string) => {
  if (searchTimer.value) clearTimeout(searchTimer.value)
  if (!val) return

  searchTimer.value = setTimeout(async () => {
    try {
      const res = await searchSymbols({ market: form.market, keyword: val })
      if (res.code === 1) {
        symbolOptions.value = res.data
      }
    } catch (e) {}
  }, 300)
}

const handleSymbolSelect = (val: string) => {
  const item = symbolOptions.value.find(s => s.symbol === val)
  if (item) {
    form.name = item.name
  }
}

const handleOk = () => {
  if (!form.symbol || !form.market || !form.quantity || !form.entry_price) {
    message.warning('请填写必要信息')
    return
  }
  emit('save', { ...form })
}
</script>
