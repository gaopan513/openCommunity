<script setup>
/**
 * 二手市场 - 商品详情页
 *
 * 功能：图片轮播、商品信息、状态管理（卖家）、留言
 */
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getProduct, changeProductStatus, deleteProduct, addProductComment } from '@/api/secondhand'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loading = ref(true)
const product = ref(null)
const commentContent = ref('')
const submitting = ref(false)

const isSeller = computed(() => product.value && userStore.userInfo?.id === product.value.seller)

const statusMap = {
  on_sale: { label: '在售', cls: 'status--sale' },
  reserved: { label: '已预订', cls: 'status--reserved' },
  sold: { label: '已售出', cls: 'status--sold' },
  off_shelf: { label: '已下架', cls: 'status--off' },
}

const conditionMap = {
  brand_new: '全新',
  like_new: '九成新',
  good: '八成新',
  fair: '七成新及以下',
}

async function fetchProduct() {
  loading.value = true
  try {
    const res = await getProduct(route.params.id)
    product.value = res.data
  } catch (e) {
    // 错误已处理
  } finally {
    loading.value = false
  }
}

async function handleStatusChange(status) {
  try {
    await changeProductStatus(route.params.id, status)
    ElMessage.success('状态已更新')
    fetchProduct()
  } catch (e) {
    // 错误已处理
  }
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm('确定删除这件商品吗？', '删除确认', { type: 'warning' })
    await deleteProduct(route.params.id)
    ElMessage.success('删除成功')
    router.push('/secondhand')
  } catch (e) {
    // 用户取消或错误已处理
  }
}

async function submitComment() {
  if (!commentContent.value.trim()) {
    ElMessage.warning('留言内容不能为空')
    return
  }
  submitting.value = true
  try {
    await addProductComment(route.params.id, { content: commentContent.value })
    ElMessage.success('留言成功')
    commentContent.value = ''
    fetchProduct()
  } catch (e) {
    // 错误已处理
  } finally {
    submitting.value = false
  }
}

function contactSeller() {
  ElMessage.info(`可通过站内信联系卖家 ${product.value.seller_info?.username}（功能开发中）`)
}

onMounted(fetchProduct)
</script>

<template>
  <div class="oc-page product-detail" v-loading="loading">
    <el-button text @click="router.push('/secondhand')" style="margin-bottom: 16px">
      <el-icon><ArrowLeft /></el-icon> 返回市场
    </el-button>

    <div v-if="product" class="detail-layout">
      <!-- 左侧：图片 -->
      <div class="oc-card gallery-card">
        <el-carousel v-if="product.images && product.images.length" height="420px" :autoplay="false">
          <el-carousel-item v-for="img in product.images" :key="img.id">
            <el-image :src="img.image" fit="contain" class="carousel-img" :preview-src-list="product.images.map(i => i.image)" />
          </el-carousel-item>
        </el-carousel>
        <div v-else class="gallery-placeholder">
          <el-icon :size="60"><Picture /></el-icon>
          <p>暂无图片</p>
        </div>
      </div>

      <!-- 右侧：信息 -->
      <div class="info-column">
        <div class="oc-card info-card">
          <div class="info-head">
            <span class="status-badge" :class="statusMap[product.status]?.cls">
              {{ statusMap[product.status]?.label }}
            </span>
            <span class="condition-chip">{{ conditionMap[product.condition] }}</span>
          </div>

          <h1 class="product-title">{{ product.title }}</h1>
          <div class="product-price">¥{{ product.price }}</div>

          <div class="seller-box">
            <el-avatar :size="44" :src="product.seller_info?.avatar">
              {{ product.seller_info?.username?.charAt(0)?.toUpperCase() }}
            </el-avatar>
            <div class="seller-info">
              <div class="seller-name">{{ product.seller_info?.username }}</div>
              <div class="seller-label">卖家 · {{ product.view_count }} 人看过</div>
            </div>
            <el-button type="primary" round @click="contactSeller">联系卖家</el-button>
          </div>

          <div class="desc-block">
            <h4>商品描述</h4>
            <p>{{ product.description }}</p>
          </div>

          <!-- 卖家操作 -->
          <div v-if="isSeller" class="seller-actions">
            <el-divider>卖家管理</el-divider>
            <div class="action-btns">
              <el-button v-if="product.status === 'on_sale'" @click="handleStatusChange('reserved')">标记已预订</el-button>
              <el-button v-if="product.status === 'on_sale' || product.status === 'reserved'" type="success" @click="handleStatusChange('sold')">标记已售出</el-button>
              <el-button v-if="product.status === 'on_sale'" @click="handleStatusChange('off_shelf')">下架</el-button>
              <el-button v-if="product.status === 'off_shelf'" @click="handleStatusChange('on_sale')">重新上架</el-button>
              <el-button type="danger" plain @click="handleDelete">删除</el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 留言区 -->
    <div v-if="product" class="oc-card comment-card">
      <h3 class="section-title">买家留言 <span class="count">({{ product.comments?.length || 0 }})</span></h3>

      <div class="comment-input">
        <el-input v-model="commentContent" placeholder="对这件宝贝感兴趣？给卖家留个言..." @keyup.enter="submitComment">
          <template #append>
            <el-button :loading="submitting" @click="submitComment">发送</el-button>
          </template>
        </el-input>
      </div>

      <div class="comment-list">
        <div v-for="c in product.comments" :key="c.id" class="comment-item">
          <el-avatar :size="34" :src="c.author_info?.avatar">
            {{ c.author_info?.username?.charAt(0)?.toUpperCase() }}
          </el-avatar>
          <div class="comment-body">
            <div class="comment-author">{{ c.author_info?.username }}</div>
            <div class="comment-text">{{ c.content }}</div>
            <div class="comment-time">{{ c.created_at }}</div>
          </div>
        </div>
        <div v-if="!product.comments || product.comments.length === 0" class="oc-empty">
          还没有留言
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.detail-layout {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.gallery-card {
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.carousel-img {
  width: 100%;
  height: 420px;
}

.gallery-placeholder {
  width: 100%;
  height: 420px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #d8cfc0;
  gap: 10px;
}

.info-card {
  padding: 28px;
}

.info-head {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 14px;
}

.status-badge {
  padding: 4px 14px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
}

.status--sale { background: var(--oc-accent); }
.status--reserved { background: var(--oc-gold); }
.status--sold { background: #999; }
.status--off { background: #bbb; }

.condition-chip {
  background: var(--oc-paper);
  color: var(--oc-ink-soft);
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 999px;
  border: 1px solid var(--oc-line);
}

.product-title {
  font-family: var(--oc-font-display);
  font-size: 26px;
  font-weight: 700;
  color: var(--oc-ink);
  margin: 0 0 12px;
  line-height: 1.35;
}

.product-price {
  font-size: 34px;
  font-weight: 800;
  color: var(--oc-primary);
  margin-bottom: 20px;
}

.seller-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  background: var(--oc-paper);
  border-radius: 12px;
  margin-bottom: 20px;
}

.seller-info { flex: 1; }
.seller-name { font-weight: 700; color: var(--oc-ink); font-size: 15px; }
.seller-label { font-size: 12px; color: var(--oc-ink-soft); margin-top: 2px; }

.desc-block h4 {
  font-size: 15px;
  font-weight: 700;
  color: var(--oc-ink);
  margin: 0 0 8px;
}

.desc-block p {
  color: var(--oc-ink-soft);
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  margin: 0;
}

.action-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.comment-card {
  padding: 28px 32px;
}

.section-title {
  font-size: 19px;
  font-weight: 700;
  color: var(--oc-ink);
  margin: 0 0 18px;
}

.section-title .count { color: var(--oc-ink-soft); font-weight: 400; font-size: 15px; }

.comment-list {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comment-item { display: flex; gap: 12px; }
.comment-body { flex: 1; }
.comment-author { font-weight: 700; color: var(--oc-ink); font-size: 14px; }
.comment-text { color: var(--oc-ink); font-size: 14px; line-height: 1.7; margin: 4px 0; }
.comment-time { font-size: 12px; color: var(--oc-ink-soft); }

@media (max-width: 900px) {
  .detail-layout { grid-template-columns: 1fr; }
}
</style>
