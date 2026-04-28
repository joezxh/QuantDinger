<template>
  <div class="sync-task-tab">
    <!-- Global Stats -->
    <a-row :gutter="16" class="status-cards">
      <a-col :span="6">
        <a-card size="small" :loading="loading">
          <a-statistic title="运行中 Worker" :value="runningWorkers" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small" :loading="loading">
          <a-statistic title="总任务数" :value="jobs.length" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small" :loading="loading">
          <a-statistic title="已启用" :value="enabledJobs" :value-style="{ color: '#52c41a' }" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small" :loading="loading">
          <a-statistic title="上次失败" :value="failedJobs" :value-style="{ color: failedJobs > 0 ? '#ff4d4f' : '#52c41a' }" />
        </a-card>
      </a-col>
    </a-row>

    <!-- Toolbar -->
    <div class="table-operator">
      <a-space>
        <a-button type="primary" @click="handleAddJob">
          <template #icon><PlusOutlined /></template>
          新增任务
        </a-button>
        <a-button @click="loadStatus" :loading="loading">
          <template #icon><SyncOutlined /></template>
          刷新
        </a-button>
        <a-select
          v-model:value="filterSourceType"
          placeholder="筛选数据源类型"
          style="width: 180px"
          allow-clear
        >
          <a-select-option value="polymarket">Polymarket</a-select-option>
          <a-select-option value="crypto">Crypto</a-select-option>
          <a-select-option value="stock">Stock</a-select-option>
        </a-select>
      </a-space>
    </div>

    <!-- Job Table -->
    <a-table
      size="middle"
      row-key="id"
      :columns="jobColumns"
      :data-source="filteredJobs"
      :loading="loading"
      :expand-column-width="50"
    >
      <template #bodyCell="{ column, record, text }">
        <template v-if="column.key === 'enabled'">
          <a-badge :status="text ? 'success' : 'default'" :text="text ? '启用' : '禁用'" />
        </template>
        <template v-if="column.key === 'source_type'">
          <a-tag color="blue">{{ text }}</a-tag>
        </template>
        <template v-if="column.key === 'last_run_at'">
          {{ text ? dayjs(text).format('YYYY-MM-DD HH:mm:ss') : '暂无' }}
        </template>
        <template v-if="column.key === 'last_status'">
          <a-badge :status="statusBadgeMap[text] || 'default'" :text="statusTextMap[text] || text || '未知'" />
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a @click="handleManualRun(record, 'incremental')">增量同步</a>
            <a @click="handleManualRun(record, 'full')">全量同步</a>
            <a @click="handleEdit(record)">配置</a>
            <a-popconfirm title="确定删除此任务？" @confirm="handleDelete(record.id)">
              <a style="color: #ff4d4f">删除</a>
            </a-popconfirm>
          </a-space>
        </template>
      </template>

      <!-- Expanded History -->
      <template #expandedRowRender="{ record }">
        <div class="expanded-history">
          <h4 style="margin-bottom: 12px">执行历史 - {{ record.name }}</h4>
          <a-table
            size="small"
            row-key="id"
            :columns="runColumns"
            :data-source="runMap[record.id] || []"
            :loading="runLoadingMap[record.id]"
            :pagination="false"
          >
            <template #bodyCell="{ column, record: run, text }">
              <template v-if="column.key === 'run_type'">
                <a-tag :color="text === 'full' ? 'purple' : 'blue'">{{ text === 'full' ? '全量' : '增量' }}</a-tag>
              </template>
              <template v-if="column.key === 'status'">
                <a-badge :status="statusBadgeMap[text] || 'default'" :text="statusTextMap[text] || text" />
              </template>
              <template v-if="column.key === 'items'">
                <span v-if="run.items_fetched !== null">
                  {{ run.items_saved || 0 }} / {{ run.items_fetched || 0 }}
                  <span v-if="run.items_failed" style="color: #ff4d4f; font-size: 11px">(失败 {{ run.items_failed }})</span>
                </span>
                <span v-else>-</span>
              </template>
              <template v-if="column.key === 'time'">
                <div style="font-size: 11px">
                  <div>起: {{ dayjs(run.started_at).format('MM-DD HH:mm:ss') }}</div>
                  <div v-if="run.finished_at">终: {{ dayjs(run.finished_at).format('MM-DD HH:mm:ss') }}</div>
                </div>
              </template>
            </template>
          </a-table>
        </div>
      </template>
    </a-table>

    <!-- Edit Modal -->
    <a-modal
      v-model:open="modalVisible"
      :title="editId ? '编辑同步任务' : '新增同步任务'"
      :confirm-loading="modalLoading"
      @ok="handleModalOk"
      width="600px"
    >
      <a-form :model="formState" layout="vertical">
        <a-form-item label="任务名称" required>
          <a-input v-model:value="formState.name" />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="数据源类型" required>
              <a-select v-model:value="formState.source_type" :disabled="!!editId">
                <a-select-option value="polymarket">Polymarket</a-select-option>
                <a-select-option value="crypto">Crypto</a-select-option>
                <a-select-option value="stock">Stock</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="执行间隔 (分钟)" required>
              <a-input-number v-model:value="formState.interval_minutes" :min="1" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="启用状态">
          <a-switch v-model:checked="formState.enabled" />
        </a-form-item>
        <a-form-item label="高级配置 (JSON)">
          <a-textarea v-model:value="formState.config_json" :rows="4" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { PlusOutlined, SyncOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import {
  createSyncJob, updateSyncJob, deleteSyncJob,
  runSyncJob, getSyncRuns, getSyncStatus
} from '@/api/sync'

const loading = ref(false)
const modalLoading = ref(false)
const modalVisible = ref(false)
const editId = ref<number | null>(null)
const filterSourceType = ref(undefined)

const jobs = ref<any[]>([])
const workers = ref<any[]>([])
const runMap = ref<Record<number, any[]>>({})
const runLoadingMap = ref<Record<number, boolean>>({})

const statusBadgeMap = { success: 'success', failed: 'error', running: 'processing' }
const statusTextMap = { success: '成功', failed: '失败', running: '运行中' }

const jobColumns = [
  { title: 'ID', dataIndex: 'id', width: 60 },
  { title: '名称', dataIndex: 'name' },
  { title: '数据源', dataIndex: 'source_type', key: 'source_type', width: 120 },
  { title: '间隔(min)', dataIndex: 'interval_minutes', width: 100 },
  { title: '状态', dataIndex: 'enabled', key: 'enabled', width: 80 },
  { title: '上次执行', dataIndex: 'last_run_at', key: 'last_run_at', width: 160 },
  { title: '结果', dataIndex: 'last_status', key: 'last_status', width: 100 },
  { title: '操作', key: 'action', width: 240 }
]

const runColumns = [
  { title: 'ID', dataIndex: 'id', width: 50 },
  { title: '类型', dataIndex: 'run_type', key: 'run_type', width: 80 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
  { title: '数据量', key: 'items', width: 130 },
  { title: '时间', key: 'time', width: 220 },
  { title: '错误', dataIndex: 'error_message', ellipsis: true }
]

const formState = reactive({
  name: '',
  source_type: 'polymarket',
  interval_minutes: 30,
  enabled: true,
  config_json: '{}'
})

const filteredJobs = computed(() => {
  if (!filterSourceType.value) return jobs.value
  return jobs.value.filter(j => j.source_type === filterSourceType.value)
})

const runningWorkers = computed(() => workers.value.filter(w => w.running).length)
const enabledJobs = computed(() => jobs.value.filter(j => j.enabled).length)
const failedJobs = computed(() => jobs.value.filter(j => j.last_status === 'failed').length)

const loadStatus = async () => {
  loading.value = true
  try {
    const res = await getSyncStatus()
    if (res.code === 1) {
      jobs.value = res.data.jobs || []
      workers.value = res.data.workers || []
    }
  } finally {
    loading.value = false
  }
}

const handleAddJob = () => {
  editId.value = null
  Object.assign(formState, {
    name: '', source_type: 'polymarket', interval_minutes: 30, enabled: true, config_json: '{}'
  })
  modalVisible.value = true
}

const handleEdit = (record: any) => {
  editId.value = record.id
  Object.assign(formState, { ...record })
  modalVisible.value = true
}

const handleModalOk = async () => {
  modalLoading.value = true
  try {
    const res = editId.value 
      ? await updateSyncJob(editId.value, formState)
      : await createSyncJob(formState)
    if (res.code === 1) {
      message.success('操作成功')
      modalVisible.value = false
      loadStatus()
    }
  } finally {
    modalLoading.value = false
  }
}

const handleDelete = async (id: number) => {
  const res = await deleteSyncJob(id)
  if (res.code === 1) {
    message.success('已删除')
    loadStatus()
  }
}

const handleManualRun = async (record: any, type: string) => {
  const res = await runSyncJob(record.id, { run_type: type })
  if (res.code === 1) {
    message.success('同步已触发')
    setTimeout(loadStatus, 2000)
  }
}

onMounted(loadStatus)
</script>

<style scoped lang="less">
.sync-task-tab {
  .status-cards { margin-bottom: 24px; }
  .table-operator { margin-bottom: 16px; }
  .expanded-history {
    padding: 16px 24px;
    background: #f8fafc;
    border-radius: 8px;
  }
}
</style>
