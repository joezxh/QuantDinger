<template>
  <div class="sync-task-tab">
    <!-- 全局状态概览 -->
    <a-row :gutter="16" class="status-cards">
      <a-col :span="6">
        <a-card :loading="statusLoading">
          <a-statistic
            title="运行中 Worker"
            :value="runningWorkers"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :loading="statusLoading">
          <a-statistic
            title="总任务数"
            :value="jobs.length"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :loading="statusLoading">
          <a-statistic
            title="已启用"
            :value="enabledJobs"
            :value-style="{ color: '#52c41a' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :loading="statusLoading">
          <a-statistic
            title="上次失败"
            :value="failedJobs"
            :value-style="{ color: failedJobs > 0 ? '#ff4d4f' : '#52c41a' }"
          />
        </a-card>
      </a-col>
    </a-row>

    <!-- 操作栏 -->
    <div class="table-operator">
      <a-button type="primary" icon="plus" @click="handleAddJob">新增任务</a-button>
      <a-button icon="sync" style="margin-left: 8px" :loading="statusLoading" @click="loadStatus">刷新</a-button>
      <a-select
        v-model="filterSourceType"
        placeholder="筛选数据源类型"
        style="width: 180px; margin-left: 16px"
        allowClear
        @change="handleFilterChange"
      >
        <a-select-option value="polymarket">Polymarket</a-select-option>
        <a-select-option value="crypto">Crypto</a-select-option>
        <a-select-option value="stock">Stock</a-select-option>
      </a-select>
    </div>

    <!-- 任务列表表格 -->
    <a-table
      size="default"
      rowKey="id"
      :columns="jobColumns"
      :dataSource="filteredJobs"
      :loading="statusLoading"
      :expandedRowKeys="expandedRowKeys"
      @expand="handleExpand"
    >
      <span slot="enabled" slot-scope="text">
        <a-badge :status="text ? 'success' : 'default'" :text="text ? '启用' : '禁用'" />
      </span>
      <span slot="source_type" slot-scope="text">
        <a-tag color="blue">{{ text }}</a-tag>
      </span>
      <span slot="last_run_at" slot-scope="text">
        {{ formatTime(text) || '暂无' }}
      </span>
      <span slot="last_status" slot-scope="text">
        <a-badge
          :status="statusBadge[text] || 'default'"
          :text="statusText[text] || text || '未知'"
        />
      </span>
      <span slot="action" slot-scope="text, record">
        <template>
          <a @click="handleRun(record, 'incremental')">增量同步</a>
          <a-divider type="vertical" />
          <a @click="handleRun(record, 'full')">全量同步</a>
          <a-divider type="vertical" />
          <a @click="handleEdit(record)">配置</a>
          <a-divider type="vertical" />
          <a-popconfirm title="确定删除此任务？关联的执行历史也会被清理" @confirm="handleDelete(record.id)">
            <a style="color: red">删除</a>
          </a-popconfirm>
        </template>
      </span>

      <!-- 展开区域：执行历史 -->
      <div slot="expandedRowRender" slot-scope="record" class="expanded-content">
        <a-divider orientation="left">执行历史 ({{ record.source_type }} - {{ record.name }})</a-divider>
        <a-table
          size="small"
          rowKey="id"
          :columns="runColumns"
          :dataSource="runMap[record.id] || []"
          :loading="runLoadingMap[record.id]"
          :pagination="false"
        >
          <span slot="run_type" slot-scope="text">
            <a-tag :color="text === 'full' ? 'purple' : 'blue'">
              {{ text === 'full' ? '全量' : '增量' }}
            </a-tag>
          </span>
          <span slot="status" slot-scope="text">
            <a-badge :status="statusBadge[text] || 'default'" :text="statusText[text] || text" />
          </span>
          <span slot="items" slot-scope="text, run">
            <span v-if="run.items_fetched !== null">
              {{ run.items_saved || 0 }} / {{ run.items_fetched || 0 }}
              <span v-if="run.items_failed" style="color: #ff4d4f">(失败 {{ run.items_failed }})</span>
            </span>
            <span v-else>-</span>
          </span>
          <span slot="time" slot-scope="text, run">
            <div>开始: {{ formatTime(run.started_at) }}</div>
            <div v-if="run.finished_at">结束: {{ formatTime(run.finished_at) }}</div>
          </span>
        </a-table>
      </div>
    </a-table>

    <!-- 创建/编辑任务模态框 -->
    <a-modal
      :title="modalTitle"
      :visible="modalVisible"
      :confirmLoading="modalLoading"
      @ok="handleModalOk"
      @cancel="modalVisible = false"
      width="600px"
    >
      <a-form :form="jobForm" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item label="任务名称">
          <a-input v-decorator="['name', { rules: [{ required: true, message: '请输入任务名称' }] }]" />
        </a-form-item>
        <a-form-item label="数据源类型">
          <a-select
            v-decorator="['source_type', { initialValue: 'polymarket', rules: [{ required: true }] }]"
            :disabled="!!editJobId"
          >
            <a-select-option value="polymarket">Polymarket</a-select-option>
            <a-select-option value="crypto">Crypto</a-select-option>
            <a-select-option value="stock">Stock</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="执行器类型">
          <a-input
            v-decorator="['executor_type', { initialValue: 'polymarket' }]"
            placeholder="默认与数据源类型相同"
          />
        </a-form-item>
        <a-form-item label="执行间隔">
          <a-input-number
            v-decorator="['interval_minutes', { initialValue: 30, rules: [{ required: true }] }]"
            :min="1"
            :max="10080"
            style="width: 100%"
          />
          <span style="margin-left: 8px; color: #999">分钟</span>
        </a-form-item>
        <a-form-item label="启用状态">
          <a-switch v-decorator="['enabled', { valuePropName: 'checked', initialValue: true }]" />
        </a-form-item>
        <a-form-item label="高级配置 (JSON)">
          <a-textarea
            v-decorator="['config_json', { initialValue: '{}' }]"
            :rows="4"
            placeholder="{&quot;limit&quot;: 500}"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 手动执行确认 -->
    <a-modal
      title="手动执行同步"
      :visible="runVisible"
      :confirmLoading="runLoading"
      @ok="confirmRun"
      @cancel="runVisible = false"
    >
      <a-form :form="runForm" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item label="执行类型">
          <a-radio-group v-decorator="['run_type', { initialValue: 'incremental' }]">
            <a-radio value="incremental">增量同步</a-radio>
            <a-radio value="full">全量同步</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="数量上限">
          <a-input-number
            v-decorator="['limit', { initialValue: 3000 }]"
            :min="10"
            :max="100000"
            style="width: 100%"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script>
import {
  createSyncJob,
  updateSyncJob,
  deleteSyncJob,
  runSyncJob,
  getSyncRuns,
  getSyncStatus
} from '@/api/sync'

export default {
  name: 'SyncTaskTab',
  data () {
    return {
      statusLoading: false,
      modalLoading: false,
      runLoading: false,
      modalVisible: false,
      runVisible: false,
      filterSourceType: undefined,
      jobs: [],
      workers: [],
      expandedRowKeys: [],
      runMap: {},
      runLoadingMap: {},
      editJobId: null,
      currentRunJob: null,
      jobForm: this.$form.createForm(this),
      runForm: this.$form.createForm(this),
      statusBadge: {
        success: 'success',
        failed: 'error',
        running: 'processing'
      },
      statusText: {
        success: '成功',
        failed: '失败',
        running: '运行中'
      },
      jobColumns: [
        { title: 'ID', dataIndex: 'id', width: 60 },
        { title: '名称', dataIndex: 'name' },
        { title: '数据源', dataIndex: 'source_type', scopedSlots: { customRender: 'source_type' }, width: 120 },
        { title: '间隔(分钟)', dataIndex: 'interval_minutes', width: 100 },
        { title: '状态', dataIndex: 'enabled', scopedSlots: { customRender: 'enabled' }, width: 80 },
        { title: '上次执行', dataIndex: 'last_run_at', scopedSlots: { customRender: 'last_run_at' }, width: 160 },
        { title: '执行结果', dataIndex: 'last_status', scopedSlots: { customRender: 'last_status' }, width: 100 },
        { title: '操作', dataIndex: 'action', scopedSlots: { customRender: 'action' }, width: 240 }
      ],
      runColumns: [
        { title: 'ID', dataIndex: 'id', width: 50 },
        { title: '类型', dataIndex: 'run_type', scopedSlots: { customRender: 'run_type' }, width: 80 },
        { title: '状态', dataIndex: 'status', scopedSlots: { customRender: 'status' }, width: 80 },
        { title: '数据量', scopedSlots: { customRender: 'items' }, width: 130 },
        { title: '时间', scopedSlots: { customRender: 'time' }, width: 220 },
        { title: '错误', dataIndex: 'error_message', ellipsis: true }
      ]
    }
  },
  computed: {
    filteredJobs () {
      if (!this.filterSourceType) return this.jobs
      return this.jobs.filter(j => j.source_type === this.filterSourceType)
    },
    runningWorkers () {
      return this.workers.filter(w => w.running).length
    },
    enabledJobs () {
      return this.jobs.filter(j => j.enabled).length
    },
    failedJobs () {
      return this.jobs.filter(j => j.last_status === 'failed').length
    },
    modalTitle () {
      return this.editJobId ? '编辑同步任务' : '新增同步任务'
    }
  },
  created () {
    this.loadStatus()
  },
  methods: {
    loadStatus () {
      this.statusLoading = true
      getSyncStatus().then(res => {
        if (res.code === 1) {
          this.jobs = res.data.jobs || []
          this.workers = res.data.workers || []
        }
      }).finally(() => {
        this.statusLoading = false
      })
    },
    handleFilterChange () {
      this.expandedRowKeys = []
    },
    handleExpand (expanded, record) {
      if (expanded) {
        this.expandedRowKeys = [record.id]
        this.loadRuns(record.id)
      } else {
        this.expandedRowKeys = []
      }
    },
    loadRuns (jobId) {
      this.$set(this.runLoadingMap, jobId, true)
      getSyncRuns({ job_id: jobId, page_size: 20 }).then(res => {
        if (res.code === 1) {
          this.$set(this.runMap, jobId, res.data.items || [])
        }
      }).finally(() => {
        this.$set(this.runLoadingMap, jobId, false)
      })
    },
    handleAddJob () {
      this.editJobId = null
      this.modalVisible = true
      this.$nextTick(() => {
        this.jobForm.resetFields()
        this.jobForm.setFieldsValue({
          source_type: 'polymarket',
          executor_type: 'polymarket',
          interval_minutes: 30,
          enabled: true,
          config_json: '{}'
        })
      })
    },
    handleEdit (record) {
      this.editJobId = record.id
      this.modalVisible = true
      this.$nextTick(() => {
        this.jobForm.setFieldsValue({
          name: record.name,
          source_type: record.source_type,
          executor_type: record.executor_type || record.source_type,
          interval_minutes: record.interval_minutes,
          enabled: record.enabled,
          config_json: record.config_json || '{}'
        })
      })
    },
    handleModalOk () {
      this.jobForm.validateFields((err, values) => {
        if (err) return
        this.modalLoading = true

        const payload = {
          name: values.name,
          source_type: values.source_type,
          executor_type: values.executor_type || values.source_type,
          interval_minutes: values.interval_minutes,
          enabled: values.enabled,
          config_json: values.config_json
        }

        const promise = this.editJobId
          ? updateSyncJob(this.editJobId, payload)
          : createSyncJob(payload)

        promise.then(res => {
          if (res.code === 1) {
            this.$message.success(this.editJobId ? '更新成功' : '创建成功')
            this.modalVisible = false
            this.loadStatus()
          } else {
            this.$message.error(res.msg || '操作失败')
          }
        }).catch(err => {
          this.$message.error(err.message || '请求失败')
        }).finally(() => {
          this.modalLoading = false
        })
      })
    },
    handleDelete (id) {
      deleteSyncJob(id).then(res => {
        if (res.code === 1) {
          this.$message.success('删除成功')
          this.loadStatus()
        } else {
          this.$message.error(res.msg || '删除失败')
        }
      })
    },
    handleRun (record, defaultType) {
      this.currentRunJob = record
      this.runVisible = true
      this.$nextTick(() => {
        this.runForm.setFieldsValue({
          run_type: defaultType,
          limit: defaultType === 'full' ? 3000 : 500
        })
      })
    },
    confirmRun () {
      this.runForm.validateFields((err, values) => {
        if (err) return
        this.runLoading = true
        const payload = { run_type: values.run_type }
        if (values.limit) payload.limit = values.limit

        runSyncJob(this.currentRunJob.id, payload).then(res => {
          if (res.code === 1) {
            this.$message.success('同步任务已触发，请在历史记录中查看结果')
            this.runVisible = false
            setTimeout(() => {
              if (this.expandedRowKeys.includes(this.currentRunJob.id)) {
                this.loadRuns(this.currentRunJob.id)
              }
            }, 2000)
          } else {
            this.$message.error(res.msg || '触发失败')
          }
        }).catch(err => {
          this.$message.error(err.message || '请求失败')
        }).finally(() => {
          this.runLoading = false
        })
      })
    },
    formatTime (iso) {
      if (!iso) return null
      const d = new Date(iso)
      if (isNaN(d.getTime())) return iso
      return d.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      }).replace(/\//g, '-')
    }
  }
}
</script>

<style lang="less" scoped>
.sync-task-tab {
  .status-cards {
    margin-bottom: 16px;
  }

  .table-operator {
    margin-bottom: 16px;
  }

  .expanded-content {
    padding: 8px 24px;
    background: #fafafa;
  }
}
</style>
