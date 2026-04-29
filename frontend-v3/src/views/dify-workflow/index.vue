<template>
  <div class="dify-workflow-page">
    <a-page-header
      :title="t('batch.auto68')"
      sub-:title="t('batch.auto69')"
    >
      <template #extra>
        <a-button type="primary" @click="showCreateModal">
          <template #icon><PlusOutlined /></template>
          注册工作流
        </a-button>
      </template>
    </a-page-header>

    <a-card :bordered="false">
      <a-table
        :columns="columns"
        :data-source="workflows"
        :loading="loading"
        row-key="code"
        size="middle"
      >
        <template #status="{ record }">
          <a-switch
            :checked="record.is_active"
            @change="(checked: boolean) => toggleActive(record, checked)"
          />
        </template>
        <template #action="{ record }">
          <a-button type="link" size="small" @click="showRunModal(record)">{{ t('graphAnalysis.executeQuery') }}</a-button>
          <a-button type="link" size="small" @click="showLogs(record)">{{ t('trading-bot.tab.logs') }}</a-button>
          <a-button type="link" size="small" @click="showEditModal(record)">{{ t('common.edit') }}</a-button>
          <a-popconfirm
            :title="t('batch.auto70')"
            @confirm="handleDelete(record.code)"
          >
            <a-button type="link" size="small" danger>{{ t('common.delete') }}</a-button>
          </a-popconfirm>
        </template>
      </a-table>
    </a-card>

    <!-- Create / Edit Modal -->
    <a-modal
      :title="modalTitle"
      v-model:visible="modalVisible"
      :confirm-loading="modalLoading"
      @ok="handleModalSubmit"
      width="700px"
    >
      <a-form :model="form" :label-col="{ span: 5 }" :wrapper-col="{ span: 18 }">
        <a-form-item :label="t('batch.auto73')" required>
          <a-input v-model="form.code" :placeholder="t('batch.auto66')" :disabled="isEdit" />
        </a-form-item>
        <a-form-item :label="t('common.name')" required>
          <a-input v-model="form.name" :placeholder="t('batch.auto67')" />
        </a-form-item>
        <a-form-item :label="t('batch.auto74')">
          <a-textarea v-model="form.description" :rows="2" />
        </a-form-item>
        <a-form-item :label="t('common.type')">
          <a-select v-model="form.workflow_type">
            <a-select-option value="chat">Chat</a-select-option>
            <a-select-option value="workflow">Workflow</a-select-option>
            <a-select-option value="completion">Completion</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Endpoint" required>
          <a-input v-model="form.endpoint" placeholder="Dify API endpoint" />
        </a-form-item>
        <a-form-item label="API Key" required>
          <a-input-password v-model="form.api_key" placeholder="Dify API Key" />
        </a-form-item>
        <a-form-item :label="t('batch.auto75')">
          <a-textarea v-model="form.input_schema" :rows="3" placeholder='{"market": "string", "symbol": "string"}' />
        </a-form-item>
        <a-form-item :label="t('batch.auto76')">
          <a-textarea v-model="form.output_schema" :rows="3" placeholder='{"signal": "string", "confidence": "number"}' />
        </a-form-item>
        <a-form-item :label="t('batch.auto77')">
          <a-input-number v-model="form.timeout_seconds" :min="10" :max="600" />
        </a-form-item>
        <a-form-item :label="t('batch.auto78')">
          <a-input-number v-model="form.max_retries" :min="0" :max="10" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Run Modal -->
    <a-modal
      :title="t('batch.auto71')"
      v-model:visible="runModalVisible"
      :confirm-loading="runLoading"
      @ok="handleRunSubmit"
    >
      <a-form :model="runForm" :label-col="{ span: 5 }" :wrapper-col="{ span: 18 }">
        <a-form-item :label="t('batch.auto79')">
          <span>{{ runForm.code }}</span>
        </a-form-item>
        <a-form-item :label="t('batch.auto80')">
          <a-textarea
            v-model="runForm.inputsJson"
            :rows="5"
            placeholder='{"market": "crypto", "symbol": "BTC/USDT"}'
          />
        </a-form-item>
      </a-form>
      <a-divider v-if="runResult" />
      <pre v-if="runResult" class="run-result-preview">{{ JSON.stringify(runResult, null, 2) }}</pre>
    </a-modal>

    <!-- Logs Modal -->
    <a-modal
      :title="t('batch.auto72')"
      v-model:visible="logsModalVisible"
      :footer="null"
      width="800px"
    >
      <a-table
        :columns="logColumns"
        :data-source="logs"
        :loading="logsLoading"
        row-key="id"
        size="small"
        :pagination="{ pageSize: 10 }"
      />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import {
  getWorkflows,
  createWorkflow,
  updateWorkflow,
  deleteWorkflow,
  runWorkflow,
  getWorkflowLogs
} from '@/api/dify'

interface Workflow {
  code: string
  name: string
  description?: string
  workflow_type: string
  endpoint: string
  api_key: string
  input_schema?: Record<string, any>
  output_schema?: Record<string, any>
  timeout_seconds?: number
  max_retries?: number
  is_active: boolean
}

interface WorkflowForm {
  code: string
  name: string
  description: string
  workflow_type: string
  endpoint: string
  api_key: string
  input_schema: string
  output_schema: string
  timeout_seconds: number
  max_retries: number
  is_active: boolean
}

const { t } = useI18n()
const columns = [
  { title: t('batch.auto73'), dataIndex: 'code', width: 160 },
  { title: t('common.name'), dataIndex: 'name' },
  { title: t('common.type'), dataIndex: 'workflow_type', width: 100 },
  { title: t('common.status'), slots: { customRender: 'status' }, width: 80 },
  { title: t('common.action'), slots: { customRender: 'action' }, width: 200 }
]

const logColumns = [
  { title: 'ID', dataIndex: 'id', width: 60 },
  { title: t('common.status'), dataIndex: 'status', width: 100 },
  { title: t('common.mode'), dataIndex: 'call_mode', width: 80 },
  { title: 'Token', dataIndex: 'tokens_used', width: 80 },
  { title: t('batch.auto81'), dataIndex: 'latency_ms', width: 100 },
  { title: t('batch.auto82'), dataIndex: 'started_at' },
  { title: t('batch.auto83'), dataIndex: 'error_message', ellipsis: true }
]

const workflows = ref<Workflow[]>([])
const loading = ref(false)
const modalVisible = ref(false)
const modalLoading = ref(false)
const modalTitle = ref('注册工作流')
const isEdit = ref(false)

const getEmptyForm = (): WorkflowForm => ({
  code: '',
  name: '',
  description: '',
  workflow_type: 'chat',
  endpoint: '',
  api_key: '',
  input_schema: '{}',
  output_schema: '{}',
  timeout_seconds: 120,
  max_retries: 3,
  is_active: true
})

const form = reactive<WorkflowForm>(getEmptyForm())

const runModalVisible = ref(false)
const runLoading = ref(false)
const runForm = reactive({ code: '', inputsJson: '{}' })
const runResult = ref<any>(null)

const logsModalVisible = ref(false)
const logsLoading = ref(false)
const logs = ref<any[]>([])

async function loadWorkflows() {
  loading.value = true
  try {
    const res = await getWorkflows()
    if ((res as any).success) {
      workflows.value = (res as any).data || []
    }
  } catch (e) {
    message.error(t('batch.auto62'))
  } finally {
    loading.value = false
  }
}

function showCreateModal() {
  isEdit.value = false
  modalTitle.value = '注册工作流'
  Object.assign(form, getEmptyForm())
  modalVisible.value = true
}

function showEditModal(record: Workflow) {
  isEdit.value = true
  modalTitle.value = '编辑工作流'
  Object.assign(form, {
    ...record,
    input_schema: JSON.stringify(record.input_schema || {}),
    output_schema: JSON.stringify(record.output_schema || {})
  })
  modalVisible.value = true
}

async function handleModalSubmit() {
  modalLoading.value = true
  try {
    const payload = {
      ...form,
      input_schema: JSON.parse(form.input_schema || '{}'),
      output_schema: JSON.parse(form.output_schema || '{}')
    }
    if (isEdit.value) {
      await updateWorkflow(form.code, payload)
    } else {
      await createWorkflow(payload)
    }
    message.success(isEdit.value ? '更新成功' : '注册成功')
    modalVisible.value = false
    await loadWorkflows()
  } catch (e: any) {
    message.error('保存失败: ' + (e.message || 'Unknown error'))
  } finally {
    modalLoading.value = false
  }
}

async function handleDelete(code: string) {
  try {
    await deleteWorkflow(code)
    message.success(t('batch.auto1'))
    await loadWorkflows()
  } catch (e) {
    message.error(t('common.deleteFailed'))
  }
}

function showRunModal(record: Workflow) {
  runForm.code = record.code
  runForm.inputsJson = '{}'
  runResult.value = null
  runModalVisible.value = true
}

async function handleRunSubmit() {
  runLoading.value = true
  try {
    const inputs = JSON.parse(runForm.inputsJson || '{}')
    const res = await runWorkflow(runForm.code, { inputs, streaming: false })
    if ((res as any).success) {
      runResult.value = (res as any).data
      message.success(t('batch.auto63'))
    } else {
      message.error((res as any).error || '执行失败')
    }
  } catch (e: any) {
    message.error('执行失败: ' + (e.message || 'Unknown error'))
  } finally {
    runLoading.value = false
  }
}

async function showLogs(record: Workflow) {
  logsModalVisible.value = true
  logsLoading.value = true
  try {
    const res = await getWorkflowLogs(record.code, { limit: 50 })
    if ((res as any).success) {
      logs.value = (res as any).data || []
    }
  } catch (e) {
    message.error(t('batch.auto64'))
  } finally {
    logsLoading.value = false
  }
}

async function toggleActive(record: Workflow, checked: boolean) {
  try {
    await updateWorkflow(record.code, { ...record, is_active: checked })
    record.is_active = checked
  } catch (e) {
    message.error(t('batch.auto65'))
  }
}

onMounted(() => {
  loadWorkflows()
})
</script>

<style scoped lang="less">
.dify-workflow-page {
  padding: 0 12px;
}

.run-result-preview {
  max-height: 300px;
  overflow: auto;
  background: #f6f6f6;
  padding: 12px;
  border-radius: 4px;
}
</style>
