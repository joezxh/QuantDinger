<template>
  <div class="perm-manage-page">
    <div class="page-header">
      <h2 class="page-title">
        <LockOutlined />
        <span>{{ t('menu.permissionManage') }}</span>
      </h2>
      <p class="page-desc">{{ t('permissionManage.pageSubtitle') }}</p>
    </div>

    <!-- Toolbar -->
    <div class="toolbar">
      <a-space>
        <a-button type="primary" @click="showCreateModal('dir')">
          <FolderAddOutlined />
          {{ t('permissionManage.addDir') }}
        </a-button>
        <a-button @click="showCreateModal('menu')">
          <MenuOutlined />
          {{ t('permissionManage.addMenu') }}
        </a-button>
        <a-button @click="showCreateModal('button')">
          <ControlOutlined />
          {{ t('permissionManage.addButton') }}
        </a-button>
      </a-space>
      <a-button @click="fetchTree">
        <ReloadOutlined />
        {{ t('common.refresh') }}
      </a-button>
    </div>

    <!-- Permission Tree Table -->
    <a-table
      :columns="columns"
      :data-source="flatList"
      :loading="loading"
      :pagination="false"
      :row-key="(record: any) => record._uniqueKey"
      :expand-row-by-click="false"
      :default-expand-all-rows="true"
      :expand-icon-column-index="-1"
    >
      <template #type="{ record }">
        <a-tag :color="typeColor(record.type)">{{ typeLabel(record.type) }}</a-tag>
      </template>
      <template #name="{ record }">
        <span :style="{ paddingLeft: (record._level || 0) * 24 + 'px' }">
          <component
            :is="getIcon(record.icon || typeIcon(record.type))"
            style="margin-right: 6px"
          />
          {{ record.name }}
        </span>
      </template>
      <template #status="{ record }">
        <a-badge :status="record.status === 'active' ? 'success' : 'default'" />
        {{ record.status === 'active' ? '启用' : '禁用' }}
      </template>
      <template #action="{ record }">
        <a-space>
          <a-button type="link" size="small" @click="showEditModal(record)">
            <EditOutlined />
          </a-button>
          <a-popconfirm
            :title="t('batch.auto195')"
            @confirm="handleDelete(record.id)"
          >
            <a-button type="link" size="small" style="color: #ff4d4f">
              <DeleteOutlined />
            </a-button>
          </a-popconfirm>
        </a-space>
      </template>
    </a-table>

    <!-- Create/Edit Modal -->
    <a-modal
      v-model:visible="modalVisible"
      :title="modalTitle"
      @ok="handleModalOk"
      :confirmLoading="modalLoading"
      width="560"
    >
      <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item :label="t('common.type')">
          <a-radio-group v-model:value="form.type" :disabled="!!editingPerm">
            <a-radio value="dir">目录</a-radio>
            <a-radio value="menu">菜单</a-radio>
            <a-radio value="button">按钮</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item :label="t('batch.auto196')">
          <a-input v-model:value="form.name" :placeholder="t('batch.auto192')" />
        </a-form-item>
        <a-form-item :label="t('batch.auto197')">
          <a-input
            v-model:value="form.permission_code"
            :placeholder="t('batch.auto193')"
            :disabled="!!editingPerm"
          />
        </a-form-item>
        <a-form-item :label="t('batch.auto198')">
          <a-tree-select
            v-model:value="form.parent_id"
            :tree-data="parentTree"
            :placeholder="t('batch.auto194')"
            :replace-fields="{ title: 'name', key: 'permId', value: 'id' }"
            tree-default-expand-all
            allow-clear
          />
        </a-form-item>
        <a-form-item v-if="form.type === 'menu'" :label="t('menuManage.column.path')">
          <a-input v-model:value="form.path" placeholder="/user-manage" />
        </a-form-item>
        <a-form-item v-if="form.type === 'menu'" :label="t('batch.auto199')">
          <a-input v-model:value="form.component" placeholder="@/views/user-manage" />
        </a-form-item>
        <a-form-item v-if="form.type !== 'button'" :label="t('batch.auto200')">
          <a-input v-model:value="form.icon" placeholder="team / setting" />
        </a-form-item>
        <a-form-item :label="t('batch.auto201')">
          <a-input-number v-model:value="form.sort_order" :min="0" style="width: 100%" />
        </a-form-item>
        <a-form-item v-if="form.type !== 'button'" :label="t('batch.auto202')">
          <a-switch v-model:checked="form.visible" />
        </a-form-item>
        <a-form-item :label="t('common.status')">
          <a-select v-model:value="form.status">
            <a-select-option value="active">{{ t('batch.auto203') }}</a-select-option>
            <a-select-option value="disabled">{{ t('batch.auto156') }}</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import {
  LockOutlined,
  FolderAddOutlined,
  MenuOutlined,
  ControlOutlined,
  ReloadOutlined,
  EditOutlined,
  DeleteOutlined,
  FolderOutlined,
  MenuFoldOutlined,
} from '@ant-design/icons-vue'
import {
  getPermissionTree,
  createPermission,
  updatePermission,
  deletePermission,
} from '@/api/permission'

interface Permission {
  id: number
  name: string
  permission_code: string
  type: string
  parent_id: number | null
  path?: string
  component?: string
  icon?: string
  sort_order?: number
  visible?: boolean
  status: string
  children?: Permission[]
}

interface PermissionForm {
  type: string
  name: string
  permission_code: string
  parent_id: number | null
  path: string
  component: string
  icon: string
  sort_order: number
  visible: boolean
  status: string
}

interface FlatPermission extends Permission {
  _level: number
  _uniqueKey: string
}

interface ParentTreeNode extends Permission {
  permId: string
}

const TYPE_MAP: Record<string, { label: string; color: string }> = {
  dir: { label: '目录', color: 'blue' },
  menu: { label: '菜单', color: 'green' },
  button: { label: '按钮', color: 'orange' },
}

const { t } = useI18n()
const loading = ref(false)
const treeData = ref<Permission[]>([])
const flatList = ref<FlatPermission[]>([])

const modalVisible = ref(false)
const modalLoading = ref(false)
const editingPerm = ref<Permission | null>(null)
const form = reactive<PermissionForm>({
  type: 'menu',
  name: '',
  permission_code: '',
  parent_id: null,
  path: '',
  component: '',
  icon: '',
  sort_order: 0,
  visible: true,
  status: 'active',
})

const columns = [
  { title: t('batch.auto196'), dataIndex: 'name', key: 'name', slots: { customRender: 'name' } },
  { title: t('common.type'), dataIndex: 'type', key: 'type', slots: { customRender: 'type' }, width: 80 },
  { title: t('batch.auto197'), dataIndex: 'permission_code', key: 'permission_code', width: 200 },
  { title: t('menuManage.column.path'), dataIndex: 'path', key: 'path', ellipsis: true, width: 160 },
  { title: t('common.status'), dataIndex: 'status', key: 'status', slots: { customRender: 'status' }, width: 80 },
  { title: t('common.action'), key: 'action', slots: { customRender: 'action' }, width: 120 },
]

const modalTitle = computed(() =>
  editingPerm.value ? '编辑权限' : '新增权限'
)

const parentTree = computed<ParentTreeNode[]>(() => {
  let counter = 0
  const build = (nodes: Permission[]): ParentTreeNode[] => {
    return nodes
      .filter((n) => n.type !== 'button')
      .map((node) => {
        const permId = `perm-${counter++}`
        const result: ParentTreeNode = { ...node, permId }
        if (node.children?.length) {
          result.children = build(node.children)
        }
        return result
      })
  }
  return build(treeData.value)
})

function typeColor(t: string) {
  const m = TYPE_MAP[t] || { color: 'default' }
  return m.color
}

function typeLabel(t: string) {
  const m = TYPE_MAP[t] || { label: t }
  return m.label
}

function typeIcon(t: string) {
  if (t === 'dir') return 'folder'
  if (t === 'menu') return 'menu'
  return 'control'
}

const iconMap: Record<string, any> = {
  folder: FolderOutlined,
  menu: MenuFoldOutlined,
  control: ControlOutlined,
}

function getIcon(name: string) {
  return iconMap[name] || MenuFoldOutlined
}

async function fetchTree() {
  loading.value = true
  try {
    const res = await getPermissionTree(true)
    treeData.value = res.data || []
    flatList.value = flattenTree(treeData.value)
  } catch (e: any) {
    message.error(t('batch.auto187'))
  }
  loading.value = false
}

function flattenTree(nodes: Permission[]): FlatPermission[] {
  const result: FlatPermission[] = []
  let counter = 0
  const flatten = (nodes: Permission[], level: number) => {
    for (const node of nodes) {
      const uniqueKey = `row-${counter++}`
      const { children, ...rest } = node
      result.push({ ...rest, _level: level, _uniqueKey: uniqueKey })
      if (children?.length) {
        flatten(children, level + 1)
      }
    }
  }
  flatten(nodes, 0)
  return result
}

function showCreateModal(type: string) {
  editingPerm.value = null
  Object.assign(form, {
    type,
    name: '',
    permission_code: '',
    parent_id: null,
    path: '',
    component: '',
    icon: '',
    sort_order: 0,
    visible: true,
    status: 'active',
  })
  modalVisible.value = true
}

function showEditModal(record: Permission) {
  editingPerm.value = record
  Object.assign(form, {
    type: record.type,
    name: record.name,
    permission_code: record.permission_code,
    parent_id: record.parent_id,
    path: record.path || '',
    component: record.component || '',
    icon: record.icon || '',
    sort_order: record.sort_order || 0,
    visible: record.visible !== false,
    status: record.status || 'active',
  })
  modalVisible.value = true
}

async function handleModalOk() {
  if (!form.name || !form.permission_code) {
    message.warning(t('batch.auto188'))
    return
  }
  modalLoading.value = true
  try {
    if (editingPerm.value) {
      await updatePermission(editingPerm.value.id, form)
      message.success(t('batch.auto189'))
    } else {
      await createPermission(form)
      message.success(t('batch.auto190'))
    }
    modalVisible.value = false
    await fetchTree()
  } catch (e: any) {
    message.error(e.response?.data?.msg || '操作失败')
  }
  modalLoading.value = false
}

async function handleDelete(id: number) {
  try {
    await deletePermission(id)
    message.success(t('batch.auto191'))
    await fetchTree()
  } catch (e: any) {
    message.error(e.response?.data?.msg || '操作失败')
  }
}

onMounted(() => {
  fetchTree()
})
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
</style>
