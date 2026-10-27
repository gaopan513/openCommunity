<template>
  <view class="oc-page detail-page">
    <template v-if="post.id">
      <!-- 帖子主体 -->
      <view class="oc-card">
        <view class="head">
          <image class="oc-avatar" :src="mediaUrl(post.author_info?.avatar)" mode="aspectFill" />
          <view class="head-info">
            <view class="author">{{ post.author_info?.username || '邻里用户' }}</view>
            <view class="meta-row">
              <text class="oc-tag" :style="{ background: tagBg, color: tagColor }">{{ typeLabel }}</text>
              <text v-if="post.is_top" class="oc-tag top-tag">置顶</text>
              <text class="time">{{ dateTime(post.created_at) }}</text>
            </view>
          </view>
          <text v-if="isMine" class="del-btn" @tap="handleDelete">删除</text>
        </view>

        <view class="title">{{ post.title }}</view>
        <view class="content">{{ post.content }}</view>

        <!-- 图片九宫格（点击大图预览） -->
        <view v-if="images.length" class="grid">
          <image
            v-for="(img, i) in images"
            :key="i"
            class="grid-img"
            :src="img"
            mode="aspectFill"
            @tap="previewImage(i)"
          />
        </view>

        <view v-if="post.tags" class="tags">
          <text v-for="tag in post.tags.split(',')" :key="tag" class="q-tag">#{{ tag }}</text>
        </view>

        <view class="foot">
          <text class="like" :class="{ liked: post.is_liked }" @tap="toggleLike">
            {{ post.is_liked ? '❤️' : '🤍' }} {{ post.like_count }}
          </text>
          <text class="views">👁 {{ post.view_count }}</text>
        </view>
      </view>

      <!-- 评论列表 -->
      <view class="oc-card">
        <view class="oc-section-title">评论 {{ post.comment_count ?? comments.length }}</view>
        <block v-if="comments.length">
          <view v-for="c in comments" :key="c.id" class="comment">
            <image class="oc-avatar c-avatar" :src="mediaUrl(c.author_info?.avatar)" mode="aspectFill" />
            <view class="c-body">
              <view class="c-head">
                <text class="c-author">{{ c.author_info?.username || '邻里用户' }}</text>
                <text class="c-reply-btn" @tap="startReply(c)">回复</text>
              </view>
              <view class="c-content">{{ c.content }}</view>

              <!-- 楼中楼回复 -->
              <view v-for="r in c.replies || []" :key="r.id" class="reply-item">
                <text class="c-author">{{ r.author_info?.username || '邻里用户' }}：</text>
                <text class="c-content--inline">{{ r.content }}</text>
              </view>
            </view>
          </view>
        </block>
        <view v-else class="oc-empty">还没有评论，来说两句</view>
      </view>
    </template>

    <!-- 底部评论输入条 -->
    <CommentBar
      ref="commentBar"
      :reply-to="pendingParent"
      :submitting="submitting"
      @submit="submitComment"
      @cancel-reply="cancelReply"
    />
  </view>
</template>

<script setup>
/**
 * 帖子详情：正文/图片预览/点赞/删除自己的帖子 + 两级评论与楼中楼回复。
 */
import { ref, computed } from 'vue'
import { onLoad, onShareAppMessage, onShareTimeline } from '@dcloudio/uni-app'
import { getPost, deletePost, likePost, addComment } from '@/api/discussion'
import { useUserStore } from '@/stores/user'
import { requireLogin } from '@/utils/auth'
import { mediaUrl, dateTime } from '@/utils/format'
import { POST_TYPE_MAP } from '@/constants/statusMaps'
import { EVENTS } from '@/constants'
import CommentBar from '@/components/CommentBar.vue'
import { track } from '@/utils/analytics'

const userStore = useUserStore()
const postId = ref(null)
const post = ref({})
const comments = ref([])
const pendingParent = ref(null)
// 提交防抖：防止快速双击发出重复评论
const submitting = ref(false)
const commentBar = ref(null)

const isMine = computed(() => userStore.userInfo?.id === post.value.author)
const typeLabel = computed(() => POST_TYPE_MAP[post.value.post_type]?.label || '闲聊')
const tagColor = computed(() => POST_TYPE_MAP[post.value.post_type]?.color || '#165dff')
const tagBg = computed(() =>
  post.value.post_type === 'help' ? '#ffece8' : post.value.post_type === 'share' ? '#e8f7ef' : '#ecf2ff'
)
// 详情接口返回嵌套 image 对象数组 [{id,image}]
const images = computed(() => (post.value.images || []).map((it) => mediaUrl(it.image)))

onLoad((options) => {
  postId.value = options.id
  load()
})

async function load() {
  try {
    const res = await getPost(postId.value)
    post.value = res.data
    // CommentSerializer 的 replies 仅一层嵌套；顶层评论 = parent 为空的记录
    comments.value = (res.data.comments || []).filter((c) => !c.parent)
  } catch {
    /* 已提示 */
  }
}

function previewImage(index) {
  uni.previewImage({ urls: images.value, current: index })
}

async function toggleLike() {
  if (!requireLogin()) return
  try {
    const res = await likePost(postId.value)
    // 后端 toggle 接口返回字段为 liked（非 is_liked）
    post.value.is_liked = res.data.liked
    post.value.like_count = res.data.like_count
    track('post_like', { is_liked: !!res.data.liked })
  } catch {
    /* 提示由请求层处理 */
  }
}

/** 提交评论：无 pendingParent 为楼层评论，否则为楼中楼 */
async function submitComment(content) {
  if (submitting.value) return
  if (!requireLogin()) return
  const payload = { content }
  if (pendingParent.value) payload.parent = pendingParent.value.id
  submitting.value = true
  try {
    await addComment(postId.value, payload)
    const wasReply = !!pendingParent.value
    commentBar.value?.clear()
    cancelReply()
    uni.showToast({ title: '评论成功', icon: 'none' })
    track('post_comment', { reply: wasReply })
    load()
  } catch {
    /* 提示由请求层处理 */
  } finally {
    submitting.value = false
  }
}

function startReply(comment) {
  pendingParent.value = comment
}
function cancelReply() {
  pendingParent.value = null
}

function handleDelete() {
  uni.showModal({
    title: '删除帖子',
    content: '删除后不可恢复，确定吗？',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await deletePost(postId.value)
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
  title: post.value.title || '邻里圈热帖',
  path: '/modules/posts/detail?id=' + postId.value,
}))

onShareTimeline(() => ({
  title: post.value.title || '邻里圈热帖',
  query: 'id=' + postId.value,
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
}
.author {
  font-size: 26rpx;
  font-weight: 600;
}
.meta-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 6rpx;
}
.time {
  color: var(--oc-text-secondary);
  font-size: 22rpx;
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
.grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 24rpx;
}
.grid-img {
  width: calc((100% - 24rpx) / 3);
  height: 210rpx;
  border-radius: 12rpx;
  background: #f0f0f0;
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

.comment {
  display: flex;
  gap: 18rpx;
  padding: 24rpx 0;
  border-bottom: 1rpx solid var(--oc-border);
}
.comment:last-child {
  border-bottom: none;
  padding-bottom: 0;
}
.c-avatar {
  width: 56rpx;
  height: 56rpx;
}
.c-body {
  flex: 1;
}
.c-head {
  display: flex;
  justify-content: space-between;
}
.c-author {
  font-size: 25rpx;
  font-weight: 600;
}
.c-reply-btn {
  color: var(--oc-primary);
  font-size: 23rpx;
}
.c-content {
  font-size: 28rpx;
  line-height: 1.6;
  margin-top: 8rpx;
}
.c-content--inline {
  font-size: 27rpx;
  line-height: 1.6;
}
.reply-item {
  background: #f7f8fa;
  border-radius: 10rpx;
  padding: 14rpx 18rpx;
  margin-top: 12rpx;
}
</style>
