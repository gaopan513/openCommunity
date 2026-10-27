<script setup>
/**
 * 周边商家 - 商家列表页
 *
 * 功能：分类筛选、名称搜索、评分排序、商家卡片、入驻申请入口
 */
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getMerchants, getMerchantCategories } from '@/api/merchants'
import { useUserStore } from '@/stores/user'
import MerchantApplyDialog from '@/components/merchant/MerchantApplyDialog.vue'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const merchants = ref([])
const categories = ref([])
const total = ref(0)
const applyVisible = ref(false)

const query = reactive({
  page: 1,
  page_size: 12,
  category: '',
  search: '',
  status: '',
})

async function fetchCategories() {
  try {
    const res = await getMerchantCategories()
    categories.value = res.data.results || res.data || []
  } catch (e) {
    // 错误已处理
  }
}

async function fetchMerchants() {
  loading.value = true
  try {
    const res = await getMerchants(query)
    merchants.value = res.data.results
    total.value = res.data.total
  } catch (e) {
    // 错误已处理
  } finally {
    loading.value = false
  }
}

function handleCategoryChange(id) {
  query.category = id
  query.status = ''
  query.page = 1
  fetchMerchants()
}

/** 管理员：切换查看待审核商家 */
function togglePending() {
  query.status = query.status === 'pending' ? '' : 'pending'
  query.category = ''
  query.page = 1
  fetchMerchants()
}

function handleSearch() {
  query.page = 1
  fetchMerchants()
}

function handlePageChange(page) {
  query.page = page
  fetchMerchants()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function goDetail(id) {
  router.push(`/merchants/${id}`)
}

/** 打开入驻申请：登录用户可申请（审核通过后授予商家角色） */
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
  fetchMerchants()
})
</script>

<template>
  <div class="oc-page merchant-page">
    <div class="oc-page-head head-row">
      <div>
        <span class="oc-kicker">Neighborhood Shops</span>
        <h1>周边商家</h1>
        <p class="oc-sub">小区周边吃穿住行，一站掌握，好店就在楼下</p>
      </div>
      <el-button type="primary" size="large" round @click="openApply">
        <el-icon style="margin-right: 6px"><Shop /></el-icon>
        商家入驻
      </el-button>
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
        :class="{ active: query.category === cat.id }"
        @click="handleCategoryChange(cat.id)"
      >
        <span v-if="cat.icon" class="cat-icon">{{ cat.icon }}</span>
        {{ cat.name }}
      </button>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <el-input
        v-model="query.search"
        placeholder="搜索商家名称..."
        clearable
        style="width: 260px"
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
      <span class="total-tip">共 {{ total }} 家店铺</span>
    </div>

    <!-- 商家网格 -->
    <div v-loading="loading" class="merchant-grid">
      <div
        v-for="m in merchants"
        :key="m.id"
        class="oc-card oc-card--hover merchant-card"
        @click="goDetail(m.id)"
      >
        <div class="shop-banner">
          <el-image
            v-if="m.logo"
            :src="m.logo"
            fit="cover"
            class="shop-logo"
          />
          <span v-else class="shop-initial">{{ m.name.charAt(0) }}</span>
          <span v-if="m.category_name" class="shop-cat">{{ m.category_name }}</span>
        </div>
        <div class="shop-body">
          <h3 class="shop-name">{{ m.name }}</h3>
          <div class="shop-rating">
            <el-rate :model-value="Number(m.avg_rating)" disabled show-score score-template="{value}" />
            <span class="review-count">{{ m.review_count }} 条评价</span>
          </div>
          <div class="shop-rows">
            <p class="shop-row">
              <el-icon><Clock /></el-icon>
              {{ m.business_hours || '营业时间待完善' }}
            </p>
            <p class="shop-row">
              <el-icon><Location /></el-icon>
              {{ m.address }}
            </p>
            <p class="shop-row">
              <el-icon><Phone /></el-icon>
              {{ m.phone }}
            </p>
          </div>
          <div class="shop-footer">
            <span class="enter-link">进店看看 <el-icon><ArrowRight /></el-icon></span>
          </div>
        </div>
      </div>

      <div v-if="!loading && merchants.length === 0" class="grid-empty">
        <el-empty description="暂无商家，快邀请楼下的好店入驻吧" />
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

    <MerchantApplyDialog v-model="applyVisible" :categories="categories" @created="handleApplied" />
  </div>
</template>

<style scoped>
.head-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
}

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

.cat-chip:hover { border-color: var(--oc-primary); color: var(--oc-primary-deep); }
.cat-chip.active {
  background: var(--oc-primary);
  border-color: var(--oc-primary);
  color: #fff;
  box-shadow: 0 3px 10px rgba(232, 98, 44, 0.3);
}

.cat-icon { font-size: 14px; }

.toolbar {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 20px;
}

.total-tip {
  font-size: 13px;
  color: var(--oc-ink-soft);
}

.merchant-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 18px;
  min-height: 200px;
}

.merchant-card {
  overflow: hidden;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  padding: 0;
}

.shop-banner {
  position: relative;
  height: 92px;
  background:
    radial-gradient(circle at 85% 20%, rgba(255, 255, 255, 0.35), transparent 45%),
    linear-gradient(120deg, var(--oc-primary) 0%, #f08c4f 60%, var(--oc-gold) 100%);
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.shop-initial {
  font-family: var(--oc-font-display);
  font-size: 44px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.92);
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.shop-logo {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  flex-shrink: 0;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.shop-cat {
  position: absolute;
  top: 12px;
  right: 14px;
  background: rgba(255, 255, 255, 0.88);
  color: var(--oc-primary-deep);
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 999px;
}

.shop-body {
  padding: 16px 18px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
}

.shop-name {
  margin: 0;
  font-size: 17px;
  font-weight: 800;
  color: var(--oc-ink);
}

.merchant-card:hover .shop-name { color: var(--oc-primary-deep); }

.shop-rating {
  display: flex;
  align-items: center;
  gap: 8px;
}

.shop-rating :deep(.el-rate__icon) { font-size: 15px; }

.review-count {
  font-size: 12px;
  color: var(--oc-ink-soft);
}

.shop-rows {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.shop-row {
  display: flex;
  align-items: center;
  gap: 7px;
  margin: 0;
  font-size: 13px;
  color: var(--oc-ink-soft);
  line-height: 1.5;
}

.shop-row .el-icon { color: var(--oc-accent); flex-shrink: 0; }

.shop-footer {
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
  color: var(--oc-primary);
  transition: gap 0.2s ease;
}

.merchant-card:hover .enter-link { gap: 8px; }

.grid-empty { grid-column: 1 / -1; }

.pagination-wrap { display: flex; justify-content: center; margin-top: 28px; }

@media (max-width: 768px) {
  .head-row { flex-direction: column; align-items: stretch; }
}
</style>
