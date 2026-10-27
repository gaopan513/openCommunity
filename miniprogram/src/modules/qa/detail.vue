<template>
  <view class="oc-page detail-page">
    <template v-if="question.id">
      <!-- 问题主体 -->
      <view class="oc-card">
        <view class="head">
          <image class="oc-avatar" :src="mediaUrl(question.author_info?.avatar)" mode="aspectFill" />
          <view class="head-info">
            <view class="author">{{ question.author_info?.username || '邻里用户' }}</view>
            <text class="oc-tag" :style="question.is_solved ? solvedStyle : unsolvedStyle">
              {{ question.is_solved ? '已解决' : '待解答' }}
            </text>
          </view>
          <text v-if="isMine" class="del-btn" @tap="handleDelete">删除</text>
        </view>

        <view class="title">{{ question.title }}</view>
        <view class="content">{{ question.content }}</view>
        <view v-if="question.tags?.length" class="tags">
          <text v-for="tag in question.tags" :key="tag.id" class="q-tag">#{{ tag.name }}</text>
        </view>
        <view class="foot">
          <text class="like" :class="{ liked: question.is_liked }" @tap="toggleLike">
            {{ question.is_liked ? '❤️' : '🤍' }} {{ question.like_count }}
          </text>
          <text>💬 {{ question.answer_count }}</text>
          <text>👁 {{ question.view_count }}</text>
        </view>
      </view>

      <!-- 回答列表 -->
      <view class="oc-section-title answer-title">回答 {{ answers.length }}</view>
      <view v-for="ans in answers" :key="ans.id" class="oc-card answer-card" :class="{ accepted: ans.is_accepted }">
        <view class="a-head">
          <image class="oc-avatar a-avatar" :src="mediaUrl(ans.author_info?.avatar)" mode="aspectFill" />
          <view class="a-info">
            <view class="author">{{ ans.author_info?.username || '邻里用户' }}</view>
            <view class="time">{{ dateTime(ans.created_at) }}</view>
          </view>
          <view v-if="ans.is_accepted" class="accepted-badge">✓ 已采纳</view>
        </view>
        <view class="a-content">{{ ans.content }}</view>
        <view class="a-foot">
          <text class="a-like" :class="{ liked: ans.is_liked }" @tap="toggleAnswerLike(ans)">
            {{ ans.is_liked ? '❤️' : '🤍' }} {{ ans.like_count }}
          </text>
          <text v-if="canAccept && !ans.is_accepted" class="adopt-btn" @tap="adopt(ans)">采纳为最佳答案</text>
        </view>
      </view>
      <view v-if="!answers.length" class="oc-empty">还没有回答，快来帮帮他</view>
    </template>

    <!-- 底部回答输入条 -->
    <CommentBar
      ref="commentBar"
      placeholder="分享你的经验，帮助邻里"
      btn-text="回答"
      :submitting="submitting"
      @submit="submitAnswer"
    />
  </view>
</template>

<script setup>
/**
 * 问题详情：问题正文 + 回答列表。
 * 提问者可采纳最佳答案（仅问题未解决时可采纳，后端同步兜底校验）。
 */
import { ref, computed } from 'vue'
import { onLoad, onShareAppMessage, onShareTimeline } from '@dcloudio/uni-app'
import { getQuestion, deleteQuestion, addAnswer, acceptAnswer, likeQuestion, likeAnswer } from '@/api/qa'
import { useUserStore } from '@/stores/user'
import { requireLogin } from '@/utils/auth'
import { mediaUrl, dateTime } from '@/utils/format'
import { EVENTS } from '@/constants'
import CommentBar from '@/components/CommentBar.vue'
import { track } from '@/utils/analytics'

const userStore = useUserStore()
const questionId = ref(null)
const question = ref({})
const answers = computed(() => question.value.answers || [])
// 提交防抖：防止快速双击发出重复回答
const submitting = ref(false)
const commentBar = ref(null)

const isMine = computed(() => userStore.userInfo?.id === question.value.author)
// 仅提问者且问题未解决时展示采纳入口
const canAccept = computed(() => isMine.value && !question.value.is_solved)

const solvedStyle = { background: '#e8f7ef', color: '#00b42a' }
const unsolvedStyle = { background: '#fff3ec', color: '#ff7d00' }

onLoad((options) => {
  questionId.value = options.id
  load()
})

async function load() {
  try {
    const res = await getQuestion(questionId.value)
    question.value = res.data
  } catch {
    /* 提示由请求层处理 */
  }
}

async function toggleLike() {
  if (!requireLogin()) return
  try {
    const res = await likeQuestion(questionId.value)
    // 后端 toggle 接口返回字段为 liked（非 is_liked）
    question.value.is_liked = res.data.liked
    question.value.like_count = res.data.like_count
  } catch {
    /* 提示由请求层处理 */
  }
}

async function toggleAnswerLike(ans) {
  if (!requireLogin()) return
  try {
    const res = await likeAnswer(questionId.value, ans.id)
    ans.is_liked = res.data.liked
    ans.like_count = res.data.like_count
  } catch {
    /* 提示由请求层处理 */
  }
}

async function submitAnswer(content) {
  if (submitting.value) return
  if (!requireLogin()) return
  submitting.value = true
  try {
    await addAnswer(questionId.value, { content })
    commentBar.value?.clear()
    uni.showToast({ title: '回答成功', icon: 'none' })
    track('qa_answer')
    load()
  } catch {
    /* 提示由请求层处理 */
  } finally {
    submitting.value = false
  }
}

function adopt(answer) {
  uni.showModal({
    title: '采纳答案',
    content: '确定采纳该回答为最佳答案吗？',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await acceptAnswer(questionId.value, answer.id)
        uni.showToast({ title: '已采纳', icon: 'success' })
        load()
      } catch {
        /* 提示由请求层处理 */
      }
    },
  })
}

function handleDelete() {
  uni.showModal({
    title: '删除问题',
    content: '删除后不可恢复，确定吗？',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await deleteQuestion(questionId.value)
        uni.$emit(EVENTS.LIST_CHANGED)
        uni.showToast({ title: '已删除', icon: 'none' })
        setTimeout(() => uni.navigateBack(), 500)
      } catch {
        /* 提示由请求层处理 */
      }
    },
  })
}

onShareAppMessage(() => ({
  title: question.value.title || '邻里问答',
  path: '/modules/qa/detail?id=' + questionId.value,
}))

onShareTimeline(() => ({
  title: question.value.title || '邻里问答',
  query: 'id=' + questionId.value,
}))
</script>

<style scoped>
.detail-page {
  padding-bottom: 200rpx;
}
.head {
  display: flex;
  align-items: center;
  gap: 18rpx;
}
.head-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 14rpx;
}
.author {
  font-size: 26rpx;
  font-weight: 600;
}
.del-btn {
  color: var(--oc-text-secondary);
  font-size: 24rpx;
}
.title {
  font-size: 38rpx;
  font-weight: 700;
  line-height: 1.4;
  margin: 24rpx 0 16rpx;
}
.content {
  font-size: 30rpx;
  line-height: 1.7;
  white-space: pre-wrap;
}
.tags {
  margin-top: 20rpx;
}
.q-tag {
  color: var(--oc-primary);
  font-size: 24rpx;
  margin-right: 16rpx;
}
.foot {
  display: flex;
  gap: 40rpx;
  margin-top: 28rpx;
  padding-top: 20rpx;
  border-top: 1rpx solid var(--oc-border);
  font-size: 26rpx;
  color: var(--oc-text-secondary);
}
.like.liked {
  color: var(--oc-danger);
}

.answer-title {
  display: block;
}
.answer-card.accepted {
  border: 1rpx solid #b7eb8f;
  background: #fafff5;
}
.a-head {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.a-avatar {
  width: 56rpx;
  height: 56rpx;
}
.a-info {
  flex: 1;
}
.time {
  color: var(--oc-text-secondary);
  font-size: 22rpx;
  margin-top: 4rpx;
}
.accepted-badge {
  color: var(--oc-success);
  font-size: 24rpx;
  font-weight: 700;
}
.a-content {
  font-size: 29rpx;
  line-height: 1.7;
  margin-top: 18rpx;
}
.a-foot {
  display: flex;
  align-items: center;
  gap: 32rpx;
  margin-top: 12rpx;
}
.a-like {
  margin-right: auto;
  font-size: 26rpx;
  color: var(--oc-text-secondary);
}
.a-like.liked {
  color: var(--oc-danger);
}
.adopt-btn {
  color: var(--oc-primary);
  font-size: 26rpx;
  font-weight: 600;
}
</style>
