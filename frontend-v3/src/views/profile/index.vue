<template>
  <div class="profile-page">
    <div class="page-header">
      <h2 class="page-title">
        <UserOutlined />
        <span>{{ t('menu.profile') }}</span>
      </h2>
      <p class="page-desc">管理您的账户设置和偏好</p>
    </div>

    <a-row :gutter="24" class="profile-cards-row">
      <!-- Left Column: Profile Card -->
      <a-col :xs="24" :md="8" class="profile-card-col">
        <a-card :bordered="false" class="profile-card">
          <div class="avatar-section">
            <a-avatar :size="100" :src="profile.avatar || '/avatar2.jpg'" />
            <h3 class="username">{{ profile.nickname || profile.username }}</h3>
            <p class="user-role">
              <a-tag :color="getRoleColor(profile.role)">
                {{ getRoleLabel(profile.role) }}
              </a-tag>
              <a-tag v-if="isVip" color="gold">
                <CrownOutlined />
                VIP
              </a-tag>
            </p>
          </div>
          <a-divider />
          <div class="profile-info">
            <div class="info-item">
              <UserOutlined />
              <span class="label">用户名:</span>
              <span class="value">{{ profile.username }}</span>
            </div>
            <div class="info-item">
              <MailOutlined />
              <span class="label">邮箱:</span>
              <span class="value">{{ profile.email || '-' }}</span>
            </div>
            <div class="info-item">
              <CalendarOutlined />
              <span class="label">最后登录:</span>
              <span class="value">{{ formatTime(profile.last_login_at) || '-' }}</span>
            </div>
          </div>
        </a-card>
      </a-col>

      <!-- Right Column: Credits and Referral Cards -->
      <a-col :xs="24" :md="16" class="right-cards-col">
        <a-row :gutter="16" class="right-cards-row">
          <!-- Credits Card -->
          <a-col :xs="24" :md="12">
            <a-card :bordered="false" class="credits-card">
              <div class="credits-header">
                <h3 class="credits-title">
                  <WalletOutlined />
                  我的积分
                </h3>
              </div>
              <div class="credits-body">
                <div class="credits-amount">
                  <span class="amount-value">{{ formatCredits(billing.credits) }}</span>
                  <span>{{ t('userManage.credits') }}</span>
                </div>
                <div class="vip-status" v-if="billing.vip_expires_at">
                  <CrownOutlined :style="{ color: isVip ? '#faad14' : '#999' }" />
                  <span v-if="isVip" class="vip-active">
                    VIP有效期至: {{ formatDate(billing.vip_expires_at) }}
                  </span>
                  <span v-else class="vip-expired">
                    VIP已过期
                  </span>
                </div>
                <div class="vip-status" v-else-if="!billing.is_vip">
                  <span class="no-vip">非VIP用户</span>
                </div>
              </div>
              <a-divider />
              <div class="credits-actions">
                <a-button type="primary" @click="handleRecharge">
                  <ShoppingOutlined />
                  开通/充值
                </a-button>
              </div>
              <div class="credits-hint" v-if="billing.billing_enabled">
                <InfoCircleOutlined />
                <span>使用AI分析/回测/监控等功能会消耗积分；VIP仅可免费使用VIP免费指标。</span>
              </div>
            </a-card>
          </a-col>

          <!-- Referral Card -->
          <a-col :xs="24" :md="12">
            <a-card :bordered="false" class="referral-card">
              <div class="referral-header">
                <h3 class="referral-title">
                  <TeamOutlined />
                  邀请好友
                </h3>
              </div>
              <div class="referral-body">
                <div class="referral-stats">
                  <div class="stat-item">
                    <span class="stat-value">{{ referralData.total || 0 }}</span>
                    <span class="stat-label">已邀请</span>
                  </div>
                  <div class="stat-item" v-if="referralData.referral_bonus > 0">
                    <span class="stat-value">+{{ referralData.referral_bonus }}</span>
                    <span class="stat-label">每邀请获得</span>
                  </div>
                </div>
                <a-divider style="margin: 12px 0" />
                <div class="referral-link-section">
                  <div class="link-label">您的邀请链接</div>
                  <div class="link-box">
                    <a-input
                      :value="referralLink"
                      readonly
                      size="small"
                    >
                      <template #suffix>
                        <a-tooltip title="复制链接">
                          <CopyOutlined style="cursor: pointer" @click="copyReferralLink" />
                        </a-tooltip>
                      </template>
                    </a-input>
                  </div>
                </div>
                <div class="referral-hint" v-if="referralData.register_bonus > 0">
                  <GiftOutlined />
                  <span>新用户注册获得 {{ referralData.register_bonus }} 积分</span>
                </div>
              </div>
            </a-card>
          </a-col>
        </a-row>
      </a-col>
    </a-row>

    <!-- Edit Profile Tabs -->
    <a-row :gutter="24" style="margin-top: 24px">
      <a-col :xs="24">
        <a-card :bordered="false" class="edit-card">
          <a-tabs v-model:activeKey="activeTab">
            <!-- Basic Info Tab -->
            <a-tab-pane key="basic" tab="基本信息">
              <a-form :model="profileForm" layout="vertical" class="profile-form">
                <a-form-item :label="t('common.nickname')">
                  <a-input
                    v-model:value="profileForm.nickname"
                    :placeholder="t('validation.nicknameRequired')"
                  >
                    <template #prefix><SmileOutlined /></template>
                  </a-input>
                </a-form-item>

                <a-form-item :label="t('user.login.email')">
                  <a-input
                    :value="profile.email || '-'"
                    disabled
                  >
                    <template #prefix><MailOutlined /></template>
                    <template #suffix>
                      <a-tooltip title="注册后邮箱不可更改">
                        <InfoCircleOutlined style="color: rgba(0,0,0,.45)" />
                      </a-tooltip>
                    </template>
                  </a-input>
                </a-form-item>

                <a-form-item label="时区">
                  <a-select
                    v-model:value="profileForm.timezone"
                    placeholder="跟随浏览器/系统"
                    show-search
                    allow-clear
                  >
                    <a-select-option value="">
                      跟随浏览器
                    </a-select-option>
                    <a-select-option v-for="z in timezoneList" :key="z" :value="z">
                      {{ z }}
                    </a-select-option>
                  </a-select>
                </a-form-item>

                <a-form-item>
                  <a-button type="primary" :loading="saving" @click="handleSaveProfile">
                    <SaveOutlined />
                    保存
                  </a-button>
                </a-form-item>
              </a-form>
            </a-tab-pane>

            <!-- Change Password Tab -->
            <a-tab-pane key="password" tab="修改密码">
              <a-form :model="passwordForm" layout="vertical" class="password-form">
                <a-alert
                  message="为了安全，修改密码需要验证邮箱。密码至少8位，包含大小写字母和数字。"
                  type="info"
                  showIcon
                  style="margin-bottom: 24px"
                />

                <a-form-item label="当前密码">
                  <a-input-password
                    v-model:value="passwordForm.current_password"
                    placeholder="请输入当前密码"
                  >
                    <template #prefix><LockOutlined /></template>
                  </a-input-password>
                </a-form-item>

                <a-form-item :label="t('common.newPassword')">
                  <a-input-password
                    v-model:value="passwordForm.new_password"
                    placeholder="请输入新密码"
                  >
                    <template #prefix><LockOutlined /></template>
                  </a-input-password>
                </a-form-item>

                <a-form-item label="确认新密码">
                  <a-input-password
                    v-model:value="passwordForm.confirm_password"
                    placeholder="请再次输入新密码"
                  >
                    <template #prefix><LockOutlined /></template>
                  </a-input-password>
                </a-form-item>

                <a-form-item>
                  <a-button type="primary" :loading="saving" @click="handleChangePassword">
                    <SaveOutlined />
                    修改密码
                  </a-button>
                </a-form-item>
              </a-form>
            </a-tab-pane>

            <!-- Notification Settings Tab -->
            <a-tab-pane key="notifications" :tab="t('settings.tabs.notification')">
              <a-form :model="notificationForm" layout="vertical">
                <a-form-item label="邮件通知">
                  <a-switch v-model:checked="notificationForm.email_enabled" />
                  <span style="margin-left: 8px; color: #666;">接收邮件通知</span>
                </a-form-item>

                <a-form-item label="通知类型">
                  <a-select
                    v-model:value="notificationForm.notification_types"
                    mode="multiple"
                    placeholder="选择通知类型"
                  >
                    <a-select-option value="alert">预警通知</a-select-option>
                    <a-select-option value="monitor">监控结果</a-select-option>
                    <a-select-option value="report">日报/周报</a-select-option>
                    <a-select-option value="system">系统公告</a-select-option>
                  </a-select>
                </a-form-item>

                <a-form-item>
                  <a-button type="primary" :loading="saving" @click="handleSaveNotifications">
                    <SaveOutlined />
                    保存设置
                  </a-button>
                </a-form-item>
              </a-form>
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import {
  UserOutlined,
  MailOutlined,
  CalendarOutlined,
  CrownOutlined,
  WalletOutlined,
  TeamOutlined,
  CopyOutlined,
  GiftOutlined,
  InfoCircleOutlined,
  SmileOutlined,
  LockOutlined,
  SaveOutlined,
  ShoppingOutlined,
} from '@ant-design/icons-vue'
import { getProfile, updateProfile, changePassword, getReferralData, getBillingInfo } from '@/api/profile'
import { useUserStore } from '@/stores/user'

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('basic')
const saving = ref(false)

const profile = reactive({
  username: '',
  nickname: '',
  email: '',
  role: '',
  avatar: '',
  last_login_at: '',
  timezone: '',
})

const billing = reactive({
  credits: 0,
  is_vip: false,
  vip_expires_at: null as string | null,
  billing_enabled: false,
})

const referralData = reactive({
  total: 0,
  referral_bonus: 0,
  register_bonus: 0,
  referral_code: '',
})

const profileForm = reactive({
  nickname: '',
  timezone: '',
})

const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: '',
})

const notificationForm = reactive({
  email_enabled: true,
  notification_types: ['alert', 'monitor'],
})

const isVip = computed(() => {
  if (!billing.vip_expires_at) return false
  return new Date(billing.vip_expires_at) > new Date()
})

const referralLink = computed(() => {
  const code = referralData.referral_code || profile.username
  return `${window.location.origin}/register?ref=${code}`
})

const timezoneList = [
  'Asia/Shanghai',
  'Asia/Hong_Kong',
  'Asia/Tokyo',
  'America/New_York',
  'America/Chicago',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Paris',
  'UTC',
]

function formatCredits(v: number): string {
  if (!v && v !== 0) return '0'
  return Number(v).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

function formatTime(timestamp: string): string {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleString('zh-CN')
}

function getRoleColor(role: string): string {
  const colors: Record<string, string> = { admin: 'red', manager: 'orange', user: 'blue', viewer: 'default' }
  return colors[role] || 'default'
}

function getRoleLabel(role: string): string {
  const labels: Record<string, string> = { admin: '管理员', manager: '经理', user: '用户', viewer: '观察者' }
  return labels[role] || role
}

async function loadProfile() {
  try {
    const res = await getProfile()
    if (res && res.code === 1 && res.data) {
      Object.assign(profile, res.data)
      Object.assign(profileForm, {
        nickname: res.data.nickname,
        timezone: res.data.timezone || '',
      })
    }
  } catch (e: any) {
    message.error('加载个人信息失败')
  }
}

async function loadBilling() {
  try {
    const res = await getBillingInfo()
    if (res && res.code === 1 && res.data) {
      Object.assign(billing, res.data)
    }
  } catch (e) {
    console.error('加载账单信息失败:', e)
  }
}

async function loadReferral() {
  try {
    const res = await getReferralData()
    if (res && res.code === 1 && res.data) {
      Object.assign(referralData, res.data)
    }
  } catch (e) {
    console.error('加载邀请数据失败:', e)
  }
}

function handleRecharge() {
  router.push('/billing')
}

async function copyReferralLink() {
  try {
    await navigator.clipboard.writeText(referralLink.value)
    message.success('链接已复制')
  } catch (e) {
    message.error(t('common.copyFailed'))
  }
}

async function handleSaveProfile() {
  if (!profileForm.nickname) {
    message.warning('昵称不能为空')
    return
  }
  saving.value = true
  try {
    await updateProfile({
      nickname: profileForm.nickname,
      timezone: profileForm.timezone,
    })
    message.success(t('common.saveSuccess'))
    loadProfile()
  } catch (e: any) {
    message.error(e.response?.data?.msg || '保存失败')
  }
  saving.value = false
}

async function handleChangePassword() {
  if (!passwordForm.current_password || !passwordForm.new_password || !passwordForm.confirm_password) {
    message.warning('请填写完整密码信息')
    return
  }
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    message.warning('两次输入的密码不一致')
    return
  }
  if (passwordForm.new_password.length < 8) {
    message.warning('密码至少8位')
    return
  }
  saving.value = true
  try {
    await changePassword({
      old_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    })
    message.success('密码修改成功，请重新登录')
    userStore.logout()
    router.push('/login')
  } catch (e: any) {
    message.error(e.response?.data?.msg || '修改失败')
  }
  saving.value = false
}

async function handleSaveNotifications() {
  saving.value = true
  try {
    message.success('通知设置已保存')
  } catch (e: any) {
    message.error(t('common.saveFailed'))
  }
  saving.value = false
}

onMounted(() => {
  loadProfile()
  loadBilling()
  loadReferral()
})
</script>

<style scoped>
.profile-page {
  padding: 18px;
  background: #f5f7fa;
  min-height: calc(100vh - 120px);
}

.page-header {
  margin-bottom: 16px;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: #1e3a5f;
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-title .anticon {
  font-size: 24px;
  color: #1890ff;
}

.page-desc {
  color: #64748b;
  font-size: 14px;
  margin: 0;
}

.profile-card {
  background: #fff;
  border-radius: 8px;
  text-align: center;
}

.avatar-section {
  padding: 20px 0;
}

.avatar-section .username {
  margin-top: 16px;
  font-size: 20px;
  font-weight: 700;
  color: #1e3a5f;
}

.user-role {
  margin-top: 8px;
  display: flex;
  justify-content: center;
  gap: 8px;
}

.profile-info {
  padding: 16px 0;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item .label {
  color: #64748b;
  min-width: 70px;
}

.info-item .value {
  color: #1e3a5f;
  font-weight: 500;
}

.credits-card,
.referral-card {
  background: #fff;
  border-radius: 8px;
  height: 100%;
}

.credits-header,
.referral-header {
  padding: 16px 0 8px;
}

.credits-title,
.referral-title {
  font-size: 16px;
  font-weight: 700;
  color: #1e3a5f;
  display: flex;
  align-items: center;
  gap: 8px;
}

.credits-body {
  padding: 16px 0;
}

.credits-amount {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.amount-value {
  font-size: 28px;
  font-weight: 700;
  color: #722ed1;
}

.amount-label {
  font-size: 14px;
  color: #64748b;
}

.vip-status {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
}

.vip-active {
  color: #faad14;
}

.vip-expired,
.no-vip {
  color: #999;
}

.credits-actions {
  padding: 16px 0;
}

.credits-hint {
  font-size: 12px;
  color: #64748b;
  padding: 8px 0 16px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.referral-body {
  padding: 16px 0;
}

.referral-stats {
  display: flex;
  justify-content: space-around;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1890ff;
  display: block;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
}

.referral-link-section {
  margin-top: 12px;
}

.link-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}

.link-box {
  display: flex;
  align-items: center;
}

.referral-hint {
  margin-top: 12px;
  font-size: 12px;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 6px;
}

.edit-card {
  background: #fff;
  border-radius: 8px;
}

.profile-form,
.password-form {
  max-width: 600px;
}

@media (max-width: 768px) {
  .profile-card-col {
    margin-bottom: 16px;
  }
}
</style>
