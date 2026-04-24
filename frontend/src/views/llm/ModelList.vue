<template>
  <div class="model-list">
    <div class="table-operator">
      <a-button type="primary" icon="plus" @click="handleAdd">{{ $t('llm.addModel') }}</a-button>
    </div>

    <a-table
      ref="table"
      size="default"
      rowKey="id"
      :columns="columns"
      :dataSource="data"
      :loading="loading"
    >
      <span slot="strategy" slot-scope="text">
        {{ $t(`llm.strategy.${text}`) || text }}
      </span>
      <span slot="action" slot-scope="text, record">
        <template>
          <a @click="handleEdit(record)">{{ $t('common.edit') }}</a>
          <a-divider type="vertical" />
          <a-popconfirm title="Delete?" @confirm="handleDelete(record.id)">
            <a style="color: red">{{ $t('common.delete') }}</a>
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
        <a-form-item :label="$t('llm.provider')">
          <a-select v-decorator="['provider_id', { rules: [{ required: true }] }]">
            <a-select-option v-for="p in providers" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="$t('llm.modelName')">
          <a-input v-decorator="['model_name', { rules: [{ required: true }] }]" placeholder="e.g. gpt-4o" />
        </a-form-item>
        <a-form-item label="Display Name">
          <a-input v-decorator="['display_name', { rules: [{ required: true }] }]" />
        </a-form-item>
        <a-form-item :label="$t('llm.strategy')">
          <a-select v-decorator="['lb_strategy', { initialValue: 'round_robin', rules: [{ required: true }] }]">
            <a-select-option value="round_robin">{{ $t('llm.strategy.round_robin') }}</a-select-option>
            <a-select-option value="weighted_round_robin">{{ $t('llm.strategy.weighted_round_robin') }}</a-select-option>
            <a-select-option value="random">{{ $t('llm.strategy.random') }}</a-select-option>
            <a-select-option value="least_connections">{{ $t('llm.strategy.least_connections') }}</a-select-option>
            <a-select-option value="consistent_hash">{{ $t('llm.strategy.consistent_hash') }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Max Retries">
          <a-input-number v-decorator="['retries', { initialValue: 3 }]" :min="0" :max="10" />
        </a-form-item>
        <a-form-item label="Timeout (s)">
          <a-input-number v-decorator="['timeout', { initialValue: 60 }]" :min="1" :max="300" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script>
import { getModels, saveModel, deleteModel, getProviders } from '@/api/llm'

export default {
  name: 'ModelList',
  data () {
    return {
      loading: false,
      data: [],
      providers: [],
      visible: false,
      confirmLoading: false,
      modalTitle: '',
      editId: null,
      form: this.$form.createForm(this),
      columns: [
        { title: 'ID', dataIndex: 'id' },
        { title: this.$t('llm.provider'), dataIndex: 'provider_name' },
        { title: this.$t('llm.modelName'), dataIndex: 'model_name' },
        { title: 'Display Name', dataIndex: 'display_name' },
        { title: this.$t('llm.strategy'), dataIndex: 'lb_strategy', scopedSlots: { customRender: 'strategy' } },
        { title: this.$t('llm.actions'), dataIndex: 'action', scopedSlots: { customRender: 'action' } }
      ]
    }
  },
  created () {
    this.loadData()
    this.loadProviders()
  },
  methods: {
    loadData () {
      this.loading = true
      getModels().then(res => {
        this.data = res.data
      }).finally(() => {
        this.loading = false
      })
    },
    loadProviders () {
      getProviders().then(res => {
        this.providers = res.data
      })
    },
    handleAdd () {
      this.modalTitle = this.$t('llm.addModel')
      this.editId = null
      this.visible = true
      this.$nextTick(() => {
        this.form.resetFields()
      })
    },
    handleEdit (record) {
      this.modalTitle = this.$t('common.edit')
      this.editId = record.id
      this.visible = true
      this.$nextTick(() => {
        this.form.setFieldsValue({
          provider_id: record.provider_id,
          model_name: record.model_name,
          display_name: record.display_name,
          lb_strategy: record.lb_strategy,
          retries: record.retries,
          timeout: record.timeout
        })
      })
    },
    handleOk () {
      this.form.validateFields((err, values) => {
        if (!err) {
          this.confirmLoading = true
          const params = { ...values }
          if (this.editId) params.id = this.editId
          saveModel(params).then(() => {
            this.$message.success('Success')
            this.visible = false
            this.loadData()
          }).finally(() => {
            this.confirmLoading = false
          })
        }
      })
    },
    handleCancel () {
      this.visible = false
    },
    handleDelete (id) {
      deleteModel(id).then(() => {
        this.$message.success('Deleted')
        this.loadData()
      })
    }
  }
}
</script>
