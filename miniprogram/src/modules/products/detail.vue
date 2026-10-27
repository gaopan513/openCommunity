<template>
  <view class="oc-page detail-page">
    <template v-if="product.id">
      <!-- 图片轮播 -->
      <swiper v-if="images.length" class="banner" indicator-dots circular>
        <swiper-item v-for="(img, i) in images" :key="i" @tap="preview(i)">
          <image class="banner-img" :src="img" mode="aspectFill" />
        </swiper-item>
      </swiper>

      <view class="oc-card">
        <view class="price-row">
          <text class="price">¥{{ product.price }}</text>
          <text class="oc-tag status-tag" :style="{ color: statusColor, background: '#f7f8fa' }">
            {{ PRODUCT_STATUS_MAP[product.status]?.label }}
          </text>
        </view>
        <view class="title">{{ product.title }}</view>
        <view class="meta">
          {{ PRODUCT_CONDITION_MAP[product.condition]?.label }} · 👁 {{ product.view_count }} 浏览
        </view>
        <view class="desc">{{ product.description }}</view>
        <view class="seller">发布于 {{ dateTime(product.created_at) }}</view>
      </view>

      <!-- 卖家操作：按状态机展示合法流转（后端 change_status 兜底校验） -->
      <view v-if="isMine && transitions.length" class="oc-card owner-card">
        <view class="oc-section-title">商品管理</view>
        <button
          v-for="t in transitions"
          :key="t.value"
          class="action-btn"
          :class="{ primary: t.primary }"
          size="mini"
          @tap="changeStatus(t)"
        >
          {{ t.label }}
        </button>
        <button class="action-btn danger" size="mini" @tap="handleDelete">删除商品</button>
      </view>

      <!-- 留言区 -->
      <view class="oc-card">
        <view class="oc-section-title">留言 {{ comments.length }}</view>
        <block v-if="comments.length">
          <view v-for="c in comments" :key="c.id" class="comment">
            <image class="oc-avatar c-avatar" :src="mediaUrl(c.author_info?.avatar)" mode="aspectFill" />
            <view class="c-body">
              <view class="c-head">
                <text class="author">{{ c.author_info?.username || '邻里用户' }}</text>
              </view>
              <view class="time">{{ dateTime(c.created_at) }}</view>
              <view class="c-content">{{ c.content }}</view>
            </view>
          </view>
        </block>
        <view v-else class="oc-empty">暂无留言，想了解就留言问问</view>
      </view>
    </template>

    <!-- 底部留言输入条 -->
    <CommentBar
      ref="commentBar"
      placeholder="向卖家留言咨询…"
      btn-text="留言"
      :submitting="submitting"
      @submit="submitComment"
    />
  </view>
</template>

<script setup>
/**
 * 商品详情：轮播 + 卖家状态机操作 + 留言。
 * 状态流转走专用 PUT /products/{id}/status/（serializer 层 status 只读）。
 */
import { ref, computed } from 'vue'
import { onLoad, onShareAppMessage, onShareTimeline } from '@dcloudio/uni-app'
import { getProduct, deleteProduct, changeProductStatus, addProductComment } from '@/api/secondhand'
import { useUserStore } from '@/stores/user'
import { requireLogin } from '@/utils/auth'
import { mediaUrl, dateTime } from '@/utils/format'
import { PRODUCT_STATUS_MAP, PRODUCT_CONDITION_MAP } from '@/constants/statusMaps'
import { EVENTS } from '@/constants'
import CommentBar from '@/components/CommentBar.vue'

const userStore = useUserStore()
const productId = ref(null)
const product = ref({})
const comments = ref([])
// 提交防抖：防止快速双击发出重复留言
const submitting = ref(false)
const commentBar = ref(null)

const isMine = computed(() => userStore.userInfo?.id === product.value.seller_info?.id)
const images = computed(() => (product.value.images || []).map((it) => mediaUrl(it.image)))

// 状态机驱动按钮文案与目标值：
// on_sale → 已预订/已下架；reserved → 恢复在售/已售出；off_shelf → 重新上架；sold 终态
const TRANSITIONS = {
  on_sale: [
    { value: 'reserved', label: '标记已预订', primary: true },
    { value: 'off_shelf', label: '下架' },
  ],
  reserved: [
    { value: 'sold', label: '标记已售出', primary: true },
    { value: 'on_sale', label: '恢复在售' },
  ],
  off_shelf: [{ value: 'on_sale', label: '重新上架', primary: true }],
}
const transitions = computed(() => (product.value.status && TRANSITIONS[product.value.status]) || [])
const statusColor = computed(() => PRODUCT_STATUS_MAP[product.value.status]?.color || '#86909c')

onLoad((options) => {
  productId.value = options.id
  load()
})

async function load() {
  try {
    const res = await getProduct(productId.value)
    product.value = res.data
    comments.value = res.data.comments || []
  } catch {
    /* 提示由请求层处理 */
  }
}

function preview(index) {
  uni.previewImage({ urls: images.value, current: index })
}

function changeStatus(t) {
  uni.showModal({
    title: '确认操作',
    content: `确定将商品标记为「${PRODUCT_STATUS_MAP[t.value]?.label}」吗？`,
    success: async (res) => {
      if (!res.confirm) return
      try {
        await changeProductStatus(productId.value, t.value)
        uni.$emit(EVENTS.LIST_CHANGED)
        uni.showToast({ title: '已更新', icon: 'success' })
        load()
      } catch {
        /* 提示由请求层处理 */
      }
    },
  })
}

function handleDelete() {
  uni.showModal({
    title: '删除商品',
    content: '删除后不可恢复，确定吗？',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await deleteProduct(productId.value)
        uni.$emit(EVENTS.LIST_CHANGED)
        uni.showToast({ title: '已删除', icon: 'none' })
        setTimeout(() => uni.navigateBack(), 500)
      } catch {
        /* 提示由请求层处理 */
      }
    },
  })
}

async function submitComment(content) {
  if (submitting.value) return
  if (!requireLogin()) return
  submitting.value = true
  try {
    await addProductComment(productId.value, { content })
    commentBar.value?.clear()
    uni.showToast({ title: '留言成功', icon: 'none' })
    load()
  } catch {
    /* 提示由请求层处理 */
  } finally {
    submitting.value = false
  }
}

onShareAppMessage(() => ({
  title: product.value.title || '二手闲置好物',
  path: '/modules/products/detail?id=' + productId.value,
}))

onShareTimeline(() => ({
  title: product.value.title || '二手闲置好物',
  query: 'id=' + productId.value,
}))
</script>

<style scoped>
.detail-page {
  padding-bottom: 200rpx;
}
.banner {
  height: 560rpx;
  border-radius: 16rpx;
  overflow: hidden;
  margin-bottom: 20rpx;
}
.banner-img {
  width: 100%;
  height: 100%;
}
.price-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.price {
  color: var(--oc-primary);
  font-size: 48rpx;
  font-weight: 700;
}
.status-tag {
  font-size: 24rpx;
}
.title {
  font-size: 36rpx;
  font-weight: 700;
  line-height: 1.4;
  margin-top: 14rpx;
}
.meta {
  color: var(--oc-text-secondary);
  font-size: 25rpx;
  margin-top: 12rpx;
}
.desc {
  font-size: 29rpx;
  line-height: 1.7;
  white-space: pre-wrap;
  margin-top: 18rpx;
}
.seller {
  color: var(--oc-text-secondary);
  font-size: 23rpx;
  margin-top: 22rpx;
  padding-top: 18rpx;
  border-top: 1rpx solid var(--oc-border);
}
.owner-card .action-btn {
  margin-right: 16rpx;
  margin-bottom: 12rpx;
  background: #f7f8fa;
  color: var(--oc-text);
}
.action-btn.primary {
  background: var(--oc-primary);
  color: #fff;
}
.action-btn.danger {
  color: var(--oc-danger);
}
.comment {
  display: flex;
  gap: 18rpx;
  padding: 22rpx 0;
  border-bottom: 1rpx solid var(--oc-border);
}
.comment:last-child {
  border-bottom: none;
  padding-bottom: 0;
}
.c-avatar {
  width: 56rpx;
  height: 56rpx;
}
.c-body {
  flex: 1;
}
.author {
  font-size: 25rpx;
  font-weight: 600;
}
.time {
  color: var(--oc-text-secondary);
  font-size: 21rpx;
  margin-top: 4rpx;
}
.c-content {
  font-size: 28rpx;
  line-height: 1.6;
  margin-top: 8rpx;
}
</style>
