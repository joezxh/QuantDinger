<template>
  <div class="api-key-manager">
    <div class="page-header">
      <div>
        <h2>API 密钥管理</h2>
        <p class="subtitle">数据源: {{ sourceCode }}</p>
      </div>
      <a-space>
        <a-button @click="goBack">返回</a-button>
        <a-button type="primary" @click="showAddModal" icon="PlusOutlined">
          添加密钥
        </a-button>
      </a-space>
    </div>

    <a-card :bordered="false">
      <a-table
        :columns="columns"
        :data-source="apiKeys"
        :loading="loading"
        row-key="id"
        :pagination="false"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'key_type'">
            <a-tag :color="record.key_type === 'public' ? 'blue' : 'purple'">
              {{ record.key_type === 'public' ? '公共' : '私有' }}
            </a-tag>
          </template>

          <template v-if="column.key === 'status'">
            <a-badge
              :status="record.status === 'active' ? 'success' : 'default'"
              :text="record.status === 'active' ? '启用' : '禁用'"
            />
          </template>

          <template v-if="column.key === 'health_status'">
            <a-badge
              :status="record.health_status === 'healthy' ? 'success' : 
                       record.health_status === 'unhealthy' ? 'error' : 'default'"
              :text="record.health_status === 'healthy' ? '健康' : 
                     record.health_status === 'unhealthy' ? '异常' : '未知'"
            />
          </template>

          <template v-if="column.key === 'usage'">
            <div>
              <div>今日调用: {{ record.current_daily_calls }} / {{ record.daily_call_limit || '∞' }}</div>
              <a-progress
                :percent="calculateUsagePercent(record)"
                :status="getUsageStatus(record)"
                size="small"
                style="margin-top: 4px;"
              />
            </div>
          </template>

          <template v-if="column.key === 'action'">
            <a-space>
              <a @click="handleToggleStatus(record)">
                {{ record.status === 'active' ? '禁用' : '启用' }}
              </a>
              <a @click="handleEdit(record)">编辑</a>
              <a-popconfirm
                title="确定删除此密钥吗？"
                @confirm="handleDelete(record.id)"
              >
                <a style="color: #ff4d4f">删除</a>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- Add/Edit Modal -->
    <a-modal
      v-model:open="modalVisible"
      :title="editingKey ? '编辑密钥' : '添加密钥'"
      @ok="handleSubmit"
      :confirmLoading="submitting"
      width="600px"
    >
      <a-form :model="formState" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="密钥类型" required>
              <a-select v-model:value="formState.key_type">
                <a-select-option value="public">公共密钥</a-select-option>
                <a-select-option value="private">私有密钥</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="密钥别名" required>
              <a-input v-model:value="formState.key_alias" placeholder="如: API Key #1" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="密钥值" required>
          <a-input-password
            v-model:value="formState.encrypted_key_value"
            placeholder="请输入API密钥"
          />
        </a-form-item>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="权重">
              <a-input-number
                v-model:value="formState.weight"
                :min="1"
                :max="100"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="日调用限制">
              <a-input-number
                v-model:value="formState.daily_call_limit"
                :min="0"
                :step="10"
                style="width: 100%"
                placeholder="0表示不限制"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="启用状态">
          <a-switch v-model:checked="formState.status" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  getApiKeys,
  addApiKey,
  updateApiKey,
  deleteApiKey,
  toggleApiKey
} from '@/api/data-source'

const route = useRoute()
const router = useRouter()

const sourceCode = ref(route.query.source_code as string || '')
const loading = ref(false)
const submitting = ref(false)
const modalVisible = ref(false)
const editingKey = ref<any>(null)
const apiKeys = ref<any[]>([])

const columns = [
  { title: 'ID', dataIndex: 'id', width: 60 },
  { title: '密钥类型', dataIndex: 'key_type', key: 'key_type', width: 100 },
  { title: '别名', dataIndex: 'key_alias', width: 180 },
  { title: '权重', dataIndex: 'weight', width: 80 },
  { title: '使用统计', dataIndex: 'usage', key: 'usage', width: 250 },
  { title: '连续错误', dataIndex: 'consecutive_errors', width: 100 },
  { title: '健康状态', dataIndex: 'health_status', key: 'health_status', width: 100 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
  { title: '操作', key: 'action', width: 200 }
]

const formState = reactive({
  key_type: 'public',
  key_alias: '',
  encrypted_key_value: '',
  weight: 1,
  daily_call_limit: 0,
  status: true
})

const loadData = async () => {
  if (!sourceCode.value) return
  
  loading.value = true
  try {
    const res = await getApiKeys(sourceCode.value)
    if (res) {
      apiKeys.value = res.api_keys || []
    }
  } catch (error) {
    message.error('加载密钥失败')
  } finally {
    loading.value = false
  }
}

const showAddModal = () => {
  editingKey.value = null
  Object.assign(formState, {
    key_type: 'public',
    key_alias: '',
    encrypted_key_value: '',
    weight: 1,
    daily_call_limit: 0,
    status: true
  })
  modalVisible.value = true
}

const handleEdit = (record: any) => {
  editingKey.value = record
  Object.assign(formState, {
    key_type: record.key_type,
    key_alias: record.key_alias,
    encrypted_key_value: '',
    weight: record.weight,
    daily_call_limit: record.daily_call_limit || 0,
    status: record.status === 'active'
  })
  modalVisible.value = true
}

const handleSubmit = async () => {
  if (!formState.key_alias || !formState.encrypted_key_value) {
    message.warning('请填写必填项')
    return
  }

  submitting.value = true
  try {
    const payload = {
      key_type: formState.key_type,
      key_alias: formState.key_alias,
      encrypted_key_value: formState.encrypted_key_value,
      weight: formState.weight,
      daily_call_limit: formState.daily_call_limit,
      status: formState.status ? 'active' : 'inactive'
    }

    if (editingKey.value) {
      await updateApiKey(sourceCode.value, editingKey.value.id, payload)
      message.success('更新成功')
    } else {
      await addApiKey(sourceCode.value, payload)
      message.success('添加成功')
    }

    modalVisible.value = false
    loadData()
  } catch (error) {
    message.error('操作失败')
  } finally {
    submitting.value = false
  }
}

const handleToggleStatus = async (record: any) => {
  try {
    const newStatus = record.status === 'active' ? false : true
    await toggleApiKey(sourceCode.value, record.id, newStatus)
    message.success(newStatus ? '已启用' : '已禁用')
    loadData()
  } catch (error) {
    message.error('操作失败')
  }
}

const handleDelete = async (id: number) => {
  try {
    await deleteApiKey(sourceCode.value, id)
    message.success('删除成功')
    loadData()
  } catch (error) {
    message.error('删除失败')
  }
}

const calculateUsagePercent = (record: any) => {
  if (!record.daily_call_limit || record.daily_call_limit === 0) return 0
  return Math.min((record.current_daily_calls / record.daily_call_limit) * 100, 100)
}

const getUsageStatus = (record: any) => {
  const percent = calculateUsagePercent(record)
  if (percent >= 90) return 'exception'
  if (percent >= 70) return 'normal'
  return 'success'
}

const goBack = () => {
  router.push('/data-source')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="less">
.api-key-manager {
  padding: 32px;
  background: #f8fafc;
  min-height: 100vh;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;

    h2 {
      font-size: 24px;
      font-weight: 700;
      color: #1e293b;
      margin: 0 0 4px 0;
    }

    .subtitle {
      color: #64748b;
      font-size: 14px;
      margin: 0;
    }
  }
}
</style>
