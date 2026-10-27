<template>
  <view class="list-wrap">
    <!-- 搜索栏 -->
    <view class="search-bar">
      <input
        v-model="keyword"
        class="oc-input search-input"
        placeholder="搜索二手好物"
        confirm-type="search"
        @confirm="search"
      />
    </view>

    <!-- 分类筛选 -->
    <scroll-view class="chips" scroll-x>
      <view class="oc-chip" :class="{ 'oc-chip--active': !filterCategory }" @tap="setFilter('')">全部</view>
      <view
        v-for="cat in categories"
        :key="cat.id"
        class="oc-chip"
        :class="{ 'oc-chip--active': filterCategory === cat.id }"
        @tap="setFilter(cat.id)"
      >
        {{ cat.name }}
      </view>
    </scroll-view>

    <!-- 排序 -->
    <view class="sort-row">
      <text class="sort-item" :class="{ active: ordering === '-created_at' }" @tap="setOrdering('-created_at')">
        最新
      </text>
      <text class="divider">|</text>
      <text class="sort-item" :class="{ active: ordering === 'price' }" @tap="setOrdering('price')">价格↑</text>
      <text class="divider">|</text>
      <text class="sort-item" :class="{ active: ordering === '-price' }" @tap="setOrdering('-price')">价格↓</text>
    </view>

    <!-- 商品双列瀑布卡片 -->
    <view class="product-grid">
      <view v-for="p in products" :key="p.id" class="p-card" @tap="goDetail(p.id)">
        <image class="p-cover" :src="mediaUrl(p.first_image)" mode="aspectFill" lazy-load />
        <view class="p-body">
          <view class="p-title">{{ p.title }}</view>
          <view class="p-meta">
            <text class="price">¥{{ p.price }}</text>
            <text v-if="p.status !== 'on_sale'" class="oc-tag status-tag" :style="{ color: statusColor(p.status) }">
              {{ PRODUCT_STATUS_MAP[p.status]?.label }}
            </text>
          </view>
          <view class="p-foot">
            <text class="cond">{{ PRODUCT_CONDITION_MAP[p.condition]?.label }}</text>
            <text>👁 {{ p.view_count }}</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="!loading && !products.length" class="oc-empty">暂无闲置好物，点右下角出一件</view>
    <view v-if="loading" class="oc-loadmore">加载中…</view>
    <view v-else-if="loadError" class="oc-loadmore oc-loadmore--error" @tap="loadMore">加载失败，点击重试</view>
    <view v-else-if="finished && products.length" class="oc-loadmore">没有更多了</view>

    <view class="oc-fab" @tap="goCreate">＋</view>
  </view>
</template>

<script setup>
/**
 * 二手市场列表：分类筛选（id 对接 filterset_fields['category'] 的主键过滤）+ 搜索 + 价格排序。
 * 分页/刷新/竞态守卫统一由 usePagedList 收口。
 */
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getProducts, getProductCategories } from '@/api/secondhand'
import { mediaUrl } from '@/utils/format'
import { requireLogin } from '@/utils/auth'
import { PRODUCT_STATUS_MAP, PRODUCT_CONDITION_MAP } from '@/constants/statusMaps'
import { usePagedList } from '@/composables/usePagedList'
import { ROUTE } from '@/router/paths'

const categories = ref([])
const filterCategory = ref('')
const keyword = ref('')
const ordering = ref('-created_at')

const {
  items: products,
  loading,
  finished,
  loadError,
  loadFirst,
  loadMore,
} = usePagedList(async (pageNo) => {
  const params = { page: pageNo, page_size: 10, ordering: ordering.value }
  if (filterCategory.value) params.category = filterCategory.value
  if (keyword.value) params.search = keyword.value
  const res = await getProducts(params)
  return res.data
})

onLoad(async () => {
  try {
    const res = await getProductCategories()
    categories.value = res.data?.results || res.data || []
  } catch {
    /* 分类加载失败不阻塞列表 */
  }
})

function setFilter(id) {
  filterCategory.value = id
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
  uni.navigateTo({ url: ROUTE.productDetail(id) })
}
function goCreate() {
  if (!requireLogin()) return
  uni.navigateTo({ url: ROUTE.productCreateEdit() })
}
function statusColor(s) {
  return PRODUCT_STATUS_MAP[s]?.color || '#86909c'
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
.product-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
}
.p-card {
  width: calc((100% - 20rpx) / 2);
  background: #fff;
  border-radius: 16rpx;
  overflow: hidden;
}
.p-cover {
  width: 100%;
  height: 330rpx;
  background: #f0f0f0;
}
.p-body {
  padding: 18rpx 20rpx 22rpx;
}
.p-title {
  font-size: 28rpx;
  font-weight: 600;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.p-meta {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 14rpx;
}
.price {
  color: var(--oc-primary);
  font-size: 32rpx;
  font-weight: 700;
}
.status-tag {
  font-size: 22rpx;
}
.p-foot {
  display: flex;
  justify-content: space-between;
  color: var(--oc-text-secondary);
  font-size: 22rpx;
  margin-top: 12rpx;
}
</style>
