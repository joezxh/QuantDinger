<template>
  <div class="rate-limit-manager">
    <div class="page-header">
      <div>
        <h2>限流配置管理</h2>
        <p class="subtitle">数据源: {{ sourceCode }}</p>
      </div>
      <a-space>
        <a-button @click="goBack">返回</a-button>
        <a-button type="primary" @click="loadData" :loading="loading">
          刷新
        </a-button>
      </a-space>
    </div>

    <a-row :gutter="24">
      <!-- 限流配置卡片 -->
      <a-col :span="16">
        <a-card title="限流参数配置" :bordered="false">
          <a-form
            :model="formState"
            layout="vertical"
            @finish="handleSubmit"
          >
            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="限流策略" required>
                  <a-select v-model:value="formState.strategy">
                    <a-select-option value="token_bucket">令牌桶 (Token Bucket)</a-select-option>
                    <a-select-option value="sliding_window">滑动窗口 (Sliding Window)</a-select-option>
                    <a-select-option value="fixed_window">固定窗口 (Fixed Window)</a-select-option>
                    <a-select-option value="adaptive">自适应 (Adaptive)</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="每周期请求数" required>
                  <a-input-number
                    v-model:value="formState.rate"
                    :min="1"
                    :max="10000"
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
            </a-row>

            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="周期长度（秒）" required>
                  <a-input-number
                    v-model:value="formState.period"
                    :min="1"
                    :max="3600"
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="突发容量">
                  <a-input-number
                    v-model:value="formState.burst"
                    :min="1"
                    :max="10000"
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
            </a-row>

            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="最大并发数">
                  <a-input-number
                    v-model:value="formState.max_concurrent"
                    :min="1"
                    :max="100"
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="优先级">
                  <a-input-number
                    v-model:value="formState.priority"
                    :min="1"
                    :max="100"
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
            </a-row>

            <a-form-item label="启用自适应限流">
              <a-switch v-model:checked="formState.enable_adaptive" />
            </a-form-item>

            <a-form-item label="错误时降速">
              <a-switch v-model:checked="formState.reduce_rate_on_error" />
            </a-form-item>

            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="错误阈值">
                  <a-input-number
                    v-model:value="formState.error_threshold"
                    :min="1"
                    :max="20"
                    style="width: 100%"
                    placeholder="连续错误次数"
                  />
                </a-form-item>
              </a-col>
            </a-row>

            <a-form-item label="备注">
              <a-textarea
                v-model:value="formState.notes"
                :rows="3"
                placeholder="限流配置说明"
              />
            </a-form-item>

            <a-form-item>
              <a-button type="primary" html-type="submit" :loading="submitting">
                保存配置
              </a-button>
            </a-form-item>
          </a-form>
        </a-card>
      </a-col>

      <!-- 限流统计卡片 -->
      <a-col :span="8">
        <a-card title="限流统计" :bordered="false" style="margin-bottom: 24px;">
          <a-statistic
            title="总请求数"
            :value="stats.total_requests || 0"
            :precision="0"
            style="margin-bottom: 16px;"
          />
          <a-statistic
            title="成功请求"
            :value="stats.successful_requests || 0"
            :precision="0"
            :value-style="{ color: '#3f8600' }"
            style="margin-bottom: 16px;"
          />
          <a-statistic
            title="被拒绝请求"
            :value="stats.rejected_requests || 0"
            :precision="0"
            :value-style="{ color: '#cf1322' }"
            style="margin-bottom: 16px;"
          />
          <a-statistic
            title="错误请求"
            :value="stats.error_requests || 0"
            :precision="0"
            :value-style="{ color: '#faad14' }"
          />
        </a-card>

        <a-card title="实时状态" :bordered="false">
          <a-descriptions :column="1" size="small">
            <a-descriptions-item label="当前速率">
              {{ stats.current_rate || 0 }} req/{{ stats.period || 60 }}s
            </a-descriptions-item>
            <a-descriptions-item label="剩余令牌">
              {{ stats.remaining_tokens || 0 }}
            </a-descriptions-item>
            <a-descriptions-item label="活跃并发">
              {{ stats.active_concurrent || 0 }} / {{ formState.max_concurrent }}
            </a-descriptions-item>
            <a-descriptions-item label="最后更新">
              {{ formatDate(stats.last_updated) }}
            </a-descriptions-item>
          </a-descriptions>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  getRateLimitConfig,
  updateRateLimitConfig,
  getRateLimitStats
} from '@/api/data-source'

const route = useRoute()
const router = useRouter()

const sourceCode = ref(route.query.source_code as string || '')
const loading = ref(false)
const submitting = ref(false)
const stats = ref<any>({})

const formState = reactive({
  strategy: 'token_bucket',
  rate: 60,
  period: 60,
  burst: 60,
  max_concurrent: 10,
  enable_adaptive: false,
  reduce_rate_on_error: true,
  error_threshold: 5,
  priority: 50,
  notes: ''
})

const loadData = async () => {
  if (!sourceCode.value) return
  
  loading.value = true
  try {
    // 加载限流配置
    const configRes = await getRateLimitConfig(sourceCode.value)
    if (configRes && configRes.rate_limit) {
      Object.assign(formState, configRes.rate_limit)
    }

    // 加载统计信息
    const statsRes = await getRateLimitStats(sourceCode.value)
    if (statsRes) {
      stats.value = statsRes.stats || {}
    }
  } catch (error) {
    message.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    const payload = {
      strategy: formState.strategy,
      rate: formState.rate,
      period: formState.period,
      burst: formState.burst,
      max_concurrent: formState.max_concurrent,
      enable_adaptive: formState.enable_adaptive,
      reduce_rate_on_error: formState.reduce_rate_on_error,
      error_threshold: formState.error_threshold,
      priority: formState.priority,
      notes: formState.notes
    }

    await updateRateLimitConfig(sourceCode.value, payload)
    message.success('保存成功')
    loadData()
  } catch (error) {
    message.error('保存失败')
  } finally {
    submitting.value = false
  }
}

const formatDate = (dateString: string | undefined): string => {
  if (!dateString) return '未知'
  const date = new Date(dateString)
  return date.toLocaleString()
}

const goBack = () => {
  router.push('/data-source')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="less">
.rate-limit-manager {
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
}
</style>
