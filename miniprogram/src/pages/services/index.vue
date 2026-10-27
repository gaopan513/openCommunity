<template>
  <view class="oc-page">
    <!-- 家政 / 商家 双分段 -->
    <view class="segment">
      <view class="seg-item" :class="{ active: tab === 'housekeeping' }" @tap="switchTab('housekeeping')">
        家政服务
      </view>
      <view class="seg-item" :class="{ active: tab === 'merchants' }" @tap="switchTab('merchants')">周边商家</view>
    </view>

    <!-- ===== 家政：分类宫格 + 服务商列表 ===== -->
    <block v-if="tab === 'housekeeping'">
      <scroll-view class="chips" scroll-x>
        <view class="oc-chip" :class="{ 'oc-chip--active': !hkCategory }" @tap="setHkCategory('')">全部</view>
        <view
          v-for="cat in hkCategories"
          :key="cat.id"
          class="oc-chip"
          :class="{ 'oc-chip--active': hkCategory === cat.slug }"
          @tap="setHkCategory(cat.slug)"
        >
          {{ cat.name }}
        </view>
      </scroll-view>

      <view v-for="p in providers" :key="p.id" class="oc-card provider-card" @tap="goProvider(p.id)">
        <view class="cover cover--empty">{{ p.name?.[0] || '家' }}</view>
        <view class="body">
          <view class="name-row">
            <text class="name">{{ p.name }}</text>
            <text class="stars">{{ renderStars(p.avg_rating) }}</text>
          </view>
          <view class="area">📍 {{ p.service_area || '服务区域未填写' }}</view>
          <view class="desc">{{ p.description?.slice(0, 40) }}{{ (p.description || '').length > 40 ? '…' : '' }}</view>
          <view class="stats">
            ⭐ {{ p.avg_rating || '暂无' }} · {{ p.service_count ?? p.services?.length ?? 0 }} 个服务项目
          </view>
        </view>
      </view>

      <view v-if="!hkLoading && !providers.length" class="oc-empty">该分类下暂无服务商</view>
      <view v-if="hkLoading" class="oc-loadmore">加载中…</view>
      <view v-else-if="providers.length && hkFinished" class="oc-loadmore">没有更多了</view>
    </block>

    <!-- ===== 商家：分类筛选 + 列表 ===== -->
    <block v-else>
      <scroll-view class="chips" scroll-x>
        <view class="oc-chip" :class="{ 'oc-chip--active': !mCategory }" @tap="setMCategory('')">全部</view>
        <view
          v-for="cat in mCategories"
          :key="cat.id"
          class="oc-chip"
          :class="{ 'oc-chip--active': mCategory === cat.id }"
          @tap="setMCategory(cat.id)"
        >
          {{ cat.name }}
        </view>
      </scroll-view>

      <view v-for="m in merchants" :key="m.id" class="oc-card provider-card" @tap="goMerchant(m.id)">
        <image v-if="m.logo" class="cover" :src="mediaUrl(m.logo)" mode="aspectFill" lazy-load />
        <view v-else class="cover cover--empty">{{ m.name?.[0] || '商' }}</view>
        <view class="body">
          <view class="name-row">
            <text class="name">{{ m.name }}</text>
            <text class="oc-tag cat-tag">{{ m.category_name || '商家' }}</text>
          </view>
          <view class="area">🕘 {{ m.business_hours || '营业时间未填写' }}</view>
          <view class="desc">📍 {{ m.address }}</view>
          <view class="stats">⭐ {{ m.avg_rating || '暂无' }} · {{ m.review_count }} 条评价</view>
        </view>
      </view>

      <view v-if="!mLoading && !merchants.length" class="oc-empty">该分类下暂无商家</view>
      <view v-if="mLoading" class="oc-loadmore">加载中…</view>
      <view v-else-if="merchants.length && mFinished" class="oc-loadmore">没有更多了</view>
    </block>
  </view>
</template>

<script setup>
/**
 * 服务圈（Tab 页）：家政服务 / 周边商家 双分段。
 * 家政按分类 slug 筛选（后端 services__category__slug），商家按分类 id 筛选（后端 category_id）；
 * 触底分页加载；服务商进入预约流程，商家进入详情浏览评价。
 *
 * 家政/商家两侧各自持有 usePagedList 实例，用 active 控制：仅激活 tab 响应触底加载、
 * 响应全局 LIST_CHANGED 刷新；切回未加载的 tab 自动加载。消除了手工分页/竞态守卫重复。
 */
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getServiceCategories, getProviders } from '@/api/housekeeping'
import { getMerchants, getMerchantCategories } from '@/api/merchants'
import { mediaUrl, renderStars } from '@/utils/format'
import { usePagedList } from '@/composables/usePagedList'
import { ROUTE } from '@/router/paths'

const PAGE_SIZE = 20

const tab = ref('housekeeping')

// —— 家政侧状态
const hkCategories = ref([])
const hkCategory = ref('')
// 家政是否处于激活 tab
const hkActive = ref(true)
const {
  items: providers,
  loading: hkLoading,
  finished: hkFinished,
  loadFirst: hkLoadFirst,
  loadMore: hkLoadMore,
} = usePagedList(
  async (pageNo) => {
    const params = { page: pageNo, page_size: PAGE_SIZE }
    if (hkCategory.value) params.category = hkCategory.value
    const res = await getProviders(params)
    return Array.isArray(res.data)
      ? { results: res.data, total: res.data.length }
      : { results: res.data?.results || [], total: res.data?.total ?? (res.data?.results || []).length }
  },
  { active: hkActive }
)

// —— 商家侧状态
const mCategories = ref([])
const mCategory = ref('')
// 商家是否处于激活 tab
const mActive = ref(false)
const {
  items: merchants,
  loading: mLoading,
  finished: mFinished,
  loadFirst: mLoadFirst,
  loadMore: mLoadMore,
} = usePagedList(
  async (pageNo) => {
    const params = { page: pageNo, page_size: PAGE_SIZE }
    if (mCategory.value) params.category = mCategory.value
    const res = await getMerchants(params)
    return Array.isArray(res.data)
      ? { results: res.data, total: res.data.length }
      : { results: res.data?.results || [], total: res.data?.total ?? (res.data?.results || []).length }
  },
  { active: mActive }
)

onLoad(async () => {
  // 默认激活家政 tab：首次进入由 onShow 触发加载，此处仅加载分类（非阻塞）
  try {
    const res = await getServiceCategories()
    hkCategories.value = res.data?.results || res.data || []
  } catch {
    /* 非阻塞 */
  }
  try {
    const res = await getMerchantCategories()
    mCategories.value = res.data?.results || res.data || []
  } catch {
    /* 非阻塞 */
  }
})

function switchTab(name) {
  tab.value = name
  if (name === 'housekeeping') {
    hkActive.value = true
    mActive.value = false
    // 家政首次激活（冷 tab 默认即 true 场景）由 onShow/watch 兜底
  } else {
    mActive.value = true
    hkActive.value = false
  }
}

function setHkCategory(slug) {
  hkCategory.value = slug
  hkLoadFirst()
}

function setMCategory(id) {
  mCategory.value = id
  mLoadFirst()
}

function goProvider(id) {
  uni.navigateTo({ url: ROUTE.housekeepingDetail(id) })
}
function goMerchant(id) {
  uni.navigateTo({ url: ROUTE.merchantDetail(id) })
}
</script>

<style scoped>
.segment {
  display: flex;
  background: #fff;
  border-radius: 44rpx;
  padding: 6rpx;
  margin-bottom: 24rpx;
}
.seg-item {
  flex: 1;
  text-align: center;
  line-height: 72rpx;
  border-radius: 38rpx;
  color: var(--oc-text-secondary);
  font-size: 28rpx;
}
.seg-item.active {
  background: var(--oc-primary);
  color: #fff;
  font-weight: 700;
}
.chips {
  white-space: nowrap;
  margin-bottom: 20rpx;
}
.provider-card {
  display: flex;
  gap: 20rpx;
}
.cover {
  width: 170rpx;
  height: 170rpx;
  border-radius: 14rpx;
  flex-shrink: 0;
  background: #f0f0f0;
}
.cover--empty {
  line-height: 170rpx;
  text-align: center;
  font-size: 56rpx;
  font-weight: 700;
  color: #fff;
  background: var(--oc-primary-light);
  color: var(--oc-primary);
}
.body {
  flex: 1;
  min-width: 0;
}
.name-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
}
.name {
  font-size: 31rpx;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cat-tag {
  background: var(--oc-primary-light);
  color: var(--oc-primary);
  flex-shrink: 0;
}
.stars {
  color: #ff9a2e;
  font-size: 22rpx;
}
.area,
.desc {
  color: var(--oc-text-secondary);
  font-size: 24rpx;
  margin-top: 10rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.stats {
  color: var(--oc-text-secondary);
  font-size: 23rpx;
  margin-top: 12rpx;
}
</style>
