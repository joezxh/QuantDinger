<template>
  <div class="health-dashboard">
    <div class="page-header">
      <div>
        <h2>数据源健康监控</h2>
        <p class="subtitle">实时监控所有数据源的连接状态和性能</p>
      </div>
      <a-space>
        <a-button type="primary" @click="checkAllHealth" :loading="checking">
          全面健康检查
        </a-button>
        <a-button @click="loadData">
          刷新
        </a-button>
      </a-space>
    </div>

    <a-row :gutter="24">
      <!-- 总览统计 -->
      <a-col :span="6">
        <a-card :bordered="false" class="stat-card">
          <a-statistic
            title="总数据源"
            :value="totalSources"
            :value-style="{ fontSize: '32px' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false" class="stat-card">
          <a-statistic
            title="健康"
            :value="healthyCount"
            :value-style="{ color: '#3f8600', fontSize: '32px' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false" class="stat-card">
          <a-statistic
            title="异常"
            :value="unhealthyCount"
            :value-style="{ color: '#cf1322', fontSize: '32px' }"
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
            :value-style="{ fontSize: '32px' }"
          />
        </a-card>
      </a-col>
    </a-row>

    <a-card title="数据源健康状态" :bordered="false" style="margin-top: 24px;">
      <a-table
        :columns="columns"
        :data-source="healthData"
        :loading="loading"
        row-key="source_code"
        :pagination="false"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-badge
              :status="record.status === 'healthy' ? 'success' : 'error'"
              :text="record.status === 'healthy' ? '健康' : '异常'"
            />
          </template>

          <template v-if="column.key === 'latency'">
            <a-tag :color="getLatencyColor(record.latency_ms)">
              {{ record.latency_ms || 0 }}ms
            </a-tag>
          </template>

          <template v-if="column.key === 'categories'">
            <a-tag v-for="cat in (record.categories || [])" :key="cat" color="blue">
              {{ cat }}
            </a-tag>
          </template>

          <template v-if="column.key === 'last_check'">
            {{ formatDate(record.last_check_at) }}
          </template>

          <template v-if="column.key === 'error'">
            <span v-if="record.error" style="color: #ff4d4f;">
              {{ record.error }}
            </span>
            <span v-else>-</span>
          </template>

          <template v-if="column.key === 'action'">
            <a-space>
              <a @click="checkSingleHealth(record)">单独检查</a>
              <a @click="viewDetails(record)">查看详情</a>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 详情对话框 -->
    <a-modal
      v-model:open="detailVisible"
      title="数据源详情"
      width="700px"
      :footer="null"
    >
      <a-descriptions :column="2" bordered v-if="selectedSource">
        <a-descriptions-item label="数据源代码">
          {{ selectedSource.source_code }}
        </a-descriptions-item>
        <a-descriptions-item label="数据源名称">
          {{ selectedSource.source_name }}
        </a-descriptions-item>
        <a-descriptions-item label="层">
          {{ selectedSource.layer }}
        </a-descriptions-item>
        <a-descriptions-item label="启用状态">
          <a-badge
            :status="selectedSource.enabled ? 'success' : 'default'"
            :text="selectedSource.enabled ? '启用' : '禁用'"
          />
        </a-descriptions-item>
        <a-descriptions-item label="健康状态" :span="2">
          <a-badge
            :status="selectedSource.status === 'healthy' ? 'success' : 'error'"
            :text="selectedSource.status === 'healthy' ? '健康' : '异常'"
          />
        </a-descriptions-item>
        <a-descriptions-item label="响应时间">
          {{ selectedSource.latency_ms || 0 }}ms
        </a-descriptions-item>
        <a-descriptions-item label="最后检查">
          {{ formatDate(selectedSource.last_check_at) }}
        </a-descriptions-item>
        <a-descriptions-item label="市场类别" :span="2">
          <a-tag v-for="cat in (selectedSource.categories || [])" :key="cat" color="blue">
            {{ cat }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="错误信息" :span="2" v-if="selectedSource.error">
          <a-alert
            :message="selectedSource.error"
            type="error"
            show-icon
          />
        </a-descriptions-item>
        <a-descriptions-item label="负载均衡策略" :span="2">
          {{ selectedSource.load_balance_strategy || 'round_robin' }}
        </a-descriptions-item>
      </a-descriptions>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  getDataSources,
  getHealthStatus,
  testDataSource
} from '@/api/data-source'

const loading = ref(false)
const checking = ref(false)
const healthData = ref<any[]>([])
const detailVisible = ref(false)
const selectedSource = ref<any>(null)

const columns = [
  { title: '数据源代码', dataIndex: 'source_code', width: 180 },
  { title: '数据源名称', dataIndex: 'source_name', width: 200 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '响应时间', dataIndex: 'latency', key: 'latency', width: 120 },
  { title: '市场类别', dataIndex: 'categories', key: 'categories', width: 200 },
  { title: '最后检查', dataIndex: 'last_check', key: 'last_check', width: 180 },
  { title: '错误信息', dataIndex: 'error', key: 'error', ellipsis: true },
  { title: '操作', key: 'action', width: 180, fixed: 'right' as const }
]

const totalSources = computed(() => healthData.value.length)
const healthyCount = computed(() => 
  healthData.value.filter(item => item.status === 'healthy').length
)
const unhealthyCount = computed(() => 
  healthData.value.filter(item => item.status === 'unhealthy').length
)
const avgLatency = computed(() => {
  if (healthData.value.length === 0) return 0
  const total = healthData.value.reduce((sum, item) => sum + (item.latency_ms || 0), 0)
  return total / healthData.value.length
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await getDataSources({})
    if (res && res.data_sources) {
      healthData.value = res.data_sources.map((item: any) => ({
        ...item,
        status: 'unknown',
        latency_ms: 0,
        last_check_at: null,
        error: null
      }))
    }
  } catch (error) {
    message.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const checkAllHealth = async () => {
  checking.value = true
  try {
    // 并行检查所有数据源
    const promises = healthData.value.map(async (source) => {
      try {
        const res = await testDataSource(source.source_code)
        if (res) {
          source.status = res.status
          source.latency_ms = res.latency_ms
          source.error = res.error
        }
      } catch (error) {
        source.status = 'unhealthy'
        source.error = '检查失败'
      }
    })

    await Promise.all(promises)
    message.success('健康检查完成')
  } catch (error) {
    message.error('健康检查失败')
  } finally {
    checking.value = false
  }
}

const checkSingleHealth = async (record: any) => {
  try {
    const res = await testDataSource(record.source_code)
    if (res) {
      record.status = res.status
      record.latency_ms = res.latency_ms
      record.error = res.error
      message.success('检查完成')
    }
  } catch (error) {
    message.error('检查失败')
  }
}

const viewDetails = (record: any) => {
  selectedSource.value = record
  detailVisible.value = true
}

const getLatencyColor = (latency: number): string => {
  if (!latency) return 'default'
  if (latency < 200) return 'green'
  if (latency < 500) return 'orange'
  return 'red'
}

const formatDate = (dateString: string | null): string => {
  if (!dateString) return '从未检查'
  const date = new Date(dateString)
  return date.toLocaleString()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="less">
.health-dashboard {
  padding: 32px;
  background: #f8fafc;
  min-height: 100vh;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;

    h2 {
      font-size: 24px;
      font-weight: 700;
      color: #1e293b;
      margin: 0 0 4px 0;
    }

    .subtitle {
      color: #64748b;
      font-size: 14px;
      margin: 0;
    }
  }

  .stat-card {
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    transition: all 0.3s;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
  }
}
</style>
