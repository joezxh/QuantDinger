<template>
  <div class="llm-stats">
    <a-row :gutter="16">
      <a-col :span="6">
        <a-card>
          <a-statistic title="总调用次数" :value="stats.total_calls" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="成功率"
            :value="stats.success_rate * 100"
            suffix="%"
            :precision="2"
            :value-style="{ color: stats.success_rate > 0.9 ? '#3f8600' : '#cf1322' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="平均延迟" :value="stats.avg_latency" suffix="ms" :precision="0" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="活跃 Key 数量" :value="stats.active_keys" />
        </a-card>
      </a-col>
    </a-row>

    <a-card style="margin-top: 24px" title="最近调用日志">
      <a-table
        :columns="logColumns"
        :data-source="logs"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        size="small"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, text }">
          <template v-if="column.dataIndex === 'status'">
            <a-tag :color="text === 1 ? 'green' : 'red'">{{ text === 1 ? '成功' : '失败' }}</a-tag>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { getLLMStats, getLLMLogs } from '@/api/llm'
import dayjs from 'dayjs'

const stats = reactive({
  total_calls: 0,
  success_rate: 0,
  avg_latency: 0,
  active_keys: 0
})

const loading = ref(false)
const logs = ref([])
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true
})

const logColumns = [
  { title: '时间', dataIndex: 'created_at', width: 180, customRender: ({ text }: any) => dayjs(text).format('YYYY-MM-DD HH:mm:ss') },
  { title: '模型', dataIndex: 'model' },
  { title: '供应商', dataIndex: 'provider_name' },
  { title: '延迟', dataIndex: 'latency', width: 100, customRender: ({ text }: any) => `${text}ms` },
  { title: '状态', dataIndex: 'status', width: 100 },
  { title: '错误详情', dataIndex: 'error_msg', ellipsis: true }
]

const loadStats = async () => {
  try {
    const res: any = await getLLMStats()
    Object.assign(stats, res.data || {})
  } catch (e) {
    console.error('Failed to load stats')
  }
}

const loadLogs = async () => {
  loading.value = true
  try {
    const res: any = await getLLMLogs({
      page: pagination.current,
      page_size: pagination.pageSize
    })
    logs.value = res.data || []
    pagination.total = res.total || 0
  } catch (e) {
    console.error('Failed to load logs')
  } finally {
    loading.value = false
  }
}

const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadLogs()
}

onMounted(() => {
  loadStats()
  loadLogs()
})
</script>
