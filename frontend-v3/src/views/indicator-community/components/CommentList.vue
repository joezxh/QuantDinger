<template>
  <div class="comment-list">
    <!-- Comment Form -->
    <div v-if="canComment || isEditing" class="comment-form">
      <div class="form-header" v-if="isEditing">
        <span class="edit-label">编辑评价</span>
        <a-button type="link" size="small" @click="cancelEdit">取消编辑</a-button>
      </div>
      
      <div class="rating-input">
        <span class="label">您的评分:</span>
        <a-rate v-model:value="formData.rating" />
      </div>
      
      <a-textarea
        v-model:value="formData.content"
        placeholder="写下您对该指标的使用体验..."
        :rows="3"
        :max-length="500"
      />
      
      <div class="form-footer">
        <span class="char-count">{{ formData.content.length }}/500</span>
        <a-button type="primary" :loading="submitting" @click="submitComment">
          {{ isEditing ? '更新评价' : '发表评价' }}
        </a-button>
      </div>
    </div>

    <!-- Already Commented Hint -->
    <div v-else-if="myComment && !canComment && !isEditing" class="my-comment-hint">
      <CheckCircleTwoTone two-tone-color="#52c41a" />
      <span>您已评价过该指标</span>
      <a-button type="link" size="small" @click="startEdit(myComment)">
        修改我的评价
      </a-button>
    </div>

    <!-- Comments List -->
    <a-spin :spinning="loading">
      <div v-if="comments.length === 0" class="empty-state">
        <a-empty description="暂无评价" />
      </div>
      <div v-else class="comments-container">
        <div 
          v-for="comment in comments" 
          :key="comment.id" 
          class="comment-item"
          :class="{ 'is-mine': comment.user?.id === currentUserId }"
        >
          <div class="comment-header">
            <a-avatar :src="comment.user?.avatar" :size="40" />
            <div class="user-info">
              <div class="name">
                {{ comment.user?.nickname || comment.user?.username }}
                <a-tag v-if="comment.user?.id === currentUserId" color="blue" size="small">我</a-tag>
              </div>
              <div class="meta">
                <a-rate :value="comment.rating" disabled style="font-size: 12px" />
                <span class="time">{{ formatTime(comment.created_at) }}</span>
                <span v-if="comment.updated_at !== comment.created_at" class="edited">(已编辑)</span>
              </div>
            </div>
            
            <div v-if="comment.user?.id === currentUserId" class="actions">
              <a-button type="link" size="small" @click="startEdit(comment)">
                <EditOutlined />
              </a-button>
            </div>
          </div>
          <div class="comment-content">{{ comment.content }}</div>
        </div>
      </div>
    </a-spin>

    <div v-if="hasMore" class="load-more">
      <a-button type="link" @click="$emit('load-more')">加载更多评价</a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { CheckCircleTwoTone, EditOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const props = defineProps<{
  comments: any[]
  total: number
  loading: boolean
  canComment: boolean
  currentUserId: number | string | undefined
  myComment: any | null
}>()

const emit = defineEmits(['add-comment', 'update-comment', 'load-more'])

const submitting = ref(false)
const isEditing = ref(false)
const editingCommentId = ref<number | string | null>(null)

const formData = reactive({
  rating: 5,
  content: ''
})

const hasMore = computed(() => props.comments.length < props.total)

watch(() => props.myComment, (val) => {
  if (val && isEditing.value) {
    formData.rating = val.rating || 5
    formData.content = val.content || ''
    editingCommentId.value = val.id
  }
}, { immediate: true })

const startEdit = (comment: any) => {
  isEditing.value = true
  editingCommentId.value = comment.id
  formData.rating = comment.rating || 5
  formData.content = comment.content || ''
}

const cancelEdit = () => {
  isEditing.value = false
  editingCommentId.value = null
  formData.rating = 5
  formData.content = ''
}

const submitComment = async () => {
  if (formData.rating < 1) return
  
  submitting.value = true
  try {
    const data = {
      rating: formData.rating,
      content: formData.content.trim()
    }

    if (isEditing.value && editingCommentId.value) {
      emit('update-comment', {
        comment_id: editingCommentId.value,
        ...data
      })
    } else {
      emit('add-comment', data)
    }
    
    cancelEdit()
  } finally {
    submitting.value = false
  }
}

const formatTime = (time: string) => {
  return dayjs(time).fromNow()
}
</script>

<style scoped lang="less">
.comment-list {
  .comment-form {
    background: #f8fafc;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 24px;
    border: 1px solid #f1f5f9;

    .form-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 12px;
      .edit-label { font-weight: 600; color: #6366f1; }
    }

    .rating-input {
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 12px;
      .label { font-size: 13px; color: #475569; }
    }

    .form-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 12px;
      .char-count { font-size: 12px; color: #94a3b8; }
    }
  }

  .my-comment-hint {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 20px;
    background: #f0fdf4;
    border: 1px solid #dcfce7;
    border-radius: 12px;
    margin-bottom: 24px;
    color: #166534;
    font-size: 14px;
  }

  .comment-item {
    padding: 24px 0;
    border-bottom: 1px solid #f1f5f9;
    
    &:last-child { border-bottom: none; }
    
    &.is-mine {
      background: #fdfeff;
      padding: 24px;
      margin: 0 -24px;
      border-radius: 12px;
    }

    .comment-header {
      display: flex;
      gap: 16px;
      margin-bottom: 12px;
      position: relative;

      .user-info {
        flex: 1;
        .name {
          font-weight: 700;
          color: #1e293b;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .meta {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-top: 2px;
          .time { font-size: 12px; color: #94a3b8; }
          .edited { font-size: 12px; color: #cbd5e1; font-style: italic; }
        }
      }

      .actions {
        opacity: 0;
        transition: opacity 0.2s;
      }
    }

    &:hover .actions { opacity: 1; }

    .comment-content {
      padding-left: 56px;
      color: #334155;
      line-height: 1.7;
      white-space: pre-wrap;
    }
  }

  .load-more {
    text-align: center;
    padding: 20px 0;
  }
}
</style>
