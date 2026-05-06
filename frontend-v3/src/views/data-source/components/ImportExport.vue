<template>
  <div class="import-export">
    <div class="import-header">
      <h3>导入/导出配置</h3>
      <a-space>
        <a-button type="primary" @click="showImportModal">
          <template #icon><UploadOutlined /></template>
          导入配置
        </a-button>
        <a-button @click="exportConfigs">
          <template #icon><DownloadOutlined /></template>
          导出配置
        </a-button>
        <a-button @click="loadTemplates">
          <template #icon><FileTextOutlined /></template>
          模板库
        </a-button>
      </a-space>
    </div>

    <!-- 导入进度 -->
    <a-alert
      v-if="importing"
      :message="`正在导入 ${importedCount}/${totalImportCount} 个配置...`"
      type="info"
      show-icon
      style="margin-bottom: 16px;"
    >
      <template #description>
        <a-progress :percent="importProgress" status="active" />
      </template>
    </a-alert>

    <!-- 导入历史 -->
    <a-card title="导入历史" :bordered="false" style="margin-top: 24px;">
      <a-table
        :columns="historyColumns"
        :data-source="importHistory"
        :pagination="false"
        size="middle"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-badge
              :status="record.status === 'success' ? 'success' : 'error'"
              :text="record.status === 'success' ? '成功' : '失败'"
            />
          </template>

          <template v-if="column.key === 'count'">
            {{ record.success_count }} / {{ record.total_count }}
          </template>

          <template v-if="column.key === 'created_at'">
            {{ formatTime(record.created_at) }}
          </template>

          <template v-if="column.key === 'action'">
            <a-button 
              type="link" 
              size="small" 
              @click="viewImportDetail(record)"
            >
              查看详情
            </a-button>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 导入对话框 -->
    <a-modal
      v-model:open="importModalVisible"
      title="导入数据源配置"
      width="700px"
      :footer="null"
    >
      <a-steps :current="importStep" style="margin-bottom: 24px;">
        <a-step title="选择文件" />
        <a-step title="预览配置" />
        <a-step title="确认导入" />
      </a-steps>

      <!-- 步骤1: 选择文件 -->
      <div v-if="importStep === 0">
        <a-upload-dragger
          v-model:file-list="fileList"
          :before-upload="beforeUpload"
          :custom-request="handleFileUpload"
          :max-count="1"
          accept=".json,.csv,.yaml,.yml"
        >
          <p class="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p class="ant-upload-text">点击或拖拽文件到此区域</p>
          <p class="ant-upload-hint">
            支持 JSON、CSV、YAML 格式，文件大小不超过 10MB
          </p>
        </a-upload-dragger>

        <a-divider>或从模板导入</a-divider>

        <a-row :gutter="16">
          <a-col :span="8" v-for="template in templates" :key="template.code">
            <a-card
              hoverable
              size="small"
              @click="selectTemplate(template)"
              style="margin-bottom: 16px; cursor: pointer;"
            >
              <template #title>
                <a-space>
                  <component :is="template.icon" />
                  <span>{{ template.name }}</span>
                </a-space>
              </template>
              <p style="color: #666; font-size: 12px;">{{ template.description }}</p>
            </a-card>
          </a-col>
        </a-row>
      </div>

      <!-- 步骤2: 预览配置 -->
      <div v-if="importStep === 1">
        <a-alert
          :message="`已解析 ${parsedConfigs.length} 个数据源配置`"
          type="info"
          show-icon
          style="margin-bottom: 16px;"
        />

        <a-table
          :columns="previewColumns"
          :data-source="parsedConfigs"
          :pagination="false"
          size="small"
          :row-selection="{
            selectedRowKeys: selectedKeys,
            onChange: onSelectionChange
          }"
          row-key="source_code"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-badge
                :status="record.valid ? 'success' : 'error'"
                :text="record.valid ? '有效' : '无效'"
              />
            </template>

            <template v-if="column.key === 'categories'">
              <a-tag v-for="cat in (record.market_categories || [])" :key="cat" color="blue">
                {{ cat }}
              </a-tag>
            </template>
          </template>
        </a-table>

        <a-space style="margin-top: 16px;">
          <a-button @click="importStep = 0">上一步</a-button>
          <a-button type="primary" @click="importStep = 2" :disabled="selectedKeys.length === 0">
            下一步
          </a-button>
        </a-space>
      </div>

      <!-- 步骤3: 确认导入 -->
      <div v-if="importStep === 2">
        <a-alert
          :message="`将导入 ${selectedKeys.length} 个数据源配置`"
          type="warning"
          show-icon
          style="margin-bottom: 16px;"
        />

        <a-form layout="vertical">
          <a-form-item label="导入模式">
            <a-radio-group v-model:value="importMode">
              <a-radio value="create">仅创建新配置</a-radio>
              <a-radio value="update">更新已存在的配置</a-radio>
              <a-radio value="upsert">创建或更新（推荐）</a-radio>
            </a-radio-group>
          </a-form-item>

          <a-form-item label="启用导入的数据源">
            <a-switch v-model:checked="enableAfterImport" />
          </a-form-item>

          <a-form-item label="同时导入API密钥">
            <a-switch v-model:checked="importApiKeys" />
          </a-form-item>

          <a-form-item label="同时导入限流配置">
            <a-switch v-model:checked="importRateLimits" />
          </a-form-item>
        </a-form>

        <a-space style="margin-top: 16px;">
          <a-button @click="importStep = 1">上一步</a-button>
          <a-button type="primary" @click="executeImport" :loading="importing">
            开始导入
          </a-button>
        </a-space>
      </div>
    </a-modal>

    <!-- 导入详情对话框 -->
    <a-modal
      v-model:open="detailModalVisible"
      title="导入详情"
      width="800px"
      :footer="null"
    >
      <a-descriptions :column="2" bordered v-if="selectedImport">
        <a-descriptions-item label="导入时间">
          {{ formatTime(selectedImport.created_at) }}
        </a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-badge
            :status="selectedImport.status === 'success' ? 'success' : 'error'"
            :text="selectedImport.status === 'success' ? '成功' : '失败'"
          />
        </a-descriptions-item>
        <a-descriptions-item label="总数">
          {{ selectedImport.total_count }}
        </a-descriptions-item>
        <a-descriptions-item label="成功">
          {{ selectedImport.success_count }}
        </a-descriptions-item>
        <a-descriptions-item label="失败">
          {{ selectedImport.failed_count }}
        </a-descriptions-item>
        <a-descriptions-item label="文件类型">
          {{ selectedImport.file_type }}
        </a-descriptions-item>
      </a-descriptions>

      <a-divider>导入结果详情</a-divider>

      <a-table
        :columns="detailColumns"
        :data-source="selectedImport?.details || []"
        :pagination="false"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 'success' ? 'green' : 'red'">
              {{ record.status === 'success' ? '成功' : '失败' }}
            </a-tag>
          </template>
        </template>
      </a-table>
    </a-modal>

    <!-- 模板库对话框 -->
    <a-modal
      v-model:open="templateModalVisible"
      title="数据源模板库"
      width="900px"
      :footer="null"
    >
      <a-row :gutter="16">
        <a-col :span="12" v-for="template in allTemplates" :key="template.code">
          <a-card
            hoverable
            @click="useTemplate(template)"
            style="margin-bottom: 16px; cursor: pointer;"
          >
            <template #title>
              <a-space>
                <component :is="template.icon" />
                <span>{{ template.name }}</span>
              </a-space>
            </template>
            <p style="color: #666;">{{ template.description }}</p>
            <a-divider style="margin: 12px 0;" />
            <a-descriptions :column="1" size="small">
              <a-descriptions-item label="类别">
                <a-tag v-for="cat in template.categories" :key="cat" color="blue">
                  {{ cat }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="需要API密钥">
                {{ template.requires_api_key ? '是' : '否' }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>
      </a-row>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  UploadOutlined,
  DownloadOutlined,
  FileTextOutlined,
  InboxOutlined,
  DatabaseOutlined,
  CloudServerOutlined,
  SearchOutlined
} from '@ant-design/icons-vue'
import { getDataSources, createDataSource } from '@/api/data-source'

const importing = ref(false)
const importModalVisible = ref(false)
importStep = ref(0)
const importMode = ref('upsert')
const enableAfterImport = ref(true)
const importApiKeys = ref(false)
const importRateLimits = ref(false)

const fileList = ref<any[]>([])
const parsedConfigs = ref<any[]>([])
const selectedKeys = ref<string[]>([])
const importedCount = ref(0)
const totalImportCount = ref(0)

const importHistory = ref<any[]>([])
const detailModalVisible = ref(false)
const selectedImport = ref<any>(null)

const templateModalVisible = ref(false)

const historyColumns = [
  { title: '导入时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: '文件类型', dataIndex: 'file_type', width: 100 },
  { title: '导入数量', dataIndex: 'count', key: 'count', width: 120 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '操作', key: 'action', width: 120 }
]

const previewColumns = [
  { title: '数据源代码', dataIndex: 'source_code', width: 180 },
  { title: '数据源名称', dataIndex: 'source_name', width: 200 },
  { title: '类别', dataIndex: 'categories', key: 'categories' },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 }
]

const detailColumns = [
  { title: '数据源代码', dataIndex: 'source_code', width: 180 },
  { title: '数据源名称', dataIndex: 'source_name', width: 200 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '错误信息', dataIndex: 'error', ellipsis: true }
]

const importProgress = computed(() => {
  if (totalImportCount.value === 0) return 0
  return Math.round((importedCount.value / totalImportCount.value) * 100)
})

const templates = [
  {
    code: 'crypto',
    name: '加密货币数据源',
    description: 'CCXT、CoinGecko等加密货币数据源模板',
    icon: CloudServerOutlined
  },
  {
    code: 'us_stock',
    name: '美股数据源',
    description: 'yfinance、Finnhub等美股数据源模板',
    icon: DatabaseOutlined
  },
  {
    code: 'search',
    name: '搜索引擎数据源',
    description: 'Google、Baidu、Bing等搜索引擎API模板',
    icon: SearchOutlined
  }
]

const allTemplates = [
  ...templates,
  {
    code: 'cn_stock',
    name: 'A股数据源',
    description: 'AKShare、Tushare等A股数据源模板',
    categories: ['CNStock'],
    requires_api_key: true,
    icon: DatabaseOutlined
  },
  {
    code: 'macro',
    name: '宏观经济数据源',
    description: 'FRED、IMF、OECD等宏观经济数据模板',
    categories: ['Macro'],
    requires_api_key: false,
    icon: DatabaseOutlined
  },
  {
    code: 'news',
    name: '新闻数据源',
    description: 'NewsAPI、Google News等新闻数据模板',
    categories: ['News'],
    requires_api_key: true,
    icon: DatabaseOutlined
  }
]

const showImportModal = () => {
  importStep.value = 0
  fileList.value = []
  parsedConfigs.value = []
  selectedKeys.value = []
  importModalVisible.value = true
}

const beforeUpload = (file: File) => {
  const isValidType = ['application/json', 'text/csv', 'text/yaml', 'application/x-yaml'].includes(file.type)
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isValidType) {
    message.error('只支持 JSON、CSV、YAML 格式文件')
    return false
  }
  if (!isLt10M) {
    message.error('文件大小不能超过 10MB')
    return false
  }
  return true
}

const handleFileUpload = async (options: any) => {
  const { file } = options
  const reader = new FileReader()

  reader.onload = (e) => {
    try {
      const content = e.target?.result as string
      let configs: any[] = []

      if (file.name.endsWith('.json')) {
        configs = JSON.parse(content)
      } else if (file.name.endsWith('.csv')) {
        configs = parseCSV(content)
      } else if (file.name.endsWith('.yaml') || file.name.endsWith('.yml')) {
        // 需要 yaml 解析库
        message.warning('YAML 解析需要安装 js-yaml 库')
        return
      }

      if (!Array.isArray(configs)) {
        configs = [configs]
      }

      parsedConfigs.value = configs.map((config: any) => ({
        ...config,
        valid: validateConfig(config)
      }))

      importStep.value = 1
      message.success(`成功解析 ${configs.length} 个配置`)
    } catch (error: any) {
      message.error(`文件解析失败: ${error.message}`)
    }
  }

  reader.readAsText(file)
}

const parseCSV = (csv: string): any[] => {
  const lines = csv.split('\n')
  const headers = lines[0].split(',').map(h => h.trim())
  const result: any[] = []

  for (let i = 1; i < lines.length; i++) {
    if (!lines[i].trim()) continue
    const values = lines[i].split(',').map(v => v.trim())
    const obj: any = {}
    headers.forEach((header, index) => {
      obj[header] = values[index]
    })
    result.push(obj)
  }

  return result
}

const validateConfig = (config: any): boolean => {
  return !!(config.source_code && config.source_name && config.layer)
}

const onSelectionChange = (keys: string[]) => {
  selectedKeys.value = keys
}

const selectTemplate = (template: any) => {
  // 加载模板配置
  const templateConfig = getTemplateConfig(template.code)
  parsedConfigs.value = templateConfig.map((config: any) => ({
    ...config,
    valid: true
  }))
  importStep.value = 1
  message.success('模板加载成功')
}

const getTemplateConfig = (code: string): any[] => {
  const templates: Record<string, any[]> = {
    crypto: [
      {
        source_code: 'crypto_ccxt',
        source_name: 'CCXT 加密货币交易所',
        layer: 'data_source',
        market_categories: ['Crypto'],
        enabled: true,
        load_balance_strategy: 'round_robin',
        config_json: {
          base_url: 'https://api.coinbase.com',
          timeout_sec: 10,
          retry_count: 3
        }
      }
    ],
    us_stock: [
      {
        source_code: 'us_stock_yfinance',
        source_name: 'Yahoo Finance',
        layer: 'data_source',
        market_categories: ['USStock'],
        enabled: true,
        load_balance_strategy: 'round_robin',
        config_json: {
          timeout_sec: 15,
          retry_count: 3
        }
      }
    ],
    search: [
      {
        source_code: 'search_google',
        source_name: 'Google Search API',
        layer: 'data_source',
        market_categories: ['News', 'Alternative'],
        enabled: true,
        load_balance_strategy: 'round_robin',
        config_json: {
          base_url: 'https://www.googleapis.com/customsearch/v1',
          timeout_sec: 10,
          rate_limit_per_min: 100
        }
      }
    ]
  }

  return templates[code] || []
}

const executeImport = async () => {
  importing.value = true
  importedCount.value = 0
  totalImportCount.value = selectedKeys.value.length

  const selectedConfigs = parsedConfigs.value.filter(
    (c: any) => selectedKeys.value.includes(c.source_code)
  )

  const details: any[] = []

  try {
    for (const config of selectedConfigs) {
      try {
        await createDataSource({
          source_code: config.source_code,
          source_name: config.source_name,
          layer: config.layer,
          market_categories: config.market_categories || [],
          enabled: enableAfterImport.value,
          load_balance_strategy: config.load_balance_strategy || 'round_robin',
          config_json: config.config_json || {},
          notes: config.notes
        })

        details.push({
          source_code: config.source_code,
          source_name: config.source_name,
          status: 'success'
        })
      } catch (error: any) {
        details.push({
          source_code: config.source_code,
          source_name: config.source_name,
          status: 'failed',
          error: error.message
        })
      } finally {
        importedCount.value++
      }
    }

    // 保存导入历史
    importHistory.value.unshift({
      created_at: new Date().toISOString(),
      file_type: 'template',
      total_count: selectedConfigs.length,
      success_count: details.filter(d => d.status === 'success').length,
      failed_count: details.filter(d => d.status === 'failed').length,
      status: details.some(d => d.status === 'failed') ? 'partial' : 'success',
      details
    })

    message.success('导入完成')
    importModalVisible.value = false
  } catch (error) {
    message.error('导入失败')
  } finally {
    importing.value = false
  }
}

const exportConfigs = async () => {
  try {
    const res = await getDataSources({})
    if (res && res.data_sources) {
      const dataStr = JSON.stringify(res.data_sources, null, 2)
      const blob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `data-sources-${new Date().toISOString().split('T')[0]}.json`
      link.click()
      URL.revokeObjectURL(url)
      message.success('导出成功')
    }
  } catch (error) {
    message.error('导出失败')
  }
}

const loadTemplates = () => {
  templateModalVisible.value = true
}

const useTemplate = (template: any) => {
  templateModalVisible.value = false
  showImportModal()
  selectTemplate(template)
}

const viewImportDetail = (record: any) => {
  selectedImport.value = record
  detailModalVisible.value = true
}

const formatTime = (timeStr: string): string => {
  const date = new Date(timeStr)
  return date.toLocaleString()
}

onMounted(() => {
  // 加载导入历史（从 localStorage）
  const history = localStorage.getItem('import_history')
  if (history) {
    importHistory.value = JSON.parse(history)
  }
})
</script>

<style scoped lang="less">
.import-export {
  .import-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;

    h3 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
    }
  }
}
</style>
