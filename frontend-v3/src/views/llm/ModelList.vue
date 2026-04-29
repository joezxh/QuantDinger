<template>
  <div class="model-list">
    <div class="table-operator">
      <a-button type="primary" @click="handleAdd">
        <template #icon><PlusOutlined /></template>
        添加模型
      </a-button>
    </div>

    <a-table
      :columns="columns"
      :data-source="data"
      :loading="loading"
      row-key="id"
      size="middle"
    >
      <template #bodyCell="{ column, text, record }">
        <template v-if="column.dataIndex === 'lb_strategy'">
          {{ getStrategyLabel(text) }}
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a @click="handleEdit(record)">编辑</a>
            <a-divider type="vertical" />
            <a-popconfirm :title="t('common.confirmDelete')" @confirm="handleDelete(record.id)">
              <a class="text-danger">删除</a>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <a-modal
      v-model:visible="visible"
      :title="modalTitle"
      :confirm-loading="confirmLoading"
      @ok="handleOk"
    >
      <a-form :model="formState" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item label="供应商" name="provider_id" required>
          <a-select v-model:value="formState.provider_id" placeholder="选择供应商">
            <a-select-option v-for="p in providers" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="模型代码" name="model_name" required>
          <a-input v-model:value="formState.model_name" placeholder="例如: gpt-4o" />
        </a-form-item>
        <a-form-item label="显示名称" name="display_name" required>
          <a-input v-model:value="formState.display_name" placeholder="例如: GPT-4 Omni" />
        </a-form-item>
        <a-form-item label="负载均衡策略" name="lb_strategy">
          <a-select v-model:value="formState.lb_strategy">
            <a-select-option value="round_robin">轮询 (Round Robin)</a-select-option>
            <a-select-option value="weighted_round_robin">加权轮询</a-select-option>
            <a-select-option value="random">随机</a-select-option>
            <a-select-option value="least_connections">最小连接数</a-select-option>
            <a-select-option value="consistent_hash">一致性哈希</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="最大重试次数" name="retries">
          <a-input-number v-model:value="formState.retries" :min="0" :max="10" style="width: 100%" />
        </a-form-item>
        <a-form-item label="超时时间 (s)" name="timeout">
          <a-input-number v-model:value="formState.timeout" :min="1" :max="300" style="width: 100%" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { PlusOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { getModels, saveModel, deleteModel, getProviders } from '@/api/llm'

const { t } = useI18n()
const columns = [
  { title: 'ID', dataIndex: 'id', width: 80 },
  { title: '供应商', dataIndex: 'provider_name' },
  { title: '模型名称', dataIndex: 'model_name' },
  { title: '显示名称', dataIndex: 'display_name' },
  { title: '均衡策略', dataIndex: 'lb_strategy' },
  { title: t('common.action'), key: 'action', width: 150 }
]

const loading = ref(false)
const data = ref([])
const providers = ref([])
const visible = ref(false)
const confirmLoading = ref(false)
const modalTitle = ref('')
const editId = ref<number | null>(null)

const formState = reactive({
  provider_id: undefined,
  model_name: '',
  display_name: '',
  lb_strategy: 'round_robin',
  retries: 3,
  timeout: 60
})

const getStrategyLabel = (strategy: string) => {
  const map: Record<string, string> = {
    'round_robin': '轮询',
    'weighted_round_robin': '加权轮询',
    'random': '随机',
    'least_connections': '最小连接数',
    'consistent_hash': '一致性哈希'
  }
  return map[strategy] || strategy
}

const loadData = async () => {
  loading.value = true
  try {
    const res: any = await getModels()
    data.value = res.data || []
  } catch (e) {
    message.error(t('common.loadFailed'))
  } finally {
    loading.value = false
  }
}

const loadProviders = async () => {
  try {
    const res: any = await getProviders()
    providers.value = res.data || []
  } catch (e) {
    console.error('Failed to load providers')
  }
}

const handleAdd = () => {
  modalTitle.value = '添加模型'
  editId.value = null
  Object.assign(formState, {
    provider_id: providers.value.length > 0 ? providers.value[0].id : undefined,
    model_name: '',
    display_name: '',
    lb_strategy: 'round_robin',
    retries: 3,
    timeout: 60
  })
  visible.value = true
}

const handleEdit = (record: any) => {
  modalTitle.value = '编辑模型'
  editId.value = record.id
  Object.assign(formState, {
    provider_id: record.provider_id,
    model_name: record.model_name,
    display_name: record.display_name,
    lb_strategy: record.lb_strategy,
    retries: record.retries,
    timeout: record.timeout
  })
  visible.value = true
}

const handleOk = async () => {
  if (!formState.provider_id || !formState.model_name || !formState.display_name) {
    message.warning('请填写必填项')
    return
  }
  confirmLoading.value = true
  try {
    const params: any = { ...formState }
    if (editId.value) params.id = editId.value
    await saveModel(params)
    message.success(t('common.saveSuccess'))
    visible.value = false
    loadData()
  } catch (e) {
    message.error(t('common.saveFailed'))
  } finally {
    confirmLoading.value = false
  }
}

const handleDelete = async (id: number) => {
  try {
    await deleteModel(id)
    message.success('删除成功')
    loadData()
  } catch (e) {
    message.error(t('common.deleteFailed'))
  }
}

onMounted(() => {
  loadData()
  loadProviders()
})
</script>

<style scoped>
.table-operator {
  margin-bottom: 18px;
}
.text-danger {
  color: #ff4d4f;
}
</style>
