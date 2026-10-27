<template>
  <view class="oc-page detail-page">
    <template v-if="merchant.id">
      <!-- 商家头部 -->
      <view class="oc-card head-card">
        <image v-if="merchant.logo" class="logo" :src="mediaUrl(merchant.logo)" mode="aspectFill" />
        <view class="head-info">
          <view class="name">{{ merchant.name }}</view>
          <view class="cat-row">
            <text class="oc-tag cat-tag">{{ merchant.category_name || '商家' }}</text>
            <text class="stars">{{ renderStars(merchant.avg_rating) }} {{ merchant.avg_rating || '暂无评分' }}</text>
          </view>
          <view class="stat-line">{{ merchant.review_count || 0 }} 条评价</view>
        </view>
      </view>

      <!-- 商家信息 -->
      <view class="oc-card">
        <view class="info-row" @tap="call(merchant.phone)">
          <text class="label">电话</text>
          <text class="value link">{{ merchant.phone || '未填写' }}</text>
        </view>
        <view class="info-row">
          <text class="label">地址</text>
          <text class="value">{{ merchant.address || '未填写' }}</text>
        </view>
        <view class="info-row">
          <text class="label">营业</text>
          <text class="value">{{ merchant.business_hours || '未填写' }}</text>
        </view>
        <view v-if="merchant.description" class="desc">{{ merchant.description }}</view>
        <!-- 商家相册 -->
        <scroll-view v-if="(merchant.images || []).length" class="album" scroll-x>
          <image
            v-for="img in merchant.images"
            :key="img.id"
            class="album-img"
            :src="mediaUrl(img.image)"
            mode="aspectFill"
          />
        </scroll-view>
      </view>

      <!-- 活动（只读浏览） -->
      <view class="oc-section-title">商家活动</view>
      <view v-for="act in activities" :key="act.id" class="oc-card act-card">
        <image v-if="act.image" class="act-img" :src="mediaUrl(act.image)" mode="aspectFill" />
        <view class="act-body">
          <view class="act-title">{{ act.title }}</view>
          <view v-if="act.discount_info" class="act-discount">{{ act.discount_info }}</view>
          <view class="act-time">{{ dateTime(act.start_time) }} ~ {{ dateTime(act.end_time) }}</view>
        </view>
      </view>
      <view v-if="!activities.length" class="oc-empty oc-empty--tight">暂无进行中的活动</view>

      <!-- 评价列表 + 发表评价 -->
      <view class="oc-section-title">用户评价</view>
      <view v-for="r in reviews" :key="r.id" class="oc-card review-card">
        <view class="rv-head">
          <image class="oc-avatar rv-avatar" :src="mediaUrl(r.user_info?.avatar)" mode="aspectFill" />
          <view class="rv-info">
            <view class="author">{{ r.user_info?.username || '邻里用户' }}</view>
            <view class="time">{{ dateTime(r.created_at) }}</view>
          </view>
          <text class="stars">{{ renderStars(r.rating) }}</text>
        </view>
        <view class="rv-content">{{ r.content }}</view>
        <view v-if="r.reply" class="reply-box"> <text class="reply-label">商家回复：</text>{{ r.reply }} </view>
      </view>
      <view v-if="!reviews.length" class="oc-empty oc-empty--tight">还没有评价，来写第一条</view>
    </template>

    <!-- 底部发表评价入口 -->
    <view class="review-bar oc-safe-bottom">
      <button class="oc-btn bar-btn" @tap="openReviewSheet">写评价</button>
    </view>

    <!-- 评价弹层 -->
    <ReviewSheet
      v-model:show="showReviewSheet"
      :title="`评价 ${merchant.name}`"
      placeholder="说说你的消费体验…"
      :submitting="submitting"
      @submit="submitReview"
    />
  </view>
</template>

<script setup>
/**
 * 商家详情（居民视角只读）：信息/相册/活动浏览 + 评价查看与发表。
 * 活动发布、店铺管理、评价回复为商家侧能力，留 Web 端操作。
 */
import { ref } from 'vue'
import { onLoad, onShow, onShareAppMessage, onShareTimeline } from '@dcloudio/uni-app'
import { getMerchant, getMerchantActivities, addMerchantReview } from '@/api/merchants'
import { requireLogin } from '@/utils/auth'
import { mediaUrl, dateTime, renderStars } from '@/utils/format'
import ReviewSheet from '@/components/ReviewSheet.vue'
import { track } from '@/utils/analytics'

const merchantId = ref(null)
const merchant = ref({})
const activities = ref([])
const reviews = ref([])
const showReviewSheet = ref(false)
const submitting = ref(false)

onLoad((options) => {
  merchantId.value = options.id
})

// 从评价页返回或提交后刷新最新数据
onShow(load)

async function load() {
  if (!merchantId.value) return
  try {
    const [detailRes, actRes] = await Promise.all([
      getMerchant(merchantId.value),
      // 活动列表分页返回；失败时回退详情内嵌的活动数组
      getMerchantActivities(merchantId.value, { page_size: 20 }).catch(() => null),
    ])
    merchant.value = detailRes.data
    reviews.value = detailRes.data.reviews || []
    activities.value = actRes?.data?.results || actRes?.data || detailRes.data.activities || []
  } catch {
    /* 提示由请求层处理 */
  }
}

function openReviewSheet() {
  if (!requireLogin()) return
  showReviewSheet.value = true
}

async function submitReview({ rating, content }) {
  if (submitting.value) return
  submitting.value = true
  try {
    await addMerchantReview(merchantId.value, { rating, content })
    showReviewSheet.value = false
    uni.showToast({ title: '评价成功', icon: 'success' })
    track('merchant_review', { rating })
    load()
  } catch {
    /* 提示由请求层处理 */
  } finally {
    submitting.value = false
  }
}

function call(phone) {
  if (!phone) return
  uni.makePhoneCall({ phoneNumber: phone }).catch(() => {})
}

onShareAppMessage(() => ({
  title: merchant.value.name || '周边好店推荐',
  path: '/modules/merchants/detail?id=' + merchantId.value,
}))

onShareTimeline(() => ({
  title: merchant.value.name || '周边好店推荐',
  query: 'id=' + merchantId.value,
}))
</script>

<style scoped>
.detail-page {
  padding-bottom: 180rpx;
}
.head-card {
  display: flex;
  gap: 24rpx;
  align-items: center;
}
.logo {
  width: 130rpx;
  height: 130rpx;
  border-radius: 18rpx;
  background: #f0f0f0;
  flex-shrink: 0;
}
.name {
  font-size: 36rpx;
  font-weight: 700;
}
.cat-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-top: 12rpx;
}
.cat-tag {
  background: var(--oc-primary-light);
  color: var(--oc-primary);
}
.stars {
  color: #ff9a2e;
  font-size: 23rpx;
}
.stat-line {
  color: var(--oc-text-secondary);
  font-size: 23rpx;
  margin-top: 8rpx;
}
.info-row {
  display: flex;
  gap: 20rpx;
  padding: 12rpx 0;
}
.label {
  width: 90rpx;
  color: var(--oc-text-secondary);
  flex-shrink: 0;
}
.value.link {
  color: var(--oc-primary);
}
.desc {
  font-size: 28rpx;
  line-height: 1.7;
  margin-top: 16rpx;
}
.album {
  white-space: nowrap;
  margin-top: 20rpx;
}
.album-img {
  display: inline-block;
  width: 220rpx;
  height: 160rpx;
  border-radius: 12rpx;
  margin-right: 14rpx;
  background: #f0f0f0;
}
.oc-empty--tight {
  padding: 40rpx 0;
}
.act-card {
  display: flex;
  gap: 20rpx;
}
.act-img {
  width: 150rpx;
  height: 150rpx;
  border-radius: 12rpx;
  background: #f0f0f0;
  flex-shrink: 0;
}
.act-title {
  font-size: 30rpx;
  font-weight: 700;
}
.act-discount {
  display: inline-block;
  color: var(--oc-danger);
  background: #ffece8;
  border-radius: 8rpx;
  padding: 4rpx 14rpx;
  font-size: 23rpx;
  margin-top: 10rpx;
}
.act-time {
  color: var(--oc-text-secondary);
  font-size: 23rpx;
  margin-top: 12rpx;
}
.rv-head {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.rv-avatar {
  width: 56rpx;
  height: 56rpx;
}
.rv-info {
  flex: 1;
}
.author {
  font-size: 26rpx;
  font-weight: 600;
}
.time {
  color: var(--oc-text-secondary);
  font-size: 21rpx;
  margin-top: 4rpx;
}
.rv-content {
  font-size: 28rpx;
  line-height: 1.6;
  margin-top: 14rpx;
}
.reply-box {
  background: #f7f8fa;
  border-radius: 10rpx;
  padding: 16rpx 20rpx;
  font-size: 25rpx;
  line-height: 1.6;
  margin-top: 14rpx;
}
.reply-label {
  color: var(--oc-primary);
  font-weight: 600;
}

.review-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  background: #fff;
  padding: 16rpx 24rpx;
  box-shadow: 0 -4rpx 16rpx rgba(0, 0, 0, 0.04);
  z-index: 100;
}
.bar-btn {
  width: 100%;
}
</style>
