<template>
  <div class="login-page">
    <!-- OAuth Processing Overlay -->
    <div v-if="oauthProcessing" class="oauth-processing">
      <a-spin size="large" />
      <p>{{ t('user.oauth.processing') || 'Processing login...' }}</p>
    </div>

    <!-- Main Content -->
    <div v-show="!oauthProcessing" class="login-card">
      <div class="auth-intro">
        <div class="desc">AI driven quantitative insights for global markets</div>
      </div>

      <a-tabs v-model:activeKey="activeTab" :animated="false">
        <!-- ========== Login Tab ========== -->
        <a-tab-pane key="login" :tab="t('user.login.tab') || 'Login'">
          <!-- Login Method Switch -->
          <div class="login-method-switch">
            <a
              :class="{ active: loginMethod === 'password' }"
              @click="loginMethod = 'password'"
            >{{ t('user.login.methodPassword') || 'Password' }}</a>
            <a-divider type="vertical" />
            <a
              :class="{ active: loginMethod === 'code' }"
              @click="loginMethod = 'code'"
            >{{ t('user.login.methodCode') || 'Email Code' }}</a>
          </div>

          <!-- Password Login Form -->
          <a-form
            v-show="loginMethod === 'password'"
            :model="passwordLoginForm"
            :rules="passwordLoginRules"
            @finish="handlePasswordLogin"
            layout="vertical"
            class="auth-form"
          >
            <a-alert
              v-if="passwordLoginError"
              type="error"
              show-icon
              style="margin-bottom: 24px"
              :message="passwordLoginError"
            />
            <a-alert
              v-if="oauthError"
              type="error"
              show-icon
              style="margin-bottom: 24px"
              :message="oauthError"
            />

            <a-form-item name="username">
              <a-input
                v-model:value="passwordLoginForm.username"
                size="large"
                :placeholder="t('user.login.username') || 'Username'"
              >
                <template #prefix>
                  <UserOutlined style="color: rgba(0,0,0,.25)" />
                </template>
              </a-input>
            </a-form-item>

            <a-form-item name="password">
              <a-input-password
                v-model:value="passwordLoginForm.password"
                size="large"
                :placeholder="t('user.login.password') || 'Password'"
              >
                <template #prefix>
                  <LockOutlined style="color: rgba(0,0,0,.25)" />
                </template>
              </a-input-password>
            </a-form-item>

            <Turnstile
              v-if="securityConfig.turnstile_enabled"
              ref="loginTurnstileRef"
              :site-key="securityConfig.turnstile_site_key"
              :enabled="securityConfig.turnstile_enabled"
              @success="(t: string) => (loginTurnstileToken = t)"
              @error="() => (loginTurnstileToken = null)"
            />

            <a-form-item style="margin-top: 24px">
              <a-button
                size="large"
                type="primary"
                html-type="submit"
                class="submit-button"
                :loading="passwordLoginLoading"
                :disabled="passwordLoginLoading || (securityConfig.turnstile_enabled && !loginTurnstileToken)"
                block
              >
                {{ t('user.login.submit') || 'Login' }}
              </a-button>
            </a-form-item>

            <div class="auth-links">
              <a @click="showResetModal = true">{{ t('user.login.forgotPassword') || 'Forgot Password?' }}</a>
            </div>
          </a-form>

          <!-- Email Code Login Form -->
          <a-form
            v-show="loginMethod === 'code'"
            :model="codeLoginForm"
            :rules="codeLoginRules"
            @finish="handleCodeLogin"
            layout="vertical"
            class="auth-form"
          >
            <a-alert
              v-if="codeLoginError"
              type="error"
              show-icon
              style="margin-bottom: 24px"
              :message="codeLoginError"
            />
            <a-alert
              v-if="oauthError"
              type="error"
              show-icon
              style="margin-bottom: 24px"
              :message="oauthError"
            />

            <a-form-item name="email">
              <a-input
                v-model:value="codeLoginForm.email"
                size="large"
                type="email"
                :placeholder="t('user.login.email') || 'Email'"
              >
                <template #prefix>
                  <MailOutlined style="color: rgba(0,0,0,.25)" />
                </template>
              </a-input>
            </a-form-item>

            <a-form-item name="code">
              <a-row :gutter="12">
                <a-col :span="16">
                  <a-input
                    v-model:value="codeLoginForm.code"
                    size="large"
                    :placeholder="t('user.login.verificationCode') || 'Verification Code'"
                  >
                    <template #prefix>
                      <SafetyCertificateOutlined style="color: rgba(0,0,0,.25)" />
                    </template>
                  </a-input>
                </a-col>
                <a-col :span="8">
                  <a-button
                    size="large"
                    block
                    :loading="codeLoginSendingCode"
                    :disabled="codeLoginSendingCode || codeLoginCountdown > 0"
                    @click="handleCodeLoginSendCode"
                  >
                    {{ codeLoginCountdown > 0 ? `${codeLoginCountdown}s` : (t('user.login.sendCode') || 'Send') }}
                  </a-button>
                </a-col>
              </a-row>
            </a-form-item>

            <Turnstile
              v-if="securityConfig.turnstile_enabled"
              ref="codeLoginTurnstileRef"
              :site-key="securityConfig.turnstile_site_key"
              :enabled="securityConfig.turnstile_enabled"
              @success="(t: string) => (codeLoginTurnstileToken = t)"
              @error="() => (codeLoginTurnstileToken = null)"
            />

            <a-form-item style="margin-top: 24px">
              <a-button
                size="large"
                type="primary"
                html-type="submit"
                class="submit-button"
                :loading="codeLoginLoading"
                :disabled="codeLoginLoading || (securityConfig.turnstile_enabled && !codeLoginTurnstileToken)"
                block
              >
                {{ t('user.login.submit') || 'Login' }}
              </a-button>
            </a-form-item>

            <div class="code-login-hint">
              <InfoCircleOutlined />
              <span>{{ t('user.login.codeLoginHint') || 'New users will be automatically registered' }}</span>
            </div>
          </a-form>

          <!-- OAuth Login -->
          <div v-if="hasOAuth" class="oauth-section">
            <a-divider>{{ t('user.login.orLoginWith') || 'Or login with' }}</a-divider>
            <div class="oauth-buttons">
              <a-button
                v-if="securityConfig.oauth_google_enabled"
                class="oauth-btn google-btn"
                @click="handleGoogleLogin"
              >
                <svg class="oauth-icon" viewBox="0 0 24 24" width="18" height="18">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Google
              </a-button>
              <a-button
                v-if="securityConfig.oauth_github_enabled"
                class="oauth-btn github-btn"
                @click="handleGitHubLogin"
              >
                <GithubOutlined />
                GitHub
              </a-button>
            </div>
          </div>
        </a-tab-pane>

        <!-- ========== Register Tab ========== -->
        <a-tab-pane v-if="securityConfig.registration_enabled" key="register" :tab="t('user.register.tab') || 'Register'">
          <a-form
            :model="registerForm"
            :rules="registerRules"
            @finish="handleRegister"
            layout="vertical"
            class="auth-form"
          >
            <a-alert
              v-if="registerError"
              type="error"
              show-icon
              style="margin-bottom: 24px"
              :message="registerError"
            />

            <a-form-item name="email">
              <a-input
                v-model:value="registerForm.email"
                size="large"
                type="email"
                :placeholder="t('user.register.email') || 'Email'"
              >
                <template #prefix>
                  <MailOutlined style="color: rgba(0,0,0,.25)" />
                </template>
              </a-input>
            </a-form-item>

            <a-form-item name="code">
              <a-row :gutter="12">
                <a-col :span="16">
                  <a-input
                    v-model:value="registerForm.code"
                    size="large"
                    :placeholder="t('user.register.verificationCode') || 'Verification Code'"
                  >
                    <template #prefix>
                      <SafetyCertificateOutlined style="color: rgba(0,0,0,.25)" />
                    </template>
                  </a-input>
                </a-col>
                <a-col :span="8">
                  <a-button
                    size="large"
                    block
                    :loading="registerSendingCode"
                    :disabled="registerSendingCode || registerCountdown > 0"
                    @click="handleRegisterSendCode"
                  >
                    {{ registerCountdown > 0 ? `${registerCountdown}s` : (t('user.register.sendCode') || 'Send') }}
                  </a-button>
                </a-col>
              </a-row>
            </a-form-item>

            <a-form-item name="username">
              <a-input
                v-model:value="registerForm.username"
                size="large"
                :placeholder="t('user.register.username') || 'Username'"
              >
                <template #prefix>
                  <UserOutlined style="color: rgba(0,0,0,.25)" />
                </template>
              </a-input>
            </a-form-item>

            <a-form-item name="password">
              <a-popover
                placement="rightTop"
                :trigger="['focus']"
                :open="regPwdFocused && !regPwdValid"
              >
                <template #content>
                  <div class="password-requirements">
                    <div :class="{ valid: regHasMinLength }">
                      <CheckCircleOutlined v-if="regHasMinLength" style="color: #52c41a" />
                      <CloseCircleOutlined v-else style="color: #ff4d4f" />
                      {{ t('user.register.pwdMinLength') || 'At least 8 characters' }}
                    </div>
                    <div :class="{ valid: regHasUppercase }">
                      <CheckCircleOutlined v-if="regHasUppercase" style="color: #52c41a" />
                      <CloseCircleOutlined v-else style="color: #ff4d4f" />
                      {{ t('user.register.pwdUppercase') || 'At least one uppercase letter' }}
                    </div>
                    <div :class="{ valid: regHasLowercase }">
                      <CheckCircleOutlined v-if="regHasLowercase" style="color: #52c41a" />
                      <CloseCircleOutlined v-else style="color: #ff4d4f" />
                      {{ t('user.register.pwdLowercase') || 'At least one lowercase letter' }}
                    </div>
                    <div :class="{ valid: regHasNumber }">
                      <CheckCircleOutlined v-if="regHasNumber" style="color: #52c41a" />
                      <CloseCircleOutlined v-else style="color: #ff4d4f" />
                      {{ t('user.register.pwdNumber') || 'At least one number' }}
                    </div>
                  </div>
                </template>
                <a-input-password
                  v-model:value="registerForm.password"
                  size="large"
                  :placeholder="t('user.register.password') || 'Password'"
                  @focus="regPwdFocused = true"
                  @blur="regPwdFocused = false"
                  @change="checkRegPassword"
                >
                  <template #prefix>
                    <LockOutlined style="color: rgba(0,0,0,.25)" />
                  </template>
                </a-input-password>
              </a-popover>
            </a-form-item>

            <a-form-item name="confirmPassword">
              <a-input-password
                v-model:value="registerForm.confirmPassword"
                size="large"
                :placeholder="t('user.register.confirmPassword') || 'Confirm Password'"
              >
                <template #prefix>
                  <LockOutlined style="color: rgba(0,0,0,.25)" />
                </template>
              </a-input-password>
            </a-form-item>

            <Turnstile
              v-if="securityConfig.turnstile_enabled"
              ref="registerTurnstileRef"
              :site-key="securityConfig.turnstile_site_key"
              :enabled="securityConfig.turnstile_enabled"
              @success="(t: string) => (registerTurnstileToken = t)"
              @error="() => (registerTurnstileToken = null)"
            />

            <a-form-item style="margin-top: 24px">
              <a-button
                size="large"
                type="primary"
                html-type="submit"
                class="submit-button"
                :loading="registerLoading"
                :disabled="registerLoading || (securityConfig.turnstile_enabled && !registerTurnstileToken)"
                block
              >
                {{ t('user.register.submit') || 'Create Account' }}
              </a-button>
            </a-form-item>
          </a-form>
        </a-tab-pane>
      </a-tabs>

      <!-- Legal Agreement -->
      <div class="legal-wrap">
        <div class="legal-header">
          <div class="legal-title">{{ t('user.login.legal.title') || 'Legal Agreement' }}</div>
          <a class="legal-toggle" @click="showLegal = !showLegal">
            {{ showLegal ? (t('user.login.legal.collapse') || 'Collapse') : (t('user.login.legal.view') || 'View') }}
          </a>
        </div>
        <div v-show="showLegal" class="legal-content">
          {{ t('user.login.legal.content') || '' }}
        </div>
        <div class="legal-agree">
          <a-checkbox v-model:checked="legalAgreed">
            {{ t('user.login.legal.agree') || 'I agree to the terms' }}
          </a-checkbox>
          <div v-if="legalError" class="legal-error">{{ t('user.login.legal.required') || 'Please agree to continue' }}</div>
        </div>
      </div>
    </div>

    <!-- Reset Password Modal -->
    <a-modal
      v-model:open="showResetModal"
      :title="t('user.resetPassword.title') || 'Reset Password'"
      :footer="null"
      :width="420"
      :destroy-on-close="true"
      @cancel="resetResetModal"
    >
      <!-- Step 1: Email & Code -->
      <a-form
        v-if="resetStep === 1"
        :model="resetForm"
        :rules="resetRules"
        @finish="handleResetVerify"
        layout="vertical"
        class="auth-form"
      >
        <a-alert
          v-if="resetError"
          type="error"
          show-icon
          style="margin-bottom: 24px"
          :message="resetError"
        />

        <a-form-item name="email">
          <a-input
            v-model:value="resetForm.email"
            size="large"
            type="email"
            :placeholder="t('user.resetPassword.email') || 'Email'"
          >
            <template #prefix>
              <MailOutlined style="color: rgba(0,0,0,.25)" />
            </template>
          </a-input>
        </a-form-item>

        <a-form-item name="code">
          <a-row :gutter="12">
            <a-col :span="16">
              <a-input
                v-model:value="resetForm.code"
                size="large"
                :placeholder="t('user.resetPassword.verificationCode') || 'Verification Code'"
              >
                <template #prefix>
                  <SafetyCertificateOutlined style="color: rgba(0,0,0,.25)" />
                </template>
              </a-input>
            </a-col>
            <a-col :span="8">
              <a-button
                size="large"
                block
                :loading="resetSendingCode"
                :disabled="resetSendingCode || resetCountdown > 0"
                @click="handleResetSendCode"
              >
                {{ resetCountdown > 0 ? `${resetCountdown}s` : (t('user.resetPassword.sendCode') || 'Send') }}
              </a-button>
            </a-col>
          </a-row>
        </a-form-item>

        <Turnstile
          v-if="securityConfig.turnstile_enabled"
          ref="resetTurnstileRef"
          :site-key="securityConfig.turnstile_site_key"
          :enabled="securityConfig.turnstile_enabled"
          @success="(t: string) => (resetTurnstileToken = t)"
          @error="() => (resetTurnstileToken = null)"
        />

        <a-form-item style="margin-top: 24px">
          <a-button
            size="large"
            type="primary"
            html-type="submit"
            class="submit-button"
            :disabled="securityConfig.turnstile_enabled && !resetTurnstileToken"
            block
          >
            {{ t('user.resetPassword.next') || 'Next' }}
          </a-button>
        </a-form-item>
      </a-form>

      <!-- Step 2: New Password -->
      <a-form
        v-if="resetStep === 2"
        :model="resetPwdForm"
        :rules="resetPwdRules"
        @finish="handleResetPassword"
        layout="vertical"
        class="auth-form"
      >
        <a-alert
          v-if="resetError"
          type="error"
          show-icon
          style="margin-bottom: 24px"
          :message="resetError"
        />

        <div class="email-display">
          <span>{{ t('user.resetPassword.resettingFor') || 'Resetting for' }}:</span>
          <strong>{{ resetEmail }}</strong>
        </div>

        <a-form-item name="new_password">
          <a-popover
            placement="rightTop"
            :trigger="['focus']"
            :open="resetPwdFocused && !resetPwdValid"
          >
            <template #content>
              <div class="password-requirements">
                <div :class="{ valid: resetHasMinLength }">
                  <CheckCircleOutlined v-if="resetHasMinLength" style="color: #52c41a" />
                  <CloseCircleOutlined v-else style="color: #ff4d4f" />
                  {{ t('user.register.pwdMinLength') || 'At least 8 characters' }}
                </div>
                <div :class="{ valid: resetHasUppercase }">
                  <CheckCircleOutlined v-if="resetHasUppercase" style="color: #52c41a" />
                  <CloseCircleOutlined v-else style="color: #ff4d4f" />
                  {{ t('user.register.pwdUppercase') || 'At least one uppercase letter' }}
                </div>
                <div :class="{ valid: resetHasLowercase }">
                  <CheckCircleOutlined v-if="resetHasLowercase" style="color: #52c41a" />
                  <CloseCircleOutlined v-else style="color: #ff4d4f" />
                  {{ t('user.register.pwdLowercase') || 'At least one lowercase letter' }}
                </div>
                <div :class="{ valid: resetHasNumber }">
                  <CheckCircleOutlined v-if="resetHasNumber" style="color: #52c41a" />
                  <CloseCircleOutlined v-else style="color: #ff4d4f" />
                  {{ t('user.register.pwdNumber') || 'At least one number' }}
                </div>
              </div>
            </template>
            <a-input-password
              v-model:value="resetPwdForm.new_password"
              size="large"
              :placeholder="t('user.resetPassword.newPassword') || 'New Password'"
              @focus="resetPwdFocused = true"
              @blur="resetPwdFocused = false"
              @change="checkResetPassword"
            >
              <template #prefix>
                <LockOutlined style="color: rgba(0,0,0,.25)" />
              </template>
            </a-input-password>
          </a-popover>
        </a-form-item>

        <a-form-item name="confirm_password">
          <a-input-password
            v-model:value="resetPwdForm.confirm_password"
            size="large"
            :placeholder="t('user.resetPassword.confirmPassword') || 'Confirm Password'"
          >
            <template #prefix>
              <LockOutlined style="color: rgba(0,0,0,.25)" />
            </template>
          </a-input-password>
        </a-form-item>

        <a-form-item style="margin-top: 24px">
          <a-button
            size="large"
            type="primary"
            html-type="submit"
            class="submit-button"
            :loading="resetLoading"
            block
          >
            {{ t('user.resetPassword.submit') || 'Reset Password' }}
          </a-button>
        </a-form-item>

        <div class="auth-links">
          <a @click="resetStep = 1">
            <ArrowLeftOutlined />
            {{ t('user.resetPassword.back') || 'Back' }}
          </a>
        </div>
      </a-form>

      <!-- Step 3: Success -->
      <div v-if="resetStep === 3" class="success-panel">
        <a-result
          status="success"
          :title="t('user.resetPassword.successTitle') || 'Password Reset Successful'"
          :sub-title="t('user.resetPassword.successSubtitle') || 'You can now login with your new password'"
        >
          <template #extra>
            <a-button type="primary" @click="showResetModal = false; activeTab = 'login'">
              {{ t('user.resetPassword.goToLogin') || 'Go to Login' }}
            </a-button>
          </template>
        </a-result>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { message, notification } from 'ant-design-vue'
import {
  UserOutlined,
  LockOutlined,
  MailOutlined,
  SafetyCertificateOutlined,
  InfoCircleOutlined,
  GithubOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons-vue'
import {
  getSecurityConfig,
  sendVerificationCode,
  register as registerApi,
  resetPassword as resetPasswordApi,
  loginWithCode,
  getGoogleOAuthUrl,
  getGitHubOAuthUrl,
} from '@/api/auth'
import { useUserStore } from '@/stores/user'
import Turnstile from '@/components/Turnstile/index.vue'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const userStore = useUserStore()

// ==================== Security Config ====================
const securityConfig = reactive({
  turnstile_enabled: false,
  turnstile_site_key: '',
  registration_enabled: true,
  oauth_google_enabled: false,
  oauth_github_enabled: false,
})

async function loadSecurityConfig() {
  try {
    const res = (await getSecurityConfig()) as any
    if (res.code === 1 && res.data) {
      Object.assign(securityConfig, res.data)
    }
  } catch (e) {
    console.error('Failed to load security config:', e)
  }
}

// ==================== Referral Code ====================
const referralCode = ref('')

function extractReferralCode() {
  const urlParams = new URLSearchParams(window.location.search)
  let hashParams = new URLSearchParams()
  if (window.location.hash) {
    const hashParts = window.location.hash.split('?')
    if (hashParts.length > 1) {
      hashParams = new URLSearchParams(hashParts[1])
    }
  }
  const routerRef = (route.query.ref || route.query.referral_code) as string
  referralCode.value =
    routerRef ||
    urlParams.get('ref') ||
    urlParams.get('referral_code') ||
    hashParams.get('ref') ||
    hashParams.get('referral_code') ||
    ''
  if (referralCode.value && securityConfig.registration_enabled) {
    activeTab.value = 'register'
  }
}

// ==================== OAuth ====================
const oauthProcessing = ref(false)
const oauthError = ref<string | null>(null)

const hasOAuth = computed(() => securityConfig.oauth_google_enabled || securityConfig.oauth_github_enabled)

function handleOAuthCallback() {
  const urlParams = new URLSearchParams(window.location.search)
  const hashParams = new URLSearchParams(window.location.hash.split('?')[1] || '')
  const oauthToken = urlParams.get('oauth_token') || hashParams.get('oauth_token')
  const oauthErrorParam = urlParams.get('oauth_error') || hashParams.get('oauth_error')

  if (oauthErrorParam) {
    oauthError.value = t(`user.oauth.error.${oauthErrorParam}`) || `OAuth error: ${oauthErrorParam}`
    window.history.replaceState({}, document.title, window.location.pathname + window.location.hash.split('?')[0])
    return
  }

  if (oauthToken) {
    oauthProcessing.value = true
    const expiresAt = new Date().getTime() + 7 * 24 * 60 * 60 * 1000
    userStore.token = oauthToken
    localStorage.setItem('access_token', oauthToken)

    window.history.replaceState({}, document.title, window.location.pathname + window.location.hash.split('?')[0])

    userStore
      .fetchUserInfo()
      .then(() => {
        router.push({ path: '/' })
        notification.success({
          message: 'Welcome',
          description: `Welcome back.`,
        })
      })
      .catch((err) => {
        oauthProcessing.value = false
        oauthError.value = 'Failed to get user info'
        console.error('OAuth login error:', err)
        userStore.logout()
      })
  }
}

function handleGoogleLogin() {
  window.location.href = getGoogleOAuthUrl()
}

function handleGitHubLogin() {
  window.location.href = getGitHubOAuthUrl()
}

// ==================== Tabs & Legal ====================
const activeTab = ref('login')
const showLegal = ref(false)
const legalAgreed = ref(true)
const legalError = ref(false)

// ==================== Password Login ====================
const passwordLoginForm = reactive({ username: '', password: '' })
const passwordLoginRules = {
  username: [{ required: true, message: t('user.login.usernameRequired') || 'Please enter username', trigger: 'blur' }],
  password: [{ required: true, message: t('user.login.passwordRequired') || 'Please enter password', trigger: 'blur' }],
}
const passwordLoginError = ref('')
const passwordLoginLoading = ref(false)
const loginTurnstileToken = ref<string | null>(null)
const loginTurnstileRef = ref<InstanceType<typeof Turnstile> | null>(null)

async function handlePasswordLogin() {
  legalError.value = false
  if (!legalAgreed.value) {
    legalError.value = true
    return
  }
  passwordLoginLoading.value = true
  passwordLoginError.value = ''
  try {
    await userStore.login({
      username: passwordLoginForm.username,
      password: passwordLoginForm.password,
      turnstile_token: loginTurnstileToken.value || undefined,
    })
    message.success(t('user.login.success') || 'Login successful')
    router.push('/')
  } catch (err: any) {
    const data = err.response?.data || {}
    passwordLoginError.value = data.msg || err.message || (t('user.login.failed') || 'Login failed')
    loginTurnstileRef.value?.reset()
    loginTurnstileToken.value = null
  } finally {
    passwordLoginLoading.value = false
  }
}

// ==================== Code Login ====================
const loginMethod = ref('password')
const codeLoginForm = reactive({ email: '', code: '' })
const codeLoginRules = {
  email: [
    { required: true, message: t('user.login.emailRequired') || 'Please enter email', trigger: 'blur' },
    { type: 'email', message: t('user.login.emailInvalid') || 'Invalid email format', trigger: 'blur' },
  ],
  code: [{ required: true, message: t('user.login.codeRequired') || 'Please enter verification code', trigger: 'blur' }],
}
const codeLoginError = ref('')
const codeLoginLoading = ref(false)
const codeLoginTurnstileToken = ref<string | null>(null)
const codeLoginSendingCode = ref(false)
const codeLoginCountdown = ref(0)
const codeLoginCountdownTimer = ref<ReturnType<typeof setInterval> | null>(null)
const codeLoginTurnstileRef = ref<InstanceType<typeof Turnstile> | null>(null)

async function handleCodeLoginSendCode() {
  if (!codeLoginForm.email) {
    message.error(t('user.login.emailRequired') || 'Please enter email')
    return
  }
  codeLoginSendingCode.value = true
  codeLoginError.value = ''
  try {
    const res = (await sendVerificationCode({
      email: codeLoginForm.email,
      type: 'login',
      turnstile_token: codeLoginTurnstileToken.value || undefined,
    })) as any
    if (res.code === 1) {
      message.success(t('user.login.codeSent') || 'Verification code sent')
      startCodeLoginCountdown()
    } else {
      codeLoginError.value = res.msg || 'Failed to send code'
    }
  } catch (e: any) {
    codeLoginError.value = e.response?.data?.msg || 'Failed to send code'
  } finally {
    codeLoginSendingCode.value = false
  }
}

function startCodeLoginCountdown() {
  codeLoginCountdown.value = 60
  codeLoginCountdownTimer.value = setInterval(() => {
    codeLoginCountdown.value--
    if (codeLoginCountdown.value <= 0) {
      if (codeLoginCountdownTimer.value) clearInterval(codeLoginCountdownTimer.value)
      codeLoginCountdownTimer.value = null
    }
  }, 1000)
}

async function handleCodeLogin() {
  legalError.value = false
  if (!legalAgreed.value) {
    legalError.value = true
    return
  }
  codeLoginLoading.value = true
  codeLoginError.value = ''
  try {
    const res = (await loginWithCode({
      email: codeLoginForm.email,
      code: codeLoginForm.code,
      turnstile_token: codeLoginTurnstileToken.value || undefined,
      referral_code: referralCode.value,
    })) as any

    if (res.code === 1 && res.data?.token) {
      userStore.token = res.data.token
      localStorage.setItem('access_token', res.data.token)
      if (res.data.userinfo) {
        userStore.userInfo = res.data.userinfo
      }
      await userStore.fetchUserInfo().catch(() => {})
      const isNew = res.data.is_new_user
      router.push('/').then(() => {
        notification.success({
          message: isNew ? (t('user.login.welcomeNew') || 'Welcome!') : 'Welcome',
          description: isNew
            ? (t('user.login.accountCreated') || 'Your account has been created.')
            : 'Welcome back.',
        })
      })
    } else {
      codeLoginError.value = res.msg || (t('user.login.failed') || 'Login failed')
      codeLoginTurnstileRef.value?.reset()
      codeLoginTurnstileToken.value = null
    }
  } catch (e: any) {
    codeLoginError.value = e.response?.data?.msg || (t('user.login.failed') || 'Login failed')
    codeLoginTurnstileRef.value?.reset()
    codeLoginTurnstileToken.value = null
  } finally {
    codeLoginLoading.value = false
  }
}

// ==================== Register ====================
const registerForm = reactive({ email: '', code: '', username: '', password: '', confirmPassword: '' })
const registerRules = {
  email: [
    { required: true, message: t('user.register.emailRequired') || 'Please enter email', trigger: 'blur' },
    { type: 'email', message: t('user.register.emailInvalid') || 'Invalid email format', trigger: 'blur' },
  ],
  code: [{ required: true, message: t('user.register.codeRequired') || 'Please enter verification code', trigger: 'blur' }],
  username: [
    { required: true, message: t('user.register.usernameRequired') || 'Please enter username', trigger: 'blur' },
    { min: 3, max: 30, message: t('user.register.usernameLength') || 'Username must be 3-30 characters', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: t('user.register.usernamePattern') || 'Start with letter, letters/numbers/underscore only', trigger: 'blur' },
  ],
  password: [
    { required: true, message: t('user.register.passwordRequired') || 'Please enter password', trigger: 'blur' },
    { validator: validateRegPasswordRule, trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: t('user.register.confirmPasswordRequired') || 'Please confirm password', trigger: 'blur' },
    { validator: validateRegConfirmPasswordRule, trigger: 'blur' },
  ],
}
const registerError = ref('')
const registerLoading = ref(false)
const registerTurnstileToken = ref<string | null>(null)
const registerSendingCode = ref(false)
const registerCountdown = ref(0)
const registerCountdownTimer = ref<ReturnType<typeof setInterval> | null>(null)
const registerTurnstileRef = ref<InstanceType<typeof Turnstile> | null>(null)

const regPwdFocused = ref(false)
const regHasMinLength = ref(false)
const regHasUppercase = ref(false)
const regHasLowercase = ref(false)
const regHasNumber = ref(false)
const regPwdValid = computed(() => regHasMinLength.value && regHasUppercase.value && regHasLowercase.value && regHasNumber.value)

function checkRegPassword() {
  const password = registerForm.password || ''
  regHasMinLength.value = password.length >= 8
  regHasUppercase.value = /[A-Z]/.test(password)
  regHasLowercase.value = /[a-z]/.test(password)
  regHasNumber.value = /[0-9]/.test(password)
}

function validateRegPasswordRule(_rule: any, value: string) {
  if (!value) return Promise.resolve()
  if (value.length < 8) return Promise.reject(new Error(t('user.register.pwdMinLength') || 'At least 8 characters'))
  if (!/[A-Z]/.test(value)) return Promise.reject(new Error(t('user.register.pwdUppercase') || 'At least one uppercase letter'))
  if (!/[a-z]/.test(value)) return Promise.reject(new Error(t('user.register.pwdLowercase') || 'At least one lowercase letter'))
  if (!/[0-9]/.test(value)) return Promise.reject(new Error(t('user.register.pwdNumber') || 'At least one number'))
  return Promise.resolve()
}

function validateRegConfirmPasswordRule(_rule: any, value: string) {
  if (value && value !== registerForm.password) {
    return Promise.reject(new Error(t('user.register.passwordMismatch') || 'Passwords do not match'))
  }
  return Promise.resolve()
}

async function handleRegisterSendCode() {
  if (!registerForm.email) {
    message.error(t('user.register.emailRequired') || 'Please enter email')
    return
  }
  registerSendingCode.value = true
  registerError.value = ''
  try {
    const res = (await sendVerificationCode({
      email: registerForm.email,
      type: 'register',
      turnstile_token: registerTurnstileToken.value || undefined,
    })) as any
    if (res.code === 1) {
      message.success(t('user.register.codeSent') || 'Verification code sent')
      startRegisterCountdown()
    } else {
      registerError.value = res.msg || 'Failed to send code'
    }
  } catch (e: any) {
    registerError.value = e.response?.data?.msg || 'Failed to send code'
  } finally {
    registerSendingCode.value = false
  }
}

function startRegisterCountdown() {
  registerCountdown.value = 60
  registerCountdownTimer.value = setInterval(() => {
    registerCountdown.value--
    if (registerCountdown.value <= 0) {
      if (registerCountdownTimer.value) clearInterval(registerCountdownTimer.value)
      registerCountdownTimer.value = null
    }
  }, 1000)
}

async function handleRegister() {
  legalError.value = false
  if (!legalAgreed.value) {
    legalError.value = true
    return
  }
  registerLoading.value = true
  registerError.value = ''
  try {
    const res = (await registerApi({
      email: registerForm.email,
      code: registerForm.code,
      username: registerForm.username,
      password: registerForm.password,
      turnstile_token: registerTurnstileToken.value || undefined,
      referral_code: referralCode.value,
    })) as any

    if (res.code === 1) {
      message.success(t('user.register.success') || 'Registration successful')
      if (res.data?.token) {
        userStore.token = res.data.token
        localStorage.setItem('access_token', res.data.token)
        if (res.data.userinfo) {
          userStore.userInfo = res.data.userinfo
        }
        await userStore.fetchUserInfo().catch(() => {})
        router.push('/').then(() => {
          notification.success({
            message: 'Welcome',
            description: 'Welcome to QuantDinger!',
          })
        })
      } else {
        activeTab.value = 'login'
        message.info(t('user.register.pleaseLogin') || 'Please login with your new account')
      }
    } else {
      registerError.value = res.msg || 'Registration failed'
      registerTurnstileRef.value?.reset()
      registerTurnstileToken.value = null
    }
  } catch (e: any) {
    registerError.value = e.response?.data?.msg || 'Registration failed'
    registerTurnstileRef.value?.reset()
    registerTurnstileToken.value = null
  } finally {
    registerLoading.value = false
  }
}

// ==================== Reset Password ====================
const showResetModal = ref(false)
const resetStep = ref(1)
const resetForm = reactive({ email: '', code: '' })
const resetRules = {
  email: [
    { required: true, message: t('user.resetPassword.emailRequired') || 'Please enter email', trigger: 'blur' },
    { type: 'email', message: t('user.resetPassword.emailInvalid') || 'Invalid email format', trigger: 'blur' },
  ],
  code: [{ required: true, message: t('user.resetPassword.codeRequired') || 'Please enter verification code', trigger: 'blur' }],
}
const resetPwdForm = reactive({ new_password: '', confirm_password: '' })
const resetPwdRules = {
  new_password: [
    { required: true, message: t('user.resetPassword.passwordRequired') || 'Please enter new password', trigger: 'blur' },
    { validator: validateResetPasswordRule, trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: t('user.resetPassword.confirmPasswordRequired') || 'Please confirm password', trigger: 'blur' },
    { validator: validateResetConfirmPasswordRule, trigger: 'blur' },
  ],
}
const resetError = ref('')
const resetLoading = ref(false)
const resetTurnstileToken = ref<string | null>(null)
const resetSendingCode = ref(false)
const resetCountdown = ref(0)
const resetCountdownTimer = ref<ReturnType<typeof setInterval> | null>(null)
const resetEmail = ref('')
const resetCode = ref('')
const resetTurnstileRef = ref<InstanceType<typeof Turnstile> | null>(null)

const resetPwdFocused = ref(false)
const resetHasMinLength = ref(false)
const resetHasUppercase = ref(false)
const resetHasLowercase = ref(false)
const resetHasNumber = ref(false)
const resetPwdValid = computed(() => resetHasMinLength.value && resetHasUppercase.value && resetHasLowercase.value && resetHasNumber.value)

function checkResetPassword() {
  const password = resetPwdForm.new_password || ''
  resetHasMinLength.value = password.length >= 8
  resetHasUppercase.value = /[A-Z]/.test(password)
  resetHasLowercase.value = /[a-z]/.test(password)
  resetHasNumber.value = /[0-9]/.test(password)
}

function validateResetPasswordRule(_rule: any, value: string) {
  if (!value) return Promise.resolve()
  if (value.length < 8) return Promise.reject(new Error(t('user.register.pwdMinLength') || 'At least 8 characters'))
  if (!/[A-Z]/.test(value)) return Promise.reject(new Error(t('user.register.pwdUppercase') || 'At least one uppercase letter'))
  if (!/[a-z]/.test(value)) return Promise.reject(new Error(t('user.register.pwdLowercase') || 'At least one lowercase letter'))
  if (!/[0-9]/.test(value)) return Promise.reject(new Error(t('user.register.pwdNumber') || 'At least one number'))
  return Promise.resolve()
}

function validateResetConfirmPasswordRule(_rule: any, value: string) {
  if (value && value !== resetPwdForm.new_password) {
    return Promise.reject(new Error(t('user.register.passwordMismatch') || 'Passwords do not match'))
  }
  return Promise.resolve()
}

function resetResetModal() {
  resetStep.value = 1
  resetError.value = ''
  resetEmail.value = ''
  resetCode.value = ''
  resetCountdown.value = 0
  if (resetCountdownTimer.value) {
    clearInterval(resetCountdownTimer.value)
    resetCountdownTimer.value = null
  }
}

async function handleResetSendCode() {
  if (!resetForm.email) {
    message.error(t('user.resetPassword.emailRequired') || 'Please enter email')
    return
  }
  resetSendingCode.value = true
  resetError.value = ''
  try {
    const res = (await sendVerificationCode({
      email: resetForm.email,
      type: 'reset_password',
      turnstile_token: resetTurnstileToken.value || undefined,
    })) as any
    if (res.code === 1) {
      message.success(t('user.resetPassword.codeSent') || 'Verification code sent')
      startResetCountdown()
    } else {
      resetError.value = res.msg || 'Failed to send code'
    }
  } catch (e: any) {
    resetError.value = e.response?.data?.msg || 'Failed to send code'
  } finally {
    resetSendingCode.value = false
  }
}

function startResetCountdown() {
  resetCountdown.value = 60
  resetCountdownTimer.value = setInterval(() => {
    resetCountdown.value--
    if (resetCountdown.value <= 0) {
      if (resetCountdownTimer.value) clearInterval(resetCountdownTimer.value)
      resetCountdownTimer.value = null
    }
  }, 1000)
}

function handleResetVerify() {
  resetError.value = ''
  resetEmail.value = resetForm.email
  resetCode.value = resetForm.code
  resetStep.value = 2
}

async function handleResetPassword() {
  resetError.value = ''
  resetLoading.value = true
  try {
    const res = (await resetPasswordApi({
      email: resetEmail.value,
      code: resetCode.value,
      new_password: resetPwdForm.new_password,
      turnstile_token: resetTurnstileToken.value || undefined,
    })) as any
    if (res.code === 1) {
      resetStep.value = 3
    } else {
      resetError.value = res.msg || 'Failed to reset password'
      if (res.msg?.includes('code') || res.msg?.includes('expired')) {
        resetStep.value = 1
      }
    }
  } catch (e: any) {
    resetError.value = e.response?.data?.msg || 'Failed to reset password'
  } finally {
    resetLoading.value = false
  }
}

// ==================== Lifecycle ====================
onMounted(() => {
  loadSecurityConfig().then(() => {
    extractReferralCode()
    handleOAuthCallback()
    // Auto-switch tab based on route path
    if (route.path === '/register') {
      activeTab.value = 'register'
    } else if (route.path === '/forgot-password') {
      showResetModal.value = true
    }
  })
})

onUnmounted(() => {
  if (codeLoginCountdownTimer.value) clearInterval(codeLoginCountdownTimer.value)
  if (registerCountdownTimer.value) clearInterval(registerCountdownTimer.value)
  if (resetCountdownTimer.value) clearInterval(resetCountdownTimer.value)
})

watch(
  () => route.query,
  () => {
    extractReferralCode()
  }
)
</script>

<style scoped lang="less">
.login-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 40px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

  .auth-intro {
    text-align: center;
    margin-bottom: 24px;

    .desc {
      margin-top: 12px;
      color: rgba(255, 255, 255, 0.85);
      font-size: 14px;
    }
  }

  .login-card {
    min-width: 360px;
    width: 420px;
    background: #fff;
    padding: 32px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  }

  .oauth-processing {
    text-align: center;
    padding: 40px 0;
    background: #fff;
    border-radius: 8px;
    width: 420px;

    p {
      margin-top: 16px;
      color: rgba(0, 0, 0, 0.45);
    }
  }

  .auth-form {
    .submit-button {
      padding: 0 15px;
      font-size: 16px;
      height: 40px;
    }
  }

  .login-method-switch {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 24px;

    a {
      color: rgba(0, 0, 0, 0.45);
      font-size: 14px;
      cursor: pointer;
      padding: 4px 0;
      border-bottom: 2px solid transparent;
      transition: all 0.3s;

      &:hover {
        color: #1890ff;
      }

      &.active {
        color: #1890ff;
        border-bottom-color: #1890ff;
        font-weight: 500;
      }
    }

    .ant-divider {
      margin: 0 16px;
    }
  }

  .code-login-hint {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    margin-top: 16px;
    font-size: 13px;
    color: rgba(0, 0, 0, 0.45);

    .anticon {
      color: #1890ff;
    }
  }

  .auth-links {
    text-align: center;
    margin-top: 16px;
    font-size: 14px;

    a {
      color: #1890ff;
      cursor: pointer;

      &:hover {
        text-decoration: underline;
      }
    }
  }

  .oauth-section {
    margin-top: 24px;

    .ant-divider {
      color: rgba(0, 0, 0, 0.45);
      font-size: 13px;
    }

    .oauth-buttons {
      display: flex;
      gap: 12px;
      justify-content: center;

      .oauth-btn {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        height: 40px;
        font-size: 14px;

        .oauth-icon {
          width: 18px;
          height: 18px;
        }

        .anticon {
          font-size: 18px;
        }
      }

      .google-btn {
        border-color: #d9d9d9;
        color: rgba(0, 0, 0, 0.65);

        &:hover {
          border-color: #4285F4;
          color: #4285F4;
        }
      }

      .github-btn {
        border-color: #d9d9d9;
        color: rgba(0, 0, 0, 0.65);

        &:hover {
          border-color: #24292e;
          color: #24292e;
        }
      }
    }
  }

  .legal-wrap {
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px dashed #f0f0f0;

    .legal-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      line-height: 20px;
    }
    .legal-title {
      font-size: 13px;
      font-weight: 600;
      color: rgba(0, 0, 0, 0.75);
    }
    .legal-toggle {
      font-size: 12px;
      color: #1890ff;
      cursor: pointer;
    }
    .legal-content {
      margin-top: 8px;
      font-size: 12px;
      color: rgba(0, 0, 0, 0.45);
      line-height: 1.7;
      white-space: pre-wrap;
    }

    .legal-agree {
      margin-top: 10px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .legal-error {
      color: #ff4d4f;
      font-size: 12px;
      line-height: 1.4;
    }
  }
}

.email-display {
  background: #f5f5f5;
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 24px;
  font-size: 14px;

  span {
    color: rgba(0, 0, 0, 0.45);
  }

  strong {
    color: rgba(0, 0, 0, 0.85);
    margin-left: 8px;
  }
}

.success-panel {
  padding: 20px 0;
}

.password-requirements {
  font-size: 13px;

  > div {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 0;
    color: #ff4d4f;

    &.valid {
      color: #52c41a;
    }

    .anticon {
      font-size: 14px;
    }
  }
}
</style>
