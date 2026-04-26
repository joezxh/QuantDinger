<template>
  <div class="perm-manage-page">
    <div class="page-header">
      <h2 class="page-title">
        <a-icon type="lock" />
        <span>{{ $t('permManage.title') || '权限管理' }}</span>
      </h2>
      <p class="page-desc">{{ $t('permManage.description') || '管理系统菜单和权限节点' }}</p>
    </div>

    <!-- Toolbar -->
    <div class="toolbar">
      <a-space>
        <a-button type="primary" @click="showCreateModal('dir')">
          <a-icon type="folder-add" />
          {{ $t('permManage.addDir') || '新增目录' }}
        </a-button>
        <a-button @click="showCreateModal('menu')">
          <a-icon type="menu" />
          {{ $t('permManage.addMenu') || '新增菜单' }}
        </a-button>
        <a-button @click="showCreateModal('button')">
          <a-icon type="control" />
          {{ $t('permManage.addButton') || '新增按钮' }}
        </a-button>
      </a-space>
      <a-button @click="fetchTree">
        <a-icon type="reload" />
        {{ $t('common.refresh') || '刷新' }}
      </a-button>
    </div>

    <!-- Permission Tree Table -->
    <a-table
      :columns="columns"
      :dataSource="flatList"
      :loading="loading"
      :pagination="false"
      :rowKey="(record, index) => `perm-${record.id}-${index}`"
      :expandRowByClick="false"
      :defaultExpandAllRows="true"
      :expandIconColumnIndex="-1"
    >
      <template slot="type" slot-scope="text">
        <a-tag :color="typeColor(text)">{{ typeLabel(text) }}</a-tag>
      </template>
      <template slot="name" slot-scope="text, record">
        <span :style="{ paddingLeft: (record._level || 0) * 24 + 'px' }">
          <a-icon :type="record.icon || typeIcon(record.type)" style="margin-right: 6px;" />
          {{ text }}
        </span>
      </template>
      <template slot="status" slot-scope="text">
        <a-badge :status="String(text || '').trim() === 'active' ? 'success' : 'default'" />
        {{ String(text || '').trim() === 'active' ? ($t('common.enabled') || '启用') : ($t('common.disabled') || '禁用') }}
      </template>
      <template slot="action" slot-scope="text, record">
        <a-space>
          <a-button type="link" size="small" @click="showEditModal(record)">
            <a-icon type="edit" />
          </a-button>
          <a-popconfirm
            :title="$t('permManage.confirmDelete') || '确定删除此权限？子节点将一并删除'"
            @confirm="handleDelete(record.id)"
          >
            <a-button type="link" size="small" style="color: #ff4d4f">
              <a-icon type="delete" />
            </a-button>
          </a-popconfirm>
        </a-space>
      </template>
    </a-table>

    <!-- Create/Edit Modal -->
    <a-modal
      v-model="modalVisible"
      :title="modalTitle"
      @ok="handleModalOk"
      @cancel="modalVisible = false"
      :confirmLoading="modalLoading"
      width="560"
    >
      <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item :label="$t('permManage.type') || '类型'">
          <a-radio-group v-model="form.type" :disabled="!!editingPerm">
            <a-radio value="dir">{{ $t('permManage.typeDir') || '目录' }}</a-radio>
            <a-radio value="menu">{{ $t('permManage.typeMenu') || '菜单' }}</a-radio>
            <a-radio value="button">{{ $t('permManage.typeButton') || '按钮' }}</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item :label="$t('permManage.name') || '权限名称'">
          <a-input v-model="form.name" :placeholder="$t('permManage.namePlaceholder') || '如 用户管理'" />
        </a-form-item>
        <a-form-item :label="$t('permManage.code') || '权限编码'">
          <a-input
            v-model="form.permission_code"
            :placeholder="$t('permManage.codePlaceholder') || '如 system:user:view'"
            :disabled="!!editingPerm"
          />
        </a-form-item>
        <a-form-item :label="$t('permManage.parent') || '父级权限'">
          <a-tree-select
            v-model="form.parent_id"
            :treeData="parentTree"
            :placeholder="$t('permManage.parentPlaceholder') || '选择父级（目录下才能为菜单/按钮）'"
            :replaceFields="{ title: 'name', key: 'permId', value: 'id' }"
            treeDefaultExpandAll
            allowClear
          />
        </a-form-item>
        <a-form-item v-if="form.type === 'menu'" :label="$t('permManage.path') || '路由路径'">
          <a-input v-model="form.path" placeholder="/user-manage" />
        </a-form-item>
        <a-form-item v-if="form.type === 'menu'" :label="$t('permManage.component') || '组件路径'">
          <a-input v-model="form.component" placeholder="@/views/user-manage" />
        </a-form-item>
        <a-form-item v-if="form.type !== 'button'" :label="$t('permManage.icon') || '图标'">
          <a-input v-model="form.icon" placeholder="team / setting" />
        </a-form-item>
        <a-form-item :label="$t('permManage.sortOrder') || '排序'">
          <a-input-number v-model="form.sort_order" :min="0" style="width: 100%" />
        </a-form-item>
        <a-form-item v-if="form.type !== 'button'" :label="$t('permManage.visible') || '可见'">
          <a-switch v-model="form.visible" />
        </a-form-item>
        <a-form-item :label="$t('permManage.status') || '状态'">
          <a-select v-model="form.status">
            <a-select-option value="active">{{ $t('common.enabled') || '启用' }}</a-select-option>
            <a-select-option value="disabled">{{ $t('common.disabled') || '禁用' }}</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script>
import {
  getPermissionTree, createPermission, updatePermission, deletePermission
} from '@/api/permission'
import { TreeSelect } from 'ant-design-vue'

const TYPE_MAP = {
  dir: { label: '目录', color: 'blue' },
  menu: { label: '菜单', color: 'green' },
  button: { label: '按钮', color: 'orange' }
}

export default {
  name: 'PermissionManage',
  components: { ATreeSelect: TreeSelect },
  data () {
    return {
      loading: false,
      treeData: [],
      flatList: [],
      modalVisible: false,
      modalLoading: false,
      editingPerm: null,
      form: {
        type: 'menu',
        name: '',
        permission_code: '',
        parent_id: null,
        path: '',
        component: '',
        icon: '',
        sort_order: 0,
        visible: true,
        status: 'active'
      }
    }
  },
  computed: {
    columns () {
      return [
        { title: this.$t('permManage.name') || '权限名称', dataIndex: 'name', key: 'name', scopedSlots: { customRender: 'name' } },
        { title: this.$t('permManage.type') || '类型', dataIndex: 'type', key: 'type', scopedSlots: { customRender: 'type' }, width: 80 },
        { title: this.$t('permManage.code') || '权限编码', dataIndex: 'permission_code', key: 'permission_code', width: 200 },
        { title: this.$t('permManage.path') || '路由路径', dataIndex: 'path', key: 'path', ellipsis: true, width: 160 },
        { title: this.$t('permManage.status') || '状态', dataIndex: 'status', key: 'status', scopedSlots: { customRender: 'status' }, width: 80 },
        { title: this.$t('common.actions') || '操作', key: 'action', scopedSlots: { customRender: 'action' }, width: 120 }
      ]
    },
    modalTitle () {
      return this.editingPerm
        ? (this.$t('permManage.editTitle') || '编辑权限')
        : (this.$t('permManage.createTitle') || '新增权限')
    },
    parentTree () {
      // Only dir/menu can be parents - 使用稳定的 permId 作为 key
      return this.buildParentTree(this.treeData)
    }
  },
  mounted () {
    this.fetchTree()
  },
  methods: {
    typeColor (t) {
      const m = TYPE_MAP[String(t || '').trim()] || { color: 'default' }
      return m.color
    },
    typeLabel (t) {
      const m = TYPE_MAP[String(t || '').trim()] || { label: t }
      return m.label
    },
    typeIcon (t) {
      const type = String(t || '').trim()
      if (type === 'dir') return 'folder'
      if (type === 'menu') return 'menu'
      return 'control'
    },

    async fetchTree () {
      this.loading = true
      try {
        const res = await getPermissionTree(true)
        this.treeData = res.data || []
        this.flatList = this.flattenTree(this.treeData, 0)
      } catch (e) {
        this.$message.error(this.$t('permManage.fetchFailed') || '加载权限树失败')
      }
      this.loading = false
    },

    flattenTree (nodes, level) {
      const result = []
      let counter = 0
      const flatten = (nodes, level) => {
        for (const node of nodes) {
          // 使用自增计数器确保 key 绝对唯一，避免同一 id 在不同层级重复
          const uniqueKey = `row-${counter++}`
          // 删除 children 字段，避免 a-table 内部重复渲染
          const { children, ...rest } = node
          result.push({ ...rest, _level: level, _uniqueKey: uniqueKey })
          if (children?.length) {
            flatten(children, level + 1)
          }
        }
      }
      flatten(nodes, level)
      return result
    },

    buildParentTree (nodes) {
      // 为 tree-select 构建稳定的树数据，使用 permId 避免重复 key
      let counter = 0
      const build = (nodes) => {
        return nodes
          .filter(n => n.type !== 'button')
          .map(node => {
            const permId = `perm-${counter++}`
            const result = {
              ...node,
              permId
            }
            if (node.children?.length) {
              result.children = build(node.children)
            }
            return result
          })
      }
      return build(nodes)
    },

    showCreateModal (type) {
      this.editingPerm = null
      this.form = {
        type,
        name: '',
        permission_code: '',
        parent_id: null,
        path: '',
        component: '',
        icon: '',
        sort_order: 0,
        visible: true,
        status: 'active'
      }
      this.modalVisible = true
    },

    showEditModal (record) {
      this.editingPerm = record
      this.form = {
        type: record.type,
        name: record.name,
        permission_code: record.permission_code,
        parent_id: record.parent_id,
        path: record.path || '',
        component: record.component || '',
        icon: record.icon || '',
        sort_order: record.sort_order || 0,
        visible: record.visible !== false,
        status: record.status || 'active'
      }
      this.modalVisible = true
    },

    async handleModalOk () {
      if (!this.form.name || !this.form.permission_code) {
        this.$message.warning(this.$t('permManage.requiredFields') || '请填写权限名称和编码')
        return
      }
      this.modalLoading = true
      try {
        if (this.editingPerm) {
          await updatePermission(this.editingPerm.id, this.form)
          this.$message.success(this.$t('permManage.updateSuccess') || '权限更新成功')
        } else {
          await createPermission(this.form)
          this.$message.success(this.$t('permManage.createSuccess') || '权限创建成功')
        }
        this.modalVisible = false
        this.fetchTree()
      } catch (e) {
        this.$message.error(e.response?.data?.msg || (this.$t('common.operationFailed') || '操作失败'))
      }
      this.modalLoading = false
    },

    async handleDelete (id) {
      try {
        await deletePermission(id)
        this.$message.success(this.$t('permManage.deleteSuccess') || '权限删除成功')
        this.fetchTree()
      } catch (e) {
        this.$message.error(e.response?.data?.msg || (this.$t('common.operationFailed') || '操作失败'))
      }
    }
  }
}
</script>

<style scoped>
.perm-manage-page {
  padding: 20px;
}
.page-header {
  margin-bottom: 20px;
}
.page-title {
  margin: 0;
  font-size: 20px;
}
.page-desc {
  color: #999;
  margin-top: 4px;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}
.text-muted {
  color: #999;
}
</style>
