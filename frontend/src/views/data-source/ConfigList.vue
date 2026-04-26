<template>
  <div class="config-list">
    <div class="table-operator">
      <a-button type="primary" icon="plus" @click="handleAdd">新增数据源</a-button>
      <a-input-search
        v-model="searchText"
        placeholder="搜索代码或名称"
        style="width: 250px; margin-left: 16px"
        @search="handleSearch"
      />
      <a-select
        v-model="filterLayer"
        placeholder="层级筛选"
        style="width: 150px; margin-left: 8px"
        allowClear
        @change="handleSearch"
      >
        <a-select-option value="data_source">数据源</a-select-option>
        <a-select-option value="data_provider">数据提供商</a-select-option>
        <a-select-option value="fundamental">基本面</a-select-option>
        <a-select-option value="sentiment">情绪</a-select-option>
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
      <span slot="enabled" slot-scope="text">
        <a-badge :status="text ? 'success' : 'default'" :text="text ? '启用' : '禁用'" />
      </span>
      <span slot="market_categories" slot-scope="text">
        <a-tag v-for="cat in (text || [])" :key="cat" color="blue">{{ cat }}</a-tag>
      </span>
      <span slot="action" slot-scope="text, record">
        <template>
          <a @click="handleTest(record)">测试</a>
          <a-divider type="vertical" />
          <a @click="handleEdit(record)">编辑</a>
          <a-divider type="vertical" />
          <a-popconfirm title="确定删除此数据源？关联的密钥和数据集也会被删除" @confirm="handleDelete(record.id)">
            <a style="color: red">删除</a>
          </a-popconfirm>
        </template>
      </span>
    </a-table>

    <a-modal
      :title="modalTitle"
      :visible="visible"
      :confirmLoading="confirmLoading"
      width="700px"
      @ok="handleOk"
      @cancel="handleCancel"
    >
      <a-form :form="form" :label-col="{ span: 5 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="源代码">
          <a-input
            v-decorator="['source_code', { rules: [{ required: true, message: '请输入源代码' }] }]"
            :disabled="!!editId"
            placeholder="如: crypto_ccxt"
          />
        </a-form-item>
        <a-form-item label="显示名称">
          <a-input v-decorator="['source_name', { rules: [{ required: true, message: '请输入名称' }] }]" />
        </a-form-item>
        <a-form-item label="层级">
          <a-select v-decorator="['layer', { initialValue: 'data_provider', rules: [{ required: true }] }]">
            <a-select-option value="data_source">数据源</a-select-option>
            <a-select-option value="data_provider">数据提供商</a-select-option>
            <a-select-option value="fundamental">基本面</a-select-option>
            <a-select-option value="sentiment">情绪</a-select-option>
            <a-select-option value="collector">采集器</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="市场类别">
          <a-select
            v-decorator="['market_categories', { initialValue: [] }]"
            mode="multiple"
            placeholder="选择市场类别"
          >
            <a-select-option value="Crypto">加密货币</a-select-option>
            <a-select-option value="USStock">美股</a-select-option>
            <a-select-option value="CNStock">A股</a-select-option>
            <a-select-option value="HKStock">港股</a-select-option>
            <a-select-option value="Forex">外汇</a-select-option>
            <a-select-option value="Futures">期货</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="启用状态">
          <a-switch v-decorator="['enabled', { valuePropName: 'checked', initialValue: true }]" />
        </a-form-item>
        <a-form-item label="负载均衡策略">
          <a-select v-decorator="['load_balance_strategy', { initialValue: 'round_robin' }]">
            <a-select-option value="round_robin">轮询</a-select-option>
            <a-select-option value="weighted">加权</a-select-option>
            <a-select-option value="health_first">健康优先</a-select-option>
            <a-select-option value="random">随机</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="配置参数 (JSON)">
          <a-textarea
            v-decorator="['config_json_str', { initialValue: '{}' }]"
            :rows="6"
            placeholder='{"base_url": "https://api.example.com", "timeout_sec": 10}'
          />
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea v-decorator="['notes']" :rows="2" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      title="连接测试结果"
      :visible="testVisible"
      :footer="null"
      @cancel="testVisible = false"
    >
      <a-result
        :status="testResult.success ? 'success' : 'error'"
        :title="testResult.success ? '连接成功' : '连接失败'"
        :sub-title="testResult.message"
      />
    </a-modal>
  </div>
</template>

<script>
import { getConfigs, saveConfig, deleteConfig, testConfig } from '@/api/dataSource'

export default {
  name: 'ConfigList',
  data () {
    return {
      loading: false,
      data: [],
      searchText: '',
      filterLayer: undefined,
      pagination: { current: 1, pageSize: 10, total: 0 },
      visible: false,
      confirmLoading: false,
      modalTitle: '',
      editId: null,
      testVisible: false,
      testResult: { success: false, message: '' },
      form: this.$form.createForm(this),
      columns: [
        { title: 'ID', dataIndex: 'id', width: 60 },
        { title: '源代码', dataIndex: 'source_code' },
        { title: '名称', dataIndex: 'source_name' },
        { title: '层级', dataIndex: 'layer' },
        { title: '市场类别', dataIndex: 'market_categories', scopedSlots: { customRender: 'market_categories' } },
        { title: '状态', dataIndex: 'enabled', scopedSlots: { customRender: 'enabled' }, width: 80 },
        { title: '负载均衡', dataIndex: 'load_balance_strategy', width: 100 },
        { title: '操作', dataIndex: 'action', scopedSlots: { customRender: 'action' }, width: 180 }
      ]
    }
  },
  created () {
    this.loadData()
  },
  methods: {
    loadData () {
      this.loading = true
      getConfigs({
        search: this.searchText || undefined,
        layer: this.filterLayer || undefined,
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
    handleSearch () {
      this.pagination.current = 1
      this.loadData()
    },
    handleTableChange (pagination) {
      this.pagination = pagination
      this.loadData()
    },
    handleAdd () {
      this.modalTitle = '新增数据源'
      this.editId = null
      this.visible = true
      this.$nextTick(() => {
        this.form.resetFields()
        this.form.setFieldsValue({ config_json_str: '{}' })
      })
    },
    handleEdit (record) {
      this.modalTitle = '编辑数据源'
      this.editId = record.id
      this.visible = true
      this.$nextTick(() => {
        this.form.setFieldsValue({
          source_code: record.source_code,
          source_name: record.source_name,
          layer: record.layer,
          market_categories: record.market_categories || [],
          enabled: record.enabled,
          load_balance_strategy: record.load_balance_strategy,
          config_json_str: JSON.stringify(record.config_json || {}, null, 2),
          notes: record.notes
        })
      })
    },
    handleOk () {
      this.form.validateFields((err, values) => {
        if (err) return
        this.confirmLoading = true

        let configJson = {}
        try {
          configJson = JSON.parse(values.config_json_str || '{}')
        } catch (e) {
          this.$message.error('配置参数 JSON 格式错误')
          this.confirmLoading = false
          return
        }

        const payload = {
          id: this.editId,
          source_code: values.source_code,
          source_name: values.source_name,
          layer: values.layer,
          market_categories: values.market_categories,
          enabled: values.enabled,
          load_balance_strategy: values.load_balance_strategy,
          config_json: configJson,
          notes: values.notes
        }

        saveConfig(payload).then(res => {
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
      deleteConfig(id).then(res => {
        if (res.code === 1) {
          this.$message.success('删除成功')
          this.loadData()
        } else {
          this.$message.error(res.msg || '删除失败')
        }
      })
    },
    handleTest (record) {
      testConfig(record.id).then(res => {
        this.testResult = {
          success: res.code === 1,
          message: res.msg || (res.code === 1 ? '连接正常' : '连接失败')
        }
        this.testVisible = true
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
