<template>
  <div class="dataset-list">
    <div class="toolbar">
      <a-button type="primary" @click="showCreateModal">
        <template #icon><PlusOutlined /></template>
        添加数据集
      </a-button>
      <a-button @click="loadData" :loading="loading">
        <template #icon><ReloadOutlined /></template>
        刷新
      </a-button>
    </div>

    <a-table
      :columns="columns"
      :data-source="data"
      :loading="loading"
      row-key="id"
      :pagination="false"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'action'">
          <a-space>
            <a-button type="link" size="small" @click="editDataset(record)">{{ t('common.edit') }}</a-button>
            <a-popconfirm title="确定删除?" @confirm="handleDelete(record.id)">
              <a-button type="link" danger size="small">{{ t('common.delete') }}</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <a-modal
      v-model:open="modalVisible"
      :title="editingId ? '编辑数据集' : '添加数据集'"
      @ok="handleSave"
      :confirmLoading="saving"
    >
      <a-form layout="vertical">
        <a-form-item :label="t('common.name')" required>
          <a-input v-model:value="form.name" placeholder="数据集名称" />
        </a-form-item>
        <a-form-item label="代码 (Symbol)" required>
          <a-input v-model:value="form.symbol" placeholder="例如: BTC-USDT" />
        </a-form-item>
        <a-form-item label="时间周期">
          <a-select v-model:value="form.timeframe">
            <a-select-option value="1m">1分钟</a-select-option>
            <a-select-option value="5m">5分钟</a-select-option>
            <a-select-option value="15m">15分钟</a-select-option>
            <a-select-option value="1H">1小时</a-select-option>
            <a-select-option value="4H">4小时</a-select-option>
            <a-select-option value="1D">1天</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="数据源配置ID">
          <a-input-number v-model:value="form.config_id" style="width: 100%" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { getDatasets, saveDataset, deleteDataset } from '@/api/data-source'

const { t } = useI18n()
const loading = ref(false)
const data = ref<any[]>([])

const modalVisible = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({
  name: '',
  symbol: '',
  timeframe: '1H',
  config_id: null as number | null
})

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: t('common.name'), dataIndex: 'name', key: 'name' },
  { title: t('aiAnalysis.symbolCode'), dataIndex: 'symbol', key: 'symbol' },
  { title: '时间周期', dataIndex: 'timeframe', key: 'timeframe' },
  { title: '配置ID', dataIndex: 'config_id', key: 'config_id' },
  { title: t('common.createdAt'), dataIndex: 'created_at', key: 'created_at' },
  { title: t('common.action'), key: 'action', width: 150 }
]

const loadData = async () => {
  loading.value = true
  try {
    const res: any = await getDatasets()
    if (res.code === 1) {
      data.value = res.data || []
    }
  } catch (error) {
    message.error(t('common.loadFailed'))
  } finally {
    loading.value = false
  }
}

const showCreateModal = () => {
  editingId.value = null
  Object.assign(form, { name: '', symbol: '', timeframe: '1H', config_id: null })
  modalVisible.value = true
}

const editDataset = (record: any) => {
  editingId.value = record.id
  Object.assign(form, { 
    name: record.name, 
    symbol: record.symbol, 
    timeframe: record.timeframe, 
    config_id: record.config_id 
  })
  modalVisible.value = true
}

const handleSave = async () => {
  if (!form.name || !form.symbol) {
    message.warning('请填写必要信息')
    return
  }
  saving.value = true
  try {
    const payload = editingId.value ? { ...form, id: editingId.value } : form
    const res: any = await saveDataset(payload)
    if (res.code === 1) {
      message.success(t('common.saveSuccess'))
      modalVisible.value = false
      loadData()
    } else {
      message.error(res.msg || '保存失败')
    }
  } catch (error) {
    message.error('请求失败')
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id: number) => {
  try {
    const res: any = await deleteDataset(id)
    if (res.code === 1) {
      message.success('删除成功')
      loadData()
    } else {
      message.error(res.msg || '删除失败')
    }
  } catch (error) {
    message.error('请求失败')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="less">
.toolbar {
  margin-bottom: 16px;
  display: flex;
  gap: 8px;
}
</style>
