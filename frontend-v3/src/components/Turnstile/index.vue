<template>
  <div class="turnstile-container" v-if="enabled">
    <div ref="turnstileRef" :id="containerId"></div>
    <div v-if="error" class="turnstile-error">
      {{ error }}
      <a @click="reset">{{ t('user.security.retry') || 'Retry' }}</a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface Props {
  siteKey: string
  enabled?: boolean
  theme?: 'light' | 'dark' | 'auto'
  size?: 'normal' | 'compact'
}

const props = withDefaults(defineProps<Props>(), {
  enabled: true,
  theme: 'auto',
  size: 'normal',
})

const emit = defineEmits<{
  success: [token: string]
  error: []
  expired: []
}>()

let turnstileScriptLoaded = false
let turnstileScriptLoading = false
const turnstileCallbacks: Array<{ resolve: () => void; reject: (err: Error) => void }> = []

function loadTurnstileScript(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (turnstileScriptLoaded) {
      resolve()
      return
    }
    turnstileCallbacks.push({ resolve, reject })
    if (turnstileScriptLoading) return
    turnstileScriptLoading = true
    const script = document.createElement('script')
    script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'
    script.async = true
    script.defer = true
    script.onload = () => {
      turnstileScriptLoaded = true
      turnstileCallbacks.forEach((cb) => cb.resolve())
      turnstileCallbacks.length = 0
    }
    script.onerror = () => {
      turnstileScriptLoading = false
      turnstileCallbacks.forEach((cb) => cb.reject(new Error('Failed to load Turnstile script')))
      turnstileCallbacks.length = 0
    }
    document.head.appendChild(script)
  })
}

declare global {
  interface Window {
    turnstile?: {
      render: (container: HTMLElement | string, options: Record<string, unknown>) => string
      reset: (widgetId: string) => void
      remove: (widgetId: string) => void
    }
  }
}

const turnstileRef = ref<HTMLElement | null>(null)
const widgetId = ref<string | null>(null)
const token = ref<string | null>(null)
const error = ref<string | null>(null)
const containerId = `turnstile-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`

async function initTurnstile() {
  try {
    await loadTurnstileScript()
    renderWidget()
  } catch (e) {
    error.value = 'Failed to load verification'
    console.error('Turnstile init error:', e)
  }
}

function renderWidget() {
  if (!window.turnstile || !turnstileRef.value) return
  cleanup()
  widgetId.value = window.turnstile.render(turnstileRef.value, {
    sitekey: props.siteKey,
    theme: props.theme,
    size: props.size,
    callback: (t: string) => {
      token.value = t
      error.value = null
      emit('success', t)
    },
    'error-callback': () => {
      token.value = null
      error.value = 'Verification failed'
      emit('error')
    },
    'expired-callback': () => {
      token.value = null
      emit('expired')
    },
  })
}

function reset() {
  token.value = null
  error.value = null
  if (window.turnstile && widgetId.value !== null) {
    window.turnstile.reset(widgetId.value)
  } else {
    renderWidget()
  }
}

function getToken() {
  return token.value
}

function cleanup() {
  if (window.turnstile && widgetId.value !== null) {
    try {
      window.turnstile.remove(widgetId.value)
    } catch {
      // Ignore cleanup errors
    }
    widgetId.value = null
  }
}

onMounted(() => {
  if (props.enabled && props.siteKey) {
    initTurnstile()
  }
})

onUnmounted(() => {
  cleanup()
})

watch(() => props.siteKey, (newVal) => {
  if (newVal && props.enabled) initTurnstile()
})

watch(() => props.enabled, (newVal) => {
  if (newVal && props.siteKey) initTurnstile()
  else cleanup()
})

defineExpose({ reset, getToken })
</script>

<style lang="less" scoped>
.turnstile-container {
  margin: 16px 0;
  display: flex;
  flex-direction: column;
  align-items: center;

  .turnstile-error {
    margin-top: 8px;
    color: #ff4d4f;
    font-size: 13px;

    a {
      margin-left: 8px;
      color: #1890ff;
      cursor: pointer;

      &:hover {
        text-decoration: underline;
      }
    }
  }
}
</style>
