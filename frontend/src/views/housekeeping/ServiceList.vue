<script setup>
/**
 * 家政服务 - 服务列表页
 *
 * 功能：分类筛选（slug）、搜索、服务商卡片、我的预约入口、服务商入驻入口
 */
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getServiceCategories, getProviders } from '@/api/housekeeping'
import { useUserStore } from '@/stores/user'
import ProviderApplyDialog from '@/components/housekeeping/ProviderApplyDialog.vue'
import MyBookingsDrawer from '@/components/housekeeping/MyBookingsDrawer.vue'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const providers = ref([])
const categories = ref([])
const total = ref(0)
const applyVisible = ref(false)
const bookingsVisible = ref(false)

const query = reactive({
  page: 1,
  page_size: 12,
  category: '',   // 分类 slug
  search: '',
  status: '',
})

async function fetchCategories() {
  try {
    const res = await getServiceCategories()
    categories.value = res.data.results || res.data || []
  } catch (e) {
    // 错误已处理
  }
}

async function fetchProviders() {
  loading.value = true
  try {
    const res = await getProviders(query)
    providers.value = res.data.results
    total.value = res.data.total
  } catch (e) {
    // 错误已处理
  } finally {
    loading.value = false
  }
}

function handleCategoryChange(slug) {
  query.category = slug
  query.status = ''
  query.page = 1
  fetchProviders()
}

/** 管理员：切换查看待审核服务商 */
function togglePending() {
  query.status = query.status === 'pending' ? '' : 'pending'
  query.category = ''
  query.page = 1
  fetchProviders()
}

function handleSearch() {
  query.page = 1
  fetchProviders()
}

function handlePageChange(page) {
  query.page = page
  fetchProviders()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function goDetail(id) {
  router.push(`/housekeeping/${id}`)
}

/** 打开我的预约 */
function openBookings() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后再查看预约')
    router.push('/login')
    return
  }
  bookingsVisible.value = true
}

/** 打开服务商入驻申请：登录用户可申请（审核通过后授予商家角色） */
function openApply() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后再申请入驻')
    router.push('/login')
    return
  }
  applyVisible.value = true
}

function handleApplied() {
  applyVisible.value = false
  ElMessage.success('入驻申请已提交，请等待管理员审核')
}

onMounted(() => {
  fetchCategories()
  fetchProviders()
})
</script>

<template>
  <div class="oc-page service-page">
    <div class="oc-page-head head-row">
      <div>
        <span class="oc-kicker">Home Services</span>
        <h1>家政服务</h1>
        <p class="oc-sub">保洁维修搬家月嫂，靠谱的邻居师傅，随叫随到</p>
      </div>
      <div class="head-actions">
        <el-button size="large" round plain @click="openBookings">
          <el-icon style="margin-right: 6px"><Tickets /></el-icon>
          我的预约
        </el-button>
        <el-button type="primary" size="large" round @click="openApply">
          <el-icon style="margin-right: 6px"><Briefcase /></el-icon>
          服务商入驻
        </el-button>
      </div>
    </div>

    <!-- 分类导航 -->
    <div class="oc-card category-bar">
      <button
        class="cat-chip"
        :class="{ active: query.category === '' }"
        @click="handleCategoryChange('')"
      >
        全部
      </button>
      <button
        v-for="cat in categories"
        :key="cat.id"
        class="cat-chip"
        :class="{ active: query.category === cat.slug }"
        @click="handleCategoryChange(cat.slug)"
      >
        <span v-if="cat.icon" class="cat-icon">{{ cat.icon }}</span>
        {{ cat.name }}
      </button>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <el-input
        v-model="query.search"
        placeholder="搜索服务商或服务区域..."
        clearable
        style="width: 280px"
        @keyup.enter="handleSearch"
        @clear="handleSearch"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-button
        v-if="userStore.isAdmin"
        :type="query.status === 'pending' ? 'warning' : 'default'"
        size="small"
        round
        @click="togglePending"
      >
        <el-icon style="margin-right: 4px"><WarningFilled /></el-icon>
        {{ query.status === 'pending' ? '查看已通过' : '待审核' }}
      </el-button>
      <span class="total-tip">共 {{ total }} 家服务商</span>
    </div>

    <!-- 服务商网格 -->
    <div v-loading="loading" class="provider-grid">
      <div
        v-for="p in providers"
        :key="p.id"
        class="oc-card oc-card--hover provider-card"
        @click="goDetail(p.id)"
      >
        <div class="provider-top">
          <span class="provider-avatar">{{ p.name.charAt(0) }}</span>
          <div class="provider-head">
            <h3>{{ p.name }}</h3>
            <div class="provider-rating">
              <el-rate :model-value="Number(p.avg_rating)" disabled />
              <span>{{ p.avg_rating }} 分 · {{ p.review_count }} 单评价</span>
            </div>
          </div>
        </div>

        <div class="provider-tags">
          <span v-for="cat in p.categories" :key="cat.id" class="svc-tag">{{ cat.name }}</span>
          <span class="svc-count">{{ p.service_count }} 项服务</span>
        </div>

        <p v-if="p.service_area" class="provider-area">
          <el-icon><Location /></el-icon>{{ p.service_area }}
        </p>
        <p v-if="p.description" class="provider-desc">{{ p.description }}</p>

        <div class="provider-footer">
          <span class="enter-link">查看服务并预约 <el-icon><ArrowRight /></el-icon></span>
        </div>
      </div>

      <div v-if="!loading && providers.length === 0" class="grid-empty">
        <el-empty description="暂无服务商，快邀请靠谱的师傅入驻吧" />
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

    <ProviderApplyDialog v-model="applyVisible" @created="handleApplied" />
    <MyBookingsDrawer v-model="bookingsVisible" />
  </div>
</template>

<style scoped>
.head-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
}

.head-actions { display: flex; gap: 10px; }

.category-bar {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.cat-chip {
  border: 1px solid var(--oc-line);
  background: #fff;
  padding: 6px 18px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  color: var(--oc-ink-soft);
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.cat-chip:hover { border-color: var(--oc-accent); color: var(--oc-accent); }
.cat-chip.active {
  background: var(--oc-accent);
  border-color: var(--oc-accent);
  color: #fff;
  box-shadow: 0 3px 10px rgba(31, 111, 84, 0.3);
}

.cat-icon { font-size: 14px; }

.toolbar {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 20px;
}

.total-tip { font-size: 13px; color: var(--oc-ink-soft); }

.provider-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 18px;
  min-height: 200px;
}

.provider-card {
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px 22px 16px;
}

.provider-top { display: flex; gap: 14px; align-items: center; }

.provider-avatar {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--oc-accent), #2e8b6a);
  color: #fff;
  font-family: var(--oc-font-display);
  font-size: 26px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.provider-head h3 {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 800;
  color: var(--oc-ink);
}

.provider-card:hover .provider-head h3 { color: var(--oc-accent); }

.provider-rating {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--oc-ink-soft);
}

.provider-rating :deep(.el-rate__icon) { font-size: 13px; }

.provider-tags {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.svc-tag {
  background: var(--oc-accent-soft);
  color: var(--oc-accent);
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 999px;
}

.svc-count {
  font-size: 11px;
  color: var(--oc-ink-soft);
  margin-left: auto;
}

.provider-area {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-size: 13px;
  color: var(--oc-ink-soft);
}

.provider-area .el-icon { color: var(--oc-accent); }

.provider-desc {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--oc-ink-soft);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.provider-footer {
  margin-top: auto;
  padding-top: 10px;
  border-top: 1px dashed var(--oc-line);
}

.enter-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 700;
  color: var(--oc-accent);
  transition: gap 0.2s ease;
}

.provider-card:hover .enter-link { gap: 8px; }

.grid-empty { grid-column: 1 / -1; }

.pagination-wrap { display: flex; justify-content: center; margin-top: 28px; }

@media (max-width: 768px) {
  .head-row { flex-direction: column; align-items: stretch; }
  .head-actions { justify-content: flex-end; }
}
</style>
