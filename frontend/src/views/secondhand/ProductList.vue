<script setup>
/**
 * 二手市场 - 商品列表页
 *
 * 功能：分类筛选、价格排序、商品网格、发布入口
 */
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getProducts, getProductCategories } from '@/api/secondhand'
import { useUserStore } from '@/stores/user'
import ProductCreateDialog from '@/components/secondhand/ProductCreateDialog.vue'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const products = ref([])
const categories = ref([])
const total = ref(0)
const createVisible = ref(false)

const query = reactive({
  page: 1,
  page_size: 12,
  category: '',
  status: 'on_sale',
  search: '',
  ordering: '-created_at',
})

const statusMap = {
  on_sale: { label: '在售', cls: 'status--sale' },
  reserved: { label: '已预订', cls: 'status--reserved' },
  sold: { label: '已售出', cls: 'status--sold' },
  off_shelf: { label: '已下架', cls: 'status--off' },
}

const conditionMap = {
  brand_new: '全新',
  like_new: '九成新',
  good: '八成新',
  fair: '七成新及以下',
}

async function fetchCategories() {
  try {
    const res = await getProductCategories()
    categories.value = res.data.results || res.data || []
  } catch (e) {
    // 错误已处理
  }
}

async function fetchProducts() {
  loading.value = true
  try {
    const res = await getProducts(query)
    products.value = res.data.results
    total.value = res.data.total
  } catch (e) {
    // 错误已处理
  } finally {
    loading.value = false
  }
}

function handleCategoryChange(id) {
  query.category = id
  query.page = 1
  fetchProducts()
}

function handleSearch() {
  query.page = 1
  fetchProducts()
}

function handlePageChange(page) {
  query.page = page
  fetchProducts()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function goDetail(id) {
  router.push(`/secondhand/${id}`)
}

function handleCreated() {
  createVisible.value = false
  ElMessage.success('发布成功')
  query.page = 1
  fetchProducts()
}

function openCreate() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后再发布商品')
    router.push('/login')
    return
  }
  createVisible.value = true
}

onMounted(() => {
  fetchCategories()
  fetchProducts()
})
</script>

<template>
  <div class="oc-page market-page">
    <div class="oc-page-head head-row">
      <div>
        <span class="oc-kicker">Flea Market</span>
        <h1>二手市场</h1>
        <p class="oc-sub">闲置流转，邻里互惠，让好物找到新主人</p>
      </div>
      <el-button type="primary" size="large" round @click="openCreate">
        <el-icon style="margin-right: 6px"><Goods /></el-icon>
        发布闲置
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
        {{ cat.name }}
      </button>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <el-input
        v-model="query.search"
        placeholder="搜索宝贝..."
        clearable
        style="width: 240px"
        @keyup.enter="handleSearch"
        @clear="handleSearch"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-model="query.ordering" style="width: 140px" @change="handleSearch">
        <el-option label="最新发布" value="-created_at" />
        <el-option label="价格从低到高" value="price" />
        <el-option label="价格从高到低" value="-price" />
      </el-select>
    </div>

    <!-- 商品网格 -->
    <div v-loading="loading" class="product-grid">
      <div
        v-for="p in products"
        :key="p.id"
        class="oc-card oc-card--hover product-card"
        @click="goDetail(p.id)"
      >
        <div class="product-cover">
          <img v-if="p.first_image" :src="p.first_image" alt="商品图" />
          <div v-else class="cover-placeholder">
            <el-icon :size="40"><Picture /></el-icon>
          </div>
          <span class="status-badge" :class="statusMap[p.status]?.cls">
            {{ statusMap[p.status]?.label }}
          </span>
        </div>
        <div class="product-info">
          <h3 class="product-title">{{ p.title }}</h3>
          <div class="product-price-row">
            <span class="product-price">¥{{ p.price }}</span>
            <span class="product-condition">{{ conditionMap[p.condition] }}</span>
          </div>
          <div class="product-meta">
            <el-avatar :size="22" :src="p.seller_info?.avatar">
              {{ p.seller_info?.username?.charAt(0)?.toUpperCase() }}
            </el-avatar>
            <span class="seller-name">{{ p.seller_info?.username }}</span>
            <span class="view-count"><el-icon><View /></el-icon>{{ p.view_count }}</span>
          </div>
        </div>
      </div>

      <div v-if="!loading && products.length === 0" class="grid-empty">
        <el-empty description="暂无商品，快来发布第一件闲置" />
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

    <ProductCreateDialog v-model="createVisible" :categories="categories" @created="handleCreated" />
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
}

.cat-chip:hover { border-color: var(--oc-primary); color: var(--oc-primary-deep); }
.cat-chip.active {
  background: var(--oc-primary);
  border-color: var(--oc-primary);
  color: #fff;
  box-shadow: 0 3px 10px rgba(232, 98, 44, 0.3);
}

.toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 18px;
  min-height: 200px;
}

.product-card {
  overflow: hidden;
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.product-cover {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  background: var(--oc-paper);
  overflow: hidden;
}

.product-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.35s ease;
}

.product-card:hover .product-cover img {
  transform: scale(1.06);
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #d8cfc0;
}

.status-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  padding: 3px 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
}

.status--sale { background: var(--oc-accent); }
.status--reserved { background: var(--oc-gold); }
.status--sold { background: #999; }
.status--off { background: #bbb; }

.product-info {
  padding: 14px 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.product-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--oc-ink);
  margin: 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 42px;
}

.product-card:hover .product-title { color: var(--oc-primary-deep); }

.product-price-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.product-price {
  font-size: 20px;
  font-weight: 800;
  color: var(--oc-primary);
}

.product-condition {
  font-size: 12px;
  color: var(--oc-ink-soft);
  background: var(--oc-paper);
  padding: 2px 8px;
  border-radius: 6px;
}

.product-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: auto;
}

.seller-name {
  font-size: 12px;
  color: var(--oc-ink-soft);
  flex: 1;
}

.view-count {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  color: var(--oc-ink-soft);
}

.grid-empty {
  grid-column: 1 / -1;
}

.pagination-wrap { display: flex; justify-content: center; margin-top: 28px; }

@media (max-width: 768px) {
  .head-row { flex-direction: column; align-items: stretch; }
}
</style>
