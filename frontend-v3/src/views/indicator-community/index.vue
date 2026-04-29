<template>
  <div class="community-container">
    <!-- Header Section -->
    <div class="community-header">
      <div class="header-content">
        <h1 class="page-title">
          <ShopOutlined /> 指标社区
        </h1>
        <p class="page-subtitle">探索、获取并分享最前沿的技术指标与量化策略</p>
        
        <div class="search-bar">
          <a-input-search
            v-model:value="filters.keyword"
            placeholder="搜索您感兴趣的指标..."
            enter-button="搜 索"
            size="large"
            @search="handleSearch"
          />
        </div>
      </div>
    </div>

    <div class="main-content">
      <!-- Admin Controls -->
      <div v-if="isAdmin" class="admin-controls">
        <a-tabs v-model:activeKey="activeTab" @change="handleTabChange">
          <a-tab-pane key="market" :tab="t('menu.indicatorMarket')" />
          <a-tab-pane key="review">
            <template #tab>
              <a-badge :count="reviewStats.pending" :offset="[12, 0]">审核管理</a-badge>
            </template>
          </a-tab-pane>
        </a-tabs>
      </div>

      <!-- Filters Row -->
      <div v-show="activeTab === 'market'" class="filters-row">
        <div class="filter-group">
          <a-radio-group v-model:value="filters.pricingType" button-style="solid" @change="handleFilterChange">
            <a-radio-button value="">全部</a-radio-button>
            <a-radio-button value="free">免费</a-radio-button>
            <a-radio-button value="paid">付费</a-radio-button>
          </a-radio-group>
          
          <a-select v-model:value="filters.sortBy" style="width: 160px" @change="handleFilterChange">
            <a-select-option value="newest">最新发布</a-select-option>
            <a-select-option value="hot">最热门</a-select-option>
            <a-select-option value="rating">评分最高</a-select-option>
            <a-select-option value="price_asc">价格从低到高</a-select-option>
            <a-select-option value="price_desc">价格从高到低</a-select-option>
          </a-select>
        </div>

        <div class="actions-group">
          <a-button type="link" @click="showMyPurchases = true">
            <ShoppingOutlined /> 我的获取
          </a-button>
          <a-button type="primary" shape="round" @click="goToCreate">
            <PlusOutlined /> 发布指标
          </a-button>
        </div>
      </div>

      <!-- Market View -->
      <template v-if="activeTab === 'market'">
        <a-spin :spinning="loading">
          <div v-if="indicators.length === 0 && !loading" class="empty-state">
            <a-empty description="未找到符合条件的指标">
              <a-button type="primary" @click="resetFilters">重置筛选</a-button>
            </a-empty>
          </div>
          <div v-else class="indicator-grid">
            <IndicatorCard
              v-for="item in indicators"
              :key="item.id"
              :indicator="item"
              @click="openDetail(item)"
            />
          </div>
        </a-spin>

        <!-- Pagination -->
        <div v-if="pagination.total > 0" class="pagination-area">
          <a-pagination
            v-model:current="pagination.current"
            :total="pagination.total"
            :page-size="pagination.pageSize"
            show-less-items
            @change="handlePageChange"
          />
        </div>
      </template>

      <!-- Admin Review View -->
      <template v-if="activeTab === 'review' && isAdmin">
        <div class="review-panel">
          <div class="review-filter">
            <a-radio-group v-model:value="reviewFilter" button-style="solid" @change="loadPendingIndicators">
              <a-radio-button value="pending">待审核 ({{ reviewStats.pending }})</a-radio-button>
              <a-radio-button value="approved">已发布 ({{ reviewStats.approved }})</a-radio-button>
              <a-radio-button value="rejected">已驳回 ({{ reviewStats.rejected }})</a-radio-button>
            </a-radio-group>
          </div>

          <a-table
            :columns="reviewColumns"
            :data-source="pendingIndicators"
            :loading="reviewLoading"
            :pagination="reviewPagination"
            @change="handleReviewTableChange"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'author'">
                <div class="user-cell">
                  <a-avatar :src="record.author?.avatar" size="small" />
                  <span>{{ record.author?.nickname || record.author?.username }}</span>
                </div>
              </template>
              <template v-if="column.key === 'price'">
                <a-tag :color="record.pricing_type === 'free' ? 'green' : 'orange'">
                  {{ record.pricing_type === 'free' ? '免费' : `${record.price} 积分` }}
                </a-tag>
              </template>
              <template v-if="column.key === 'status'">
                <a-badge :status="getStatusBadge(record.review_status)" :text="getStatusText(record.review_status)" />
              </template>
              <template v-if="column.key === 'actions'">
                <div class="table-actions">
                  <a-button type="link" size="small" @click="openDetail(record)">{{ t('common.view') }}</a-button>
                  <template v-if="record.review_status === 'pending'">
                    <a-button type="link" size="small" @click="handleReview(record, 'approve')">通过</a-button>
                    <a-button type="link" size="small" danger @click="handleReview(record, 'reject')">驳回</a-button>
                  </template>
                  <a-popconfirm title="确定删除吗？" @confirm="handleDelete(record)">
                    <a-button type="link" size="small" danger>{{ t('common.delete') }}</a-button>
                  </a-popconfirm>
                </div>
              </template>
            </template>
          </a-table>
        </div>
      </template>
    </div>

    <!-- Modals -->
    <IndicatorDetail
      :visible="detailVisible"
      :indicator-id="selectedIndicatorId"
      :current-user-id="currentUserId"
      @close="detailVisible = false"
      @purchased="handlePurchased"
    />

    <!-- My Purchases Modal -->
    <a-modal
      v-model:visible="showMyPurchases"
      title="我的获取"
      :footer="null"
      width="640px"
    >
      <a-spin :spinning="purchasesLoading">
        <a-list :data-source="myPurchases">
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta
                :title="item.indicator?.name"
                :description="`获取时间: ${new Date(item.purchase_time).toLocaleString()}`"
              >
                <template #avatar>
                  <div class="mini-cover" :style="{ background: getCoverGradient(item.indicator?.id) }">
                    {{ item.indicator?.name?.slice(0, 1) }}
                  </div>
                </template>
              </a-list-item-meta>
              <template #actions>
                <a-button type="link" @click="openDetail(item.indicator)">{{ t('common.detail') }}</a-button>
                <a-button type="primary" size="small" @click="goToUse">使用</a-button>
              </template>
            </a-list-item>
          </template>
        </a-list>
      </a-spin>
    </a-modal>

    <!-- Review Modal -->
    <a-modal
      v-model:visible="showReviewModal"
      :title="reviewAction === 'approve' ? '审核通过' : '驳回审核'"
      @ok="submitReview"
    >
      <a-form layout="vertical">
        <a-form-item label="审核备注">
          <a-textarea v-model:value="reviewNote" placeholder="请输入审核意见或建议..." :rows="4" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { 
  ShopOutlined, PlusOutlined, ShoppingOutlined, 
  SearchOutlined, RobotOutlined 
} from '@ant-design/icons-vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import IndicatorCard from './components/IndicatorCard.vue'
import IndicatorDetail from './components/IndicatorDetail.vue'
import { 
  getCommunityIndicators, 
  getMyPurchases, 
  getAdminReviewStats,
  getAdminPendingIndicators,
  reviewIndicator,
  adminDeleteIndicator
} from '@/api/indicator'

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()

const currentUserId = computed(() => userStore.userInfo?.id)
const isAdmin = computed(() => userStore.userInfo?.role === 'admin')

const loading = ref(false)
const indicators = ref<any[]>([])
const activeTab = ref('market')

const filters = reactive({
  keyword: '',
  pricingType: '',
  sortBy: 'newest'
})

const pagination = reactive({
  current: 1,
  pageSize: 12,
  total: 0
})

const detailVisible = ref(false)
const selectedIndicatorId = ref<number | string | null>(null)

const showMyPurchases = ref(false)
const purchasesLoading = ref(false)
const myPurchases = ref<any[]>([])

// Admin Review
const reviewFilter = ref('pending')
const reviewLoading = ref(false)
const pendingIndicators = ref<any[]>([])
const reviewStats = ref({ pending: 0, approved: 0, rejected: 0 })
const showReviewModal = ref(false)
const reviewAction = ref('approve')
const reviewNote = ref('')
const reviewingIndicator = ref<any>(null)

const reviewPagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0
})

const reviewColumns = [
  { title: '指标名称', dataIndex: 'name', key: 'name' },
  { title: '作者', key: 'author' },
  { title: t('quickTrade.price'), key: 'price' },
  { title: t('common.status'), key: 'status' },
  { title: t('common.createdAt'), dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: t('common.action'), key: 'actions', width: 220 }
]

onMounted(() => {
  loadIndicators()
  if (isAdmin.value) {
    loadReviewStats()
  }
})

const loadIndicators = async () => {
  loading.value = true
  try {
    const res = await getCommunityIndicators({
      page: pagination.current,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      pricing_type: filters.pricingType || undefined,
      sort_by: filters.sortBy
    })
    if (res.code === 1) {
      indicators.value = res.data.items || []
      pagination.total = res.data.total || 0
    }
  } catch (e) {
    message.error('加载指标失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.current = 1
  loadIndicators()
}

const handleFilterChange = () => {
  pagination.current = 1
  loadIndicators()
}

const handlePageChange = (page: number) => {
  pagination.current = page
  loadIndicators()
}

const resetFilters = () => {
  filters.keyword = ''
  filters.pricingType = ''
  filters.sortBy = 'newest'
  handleFilterChange()
}

const openDetail = (indicator: any) => {
  selectedIndicatorId.value = indicator.id
  detailVisible.value = true
}

const handlePurchased = () => {
  loadIndicators()
}

const goToCreate = () => {
  router.push('/indicator-ide')
}

const goToUse = () => {
  showMyPurchases.value = false
  router.push('/indicator-ide')
}

// My Purchases
watch(showMyPurchases, (val) => {
  if (val) loadMyPurchases()
})

const loadMyPurchases = async () => {
  purchasesLoading.value = true
  try {
    const res = await getMyPurchases()
    if (res.code === 1) {
      myPurchases.value = res.data.items || []
    }
  } catch (e) {
    message.error('加载我的获取失败')
  } finally {
    purchasesLoading.value = false
  }
}

// Admin Logic
const handleTabChange = (key: string) => {
  if (key === 'review') {
    loadPendingIndicators()
    loadReviewStats()
  }
}

const loadReviewStats = async () => {
  try {
    const res = await getAdminReviewStats()
    if (res.code === 1) {
      reviewStats.value = res.data
    }
  } catch (e) {}
}

const loadPendingIndicators = async () => {
  reviewLoading.value = true
  try {
    const res = await getAdminPendingIndicators({
      page: reviewPagination.current,
      page_size: reviewPagination.pageSize,
      review_status: reviewFilter.value
    })
    if (res.code === 1) {
      pendingIndicators.value = res.data.items
      reviewPagination.total = res.data.total
    }
  } catch (e) {
    message.error('加载审核列表失败')
  } finally {
    reviewLoading.value = false
  }
}

const handleReviewTableChange = (pag: any) => {
  reviewPagination.current = pag.current
  loadPendingIndicators()
}

const handleReview = (indicator: any, action: string) => {
  reviewingIndicator.value = indicator
  reviewAction.value = action
  reviewNote.value = ''
  showReviewModal.value = true
}

const submitReview = async () => {
  if (!reviewingIndicator.value) return
  try {
    const res = await reviewIndicator(reviewingIndicator.value.id, {
      action: reviewAction.value,
      note: reviewNote.value
    })
    if (res.code === 1) {
      message.success('审核处理成功')
      showReviewModal.value = false
      loadPendingIndicators()
      loadReviewStats()
    }
  } catch (e) {
    message.error('审核处理失败')
  }
}

const handleDelete = async (indicator: any) => {
  try {
    const res = await adminDeleteIndicator(indicator.id)
    if (res.code === 1) {
      message.success('删除成功')
      loadPendingIndicators()
      loadReviewStats()
    }
  } catch (e) {
    message.error(t('common.deleteFailed'))
  }
}

const getStatusBadge = (status: string) => {
  if (status === 'pending') return 'warning'
  if (status === 'approved') return 'success'
  if (status === 'rejected') return 'error'
  return 'default'
}

const getStatusText = (status: string) => {
  if (status === 'pending') return '待审核'
  if (status === 'approved') return '已发布'
  if (status === 'rejected') return '已驳回'
  return status
}

const getCoverGradient = (id: number) => {
  const gradients = [
    'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
    'linear-gradient(135deg, #f43f5e 0%, #fb923c 100%)',
    'linear-gradient(135deg, #0ea5e9 0%, #22d3ee 100%)',
    'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
    'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)'
  ]
  return gradients[(id || 0) % gradients.length]
}
</script>

<style scoped lang="less">
.community-container {
  min-height: 100vh;
  background: #f8fafc;
  padding-bottom: 60px;

  .community-header {
    background: #1e293b;
    padding: 60px 0 100px;
    text-align: center;
    color: #fff;
    position: relative;
    overflow: hidden;

    &::after {
      content: '';
      position: absolute;
      bottom: -50px; left: -10%; right: -10%; height: 100px;
      background: #f8fafc;
      border-radius: 50%;
    }

    .header-content {
      max-width: 800px;
      margin: 0 auto;
      position: relative;
      z-index: 1;

      .page-title {
        font-size: 42px;
        font-weight: 800;
        color: #fff;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 16px;
      }

      .page-subtitle {
        font-size: 18px;
        opacity: 0.7;
        margin-bottom: 40px;
      }

      .search-bar {
        max-width: 600px;
        margin: 0 auto;
        
        :deep(.ant-input-search) {
          .ant-input {
            border-radius: 12px 0 0 12px;
            height: 56px;
            font-size: 16px;
            border: none;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
          }
          .ant-input-search-button {
            height: 56px;
            width: 120px;
            border-radius: 0 12px 12px 0;
            background: #6366f1;
            border: none;
            font-weight: 700;
          }
        }
      }
    }
  }

  .main-content {
    max-width: 1200px;
    margin: -40px auto 0;
    position: relative;
    z-index: 10;
    padding: 0 24px;

    .admin-controls {
      background: #fff;
      padding: 0 24px;
      border-radius: 16px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
      margin-bottom: 24px;
    }

    .filters-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 32px;

      .filter-group {
        display: flex;
        gap: 20px;
        align-items: center;
      }

      .actions-group {
        display: flex;
        gap: 16px;
        align-items: center;
        
        .ant-btn-primary {
          height: 40px;
          padding: 0 24px;
          font-weight: 600;
        }
      }
    }

    .indicator-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 24px;
    }

    .empty-state {
      padding: 100px 0;
      background: #fff;
      border-radius: 20px;
    }

    .pagination-area {
      margin-top: 48px;
      display: flex;
      justify-content: center;
    }
    
    .review-panel {
      background: #fff;
      padding: 24px;
      border-radius: 16px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);

      .review-filter {
        margin-bottom: 24px;
      }

      .user-cell {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .table-actions {
        display: flex;
        gap: 8px;
      }
    }
  }
}

.mini-cover {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 800;
  font-size: 20px;
}
</style>
