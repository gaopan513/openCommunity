<template>
  <view class="list-wrap">
    <!-- 搜索栏 -->
    <view class="search-bar">
      <input
        v-model="keyword"
        class="oc-input search-input"
        placeholder="搜索问题"
        confirm-type="search"
        @confirm="search"
      />
    </view>

    <!-- 解决状态筛选 -->
    <scroll-view class="chips" scroll-x>
      <view
        v-for="opt in solveOptions"
        :key="String(opt.value)"
        class="oc-chip"
        :class="{ 'oc-chip--active': filterSolved === opt.value }"
        @tap="setFilter(opt.value)"
      >
        {{ opt.label }}
      </view>
    </scroll-view>

    <view class="sort-row">
      <text class="sort-item" :class="{ active: ordering === '-created_at' }" @tap="setOrdering('-created_at')">
        最新
      </text>
      <text class="divider">|</text>
      <text class="sort-item" :class="{ active: ordering === '-view_count' }" @tap="setOrdering('-view_count')">
        最热
      </text>
    </view>

    <!-- 问题流 -->
    <view v-for="q in questions" :key="q.id" class="oc-card q-card" @tap="goDetail(q.id)">
      <view class="q-title-row">
        <text class="oc-tag" :style="q.is_solved ? solvedStyle : unsolvedStyle">
          {{ q.is_solved ? '已解决' : '待解答' }}
        </text>
        <view class="q-title">{{ q.title }}</view>
      </view>
      <view class="q-excerpt">{{ (q.content || '').slice(0, 80) }}{{ (q.content || '').length > 80 ? '…' : '' }}</view>
      <view v-if="q.tags?.length" class="q-tags">
        <text v-for="tag in q.tags" :key="tag.id" class="q-tag">#{{ tag.name }}</text>
      </view>
      <view class="q-foot">
        <text>{{ q.author_info?.username || '邻里用户' }}</text>
        <text class="foot-right">👍 {{ q.like_count }} 💬 {{ q.answer_count }} 👁 {{ q.view_count }}</text>
      </view>
    </view>

    <view v-if="!loading && !questions.length" class="oc-empty">还没有提问，点右下角问第一个</view>
    <view v-if="loading" class="oc-loadmore">加载中…</view>
    <view v-else-if="loadError" class="oc-loadmore oc-loadmore--error" @tap="loadMore">加载失败，点击重试</view>
    <view v-else-if="finished && questions.length" class="oc-loadmore">没有更多了</view>

    <view class="oc-fab" @tap="goCreate">？</view>
  </view>
</template>

<script setup>
/**
 * 经验问答列表：按解决状态筛选 + 标签页内不再单列（详情页展示）。
 * 分页/刷新/竞态守卫统一由 usePagedList 收口。
 */
import { ref } from 'vue'
import { getQuestions } from '@/api/qa'
import { requireLogin } from '@/utils/auth'
import { usePagedList } from '@/composables/usePagedList'
import { ROUTE } from '@/router/paths'

const solveOptions = [
  { value: '', label: '全部' },
  { value: 'false', label: '待解答' },
  { value: 'true', label: '已解决' },
]

const filterSolved = ref('')
const keyword = ref('')
const ordering = ref('-created_at')

const solvedStyle = { background: '#e8f7ef', color: '#00b42a' }
const unsolvedStyle = { background: '#fff3ec', color: '#ff7d00' }

const {
  items: questions,
  loading,
  finished,
  loadError,
  loadFirst,
  loadMore,
} = usePagedList(async (pageNo) => {
  const params = { page: pageNo, page_size: 10, ordering: ordering.value }
  if (filterSolved.value !== '') params.is_solved = filterSolved.value
  if (keyword.value) params.search = keyword.value
  const res = await getQuestions(params)
  return res.data
})

function setFilter(v) {
  filterSolved.value = v
  loadFirst()
}
function setOrdering(v) {
  ordering.value = v
  loadFirst()
}
function search() {
  loadFirst()
}
function goDetail(id) {
  uni.navigateTo({ url: ROUTE.qaDetail(id) })
}
function goCreate() {
  if (!requireLogin()) return
  uni.navigateTo({ url: ROUTE.qaCreate() })
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
.q-title-row {
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
}
.q-title {
  flex: 1;
  font-size: 31rpx;
  font-weight: 700;
  line-height: 1.45;
}
.q-excerpt {
  color: var(--oc-text-secondary);
  font-size: 26rpx;
  margin-top: 12rpx;
  line-height: 1.5;
}
.q-tags {
  margin-top: 14rpx;
}
.q-tag {
  color: var(--oc-primary);
  font-size: 24rpx;
  margin-right: 16rpx;
}
.q-foot {
  display: flex;
  justify-content: space-between;
  margin-top: 18rpx;
  color: var(--oc-text-secondary);
  font-size: 24rpx;
}
</style>
