<script setup>
/**
 * 自由发言 - 帖子列表页
 *
 * 功能：分类筛选、搜索、排序、发帖入口、帖子卡片流
 */
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getPosts } from '@/api/discussion'
import { useUserStore } from '@/stores/user'
import PostCreateDialog from '@/components/discussion/PostCreateDialog.vue'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const posts = ref([])
const total = ref(0)
const createVisible = ref(false)

const query = reactive({
  page: 1,
  page_size: 10,
  post_type: '',
  search: '',
  ordering: '-created_at',
})

const typeTabs = [
  { label: '全部', value: '' },
  { label: '闲聊', value: 'chat' },
  { label: '求助', value: 'help' },
  { label: '分享', value: 'share' },
  { label: '公告', value: 'notice' },
]

const typeMap = {
  chat: { label: '闲聊', cls: 'oc-tag--neutral' },
  help: { label: '求助', cls: 'oc-tag--top' },
  share: { label: '分享', cls: 'oc-tag--solved' },
  notice: { label: '公告', cls: 'oc-tag--featured' },
}

async function fetchPosts() {
  loading.value = true
  try {
    const res = await getPosts(query)
    posts.value = res.data.results
    total.value = res.data.total
  } catch (e) {
    // 错误已在拦截器处理
  } finally {
    loading.value = false
  }
}

function handleTabChange(val) {
  query.post_type = val
  query.page = 1
  fetchPosts()
}

function handleSearch() {
  query.page = 1
  fetchPosts()
}

function handlePageChange(page) {
  query.page = page
  fetchPosts()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function goDetail(id) {
  router.push(`/discussion/${id}`)
}

function handleCreated() {
  createVisible.value = false
  ElMessage.success('发布成功')
  query.page = 1
  fetchPosts()
}

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const min = Math.floor(diff / 60000)
  if (min < 1) return '刚刚'
  if (min < 60) return `${min} 分钟前`
  const hour = Math.floor(min / 60)
  if (hour < 24) return `${hour} 小时前`
  const day = Math.floor(hour / 24)
  if (day < 30) return `${day} 天前`
  return dateStr.slice(0, 10)
}

onMounted(fetchPosts)
</script>

<template>
  <div class="oc-page discussion-page">
    <!-- 页头 -->
    <div class="oc-page-head head-row">
      <div>
        <span class="oc-kicker">Neighborhood Talk</span>
        <h1>自由发言</h1>
        <p class="oc-sub">邻里之间，聊聊家常，说说心里话</p>
      </div>
      <el-button type="primary" size="large" round @click="createVisible = true">
        <el-icon style="margin-right: 6px"><EditPen /></el-icon>
        我要发帖
      </el-button>
    </div>

    <!-- 筛选栏 -->
    <div class="oc-card filter-bar">
      <div class="type-tabs">
        <button
          v-for="tab in typeTabs"
          :key="tab.value"
          class="type-tab"
          :class="{ active: query.post_type === tab.value }"
          @click="handleTabChange(tab.value)"
        >
          {{ tab.label }}
        </button>
      </div>
      <div class="filter-right">
        <el-input
          v-model="query.search"
          placeholder="搜索帖子..."
          clearable
          style="width: 220px"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="query.ordering" style="width: 130px" @change="handleSearch">
          <el-option label="最新发布" value="-created_at" />
          <el-option label="最热浏览" value="-view_count" />
          <el-option label="最多点赞" value="-like_count" />
        </el-select>
      </div>
    </div>

    <!-- 帖子流 -->
    <div v-loading="loading" class="post-stream">
      <div
        v-for="post in posts"
        :key="post.id"
        class="oc-card oc-card--hover post-card"
        @click="goDetail(post.id)"
      >
        <div class="post-avatar">
          <el-avatar :size="46" :src="post.author_info?.avatar">
            {{ post.author_info?.username?.charAt(0)?.toUpperCase() }}
          </el-avatar>
        </div>
        <div class="post-body">
          <div class="post-title-row">
            <span v-if="post.is_top" class="oc-tag oc-tag--top">置顶</span>
            <span v-if="post.is_featured" class="oc-tag oc-tag--featured">精华</span>
            <span class="oc-tag" :class="typeMap[post.post_type]?.cls">
              {{ typeMap[post.post_type]?.label }}
            </span>
            <h3 class="post-title">{{ post.title }}</h3>
          </div>
          <p class="post-excerpt">{{ post.content }}</p>
          <div class="post-meta">
            <span class="author-name">{{ post.author_info?.username }}</span>
            <span class="dot">·</span>
            <span>{{ timeAgo(post.created_at) }}</span>
            <span v-if="post.tags" class="post-tags">
              <span v-for="tag in post.tags.split(',').filter(Boolean)" :key="tag" class="hash-tag">
                #{{ tag }}
              </span>
            </span>
          </div>
        </div>
        <div class="post-stats">
          <div class="stat-item"><el-icon><View /></el-icon>{{ post.view_count }}</div>
          <div class="stat-item"><el-icon><ChatDotRound /></el-icon>{{ post.comment_count }}</div>
          <div class="stat-item" :class="{ liked: post.is_liked }">
            <el-icon><Star /></el-icon>{{ post.like_count }}
          </div>
        </div>
      </div>

      <div v-if="!loading && posts.length === 0" class="oc-empty">
        <el-empty description="还没有帖子，来发第一帖吧" />
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="total > query.page_size" class="pagination-wrap">
      <el-pagination
        background
        layout="prev, pager, next"
        :total="total"
        :page-size="query.page_size"
        :current-page="query.page"
        @current-change="handlePageChange"
      />
    </div>

    <PostCreateDialog v-model="createVisible" @created="handleCreated" />
  </div>
</template>

<style scoped>
.head-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  margin-bottom: 20px;
  gap: 16px;
  flex-wrap: wrap;
}

.type-tabs {
  display: flex;
  gap: 6px;
}

.type-tab {
  border: none;
  background: transparent;
  padding: 7px 16px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 600;
  color: var(--oc-ink-soft);
  cursor: pointer;
  transition: all 0.2s ease;
}

.type-tab:hover {
  background: var(--oc-primary-soft);
  color: var(--oc-primary-deep);
}

.type-tab.active {
  background: var(--oc-primary);
  color: #fff;
  box-shadow: 0 3px 10px rgba(232, 98, 44, 0.3);
}

.filter-right {
  display: flex;
  gap: 10px;
}

.post-stream {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 200px;
}

.post-card {
  display: flex;
  gap: 16px;
  padding: 20px;
  cursor: pointer;
}

.post-body {
  flex: 1;
  min-width: 0;
}

.post-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.post-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--oc-ink);
  margin: 0;
  line-height: 1.4;
}

.post-card:hover .post-title {
  color: var(--oc-primary-deep);
}

.post-excerpt {
  color: var(--oc-ink-soft);
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 10px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--oc-ink-soft);
  flex-wrap: wrap;
}

.author-name {
  font-weight: 600;
  color: var(--oc-accent);
}

.dot { opacity: 0.5; }

.hash-tag {
  color: var(--oc-primary);
  font-size: 12px;
  margin-left: 4px;
}

.post-stats {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 10px;
  padding-left: 16px;
  border-left: 1px solid var(--oc-line);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 5px;
  color: var(--oc-ink-soft);
  font-size: 13px;
  white-space: nowrap;
}

.stat-item.liked {
  color: var(--oc-gold);
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 28px;
}

@media (max-width: 768px) {
  .post-stats { display: none; }
  .head-row { flex-direction: column; align-items: stretch; }
}
</style>
