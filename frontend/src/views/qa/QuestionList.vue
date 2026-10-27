<script setup>
/**
 * 经验问答 - 问题列表页
 *
 * 功能：状态筛选、搜索、提问入口、问题卡片
 */
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getQuestions } from '@/api/qa'
import QuestionCreateDialog from '@/components/qa/QuestionCreateDialog.vue'
import { ElMessage } from 'element-plus'

const router = useRouter()

const loading = ref(false)
const questions = ref([])
const total = ref(0)
const createVisible = ref(false)

const query = reactive({
  page: 1,
  page_size: 10,
  is_solved: '',
  search: '',
  ordering: '-created_at',
})

const statusTabs = [
  { label: '全部', value: '' },
  { label: '待回答', value: 'false' },
  { label: '已解决', value: 'true' },
]

async function fetchQuestions() {
  loading.value = true
  try {
    const res = await getQuestions(query)
    questions.value = res.data.results
    total.value = res.data.total
  } catch (e) {
    // 错误已处理
  } finally {
    loading.value = false
  }
}

function handleTabChange(val) {
  query.is_solved = val
  query.page = 1
  fetchQuestions()
}

function handleSearch() {
  query.page = 1
  fetchQuestions()
}

function handlePageChange(page) {
  query.page = page
  fetchQuestions()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function goDetail(id) {
  router.push(`/qa/${id}`)
}

function handleCreated() {
  createVisible.value = false
  ElMessage.success('提问成功')
  query.page = 1
  fetchQuestions()
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

onMounted(fetchQuestions)
</script>

<template>
  <div class="oc-page qa-page">
    <div class="oc-page-head head-row">
      <div>
        <span class="oc-kicker">Ask &amp; Share</span>
        <h1>经验问答</h1>
        <p class="oc-sub">装修、育儿、养宠……邻里互助，经验共享</p>
      </div>
      <el-button type="primary" size="large" round @click="createVisible = true">
        <el-icon style="margin-right: 6px"><QuestionFilled /></el-icon>
        我要提问
      </el-button>
    </div>

    <div class="oc-card filter-bar">
      <div class="type-tabs">
        <button
          v-for="tab in statusTabs"
          :key="tab.value"
          class="type-tab"
          :class="{ active: query.is_solved === tab.value }"
          @click="handleTabChange(tab.value)"
        >
          {{ tab.label }}
        </button>
      </div>
      <div class="filter-right">
        <el-input
          v-model="query.search"
          placeholder="搜索问题..."
          clearable
          style="width: 220px"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="query.ordering" style="width: 130px" @change="handleSearch">
          <el-option label="最新提问" value="-created_at" />
          <el-option label="最多浏览" value="-view_count" />
          <el-option label="最多点赞" value="-like_count" />
        </el-select>
      </div>
    </div>

    <div v-loading="loading" class="question-stream">
      <div
        v-for="q in questions"
        :key="q.id"
        class="oc-card oc-card--hover question-card"
        @click="goDetail(q.id)"
      >
        <!-- 回答数徽标 -->
        <div class="answer-badge" :class="{ solved: q.is_solved }">
          <div class="answer-num">{{ q.answer_count }}</div>
          <div class="answer-label">{{ q.is_solved ? '已解决' : '回答' }}</div>
        </div>

        <div class="question-body">
          <div class="question-title-row">
            <h3 class="question-title">{{ q.title }}</h3>
            <span v-if="q.is_solved" class="oc-tag oc-tag--solved">已采纳</span>
          </div>
          <p class="question-excerpt">{{ q.content }}</p>
          <div class="question-meta">
            <span class="author-name">{{ q.author_info?.username }}</span>
            <span class="dot">·</span>
            <span>{{ timeAgo(q.created_at) }}</span>
            <span v-if="q.tags && q.tags.length" class="tag-list">
              <span v-for="tag in q.tags" :key="tag.id" class="tag-chip">{{ tag.name }}</span>
            </span>
          </div>
        </div>

        <div class="question-stats">
          <div class="stat-item"><el-icon><View /></el-icon>{{ q.view_count }}</div>
          <div class="stat-item"><el-icon><Star /></el-icon>{{ q.like_count }}</div>
        </div>
      </div>

      <div v-if="!loading && questions.length === 0" class="oc-empty">
        <el-empty description="还没有问题，来提第一个问题吧" />
      </div>
    </div>

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

    <QuestionCreateDialog v-model="createVisible" @created="handleCreated" />
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

.type-tabs { display: flex; gap: 6px; }

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

.type-tab:hover { background: var(--oc-accent-soft); color: var(--oc-accent); }
.type-tab.active {
  background: var(--oc-accent);
  color: #fff;
  box-shadow: 0 3px 10px rgba(31, 111, 84, 0.3);
}

.filter-right { display: flex; gap: 10px; }

.question-stream {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 200px;
}

.question-card {
  display: flex;
  gap: 18px;
  padding: 20px;
  cursor: pointer;
}

.answer-badge {
  flex-shrink: 0;
  width: 64px;
  text-align: center;
  padding: 10px 0;
  border-radius: 10px;
  background: var(--oc-paper);
  border: 1px solid var(--oc-line);
  align-self: flex-start;
}

.answer-badge.solved {
  background: var(--oc-accent-soft);
  border-color: #c4dccf;
}

.answer-num {
  font-size: 22px;
  font-weight: 800;
  color: var(--oc-ink);
  line-height: 1;
}

.answer-badge.solved .answer-num { color: var(--oc-accent); }

.answer-label {
  font-size: 11px;
  color: var(--oc-ink-soft);
  margin-top: 4px;
}

.answer-badge.solved .answer-label { color: var(--oc-accent); }

.question-body { flex: 1; min-width: 0; }

.question-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.question-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--oc-ink);
  margin: 0;
}

.question-card:hover .question-title { color: var(--oc-accent); }

.question-excerpt {
  color: var(--oc-ink-soft);
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 10px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.question-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--oc-ink-soft);
  flex-wrap: wrap;
}

.author-name { font-weight: 600; color: var(--oc-accent); }
.dot { opacity: 0.5; }

.tag-list { display: flex; gap: 6px; }

.tag-chip {
  background: var(--oc-accent-soft);
  color: var(--oc-accent);
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 999px;
  font-weight: 600;
}

.question-stats {
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

.pagination-wrap { display: flex; justify-content: center; margin-top: 28px; }

@media (max-width: 768px) {
  .question-stats { display: none; }
  .head-row { flex-direction: column; align-items: stretch; }
}
</style>
