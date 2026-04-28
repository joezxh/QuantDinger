<template>
  <a-modal
    :title="$t('indicatorIde.codeEditor')"
    v-model:open="visible"
    :width="isMobile ? '100%' : '90vw'"
    :confirm-loading="saving"
    @ok="handleSave"
    @cancel="handleCancel"
    :ok-text="$t('indicatorIde.save')"
    :cancel-text="$t('common.cancel')"
    :mask-closable="false"
    :centered="false"
    :style="isMobile ? { top: '0', paddingBottom: '0' } : { top: '2%' }"
    wrap-class-name="indicator-editor-modal"
  >
    <div class="editor-content">
      <a-row :gutter="16">
        <a-col :xs="24" :sm="24" :md="18" class="code-pane">
          <div class="section-header">
            <span class="section-title">Code</span>
            <div class="section-actions">
              <a-button type="link" size="small" @click="handleVerifyCode" :loading="verifying" style="color: #52c41a; font-weight: bold;">
                <template #icon><CheckCircleOutlined /></template>
                Verify Code
              </a-button>
            </div>
          </div>
          <div class="editor-container-wrapper">
            <CodeEditor v-model="localCode" />
          </div>
        </a-col>

        <a-col :xs="24" :sm="24" :md="6" class="ai-pane">
          <div class="ai-panel">
            <div class="ai-panel-title">
              <RobotOutlined />
              <span>{{ $t('indicatorIde.aiGenerate') }}</span>
            </div>
            
            <template v-if="aiGenerating">
              <div class="ai-gen-loading">
                <a-spin size="large" />
                <div class="loading-text">Generating...</div>
              </div>
            </template>
            <template v-else>
              <a-textarea
                v-model:value="aiPrompt"
                :placeholder="$t('indicatorIde.aiPromptPlaceholder')"
                :rows="12"
                :auto-size="{ minRows: 12, maxRows: 20 }"
              />
              <a-button type="primary" block @click="handleAIGenerate" :loading="aiGenerating" size="large" style="margin-top: 10px;">
                Generate
              </a-button>
            </template>
          </div>
        </a-col>
      </a-row>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { CheckCircleOutlined, RobotOutlined } from '@ant-design/icons-vue'
import { message, Modal } from 'ant-design-vue'
import CodeEditor from '@/components/CodeEditor/index.vue'
import { verifyCode as verifyIndicatorCode, aiGenerate } from '@/api/indicator'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  open: boolean
  indicator?: any
  userId?: number
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'save', data: any): void
}>()

const { t } = useI18n()

const visible = ref(false)
const saving = ref(false)
const verifying = ref(false)
const aiGenerating = ref(false)
const isMobile = ref(false)
const localCode = ref('')
const aiPrompt = ref('')

const defaultTemplate = `# Demo Code:
# my_indicator_name = "My Buy/Sell Indicator"
# my_indicator_description = "Buy/Sell only; execution is normalized in backend."

# df = df.copy()
# sma = df["close"].rolling(14).mean()
# buy = (df["close"] > sma) & (df["close"].shift(1) <= sma.shift(1))
# sell = (df["close"] < sma) & (df["close"].shift(1) >= sma.shift(1))
# df["buy"] = buy.fillna(False).astype(bool)
# df["sell"] = sell.fillna(False).astype(bool)

# buy_marks = [df["low"].iloc[i] * 0.995 if df["buy"].iloc[i] else None for i in range(len(df))]
# sell_marks = [df["high"].iloc[i] * 1.005 if df["sell"].iloc[i] else None for i in range(len(df))]

# output = {
#  "name": my_indicator_name,
#  "plots": [],
#  "signals": [
#    {"type": "buy", "text": "B", "data": buy_marks, "color": "#00E676"},
#    {"type": "sell", "text": "S", "data": sell_marks, "color": "#FF5252"}
#  ]
# }
`

watch(() => props.open, (val) => {
  visible.value = val
  if (val) {
    localCode.value = props.indicator?.code || defaultTemplate
    aiPrompt.value = ''
  }
})

watch(visible, (val) => {
  emit('update:open', val)
})

const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkMobile)
})

const handleVerifyCode = async () => {
  if (!localCode.value || !localCode.value.trim()) {
    message.warning('Code is empty')
    return
  }
  
  verifying.value = true
  try {
    const res: any = await verifyIndicatorCode({ code: localCode.value })
    if (res.code === 1) {
      const plotsCount = res.data?.plots_count || 0
      const signalsCount = res.data?.signals_count || 0
      message.success(`Verified: ${plotsCount} plots, ${signalsCount} signals`)
    } else {
      Modal.error({
        title: 'Verification Failed',
        content: res.msg || 'Unknown error',
        width: 600
      })
    }
  } catch (error: any) {
    message.error(error.message || 'Request Failed')
  } finally {
    verifying.value = false
  }
}

const handleAIGenerate = async () => {
  if (!aiPrompt.value || !aiPrompt.value.trim()) {
    message.warning('Please enter a prompt')
    return
  }
  
  aiGenerating.value = true
  
  try {
    const res: any = await aiGenerate({
      prompt: aiPrompt.value.trim(),
      existingCode: localCode.value
    })
    
    if (res.code === 1 && res.data?.content) {
      // Append or replace code based on your logic, here appending for demo
      localCode.value += `\n\n${res.data.content}`
      message.success('Generated successfully')
    } else {
      throw new Error(res.msg || 'Generation failed')
    }
  } catch (error: any) {
    message.error(error.message || 'Failed to generate code')
  } finally {
    aiGenerating.value = false
  }
}

const handleSave = () => {
  if (!localCode.value || !localCode.value.trim()) {
    message.warning('Code cannot be empty')
    return
  }
  
  saving.value = true
  emit('save', {
    id: props.indicator?.id || 0,
    code: localCode.value,
    userid: props.userId
  })
  saving.value = false
}

const handleCancel = () => {
  visible.value = false
}
</script>

<style scoped lang="less">
.editor-content {
  height: 70vh;
  display: flex;
  flex-direction: column;
}

.editor-container-wrapper {
  height: calc(100% - 40px);
  border: 1px solid #d9d9d9;
  border-radius: 4px;
}

.code-pane, .ai-pane {
  height: 100%;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.section-title {
  font-weight: 600;
  font-size: 16px;
}

.ai-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fafafa;
  padding: 16px;
  border-radius: 4px;
  border: 1px solid #e8e8e8;
}

.ai-panel-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-gen-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
}

.loading-text {
  margin-top: 16px;
  color: #1890ff;
}

/* Dark mode overrides can be added here or globally */
</style>
