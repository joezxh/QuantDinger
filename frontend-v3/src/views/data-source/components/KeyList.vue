<template>
  <div class="key-list">
    <div class="toolbar">
      <a-button type="primary" @click="showCreateModal">
        <template #icon><PlusOutlined /></template>
        添加API密钥
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
        <template v-if="column.key === 'is_active'">
          <a-tag :color="record.is_active ? 'success' : 'default'">
            {{ record.is_active ? '启用' : '禁用' }}
          </a-tag>
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a-button type="link" size="small" @click="editKey(record)">{{ t('common.edit') }}</a-button>
            <a-popconfirm title="确定删除?" @confirm="handleDelete(record.id)">
              <a-button type="link" danger size="small">{{ t('common.delete') }}</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <a-modal
      v-model:open="modalVisible"
      :title="editingId ? '编辑API密钥' : '添加API密钥'"
      @ok="handleSave"
      :confirmLoading="saving"
    >
      <a-form layout="vertical">
        <a-form-item :label="t('common.name')" required>
          <a-input v-model:value="form.name" placeholder="如: Binance Main Account" />
        </a-form-item>
        <a-form-item :label="t('common.exchange')" required>
          <a-select v-model:value="form.exchange">
            <a-select-option value="binance">Binance</a-select-option>
            <a-select-option value="okx">OKX</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="API Key">
          <a-input v-model:value="form.api_key" placeholder="输入API Key" />
        </a-form-item>
        <a-form-item label="API Secret">
          <a-input-password v-model:value="form.api_secret" placeholder="输入API Secret" />
        </a-form-item>
        <a-form-item :label="t('common.status')">
          <a-switch v-model:checked="form.is_active" />
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
import { getDataSourceKeys, saveDataSourceKey, deleteDataSourceKey } from '@/api/data-source'

const { t } = useI18n()
const loading = ref(false)
const data = ref<any[]>([])

const modalVisible = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({
  name: '',
  exchange: 'binance',
  api_key: '',
  api_secret: '',
  is_active: true
})

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: t('common.name'), dataIndex: 'name', key: 'name' },
  { title: t('common.exchange'), dataIndex: 'exchange', key: 'exchange' },
  { title: 'API Key', dataIndex: 'api_key', key: 'api_key' },
  { title: t('common.status'), dataIndex: 'is_active', key: 'is_active' },
  { title: t('common.createdAt'), dataIndex: 'created_at', key: 'created_at' },
  { title: t('common.action'), key: 'action', width: 150 }
]

const loadData = async () => {
  loading.value = true
  try {
    const res: any = await getDataSourceKeys()
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
  Object.assign(form, { name: '', exchange: 'binance', api_key: '', api_secret: '', is_active: true })
  modalVisible.value = true
}

const editKey = (record: any) => {
  editingId.value = record.id
  Object.assign(form, { 
    name: record.name, 
    exchange: record.exchange, 
    api_key: record.api_key, 
    api_secret: '', // Do not load the secret for security, typically
    is_active: record.is_active 
  })
  modalVisible.value = true
}

const handleSave = async () => {
  if (!form.name || !form.exchange) {
    message.warning('请填写必要信息')
    return
  }
  saving.value = true
  try {
    const payload = editingId.value ? { ...form, id: editingId.value } : form
    const res: any = await saveDataSourceKey(payload)
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
    const res: any = await deleteDataSourceKey(id)
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
