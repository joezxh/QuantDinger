<template>
  <div class="llm-stats">
    <a-row :gutter="16">
      <a-col :span="6">
        <a-card>
          <a-statistic :title="t('batch.auto157')" :value="stats.total_calls" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic
            :title="t('batch.auto158')"
            :value="stats.success_rate * 100"
            suffix="%"
            :precision="2"
            :value-style="{ color: stats.success_rate > 0.9 ? '#3f8600' : '#cf1322' }"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic :title="t('batch.auto159')" :value="stats.avg_latency" suffix="ms" :precision="0" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic :title="t('batch.auto160')" :value="stats.active_keys" />
        </a-card>
      </a-col>
    </a-row>

    <a-card style="margin-top: 24px" :title="t('batch.auto161')">
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
            <a-tag :color="text === 1 ? 'green' : 'red'">{{ t('batch.auto162') }}</a-tag>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { getLLMStats, getLLMLogs } from '@/api/llm'
import dayjs from 'dayjs'

const { t } = useI18n()
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
  { title: t('common.time'), dataIndex: 'created_at', width: 180, customRender: ({ text }: any) => dayjs(text).format('YYYY-MM-DD HH:mm:ss') },
  { title: t('batch.auto163'), dataIndex: 'model' },
  { title: t('batch.auto150'), dataIndex: 'provider_name' },
  { title: t('batch.auto164'), dataIndex: 'latency', width: 100, customRender: ({ text }: any) => `${text}ms` },
  { title: t('common.status'), dataIndex: 'status', width: 100 },
  { title: t('batch.auto165'), dataIndex: 'error_msg', ellipsis: true }
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
