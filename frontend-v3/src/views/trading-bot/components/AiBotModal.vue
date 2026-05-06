<template>
  <a-modal
    v-model:open="visible"
    :title="t('trading-bot.ai.dialogTitle')"
    :width="560"
    :footer="null"
    @cancel="close"
  >
    <div class="ai-bot-modal">
      <p class="ai-desc">{{ t('trading-bot.ai.dialogDesc') }}</p>

      <!-- Quick prompts -->
      <div v-if="!result" class="quick-prompts">
        <div class="prompt-label">{{ t('trading-bot.ai.quickPrompts') }}</div>
        <div class="prompt-chips">
          <a-tag
            v-for="(item, idx) in quickPrompts"
            :key="idx"
            class="prompt-chip"
            @click="userInput = item"
          >{{ item }}</a-tag>
        </div>
      </div>

      <!-- Input -->
      <div v-if="!result" class="input-section">
        <a-textarea
          v-model:value="userInput"
          :placeholder="t('trading-bot.ai.inputPlaceholder')"
          :auto-size="{ minRows: 3, maxRows: 6 }"
          :disabled="loading"
        />
        <div class="input-footer">
          <a-button
            type="primary"
            :loading="loading"
            :disabled="!userInput.trim()"
            @click="handleGenerate"
          >
            <ThunderboltOutlined />
            {{ t('trading-bot.ai.generate') }}
          </a-button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="ai-loading">
        <a-spin />
        <p>{{ t('trading-bot.ai.analyzing') }}</p>
      </div>

      <!-- Result -->
      <div v-if="result && !loading" class="ai-result">
        <a-alert
          type="success"
          :message="t('trading-bot.ai.recommendReady')"
          show-icon
          style="margin-bottom: 16px"
        />

        <a-descriptions bordered size="small" :column="1">
          <a-descriptions-item :label="t('trading-bot.ai.recType')">
            <a-tag color="purple">{{ typeName(result.botType) }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item v-if="result.reason" :label="t('trading-bot.ai.reason')">
            {{ result.reason }}
          </a-descriptions-item>
          <a-descriptions-item :label="t('trading-bot.form.symbol')">
            {{ result.symbol || '-' }}
          </a-descriptions-item>
          <a-descriptions-item :label="t('trading-bot.form.timeframe')">
            {{ result.timeframe || '-' }}
          </a-descriptions-item>
          <a-descriptions-item :label="t('trading-bot.form.marketType')">
            {{ result.marketType || 'swap' }}
          </a-descriptions-item>
        </a-descriptions>

        <div class="result-actions">
          <a-button type="primary" @click="applyResult">
            <CheckOutlined />
            {{ t('trading-bot.ai.apply') }}
          </a-button>
          <a-button @click="reset">{{ t('common.retry') }}</a-button>
        </div>
      </div>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { ThunderboltOutlined, CheckOutlined } from '@ant-design/icons-vue'
import { aiGenerateStrategy } from '@/api/strategy'

const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<['update:open', 'apply']>()

const { t } = useI18n()
const userInput = ref('')
const loading = ref(false)
const result = ref<any>(null)

const visible = computed({
  get: () => props.open,
  set: (v) => emit('update:open', v),
})

const quickPrompts = [
  t('trading-bot.ai.prompt1'),
  t('trading-bot.ai.prompt2'),
  t('trading-bot.ai.prompt3'),
  t('trading-bot.ai.prompt4'),
]

function typeName(type: string) {
  const map: Record<string, string> = {
    grid: t('trading-bot.type.grid'),
    dca: t('trading-bot.type.dca'),
    martingale: t('trading-bot.type.martingale'),
    trend: t('trading-bot.type.trend'),
  }
  return map[type] || type
}

async function handleGenerate() {
  if (!userInput.value.trim()) return
  loading.value = true
  result.value = null
  try {
    const res: any = await aiGenerateStrategy({ prompt: userInput.value.trim() })
    if (res.code === 1 && res.data) {
      result.value = res.data
    } else {
      message.error(res.msg || t('trading-bot.ai.failed'))
    }
  } catch (e: any) {
    message.error(e.response?.data?.msg || t('common.failed'))
  } finally {
    loading.value = false
  }
}

function applyResult() {
  if (!result.value) return
  emit('apply', result.value)
  close()
}

function reset() {
  result.value = null
  userInput.value = ''
}

function close() {
  visible.value = false
  setTimeout(() => {
    reset()
  }, 300)
}
</script>

<style scoped>
.ai-bot-modal {
  padding: 8px 0;
}
.ai-desc {
  color: #8c8c8c;
  margin-bottom: 16px;
}
.quick-prompts {
  margin-bottom: 16px;
}
.prompt-label {
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 8px;
}
.prompt-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.prompt-chip {
  cursor: pointer;
  transition: all 0.2s;
}
.prompt-chip:hover {
  color: #1890ff;
  border-color: #1890ff;
}
.input-section {
  margin-bottom: 16px;
}
.input-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
.ai-loading {
  text-align: center;
  padding: 40px 0;
}
.ai-result {
  animation: fadeIn 0.3s ease;
}
.result-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
