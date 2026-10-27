<template>
  <view class="list-wrap">
    <!-- 搜索栏 -->
    <view class="search-bar">
      <input
        v-model="keyword"
        class="oc-input search-input"
        placeholder="搜索帖子"
        confirm-type="search"
        @confirm="search"
      />
    </view>

    <!-- 类型筛选 -->
    <scroll-view class="chips" scroll-x>
      <view
        v-for="opt in typeOptions"
        :key="opt.value"
        class="oc-chip"
        :class="{ 'oc-chip--active': filterType === opt.value }"
        @tap="setFilterType(opt.value)"
      >
        {{ opt.label }}
      </view>
    </scroll-view>

    <!-- 排序 -->
    <view class="sort-row">
      <text class="sort-item" :class="{ active: ordering === '-created_at' }" @tap="setOrdering('-created_at')">
        最新
      </text>
      <text class="divider">|</text>
      <text class="sort-item" :class="{ active: ordering === '-like_count' }" @tap="setOrdering('-like_count')">
        最热
      </text>
    </view>

    <!-- 帖子流 -->
    <view class="post-list">
      <view v-for="post in posts" :key="post.id" class="oc-card post-card" @tap="goDetail(post.id)">
        <view class="post-head">
          <image class="oc-avatar head-avatar" :src="mediaUrl(post.author_info?.avatar)" mode="aspectFill" lazy-load />
          <view class="head-info">
            <view class="author">{{ post.author_info?.username || '邻里用户' }}</view>
            <view class="meta-row">
              <text class="oc-tag" :style="{ background: tagBg(post.post_type), color: tagColor(post.post_type) }">
                {{ POST_TYPE_MAP[post.post_type]?.label || '闲聊' }}
              </text>
              <text v-if="post.is_top" class="oc-tag top-tag">置顶</text>
              <text class="time">{{ shortDate(post.created_at) }}</text>
            </view>
          </view>
        </view>

        <view class="post-title">{{ post.title }}</view>
        <view class="post-excerpt">{{ (post.content || '').slice(0, 80) }}{{ (post.content || '').length > 80 ? '…' : '' }}</view>

        <view class="post-foot">
          <text class="stat">💬 {{ post.comment_count }}</text>
          <text class="stat" :class="{ liked: post.is_liked }" @tap.stop="toggleLike(post)">
            {{ post.is_liked ? '❤️' : '🤍' }} {{ post.like_count }}
          </text>
          <text class="stat stat--right">👁 {{ post.view_count }}</text>
        </view>
      </view>

      <view v-if="!loading && !posts.length" class="oc-empty">还没有帖子，点右下角发第一帖</view>
      <view v-if="loading" class="oc-loadmore">加载中…</view>
      <view v-else-if="loadError" class="oc-loadmore oc-loadmore--error" @tap="loadMore">加载失败，点击重试</view>
      <view v-else-if="finished && posts.length" class="oc-loadmore">没有更多了</view>
    </view>

    <view class="oc-fab" @tap="goCreate">＋</view>
  </view>
</template>

<script setup>
/**
 * 邻里圈列表：类型筛选 + 搜索 + 排序 + 分页加载（usePagedList 统一收口）。
 * 发帖成功后通过全局事件 EVENTS.LIST_CHANGED 触发刷新。
 */
import { ref } from 'vue'
import { getPosts, likePost } from '@/api/discussion'
import { mediaUrl, shortDate } from '@/utils/format'
import { requireLogin } from '@/utils/auth'
import { POST_TYPE_MAP } from '@/constants/statusMaps'
import { usePagedList } from '@/composables/usePagedList'
import { ROUTE } from '@/router/paths'

const typeOptions = [
  { value: '', label: '全部' },
  { value: 'chat', label: '闲聊' },
  { value: 'help', label: '求助' },
  { value: 'share', label: '分享' },
]

const filterType = ref('')
const keyword = ref('')
const ordering = ref('-created_at')

const {
  items: posts,
  loading,
  finished,
  loadError,
  loadFirst,
  loadMore,
} = usePagedList(async (pageNo) => {
  const params = { page: pageNo, page_size: 10, ordering: ordering.value }
  if (filterType.value) params.post_type = filterType.value
  if (keyword.value) params.search = keyword.value
  const res = await getPosts(params)
  return res.data
})

function setFilterType(v) {
  filterType.value = v
  loadFirst()
}
function setOrdering(v) {
  ordering.value = v
  loadFirst()
}
function search() {
  loadFirst()
}

/** 点赞（乐观更新；游客先引导登录） */
async function toggleLike(post) {
  if (!requireLogin()) return
  try {
    const res = await likePost(post.id)
    // 后端 toggle 接口返回字段为 liked（非 is_liked）
    post.is_liked = res.data.liked
    post.like_count = res.data.like_count
  } catch {
    /* 提示由请求层处理 */
  }
}

function goDetail(id) {
  uni.navigateTo({ url: ROUTE.postDetail(id) })
}
function goCreate() {
  if (!requireLogin()) return
  uni.navigateTo({ url: ROUTE.postCreate() })
}

function tagColor(t) {
  return POST_TYPE_MAP[t]?.color || '#165dff'
}
function tagBg(t) {
  return t === 'help' ? '#ffece8' : t === 'share' ? '#e8f7ef' : '#ecf2ff'
}
</script>

<style scoped>
.list-wrap {
  padding-bottom: 160rpx;
}
.search-bar {
  margin-bottom: 20rpx;
}
.chips {
  white-space: nowrap;
  margin-bottom: 16rpx;
}
.sort-row {
  font-size: 26rpx;
  color: var(--oc-text-secondary);
  margin-bottom: 20rpx;
}
.sort-item.active {
  color: var(--oc-primary);
  font-weight: 700;
}
.divider {
  margin: 0 20rpx;
  color: var(--oc-border);
}
.post-head {
  display: flex;
  align-items: center;
  gap: 18rpx;
  margin-bottom: 18rpx;
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
.top-tag {
  background: #fff3ec;
  color: var(--oc-primary);
}
.post-title {
  font-size: 32rpx;
  font-weight: 700;
  line-height: 1.4;
}
.post-excerpt {
  color: var(--oc-text-secondary);
  font-size: 27rpx;
  margin-top: 10rpx;
  line-height: 1.5;
}
.post-foot {
  display: flex;
  gap: 40rpx;
  margin-top: 20rpx;
  color: var(--oc-text-secondary);
  font-size: 24rpx;
}
.stat--right {
  margin-left: auto;
}
.stat.liked {
  color: var(--oc-danger);
}
</style>
