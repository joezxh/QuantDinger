<template>
  <div class="dataset-list">
    <div class="table-operator">
      <a-button type="primary" icon="plus" @click="handleAdd">新增数据集</a-button>
      <a-select
        v-model="filterSourceId"
        placeholder="数据源筛选"
        style="width: 200px; margin-left: 8px"
        allowClear
        @change="handleSearch"
      >
        <a-select-option v-for="cfg in configOptions" :key="cfg.id" :value="cfg.id">
          {{ cfg.source_name }}
        </a-select-option>
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
      <span slot="action" slot-scope="text, record">
        <template>
          <a @click="handleEdit(record)">编辑</a>
          <a-divider type="vertical" />
          <a-popconfirm title="确定删除此数据集？" @confirm="handleDelete(record.id)">
            <a style="color: red">删除</a>
          </a-popconfirm>
        </template>
      </span>
    </a-table>

    <a-modal
      :title="modalTitle"
      :visible="visible"
      :confirmLoading="confirmLoading"
      width="750px"
      @ok="handleOk"
      @cancel="handleCancel"
    >
      <a-form :form="form" :label-col="{ span: 5 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="所属数据源">
          <a-select v-decorator="['source_id', { rules: [{ required: true, message: '请选择数据源' }] }]">
            <a-select-option v-for="cfg in configOptions" :key="cfg.id" :value="cfg.id">
              {{ cfg.source_name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="数据集代码">
          <a-input
            v-decorator="['dataset_code', { rules: [{ required: true, message: '请输入数据集代码' }] }]"
            :disabled="!!editId"
            placeholder="如: crypto_klines"
          />
        </a-form-item>
        <a-form-item label="显示名称">
          <a-input v-decorator="['dataset_name', { rules: [{ required: true, message: '请输入名称' }] }]" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-decorator="['description']" :rows="2" />
        </a-form-item>
        <a-form-item label="函数名">
          <a-input v-decorator="['function_name']" placeholder="如: get_kline()" />
        </a-form-item>
        <a-form-item label="返回类型">
          <a-select v-decorator="['return_type', { initialValue: 'list[dict]' }]">
            <a-select-option value="list[dict]">list[dict]</a-select-option>
            <a-select-option value="dict">dict</a-select-option>
            <a-select-option value="list">list</a-select-option>
            <a-select-option value="str">str</a-select-option>
            <a-select-option value="scalar">scalar</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="字段 Schema (JSON)">
          <a-textarea
            v-decorator="['fields_schema_str', { initialValue: '[]' }]"
            :rows="6"
            placeholder='[{"name": "time", "type": "int", "description": "时间戳"}]'
          />
        </a-form-item>
        <a-form-item label="样本输出 (JSON)">
          <a-textarea
            v-decorator="['sample_output_str', { initialValue: '{}' }]"
            :rows="4"
          />
        </a-form-item>
        <a-form-item label="覆盖范围">
          <a-textarea v-decorator="['coverage_text']" :rows="2" placeholder="描述数据覆盖范围" />
        </a-form-item>
        <a-form-item label="源文件引用">
          <a-input v-decorator="['source_file_ref']" placeholder="如: app/data_providers/crypto.py" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script>
import { getDatasets, saveDataset, deleteDataset, getConfigs } from '@/api/dataSource'

export default {
  name: 'DatasetList',
  data () {
    return {
      loading: false,
      data: [],
      configOptions: [],
      filterSourceId: undefined,
      pagination: { current: 1, pageSize: 10, total: 0 },
      visible: false,
      confirmLoading: false,
      modalTitle: '',
      editId: null,
      form: this.$form.createForm(this),
      columns: [
        { title: 'ID', dataIndex: 'id', width: 60 },
        { title: '数据集代码', dataIndex: 'dataset_code' },
        { title: '名称', dataIndex: 'dataset_name' },
        { title: '返回类型', dataIndex: 'return_type', width: 100 },
        { title: '函数', dataIndex: 'function_name' },
        { title: '源文件', dataIndex: 'source_file_ref' },
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
      getDatasets({
        source_id: this.filterSourceId || undefined,
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
      this.modalTitle = '新增数据集'
      this.editId = null
      this.visible = true
      this.$nextTick(() => {
        this.form.resetFields()
        this.form.setFieldsValue({
          fields_schema_str: '[]',
          sample_output_str: '{}',
          return_type: 'list[dict]'
        })
      })
    },
    handleEdit (record) {
      this.modalTitle = '编辑数据集'
      this.editId = record.id
      this.visible = true
      this.$nextTick(() => {
        this.form.setFieldsValue({
          source_id: record.source_id,
          dataset_code: record.dataset_code,
          dataset_name: record.dataset_name,
          description: record.description,
          function_name: record.function_name,
          return_type: record.return_type,
          fields_schema_str: JSON.stringify(record.fields_schema || [], null, 2),
          sample_output_str: JSON.stringify(record.sample_output || {}, null, 2),
          coverage_text: record.coverage_text,
          source_file_ref: record.source_file_ref
        })
      })
    },
    handleOk () {
      this.form.validateFields((err, values) => {
        if (err) return
        this.confirmLoading = true

        let fieldsSchema = []
        let sampleOutput = {}
        try {
          fieldsSchema = JSON.parse(values.fields_schema_str || '[]')
          sampleOutput = JSON.parse(values.sample_output_str || '{}')
        } catch (e) {
          this.$message.error('JSON 格式错误')
          this.confirmLoading = false
          return
        }

        const payload = {
          id: this.editId,
          source_id: values.source_id,
          dataset_code: values.dataset_code,
          dataset_name: values.dataset_name,
          description: values.description,
          function_name: values.function_name,
          return_type: values.return_type,
          fields_schema: fieldsSchema,
          sample_output: sampleOutput,
          coverage_text: values.coverage_text,
          source_file_ref: values.source_file_ref
        }

        saveDataset(payload).then(res => {
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
      deleteDataset(id).then(res => {
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
