<template>
  <div class="provider-list">
    <div class="table-operator">
      <a-button type="primary" icon="plus" @click="handleAdd">{{ $t('llm.addProvider') }}</a-button>
    </div>

    <a-table
      ref="table"
      size="default"
      rowKey="id"
      :columns="columns"
      :dataSource="data"
      :loading="loading"
    >
      <span slot="status" slot-scope="text">
        <a-badge :status="text === 1 ? 'success' : 'error'" :text="text === 1 ? $t('llm.status.active') : $t('llm.status.disabled')" />
      </span>
      <span slot="apiType" slot-scope="text">
        <a-tag color="blue">{{ getApiTypeLabel(text) }}</a-tag>
      </span>
      <span slot="action" slot-scope="text, record">
        <template>
          <a @click="handleEdit(record)">{{ $t('common.edit') }}</a>
          <a-divider type="vertical" />
          <a-popconfirm :title="$t('common.confirmDelete') || 'Confirm Delete?'" @confirm="handleDelete(record.id)">
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
        <a-form-item :label="$t('llm.providerName')">
          <a-input v-decorator="['name', { rules: [{ required: true, message: 'Please enter name' }] }]" />
        </a-form-item>
        <a-form-item :label="$t('llm.baseUrl')">
          <a-input v-decorator="['base_url', { rules: [{ required: true, message: 'Please enter base url' }] }]" />
        </a-form-item>
        <a-form-item label="API Type">
          <a-select v-decorator="['api_type', { initialValue: 'openai', rules: [{ required: true }] }]">
            <a-select-option value="openai">OpenAI</a-select-option>
            <a-select-option value="openrouter">OpenRouter</a-select-option>
            <a-select-option value="openai-compatible">OpenAI Compatible</a-select-option>
            <a-select-option value="google">Google Gemini</a-select-option>
            <a-select-option value="deepseek">DeepSeek</a-select-option>
            <a-select-option value="grok">xAI Grok</a-select-option>
            <a-select-option value="ollama">Ollama</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="$t('llm.status')">
          <a-switch v-decorator="['status', { valuePropName: 'checked', initialValue: true }]" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script>
import { getProviders, saveProvider, deleteProvider } from '@/api/llm'

export default {
  name: 'ProviderList',
  data () {
    return {
      loading: false,
      data: [],
      visible: false,
      confirmLoading: false,
      modalTitle: '',
      editId: null,
      form: this.$form.createForm(this),
      columns: [
        { title: 'ID', dataIndex: 'id' },
        { title: this.$t('llm.providerName'), dataIndex: 'name' },
        { title: this.$t('llm.baseUrl'), dataIndex: 'base_url' },
        { title: 'API Type', dataIndex: 'api_type', scopedSlots: { customRender: 'apiType' } },
        { title: this.$t('llm.status'), dataIndex: 'status', scopedSlots: { customRender: 'status' } },
        { title: this.$t('llm.actions'), dataIndex: 'action', scopedSlots: { customRender: 'action' } }
      ]
    }
  },
  created () {
    this.loadData()
  },
  methods: {
    getApiTypeLabel (type) {
      const map = {
        'openai': 'OpenAI',
        'openrouter': 'OpenRouter',
        'openai-compatible': 'OpenAI Compatible',
        'google': 'Google Gemini',
        'deepseek': 'DeepSeek',
        'grok': 'xAI Grok',
        'ollama': 'Ollama'
      }
      return map[type] || type
    },
    loadData () {
      this.loading = true
      getProviders().then(res => {
        this.data = res.data
      }).finally(() => {
        this.loading = false
      })
    },
    handleAdd () {
      this.modalTitle = this.$t('llm.addProvider')
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
          name: record.name,
          base_url: record.base_url,
          api_type: record.api_type,
          status: record.status === 1
        })
      })
    },
    handleOk () {
      this.form.validateFields((err, values) => {
        if (!err) {
          this.confirmLoading = true
          const params = {
            ...values,
            status: values.status ? 1 : 0
          }
          if (this.editId) params.id = this.editId
          saveProvider(params).then(() => {
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
      deleteProvider(id).then(() => {
        this.$message.success('Deleted')
        this.loadData()
      })
    }
  }
}
</script>

<style scoped>
.table-operator {
  margin-bottom: 18px;
}
</style>
