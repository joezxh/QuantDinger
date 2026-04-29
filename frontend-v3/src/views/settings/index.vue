<template>
  <div class="settings-page">
    <div class="settings-header">
      <h2 class="page-title">
        <SettingOutlined />
        <span>{{ t('settings.title') }}</span>
      </h2>
      <p class="page-desc">{{ t('settings.subtitle') }}</p>
    </div>

    <!-- 重启提示 -->
    <a-alert
      v-if="showRestartTip"
      class="restart-alert"
      type="warning"
      showIcon
      closable
      @close="showRestartTip = false"
    >
      <template #message>
        <span>{{ t('settings.restartRequired') }}</span>
        <a-button type="link" size="small" @click="copyRestartCommand">{{ t('settings.copyRestartCmd') }}</a-button>
      </template>
    </a-alert>

    <a-spin :spinning="loading">
      <div class="settings-content">
        <a-collapse v-model:activeKey="activeKeys" :bordered="false" class="settings-collapse">
          <a-collapse-panel
            v-for="(group, groupKey) in sortedSchema"
            :key="groupKey"
          >
            <template #header>
              <span class="panel-header">
                <component :is="getGroupIcon(groupKey)" class="panel-icon" />
                <span class="panel-title">{{ group.title || groupKey }}</span>
              </span>
            </template>

            <div class="settings-form">
              <a-row :gutter="24">
                <a-col
                  v-for="item in group.items"
                  :key="item.key"
                  :xs="24"
                  :sm="24"
                  :md="12"
                  :lg="12"
                  v-show="shouldShowItem(item, groupKey)"
                >
                  <div class="form-item">
                    <div class="form-label">
                      <span class="label-text">{{ item.label }}</span>
                      <a-tooltip v-if="item.description" placement="top">
                        <template #title>{{ item.description }}</template>
                        <QuestionCircleOutlined class="help-icon" />
                      </a-tooltip>
                      <a
                        v-if="item.link"
                        :href="item.link"
                        target="_blank"
                        rel="noopener noreferrer"
                        class="api-link"
                      >
                        <LinkOutlined />
                        {{ item.link_text || t('settings.getApiLink') }}
                      </a>
                    </div>

                    <!-- 文本输入 -->
                    <a-input
                      v-if="item.type === 'text'"
                      v-model:value="formValues[getItemKey(groupKey, item)]"
                      :placeholder="item.default || t('settings.pleaseInput')"
                      allow-clear
                    />

                    <!-- 密码输入 -->
                    <a-input-password
                      v-else-if="item.type === 'password'"
                      v-model:value="formValues[getItemKey(groupKey, item)]"
                      :placeholder="t('common.pleaseInputKey')"
                      allow-clear
                    />

                    <!-- 数字输入 -->
                    <a-input-number
                      v-else-if="item.type === 'number'"
                      v-model:value="formValues[getItemKey(groupKey, item)]"
                      :placeholder="item.default || t('settings.pleaseInput')"
                      style="width: 100%"
                    />

                    <!-- 布尔开关 -->
                    <a-switch
                      v-else-if="item.type === 'boolean'"
                      v-model:checked="formValues[getItemKey(groupKey, item)]"
                    />

                    <!-- 下拉选择 -->
                    <a-select
                      v-else-if="item.type === 'select'"
                      v-model:value="formValues[getItemKey(groupKey, item)]"
                      :placeholder="item.default || t('settings.pleaseSelect')"
                    >
                      <a-select-option
                        v-for="opt in getSelectOptions(item)"
                        :key="opt.value"
                        :value="opt.value"
                      >
                        {{ opt.label }}
                      </a-select-option>
                    </a-select>

                    <!-- 文本域 -->
                    <a-textarea
                      v-else-if="item.type === 'textarea'"
                      v-model:value="formValues[getItemKey(groupKey, item)]"
                      :rows="3"
                      :placeholder="item.default || t('settings.pleaseInput')"
                    />

                    <div class="field-default" v-if="item.default && item.type !== 'boolean' && item.type !== 'password'">
                      {{ t('settings.defaultLabel') }}: {{ item.default }}
                    </div>
                  </div>
                </a-col>
              </a-row>
            </div>
          </a-collapse-panel>
        </a-collapse>
      </div>
    </a-spin>

    <div class="settings-footer">
      <a-button @click="handleReset" :disabled="saving">
        <UndoOutlined />
        {{ t('common.reset') }}
      </a-button>
      <a-button type="primary" @click="handleSave" :loading="saving">
        <SaveOutlined />
        {{ t('common.save') }}
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import {
  SettingOutlined,
  QuestionCircleOutlined,
  LinkOutlined,
  UndoOutlined,
  SaveOutlined,
  LockOutlined,
  MailOutlined,
  PhoneOutlined,
  GlobalOutlined,
  AppstoreOutlined,
  RobotOutlined,
  StockOutlined,
  DatabaseOutlined,
  SearchOutlined,
  ExperimentOutlined,
  SafetyOutlined,
  DollarOutlined,
} from '@ant-design/icons-vue'
import { getSettingsSchema, getSettingsValues, saveSettings } from '@/api/settings'

interface SettingItem {
  key: string
  label: string
  type: string
  description?: string
  default?: string
  options?: any[]
  link?: string
  link_text?: string
  group?: string
}

interface SettingGroup {
  title: string
  icon?: string
  order: number
  items: SettingItem[]
}

const { t } = useI18n()
const loading = ref(false)
const saving = ref(false)
const schema = reactive<Record<string, SettingGroup>>({})
const values = reactive<Record<string, Record<string, any>>>({})
const activeKeys = ref<string[]>([])
const showRestartTip = ref(false)
const currentAiProvider = ref('openai-compatible')

const formValues = reactive<Record<string, any>>({})

const sortedSchema = computed(() => {
  const entries = Object.entries(schema)
  entries.sort((a, b) => {
    const orderA = a[1].order || 999
    const orderB = b[1].order || 999
    return orderA - orderB
  })
  const sorted: Record<string, SettingGroup> = {}
  for (const [key, value] of entries) {
    sorted[key] = value
  }
  return sorted
})

function getIconComponent(type: string) {
  const icons: Record<string, any> = {
    lock: LockOutlined,
    mail: MailOutlined,
    phone: PhoneOutlined,
    global: GlobalOutlined,
    appstore: AppstoreOutlined,
    robot: RobotOutlined,
    stock: StockOutlined,
    database: DatabaseOutlined,
    search: SearchOutlined,
    experiment: ExperimentOutlined,
    safety: SafetyOutlined,
    dollar: DollarOutlined,
  }
  return icons[type] || SettingOutlined
}

function getGroupIcon(groupKey: string) {
  const icons: Record<string, string> = {
    auth: 'lock',
    email: 'mail',
    sms: 'phone',
    network: 'global',
    app: 'appstore',
    ai: 'robot',
    trading: 'stock',
    data_source: 'database',
    search: 'search',
    agent: 'experiment',
    security: 'safety',
    billing: 'dollar'
  }
  const iconType = icons[groupKey] || 'setting'
  return getIconComponent(iconType)
}

function getItemKey(groupKey: string, item: SettingItem): string {
  return `${groupKey}.${item.key}`
}

function getSelectOptions(item: SettingItem) {
  const options = item.options || []
  return options.map((opt: any) => {
    if (typeof opt === 'object') {
      return { value: String(opt.value), label: String(opt.label || opt.value) }
    }
    return { value: String(opt), label: String(opt) }
  }).filter((o: any) => o.value !== '')
}

function shouldShowItem(item: SettingItem, groupKey: string): boolean {
  if (groupKey !== 'ai') return true
  if (item.key === 'LLM_PROVIDER') return true
  if (!item.group) return true
  return item.group === currentAiProvider.value
}

async function loadSettings() {
  loading.value = true
  try {
    const [schemaRes, valuesRes] = await Promise.all([
      getSettingsSchema(),
      getSettingsValues()
    ])

    if (schemaRes.code === 1) {
      Object.assign(schema, schemaRes.data)
      activeKeys.value = Object.keys(schemaRes.data)
    }

    if (valuesRes.code === 1) {
      Object.assign(values, valuesRes.data)
      // 初始化表单值
      for (const [groupKey, groupValues] of Object.entries(valuesRes.data)) {
        if (schema[groupKey]) {
          for (const item of schema[groupKey].items) {
            const key = getItemKey(groupKey, item)
            let value = (groupValues as any)[item.key]
            if (item.type === 'boolean') {
              value = value === 'True' || value === 'true' || value === true
            } else if (item.type === 'number' && value) {
              value = parseFloat(value)
            }
            formValues[key] = value || ''
          }
        }
      }
      // 初始化当前AI provider
      const aiValues = valuesRes.data.ai || {}
      currentAiProvider.value = (aiValues as any).LLM_PROVIDER || 'openai-compatible'
    }
  } catch (error) {
    message.error(t('settings.loadFailed'))
  } finally {
    loading.value = false
  }
}

function handleReset() {
  loadSettings()
  showRestartTip.value = false
}

async function handleSave() {
  saving.value = true
  try {
    // 按组整理数据
    const data: Record<string, Record<string, any>> = {}
    for (const groupKey of Object.keys(schema)) {
      data[groupKey] = {}
      const group = schema[groupKey]
      for (const item of group.items) {
        const key = getItemKey(groupKey, item)
        if (key in formValues) {
          let value = formValues[key]
          if (item.type === 'boolean') {
            value = value ? 'True' : 'False'
          }
          data[groupKey][item.key] = value
        }
      }
    }

    const res = await saveSettings(data)
    if (res.code === 1) {
      message.success(res.msg || t('common.saveSuccess'))
      if (res.data && res.data.requires_restart) {
        showRestartTip.value = true
      }
      loadSettings()
    } else {
      message.error(res.msg || t('common.saveFailed'))
    }
  } catch (error: any) {
    message.error(t('common.saveFailed') + ': ' + error.message)
  } finally {
    saving.value = false
  }
}

function copyRestartCommand() {
  const cmd = 'cd backend_api_python && py run.py'
  navigator.clipboard.writeText(cmd).then(() => {
    message.success(t('common.copied'))
  }).catch(() => {
    message.error(t('common.copyFailed'))
  })
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-page {
  padding: 24px;
  min-height: calc(100vh - 120px);
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

.restart-alert {
  margin-bottom: 16px;
  border-radius: 8px;
}

.settings-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: #1e3a5f;
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title .anticon {
  font-size: 28px;
  color: #1890ff;
}

.page-desc {
  color: #64748b;
  font-size: 14px;
  margin: 0;
}

.settings-content {
  margin-bottom: 80px;
}

.settings-collapse {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-icon {
  font-size: 18px;
  color: #1890ff;
}

.panel-title {
  font-size: 16px;
  font-weight: 700;
  color: #1e3a5f;
}

.settings-form {
  padding: 16px 0;
}

.form-item {
  margin-bottom: 20px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.label-text {
  font-weight: 600;
  color: #1e3a5f;
}

.help-icon {
  color: #999;
  cursor: pointer;
}

.api-link {
  margin-left: auto;
  font-size: 12px;
  color: #1890ff;
  text-decoration: none;
}

.api-link:hover {
  color: #40a9ff;
}

.field-default {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.settings-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px 24px;
  background: #fff;
  border-top: 1px solid #e8e8e8;
  display: flex;
  justify-content: center;
  gap: 12px;
  z-index: 100;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
}
</style>
