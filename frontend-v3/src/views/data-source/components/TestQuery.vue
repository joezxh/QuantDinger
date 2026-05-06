<template>
  <div class="test-query">
    <div class="test-header">
      <h3>测试查询</h3>
      <a-space>
        <a-button 
          type="primary" 
          @click="testAllSources" 
          :loading="testingAll"
          :disabled="testingAll"
        >
          <template #icon><ThunderboltOutlined /></template>
          批量测试所有数据源
        </a-button>
        <a-button @click="loadData" :loading="loading">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
      </a-space>
    </div>

    <!-- 测试进度 -->
    <a-alert
      v-if="testingAll"
      :message="`正在测试 ${testedCount}/${totalSources} 个数据源...`"
      type="info"
      show-icon
      style="margin-bottom: 16px;"
    >
      <template #description>
        <a-progress :percent="progressPercent" status="active" />
      </template>
    </a-alert>

    <!-- 测试结果概览 -->
    <a-row :gutter="16" style="margin-bottom: 24px;">
      <a-col :span="6">
        <a-card :bordered="false" class="stat-card">
          <a-statistic
            title="总数据源"
            :value="totalSources"
            :value-style="{ fontSize: '24px' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false" class="stat-card">
          <a-statistic
            title="测试成功"
            :value="successCount"
            :value-style="{ color: '#3f8600', fontSize: '24px' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false" class="stat-card">
          <a-statistic
            title="测试失败"
            :value="failCount"
            :value-style="{ color: '#cf1322', fontSize: '24px' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false" class="stat-card">
          <a-statistic
            title="平均响应时间"
            :value="avgLatency"
            :precision="0"
            suffix="ms"
            :value-style="{ fontSize: '24px' }"
          />
        </a-card>
      </a-col>
    </a-row>

    <!-- 测试列表 -->
    <a-table
      :columns="columns"
      :data-source="testResults"
      :loading="loading"
      row-key="source_code"
      :pagination="false"
      size="middle"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <a-badge
            v-if="record.status"
            :status="record.status === 'healthy' ? 'success' : 'error'"
            :text="record.status === 'healthy' ? '成功' : '失败'"
          />
          <span v-else style="color: #999;">未测试</span>
        </template>

        <template v-if="column.key === 'latency'">
          <a-tag v-if="record.latency_ms !== undefined" :color="getLatencyColor(record.latency_ms)">
            {{ record.latency_ms }}ms
          </a-tag>
          <span v-else>-</span>
        </template>

        <template v-if="column.key === 'error'">
          <a-tooltip :title="record.error" v-if="record.error">
            <a-tag color="red" style="cursor: help;">
              {{ record.error.substring(0, 30) }}...
            </a-tag>
          </a-tooltip>
          <span v-else style="color: #52c41a;">✓</span>
        </template>

        <template v-if="column.key === 'last_tested'">
          {{ formatTime(record.last_tested_at) }}
        </template>

        <template v-if="column.key === 'action'">
          <a-space>
            <a-button 
              type="link" 
              size="small" 
              @click="testSingle(record)"
              :loading="record.testing"
            >
              测试
            </a-button>
            <a-button 
              type="link" 
              size="small" 
              @click="showTestDialog(record)"
              :disabled="!record.status || record.status !== 'healthy'"
            >
              查询测试
            </a-button>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 查询测试对话框 -->
    <a-modal
      v-model:open="queryDialogVisible"
      :title="`查询测试 - ${selectedSource?.source_name}`"
      width="700px"
      :footer="null"
    >
      <a-form layout="vertical" v-if="selectedSource">
        <a-form-item label="测试查询参数">
          <a-textarea
            v-model:value="queryParams"
            :rows="4"
            placeholder='输入JSON格式的查询参数，例如:
{
  "symbol": "AAPL",
  "period": "1d"
}'
          />
        </a-form-item>

        <a-form-item>
          <a-button 
            type="primary" 
            @click="executeQuery"
            :loading="queryLoading"
          >
            执行查询
          </a-button>
        </a-form-item>

        <a-divider>查询结果</a-divider>

        <a-alert
          v-if="queryResult"
          :type="queryResult.success ? 'success' : 'error'"
          :message="queryResult.success ? '查询成功' : '查询失败'"
          show-icon
          style="margin-bottom: 16px;"
        >
          <template #description>
            <div v-if="queryResult.success">
              <p>响应时间: {{ queryResult.latency_ms }}ms</p>
              <p>返回数据: {{ queryResult.data_count }} 条记录</p>
            </div>
            <div v-else>
              <p>错误信息: {{ queryResult.error }}</p>
            </div>
          </template>
        </a-alert>

        <a-card v-if="queryResult?.success" title="返回数据预览" size="small">
          <pre style="max-height: 300px; overflow: auto;">{{ formatJson(queryResult.data) }}</pre>
        </a-card>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { ThunderboltOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { getDataSources, testDataSource } from '@/api/data-source'

const loading = ref(false)
const testingAll = ref(false)
const testResults = ref<any[]>([])
const testedCount = ref(0)
const totalSources = ref(0)

const queryDialogVisible = ref(false)
const queryLoading = ref(false)
const selectedSource = ref<any>(null)
const queryParams = ref('{}')
const queryResult = ref<any>(null)

const columns = [
  { title: '数据源代码', dataIndex: 'source_code', width: 180 },
  { title: '数据源名称', dataIndex: 'source_name', width: 200 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '响应时间', dataIndex: 'latency', key: 'latency', width: 120 },
  { title: '错误信息', dataIndex: 'error', key: 'error', ellipsis: true },
  { title: '最后测试', dataIndex: 'last_tested', key: 'last_tested', width: 180 },
  { title: '操作', key: 'action', width: 150, fixed: 'right' as const }
]

const successCount = computed(() => 
  testResults.value.filter(r => r.status === 'healthy').length
)

const failCount = computed(() => 
  testResults.value.filter(r => r.status === 'unhealthy').length
)

const avgLatency = computed(() => {
  const tested = testResults.value.filter(r => r.latency_ms !== undefined)
  if (tested.length === 0) return 0
  const total = tested.reduce((sum, r) => sum + r.latency_ms, 0)
  return total / tested.length
})

const progressPercent = computed(() => {
  if (totalSources.value === 0) return 0
  return Math.round((testedCount.value / totalSources.value) * 100)
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await getDataSources({})
    if (res && res.data_sources) {
      testResults.value = res.data_sources.map((item: any) => ({
        ...item,
        status: undefined,
        latency_ms: undefined,
        error: undefined,
        last_tested_at: undefined,
        testing: false
      }))
      totalSources.value = res.data_sources.length
    }
  } catch (error) {
    message.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const testSingle = async (record: any) => {
  record.testing = true
  try {
    const res = await testDataSource(record.source_code)
    if (res) {
      record.status = res.status
      record.latency_ms = res.latency_ms
      record.error = res.error
      record.last_tested_at = new Date().toISOString()
      message.success(`${record.source_name} 测试完成`)
    }
  } catch (error: any) {
    record.status = 'unhealthy'
    record.error = error.message || '测试失败'
    record.last_tested_at = new Date().toISOString()
    message.error(`${record.source_name} 测试失败`)
  } finally {
    record.testing = false
  }
}

const testAllSources = async () => {
  testingAll.value = true
  testedCount.value = 0

  try {
    // 并行测试，但限制并发数
    const batchSize = 5
    const sources = [...testResults.value]
    
    for (let i = 0; i < sources.length; i += batchSize) {
      const batch = sources.slice(i, i + batchSize)
      const promises = batch.map(async (record) => {
        try {
          record.testing = true
          const res = await testDataSource(record.source_code)
          if (res) {
            record.status = res.status
            record.latency_ms = res.latency_ms
            record.error = res.error
            record.last_tested_at = new Date().toISOString()
          }
        } catch (error: any) {
          record.status = 'unhealthy'
          record.error = error.message || '测试失败'
          record.last_tested_at = new Date().toISOString()
        } finally {
          record.testing = false
          testedCount.value++
        }
      })

      await Promise.all(promises)
    }

    message.success('批量测试完成')
  } catch (error) {
    message.error('批量测试失败')
  } finally {
    testingAll.value = false
  }
}

const showTestDialog = (record: any) => {
  selectedSource.value = record
  queryResult.value = null
  queryParams.value = getDefaultQueryParams(record.source_code)
  queryDialogVisible.value = true
}

const executeQuery = async () => {
  if (!selectedSource.value) return

  queryLoading.value = true
  try {
    const params = JSON.parse(queryParams.value)
    const startTime = Date.now()

    // 这里调用实际的查询API
    // 根据不同的数据源调用不同的接口
    const response = await executeDataSourceQuery(selectedSource.value.source_code, params)
    
    const latency = Date.now() - startTime
    
    queryResult.value = {
      success: true,
      latency_ms: latency,
      data: response.data || response,
      data_count: Array.isArray(response.data || response) ? (response.data || response).length : 1
    }

    message.success('查询成功')
  } catch (error: any) {
    queryResult.value = {
      success: false,
      error: error.message || '查询失败'
    }
    message.error('查询失败')
  } finally {
    queryLoading.value = false
  }
}

const executeDataSourceQuery = async (sourceCode: string, params: any) => {
  // 根据不同数据源调用不同的API
  // 这里是一个通用的实现示例
  const response = await fetch(`/api/data-sources/${sourceCode}/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(params)
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

const getDefaultQueryParams = (sourceCode: string): string => {
  // 根据不同数据源返回默认查询参数
  const defaults: Record<string, any> = {
    'crypto_ccxt': { symbol: 'BTC/USDT', timeframe: '1d' },
    'us_stock_yfinance': { symbol: 'AAPL', period: '1mo' },
    'search_google': { q: 'AI technology', num: 10 },
    'search_baidu': { wd: '人工智能', rn: 10 },
    'macro_fred': { series_id: 'GDP', frequency: 'Q' }
  }

  return JSON.stringify(defaults[sourceCode] || { query: 'test' }, null, 2)
}

const getLatencyColor = (latency: number): string => {
  if (latency < 200) return 'green'
  if (latency < 500) return 'orange'
  return 'red'
}

const formatTime = (timeStr: string | undefined): string => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleString()
}

const formatJson = (data: any): string => {
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="less">
.test-query {
  .test-header {
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

  .stat-card {
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    text-align: center;
  }
}
</style>
