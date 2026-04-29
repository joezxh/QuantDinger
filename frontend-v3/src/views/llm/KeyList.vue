<template>
  <div class="key-list">
    <div class="table-operator">
      <a-button type="primary" @click="handleAdd">
        <template #icon><PlusOutlined /></template>
        添加 API Key
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
          <a-tag v-if="text === 1" color="green">{{ t('dataSource.status.active') }}</a-tag>
          <a-tag v-else-if="text === 2" color="orange">已损坏</a-tag>
          <a-tag v-else color="red">{{ t('dataSource.status.inactive') }}</a-tag>
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
        <a-form-item label="名称/备注" name="name" required>
          <a-input v-model:value="formState.name" placeholder="例如: OpenAI Main Key" />
        </a-form-item>
        <a-form-item label="API Key" name="api_key">
          <a-input-password
            v-model:value="formState.api_key"
            :placeholder="editId ? '留空表示不修改' : '输入 API Key'"
          />
        </a-form-item>
        <a-form-item label="权重" name="weight">
          <a-input-number v-model:value="formState.weight" :min="1" :max="100" style="width: 100%" />
        </a-form-item>
        <a-form-item label="公开" name="is_public">
          <a-switch v-model:checked="formState.is_public" />
        </a-form-item>
        <a-form-item :label="t('common.status')" name="status">
          <a-select v-model:value="formState.status">
            <a-select-option :value="1">正常</a-select-option>
            <a-select-option :value="0">禁用</a-select-option>
            <a-select-option :value="2">已损坏</a-select-option>
          </a-select>
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
import { getKeys, saveKey, deleteKey, getProviders } from '@/api/llm'

const { t } = useI18n()
const columns = [
  { title: 'ID', dataIndex: 'id', width: 80 },
  { title: '供应商', dataIndex: 'provider_name' },
  { title: t('common.name'), dataIndex: 'name' },
  { title: '权重', dataIndex: 'weight', width: 100 },
  { title: t('common.status'), dataIndex: 'status', width: 120 },
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
  name: '',
  api_key: '',
  weight: 1,
  is_public: false,
  status: 1
})

const loadData = async () => {
  loading.value = true
  try {
    const res: any = await getKeys()
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
  modalTitle.value = '添加 API Key'
  editId.value = null
  Object.assign(formState, {
    provider_id: providers.value.length > 0 ? providers.value[0].id : undefined,
    name: '',
    api_key: '',
    weight: 1,
    is_public: false,
    status: 1
  })
  visible.value = true
}

const handleEdit = (record: any) => {
  modalTitle.value = '编辑 API Key'
  editId.value = record.id
  Object.assign(formState, {
    provider_id: record.provider_id,
    name: record.name,
    api_key: '',
    weight: record.weight,
    is_public: record.is_public === 1,
    status: record.status
  })
  visible.value = true
}

const handleOk = async () => {
  if (!formState.provider_id || !formState.name) {
    message.warning('请填写必填项')
    return
  }
  confirmLoading.value = true
  try {
    const params: any = {
      ...formState,
      is_public: formState.is_public ? 1 : 0
    }
    if (editId.value) params.id = editId.value
    await saveKey(params)
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
    await deleteKey(id)
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
