<template>
  <div class="billing-page">
    <div class="page-header">
      <h2 class="page-title">
        <WalletOutlined />
        <span>账单管理</span>
      </h2>
      <p class="page-desc">管理您的积分、VIP会员和套餐</p>
    </div>

    <a-card :bordered="false" class="snapshot-card">
      <div class="snapshot-row">
        <div class="snap-item">
          <div class="snap-label">当前积分</div>
          <div class="snap-value">{{ formatCredits(billing.credits) }}</div>
        </div>
        <div class="snap-item">
          <div class="snap-label">VIP状态</div>
          <div class="snap-value">
            <a-tag v-if="billing.is_vip" color="gold">
              <CrownOutlined /> VIP
            </a-tag>
            <a-tag v-else>非VIP</a-tag>
            <span v-if="billing.vip_expires_at" class="vip-exp">
              到期: {{ formatDate(billing.vip_expires_at) }}
            </span>
          </div>
        </div>
      </div>
      <a-alert
        style="margin-top: 12px;"
        type="info"
        show-icon
        message="VIP会员规则"
        description="VIP会员每月获得额外积分奖励，可在有效期内享受高级功能。"
      />
    </a-card>

    <a-row :gutter="16" style="margin-top: 16px;">
      <a-col :xs="24" :md="8">
        <a-card :bordered="false" class="plan-card">
          <div class="plan-title">月度套餐</div>
          <div class="plan-price">
            ${{ plans.monthly.price_usd }}
            <span class="plan-unit">/ 月</span>
          </div>
          <div class="plan-benefit">
            +{{ plans.monthly.credits_once }} 积分
          </div>
          <a-button type="primary" block :loading="purchasing === 'monthly'" @click="buy('monthly')">
            立即购买
          </a-button>
        </a-card>
      </a-col>

      <a-col :xs="24" :md="8">
        <a-card :bordered="false" class="plan-card highlight">
          <div class="plan-title">年度套餐</div>
          <div class="plan-price">
            ${{ plans.yearly.price_usd }}
            <span class="plan-unit">/ 年</span>
          </div>
          <div class="plan-benefit">
            +{{ plans.yearly.credits_once }} 积分
          </div>
          <a-button type="primary" block :loading="purchasing === 'yearly'" @click="buy('yearly')">
            立即购买
          </a-button>
        </a-card>
      </a-col>

      <a-col :xs="24" :md="8">
        <a-card :bordered="false" class="plan-card">
          <div class="plan-title">永久会员</div>
          <div class="plan-price">
            ${{ plans.lifetime.price_usd }}
            <span class="plan-unit">（一次性）</span>
          </div>
          <div class="plan-benefit">
            每月 +{{ plans.lifetime.credits_monthly }} 积分
          </div>
          <a-button type="primary" block :loading="purchasing === 'lifetime'" @click="buy('lifetime')">
            立即购买
          </a-button>
        </a-card>
      </a-col>
    </a-row>

    <!-- USDT Pay Modal -->
    <a-modal
      v-model:visible="usdtModalVisible"
      :title="null"
      :footer="null"
      :maskClosable="false"
      :closable="false"
      wrapClassName="usdt-pay-modal-wrap"
      width="600px"
      @cancel="closeUsdtModal"
    >
      <div v-if="usdtOrder" class="usdt-checkout">
        <!-- Custom Header -->
        <div class="checkout-header">
          <div class="header-left">
            <div class="usdt-logo">
              <svg viewBox="0 0 32 32" width="28" height="28"><circle cx="16" cy="16" r="16" fill="#26A17B"/><path d="M17.9 17.9v-.003c-.1.008-.6.04-1.8.04-1 0-1.5-.028-1.7-.04v.004c-3.4-.15-5.9-.74-5.9-1.44 0-.7 2.5-1.29 5.9-1.44v2.3c.2.013.7.05 1.7.05 1.2 0 1.6-.04 1.8-.05v-2.3c3.4.15 5.9.74 5.9 1.44 0 .7-2.5 1.29-5.9 1.44zm0-3.12V12.7h5v-2.4H9.2v2.4h5v2.08c-3.8.18-6.7.93-6.7 1.83s2.9 1.65 6.7 1.83v6.56h3.6v-6.56c3.8-.18 6.7-.93 6.7-1.83s-2.8-1.65-6.6-1.83z" fill="#fff"/></svg>
            </div>
            <div class="header-text">
              <div class="header-title">USDT 支付</div>
              <div class="header-desc">请扫描下方二维码完成支付</div>
            </div>
          </div>
          <a-button type="link" class="close-btn" @click="closeUsdtModal">
            <CloseOutlined />
          </a-button>
        </div>

        <!-- Status Steps -->
        <div class="checkout-steps">
          <div
            v-for="(step, idx) in stepItems"
            :key="idx"
            class="step-item"
            :class="{ active: idx <= usdtStepCurrent, current: idx === usdtStepCurrent }"
          >
            <div class="step-dot">
              <span class="dot-inner" />
              <span v-if="idx === usdtStepCurrent && usdtOrder.status === 'pending'" class="dot-pulse" />
            </div>
            <span class="step-label">{{ step }}</span>
            <div v-if="idx < stepItems.length - 1" class="step-line" :class="{ filled: idx < usdtStepCurrent }" />
          </div>
        </div>

        <!-- Main Content -->
        <div class="checkout-body">
          <!-- QR Section -->
          <div class="qr-section">
            <div class="qr-frame" :class="{ 'qr-confirmed': usdtOrder.status === 'confirmed' }">
              <img :src="usdtQrUrl" alt="USDT QR" />
            </div>
            <div class="qr-amount">
              <span class="amt-number">{{ usdtOrder.amount_usdt }}</span>
              <span class="amt-currency">USDT</span>
            </div>
            <div class="qr-chain">
              <a-tag color="green">{{ usdtOrder.chain }}</a-tag>
            </div>
          </div>

          <!-- Info Section -->
          <div class="info-section">
            <!-- Address -->
            <div class="info-block">
              <div class="info-label">
                <EnvironmentOutlined />
                <span>收款地址</span>
              </div>
              <div class="addr-box">
                <code class="addr-text">{{ usdtOrder.address }}</code>
                <a-tooltip title="复制地址">
                  <a-button size="small" class="copy-btn" @click="copyText(usdtOrder.address)">
                    <CopyOutlined />
                  </a-button>
                </a-tooltip>
              </div>
            </div>

            <!-- Amount -->
            <div class="info-block">
              <div class="info-label">
                <DollarOutlined />
                <span>支付金额</span>
              </div>
              <div class="amt-box">
                <code class="amt-text">{{ usdtOrder.amount_usdt }} USDT</code>
                <a-tooltip title="复制金额">
                  <a-button size="small" class="copy-btn" @click="copyText(usdtOrder.amount_usdt)">
                    <CopyOutlined />
                  </a-button>
                </a-tooltip>
              </div>
            </div>

            <!-- Warning -->
            <div class="warn-strip">
              <ExclamationCircleOutlined />
              <span>请使用TRC20网络转账，确认后将自动到账</span>
            </div>

            <!-- Expiry & Status -->
            <div class="meta-row">
              <div class="meta-status">
                <a-tag :color="statusColor">{{ statusText }}</a-tag>
              </div>
              <div v-if="usdtOrder.expires_at" class="meta-expire">
                <ClockCircleOutlined />
                <span>{{ formatDateTime(usdtOrder.expires_at) }}</span>
              </div>
            </div>

            <!-- Expired: contact support -->
            <div v-if="usdtOrder.status === 'expired'" class="expired-hint">
              <a-alert
                type="warning"
                message="订单已过期"
                show-icon
                banner
              />
            </div>

            <!-- Confirmed: success banner -->
            <div v-if="usdtOrder.status === 'confirmed'" class="confirmed-hint">
              <a-alert
                type="success"
                message="支付成功"
                show-icon
                banner
              />
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="checkout-footer">
          <a-button v-if="usdtOrder.status !== 'confirmed'" size="small" :loading="usdtRefreshing" @click="refreshUsdtOrder">
            <ReloadOutlined />
            刷新状态
          </a-button>
          <a-button v-if="usdtOrder.status === 'confirmed'" type="primary" @click="closeUsdtModal">
            <CheckCircleOutlined />
            完成
          </a-button>
          <a-button v-else @click="closeUsdtModal">关闭</a-button>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { message } from 'ant-design-vue'
import {
  WalletOutlined,
  CrownOutlined,
  CloseOutlined,
  EnvironmentOutlined,
  DollarOutlined,
  CopyOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons-vue'
import { getMembershipPlans, createUsdtOrder, getUsdtOrder } from '@/api/billing'

interface Billing {
  credits: number
  is_vip: boolean
  vip_expires_at: string | null
}

interface Plan {
  price_usd: number
  credits_once?: number
  credits_monthly?: number
}

interface UsdtOrder {
  order_id: string
  amount_usdt: number
  address: string
  chain: string
  status: string
  expires_at?: string
}

const loading = ref(false)
const purchasing = ref('')
const usdtModalVisible = ref(false)
const usdtOrder = ref<UsdtOrder | null>(null)
const usdtPollingTimer = ref<number | null>(null)
const usdtRefreshing = ref(false)

const billing = reactive<Billing>({
  credits: 0,
  is_vip: false,
  vip_expires_at: null,
})

const plans = reactive<Record<string, Plan>>({
  monthly: { price_usd: 19.9, credits_once: 500 },
  yearly: { price_usd: 199, credits_once: 8000 },
  lifetime: { price_usd: 499, credits_monthly: 800 },
})

const usdtQrUrl = computed(() => {
  const text = getUsdtQrText()
  if (!text) return ''
  return `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(text)}`
})

const statusText = computed(() => {
  const s = usdtOrder.value?.status || ''
  const map: Record<string, string> = {
    pending: '待支付',
    paid: '已支付',
    confirmed: '已确认',
    expired: '已过期',
    cancelled: '已取消',
    failed: '支付失败',
  }
  return map[s] || s || '--'
})

const statusColor = computed(() => {
  const s = usdtOrder.value?.status || ''
  if (s === 'confirmed') return 'green'
  if (s === 'paid') return 'blue'
  if (s === 'expired' || s === 'failed' || s === 'cancelled') return 'red'
  return 'orange'
})

const usdtStepCurrent = computed(() => {
  const s = usdtOrder.value?.status || ''
  if (s === 'confirmed') return 2
  if (s === 'paid') return 1
  return 0
})

const stepItems = ['待支付', '已支付', '已确认']

function getUsdtQrText(): string {
  if (!usdtOrder.value) return ''
  return usdtOrder.value.address || ''
}

function formatCredits(v: number): string {
  if (!v && v !== 0) return '0'
  return Number(v).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString()
}

function formatDateTime(dateStr: string): string {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString()
}

async function load() {
  loading.value = true
  try {
    const res = await getMembershipPlans()
    if (res && res.code === 1 && res.data) {
      Object.assign(plans, res.data.plans || plans)
      Object.assign(billing, res.data.billing || billing)
    } else {
      message.error(res?.msg || '加载失败')
    }
  } catch (e: any) {
    message.error(e?.response?.data?.msg || '加载失败')
  } finally {
    loading.value = false
  }
}

async function buy(plan: string) {
  purchasing.value = plan
  try {
    const res = await createUsdtOrder(plan)
    if (res && res.code === 1 && res.data) {
      usdtOrder.value = res.data
      usdtModalVisible.value = true
      startUsdtPolling()
    } else {
      message.error(res?.msg || '购买失败')
    }
  } catch (e: any) {
    message.error(e?.response?.data?.msg || '购买失败')
  } finally {
    purchasing.value = ''
  }
}

function copyText(txt: string) {
  try {
    const t = String(txt || '')
    if (!t) return
    navigator.clipboard.writeText(t)
    message.success('复制成功')
  } catch (e) {
    message.error('复制失败')
  }
}

async function refreshUsdtOrder() {
  if (!usdtOrder.value || !usdtOrder.value.order_id) return
  usdtRefreshing.value = true
  try {
    const res = await getUsdtOrder(usdtOrder.value.order_id, true)
    if (res && res.code === 1 && res.data) {
      usdtOrder.value = res.data
      const status = usdtOrder.value.status
      if (status === 'confirmed') {
        message.success('支付成功')
        stopUsdtPolling()
        await load()
      } else if (status === 'expired' || status === 'failed' || status === 'cancelled') {
        stopUsdtPolling()
      }
    }
  } catch (e) {
    // Ignore polling errors
  } finally {
    usdtRefreshing.value = false
  }
}

function startUsdtPolling() {
  stopUsdtPolling()
  usdtPollingTimer.value = window.setInterval(() => {
    refreshUsdtOrder()
  }, 5000)
}

function stopUsdtPolling() {
  if (usdtPollingTimer.value) {
    clearInterval(usdtPollingTimer.value)
    usdtPollingTimer.value = null
  }
}

function closeUsdtModal() {
  usdtModalVisible.value = false
  stopUsdtPolling()
}

onMounted(() => {
  load()
})

onBeforeUnmount(() => {
  stopUsdtPolling()
})
</script>

<style scoped>
.billing-page {
  padding: 18px;
}

.page-header {
  margin-bottom: 14px;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #1e3a5f;
}

.page-title .anticon {
  font-size: 22px;
  color: #1890ff;
}

.page-desc {
  margin: 6px 0 0;
  color: #64748b;
}

.snapshot-card {
  .snapshot-row {
    display: flex;
    gap: 18px;
    flex-wrap: wrap;
  }
  .snap-item {
    min-width: 220px;
    .snap-label { color: #64748b; font-size: 12px; }
    .snap-value { font-size: 18px; font-weight: 700; margin-top: 2px; }
    .vip-exp { margin-left: 8px; color: #94a3b8; font-size: 12px; }
  }
}

.plan-card {
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  margin-top: 12px;
  &.highlight { border: 1px solid rgba(24, 144, 255, 0.35); }
  .plan-title {
    font-weight: 700;
    font-size: 16px;
    color: #1e3a5f;
  }
  .plan-price {
    margin-top: 10px;
    font-size: 28px;
    font-weight: 800;
    color: #1e3a5f;
    .plan-unit {
      font-size: 12px;
      font-weight: 500;
      color: #64748b;
      margin-left: 6px;
    }
  }
  .plan-benefit {
    margin: 10px 0 16px;
    color: #475569;
    font-weight: 600;
  }
}
</style>

<style>
/* ===== Modal Wrapper ===== */
.usdt-pay-modal-wrap {
  .ant-modal-header { display: none; }
  .ant-modal-body { padding: 0 !important; }
  .ant-modal-content { border-radius: 16px; overflow: hidden; }
}

/* ===== Checkout UI ===== */
.usdt-checkout {
  /* -- Header -- */
  .checkout-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    background: linear-gradient(135deg, #26A17B 0%, #1b8a6b 100%);
    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;
      .usdt-logo {
        width: 40px; height: 40px; border-radius: 50%;
        background: rgba(255,255,255,0.18);
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0;
      }
      .header-text {
        .header-title { font-size: 16px; font-weight: 800; color: #fff; }
        .header-desc { font-size: 12px; color: rgba(255,255,255,0.75); margin-top: 2px; line-height: 1.4; }
      }
    }
    .close-btn {
      color: rgba(255,255,255,0.8) !important;
      font-size: 18px;
      &:hover { color: #fff !important; }
    }
  }

  /* -- Steps -- */
  .checkout-steps {
    display: flex;
    align-items: center;
    padding: 16px 24px 12px;
    .step-item {
      display: flex;
      align-items: center;
      gap: 6px;
      .step-dot {
        position: relative;
        width: 18px; height: 18px;
        display: flex; align-items: center; justify-content: center;
        .dot-inner {
          width: 10px; height: 10px; border-radius: 50%;
          background: #d9d9d9;
          transition: all 0.3s;
        }
        .dot-pulse {
          position: absolute;
          width: 18px; height: 18px; border-radius: 50%;
          background: rgba(38, 161, 123, 0.35);
          animation: pulse-ring 1.5s ease-out infinite;
        }
      }
      .step-label {
        font-size: 12px;
        color: #94a3b8;
        font-weight: 500;
        white-space: nowrap;
        transition: all 0.3s;
      }
      .step-line {
        flex: 1;
        height: 2px;
        min-width: 30px;
        background: #e8e8e8;
        margin: 0 6px;
        border-radius: 1px;
        transition: all 0.3s;
        &.filled { background: #26A17B; }
      }
      &.active {
        .dot-inner { background: #26A17B; }
        .step-label { color: #1e3a5f; font-weight: 700; }
      }
      &.current {
        .dot-inner { background: #26A17B; box-shadow: 0 0 0 3px rgba(38, 161, 123, 0.2); }
      }
    }
  }

  @keyframes pulse-ring {
    0% { transform: scale(0.8); opacity: 1; }
    100% { transform: scale(1.8); opacity: 0; }
  }

  /* -- Body -- */
  .checkout-body {
    display: flex;
    gap: 20px;
    padding: 4px 24px 16px;

    .qr-section {
      display: flex;
      flex-direction: column;
      align-items: center;
      flex-shrink: 0;

      .qr-frame {
        width: 180px; height: 180px;
        padding: 8px;
        border-radius: 14px;
        background: #fff;
        border: 2px solid #e8e8e8;
        display: flex; align-items: center; justify-content: center;
        position: relative;
        transition: border-color 0.4s;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        img { width: 100%; height: 100%; border-radius: 8px; }
        &.qr-confirmed {
          border-color: #26A17B;
          &::after {
            content: '\2713';
            position: absolute;
            top: -10px; right: -10px;
            width: 28px; height: 28px;
            background: #26A17B;
            color: #fff;
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 16px; font-weight: 700;
            box-shadow: 0 2px 8px rgba(38,161,123,0.4);
          }
        }
      }

      .qr-amount {
        margin-top: 12px;
        display: flex;
        align-items: baseline;
        gap: 4px;
        .amt-number {
          font-size: 22px;
          font-weight: 900;
          color: #1e3a5f;
          letter-spacing: -0.5px;
        }
        .amt-currency {
          font-size: 12px;
          font-weight: 700;
          color: #64748b;
        }
      }

      .qr-chain {
        margin-top: 4px;
      }
    }

    .info-section {
      flex: 1;
      min-width: 0;

      .info-block {
        margin-bottom: 14px;
        .info-label {
          display: flex; align-items: center; gap: 6px;
          font-size: 12px; color: #64748b; font-weight: 600;
          margin-bottom: 6px;
        }
      }

      .addr-box, .amt-box {
        display: flex;
        align-items: center;
        gap: 6px;
        background: #f6f8fa;
        border: 1px solid #e8e8e8;
        border-radius: 8px;
        padding: 8px 10px;

        code {
          flex: 1;
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Courier New", monospace;
          font-size: 12px;
          color: #1e3a5f;
          word-break: break-all;
          line-height: 1.5;
          background: none;
          border: none;
          padding: 0;
        }

        .copy-btn {
          flex-shrink: 0;
          border: none;
          background: rgba(0,0,0,0.04);
          color: #64748b;
          border-radius: 6px;
          &:hover {
            background: rgba(24, 144, 255, 0.08);
            color: #1890ff;
          }
        }
      }

      .warn-strip {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border-radius: 8px;
        background: rgba(250, 173, 20, 0.08);
        border: 1px solid rgba(250, 173, 20, 0.2);
        font-size: 12px;
        font-weight: 600;
        color: #d48806;
        margin-bottom: 14px;
      }

      .meta-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        .meta-expire {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 12px;
          color: #64748b;
        }
      }

      .expired-hint, .confirmed-hint {
        margin-top: 12px;
      }
    }
  }

  /* -- Footer -- */
  .checkout-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 24px 16px;
    border-top: 1px solid rgba(0,0,0,0.06);
  }
}

/* ===== Mobile ===== */
@media (max-width: 560px) {
  .usdt-checkout .checkout-body {
    flex-direction: column;
    align-items: center;
    .info-section { width: 100%; }
  }
}
</style>
