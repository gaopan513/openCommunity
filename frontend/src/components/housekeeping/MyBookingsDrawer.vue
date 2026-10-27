<script setup>
/**
 * 家政服务 - 我的预约抽屉
 *
 * 居民查看自己的预约并评价已完成服务；
 * 服务商（商家角色）查看收到的预约并推进订单状态。
 */
import { ref, reactive, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getBookings, updateBookingStatus, addBookingReview } from '@/api/housekeeping'
import { useUserStore } from '@/stores/user'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const userStore = useUserStore()

const visible = ref(props.modelValue)
watch(() => props.modelValue, (v) => {
  visible.value = v
  if (v) fetchBookings()
})
watch(visible, (v) => emit('update:modelValue', v))

const loading = ref(false)
const bookings = ref([])
const total = ref(0)

const query = reactive({ page: 1, page_size: 10, status: '' })

/** 状态映射：标签与样式 */
const statusMap = {
  pending: { label: '待确认', cls: 'bk--pending' },
  confirmed: { label: '已确认', cls: 'bk--confirmed' },
  in_service: { label: '服务中', cls: 'bk--service' },
  completed: { label: '已完成', cls: 'bk--completed' },
  reviewed: { label: '已评价', cls: 'bk--reviewed' },
  rejected: { label: '已拒绝', cls: 'bk--rejected' },
}

const statusFilters = [
  { label: '全部', value: '' },
  { label: '待确认', value: 'pending' },
  { label: '已确认', value: 'confirmed' },
  { label: '服务中', value: 'in_service' },
  { label: '已完成', value: 'completed' },
  { label: '已评价', value: 'reviewed' },
  { label: '已拒绝', value: 'rejected' },
]

async function fetchBookings() {
  loading.value = true
  try {
    const res = await getBookings(query)
    bookings.value = res.data.results
    total.value = res.data.total
  } catch (e) {
    // 错误已处理
  } finally {
    loading.value = false
  }
}

function handleFilterChange(value) {
  query.status = value
  query.page = 1
  fetchBookings()
}

function handlePageChange(page) {
  query.page = page
  fetchBookings()
}

/* ---------- 服务商推进订单状态 ---------- */

/** 服务商可执行的操作（按当前状态） */
function providerActions(booking) {
  const map = {
    pending: [
      { label: '确认接单', next: 'confirmed', type: 'primary' },
      { label: '拒绝', next: 'rejected', type: 'danger', plain: true },
    ],
    confirmed: [{ label: '开始服务', next: 'in_service', type: 'primary' }],
    in_service: [{ label: '完成服务', next: 'completed', type: 'success' }],
  }
  return map[booking.status] || []
}

async function handleStatusChange(booking, action) {
  if (action.next === 'rejected') {
    try {
      await ElMessageBox.confirm('确认拒绝该预约吗？', '操作确认', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
    } catch {
      return
    }
  }
  try {
    await updateBookingStatus(booking.id, action.next)
    ElMessage.success(`订单状态已更新为「${statusMap[action.next].label}」`)
    fetchBookings()
  } catch (e) {
    // 错误已处理
  }
}

/* ---------- 居民评价已完成服务 ---------- */
const reviewState = reactive({ bookingId: null, rating: 5, content: '' })
const reviewLoading = ref(false)

/** 当前登录用户是否为该订单的预约人 */
function isMyBooking(booking) {
  return userStore.userInfo && booking.user === userStore.userInfo.id
}

function openReview(booking) {
  reviewState.bookingId = booking.id
  reviewState.rating = 5
  reviewState.content = ''
}

async function submitReview(booking) {
  if (!reviewState.content.trim()) {
    ElMessage.warning('请输入评价内容')
    return
  }
  reviewLoading.value = true
  try {
    await addBookingReview(booking.id, {
      rating: reviewState.rating,
      content: reviewState.content,
    })
    ElMessage.success('评价提交成功，感谢你的反馈')
    reviewState.bookingId = null
    fetchBookings()
  } catch (e) {
    // 错误已处理
  } finally {
    reviewLoading.value = false
  }
}
</script>

<template>
  <el-drawer v-model="visible" title="预约订单" size="560px">
    <!-- 状态筛选 -->
    <div class="filter-bar">
      <button
        v-for="f in statusFilters"
        :key="f.value"
        class="filter-chip"
        :class="{ active: query.status === f.value }"
        @click="handleFilterChange(f.value)"
      >
        {{ f.label }}
      </button>
    </div>

    <div v-loading="loading" class="booking-list">
      <div v-for="b in bookings" :key="b.id" class="booking-card">
        <div class="booking-head">
          <div class="booking-title">
            <h4>{{ b.service_item_info?.title || '服务项目' }}</h4>
            <p>{{ b.provider_name }} · 预约于 {{ (b.created_at || '').slice(0, 10) }}</p>
          </div>
          <span class="booking-status" :class="statusMap[b.status]?.cls">
            {{ b.status_display || statusMap[b.status]?.label }}
          </span>
        </div>

        <div class="booking-rows">
          <p><el-icon><Calendar /></el-icon>{{ b.preferred_date }} {{ b.preferred_time }}</p>
          <p v-if="b.remark"><el-icon><ChatDotSquare /></el-icon>{{ b.remark }}</p>
        </div>

        <!-- 服务商操作 -->
        <div v-if="userStore.isMerchant && providerActions(b).length" class="booking-actions">
          <el-button
            v-for="act in providerActions(b)"
            :key="act.next"
            :type="act.type"
            :plain="act.plain"
            size="small"
            @click="handleStatusChange(b, act)"
          >
            {{ act.label }}
          </el-button>
        </div>

        <!-- 居民评价入口 -->
        <div v-if="isMyBooking(b) && b.status === 'completed' && reviewState.bookingId !== b.id" class="booking-actions">
          <el-button type="primary" size="small" @click="openReview(b)">评价服务</el-button>
        </div>

        <!-- 评价表单 -->
        <div v-if="reviewState.bookingId === b.id" class="review-inline">
          <div class="review-inline-head">
            <span>为这次服务打个分：</span>
            <el-rate v-model="reviewState.rating" />
          </div>
          <el-input
            v-model="reviewState.content"
            type="textarea"
            :rows="2"
            placeholder="服务态度、专业程度、是否推荐..."
            maxlength="500"
          />
          <div class="review-inline-foot">
            <el-button size="small" @click="reviewState.bookingId = null">取消</el-button>
            <el-button size="small" type="primary" :loading="reviewLoading" @click="submitReview(b)">提交评价</el-button>
          </div>
        </div>
      </div>

      <div v-if="!loading && bookings.length === 0" class="drawer-empty">
        <el-empty description="暂无预约订单" />
      </div>
    </div>

    <div v-if="total > query.page_size" class="drawer-pagination">
      <el-pagination
        small
        background
        layout="prev, pager, next"
        :total="total"
        :page-size="query.page_size"
        :current-page="query.page"
        @current-change="handlePageChange"
      />
    </div>
  </el-drawer>
</template>

<style scoped>
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.filter-chip {
  border: 1px solid var(--oc-line);
  background: #fff;
  padding: 5px 14px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  color: var(--oc-ink-soft);
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-chip:hover { border-color: var(--oc-accent); color: var(--oc-accent); }
.filter-chip.active {
  background: var(--oc-accent);
  border-color: var(--oc-accent);
  color: #fff;
}

.booking-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 160px;
}

.booking-card {
  border: 1px solid var(--oc-line);
  border-radius: 12px;
  padding: 16px;
  background: #fff;
  transition: box-shadow 0.2s ease;
}

.booking-card:hover { box-shadow: 0 4px 14px rgba(45, 58, 51, 0.07); }

.booking-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.booking-title h4 {
  margin: 0 0 4px;
  font-size: 15px;
  font-weight: 800;
  color: var(--oc-ink);
}

.booking-title p {
  margin: 0;
  font-size: 12px;
  color: var(--oc-ink-soft);
}

.booking-status {
  padding: 3px 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}

.bk--pending { background: #fdf3e0; color: #b07d1e; }
.bk--confirmed { background: var(--oc-accent-soft); color: var(--oc-accent); }
.bk--service { background: var(--oc-primary-soft); color: var(--oc-primary-deep); }
.bk--completed { background: #e8f4e8; color: #2e7d32; }
.bk--reviewed { background: #f1ede6; color: #8a8172; }
.bk--rejected { background: #fdeaea; color: #c0504d; }

.booking-rows {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.booking-rows p {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-size: 13px;
  color: var(--oc-ink-soft);
}

.booking-rows .el-icon { color: var(--oc-accent); }

.booking-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.review-inline {
  margin-top: 12px;
  background: var(--oc-paper);
  border: 1px solid var(--oc-line);
  border-radius: 10px;
  padding: 12px;
}

.review-inline-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--oc-ink);
}

.review-inline-foot { margin-top: 8px; text-align: right; }

.drawer-empty { padding: 30px 0; }

.drawer-pagination {
  display: flex;
  justify-content: center;
  margin-top: 18px;
}
</style>
