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
          <a-badge :status="text ? 'success' : 'default'" :text="text ? '启用' : '禁用'" />
        </template>
        <template v-if="column.key === 'market_categories'">
          <a-tag v-for="cat in (text || [])" :key="cat" color="blue">{{ cat }}</a-tag>
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a @click="handleTest(record)">测试</a>
            <a @click="handleEdit(record)">编辑</a>
            <a-popconfirm :title="t('batch.auto9')" @confirm="handleDelete(record.id)">
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
import { message } from 'ant-design-vue'
import { getConfigs, saveConfig, deleteConfig, testConfig } from '@/api/data-source'

const { t } = useI18n()
const loading = ref(false)
const data = ref([])
const searchText = ref('')
const filterLayer = ref(undefined)
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
  { title: t('common.status'), dataIndex: 'enabled', key: 'enabled', width: 80 },
  { title: t('common.action'), key: 'action', width: 180 }
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
    const res = await getConfigs({
      search: searchText.value || undefined,
      layer: filterLayer.value || undefined,
      page: pagination.current,
      page_size: pagination.pageSize
    })
    if (res.code === 1) {
      data.value = res.data.items
      pagination.total = res.data.total
    }
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
      return message.error(t('batch.auto3'))
    }

    const payload = { ...formState, id: editId.value, config_json: configJson }
    const res = await saveConfig(payload)
    if (res.code === 1) {
      message.success(t('common.success'))
      visible.value = false
      loadData()
    }
  } finally {
    confirmLoading.value = false
  }
}

const handleDelete = async (id: number) => {
  const res = await deleteConfig(id)
  if (res.code === 1) {
    message.success(t('common.deleted'))
    loadData()
  }
}

const handleTest = async (record: any) => {
  const res = await testConfig(record.id)
  if (res.code === 1) {
    message.success(t('batch.auto4'))
  } else {
    message.error('连接失败: ' + res.msg)
  }
}

onMounted(loadData)
</script>

<style scoped lang="less">
.table-operator { margin-bottom: 16px; }
</style>
