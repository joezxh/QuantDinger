<template>
  <div class="dify-workflow-page">
    <a-page-header
      title="Dify 工作流管理"
      sub-title="配置和管理 AI 分析工作流"
    >
      <template slot="extra">
        <a-button type="primary" icon="plus" @click="showCreateModal">
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
        <template slot="status" slot-scope="text, record">
          <a-switch
            :checked="record.is_active"
            @change="checked => toggleActive(record, checked)"
          />
        </template>
        <template slot="action" slot-scope="text, record">
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
      :visible="modalVisible"
      :confirm-loading="modalLoading"
      @ok="handleModalSubmit"
      @cancel="modalVisible = false"
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
          <a-textarea v-model="form.description" rows="2" />
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
          <a-textarea v-model="form.input_schema" rows="3" placeholder="{&quot;market&quot;: &quot;string&quot;, &quot;symbol&quot;: &quot;string&quot;}" />
        </a-form-item>
        <a-form-item label="输出 Schema">
          <a-textarea v-model="form.output_schema" rows="3" placeholder="{&quot;signal&quot;: &quot;string&quot;, &quot;confidence&quot;: &quot;number&quot;}" />
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
      :visible="runModalVisible"
      :confirm-loading="runLoading"
      @ok="handleRunSubmit"
      @cancel="runModalVisible = false"
    >
      <a-form :model="runForm" :label-col="{ span: 5 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="工作流">
          <span>{{ runForm.code }}</span>
        </a-form-item>
        <a-form-item label="输入参数">
          <a-textarea
            v-model="runForm.inputsJson"
            rows="5"
            placeholder="{&quot;market&quot;: &quot;crypto&quot;, &quot;symbol&quot;: &quot;BTC/USDT&quot;}"
          />
        </a-form-item>
      </a-form>
      <a-divider v-if="runResult" />
      <pre v-if="runResult" style="max-height: 300px; overflow: auto; background: #f6f6f6; padding: 12px; border-radius: 4px;">{{ JSON.stringify(runResult, null, 2) }}</pre>
    </a-modal>

    <!-- Logs Modal -->
    <a-modal
      title="执行日志"
      :visible="logsModalVisible"
      :footer="null"
      @cancel="logsModalVisible = false"
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

<script>
import {
  getWorkflows,
  createWorkflow,
  updateWorkflow,
  deleteWorkflow,
  runWorkflow,
  getWorkflowLogs
} from '@/api/dify'

const columns = [
  { title: '编码', dataIndex: 'code', width: 160 },
  { title: '名称', dataIndex: 'name' },
  { title: '类型', dataIndex: 'workflow_type', width: 100 },
  { title: '状态', scopedSlots: { customRender: 'status' }, width: 80 },
  { title: '操作', scopedSlots: { customRender: 'action' }, width: 200 }
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

export default {
  name: 'DifyWorkflow',
  data () {
    return {
      columns,
      logColumns,
      workflows: [],
      loading: false,
      modalVisible: false,
      modalLoading: false,
      modalTitle: '注册工作流',
      isEdit: false,
      form: this.getEmptyForm(),
      runModalVisible: false,
      runLoading: false,
      runForm: { code: '', inputsJson: '{}' },
      runResult: null,
      logsModalVisible: false,
      logsLoading: false,
      logs: []
    }
  },
  mounted () {
    this.loadWorkflows()
  },
  methods: {
    getEmptyForm () {
      return {
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
      }
    },
    async loadWorkflows () {
      this.loading = true
      try {
        const res = await getWorkflows()
        if (res.success) {
          this.workflows = res.data || []
        }
      } catch (e) {
        this.$message.error('加载工作流失败')
      } finally {
        this.loading = false
      }
    },
    showCreateModal () {
      this.isEdit = false
      this.modalTitle = '注册工作流'
      this.form = this.getEmptyForm()
      this.modalVisible = true
    },
    showEditModal (record) {
      this.isEdit = true
      this.modalTitle = '编辑工作流'
      this.form = {
        ...record,
        input_schema: JSON.stringify(record.input_schema || {}),
        output_schema: JSON.stringify(record.output_schema || {})
      }
      this.modalVisible = true
    },
    async handleModalSubmit () {
      this.modalLoading = true
      try {
        const payload = {
          ...this.form,
          input_schema: JSON.parse(this.form.input_schema || '{}'),
          output_schema: JSON.parse(this.form.output_schema || '{}')
        }
        if (this.isEdit) {
          await updateWorkflow(this.form.code, payload)
        } else {
          await createWorkflow(payload)
        }
        this.$message.success(this.isEdit ? '更新成功' : '注册成功')
        this.modalVisible = false
        this.loadWorkflows()
      } catch (e) {
        this.$message.error('保存失败: ' + e.message)
      } finally {
        this.modalLoading = false
      }
    },
    async handleDelete (code) {
      try {
        await deleteWorkflow(code)
        this.$message.success('删除成功')
        this.loadWorkflows()
      } catch (e) {
        this.$message.error('删除失败')
      }
    },
    showRunModal (record) {
      this.runForm = { code: record.code, inputsJson: '{}' }
      this.runResult = null
      this.runModalVisible = true
    },
    async handleRunSubmit () {
      this.runLoading = true
      try {
        const inputs = JSON.parse(this.runForm.inputsJson || '{}')
        const res = await runWorkflow(this.runForm.code, { inputs, streaming: false })
        if (res.success) {
          this.runResult = res.data
          this.$message.success('执行成功')
        } else {
          this.$message.error(res.error || '执行失败')
        }
      } catch (e) {
        this.$message.error('执行失败: ' + e.message)
      } finally {
        this.runLoading = false
      }
    },
    async showLogs (record) {
      this.logsModalVisible = true
      this.logsLoading = true
      try {
        const res = await getWorkflowLogs(record.code, { limit: 50 })
        if (res.success) {
          this.logs = res.data || []
        }
      } catch (e) {
        this.$message.error('加载日志失败')
      } finally {
        this.logsLoading = false
      }
    },
    async toggleActive (record, checked) {
      try {
        await updateWorkflow(record.code, { ...record, is_active: checked })
        record.is_active = checked
      } catch (e) {
        this.$message.error('状态更新失败')
      }
    }
  }
}
</script>

<style scoped>
.dify-workflow-page {
  padding: 0 12px;
}
</style>
