<template>
  <a-modal
    :visible="visible"
    :title="null"
    :footer="null"
    :width="800"
    :body-style="{ padding: 0 }"
    @cancel="$emit('close')"
    class="indicator-detail-modal"
  >
    <a-spin :spinning="loading">
      <div v-if="detail" class="detail-container">
        <!-- Hero Header -->
        <div class="hero-header" :style="headerStyle">
          <div class="header-overlay"></div>
          <div class="header-content">
            <div class="cover-wrapper">
              <img v-if="detail.preview_image" :src="detail.preview_image" :alt="detail.name" />
              <div v-else class="default-cover">
                <span>{{ indicatorInitials }}</span>
              </div>
            </div>
            
            <div class="basic-info">
              <h2 class="name">{{ detail.name }}</h2>
              <div class="meta">
                <div class="author">
                  <a-avatar :src="detail.author?.avatar" :size="32" />
                  <span>{{ detail.author?.nickname || detail.author?.username }}</span>
                </div>
                <div class="divider"></div>
                <div class="date">发布于 {{ formatDate(detail.created_at) }}</div>
              </div>
              
              <div class="quick-stats">
                <div class="stat">
                  <div class="val">{{ detail.purchase_count || 0 }}</div>
                  <div class="lbl">获取次数</div>
                </div>
                <div class="stat">
                  <div class="val">
                    <a-rate :value="detail.avg_rating" disabled allow-half />
                    <span class="count">({{ detail.rating_count || 0 }})</span>
                  </div>
                  <div class="lbl">用户评分</div>
                </div>
                <div class="stat">
                  <div class="val">{{ detail.view_count || 0 }}</div>
                  <div class="lbl">浏览量</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Body Content -->
        <div class="detail-body">
          <a-tabs v-model:activeKey="activeTab" class="detail-tabs">
            <a-tab-pane key="overview" tab="概览信息">
              <div class="tab-content">
                <section class="desc-section">
                  <h3>指标描述</h3>
                  <p class="description">{{ detail.description || '暂无详细描述' }}</p>
                </section>

                <section v-if="performance" class="perf-section">
                  <h3>实盘表现</h3>
                  <div class="perf-grid">
                    <div class="perf-card">
                      <div class="label">关联策略</div>
                      <div class="value">{{ performance.strategy_count }}</div>
                    </div>
                    <div class="perf-card">
                      <div class="label">累计交易</div>
                      <div class="value">{{ performance.trade_count }}</div>
                    </div>
                    <div class="perf-card">
                      <div class="label">平均胜率</div>
                      <div class="value highlight" :class="performance.win_rate >= 50 ? 'up' : 'down'">
                        {{ performance.win_rate }}%
                      </div>
                    </div>
                    <div class="perf-card">
                      <div class="label">总盈亏</div>
                      <div class="value highlight" :class="performance.total_profit >= 0 ? 'up' : 'down'">
                        {{ performance.total_profit >= 0 ? '+' : '' }}{{ performance.total_profit }}
                      </div>
                    </div>
                  </div>
                </section>
              </div>
            </a-tab-pane>
            
            <a-tab-pane key="reviews" :tab="`评价交流 (${comments.total})`">
              <div class="tab-content">
                <comment-list
                  :comments="comments.items"
                  :loading="commentsLoading"
                  :can-comment="detail.is_purchased && !detail.is_own && !myComment"
                  :current-user-id="currentUserId"
                  :my-comment="myComment"
                  :total="comments.total"
                  @add-comment="handleAddComment"
                  @update-comment="handleUpdateComment"
                  @load-more="loadMoreComments"
                />
              </div>
            </a-tab-pane>
          </a-tabs>
        </div>

        <!-- Footer Actions -->
        <div class="detail-footer">
          <div class="price-area">
            <template v-if="detail.vip_free">
              <a-tag color="gold" class="vip-tag">VIP 免费</a-tag>
            </template>
            <span v-if="detail.pricing_type === 'free' || detail.price <= 0" class="price free">免费获取</span>
            <span v-else class="price paid">{{ detail.price }} <small>积分</small></span>
          </div>
          
          <div class="action-btns">
            <template v-if="detail.is_own">
              <a-button disabled size="large">您是该指标的作者</a-button>
            </template>
            <template v-else-if="detail.is_purchased">
              <a-badge :dot="!!detail.has_update">
                <a-button :loading="syncing" size="large" @click="handleSyncCode">
                  <SyncOutlined :spin="syncing" /> {{ syncing ? '同步中...' : '同步最新代码' }}
                </a-button>
              </a-badge>
              <a-button type="primary" size="large" @click="goToUse">
                <CodeOutlined /> 立即使用
              </a-button>
            </template>
            <a-button
              v-else
              type="primary"
              size="large"
              :loading="purchasing"
              class="buy-btn"
              @click="handlePurchase"
            >
              <ShoppingCartOutlined />
              {{ (detail.pricing_type === 'free' || detail.price <= 0) ? '免费领取' : '立即购买' }}
            </a-button>
          </div>
        </div>
      </div>
    </a-spin>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { message, Modal } from 'ant-design-vue'
import { SyncOutlined, CodeOutlined, ShoppingCartOutlined } from '@ant-design/icons-vue'
import { useRouter } from 'vue-router'
import CommentList from './CommentList.vue'
import { 
  getIndicatorCommunityDetail, 
  getIndicatorPerformance, 
  getIndicatorComments, 
  getMyIndicatorComment,
  purchaseIndicator,
  syncIndicatorCode,
  addIndicatorComment,
  updateIndicatorComment
} from '@/api/indicator'

const { t } = useI18n()
const props = defineProps<{
  visible: boolean
  indicatorId: number | string | null
  currentUserId: number | string | undefined
}>()

const emit = defineEmits(['close', 'purchased', 'synced'])
const router = useRouter()

const loading = ref(false)
const purchasing = ref(false)
const syncing = ref(false)
const commentsLoading = ref(false)
const activeTab = ref('overview')

const detail = ref<any>(null)
const performance = ref<any>(null)
const myComment = ref<any>(null)
const comments = ref({ items: [], total: 0, page: 1 })

const GRADIENT_PRESETS = [
  'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
  'linear-gradient(135deg, #f43f5e 0%, #fb923c 100%)',
  'linear-gradient(135deg, #0ea5e9 0%, #22d3ee 100%)',
  'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
  'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)'
]

const headerStyle = computed(() => {
  if (!detail.value) return {}
  const index = (detail.value.id || 0) % GRADIENT_PRESETS.length
  return { background: GRADIENT_PRESETS[index] }
})

const indicatorInitials = computed(() => {
  if (!detail.value) return ''
  const name = detail.value.name || 'I'
  if (/[\u4e00-\u9fa5]/.test(name)) return name.slice(0, 2)
  return name.slice(0, 2).toUpperCase()
})

watch(() => props.visible, (val) => {
  if (val && props.indicatorId) {
    loadAllData()
  } else {
    resetData()
  }
})

const resetData = () => {
  detail.value = null
  performance.value = null
  comments.value = { items: [], total: 0, page: 1 }
  myComment.value = null
  activeTab.value = 'overview'
}

const loadAllData = async () => {
  loading.value = true
  try {
    const id = props.indicatorId!
    const [detailRes, perfRes, commentRes, myCommentRes] = await Promise.all([
      getIndicatorCommunityDetail(id),
      getIndicatorPerformance(id),
      getIndicatorComments(id, { page: 1, page_size: 10 }),
      getMyIndicatorComment(id)
    ])

    if (detailRes.code === 1) detail.value = detailRes.data
    if (perfRes.code === 1) performance.value = perfRes.data
    if (commentRes.code === 1) {
      comments.value.items = commentRes.data.items
      comments.value.total = commentRes.data.total
    }
    if (myCommentRes.code === 1) myComment.value = myCommentRes.data
  } catch (e) {
    message.error('加载详情失败')
  } finally {
    loading.value = false
  }
}

const loadMoreComments = async () => {
  if (comments.value.items.length >= comments.value.total) return
  
  commentsLoading.value = true
  try {
    const page = comments.value.page + 1
    const res = await getIndicatorComments(props.indicatorId!, { page, page_size: 10 })
    if (res.code === 1) {
      comments.value.items = [...comments.value.items, ...res.data.items] as any
      comments.value.page = page
    }
  } catch (e) {
    message.error('加载更多评价失败')
  } finally {
    commentsLoading.value = false
  }
}

const handleAddComment = async (data: any) => {
  try {
    const res = await addIndicatorComment(props.indicatorId!, data)
    if (res.code === 1) {
      message.success('评价成功')
      loadAllData() // Reload to update scores and list
    } else {
      message.error(res.msg || '评价失败')
    }
  } catch (e) {
    message.error('评价失败')
  }
}

const handleUpdateComment = async (data: any) => {
  try {
    const res = await updateIndicatorComment(props.indicatorId!, data.comment_id, {
      rating: data.rating,
      content: data.content
    })
    if (res.code === 1) {
      message.success('更新评价成功')
      loadAllData()
    } else {
      message.error(res.msg || '更新评价失败')
    }
  } catch (e) {
    message.error('更新评价失败')
  }
}

const handlePurchase = async () => {
  purchasing.value = true
  try {
    const res = await purchaseIndicator(props.indicatorId!)
    if (res.code === 1) {
      message.success('获取成功')
      loadAllData()
      emit('purchased')
    } else {
      message.error(res.msg || '获取失败')
    }
  } catch (e) {
    message.error('获取失败')
  } finally {
    purchasing.value = false
  }
}

const handleSyncCode = () => {
  Modal.confirm({
    title: '同步代码',
    content: '同步操作将覆盖您本地 IDE 中的同名指标代码，是否继续？',
    onOk: async () => {
      syncing.value = true
      try {
        const res = await syncIndicatorCode(props.indicatorId!)
        if (res.code === 1) {
          message.success('同步成功')
          loadAllData()
          emit('synced')
        } else {
          message.error(res.msg || '同步失败')
        }
      } catch (e) {
        message.error('同步失败')
      } finally {
        syncing.value = false
      }
    }
  })
}

const goToUse = () => {
  emit('close')
  router.push('/indicator-ide')
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString()
}
</script>

<style scoped lang="less">
.indicator-detail-modal {
  :deep(.ant-modal-content) {
    border-radius: 20px;
    overflow: hidden;
  }

  .detail-container {
    display: flex;
    flex-direction: column;
    background: #fff;
  }

  .hero-header {
    height: 240px;
    position: relative;
    padding: 40px;
    display: flex;
    align-items: flex-end;
    color: #fff;

    .header-overlay {
      position: absolute;
      top: 0; left: 0; right: 0; bottom: 0;
      background: linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,0.4) 100%);
    }

    .header-content {
      position: relative;
      z-index: 1;
      display: flex;
      gap: 32px;
      width: 100%;
      align-items: flex-end;

      .cover-wrapper {
        width: 240px;
        height: 150px;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 12px 32px -8px rgba(0,0,0,0.3);
        border: 4px solid rgba(255,255,255,0.2);
        background: #fff;

        img { width: 100%; height: 100%; object-fit: cover; }
        
        .default-cover {
          width: 100%; height: 100%;
          display: flex; align-items: center; justify-content: center;
          font-size: 64px; font-weight: 800; opacity: 0.2; color: #000;
        }
      }

      .basic-info {
        flex: 1;
        .name { font-size: 32px; font-weight: 800; color: #fff; margin-bottom: 8px; }
        .meta {
          display: flex; align-items: center; gap: 16px; margin-bottom: 24px;
          .author { display: flex; align-items: center; gap: 8px; font-weight: 600; }
          .divider { width: 1px; height: 12px; background: rgba(255,255,255,0.3); }
          .date { font-size: 13px; opacity: 0.8; }
        }
      }

      .quick-stats {
        display: flex; gap: 40px;
        .stat {
          .val { 
            font-size: 20px; font-weight: 800; 
            display: flex; align-items: center; gap: 8px;
            .count { font-size: 14px; font-weight: 400; opacity: 0.8; }
          }
          .lbl { font-size: 12px; font-weight: 600; opacity: 0.6; text-transform: uppercase; letter-spacing: 1px; }
        }
      }
    }
  }

  .detail-body {
    padding: 0 40px 40px;
    min-height: 400px;
    
    .detail-tabs {
      :deep(.ant-tabs-nav) {
        margin-bottom: 32px;
        &::before { border-bottom: 1px solid #f1f5f9; }
      }
    }

    .tab-content {
      section {
        margin-bottom: 40px;
        h3 { font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 20px; }
        .description { font-size: 15px; color: #475569; line-height: 1.8; white-space: pre-wrap; }
      }

      .perf-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
        
        .perf-card {
          background: #f8fafc;
          padding: 20px;
          border-radius: 16px;
          border: 1px solid #f1f5f9;
          text-align: center;
          
          .label { font-size: 12px; color: #64748b; margin-bottom: 8px; font-weight: 600; }
          .value { 
            font-size: 24px; font-weight: 800; color: #1e293b;
            &.highlight.up { color: #10b981; }
            &.highlight.down { color: #ef4444; }
          }
        }
      }
    }
  }

  .detail-footer {
    padding: 24px 40px;
    border-top: 1px solid #f1f5f9;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #fff;
    position: sticky;
    bottom: 0;

    .price-area {
      display: flex; align-items: center; gap: 12px;
      .vip-tag { border-radius: 6px; font-weight: 700; }
      .price {
        font-size: 28px; font-weight: 800;
        &.free { color: #10b981; }
        &.paid { color: #ef4444; small { font-size: 14px; opacity: 0.6; } }
      }
    }

    .action-btns {
      display: flex; gap: 16px;
      .ant-btn { 
        height: 48px; border-radius: 12px; font-weight: 700; padding: 0 32px;
        display: flex; align-items: center; gap: 8px;
      }
      .buy-btn { background: #1e293b; border-color: #1e293b; }
    }
  }
}
</style>
