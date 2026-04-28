<template>
  <div class="dify-workflow-page">
    <a-page-header
      title="Dify 工作流管理"
      sub-title="配置和管理 AI 分析工作流"
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
          <a-button type="link" size="small" @click="showRunModal(record)">
            执行
          </a-button>
          <a-button type="link" size="small" @click="showLogs(record)">
            日志
          </a-button>
          <a-button type="link" size="small" @click="showEditModal(record)">
            编辑
          </a-button>
          <a-popconfirm
            title="确认删除该工作流？"
            @confirm="handleDelete(record.code)"
          >
            <a-button type="link" size="small" danger>
              删除
            </a-button>
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
        <a-form-item label="编码" required>
          <a-input v-model="form.code" placeholder="如 ai_stock_analysis_v1" :disabled="isEdit" />
        </a-form-item>
        <a-form-item label="名称" required>
          <a-input v-model="form.name" placeholder="工作流名称" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model="form.description" :rows="2" />
        </a-form-item>
        <a-form-item label="类型">
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
        <a-form-item label="输入 Schema">
          <a-textarea v-model="form.input_schema" :rows="3" placeholder='{"market": "string", "symbol": "string"}' />
        </a-form-item>
        <a-form-item label="输出 Schema">
          <a-textarea v-model="form.output_schema" :rows="3" placeholder='{"signal": "string", "confidence": "number"}' />
        </a-form-item>
        <a-form-item label="超时(秒)">
          <a-input-number v-model="form.timeout_seconds" :min="10" :max="600" />
        </a-form-item>
        <a-form-item label="最大重试">
          <a-input-number v-model="form.max_retries" :min="0" :max="10" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Run Modal -->
    <a-modal
      title="执行工作流"
      v-model:visible="runModalVisible"
      :confirm-loading="runLoading"
      @ok="handleRunSubmit"
    >
      <a-form :model="runForm" :label-col="{ span: 5 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="工作流">
          <span>{{ runForm.code }}</span>
        </a-form-item>
        <a-form-item label="输入参数">
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
      title="执行日志"
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

const columns = [
  { title: '编码', dataIndex: 'code', width: 160 },
  { title: '名称', dataIndex: 'name' },
  { title: '类型', dataIndex: 'workflow_type', width: 100 },
  { title: '状态', slots: { customRender: 'status' }, width: 80 },
  { title: '操作', slots: { customRender: 'action' }, width: 200 }
]

const logColumns = [
  { title: 'ID', dataIndex: 'id', width: 60 },
  { title: '状态', dataIndex: 'status', width: 100 },
  { title: '模式', dataIndex: 'call_mode', width: 80 },
  { title: 'Token', dataIndex: 'tokens_used', width: 80 },
  { title: '延迟(ms)', dataIndex: 'latency_ms', width: 100 },
  { title: '开始时间', dataIndex: 'started_at' },
  { title: '错误信息', dataIndex: 'error_message', ellipsis: true }
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
    message.error('加载工作流失败')
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
    message.success('删除成功')
    await loadWorkflows()
  } catch (e) {
    message.error('删除失败')
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
      message.success('执行成功')
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
    message.error('加载日志失败')
  } finally {
    logsLoading.value = false
  }
}

async function toggleActive(record: Workflow, checked: boolean) {
  try {
    await updateWorkflow(record.code, { ...record, is_active: checked })
    record.is_active = checked
  } catch (e) {
    message.error('状态更新失败')
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
