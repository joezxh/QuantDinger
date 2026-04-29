<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>QuantDinger</h1>
        <p>AI driven quantitative insights for global markets</p>
      </div>

      <a-form
        :model="loginForm"
        :rules="rules"
        @finish="handleLogin"
        layout="vertical"
        size="large"
      >
        <a-form-item name="username">
          <a-input
            v-model:value="loginForm.username"
            :placeholder="t('user.login.username')"
          >
            <template #prefix>
              <UserOutlined style="color: rgba(0,0,0,.25)" />
            </template>
          </a-input>
        </a-form-item>

        <a-form-item name="password">
          <a-input-password
            v-model:value="loginForm.password"
            :placeholder="t('user.login.password')"
          >
            <template #prefix>
              <LockOutlined style="color: rgba(0,0,0,.25)" />
            </template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            :loading="loading"
            block
            size="large"
          >
            {{ t('user.login.submit') }}
          </a-button>
        </a-form-item>
      </a-form>

      <div class="login-footer">
        <a @click="$router.push('/register')">{{ t('user.login.registerHint') }}</a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const { t } = useI18n()

const loading = ref(false)
const loginForm = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: t('user.login.usernameRequired'), trigger: 'blur' }],
  password: [{ required: true, message: t('user.login.passwordRequired'), trigger: 'blur' }],
}

async function handleLogin() {
  loading.value = true
  try {
    await userStore.login(loginForm)
    message.success(t('user.login.success'))
    router.push('/')
  } catch (e: any) {
    message.error(e.message || t('user.login.failed'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="less">
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 420px;
  padding: 40px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;

  h1 {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 8px;
  }

  p {
    color: #666;
    font-size: 14px;
  }
}

.login-footer {
  text-align: center;
  margin-top: 16px;

  a {
    color: #3b82f6;
  }
}
</style>
