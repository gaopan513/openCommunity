<script setup>
/**
 * 家政服务 - 服务商详情页
 *
 * 功能：服务商信息、服务项目列表与预约下单、服务评价、管理员审核
 */
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getProvider, auditProvider } from '@/api/housekeeping'
import { useUserStore } from '@/stores/user'
import BookingDialog from '@/components/housekeeping/BookingDialog.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const providerId = route.params.id
const loading = ref(true)
const provider = ref(null)

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

async function fetchProvider() {
  loading.value = true
  try {
    const res = await getProvider(providerId)
    provider.value = res.data
  } catch (e) {
    // 错误已处理
  } finally {
    loading.value = false
  }
}

/* ---------- 管理员审核 ---------- */
async function handleAudit(action) {
  const label = action === 'approve' ? '通过' : '拒绝'
  try {
    await ElMessageBox.confirm(`确认${label}该服务商的入驻申请？`, '审核确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await auditProvider(providerId, { action })
    ElMessage.success(`已${label}该服务商的入驻申请`)
    fetchProvider()
  } catch (e) {
    // 错误已处理
  }
}

/* ---------- 预约下单 ---------- */
const bookingVisible = ref(false)
const currentService = ref(null)

/** 打开预约对话框：仅居民角色可预约 */
function openBooking(service) {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后再预约服务')
    router.push('/login')
    return
  }
  if (userStore.userInfo.role !== 'resident') {
    ElMessage.warning('仅居民用户可以预约家政服务')
    return
  }
  currentService.value = service
  bookingVisible.value = true
}

function handleBooked() {
  bookingVisible.value = false
  ElMessage.success('预约提交成功，请等待服务方确认')
}

onMounted(fetchProvider)
</script>

<template>
  <div v-loading="loading" class="oc-page service-detail">
    <template v-if="provider">
      <!-- 返回 -->
      <div class="back-bar" @click="router.push('/housekeeping')">
        <el-icon><ArrowLeft /></el-icon> 返回服务列表
      </div>

      <!-- 服务商横幅 -->
      <div class="provider-hero">
        <div class="hero-pattern"></div>
        <div class="hero-main">
          <span class="hero-avatar">{{ provider.name ? provider.name.charAt(0) : '店' }}</span>
          <div class="hero-info">
            <div class="hero-title-row">
              <h1>{{ provider.name }}</h1>
              <span class="hero-status" :class="statusMap[provider.status]?.cls">
                {{ statusMap[provider.status]?.label }}
              </span>
            </div>
            <div class="hero-meta">
              <el-rate :model-value="Number(provider.avg_rating)" disabled />
              <span class="hero-score">{{ provider.avg_rating }} 分 · {{ provider.review_count }} 单评价</span>
            </div>
            <p v-if="provider.service_area" class="hero-area">
              <el-icon><Location /></el-icon> 服务区域：{{ provider.service_area }}
            </p>
          </div>
          <a class="hero-tel" :href="`tel:${provider.phone}`">
            <el-icon><Phone /></el-icon>
            <span>{{ provider.phone }}</span>
          </a>
        </div>
      </div>

      <!-- 管理员审核条 -->
      <div v-if="userStore.isAdmin && provider.status === 'pending'" class="oc-card audit-bar">
        <el-icon class="audit-icon"><WarningFilled /></el-icon>
        <span>该服务商正在等待入驻审核，请核实资质后处理。</span>
        <div class="audit-actions">
          <el-button type="success" size="small" @click="handleAudit('approve')">审核通过</el-button>
          <el-button type="danger" size="small" plain @click="handleAudit('reject')">拒绝入驻</el-button>
        </div>
      </div>

      <div class="detail-layout">
        <!-- 左侧主区 -->
        <div class="detail-main">
          <!-- 服务介绍 -->
          <section class="oc-card block-card">
            <h2 class="block-title"><span class="title-mark"></span>服务介绍</h2>
            <p class="desc-text">{{ provider.description || '师傅还没有填写详细介绍，电话咨询一下吧～' }}</p>
            <el-image
              v-if="provider.qualification_image"
              :src="provider.qualification_image"
              fit="cover"
              class="qual-image"
              :preview-src-list="[provider.qualification_image]"
            />
          </section>

          <!-- 服务项目 -->
          <section class="oc-card block-card">
            <h2 class="block-title">
              <span class="title-mark"></span>服务项目
              <span class="title-count">（{{ provider.services?.length || 0 }}）</span>
            </h2>

            <div v-if="provider.services?.length" class="service-list">
              <div v-for="s in provider.services" :key="s.id" class="service-card">
                <div class="service-body">
                  <div class="service-title-row">
                    <h3>{{ s.title }}</h3>
                    <span class="service-cat">{{ s.category_name }}</span>
                  </div>
                  <p v-if="s.description" class="service-desc">{{ s.description }}</p>
                  <div class="service-meta">
                    <span class="service-price">
                      ¥{{ s.price_min }}
                      <template v-if="Number(s.price_max) > Number(s.price_min)"> - {{ s.price_max }}</template>
                    </span>
                    <span v-if="s.duration" class="service-duration">
                      <el-icon><Clock /></el-icon>{{ s.duration }}
                    </span>
                  </div>
                </div>
                <el-button
                  type="primary"
                  round
                  :disabled="provider.status !== 'approved'"
                  @click="openBooking(s)"
                >
                  立即预约
                </el-button>
              </div>
            </div>
            <div v-else class="oc-empty">
              <el-empty :image-size="70" description="暂未发布服务项目" />
            </div>
          </section>

          <!-- 服务评价 -->
          <section class="oc-card block-card">
            <h2 class="block-title">
              <span class="title-mark"></span>邻居评价
              <span class="title-count">（{{ provider.review_count }}）</span>
            </h2>

            <div v-if="provider.recent_reviews?.length" class="review-list">
              <div v-for="r in provider.recent_reviews" :key="r.id" class="review-item">
                <el-avatar :size="38" :src="r.user_info?.avatar">
                  {{ r.user_info?.username?.charAt(0)?.toUpperCase() }}
                </el-avatar>
                <div class="review-main">
                  <div class="review-head">
                    <span class="review-user">{{ r.user_info?.username }}</span>
                    <el-rate :model-value="r.rating" disabled />
                    <span class="review-time">{{ timeAgo(r.created_at) }}</span>
                  </div>
                  <p class="review-content">{{ r.content || '（仅评分未留言）' }}</p>
                </div>
              </div>
            </div>
            <div v-else class="oc-empty">
              <el-empty :image-size="70" description="还没有评价，服务完成后欢迎来反馈" />
            </div>
          </section>
        </div>

        <!-- 右侧信息栏 -->
        <aside class="detail-side">
          <div class="oc-card info-card">
            <h3 class="side-title">联系师傅</h3>
            <ul class="info-list">
              <li>
                <el-icon><Phone /></el-icon>
                <div><span class="info-label">联系电话</span>{{ provider.phone }}</div>
              </li>
              <li>
                <el-icon><Location /></el-icon>
                <div><span class="info-label">服务区域</span>{{ provider.service_area || '详询师傅' }}</div>
              </li>
              <li>
                <el-icon><Calendar /></el-icon>
                <div><span class="info-label">入驻时间</span>{{ timeAgo(provider.created_at) }}</div>
              </li>
            </ul>
            <a class="tel-btn" :href="`tel:${provider.phone}`">
              <el-icon><Phone /></el-icon> 电话咨询
            </a>
          </div>

          <div class="oc-card score-card">
            <div class="score-big">{{ provider.avg_rating }}</div>
            <el-rate :model-value="Number(provider.avg_rating)" disabled />
            <p class="score-tip">{{ provider.review_count }} 位邻居的真实评价</p>
          </div>

          <div class="oc-card tip-card">
            <h3 class="side-title">预约小贴士</h3>
            <p>提交预约后，师傅会尽快确认订单；服务完成并确认无误后，记得回来评价哦。</p>
          </div>
        </aside>
      </div>

      <!-- 预约对话框 -->
      <BookingDialog v-model="bookingVisible" :service-item="currentService" @created="handleBooked" />
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

.back-bar:hover { color: var(--oc-accent); }

/* 横幅 */
.provider-hero {
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
    radial-gradient(circle at 88% 30%, rgba(233, 161, 59, 0.26), transparent 42%),
    radial-gradient(circle at 10% 92%, rgba(255, 255, 255, 0.1), transparent 40%);
  pointer-events: none;
}

.hero-main {
  position: relative;
  display: flex;
  align-items: center;
  gap: 24px;
}

.hero-avatar {
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

.hero-info { flex: 1; min-width: 0; }

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
}

.hero-meta :deep(.el-rate__icon) { font-size: 16px; }

.hero-score { font-size: 13px; opacity: 0.9; }

.hero-area {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 10px 0 0;
  font-size: 13px;
  opacity: 0.85;
}

.hero-tel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 20px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.35);
  color: #fff;
  text-decoration: none;
  font-size: 14px;
  font-weight: 700;
  transition: background 0.2s ease;
  flex-shrink: 0;
}

.hero-tel:hover { background: rgba(255, 255, 255, 0.24); }

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
  background: linear-gradient(180deg, var(--oc-accent), #4aa382);
}

.title-count { font-size: 13px; font-weight: 600; color: var(--oc-ink-soft); }

.desc-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.9;
  color: var(--oc-ink);
  white-space: pre-wrap;
}

.qual-image {
  display: block;
  width: 220px;
  aspect-ratio: 4 / 3;
  border-radius: 10px;
  overflow: hidden;
  margin-top: 14px;
}

/* 服务项目 */
.service-list { display: flex; flex-direction: column; gap: 14px; }

.service-card {
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid var(--oc-line);
  border-radius: 12px;
  padding: 18px;
  background: #fff;
  transition: box-shadow 0.25s ease, transform 0.25s ease;
}

.service-card:hover {
  box-shadow: 0 6px 18px rgba(45, 58, 51, 0.08);
  transform: translateY(-2px);
}

.service-body { flex: 1; min-width: 0; }

.service-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.service-title-row h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  color: var(--oc-ink);
}

.service-cat {
  background: var(--oc-accent-soft);
  color: var(--oc-accent);
  font-size: 11px;
  font-weight: 700;
  padding: 2px 10px;
  border-radius: 999px;
}

.service-desc {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.7;
  color: var(--oc-ink-soft);
}

.service-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 10px;
}

.service-price {
  font-size: 18px;
  font-weight: 800;
  color: var(--oc-primary);
}

.service-duration {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--oc-ink-soft);
}

/* 评价 */
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

/* 侧栏 */
.detail-side { display: flex; flex-direction: column; gap: 18px; position: sticky; top: 80px; }

.info-card, .score-card, .tip-card { padding: 20px 22px; }

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

.info-list .el-icon { color: var(--oc-accent); margin-top: 2px; flex-shrink: 0; }

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
  background: var(--oc-accent);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  text-decoration: none;
  transition: background 0.2s ease, transform 0.2s ease;
}

.tel-btn:hover { background: #185a44; transform: translateY(-1px); }

.score-card {
  text-align: center;
  background: linear-gradient(160deg, #fff 40%, var(--oc-accent-soft));
}

.score-big {
  font-family: var(--oc-font-display);
  font-size: 46px;
  font-weight: 700;
  color: var(--oc-accent);
  line-height: 1.1;
}

.score-card :deep(.el-rate) { justify-content: center; margin-top: 6px; }

.score-tip { margin: 8px 0 0; font-size: 12px; color: var(--oc-ink-soft); }

.tip-card p {
  margin: 0;
  font-size: 13px;
  line-height: 1.8;
  color: var(--oc-ink-soft);
}

@media (max-width: 900px) {
  .detail-layout { grid-template-columns: 1fr; }
  .detail-side { position: static; }
  .hero-main { flex-direction: column; align-items: flex-start; gap: 14px; }
  .service-card { flex-direction: column; align-items: stretch; }
  .service-card .el-button { align-self: flex-end; }
}
</style>
