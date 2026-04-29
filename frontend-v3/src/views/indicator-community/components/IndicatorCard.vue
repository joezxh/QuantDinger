<template>
  <a-card
    hoverable
    class="indicator-card"
    :body-style="{ padding: '16px' }"
    @click="$emit('click', indicator)"
  >
    <!-- Card Cover -->
    <template #cover>
      <div class="card-cover" :style="coverStyle">
        <img
          v-if="indicator.preview_image && !imageError"
          :src="indicator.preview_image"
          :alt="indicator.name"
          @error="handleImageError"
        />
        <!-- Default Cover -->
        <div v-else class="default-cover" :style="{ background: coverGradient }">
          <span class="cover-initials">{{ indicatorInitials }}</span>
          <span class="cover-title">{{ indicator.name }}</span>
        </div>
        
        <!-- Badges -->
        <div class="badges">
          <div class="price-tag" :class="isPaid ? 'paid' : 'free'">
            {{ isPaid ? `${indicator.price} 积分` : '免费' }}
          </div>
          <div v-if="indicator.vip_free" class="vip-tag">VIP 免费</div>
        </div>
        
        <div v-if="indicator.is_own" class="status-badge own">我的</div>
        <div v-else-if="indicator.is_purchased" class="status-badge purchased">
          <CheckCircleOutlined /> 已获授权
        </div>
      </div>
    </template>

    <!-- Content -->
    <div class="card-body">
      <h3 class="indicator-name">{{ indicator.name }}</h3>
      <p class="indicator-desc">{{ indicator.description || '暂无描述' }}</p>

      <div class="card-footer">
        <div class="author">
          <a-avatar :src="indicator.author?.avatar" :size="20" />
          <span class="author-name">{{ indicator.author?.nickname || indicator.author?.username }}</span>
        </div>
        
        <div class="stats">
          <span class="stat">
            <DownloadOutlined />
            {{ indicator.purchase_count || 0 }}
          </span>
          <span class="stat">
            <StarFilled style="color: #faad14" />
            {{ formatRating(indicator.avg_rating) }}
          </span>
        </div>
      </div>
    </div>
  </a-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { CheckCircleOutlined, DownloadOutlined, StarFilled } from '@ant-design/icons-vue'

const { t } = useI18n()
const props = defineProps<{
  indicator: any
}>()

defineEmits(['click'])

const imageError = ref(false)

const GRADIENT_PRESETS = [
  'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
  'linear-gradient(135deg, #f43f5e 0%, #fb923c 100%)',
  'linear-gradient(135deg, #0ea5e9 0%, #22d3ee 100%)',
  'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
  'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)'
]

const isPaid = computed(() => props.indicator.pricing_type !== 'free' && props.indicator.price > 0)

const coverGradient = computed(() => {
  const index = (props.indicator.id || 0) % GRADIENT_PRESETS.length
  return GRADIENT_PRESETS[index]
})

const indicatorInitials = computed(() => {
  const name = props.indicator.name || 'I'
  if (/[\u4e00-\u9fa5]/.test(name)) return name.slice(0, 2)
  return name.slice(0, 2).toUpperCase()
})

const coverStyle = computed(() => ({
  background: (!props.indicator.preview_image || imageError.value) ? coverGradient.value : '#f8fafc'
}))

const formatRating = (rating: any) => {
  const r = parseFloat(rating) || 0
  return r > 0 ? r.toFixed(1) : '-'
}

const handleImageError = () => {
  imageError.value = true
}
</script>

<style scoped lang="less">
.indicator-card {
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid #f1f5f9;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: #fff;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px -8px rgba(0, 0, 0, 0.1);
    border-color: #e2e8f0;
  }

  .card-cover {
    height: 160px;
    position: relative;
    overflow: hidden;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .default-cover {
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      color: #fff;
      padding: 20px;
      
      .cover-initials {
        font-size: 48px;
        font-weight: 800;
        opacity: 0.9;
        letter-spacing: -1px;
      }
      
      .cover-title {
        font-size: 12px;
        margin-top: 8px;
        opacity: 0.7;
        font-weight: 600;
        text-align: center;
      }
    }

    .badges {
      position: absolute;
      top: 12px;
      right: 12px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      align-items: flex-end;
    }

    .price-tag {
      padding: 4px 10px;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 700;
      color: #fff;
      backdrop-filter: blur(4px);
      
      &.free { background: rgba(16, 185, 129, 0.9); }
      &.paid { background: rgba(239, 68, 68, 0.9); }
    }

    .vip-tag {
      padding: 4px 10px;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 700;
      background: rgba(245, 158, 11, 0.9);
      color: #fff;
    }

    .status-badge {
      position: absolute;
      bottom: 12px;
      left: 12px;
      padding: 4px 10px;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 700;
      color: #fff;
      
      &.own { background: rgba(15, 23, 42, 0.8); }
      &.purchased { background: rgba(99, 102, 241, 0.9); }
    }
  }

  .card-body {
    .indicator-name {
      font-size: 16px;
      font-weight: 700;
      color: #1e293b;
      margin-bottom: 8px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .indicator-desc {
      font-size: 13px;
      color: #64748b;
      line-height: 1.6;
      height: 42px;
      margin-bottom: 16px;
      overflow: hidden;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }

    .card-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 12px;
      border-top: 1px solid #f1f5f9;

      .author {
        display: flex;
        align-items: center;
        gap: 8px;
        
        .author-name {
          font-size: 12px;
          font-weight: 600;
          color: #475569;
        }
      }

      .stats {
        display: flex;
        gap: 12px;
        
        .stat {
          font-size: 12px;
          color: #94a3b8;
          display: flex;
          align-items: center;
          gap: 4px;
        }
      }
    }
  }
}
</style>
