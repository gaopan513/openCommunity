<template>
  <view class="oc-page detail-page">
    <template v-if="provider.id">
      <!-- 服务商头部 -->
      <view class="oc-card head-card">
        <view class="avatar-fallback">{{ provider.name?.[0] || '家' }}</view>
        <view class="head-info">
          <view class="name">{{ provider.name }}</view>
          <view class="stars">
            ⭐ {{ provider.avg_rating || '暂无评分' }} · {{ provider.review_count || 0 }} 条评价
          </view>
          <view class="area">📍 {{ provider.service_area || '服务区域未填写' }}</view>
        </view>
      </view>

      <!-- 简介 -->
      <view v-if="provider.description" class="oc-card">
        <view class="oc-section-title">服务商简介</view>
        <view class="desc">{{ provider.description }}</view>
      </view>

      <!-- 服务项目（点击发起预约） -->
      <view class="oc-section-title">服务项目</view>
      <view v-for="s in services" :key="s.id" class="oc-card service-card">
        <view class="s-body">
          <view class="s-title">{{ s.title }}</view>
          <view class="s-desc">{{ s.description }}</view>
          <view class="s-meta">
            <text class="price">{{ fmtPrice(s.price_min, s.price_max) }}</text>
            <text v-if="s.duration" class="duration">约 {{ s.duration }} 分钟</text>
          </view>
        </view>
        <button class="book-btn" size="mini" @tap="openBooking(s)">预约</button>
      </view>
      <view v-if="!services.length" class="oc-empty">该服务商暂未上架服务项目</view>

      <!-- 最近评价 -->
      <template v-if="(provider.recent_reviews || []).length">
        <view class="oc-section-title">最近评价</view>
        <view v-for="r in provider.recent_reviews" :key="r.id" class="oc-card review-card">
          <view class="rv-head">
            <text class="author">{{ r.user_info?.username || '邻里用户' }}</text>
            <text class="stars small">{{ renderStars(r.rating) }}</text>
          </view>
          <view class="rv-content">{{ r.content }}</view>
          <view class="time">{{ dateTime(r.created_at) }}</view>
        </view>
      </template>
    </template>

    <!-- 预约弹层 -->
    <view v-if="bookingItem" class="mask" @tap="closeBooking">
      <view class="sheet oc-safe-bottom" @tap.stop>
        <view class="sheet-title">预约：{{ bookingItem.title }}</view>

        <view class="form-row">
          <text class="label">日期</text>
          <picker mode="date" :start="today" :value="bookingForm.preferred_date" @change="onDateChange">
            <view class="picker-value">{{ bookingForm.preferred_date || '请选择日期' }}</view>
          </picker>
        </view>
        <view class="form-row">
          <text class="label">时间</text>
          <picker mode="time" :value="bookingForm.preferred_time" @change="onTimeChange">
            <view class="picker-value">{{ bookingForm.preferred_time || '请选择时间' }}</view>
          </picker>
        </view>
        <textarea
          v-model="bookingForm.remark"
          class="content-area"
          placeholder="补充说明，如门牌号、特殊需求…（选填）"
          maxlength="200"
        />
        <button class="oc-btn sheet-btn" :class="{ 'oc-btn--disabled': submitting }" @tap="submitBooking">
          {{ submitting ? '提交中…' : '确认预约' }}
        </button>
      </view>
    </view>
  </view>
</template>

<script setup>
/**
 * 服务商详情 + 预约创建。
 * 预约字段与后端 BookingCreateSerializer 一致：
 * { service_item, preferred_date(≥今天), preferred_time, remark }；
 * 服务商审核状态由后端校验，前端仅提交并展示错误提示。
 */
import { ref, computed } from 'vue'
import { onLoad, onShow, onShareAppMessage, onShareTimeline } from '@dcloudio/uni-app'
import { getProvider, createBooking } from '@/api/housekeeping'
import { requireLogin } from '@/utils/auth'
import { dateTime, renderStars } from '@/utils/format'
import { ROUTE } from '@/router/paths'
import { track } from '@/utils/analytics'

const providerId = ref(null)
const provider = ref({})
const bookingItem = ref(null)
const bookingForm = ref({ preferred_date: '', preferred_time: '', remark: '' })
const submitting = ref(false)

const services = computed(() => provider.value.services || [])
// 今天及以后可预约（后端同样校验）。注意 toISOString 取 UTC，
// 北京时间 0-8 点会得到"昨天"，需先折算本地时区
const today = (() => {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 10)
})()

onLoad((options) => {
  providerId.value = options.id
})
onShow(load)

async function load() {
  try {
    const res = await getProvider(providerId.value)
    provider.value = res.data
  } catch {
    /* 提示由请求层处理 */
  }
}

function openBooking(serviceItem) {
  if (!requireLogin()) return
  bookingItem.value = serviceItem
  bookingForm.value = { preferred_date: '', preferred_time: '', remark: '' }
}
function closeBooking() {
  bookingItem.value = null
}
function onDateChange(e) {
  bookingForm.value.preferred_date = e.detail.value
}
function onTimeChange(e) {
  bookingForm.value.preferred_time = e.detail.value
}

async function submitBooking() {
  if (submitting.value) return
  const f = bookingForm.value
  if (!f.preferred_date) return void uni.showToast({ title: '请选择预约日期', icon: 'none' })
  if (!f.preferred_time) return void uni.showToast({ title: '请选择预约时间', icon: 'none' })
  submitting.value = true
  try {
    await createBooking({
      service_item: bookingItem.value.id,
      preferred_date: f.preferred_date,
      preferred_time: f.preferred_time,
      remark: f.remark.trim(),
    })
    closeBooking()
    uni.showToast({ title: '预约成功，待服务商确认', icon: 'success' })
    track('booking_create', { service_item: bookingItem.value.id })
    // redirectTo 替换当前页，避免多次预约不断堆叠页面栈
    setTimeout(() => uni.redirectTo({ url: ROUTE.bookingsMy() }), 700)
  } catch {
    /* 错误提示由请求层统一弹出 */
  } finally {
    submitting.value = false
  }
}

function fmtPrice(min, max) {
  if (min && max && min !== max) return `¥${min} ~ ¥${max}`
  return min ? `¥${min} 起` : '价格面议'
}

onShareAppMessage(() => ({
  title: provider.value.name || '优质家政服务',
  path: '/modules/housekeeping/detail?id=' + providerId.value,
}))

onShareTimeline(() => ({
  title: provider.value.name || '优质家政服务',
  query: 'id=' + providerId.value,
}))
</script>

<style scoped>
.detail-page {
  padding-bottom: 60rpx;
}
.head-card {
  display: flex;
  gap: 24rpx;
  align-items: center;
}
.avatar-fallback {
  width: 120rpx;
  height: 120rpx;
  border-radius: 28rpx;
  background: var(--oc-primary-light);
  color: var(--oc-primary);
  font-size: 52rpx;
  font-weight: 700;
  text-align: center;
  line-height: 120rpx;
  flex-shrink: 0;
}
.name {
  font-size: 36rpx;
  font-weight: 700;
}
.stars {
  color: #ff9a2e;
  font-size: 24rpx;
  margin-top: 10rpx;
}
.stars.small {
  font-size: 22rpx;
}
.area {
  color: var(--oc-text-secondary);
  font-size: 24rpx;
  margin-top: 8rpx;
}
.desc {
  font-size: 28rpx;
  line-height: 1.7;
}
.service-card {
  display: flex;
  align-items: center;
  gap: 20rpx;
}
.s-body {
  flex: 1;
  min-width: 0;
}
.s-title {
  font-size: 30rpx;
  font-weight: 700;
}
.s-desc {
  color: var(--oc-text-secondary);
  font-size: 25rpx;
  margin-top: 8rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.s-meta {
  display: flex;
  align-items: center;
  gap: 18rpx;
  margin-top: 12rpx;
}
.price {
  color: var(--oc-primary);
  font-size: 30rpx;
  font-weight: 700;
}
.duration {
  color: var(--oc-text-secondary);
  font-size: 22rpx;
}
.book-btn {
  background: var(--oc-primary);
  color: #fff;
  flex-shrink: 0;
}
.rv-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.author {
  font-size: 26rpx;
  font-weight: 600;
}
.rv-content {
  font-size: 27rpx;
  line-height: 1.6;
  margin-top: 12rpx;
}
.time {
  color: var(--oc-text-secondary);
  font-size: 21rpx;
  margin-top: 8rpx;
}

.mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 200;
  display: flex;
  align-items: flex-end;
}
.sheet {
  width: 100%;
  background: #fff;
  border-radius: 32rpx 32rpx 0 0;
  padding: 40rpx 32rpx;
  box-sizing: border-box;
}
.sheet-title {
  font-size: 34rpx;
  font-weight: 700;
  text-align: center;
  margin-bottom: 26rpx;
}
.form-row {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-bottom: 20rpx;
}
.label {
  width: 90rpx;
  color: var(--oc-text-secondary);
}
.picker-value {
  background: #f7f8fa;
  border-radius: 12rpx;
  padding: 18rpx 24rpx;
  min-width: 300rpx;
}
.content-area {
  width: auto;
  min-height: 150rpx;
  background: #f7f8fa;
  border-radius: 12rpx;
  padding: 20rpx 24rpx;
  font-size: 28rpx;
}
.sheet-btn {
  margin-top: 28rpx;
}
</style>
