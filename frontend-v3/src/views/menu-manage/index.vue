<template>
  <div class="menu-manage">
    <div class="page-header">
      <div class="header-left">
        <h2>{{ $t('menuManage.title') }}</h2>
        <p class="subtitle">{{ $t('menuManage.subtitle') }}</p>
      </div>
      <div class="header-actions">
        <a-space>
          <a-button @click="resetMenus">{{ $t('menuManage.reset') }}</a-button>
          <a-button type="primary" @click="handleSave">{{ $t('menuManage.save') }}</a-button>
        </a-space>
      </div>
    </div>

    <a-card :bordered="false" class="main-card">
      <div class="alert-info">
        <a-alert :message="$t('app.setting.multitab')" type="info" show-icon />
      </div>

      <a-table
        :columns="columns"
        :data-source="editableMenus"
        :pagination="false"
        row-key="path"
        children-column-name="children"
        default-expand-all-rows
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'label'">
            <a-input v-model:value="record.label" size="small" />
          </template>
          
          <template v-if="column.key === 'path'">
            <a-input v-model:value="record.path" size="small" :disabled="record.children?.length > 0" />
          </template>
          
          <template v-if="column.key === 'icon'">
            <a-input v-model:value="record.icon" size="small">
              <template #prefix>
                <component :is="getIcon(record.icon)" v-if="record.icon" />
              </template>
            </a-input>
          </template>
          
          <template v-if="column.key === 'hidden'">
            <a-switch v-model:checked="record.hidden" />
          </template>
          
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button type="link" size="small" @click="addChild(record)" v-if="!record.parentPath">{{ $t('menuManage.addChild') }}</a-button>
              <a-popconfirm :title="$t('menuManage.deleteConfirm')" @confirm="deleteItem(record)">
                <a-button type="link" size="small" danger>{{ $t('common.delete') }}</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>

      <div class="add-root">
        <a-button type="dashed" block @click="addRoot">
          <PlusOutlined /> {{ $t('menuManage.addRoot') }}
        </a-button>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { PlusOutlined } from '@ant-design/icons-vue'
import { useMenuStore, type MenuItem } from '@/stores/menu'

const { t } = useI18n()
const menuStore = useMenuStore()
const editableMenus = ref<MenuItem[]>([])
const getIcon = menuStore.getIcon

const columns = computed(() => [
  { title: t('menuManage.column.label'), dataIndex: 'label', key: 'label', width: '25%' },
  { title: t('menuManage.column.path'), dataIndex: 'path', key: 'path', width: '25%' },
  { title: t('menuManage.column.icon'), dataIndex: 'icon', key: 'icon', width: '20%' },
  { title: t('menuManage.column.hidden'), dataIndex: 'hidden', key: 'hidden', width: '10%', align: 'center' },
  { title: t('menuManage.column.action'), key: 'actions', width: '20%', align: 'right' },
])

onMounted(() => {
  editableMenus.value = JSON.parse(JSON.stringify(menuStore.menus))
})

const handleSave = () => {
  menuStore.updateMenus(editableMenus.value)
  message.success(t('menuManage.saveSuccess'))
}

const resetMenus = () => {
  menuStore.resetMenus()
  editableMenus.value = JSON.parse(JSON.stringify(menuStore.menus))
  message.success(t('menuManage.resetSuccess'))
}

const addRoot = () => {
  editableMenus.value.push({
    path: '/new-root-' + Date.now(),
    label: t('menuManage.newMenu'),
    icon: 'AppstoreOutlined',
    children: []
  })
}

const addChild = (parent: MenuItem) => {
  if (!parent.children) parent.children = []
  parent.children.push({
    path: parent.path + '/new-item-' + Date.now(),
    label: t('menuManage.newItem'),
    icon: 'FileOutlined'
  })
}

const deleteItem = (item: MenuItem) => {
  const removeFromArray = (arr: MenuItem[]) => {
    const index = arr.findIndex(i => i === item)
    if (index > -1) {
      arr.splice(index, 1)
      return true
    }
    for (const i of arr) {
      if (i.children && removeFromArray(i.children)) return true
    }
    return false
  }
  removeFromArray(editableMenus.value)
}
</script>

<style scoped lang="less">
.menu-manage {
  padding: 0;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    
    h2 { margin: 0; font-size: 24px; font-weight: 600; }
    .subtitle { margin: 4px 0 0; color: rgba(0, 0, 0, 0.45); }
  }
  
  .main-card {
    border-radius: 8px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  }
  
  .alert-info {
    margin-bottom: 24px;
  }
  
  .add-root {
    margin-top: 24px;
  }
  
  :deep(.ant-table-wrapper) {
    .ant-table-thead > tr > th {
      background: #fafafa;
      font-weight: 600;
    }
  }
}

.dark, .realdark {
  .menu-manage {
    .page-header {
      h2 { color: rgba(255, 255, 255, 0.85); }
      .subtitle { color: rgba(255, 255, 255, 0.45); }
    }
    
    .main-card {
      background: #141414;
    }
    
    :deep(.ant-table) {
      background: #141414;
      color: rgba(255, 255, 255, 0.85);
      
      .ant-table-thead > tr > th {
        background: #1d1d1d;
        color: rgba(255, 255, 255, 0.85);
        border-bottom: 1px solid #303030;
      }
      
      .ant-table-tbody > tr > td {
        border-bottom: 1px solid #303030;
      }
      
      .ant-table-row:hover > td {
        background: rgba(255, 255, 255, 0.04);
      }
    }
    
    :deep(.ant-input) {
      background: #1d1d1d;
      border-color: #434343;
      color: rgba(255, 255, 255, 0.85);
      
      &:focus {
        border-color: #177ddc;
      }
    }
  }
}
</style>
