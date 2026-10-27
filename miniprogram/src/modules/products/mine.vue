<template>
  <view class="oc-page">
    <view v-for="p in products" :key="p.id" class="oc-card my-card" @tap="goDetail(p.id)">
      <image class="cover" :src="mediaUrl(p.first_image)" mode="aspectFill" lazy-load />
      <view class="body">
        <view class="title">{{ p.title }}</view>
        <view class="row">
          <text class="price">¥{{ p.price }}</text>
          <text class="oc-tag" :style="{ color: statusColor(p.status), background: '#f7f8fa' }">
            {{ PRODUCT_STATUS_MAP[p.status]?.label }}
          </text>
        </view>
        <view class="time">{{ shortDate(p.created_at) }}发布</view>
      </view>
    </view>

    <view v-if="!loading && !products.length" class="oc-empty">你还没有发布过商品</view>
    <view v-if="loading" class="oc-loadmore">加载中…</view>
    <view v-else-if="loadError" class="oc-loadmore oc-loadmore--error" @tap="loadMore">加载失败，点击重试</view>

    <button class="oc-btn publish-btn" @tap="goPublish">发布新商品</button>
  </view>
</template>

<script setup>
/**
 * 我的商品：走后端 ?mine=1 过滤（仅返回当前登录用户发布的商品），
 * 单页请求 + 触底分页；发布/编辑商品后经 EVENTS.LIST_CHANGED 自动刷新。
 */
import { getMyProducts } from '@/api/secondhand'
import { onShow } from '@dcloudio/uni-app'
import { requireLogin } from '@/utils/auth'
import { mediaUrl, shortDate } from '@/utils/format'
import { PRODUCT_STATUS_MAP } from '@/constants/statusMaps'
import { usePagedList } from '@/composables/usePagedList'
import { ROUTE } from '@/router/paths'

const {
  items: products,
  loading,
  loadError,
  loadMore,
} = usePagedList(async (pageNo) => {
  const res = await getMyProducts({ page: pageNo, page_size: 20 })
  return res.data
})

function goDetail(id) {
  uni.navigateTo({ url: ROUTE.productDetail(id) })
}
function goPublish() {
  uni.navigateTo({ url: ROUTE.productCreateEdit() })
}
function statusColor(s) {
  return PRODUCT_STATUS_MAP[s]?.color || '#86909c'
}

onShow(() => {
  if (!requireLogin()) return
})
</script>

<style scoped>
.my-card {
  display: flex;
  gap: 20rpx;
  align-items: stretch;
}
.cover {
  width: 180rpx;
  height: 180rpx;
  border-radius: 12rpx;
  background: #f0f0f0;
  flex-shrink: 0;
}
.body {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.title {
  font-size: 29rpx;
  font-weight: 600;
  line-height: 1.4;
}
.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
}
.price {
  color: var(--oc-primary);
  font-size: 32rpx;
  font-weight: 700;
}
.time {
  color: var(--oc-text-secondary);
  font-size: 22rpx;
  margin-top: 8rpx;
}
.publish-btn {
  margin-top: 16rpx;
}
</style>
