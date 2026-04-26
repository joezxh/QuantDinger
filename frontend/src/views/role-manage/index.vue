<template>
  <div class="role-manage-page">
    <div class="page-header">
      <h2 class="page-title">
        <a-icon type="safety" />
        <span>{{ $t('roleManage.title') || '角色管理' }}</span>
      </h2>
      <p class="page-desc">{{ $t('roleManage.description') || '管理系统角色和权限分配' }}</p>
    </div>

    <!-- Toolbar -->
    <div class="toolbar">
      <a-button type="primary" @click="showCreateModal">
        <a-icon type="plus" />
        {{ $t('roleManage.createRole') || '新增角色' }}
      </a-button>
      <a-input-search
        v-model="keyword"
        class="toolbar-search"
        :placeholder="$t('roleManage.searchPlaceholder') || '搜索角色名称/编码'"
        allowClear
        @search="fetchRoles"
      />
    </div>

    <!-- Role Table -->
    <a-table
      :columns="columns"
      :dataSource="roles"
      :loading="loading"
      :pagination="false"
      :rowKey="(record, index) => `role-${record.id}-${index}`"
    >
      <template slot="status" slot-scope="text">
        <a-badge :status="String(text || '').trim() === 'active' ? 'success' : 'default'" />
        {{ String(text || '').trim() === 'active' ? ($t('common.enabled') || '启用') : ($t('common.disabled') || '禁用') }}
      </template>

      <template slot="action" slot-scope="text, record">
        <a-space>
          <a-button type="link" size="small" @click="showEditModal(record)">
            <a-icon type="edit" />
            {{ $t('common.edit') || '编辑' }}
          </a-button>
          <a-button type="link" size="small" @click="showPermissionModal(record)">
            <a-icon type="key" />
            {{ $t('roleManage.assignPermission') || '分配权限' }}
          </a-button>
          <a-popconfirm
            :title="$t('roleManage.confirmDelete') || '确定删除此角色？'"
            @confirm="handleDelete(record.id)"
          >
            <a-button type="link" size="small" style="color: #ff4d4f">
              <a-icon type="delete" />
              {{ $t('common.delete') || '删除' }}
            </a-button>
          </a-popconfirm>
        </a-space>
      </template>
    </a-table>

    <!-- Create/Edit Role Modal -->
    <a-modal
      v-model="modalVisible"
      :title="modalTitle"
      @ok="handleModalOk"
      @cancel="modalVisible = false"
      :confirmLoading="modalLoading"
    >
      <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item :label="$t('roleManage.name') || '角色名称'">
          <a-input v-model="form.name" :placeholder="$t('roleManage.namePlaceholder') || '请输入角色名称'" />
        </a-form-item>
        <a-form-item :label="$t('roleManage.code') || '角色编码'">
          <a-input
            v-model="form.role_code"
            :placeholder="$t('roleManage.codePlaceholder') || '如 admin / trader'"
            :disabled="!!editingRole"
          />
        </a-form-item>
        <a-form-item :label="$t('roleManage.descLabel') || '描述'">
          <a-textarea
            v-model="form.description"
            :rows="3"
            :placeholder="$t('roleManage.descPlaceholder') || '角色描述说明'"
          />
        </a-form-item>
        <a-form-item :label="$t('roleManage.status') || '状态'">
          <a-select v-model="form.status">
            <a-select-option value="active">{{ $t('common.enabled') || '启用' }}</a-select-option>
            <a-select-option value="disabled">{{ $t('common.disabled') || '禁用' }}</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Permission Assignment Drawer -->
    <a-drawer
      :title="permDrawerTitle"
      :visible="permDrawerVisible"
      :width="400"
      @close="permDrawerVisible = false"
    >
      <a-spin :spinning="permLoading">
        <a-tree
          v-model="checkedKeys"
          checkable
          :treeData="permTree"
          :replaceFields="{ title: 'name', key: 'treePermId' }"
          @check="onCheck"
          defaultExpandAll
        />
        <div class="drawer-footer">
          <a-button @click="permDrawerVisible = false">{{ $t('common.cancel') || '取消' }}</a-button>
          <a-button type="primary" :loading="permSaving" @click="savePermissions">
            {{ $t('common.save') || '保存' }}
          </a-button>
        </div>
      </a-spin>
    </a-drawer>
  </div>
</template>

<script>
import {
  getRoleList, createRole, updateRole, deleteRole, getRole,
  getPermissionTree, assignPermissionsToRole
} from '@/api/permission'

export default {
  name: 'RoleManage',
  data () {
    return {
      loading: false,
      keyword: '',
      roles: [],
      modalVisible: false,
      modalLoading: false,
      editingRole: null,
      form: { name: '', role_code: '', description: '', status: 'active' },
      // Permission drawer
      permDrawerVisible: false,
      permLoading: false,
      permSaving: false,
      permRoleId: null,
      permTree: [],
      checkedKeys: [],
      checkedPermIds: []
    }
  },
  computed: {
    modalTitle () {
      return this.editingRole
        ? (this.$t('roleManage.editTitle') || '编辑角色')
        : (this.$t('roleManage.createTitle') || '新增角色')
    },
    permDrawerTitle () {
      return `${this.$t('roleManage.assignPermission') || '分配权限'} - ${this.editingRole ? this.editingRole.name : ''}`
    },
    columns () {
      return [
        { title: this.$t('roleManage.name') || '角色名称', dataIndex: 'name', key: 'name' },
        { title: this.$t('roleManage.code') || '角色编码', dataIndex: 'role_code', key: 'role_code' },
        { title: this.$t('roleManage.descLabel') || '描述', dataIndex: 'description', key: 'description', ellipsis: true },
        { title: this.$t('roleManage.status') || '状态', key: 'status', scopedSlots: { customRender: 'status' }, width: 80 },
        { title: this.$t('common.actions') || '操作', key: 'action', scopedSlots: { customRender: 'action' }, width: 280 }
      ]
    }
  },
  mounted () {
    this.fetchRoles()
  },
  methods: {
    async fetchRoles () {
      this.loading = true
      try {
        const res = await getRoleList({ page: 1, page_size: 200 })
        this.roles = res.data?.items || []
      } catch (e) {
        this.$message.error(this.$t('roleManage.fetchFailed') || '加载角色列表失败')
      }
      this.loading = false
    },

    showCreateModal () {
      this.editingRole = null
      this.form = { name: '', role_code: '', description: '', status: 'active' }
      this.modalVisible = true
    },

    showEditModal (record) {
      this.editingRole = record
      this.form = { ...record }
      this.modalVisible = true
    },

    async handleModalOk () {
      if (!this.form.name || !this.form.role_code) {
        this.$message.warning(this.$t('roleManage.requiredFields') || '请填写角色名称和编码')
        return
      }
      this.modalLoading = true
      try {
        if (this.editingRole) {
          await updateRole(this.editingRole.id, this.form)
          this.$message.success(this.$t('roleManage.updateSuccess') || '角色更新成功')
        } else {
          await createRole(this.form)
          this.$message.success(this.$t('roleManage.createSuccess') || '角色创建成功')
        }
        this.modalVisible = false
        this.fetchRoles()
      } catch (e) {
        this.$message.error(e.response?.data?.msg || (this.$t('common.operationFailed') || '操作失败'))
      }
      this.modalLoading = false
    },

    async handleDelete (id) {
      try {
        await deleteRole(id)
        this.$message.success(this.$t('roleManage.deleteSuccess') || '角色删除成功')
        this.fetchRoles()
      } catch (e) {
        this.$message.error(e.response?.data?.msg || (this.$t('common.operationFailed') || '操作失败'))
      }
    },

    async showPermissionModal (record) {
      this.editingRole = record
      this.permRoleId = record.id
      this.permDrawerVisible = true
      this.permLoading = true
      try {
        const [treeRes, roleRes] = await Promise.all([
          getPermissionTree(true),
          getRole(record.id)
        ])
        // 为树节点添加唯一 key，避免重复
        const addUniqueKeys = (nodes, counter = { value: 0 }) => {
          return nodes.map(node => {
            const result = { ...node, treePermId: `tree-${counter.value++}` }
            if (node.children?.length) {
              result.children = addUniqueKeys(node.children, counter)
            }
            return result
          })
        }
        this.permTree = addUniqueKeys(treeRes.data || [])
        this.checkedPermIds = roleRes.data?.permission_ids || []
        this.checkedKeys = this.checkedPermIds.slice()
      } catch (e) {
        this.$message.error(this.$t('roleManage.permissionFetchFailed') || '加载权限数据失败')
      }
      this.permLoading = false
    },

    onCheck (checkedKeys, info) {
      this.checkedKeys = checkedKeys
      // Collect all leaf node ids
      this.checkedPermIds = [...checkedKeys]
    },

    async savePermissions () {
      this.permSaving = true
      try {
        await assignPermissionsToRole(this.permRoleId, this.checkedPermIds)
        this.$message.success(this.$t('roleManage.permissionSaved') || '权限分配成功')
        this.permDrawerVisible = false
      } catch (e) {
        this.$message.error(e.response?.data?.msg || (this.$t('common.operationFailed') || '操作失败'))
      }
      this.permSaving = false
    }
  }
}
</script>

<style scoped>
.role-manage-page {
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
.toolbar-search {
  width: 260px;
}
.drawer-footer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px 24px;
  border-top: 1px solid #e8e8e8;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  background: #fff;
}
</style>
