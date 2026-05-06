<template>
  <div class="data-source-manager">
    <!-- Header -->
    <div class="header">
      <h1 class="title">数据源管理</h1>
      <div class="actions">
        <el-button type="primary" @click="showAddDialog" icon="Plus">
          添加数据源
        </el-button>
        <el-button type="success" @click="refreshData" icon="Refresh">
          刷新
        </el-button>
      </div>
    </div>

    <!-- Search and Filter -->
    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索数据源名称或代码..."
        clearable
        style="width: 300px; margin-right: 12px;"
      />
      
      <el-select
        v-model="filterCategory"
        placeholder="选择类别"
        clearable
        style="width: 180px; margin-right: 12px;"
      >
        <el-option
          v-for="category in categories"
          :key="category"
          :label="category"
          :value="category"
        />
      </el-select>

      <el-select
        v-model="filterStatus"
        placeholder="状态"
        clearable
        style="width: 120px; margin-right: 12px;"
      >
        <el-option label="启用" value="true" />
        <el-option label="禁用" value="false" />
      </el-select>

      <el-button type="primary" @click="applyFilters" icon="Search">
        搜索
      </el-button>
      <el-button @click="resetFilters" style="margin-left: 8px;">重置</el-button>
    </div>

    <!-- Data Source List -->
    <div class="data-sources-grid">
      <el-card
        v-for="source in filteredSources"
        :key="source.id"
        class="data-source-card"
        shadow="hover"
      >
        <template #header>
          <div class="card-header">
            <div class="source-info">
              <h3 class="source-name">{{ source.source_name }}</h3>
              <span class="source-code">{{ source.source_code }}</span>
            </div>
            <div class="status-actions">
              <el-tag
                :type="source.enabled ? 'success' : 'danger'"
                size="small"
                class="status-tag"
              >
                {{ source.enabled ? '启用' : '禁用' }}
              </el-tag>
              <el-dropdown trigger="click" @command="handleSourceCommand">
                <el-button type="primary" size="small" icon="MoreFilled" />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="edit" icon="Edit">
                      编辑配置
                    </el-dropdown-item>
                    <el-dropdown-item command="toggle" :icon="source.enabled ? 'CircleClose' : 'Check'">
                      {{ source.enabled ? '禁用' : '启用' }}
                    </el-dropdown-item>
                    <el-dropdown-item command="health" icon="Health">
                      健康检查
                    </el-dropdown-item>
                    <el-dropdown-item command="api-keys" icon="Key">
                      API密钥管理
                    </el-dropdown-item>
                    <el-dropdown-item command="rate-limit" icon="Speedometer">
                      限流配置
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" icon="Delete">
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </template>

        <div class="card-content">
          <div class="section">
            <h4>基本信息</h4>
            <div class="info-row">
              <span class="label">类别:</span>
              <span class="value">{{ source.market_categories.join(', ') }}</span>
            </div>
            <div class="info-row">
              <span class="label">层:</span>
              <span class="value">{{ source.layer }}</span>
            </div>
            <div class="info-row">
              <span class="label">负载均衡:</span>
              <span class="value">{{ source.load_balance_strategy }}</span>
            </div>
          </div>

          <div class="section">
            <h4>API连接</h4>
            <div class="info-row">
              <span class="label">基础URL:</span>
              <span class="value">
                {{ source.config_json?.base_url || '未配置' }}
              </span>
            </div>
            <div class="info-row">
              <span class="label">超时:</span>
              <span class="value">
                {{ source.config_json?.timeout_sec || 30 }} 秒
              </span>
            </div>
            <div class="info-row">
              <span class="label">重试:</span>
              <span class="value">
                {{ source.config_json?.retry_count || 5 }} 次
              </span>
            </div>
          </div>

          <div class="section">
            <h4>API密钥</h4>
            <div class="info-row">
              <span class="label">已配置:</span>
              <span class="value">
                {{ source.api_key_configured ? '✓ 已配置' : '✗ 未配置' }}
              </span>
            </div>
            <div class="info-row">
              <span class="label">健康状态:</span>
              <span class="value">
                <el-tag
                  :type="source.health_status === 'healthy' ? 'success' : 'warning'"
                  size="small"
                >
                  {{ source.health_status || '未知' }}
                </el-tag>
              </span>
            </div>
          </div>

          <div class="section">
            <h4>限流配置</h4>
            <div class="info-row">
              <span class="label">策略:</span>
              <span class="value">
                {{ source.rate_limit?.strategy || 'token_bucket' }}
              </span>
            </div>
            <div class="info-row">
              <span class="label">速率:</span>
              <span class="value">
                {{ source.rate_limit?.rate || 60 }}/分钟
              </span>
            </div>
            <div class="info-row">
              <span class="label">突发容量:</span>
              <span class="value">
                {{ source.rate_limit?.burst || source.rate_limit?.rate || 60 }}
              </span>
            </div>
          </div>
        </div>

        <template #footer>
          <div class="card-footer">
            <span class="notes">{{ source.notes || '暂无说明' }}</span>
            <div class="stats">
              <span class="stat">最后更新: {{ formatDate(source.updated_at) }}</span>
            </div>
          </div>
        </template>
      </el-card>
    </div>

    <!-- Pagination -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="totalSources"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- Add/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="70%"
      :before-close="handleClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="120px"
        class="data-source-form"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="数据源代码" prop="source_code">
              <el-input
                v-model="formData.source_code"
                placeholder="如: crypto_ccxt"
                :disabled="isEditing"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="数据源名称" prop="source_name">
              <el-input v-model="formData.source_name" placeholder="如: CCXT 加密货币交易所" />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="层" prop="layer">
              <el-select v-model="formData.layer" placeholder="请选择" style="width: 100%">
                <el-option label="data_source" value="data_source" />
                <el-option label="data_provider" value="data_provider" />
                <el-option label="fundamental" value="fundamental" />
                <el-option label="sentiment" value="sentiment" />
                <el-option label="collector" value="collector" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="市场类别" prop="market_categories">
              <el-select
                v-model="formData.market_categories"
                multiple
                placeholder="请选择"
                style="width: 100%"
              >
                <el-option
                  v-for="category in categories"
                  :key="category"
                  :label="category"
                  :value="category"
                />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="启用状态" prop="enabled">
              <el-switch v-model="formData.enabled" />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="负载均衡策略" prop="load_balance_strategy">
              <el-select v-model="formData.load_balance_strategy" placeholder="请选择" style="width: 100%">
                <el-option label="round_robin" value="round_robin" />
                <el-option label="weighted" value="weighted" />
                <el-option label="health_first" value="health_first" />
                <el-option label="random" value="random" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="24">
            <el-form-item label="API连接配置 (JSON)" prop="config_json">
              <el-input
                v-model="formData.config_json"
                type="textarea"
                rows="6"
                placeholder='{"api_key_env": "CCXT_API_KEY", "base_url": "https://api.coinbase.com/api/v2/", "timeout_sec": 10, "retry_count": 3}'
              />
            </el-form-item>
          </el-col>

          <el-col :span="24">
            <el-form-item label="备注" prop="notes">
              <el-input
                v-model="formData.notes"
                type="textarea"
                rows="3"
                placeholder="数据源使用说明、注意事项等"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">{{ dialogTitle.includes('添加') ? '添加' : '保存' }}</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- API Key Management Dialog -->
    <el-dialog
      v-model="apiKeyDialogVisible"
      title="API 密钥管理"
      width="70%"
      :before-close="handleApiKeyClose"
    >
      <div class="api-key-management">
        <div class="api-key-actions">
          <el-button type="primary" @click="showAddApiKeyDialog" icon="Plus">
            添加密钥
          </el-button>
          <el-button type="success" @click="refreshApiKeys" icon="Refresh">
            刷新
          </el-button>
        </div>

        <el-table
          :data="apiKeys"
          style="width: 100%; margin-top: 16px;"
          stripe
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="key_type" label="类型" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.key_type === 'public' ? 'success' : 'info'" size="small">
                {{ scope.row.key_type === 'public' ? '公共' : '私有' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="key_alias" label="别名" width="180" />
          <el-table-column prop="weight" label="权重" width="80" />
          <el-table-column prop="daily_call_limit" label="日调用限制" width="120" />
          <el-table-column prop="current_daily_calls" label="今日调用" width="120" />
          <el-table-column prop="consecutive_errors" label="连续错误" width="120" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope">
              <el-tag
                :type="scope.row.status === 'active' ? 'success' : 'warning'"
                size="small"
              >
                {{ scope.row.status === 'active' ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="scope">
              <el-button
                size="small"
                type="primary"
                @click="editApiKey(scope.row)"
                icon="Edit"
              >
                编辑
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click="deleteApiKey(scope.row.id)"
                icon="Delete"
                style="margin-left: 8px;"
              >
                删除
              </el-button>
              <el-button
                size="small"
                :type="scope.row.status === 'active' ? 'danger' : 'success'"
                @click="toggleApiKeyStatus(scope.row)"
                icon="SwitchButton"
                style="margin-left: 8px;"
              >
                {{ scope.row.status === 'active' ? '禁用' : '启用' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="apiKeyDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Add API Key Dialog -->
    <el-dialog
      v-model="addApiKeyDialogVisible"
      title="添加 API 密钥"
      width="50%"
      :before-close="handleAddApiKeyClose"
    >
      <el-form
        ref="apiKeyFormRef"
        :model="apiKeyFormData"
        :rules="apiKeyRules"
        label-width="120px"
      >
        <el-form-item label="密钥类型" prop="key_type">
          <el-radio-group v-model="apiKeyFormData.key_type">
            <el-radio label="public">公共密钥</el-radio>
            <el-radio label="private">私有密钥</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="密钥别名" prop="key_alias">
          <el-input v-model="apiKeyFormData.key_alias" placeholder="如: Finnhub API Key #1" />
        </el-form-item>

        <el-form-item label="密钥值" prop="encrypted_key_value">
          <el-input
            v-model="apiKeyFormData.encrypted_key_value"
            type="password"
            placeholder="请输入 API 密钥"
          />
        </el-form-item>

        <el-form-item label="权重" prop="weight">
          <el-input-number
            v-model="apiKeyFormData.weight"
            :min="1"
            :max="100"
            :step="1"
            placeholder="1-100"
          />
        </el-form-item>

        <el-form-item label="日调用限制" prop="daily_call_limit">
          <el-input-number
            v-model="apiKeyFormData.daily_call_limit"
            :min="0"
            :step="10"
            placeholder="0表示不限制"
          />
        </el-form-item>

        <el-form-item label="启用状态" prop="status">
          <el-switch v-model="apiKeyFormData.status" />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addApiKeyDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitApiKeyForm">添加密钥</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Rate Limit Configuration Dialog -->
    <el-dialog
      v-model="rateLimitDialogVisible"
      title="限流配置"
      width="60%"
      :before-close="handleRateLimitClose"
    >
      <el-form
        ref="rateLimitFormRef"
        :model="rateLimitFormData"
        :rules="rateLimitRules"
        label-width="120px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="限流策略" prop="strategy">
              <el-select v-model="rateLimitFormData.strategy" placeholder="请选择" style="width: 100%">
                <el-option label="令牌桶" value="token_bucket" />
                <el-option label="滑动窗口" value="sliding_window" />
                <el-option label="固定窗口" value="fixed_window" />
                <el-option label="自适应" value="adaptive" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="每周期请求数" prop="rate">
              <el-input-number
                v-model="rateLimitFormData.rate"
                :min="1"
                :max="10000"
                :step="1"
                placeholder="1-10000"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="周期长度(秒)" prop="period">
              <el-input-number
                v-model="rateLimitFormData.period"
                :min="1"
                :max="3600"
                :step="1"
                placeholder="1-3600"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="突发容量" prop="burst">
              <el-input-number
                v-model="rateLimitFormData.burst"
                :min="1"
                :max="10000"
                :step="1"
                placeholder="1-10000"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="最大并发数" prop="max_concurrent">
              <el-input-number
                v-model="rateLimitFormData.max_concurrent"
                :min="1"
                :max="100"
                :step="1"
                placeholder="1-100"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="启用自适应" prop="enable_adaptive">
              <el-switch v-model="rateLimitFormData.enable_adaptive" />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="错误降速" prop="reduce_rate_on_error">
              <el-switch v-model="rateLimitFormData.reduce_rate_on_error" />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="错误阈值" prop="error_threshold">
              <el-input-number
                v-model="rateLimitFormData.error_threshold"
                :min="1"
                :max="20"
                :step="1"
                placeholder="1-20"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="优先级" prop="priority">
              <el-input-number
                v-model="rateLimitFormData.priority"
                :min="1"
                :max="100"
                :step="1"
                placeholder="1-100"
              />
            </el-form-item>
          </el-col>

          <el-col :span="24">
            <el-form-item label="备注" prop="notes">
              <el-input
                v-model="rateLimitFormData.notes"
                type="textarea"
                rows="3"
                placeholder="限流配置说明"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="rateLimitDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitRateLimitForm">保存配置</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Health Check Dialog -->
    <el-dialog
      v-model="healthDialogVisible"
      title="健康检查结果"
      width="50%"
      :before-close="handleHealthClose"
    >
      <div class="health-result">
        <div class="health-status">
          <el-tag
            :type="healthResult.status === 'healthy' ? 'success' : 'danger'"
            size="large"
            style="font-size: 16px; padding: 8px 16px; margin-bottom: 16px;"
          >
            {{ healthResult.status === 'healthy' ? '✅ 健康' : '❌ 不健康' }}
          </el-tag>
        </div>
        
        <div class="health-details">
          <div class="detail-row">
            <span class="label">响应时间:</span>
            <span class="value">{{ healthResult.latency_ms || 0 }}ms</span>
          </div>
          <div class="detail-row">
            <span class="label">最后检查:</span>
            <span class="value">{{ formatDate(healthResult.last_check_at) }}</span>
          </div>
          <div class="detail-row" v-if="healthResult.error">
            <span class="label">错误信息:</span>
            <span class="value error-text">{{ healthResult.error }}</span>
          </div>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="healthDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="runHealthCheck" v-if="!healthResult.status">重新检查</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Delete Confirmation Dialog -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="确认删除"
      width="40%"
      :before-close="handleDeleteClose"
    >
      <p>确定要删除数据源 "{{ deleteSourceName }}" 吗？</p>
      <p><strong>注意：</strong>此操作将删除所有相关配置和密钥，无法恢复！</p>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="deleteDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="confirmDelete">确定删除</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute } from 'vue-router'
import { useRouter } from 'vue-router'

// Types
interface DataSource {
  id: number
  source_code: string
  source_name: string
  layer: string
  market_categories: string[]
  enabled: boolean
  load_balance_strategy: string
  config_json: Record<string, any>
  api_key_configured: boolean
  notes: string | null
  health_status?: string
  rate_limit?: Record<string, any>
  updated_at?: string
}

interface ApiKey {
  id: number
  key_type: string
  key_alias: string
  weight: number
  daily_call_limit: number
  current_daily_calls: number
  consecutive_errors: number
  status: string
}

interface HealthResult {
  source_code: string
  status: string
  latency_ms: number
  last_check_at?: string
  error?: string
}

// State
const sources = ref<DataSource[]>([])
const totalSources = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')
const filterCategory = ref('')
const filterStatus = ref('')
const categories = ref([
  'Crypto',
  'USStock',
  'CNStock',
  'HKStock',
  'Forex',
  'Futures',
  'Macro',
  'News',
  'Fundamentals',
  'PredictionMarket',
  'Alternative'
])

// Dialogs
const dialogVisible = ref(false)
const apiKeyDialogVisible = ref(false)
const addApiKeyDialogVisible = ref(false)
const rateLimitDialogVisible = ref(false)
const healthDialogVisible = ref(false)
const deleteDialogVisible = ref(false)

// Forms
const formRef = ref()
const apiKeyFormRef = ref()
const rateLimitFormRef = ref()

const formData = reactive({
  id: 0,
  source_code: '',
  source_name: '',
  layer: 'data_source',
  market_categories: [] as string[],
  enabled: true,
  load_balance_strategy: 'round_robin',
  config_json: '{}',
  notes: ''
})

const apiKeyFormData = reactive({
  key_type: 'public',
  key_alias: '',
  encrypted_key_value: '',
  weight: 1,
  daily_call_limit: 0,
  status: true
})

const rateLimitFormData = reactive({
  strategy: 'token_bucket',
  rate: 60,
  period: 60,
  burst: 60,
  max_concurrent: 10,
  enable_adaptive: false,
  reduce_rate_on_error: true,
  error_threshold: 5,
  priority: 50,
  weight: 1,
  notes: ''
})

const healthResult = reactive({
  source_code: '',
  status: '',
  latency_ms: 0,
  last_check_at: '',
  error: ''
} as HealthResult)

const deleteSourceName = ref('')
const deleteSourceCode = ref('')

// Computed properties
const dialogTitle = computed(() => {
  return isEditing.value ? '编辑数据源' : '添加数据源'
})

const isEditing = computed(() => {
  return formData.id !== 0
})

const filteredSources = computed(() => {
  let result = [...sources.value]
  
  // Search
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(source =>
      source.source_name.toLowerCase().includes(query) ||
      source.source_code.toLowerCase().includes(query) ||
      (source.notes && source.notes.toLowerCase().includes(query))
    )
  }
  
  // Category filter
  if (filterCategory.value) {
    result = result.filter(source =>
      source.market_categories.includes(filterCategory.value)
    )
  }
  
  // Status filter
  if (filterStatus.value !== '') {
    const status = filterStatus.value === 'true'
    result = result.filter(source => source.enabled === status)
  }
  
  return result
})

// Form rules
const rules = {
  source_code: [
    { required: true, message: '数据源代码不能为空', trigger: 'blur' },
    { pattern: /^[a-z_]+$/, message: '只能包含小写字母和下划线', trigger: 'blur' }
  ],
  source_name: [
    { required: true, message: '数据源名称不能为空', trigger: 'blur' }
  ]
}

const apiKeyRules = {
  key_alias: [
    { required: true, message: '密钥别名不能为空', trigger: 'blur' }
  ],
  encrypted_key_value: [
    { required: true, message: 'API密钥不能为空', trigger: 'blur' }
  ]
}

const rateLimitRules = {
  rate: [
    { required: true, message: '请设置每周期请求数', trigger: 'blur' },
    { type: 'number', message: '必须是数字', trigger: 'blur' }
  ],
  period: [
    { required: true, message: '请设置周期长度', trigger: 'blur' },
    { type: 'number', message: '必须是数字', trigger: 'blur' }
  ]
}

// API Keys state
const apiKeys = ref<ApiKey[]>([])
const selectedSource = ref<DataSource | null>(null)

// Methods
const formatDate = (dateString: string | undefined): string => {
  if (!dateString) return '未更新'
  const date = new Date(dateString)
  return date.toLocaleString()
}

const refreshData = () => {
  loadData()
}

const loadData = async () => {
  try {
    const response = await fetch('/api/data-sources/')
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const data = await response.json()
    sources.value = data.data_sources
    totalSources.value = data.total
  } catch (error) {
    ElMessage.error(`加载数据源失败: ${(error as Error).message}`)
  }
}

const applyFilters = () => {
  // Filters are applied in computed property
}

const resetFilters = () => {
  searchQuery.value = ''
  filterCategory.value = ''
  filterStatus.value = ''
}

const showAddDialog = () => {
  formData.id = 0
  formData.source_code = ''
  formData.source_name = ''
  formData.layer = 'data_source'
  formData.market_categories = []
  formData.enabled = true
  formData.load_balance_strategy = 'round_robin'
  formData.config_json = '{}'
  formData.notes = ''
  dialogVisible.value = true
}

const handleSourceCommand = (command: string) => {
  switch (command) {
    case 'edit':
      editSource()
      break
    case 'toggle':
      toggleSource()
      break
    case 'health':
      checkHealth()
      break
    case 'api-keys':
      manageApiKeys()
      break
    case 'rate-limit':
      configureRateLimit()
      break
    case 'delete':
      confirmDeleteSource()
      break
  }
}

const editSource = () => {
  // Implementation will be added later
}

const toggleSource = async () => {
  if (!selectedSource.value) return
  
  try {
    const response = await fetch(`/api/data-sources/${selectedSource.value.source_code}/toggle`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        enabled: !selectedSource.value.enabled
      })
    })
    
    if (response.ok) {
      ElMessage.success(
        `数据源已${selectedSource.value.enabled ? '禁用' : '启用'}`
      )
      loadData()
      // Update local state
      const index = sources.value.findIndex(s => s.source_code === selectedSource.value!.source_code)
      if (index !== -1) {
        sources.value[index].enabled = !selectedSource.value.enabled
      }
    } else {
      throw new Error('切换状态失败')
    }
  } catch (error) {
    ElMessage.error(`切换状态失败: ${(error as Error).message}`)
  }
}

const checkHealth = async () => {
  if (!selectedSource.value) return
  
  try {
    const response = await fetch(`/api/data-sources/health/${selectedSource.value.source_code}`, {
      method: 'POST'
    })
    
    if (response.ok) {
      const data = await response.json()
      Object.assign(healthResult, data)
      healthDialogVisible.value = true
      // Update local health status
      const index = sources.value.findIndex(s => s.source_code === selectedSource.value!.source_code)
      if (index !== -1) {
        sources.value[index].health_status = data.status
      }
    } else {
      throw new Error('健康检查失败')
    }
  } catch (error) {
    ElMessage.error(`健康检查失败: ${(error as Error).message}`)
  }
}

const runHealthCheck = async () => {
  if (!healthResult.source_code) return
  
  try {
    const response = await fetch(`/api/data-sources/health/${healthResult.source_code}`, {
      method: 'POST'
    })
    
    if (response.ok) {
      const data = await response.json()
      Object.assign(healthResult, data)
      // Update local health status
      const index = sources.value.findIndex(s => s.source_code === data.source_code)
      if (index !== -1) {
        sources.value[index].health_status = data.status
      }
    } else {
      throw new Error('健康检查失败')
    }
  } catch (error) {
    ElMessage.error(`健康检查失败: ${(error as Error).message}`)
  }
}

const manageApiKeys = () => {
  // Implementation will be added later
}

const configureRateLimit = () => {
  // Implementation will be added later
}

const confirmDeleteSource = () => {
  if (!selectedSource.value) return
  deleteSourceName.value = selectedSource.value.source_name
  deleteSourceCode.value = selectedSource.value.source_code
  deleteDialogVisible.value = true
}

const confirmDelete = async () => {
  try {
    const response = await fetch(`/api/data-sources/${deleteSourceCode.value}`, {
      method: 'DELETE'
    })
    
    if (response.ok) {
      ElMessage.success('数据源删除成功')
      loadData()
      deleteDialogVisible.value = false
      deleteSourceName.value = ''
      deleteSourceCode.value = ''
    } else {
      throw new Error('删除失败')
    }
  } catch (error) {
    ElMessage.error(`删除失败: ${(error as Error).message}`)
  }
}

const submitForm = () => {
  // Implementation will be added later
}

const submitApiKeyForm = () => {
  // Implementation will be added later
}

const submitRateLimitForm = () => {
  // Implementation will be added later
}

const handleClose = () => {
  dialogVisible.value = false
}

const handleApiKeyClose = () => {
  apiKeyDialogVisible.value = false
}

const handleAddApiKeyClose = () => {
  addApiKeyDialogVisible.value = false
}

const handleRateLimitClose = () => {
  rateLimitDialogVisible.value = false
}

const handleHealthClose = () => {
  healthDialogVisible.value = false
}

const handleDeleteClose = () => {
  deleteDialogVisible.value = false
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
}

// Lifecycle hooks
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.data-source-manager {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.title {
  margin: 0;
  color: #333;
}

.search-bar {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.data-sources-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)));
  gap: 20px;
}

.data-source-card {
  transition: all 0.3s ease;
}

.data-source-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.source-info {
  display: flex;
  flex-direction: column;
}

.source-name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.source-code {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.status-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-tag {
  margin-right: 8px;
}

.card-content {
  padding: 16px 0;
}

.section {
  margin-bottom: 16px;
}

.section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #666;
}

.info-row {
  display: flex;
  margin-bottom: 8px;
  align-items: center;
}

.label {
  font-weight: 500;
  color: #666;
  min-width: 80px;
}

.value {
  flex: 1;
  color: #333;
}

.error-text {
  color: #e6a23c;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #eee;
}

.notes {
  color: #666;
  font-size: 12px;
}

.stats {
  display: flex;
  gap: 16px;
}

.stat {
  font-size: 12px;
  color: #999;
}

.pagination {
  margin-top: 24px;
  text-align: right;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.health-result {
  padding: 20px;
}

.health-status {
  text-align: center;
  margin-bottom: 20px;
}

.health-details {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 4px;
}

.detail-row {
  display: flex;
  margin-bottom: 12px;
  align-items: center;
}

.detail-row .label {
  font-weight: 500;
  color: #666;
  min-width: 100px;
}

.detail-row .value {
  flex: 1;
  color: #333;
}

.api-key-management {
  padding: 20px;
}

.api-key-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
</style>