<template>
  <div class="llm-stats">
    <a-row :gutter="16">
      <a-col :span="6">
        <a-card>
          <a-statistic title="Total Calls" :value="stats.total_calls" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="Success Rate" :value="stats.success_rate * 100" suffix="%" :precision="2" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="Avg Latency" :value="stats.avg_latency" suffix="ms" :precision="0" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="Active Keys" :value="stats.active_keys" />
        </a-card>
      </a-col>
    </a-row>

    <a-card style="margin-top: 24px" title="Recent Call Logs">
      <a-table
        size="small"
        rowKey="id"
        :columns="logColumns"
        :dataSource="logs"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
      >
        <span slot="status" slot-scope="text">
          <a-tag :color="text === 1 ? 'green' : 'red'">{{ text === 1 ? 'Success' : 'Fail' }}</a-tag>
        </span>
      </a-table>
    </a-card>
  </div>
</template>

<script>
import { getLLMStats, getLLMLogs } from '@/api/llm'
import moment from 'moment'

export default {
  name: 'LLMStats',
  data () {
    return {
      loading: false,
      stats: {
        total_calls: 0,
        success_rate: 0,
        avg_latency: 0,
        active_keys: 0
      },
      logs: [],
      pagination: {
        current: 1,
        pageSize: 10,
        total: 0
      },
      logColumns: [
        { title: 'Time', dataIndex: 'created_at', customRender: (text) => moment(text).format('YYYY-MM-DD HH:mm:ss') },
        { title: 'Model', dataIndex: 'model' },
        { title: 'Provider', dataIndex: 'provider_name' },
        { title: 'Latency', dataIndex: 'latency', customRender: (text) => `${text}ms` },
        { title: 'Status', dataIndex: 'status', scopedSlots: { customRender: 'status' } },
        { title: 'Error', dataIndex: 'error_msg', ellipsis: true }
      ]
    }
  },
  created () {
    this.loadStats()
    this.loadLogs()
  },
  methods: {
    loadStats () {
      getLLMStats().then(res => {
        this.stats = res.data
      })
    },
    loadLogs () {
      this.loading = true
      const params = {
        page: this.pagination.current,
        page_size: this.pagination.pageSize
      }
      getLLMLogs(params).then(res => {
        this.logs = res.data
        this.pagination.total = res.total || 0
      }).finally(() => {
        this.loading = false
      })
    },
    handleTableChange (pagination) {
      this.pagination.current = pagination.current
      this.loadLogs()
    }
  }
}
</script>
