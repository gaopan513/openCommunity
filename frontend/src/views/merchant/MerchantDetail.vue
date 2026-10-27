<script setup>
/**
 * 周边商家 - 商家详情页
 *
 * 功能：店铺信息展示、活动列表与发布（商家）、评价与回复、管理员审核
 */
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getMerchant, getMerchantActivities, getMerchantReviews,
  createActivity, updateActivity, deleteActivity,
  addMerchantReview, replyMerchantReview, auditMerchant,
  getMerchantCategories,
} from '@/api/merchants'
import MerchantEditDialog from '@/components/merchant/MerchantEditDialog.vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const merchantId = route.params.id
const loading = ref(true)
const merchant = ref(null)
const activities = ref([])
const reviews = ref([])
const categories = ref([])
const editVisible = ref(false)

/** 当前用户是否为该店铺经营者 */
const isOwner = computed(() =>
  merchant.value && userStore.userInfo && merchant.value.user === userStore.userInfo.id
)

const statusMap = {
  pending: { label: '审核中', cls: 'status--pending' },
  approved: { label: '已认证', cls: 'status--approved' },
  rejected: { label: '未通过', cls: 'status--rejected' },
}

/** 相对时间格式化 */
function timeAgo(dateStr) {
  if (!dateStr) return ''
  const diff = Date.now() - new Date(dateStr).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} 小时前`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days} 天前`
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

/** 活动时间格式化 */
function fmtDateTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.toLocaleDateString('zh-CN')} ${d.toTimeString().slice(0, 5)}`
}

/** 活动状态：进行中 / 即将开始 / 已结束 */
function activityState(a) {
  const now = Date.now()
  if (now < new Date(a.start_time).getTime()) return { label: '即将开始', cls: 'act--soon' }
  if (now > new Date(a.end_time).getTime()) return { label: '已结束', cls: 'act--over' }
  return { label: '进行中', cls: 'act--live' }
}

async function fetchAll() {
  loading.value = true
  try {
    const [mRes, aRes, rRes] = await Promise.all([
      getMerchant(merchantId),
      getMerchantActivities(merchantId),
      getMerchantReviews(merchantId),
    ])
    merchant.value = mRes.data
    activities.value = aRes.data || []
    reviews.value = rRes.data || []
    // 编辑对话框需要分类列表（仅在商家本人进入时拉取）
    if (isOwner.value && !categories.value.length) {
      try {
        const cRes = await getMerchantCategories()
        categories.value = cRes.data || []
      } catch (e) {
        // 错误已处理
      }
    }
  } catch (e) {
    // 错误已处理
  } finally {
    loading.value = false
  }
}

/* ---------- 商家编辑店铺信息 ---------- */
function openEditDialog() {
  editVisible.value = true
}

async function onShopUpdated() {
  await fetchAll()
}

/* ---------- 管理员审核 ---------- */
async function handleAudit(status) {
  const action = status === 'approved' ? '通过' : '拒绝'
  try {
    await ElMessageBox.confirm(`确认${action}该商家的入驻申请？`, '审核确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await auditMerchant(merchantId, { status })
    ElMessage.success(`已${action}该商家的入驻申请`)
    fetchAll()
  } catch (e) {
    // 错误已处理
  }
}

/* ---------- 发布/编辑活动 ---------- */
const activityVisible = ref(false)
const activityLoading = ref(false)
const activityFormRef = ref(null)
const activityImage = ref(null)
const editingActivity = ref(null) /** 编辑模式：非空表示正在编辑指定活动 */
const activityForm = reactive({
  title: '',
  description: '',
  discount_info: '',
  start_time: '',
  end_time: '',
})

const activityRules = {
  title: [{ required: true, message: '请输入活动标题', trigger: 'blur' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
}

function openActivityDialog() {
  editingActivity.value = null
  resetActivityForm()
  activityVisible.value = true
}

function openEditActivity(activity) {
  editingActivity.value = activity
  activityForm.title = activity.title
  activityForm.description = activity.description || ''
  activityForm.discount_info = activity.discount_info || ''
  activityForm.start_time = activity.start_time
  activityForm.end_time = activity.end_time
  activityImage.value = activity.image ? { url: activity.image } : null
  activityVisible.value = true
}

async function submitActivity() {
  const valid = await activityFormRef.value.validate().catch(() => false)
  if (!valid) return

  if (new Date(activityForm.end_time) <= new Date(activityForm.start_time)) {
    ElMessage.warning('结束时间必须晚于开始时间')
    return
  }

  activityLoading.value = true
  try {
    const fd = new FormData()
    fd.append('title', activityForm.title)
    fd.append('description', activityForm.description)
    fd.append('discount_info', activityForm.discount_info)
    fd.append('start_time', activityForm.start_time)
    fd.append('end_time', activityForm.end_time)
    if (activityImage.value?.raw) {
      fd.append('image', activityImage.value.raw)
    }

    if (editingActivity.value) {
      await updateActivity(merchantId, editingActivity.value.id, fd)
      ElMessage.success('活动已更新')
    } else {
      await createActivity(merchantId, fd)
      ElMessage.success('活动发布成功')
    }

    activityVisible.value = false
    resetActivityForm()
    const res = await getMerchantActivities(merchantId)
    activities.value = res.data || []
  } catch (e) {
    // 错误已处理
  } finally {
    activityLoading.value = false
  }
}

async function handleDeleteActivity(activity) {
  try {
    await ElMessageBox.confirm(
      `确定要删除活动「${activity.title}」吗？删除后不可恢复。`,
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }
  try {
    await deleteActivity(merchantId, activity.id)
    ElMessage.success('活动已删除')
    const res = await getMerchantActivities(merchantId)
    activities.value = res.data || []
  } catch (e) {
    // 错误已处理
  }
}

function resetActivityForm() {
  activityForm.title = ''
  activityForm.description = ''
  activityForm.discount_info = ''
  activityForm.start_time = ''
  activityForm.end_time = ''
  activityImage.value = null
  editingActivity.value = null
  activityFormRef.value?.resetFields()
}

/* ---------- 评价 ---------- */
const reviewForm = reactive({ rating: 5, content: '' })
const reviewLoading = ref(false)

/** 当前用户是否已评价过 */
const hasReviewed = computed(() =>
  userStore.userInfo && reviews.value.some((r) => r.user === userStore.userInfo.id)
)

async function submitReview() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后再评价')
    router.push('/login')
    return
  }
  if (!reviewForm.content.trim()) {
    ElMessage.warning('请输入评价内容')
    return
  }
  reviewLoading.value = true
  try {
    await addMerchantReview(merchantId, {
      rating: reviewForm.rating,
      content: reviewForm.content,
    })
    ElMessage.success('评价成功，感谢你的反馈')
    reviewForm.rating = 5
    reviewForm.content = ''
    fetchAll()
  } catch (e) {
    // 错误已处理
  } finally {
    reviewLoading.value = false
  }
}

/* ---------- 商家回复评价 ---------- */
const replyState = reactive({ reviewId: null, content: '' })

function openReply(review) {
  replyState.reviewId = review.id
  replyState.content = review.reply || ''
}

async function submitReply(review) {
  if (!replyState.content.trim()) {
    ElMessage.warning('请输入回复内容')
    return
  }
  try {
    await replyMerchantReview(merchantId, review.id, { reply: replyState.content })
    ElMessage.success('回复成功')
    replyState.reviewId = null
    replyState.content = ''
    const res = await getMerchantReviews(merchantId)
    reviews.value = res.data || []
  } catch (e) {
    // 错误已处理
  }
}

onMounted(fetchAll)
</script>

<template>
  <div v-loading="loading" class="oc-page merchant-detail">
    <template v-if="merchant">
      <!-- 返回 -->
      <div class="back-bar" @click="router.push('/merchants')">
        <el-icon><ArrowLeft /></el-icon> 返回商家列表
      </div>

      <!-- 店招横幅 -->
      <div class="shop-hero">
        <div class="hero-pattern"></div>
        <div class="hero-main">
          <el-image
            v-if="merchant.logo"
            :src="merchant.logo"
            fit="cover"
            class="hero-logo"
          />
          <span v-else class="hero-initial">{{ merchant.name.charAt(0) }}</span>
          <div class="hero-info">
            <div class="hero-title-row">
              <h1>{{ merchant.name }}</h1>
              <span class="hero-status" :class="statusMap[merchant.status]?.cls">
                {{ statusMap[merchant.status]?.label }}
              </span>
              <el-button
                v-if="isOwner && merchant.status === 'approved'"
                type="primary"
                size="small"
                round
                class="hero-edit-btn"
                @click="openEditDialog"
              >
                <el-icon style="margin-right: 4px"><Edit /></el-icon>编辑信息
              </el-button>
            </div>
            <div class="hero-meta">
              <span v-if="merchant.category_name" class="hero-cat">{{ merchant.category_name }}</span>
              <el-rate :model-value="Number(merchant.avg_rating)" disabled />
              <span class="hero-score">{{ merchant.avg_rating }} 分 · {{ merchant.review_count }} 条评价</span>
            </div>
            <p class="hero-hours">
              <el-icon><Clock /></el-icon> {{ merchant.business_hours || '营业时间待完善' }}
            </p>
          </div>
        </div>
      </div>

      <!-- 管理员审核条 -->
      <div v-if="userStore.isAdmin && merchant.status === 'pending'" class="oc-card audit-bar">
        <el-icon class="audit-icon"><WarningFilled /></el-icon>
        <span>该商家正在等待入驻审核，请核实信息后处理。</span>
        <div class="audit-actions">
          <el-button type="success" size="small" @click="handleAudit('approved')">审核通过</el-button>
          <el-button type="danger" size="small" plain @click="handleAudit('rejected')">拒绝入驻</el-button>
        </div>
      </div>

      <!-- 经营者状态提示 -->
      <el-alert
        v-if="isOwner && merchant.status === 'pending'"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 18px"
        title="您的入驻申请正在审核中，审核通过后店铺将对外展示。"
      />
      <el-alert
        v-if="isOwner && merchant.status === 'rejected'"
        type="error"
        :closable="false"
        show-icon
        style="margin-bottom: 18px"
        title="很遗憾，您的入驻申请未通过，可联系管理员了解详情。"
      />

      <div class="detail-layout">
        <!-- 左侧主区 -->
        <div class="detail-main">
          <!-- 店铺介绍 -->
          <section class="oc-card block-card">
            <h2 class="block-title"><span class="title-mark"></span>店铺介绍</h2>
            <p class="desc-text">{{ merchant.description || '店主还没有填写介绍，去店里聊聊吧～' }}</p>
            <div v-if="merchant.images && merchant.images.length" class="shop-gallery">
              <el-image
                v-for="img in merchant.images"
                :key="img.id"
                :src="img.image"
                fit="cover"
                class="gallery-item"
                :preview-src-list="merchant.images.map((i) => i.image)"
              />
            </div>
          </section>

          <!-- 店铺活动 -->
          <section class="oc-card block-card">
            <div class="block-head-row">
              <h2 class="block-title"><span class="title-mark"></span>店铺活动</h2>
              <el-button v-if="isOwner" type="primary" size="small" round @click="openActivityDialog">
                <el-icon style="margin-right: 4px"><Plus /></el-icon>发布活动
              </el-button>
            </div>

            <div v-if="activities.length" class="activity-list">
              <div
                v-for="a in activities"
                :key="a.id"
                class="activity-card"
                :class="{ 'activity--over': !a.is_active }"
              >
                <div class="activity-side">
                  <span class="activity-state" :class="activityState(a).cls">
                    {{ activityState(a).label }}
                  </span>
                </div>
                <div class="activity-body">
                  <h3>{{ a.title }}</h3>
                  <p v-if="a.discount_info" class="activity-discount">
                    <el-icon><Present /></el-icon>{{ a.discount_info }}
                  </p>
                  <p v-if="a.description" class="activity-desc">{{ a.description }}</p>
                  <p class="activity-time">
                    <el-icon><Calendar /></el-icon>
                    {{ fmtDateTime(a.start_time) }} ~ {{ fmtDateTime(a.end_time) }}
                  </p>
                </div>
                <div class="activity-actions">
                  <el-image
                    v-if="a.image"
                    :src="a.image"
                    fit="cover"
                    class="activity-cover"
                    :preview-src-list="[a.image]"
                  />
                  <div v-if="isOwner" class="activity-opts">
                    <el-tooltip content="编辑" placement="top">
                      <el-button size="small" text circle @click="openEditActivity(a)">
                        <el-icon><Edit /></el-icon>
                      </el-button>
                    </el-tooltip>
                    <el-tooltip content="删除" placement="top">
                      <el-button size="small" text circle type="danger" @click="handleDeleteActivity(a)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </el-tooltip>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="oc-empty">
              <el-empty :image-size="70" description="暂无活动，过几天再来看看" />
            </div>
          </section>

          <!-- 顾客评价 -->
          <section class="oc-card block-card">
            <h2 class="block-title">
              <span class="title-mark"></span>顾客评价
              <span class="title-count">（{{ reviews.length }}）</span>
            </h2>

            <!-- 评价表单 -->
            <div v-if="!hasReviewed && !isOwner" class="review-form">
              <div class="review-form-head">
                <span>来过这家店？给大家说说你的体验：</span>
                <el-rate v-model="reviewForm.rating" :texts="['很差', '较差', '一般', '不错', '非常棒']" show-text />
              </div>
              <el-input
                v-model="reviewForm.content"
                type="textarea"
                :rows="3"
                placeholder="环境、服务、性价比..."
                maxlength="500"
                show-word-limit
              />
              <div class="review-form-foot">
                <el-button type="primary" :loading="reviewLoading" @click="submitReview">发表评价</el-button>
              </div>
            </div>
            <el-alert
              v-else-if="hasReviewed"
              type="success"
              :closable="false"
              style="margin-bottom: 16px"
              title="你已评价过这家店，感谢你的反馈！"
            />

            <!-- 评价列表 -->
            <div v-if="reviews.length" class="review-list">
              <div v-for="r in reviews" :key="r.id" class="review-item">
                <el-avatar :size="40" :src="r.user_info?.avatar">
                  {{ r.user_info?.username?.charAt(0)?.toUpperCase() }}
                </el-avatar>
                <div class="review-main">
                  <div class="review-head">
                    <span class="review-user">{{ r.user_info?.username }}</span>
                    <el-rate :model-value="r.rating" disabled />
                    <span class="review-time">{{ timeAgo(r.created_at) }}</span>
                  </div>
                  <p class="review-content">{{ r.content || '（仅评分未留言）' }}</p>

                  <!-- 商家已回复 -->
                  <div v-if="r.reply && replyState.reviewId !== r.id" class="reply-box">
                    <span class="reply-label">商家回复</span>
                    <p>{{ r.reply }}</p>
                    <span class="reply-time">{{ timeAgo(r.replied_at) }}</span>
                  </div>

                  <!-- 商家回复编辑 -->
                  <div v-if="isOwner && replyState.reviewId === r.id" class="reply-editor">
                    <el-input
                      v-model="replyState.content"
                      type="textarea"
                      :rows="2"
                      placeholder="感谢顾客的评价，说点什么吧..."
                      maxlength="500"
                    />
                    <div class="reply-editor-foot">
                      <el-button size="small" @click="replyState.reviewId = null">取消</el-button>
                      <el-button size="small" type="primary" @click="submitReply(r)">提交回复</el-button>
                    </div>
                  </div>
                  <div v-else-if="isOwner && !r.reply" class="reply-trigger">
                    <el-button size="small" text type="primary" @click="openReply(r)">回复评价</el-button>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="oc-empty">
              <el-empty :image-size="70" description="还没有评价，快来抢沙发" />
            </div>
          </section>
        </div>

        <!-- 右侧信息栏 -->
        <aside class="detail-side">
          <div class="oc-card info-card">
            <h3 class="side-title">店铺信息</h3>
            <ul class="info-list">
              <li>
                <el-icon><Location /></el-icon>
                <div><span class="info-label">地址</span>{{ merchant.address }}</div>
              </li>
              <li>
                <el-icon><Phone /></el-icon>
                <div><span class="info-label">电话</span>{{ merchant.phone }}</div>
              </li>
              <li>
                <el-icon><Clock /></el-icon>
                <div><span class="info-label">营业时间</span>{{ merchant.business_hours || '待完善' }}</div>
              </li>
              <li>
                <el-icon><Calendar /></el-icon>
                <div><span class="info-label">入驻时间</span>{{ timeAgo(merchant.created_at) }}</div>
              </li>
            </ul>
            <a class="tel-btn" :href="`tel:${merchant.phone}`">
              <el-icon><Phone /></el-icon> 联系店家
            </a>
            <el-button
              v-if="isOwner && merchant.status === 'approved'"
              type="warning"
              class="edit-shop-btn"
              @click="openEditDialog"
            >
              编辑店铺信息
            </el-button>
          </div>

          <div class="oc-card score-card">
            <div class="score-big">{{ merchant.avg_rating }}</div>
            <el-rate :model-value="Number(merchant.avg_rating)" disabled />
            <p class="score-tip">{{ merchant.review_count }} 位邻居的真实评价</p>
          </div>
        </aside>
      </div>

      <!-- 发布/编辑活动对话框 -->
      <el-dialog v-model="activityVisible" :title="editingActivity ? '编辑活动' : '发布店铺活动'" width="560px" :close-on-click-modal="false" :append-to-body="true">
        <el-form ref="activityFormRef" :model="activityForm" :rules="activityRules" label-position="top">
          <el-form-item label="活动标题" prop="title">
            <el-input v-model="activityForm.title" placeholder="如：周年庆全场 8 折" maxlength="200" />
          </el-form-item>
          <el-form-item label="优惠信息">
            <el-input v-model="activityForm.discount_info" placeholder="如：全场 8 折，满 100 减 20" maxlength="200" />
          </el-form-item>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="开始时间" prop="start_time">
                <el-date-picker
                  v-model="activityForm.start_time"
                  type="datetime"
                  value-format="YYYY-MM-DDTHH:mm:ss"
                  placeholder="选择开始时间"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="结束时间" prop="end_time">
                <el-date-picker
                  v-model="activityForm.end_time"
                  type="datetime"
                  value-format="YYYY-MM-DDTHH:mm:ss"
                  placeholder="选择结束时间"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="活动描述">
            <el-input
              v-model="activityForm.description"
              type="textarea"
              :rows="3"
              placeholder="活动规则、参与方式..."
              maxlength="1000"
              show-word-limit
            />
          </el-form-item>
          <el-form-item label="活动图片（选填）">
            <div v-if="editingActivity && activityImage && !activityImage.raw" class="activity-edit-preview">
              <el-image :src="activityImage.url" fit="cover" class="preview-img" />
              <p class="preview-hint">如需更换图片，请点击下方上传新文件</p>
            </div>
            <el-upload
              :auto-upload="false"
              :limit="1"
              accept="image/*"
              list-type="picture-card"
              :on-change="(file) => (activityImage = file)"
              :on-remove="() => (activityImage = editingActivity?.image ? { url: editingActivity.image } : null)"
            >
              <el-icon><Plus /></el-icon>
            </el-upload>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="activityVisible = false">取消</el-button>
          <el-button type="primary" :loading="activityLoading" @click="submitActivity">
            {{ editingActivity ? '保存' : '发布' }}
          </el-button>
        </template>
      </el-dialog>

      <!-- 编辑店铺信息对话框 -->
      <MerchantEditDialog
        v-model="editVisible"
        :categories="categories"
        @updated="onShopUpdated"
      />
    </template>
  </div>
</template>

<style scoped>
.back-bar {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  font-weight: 600;
  color: var(--oc-ink-soft);
  cursor: pointer;
  margin-bottom: 14px;
  transition: color 0.2s ease;
}

.back-bar:hover { color: var(--oc-primary); }

/* 店招横幅 */
.shop-hero {
  position: relative;
  border-radius: 14px;
  overflow: hidden;
  background: linear-gradient(115deg, #2d3a33 0%, #1f6f54 55%, #2e8b6a 100%);
  padding: 30px 34px;
  margin-bottom: 18px;
  color: #fff;
}

.hero-pattern {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 88% 30%, rgba(233, 161, 59, 0.28), transparent 42%),
    radial-gradient(circle at 12% 90%, rgba(232, 98, 44, 0.22), transparent 40%);
  pointer-events: none;
}

.hero-main {
  position: relative;
  display: flex;
  align-items: center;
  gap: 24px;
}

.hero-initial {
  width: 84px;
  height: 84px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.14);
  border: 2px solid rgba(255, 255, 255, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--oc-font-display);
  font-size: 44px;
  font-weight: 700;
  flex-shrink: 0;
}

.hero-logo {
  width: 84px;
  height: 84px;
  border-radius: 18px;
  flex-shrink: 0;
  overflow: hidden;
}

.hero-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.hero-title-row h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 800;
  font-family: var(--oc-font-display);
  letter-spacing: 1px;
}

.hero-edit-btn {
  background: rgba(255, 255, 255, 0.92);
  border-color: transparent;
  color: var(--oc-primary-deep);
  font-weight: 700;
}

.hero-edit-btn:hover {
  background: #fff;
  color: var(--oc-primary);
}

.hero-status {
  padding: 3px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.status--approved { background: rgba(255, 255, 255, 0.9); color: var(--oc-accent); }
.status--pending { background: rgba(233, 161, 59, 0.95); color: #fff; }
.status--rejected { background: rgba(220, 80, 60, 0.9); color: #fff; }

.hero-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.hero-meta :deep(.el-rate__icon) { font-size: 16px; }

.hero-cat {
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.4);
  padding: 2px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.hero-score { font-size: 13px; opacity: 0.9; }

.hero-hours {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 10px 0 0;
  font-size: 13px;
  opacity: 0.85;
}

/* 审核条 */
.audit-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  margin-bottom: 18px;
  border: 1px solid #f3d9a4;
  background: #fdf6e7;
  font-size: 13px;
  color: #8a6116;
}

.audit-icon { color: var(--oc-gold); font-size: 18px; }
.audit-actions { margin-left: auto; display: flex; gap: 8px; }

/* 布局 */
.detail-layout {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 20px;
  align-items: start;
}

.detail-main { display: flex; flex-direction: column; gap: 18px; }

.block-card { padding: 22px 24px; }

.block-title {
  margin: 0 0 16px;
  font-size: 18px;
  font-weight: 800;
  color: var(--oc-ink);
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-mark {
  width: 5px;
  height: 18px;
  border-radius: 3px;
  background: linear-gradient(180deg, var(--oc-primary), var(--oc-gold));
}

.title-count { font-size: 13px; font-weight: 600; color: var(--oc-ink-soft); }

.block-head-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.desc-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.9;
  color: var(--oc-ink);
  white-space: pre-wrap;
}

.shop-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
  margin-top: 16px;
}

.gallery-item {
  width: 100%;
  aspect-ratio: 4 / 3;
  border-radius: 10px;
  overflow: hidden;
}

/* 活动 */
.activity-list { display: flex; flex-direction: column; gap: 14px; }

.activity-card {
  display: flex;
  gap: 14px;
  border: 1px solid var(--oc-line);
  border-left: 4px solid var(--oc-primary);
  border-radius: 12px;
  padding: 16px;
  background: #fff;
  transition: box-shadow 0.25s ease, transform 0.25s ease;
}

.activity-card:hover {
  box-shadow: 0 6px 18px rgba(45, 58, 51, 0.08);
  transform: translateY(-2px);
}

.activity--over {
  border-left-color: #c9c2b6;
  opacity: 0.72;
}

.activity-side { display: flex; flex-direction: column; }

.activity-state {
  writing-mode: vertical-rl;
  letter-spacing: 4px;
  font-size: 12px;
  font-weight: 800;
  padding: 10px 6px;
  border-radius: 8px;
  height: fit-content;
}

.act--live { background: var(--oc-primary-soft); color: var(--oc-primary-deep); }
.act--soon { background: var(--oc-accent-soft); color: var(--oc-accent); }
.act--over { background: #f1ede6; color: #9a9184; }

.activity-body { flex: 1; min-width: 0; }

.activity-body h3 {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 800;
  color: var(--oc-ink);
}

.activity-discount {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin: 0 0 8px;
  background: var(--oc-primary-soft);
  color: var(--oc-primary-deep);
  font-size: 13px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 8px;
}

.activity-desc {
  margin: 0 0 8px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--oc-ink-soft);
}

.activity-time {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 0;
  font-size: 12px;
  color: var(--oc-ink-soft);
}

.activity-cover {
  width: 120px;
  height: 90px;
  border-radius: 10px;
  overflow: hidden;
  flex-shrink: 0;
}

.activity-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  flex-shrink: 0;
}

.activity-opts {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.activity-card:hover .activity-opts {
  opacity: 1;
}

.activity-edit-preview {
  margin-bottom: 10px;
}

.activity-edit-preview .preview-img {
  width: 120px;
  height: 90px;
  border-radius: 8px;
  overflow: hidden;
  display: block;
}

.activity-edit-preview .preview-hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--oc-ink-soft);
}

/* 评价 */
.review-form {
  background: var(--oc-paper);
  border: 1px solid var(--oc-line);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 18px;
}

.review-form-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--oc-ink);
  flex-wrap: wrap;
}

.review-form-foot { margin-top: 10px; text-align: right; }

.review-list { display: flex; flex-direction: column; }

.review-item {
  display: flex;
  gap: 14px;
  padding: 16px 0;
  border-bottom: 1px dashed var(--oc-line);
}

.review-item:last-child { border-bottom: none; }

.review-main { flex: 1; min-width: 0; }

.review-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.review-user { font-size: 14px; font-weight: 700; color: var(--oc-ink); }

.review-time { font-size: 12px; color: var(--oc-ink-soft); }

.review-content {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--oc-ink);
  white-space: pre-wrap;
}

.reply-box {
  margin-top: 10px;
  background: var(--oc-accent-soft);
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 13px;
  color: var(--oc-ink);
}

.reply-label {
  display: inline-block;
  font-size: 11px;
  font-weight: 800;
  color: var(--oc-accent);
  margin-bottom: 4px;
}

.reply-box p { margin: 0; line-height: 1.7; }

.reply-time { display: block; margin-top: 4px; font-size: 11px; color: var(--oc-ink-soft); }

.reply-editor { margin-top: 10px; }
.reply-editor-foot { margin-top: 8px; text-align: right; }
.reply-trigger { margin-top: 6px; }

/* 侧栏 */
.detail-side { display: flex; flex-direction: column; gap: 18px; position: sticky; top: 80px; }

.info-card, .score-card { padding: 20px 22px; }

.side-title {
  margin: 0 0 14px;
  font-size: 16px;
  font-weight: 800;
  color: var(--oc-ink);
}

.info-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.info-list li {
  display: flex;
  gap: 10px;
  font-size: 13px;
  color: var(--oc-ink);
  line-height: 1.6;
}

.info-list .el-icon { color: var(--oc-primary); margin-top: 2px; flex-shrink: 0; }

.info-label {
  display: block;
  font-size: 11px;
  color: var(--oc-ink-soft);
  margin-bottom: 1px;
}

.tel-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 18px;
  padding: 11px;
  border-radius: 999px;
  background: var(--oc-primary);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  text-decoration: none;
  transition: background 0.2s ease, transform 0.2s ease;
}

.tel-btn:hover { background: var(--oc-primary-deep); transform: translateY(-1px); }

.edit-shop-btn {
  display: flex;
  width: 100%;
  margin-top: 10px;
  justify-content: center;
  font-weight: 700;
}

.score-card {
  text-align: center;
  background: linear-gradient(160deg, #fff 40%, var(--oc-primary-soft));
}

.score-big {
  font-family: var(--oc-font-display);
  font-size: 46px;
  font-weight: 700;
  color: var(--oc-primary);
  line-height: 1.1;
}

.score-card :deep(.el-rate) { justify-content: center; margin-top: 6px; }

.score-tip { margin: 8px 0 0; font-size: 12px; color: var(--oc-ink-soft); }

@media (max-width: 900px) {
  .detail-layout { grid-template-columns: 1fr; }
  .detail-side { position: static; }
  .hero-main { flex-direction: column; align-items: flex-start; gap: 14px; }
}
</style>
