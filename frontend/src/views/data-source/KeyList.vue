<template>
  <div class="key-list">
    <div class="table-operator">
      <a-button type="primary" icon="plus" @click="handleAdd">新增密钥</a-button>
      <a-select
        v-model="filterStatus"
        placeholder="状态筛选"
        style="width: 120px; margin-left: 8px"
        allowClear
        @change="handleSearch"
      >
        <a-select-option value="active">正常</a-select-option>
        <a-select-option value="disabled">禁用</a-select-option>
        <a-select-option value="error">错误</a-select-option>
      </a-select>
    </div>

    <a-table
      ref="table"
      size="default"
      rowKey="id"
      :columns="columns"
      :dataSource="data"
      :loading="loading"
      :pagination="pagination"
      @change="handleTableChange"
    >
      <span slot="key_type" slot-scope="text">
        <a-tag :color="text === 'public' ? 'green' : 'orange'">{{ text === 'public' ? '公共' : '私有' }}</a-tag>
      </span>
      <span slot="status" slot-scope="text">
        <a-badge
          :status="text === 'active' ? 'success' : text === 'error' ? 'error' : 'default'"
          :text="statusMap[text] || text"
        />
      </span>
      <span slot="usage" slot-scope="text, record">
        {{ record.current_daily_calls }}/{{ record.daily_call_limit || '∞' }}
      </span>
      <span slot="action" slot-scope="text, record">
        <template>
          <a @click="handleEdit(record)">编辑</a>
          <a-divider type="vertical" />
          <a-popconfirm title="确定删除此密钥？" @confirm="handleDelete(record.id)">
            <a style="color: red">删除</a>
          </a-popconfirm>
        </template>
      </span>
    </a-table>

    <a-modal
      :title="modalTitle"
      :visible="visible"
      :confirmLoading="confirmLoading"
      @ok="handleOk"
      @cancel="handleCancel"
    >
      <a-form :form="form" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item label="数据源">
          <a-select
            v-decorator="['source_config_id', { rules: [{ required: true, message: '请选择数据源' }] }]"
            placeholder="选择关联的数据源"
          >
            <a-select-option v-for="cfg in configOptions" :key="cfg.id" :value="cfg.id">
              {{ cfg.source_name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="密钥类型">
          <a-select v-decorator="['key_type', { initialValue: 'public', rules: [{ required: true }] }]">
            <a-select-option value="public">公共密钥</a-select-option>
            <a-select-option value="private">私有密钥</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="密钥别名">
          <a-input v-decorator="['key_alias']" placeholder="如: TwelveData Key #1" />
        </a-form-item>
        <a-form-item label="密钥值">
          <a-input-password
            v-decorator="['key_value', { rules: [{ required: !editId, message: '请输入密钥值' }] }]"
            placeholder="输入 API 密钥（编辑时留空表示不修改）"
          />
        </a-form-item>
        <a-form-item label="状态">
          <a-select v-decorator="['status', { initialValue: 'active' }]">
            <a-select-option value="active">正常</a-select-option>
            <a-select-option value="disabled">禁用</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="权重">
          <a-input-number v-decorator="['weight', { initialValue: 1 }]" :min="1" :max="100" />
        </a-form-item>
        <a-form-item label="日调用限制">
          <a-input-number
            v-decorator="['daily_call_limit', { initialValue: 0 }]"
            :min="0"
            placeholder="0 表示无限制"
          />
        </a-form-item>
        <a-form-item label="最大连续错误">
          <a-input-number v-decorator="['max_consecutive_errors', { initialValue: 5 }]" :min="1" :max="50" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script>
import { getKeys, saveKey, deleteKey, getConfigs } from '@/api/dataSource'

export default {
  name: 'KeyList',
  data () {
    return {
      loading: false,
      data: [],
      configOptions: [],
      filterStatus: undefined,
      pagination: { current: 1, pageSize: 10, total: 0 },
      visible: false,
      confirmLoading: false,
      modalTitle: '',
      editId: null,
      form: this.$form.createForm(this),
      statusMap: { active: '正常', disabled: '禁用', error: '错误', rate_limited: '限速', expired: '过期' },
      columns: [
        { title: 'ID', dataIndex: 'id', width: 60 },
        { title: '数据源ID', dataIndex: 'source_config_id', width: 80 },
        { title: '类型', dataIndex: 'key_type', scopedSlots: { customRender: 'key_type' }, width: 90 },
        { title: '别名', dataIndex: 'key_alias' },
        { title: '密钥提示', dataIndex: 'key_hint' },
        { title: '状态', dataIndex: 'status', scopedSlots: { customRender: 'status' }, width: 90 },
        { title: '权重', dataIndex: 'weight', width: 70 },
        { title: '日调用', dataIndex: 'usage', scopedSlots: { customRender: 'usage' }, width: 100 },
        { title: '连续错误', dataIndex: 'consecutive_errors', width: 90 },
        { title: '总调用', dataIndex: 'total_calls', width: 90 },
        { title: '操作', dataIndex: 'action', scopedSlots: { customRender: 'action' }, width: 140 }
      ]
    }
  },
  created () {
    this.loadData()
    this.loadConfigs()
  },
  methods: {
    loadData () {
      this.loading = true
      getKeys({
        status: this.filterStatus || undefined,
        page: this.pagination.current,
        page_size: this.pagination.pageSize
      }).then(res => {
        if (res.code === 1) {
          this.data = res.data.items
          this.pagination.total = res.data.total
        }
      }).finally(() => {
        this.loading = false
      })
    },
    loadConfigs () {
      getConfigs({ page_size: 100 }).then(res => {
        if (res.code === 1) {
          this.configOptions = res.data.items
        }
      })
    },
    handleSearch () {
      this.pagination.current = 1
      this.loadData()
    },
    handleTableChange (pagination) {
      this.pagination = pagination
      this.loadData()
    },
    handleAdd () {
      this.modalTitle = '新增密钥'
      this.editId = null
      this.visible = true
      this.$nextTick(() => {
        this.form.resetFields()
      })
    },
    handleEdit (record) {
      this.modalTitle = '编辑密钥'
      this.editId = record.id
      this.visible = true
      this.$nextTick(() => {
        this.form.setFieldsValue({
          source_config_id: record.source_config_id,
          key_type: record.key_type,
          key_alias: record.key_alias,
          status: record.status,
          weight: record.weight,
          daily_call_limit: record.daily_call_limit,
          max_consecutive_errors: record.max_consecutive_errors
        })
      })
    },
    handleOk () {
      this.form.validateFields((err, values) => {
        if (err) return
        this.confirmLoading = true

        const payload = {
          id: this.editId,
          source_config_id: values.source_config_id,
          key_type: values.key_type,
          key_alias: values.key_alias,
          key_value: values.key_value,
          status: values.status,
          weight: values.weight,
          daily_call_limit: values.daily_call_limit,
          max_consecutive_errors: values.max_consecutive_errors
        }

        // 编辑时如果密钥值为空，则不提交
        if (this.editId && !payload.key_value) {
          delete payload.key_value
        }

        saveKey(payload).then(res => {
          if (res.code === 1) {
            this.$message.success(this.editId ? '更新成功' : '创建成功')
            this.visible = false
            this.loadData()
          } else {
            this.$message.error(res.msg || '操作失败')
          }
        }).finally(() => {
          this.confirmLoading = false
        })
      })
    },
    handleCancel () {
      this.visible = false
    },
    handleDelete (id) {
      deleteKey(id).then(res => {
        if (res.code === 1) {
          this.$message.success('删除成功')
          this.loadData()
        } else {
          this.$message.error(res.msg || '删除失败')
        }
      })
    }
  }
}
</script>

<style lang="less" scoped>
.table-operator {
  margin-bottom: 16px;
}
</style>
