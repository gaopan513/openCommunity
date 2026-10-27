<template>
  <view class="oc-page">
    <!-- 状态筛选 -->
    <scroll-view class="chips" scroll-x>
      <view class="oc-chip" :class="{ 'oc-chip--active': !filterStatus }" @tap="setFilter('')">全部</view>
      <view
        v-for="(cfg, key) in BOOKING_STATUS_MAP"
        :key="key"
        class="oc-chip"
        :class="{ 'oc-chip--active': filterStatus === key }"
        @tap="setFilter(key)"
      >
        {{ cfg.label }}
      </view>
    </scroll-view>

    <!-- 预约列表（居民视角） -->
    <view v-for="b in bookings" :key="b.id" class="oc-card booking-card">
      <view class="head">
        <text class="service">{{ b.service_item_info?.title || '家政服务' }}</text>
        <text class="oc-tag status-tag" :style="{ color: statusColor(b.status), background: '#f7f8fa' }">
          {{ b.status_display || BOOKING_STATUS_MAP[b.status]?.label }}
        </text>
      </view>
      <view class="row">
        <text class="label">服务商</text><text>{{ b.provider_name || '-' }}</text>
      </view>
      <view class="row">
        <text class="label">预约时间</text><text>{{ b.preferred_date }} {{ b.preferred_time }}</text>
      </view>
      <view v-if="b.remark" class="row">
        <text class="label">备注</text><text class="remark">{{ b.remark }}</text>
      </view>
      <view class="time-line">下单于 {{ dateTime(b.created_at) }}</view>

      <!-- 居民侧操作：状态机允许时展示 -->
      <view v-if="actionsFor(b).length" class="actions">
        <button
          v-for="act in actionsFor(b)"
          :key="act.value"
          size="mini"
          class="action-btn"
          :class="[`action-btn--${act.type}`]"
          @tap="runAction(b, act)"
        >
          {{ act.label }}
        </button>
      </view>
    </view>

    <view v-if="!loading && !bookings.length" class="oc-empty">还没有预约记录</view>
    <view v-if="loading" class="oc-loadmore">加载中…</view>
    <view v-else-if="loadError" class="oc-loadmore oc-loadmore--error" @tap="loadMore">加载失败，点击重试</view>
    <view v-else-if="finished && bookings.length" class="oc-loadmore">没有更多了</view>

    <!-- 改期弹层（仅 pending 可修改） -->
    <view v-if="editingBooking" class="mask" @tap="cancelEdit">
      <view class="sheet oc-safe-bottom" @tap.stop>
        <view class="sheet-title">修改预约</view>
        <view class="form-row">
          <text class="label">日期</text>
          <picker
            mode="date"
            :start="today"
            :value="editForm.preferred_date"
            @change="(e) => (editForm.preferred_date = e.detail.value)"
          >
            <view class="picker-value">{{ editForm.preferred_date || '请选择' }}</view>
          </picker>
        </view>
        <view class="form-row">
          <text class="label">时间</text>
          <picker
            mode="time"
            :value="editForm.preferred_time"
            @change="(e) => (editForm.preferred_time = e.detail.value)"
          >
            <view class="picker-value">{{ editForm.preferred_time || '请选择' }}</view>
          </picker>
        </view>
        <textarea v-model="editForm.remark" class="content-area" placeholder="备注说明（选填）" maxlength="200" />
        <button class="oc-btn sheet-btn" @tap="saveEdit">保存修改</button>
      </view>
    </view>

    <!-- 评价弹层（completed → review） -->
    <ReviewSheet
      v-model:show="showReviewSheet"
      title="评价本次服务"
      placeholder="服务怎么样？说说你的体验…"
      :submitting="reviewSubmitting"
      @submit="saveReview"
    />
  </view>
</template>

<script setup>
/**
 * 我的预约（居民视角）：查看 + 取消（pending/confirmed）+ 改期（仅 pending）+ 完成后评价。
 * 服务商侧的确认/流转操作不在此页（留 Web 端商家身份操作）。
 */
import { ref } from 'vue'
import { requireLogin } from '@/utils/auth'
import { onLoad, onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app'
import { getBookings, updateBookingStatus, updateBooking, addBookingReview } from '@/api/housekeeping'
import { dateTime } from '@/utils/format'
import { BOOKING_STATUS_MAP } from '@/constants/statusMaps'
import ReviewSheet from '@/components/ReviewSheet.vue'
import { track } from '@/utils/analytics'
import { usePagedList } from '@/composables/usePagedList'

const filterStatus = ref('')

const {
  items: bookings,
  loading,
  finished,
  loadError,
  loadFirst,
  loadMore,
} = usePagedList(async (pageNo) => {
  const params = { page: pageNo, page_size: 20 }
  if (filterStatus.value) params.status = filterStatus.value
  const res = await getBookings(params)
  return res.data
})

const editingBooking = ref(null)
const editForm = ref({ preferred_date: '', preferred_time: '', remark: '' })
const showReviewSheet = ref(false)
// 评价提交中标记（防重复提交）
const reviewSubmitting = ref(false)
// 待评价的预约（评价提交时用）
let pendingReviewBooking = null

// 改期最早可选今天。toISOString 取 UTC，北京时间 0-8 点会得到"昨天"，需折算本地时区
const today = (() => {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 10)
})()

onLoad(() => { loadFirst() })

onPullDownRefresh(async () => {
  await loadFirst()
  uni.stopPullDownRefresh()
})

onReachBottom(() => {
  loadMore()
})

function setFilter(status) {
  filterStatus.value = status
  loadFirst()
}

/**
 * 依据业务不变量生成居民端可执行动作：
 * pending → 取消/改期；confirmed → 取消；completed → 评价
 */
function actionsFor(b) {
  const actions = []
  if (b.status === 'pending') {
    actions.push({ value: 'edit', label: '改期', type: 'plain' })
    actions.push({ value: 'cancelled', label: '取消预约', type: 'danger' })
  } else if (b.status === 'confirmed') {
    actions.push({ value: 'cancelled', label: '取消预约', type: 'danger' })
  } else if (b.status === 'completed') {
    actions.push({ value: 'review', label: '评价服务', type: 'primary' })
  }
  return actions
}

function runAction(booking, act) {
  if (act.value === 'cancelled') confirmCancel(booking)
  else if (act.value === 'edit') openEdit(booking)
  else if (act.value === 'review') openReview(booking)
}

function confirmCancel(b) {
  uni.showModal({
    title: '取消预约',
    content: `确定取消「${b.service_item_info?.title}」的预约吗？`,
    success: async (res) => {
      if (!res.confirm) return
      try {
        await updateBookingStatus(b.id, 'cancelled')
        uni.showToast({ title: '已取消', icon: 'none' })
        track('booking_cancel')
        loadFirst()
      } catch {
        /* 提示由请求层处理 */
      }
    },
  })
}

function openEdit(b) {
  editingBooking.value = b
  editForm.value = {
    preferred_date: b.preferred_date,
    preferred_time: b.preferred_time,
    remark: b.remark || '',
  }
}
function cancelEdit() {
  editingBooking.value = null
}
async function saveEdit() {
  const f = editForm.value
  if (!f.preferred_date || !f.preferred_time) {
    return void uni.showToast({ title: '请选择完整时间', icon: 'none' })
  }
  try {
    // 仅 pending 可通过 PUT 修改预约信息（后端兜底校验）
    await updateBooking(editingBooking.value.id, {
      preferred_date: f.preferred_date,
      preferred_time: f.preferred_time,
      remark: f.remark.trim(),
    })
    cancelEdit()
    uni.showToast({ title: '已更新', icon: 'success' })
    loadFirst()
  } catch {
    /* 提示由请求层处理 */
  }
}

function openReview(b) {
  pendingReviewBooking = b
  showReviewSheet.value = true
}
async function saveReview({ rating, content }) {
  if (reviewSubmitting.value) return
  reviewSubmitting.value = true
  try {
    await addBookingReview(pendingReviewBooking.id, { rating, content })
    showReviewSheet.value = false
    uni.showToast({ title: '感谢你的评价', icon: 'success' })
    track('booking_review', { rating })
    loadFirst()
  } catch {
    /* 提示由请求层处理 */
  } finally {
    reviewSubmitting.value = false
  }
}

function statusColor(s) {
  return BOOKING_STATUS_MAP[s]?.color || '#86909c'
}

onShow(() => {
  if (!requireLogin()) return
})
</script>

<style scoped>
.chips {
  white-space: nowrap;
  margin-bottom: 20rpx;
}
.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.service {
  font-size: 31rpx;
  font-weight: 700;
}
.row {
  display: flex;
  gap: 16rpx;
  font-size: 26rpx;
  margin-top: 12rpx;
}
.label {
  width: 120rpx;
  color: var(--oc-text-secondary);
  flex-shrink: 0;
}
.remark {
  flex: 1;
}
.time-line {
  color: var(--oc-text-secondary);
  font-size: 22rpx;
  margin-top: 14rpx;
}
.actions {
  display: flex;
  justify-content: flex-end;
  gap: 16rpx;
  margin-top: 20rpx;
  padding-top: 20rpx;
  border-top: 1rpx solid var(--oc-border);
}
.action-btn {
  background: #f7f8fa;
  color: var(--oc-text);
}
.action-btn--primary {
  background: var(--oc-primary);
  color: #fff;
}
.action-btn--danger {
  background: #ffece8;
  color: var(--oc-danger);
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
  margin-top: 24rpx;
}
</style>
