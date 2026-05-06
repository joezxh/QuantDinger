<template>
  <div class="config-list">
    <div class="table-operator">
      <a-space>
        <a-button type="primary" @click="handleAdd">
          <template #icon><PlusOutlined /></template>
          新增数据源
        </a-button>
        <a-input-search
          v-model:value="searchText"
          :placeholder="t('batch.auto5')"
          style="width: 250px"
          @search="handleSearch"
        />
        <a-select
          v-model:value="filterLayer"
          :placeholder="t('batch.auto6')"
          style="width: 150px"
          allow-clear
          @change="handleSearch"
        >
          <a-select-option value="data_source">{{ t('batch.auto16') }}</a-select-option>
          <a-select-option value="data_provider">{{ t('batch.auto17') }}</a-select-option>
          <a-select-option value="fundamental">{{ t('batch.auto18') }}</a-select-option>
          <a-select-option value="sentiment">{{ t('batch.auto19') }}</a-select-option>
        </a-select>
      </a-space>
    </div>

    <a-table
      size="middle"
      row-key="id"
      :columns="columns"
      :data-source="data"
      :loading="loading"
      :pagination="pagination"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record, text }">
        <template v-if="column.key === 'enabled'">
          <a-switch
            v-model:checked="record.enabled"
            @change="handleToggle(record)"
            :loading="record.toggleLoading"
          />
        </template>
        <template v-if="column.key === 'market_categories'">
          <a-tag v-for="cat in (text || [])" :key="cat" color="blue">{{ cat }}</a-tag>
        </template>
        <template v-if="column.key === 'health_status'">
          <a-badge
            :status="text === 'healthy' ? 'success' : text === 'unhealthy' ? 'error' : 'default'"
            :text="text === 'healthy' ? '健康' : text === 'unhealthy' ? '异常' : '未知'"
          />
        </template>
        <template v-if="column.key === 'api_keys'">
          <a-tag :color="text ? 'success' : 'warning'">
            {{ text ? `已配置 (${text})` : '未配置' }}
          </a-tag>
        </template>
        <template v-if="column.key === 'rate_limit'">
          <span>{{ text?.strategy || 'token_bucket' }}: {{ text?.rate || 60 }}/min</span>
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a @click="handleHealthCheck(record)">健康检查</a>
            <a @click="handleApiKeys(record)">密钥管理</a>
            <a @click="handleRateLimit(record)">限流配置</a>
            <a @click="handleEdit(record)">编辑</a>
            <a-popconfirm :title="t('batch.auto9')" @confirm="handleDelete(record)">
              <a style="color: #ff4d4f">删除</a>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- Edit Modal -->
    <a-modal
      v-model:open="visible"
      :title="editId ? '编辑数据源' : '新增数据源'"
      :confirm-loading="confirmLoading"
      width="700px"
      @ok="handleOk"
    >
      <a-form :model="formState" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item :label="t('batch.auto10')" required>
              <a-input v-model:value="formState.source_code" :disabled="!!editId" :placeholder="t('batch.auto7')" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item :label="t('batch.auto11')" required>
              <a-input v-model:value="formState.source_name" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item :label="t('batch.auto12')" required>
              <a-select v-model:value="formState.layer">
                <a-select-option value="data_source">{{ t('batch.auto16') }}</a-select-option>
                <a-select-option value="data_provider">{{ t('batch.auto17') }}</a-select-option>
                <a-select-option value="fundamental">{{ t('batch.auto18') }}</a-select-option>
                <a-select-option value="sentiment">{{ t('batch.auto19') }}</a-select-option>
                <a-select-option value="collector">{{ t('batch.auto20') }}</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item :label="t('batch.auto13')">
              <a-select v-model:value="formState.market_categories" mode="multiple" :placeholder="t('batch.auto8')">
                <a-select-option value="Crypto">{{ t('batch.auto21') }}</a-select-option>
                <a-select-option value="USStock">{{ t('batch.auto22') }}</a-select-option>
                <a-select-option value="CNStock">{{ t('batch.auto23') }}</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item :label="t('batch.auto14')">
          <a-switch v-model:checked="formState.enabled" />
        </a-form-item>
        <a-form-item :label="t('batch.auto15')">
          <a-textarea v-model:value="formState.config_json_str" :rows="6" placeholder='{"base_url": "https://api.example.com"}' />
        </a-form-item>
        <a-form-item :label="t('common.remark')">
          <a-textarea v-model:value="formState.notes" :rows="2" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { PlusOutlined } from '@ant-design/icons-vue'
import { message, Modal } from 'ant-design-vue'
import {
  getDataSources,
  createDataSource,
  updateDataSource,
  deleteDataSource,
  toggleDataSource,
  testDataSource,
  getApiKeys
} from '@/api/data-source'
import { useRouter } from 'vue-router'

const { t } = useI18n()
const router = useRouter()
const loading = ref(false)
const data = ref<any[]>([])
const searchText = ref('')
const filterLayer = ref<string | undefined>(undefined)
const visible = ref(false)
const confirmLoading = ref(false)
const editId = ref<number | null>(null)

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true
})

const columns = [
  { title: 'ID', dataIndex: 'id', width: 60 },
  { title: t('batch.auto10'), dataIndex: 'source_code' },
  { title: t('common.name'), dataIndex: 'source_name' },
  { title: t('batch.auto12'), dataIndex: 'layer' },
  { title: t('batch.auto13'), dataIndex: 'market_categories', key: 'market_categories' },
  { title: '健康状态', dataIndex: 'health_status', key: 'health_status', width: 100 },
  { title: 'API密钥', dataIndex: 'api_key_configured', key: 'api_keys', width: 120 },
  { title: '限流配置', dataIndex: 'rate_limit', key: 'rate_limit', width: 140 },
  { title: t('common.status'), dataIndex: 'enabled', key: 'enabled', width: 100 },
  { title: t('common.action'), key: 'action', width: 280 }
]

const formState = reactive({
  source_code: '',
  source_name: '',
  layer: 'data_provider',
  market_categories: [],
  enabled: true,
  config_json_str: '{}',
  notes: ''
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await getDataSources({
      search: searchText.value || undefined,
      layer: filterLayer.value || undefined,
      page: pagination.current,
      page_size: pagination.pageSize
    })
    if (res) {
      data.value = res.data_sources.map((item: any) => ({
        ...item,
        toggleLoading: false,
        health_status: 'unknown'
      }))
      pagination.total = res.total
    }
  } catch (error) {
    message.error('加载数据源失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.current = 1
  loadData()
}

const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadData()
}

const handleAdd = () => {
  editId.value = null
  Object.assign(formState, {
    source_code: '',
    source_name: '',
    layer: 'data_provider',
    market_categories: [],
    enabled: true,
    config_json_str: '{}',
    notes: ''
  })
  visible.value = true
}

const handleEdit = (record: any) => {
  editId.value = record.id
  Object.assign(formState, {
    ...record,
    config_json_str: JSON.stringify(record.config_json || {}, null, 2)
  })
  visible.value = true
}

const handleOk = async () => {
  confirmLoading.value = true
  try {
    let configJson = {}
    try {
      configJson = JSON.parse(formState.config_json_str)
    } catch (e) {
      return message.error('JSON格式错误')
    }

    const payload = {
      source_code: formState.source_code,
      source_name: formState.source_name,
      layer: formState.layer,
      market_categories: formState.market_categories,
      enabled: formState.enabled,
      load_balance_strategy: 'round_robin',
      config_json: configJson,
      notes: formState.notes
    }

    if (editId.value) {
      const res = await updateDataSource(formState.source_code, payload)
      if (res) {
        message.success('更新成功')
        visible.value = false
        loadData()
      }
    } else {
      const res = await createDataSource(payload)
      if (res) {
        message.success('创建成功')
        visible.value = false
        loadData()
      }
    }
  } catch (error) {
    message.error('操作失败')
  } finally {
    confirmLoading.value = false
  }
}

const handleDelete = async (record: any) => {
  try {
    const res = await deleteDataSource(record.source_code)
    if (res) {
      message.success('删除成功')
      loadData()
    }
  } catch (error) {
    message.error('删除失败')
  }
}

const handleToggle = async (record: any) => {
  record.toggleLoading = true
  try {
    const res = await toggleDataSource(record.source_code, record.enabled)
    if (res) {
      message.success(record.enabled ? '已启用' : '已禁用')
    }
  } catch (error) {
    record.enabled = !record.enabled
    message.error('操作失败')
  } finally {
    record.toggleLoading = false
  }
}

const handleHealthCheck = async (record: any) => {
  try {
    const res = await testDataSource(record.source_code)
    if (res) {
      record.health_status = res.status
      Modal.info({
        title: '健康检查结果',
        content: `状态: ${res.status === 'healthy' ? '健康' : '异常'}\n响应时间: ${res.latency_ms}ms`,
        okText: '确定'
      })
    }
  } catch (error) {
    message.error('健康检查失败')
  }
}

const handleApiKeys = (record: any) => {
  // 导航到API密钥管理页面
  router.push({
    path: '/data-source/keys',
    query: { source_code: record.source_code }
  })
}

const handleRateLimit = (record: any) => {
  // 导航到限流配置页面
  router.push({
    path: '/data-source/rate-limit',
    query: { source_code: record.source_code }
  })
}

const handleTest = async (record: any) => {
  await handleHealthCheck(record)
}

onMounted(loadData)
</script>

<style scoped lang="less">
.table-operator { margin-bottom: 16px; }
</style>
