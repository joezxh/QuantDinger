<template>
  <div class="provider-list">
    <div class="table-operator">
      <a-button type="primary" @click="handleAdd">
        <template #icon><PlusOutlined /></template>
        添加供应商
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
        <template v-if="column.dataIndex === 'status'">
          <a-badge :status="text === 1 ? 'success' : 'error'" :text="text === 1 ? '启用' : '禁用'" />
        </template>
        <template v-if="column.dataIndex === 'api_type'">
          <a-tag color="blue">{{ getApiTypeLabel(text) }}</a-tag>
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
        <a-form-item :label="t('batch.auto182')" name="name" required>
          <a-input v-model:value="formState.name" :placeholder="t('batch.auto179')" />
        </a-form-item>
        <a-form-item :label="t('batch.auto183')" name="code" required>
          <a-input v-model:value="formState.code" :placeholder="t('batch.auto180')" />
        </a-form-item>
        <a-form-item :label="t('batch.auto184')" name="base_url" required>
          <a-input v-model:value="formState.base_url" :placeholder="t('batch.auto181')" />
        </a-form-item>
        <a-form-item :label="t('batch.auto185')" name="api_type">
          <a-select v-model:value="formState.api_type">
            <a-select-option value="openai">OpenAI</a-select-option>
            <a-select-option value="openrouter">OpenRouter</a-select-option>
            <a-select-option value="openai-compatible">OpenAI Compatible</a-select-option>
            <a-select-option value="google">Google Gemini</a-select-option>
            <a-select-option value="deepseek">DeepSeek</a-select-option>
            <a-select-option value="grok">xAI Grok</a-select-option>
            <a-select-option value="ollama">Ollama</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('common.status')" name="status">
          <a-switch v-model:checked="formState.active" />
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
import { getProviders, saveProvider, deleteProvider } from '@/api/llm'

const { t } = useI18n()
const columns = [
  { title: 'ID', dataIndex: 'id', width: 80 },
  { title: t('common.name'), dataIndex: 'name' },
  { title: t('batch.auto186'), dataIndex: 'code' },
  { title: t('batch.auto184'), dataIndex: 'base_url' },
  { title: t('batch.auto185'), dataIndex: 'api_type' },
  { title: t('common.status'), dataIndex: 'status' },
  { title: t('common.action'), key: 'action', width: 150 }
]

const loading = ref(false)
const data = ref([])
const visible = ref(false)
const confirmLoading = ref(false)
const modalTitle = ref('')
const editId = ref<number | null>(null)

const formState = reactive({
  name: '',
  code: '',
  base_url: '',
  api_type: 'openai',
  active: true
})

const getApiTypeLabel = (type: string) => {
  const map: Record<string, string> = {
    'openai': 'OpenAI',
    'openrouter': 'OpenRouter',
    'openai-compatible': 'OpenAI Compatible',
    'google': 'Google Gemini',
    'deepseek': 'DeepSeek',
    'grok': 'xAI Grok',
    'ollama': 'Ollama'
  }
  return map[type] || type
}

const loadData = async () => {
  loading.value = true
  try {
    const res: any = await getProviders()
    data.value = res.data || []
  } catch (e) {
    message.error(t('common.loadFailed'))
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  modalTitle.value = '添加供应商'
  editId.value = null
  Object.assign(formState, {
    name: '',
    code: '',
    base_url: '',
    api_type: 'openai',
    active: true
  })
  visible.value = true
}

const handleEdit = (record: any) => {
  modalTitle.value = '编辑供应商'
  editId.value = record.id
  Object.assign(formState, {
    name: record.name,
    code: record.code,
    base_url: record.base_url,
    api_type: record.api_type,
    active: record.status === 1
  })
  visible.value = true
}

const handleOk = async () => {
  if (!formState.name || !formState.code || !formState.base_url) {
    message.warning(t('batch.auto146'))
    return
  }
  confirmLoading.value = true
  try {
    const params: any = {
      ...formState,
      status: formState.active ? 1 : 0
    }
    if (editId.value) params.id = editId.value
    await saveProvider(params)
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
    await deleteProvider(id)
    message.success(t('batch.auto1'))
    loadData()
  } catch (e) {
    message.error(t('common.deleteFailed'))
  }
}

onMounted(loadData)
</script>

<style scoped>
.table-operator {
  margin-bottom: 18px;
}
.text-danger {
  color: #ff4d4f;
}
</style>
