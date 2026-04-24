<template>
  <div class="key-list">
    <div class="table-operator">
      <a-button type="primary" icon="plus" @click="handleAdd">{{ $t('llm.addKey') }}</a-button>
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
        <a-tag v-if="text === 1" color="green">{{ $t('llm.status.active') }}</a-tag>
        <a-tag v-else-if="text === 2" color="orange">{{ $t('llm.status.broken') }}</a-tag>
        <a-tag v-else color="red">{{ $t('llm.status.disabled') }}</a-tag>
      </span>
      <span slot="apiKey" slot-scope="text">
        <code>{{ text.substring(0, 8) }}...{{ text.substring(text.length - 4) }}</code>
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
        <a-form-item label="Name/Remark">
          <a-input v-decorator="['name', { rules: [{ required: true }] }]" />
        </a-form-item>
        <a-form-item :label="$t('llm.apiKey')">
          <a-input-password v-decorator="['api_key', { rules: [{ required: !editId }] }]" :placeholder="editId ? 'Leave blank to keep current' : 'Enter API Key'" />
        </a-form-item>
        <a-form-item :label="$t('llm.weight')">
          <a-input-number v-decorator="['weight', { initialValue: 1, rules: [{ required: true }] }]" :min="1" :max="100" />
        </a-form-item>
        <a-form-item label="Public">
          <a-switch v-decorator="['is_public', { valuePropName: 'checked', initialValue: false }]" />
        </a-form-item>
        <a-form-item :label="$t('llm.status')">
          <a-select v-decorator="['status', { initialValue: 1 }]">
            <a-select-option :value="1">{{ $t('llm.status.active') }}</a-select-option>
            <a-select-option :value="0">{{ $t('llm.status.disabled') }}</a-select-option>
            <a-select-option :value="2">{{ $t('llm.status.broken') }}</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script>
import { getKeys, saveKey, deleteKey, getProviders } from '@/api/llm'

export default {
  name: 'KeyList',
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
        { title: 'Name', dataIndex: 'name' },
        { title: this.$t('llm.apiKey'), dataIndex: 'api_key_masked', scopedSlots: { customRender: 'apiKey' } },
        { title: this.$t('llm.weight'), dataIndex: 'weight' },
        { title: this.$t('llm.status'), dataIndex: 'status', scopedSlots: { customRender: 'status' } },
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
      getKeys().then(res => {
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
      this.modalTitle = this.$t('llm.addKey')
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
          name: record.name,
          weight: record.weight,
          is_public: record.is_public === 1,
          status: record.status
        })
      })
    },
    handleOk () {
      this.form.validateFields((err, values) => {
        if (!err) {
          this.confirmLoading = true
          const params = {
            ...values,
            is_public: values.is_public ? 1 : 0
          }
          if (this.editId) params.id = this.editId
          saveKey(params).then(() => {
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
      deleteKey(id).then(() => {
        this.$message.success('Deleted')
        this.loadData()
      })
    }
  }
}
</script>
