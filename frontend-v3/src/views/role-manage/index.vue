<template>
  <div class="role-manage-page">
    <div class="page-header">
      <h2 class="page-title">
        <SafetyOutlined />
        <span>{{ t('menu.roleManage') }}</span>
      </h2>
      <p class="page-desc">{{ t('roleManage.pageSubtitle') }}</p>
    </div>

    <!-- Toolbar -->
    <div class="toolbar">
      <a-button type="primary" @click="showCreateModal">
        <PlusOutlined />
        {{ t('roleManage.addRole') }}
      </a-button>
      <a-input-search
        v-model="keyword"
        class="toolbar-search"
        :placeholder="t('roleManage.searchPlaceholder')"
        allowClear
        @search="fetchRoles"
      />
    </div>

    <!-- Role Table -->
    <a-table
      :columns="columns"
      :data-source="roles"
      :loading="loading"
      :pagination="false"
      :row-key="(record: any, index: number) => `role-${record.id}-${index}`"
    >
      <template #status="{ record }">
        <a-badge :status="record.status === 'active' ? 'success' : 'default'" />
        {{ record.status === 'active' ? t('common.enable') : t('common.disable') }}
      </template>

      <template #action="{ record }">
        <a-space>
          <a-button type="link" size="small" @click="showEditModal(record)">
            <EditOutlined />
            {{ t('common.edit') }}
          </a-button>
          <a-button type="link" size="small" @click="showPermissionModal(record)">
            <KeyOutlined />
            {{ t('roleManage.assignPermission') }}
          </a-button>
          <a-popconfirm
            :title="t('roleManage.deleteConfirm')"
            @confirm="handleDelete(record.id)"
          >
            <a-button type="link" size="small" style="color: #ff4d4f">
              <DeleteOutlined />
              {{ t('common.delete') }}
            </a-button>
          </a-popconfirm>
        </a-space>
      </template>
    </a-table>

    <!-- Create/Edit Role Modal -->
    <a-modal
      v-model:visible="modalVisible"
      :title="modalTitle"
      @ok="handleModalOk"
      :confirmLoading="modalLoading"
    >
      <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item :label="t('roleManage.roleName')">
          <a-input v-model:value="form.name" :placeholder="t('roleManage.roleNamePlaceholder')" />
        </a-form-item>
        <a-form-item :label="t('roleManage.roleCode')">
          <a-input
            v-model:value="form.role_code"
            :placeholder="t('roleManage.roleCodePlaceholder')"
            :disabled="!!editingRole"
          />
        </a-form-item>
        <a-form-item :label="t('common.remark')">
          <a-textarea
            v-model:value="form.description"
            :rows="3"
            :placeholder="t('roleManage.descriptionPlaceholder')"
          />
        </a-form-item>
        <a-form-item :label="t('common.status')">
          <a-select v-model:value="form.status">
            <a-select-option value="active">{{ t('common.enable') }}</a-select-option>
            <a-select-option value="disabled">{{ t('common.disable') }}</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Permission Assignment Drawer -->
    <a-drawer
      v-model:visible="permDrawerVisible"
      :title="permDrawerTitle"
      :width="400"
    >
      <a-spin :spinning="permLoading">
        <a-tree
          v-model:checked-keys="checkedKeys"
          checkable
          :tree-data="permTree"
          :replace-fields="{ title: 'name', key: 'treePermId' }"
          @check="onCheck"
          default-expand-all
        />
        <div class="drawer-footer">
          <a-button @click="permDrawerVisible = false">{{ t('common.cancel') }}</a-button>
          <a-button type="primary" :loading="permSaving" @click="savePermissions">{{ t('indicatorIde.save') }}</a-button>
        </div>
      </a-spin>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import {
  SafetyOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  KeyOutlined,
} from '@ant-design/icons-vue'
import {
  getRoleList,
  createRole,
  updateRole,
  deleteRole,
  getRole,
  getPermissionTree,
  assignPermissionsToRole,
} from '@/api/permission'

interface Role {
  id: number
  name: string
  role_code: string
  description: string
  status: string
}

interface RoleForm {
  name: string
  role_code: string
  description: string
  status: string
}

interface PermTreeNode {
  id: number
  name: string
  treePermId: string
  children?: PermTreeNode[]
}

const { t } = useI18n()
const loading = ref(false)
const keyword = ref('')
const roles = ref<Role[]>([])

const modalVisible = ref(false)
const modalLoading = ref(false)
const editingRole = ref<Role | null>(null)
const form = reactive<RoleForm>({
  name: '',
  role_code: '',
  description: '',
  status: 'active',
})

const permDrawerVisible = ref(false)
const permLoading = ref(false)
const permSaving = ref(false)
const permRoleId = ref<number | null>(null)
const permTree = ref<PermTreeNode[]>([])
const checkedKeys = ref<string[]>([])
const checkedPermIds = ref<number[]>([])
const permIdMap = ref<Record<string, number>>({})

const modalTitle = computed(() =>
  editingRole.value ? t('roleManage.editRole') : t('roleManage.addRole')
)

const permDrawerTitle = computed(() =>
  `${t('roleManage.assignPermission')} - ${editingRole.value?.name || ''}`
)

const columns = [
  { title: t('roleManage.roleName'), dataIndex: 'name', key: 'name' },
  { title: t('roleManage.roleCode'), dataIndex: 'role_code', key: 'role_code' },
  { title: t('common.remark'), dataIndex: 'description', key: 'description', ellipsis: true },
  { title: t('common.status'), key: 'status', slots: { customRender: 'status' }, width: 80 },
  { title: t('common.action'), key: 'action', slots: { customRender: 'action' }, width: 280 },
]

async function fetchRoles() {
  loading.value = true
  try {
    const res = await getRoleList({ page: 1, page_size: 200 })
    roles.value = res.data?.items || []
  } catch (e: any) {
    message.error(t('roleManage.loadFailed'))
  }
  loading.value = false
}

function showCreateModal() {
  editingRole.value = null
  Object.assign(form, { name: '', role_code: '', description: '', status: 'active' })
  modalVisible.value = true
}

function showEditModal(record: Role) {
  editingRole.value = record
  Object.assign(form, { ...record })
  modalVisible.value = true
}

async function handleModalOk() {
  if (!form.name || !form.role_code) {
    message.warning(t('roleManage.nameCodeRequired'))
    return
  }
  modalLoading.value = true
  try {
    if (editingRole.value) {
      await updateRole(editingRole.value.id, form)
      message.success(t('common.updateSuccess'))
    } else {
      await createRole(form)
      message.success(t('common.createSuccess'))
    }
    modalVisible.value = false
    await fetchRoles()
  } catch (e: any) {
    message.error(e.response?.data?.msg || t('common.failed'))
  }
  modalLoading.value = false
}

async function handleDelete(id: number) {
  try {
    await deleteRole(id)
    message.success(t('common.deleteSuccess'))
    await fetchRoles()
  } catch (e: any) {
    message.error(e.response?.data?.msg || t('common.failed'))
  }
}

async function showPermissionModal(record: Role) {
  editingRole.value = record
  permRoleId.value = record.id
  permDrawerVisible.value = true
  permLoading.value = true
  try {
    const [treeRes, roleRes] = await Promise.all([
      getPermissionTree(true),
      getRole(record.id),
    ])

    const idMap: Record<string, number> = {}
    let counter = 0

    function addUniqueKeys(nodes: any[]): PermTreeNode[] {
      return nodes.map((node) => {
        const treePermId = `tree-${counter++}`
        idMap[treePermId] = node.id
        const result: PermTreeNode = { ...node, treePermId }
        if (node.children?.length) {
          result.children = addUniqueKeys(node.children)
        }
        return result
      })
    }

    permTree.value = addUniqueKeys(treeRes.data || [])
    permIdMap.value = idMap

    const backendIds = roleRes.data?.permission_ids || []
    const idToTreeKey: Record<number, string> = {}
    Object.entries(idMap).forEach(([k, v]) => {
      idToTreeKey[v] = k
    })
    checkedKeys.value = backendIds.map((id: number) => idToTreeKey[id]).filter(Boolean)
    checkedPermIds.value = [...backendIds]
  } catch (e: any) {
    message.error(t('roleManage.permLoadFailed'))
  }
  permLoading.value = false
}

function onCheck(checked: string[]) {
  checkedKeys.value = checked
  checkedPermIds.value = checked
    .map((k) => permIdMap.value[k])
    .filter((id): id is number => id !== undefined)
}

async function savePermissions() {
  permSaving.value = true
  try {
    if (permRoleId.value !== null) {
      await assignPermissionsToRole(permRoleId.value, checkedPermIds.value)
      message.success(t('roleManage.permAssignSuccess'))
      permDrawerVisible.value = false
    }
  } catch (e: any) {
    message.error(e.response?.data?.msg || t('common.failed'))
  }
  permSaving.value = false
}

onMounted(() => {
  fetchRoles()
})
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
