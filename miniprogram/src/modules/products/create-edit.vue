<template>
  <view class="oc-page create-page">
    <view class="oc-card">
      <input v-model="form.title" class="title-input" placeholder="商品标题（必填）" maxlength="100" />

      <view class="form-row">
        <text class="label">价格</text>
        <input v-model="form.price" class="oc-input price-input" type="digit" placeholder="0.00" />
        <text class="unit">元</text>
      </view>

      <view class="form-row">
        <text class="label">成色</text>
        <picker :range="conditionLabels" @change="onConditionChange">
          <view class="picker-value">
            {{ PRODUCT_CONDITION_MAP[form.condition]?.label || '请选择成色' }}
          </view>
        </picker>
      </view>

      <view class="form-row">
        <text class="label">分类</text>
        <picker :range="categoryNames" @change="onCategoryChange">
          <view class="picker-value">{{ categoryName || '请选择分类' }}</view>
        </picker>
      </view>

      <textarea
        v-model="form.description"
        class="content-area"
        placeholder="描述一下物品的购买时间、使用情况、转让原因…（必填）"
        maxlength="2000"
      ></textarea>

      <!-- 图片：编辑模式远程旧图为只读预览，新选图后全量替换（公共上传组件） -->
      <ImageUploader
        v-model="newImages"
        :max="9"
        :remote-images="existingImageUrls"
        :hint="isEdit && newImages.length ? '（保存后将替换全部旧图）' : ''"
      />
    </view>

    <button class="oc-btn submit-btn" :class="{ 'oc-btn--disabled': submitting }" @tap="submit">
      {{ submitting ? '提交中…' : isEdit ? '保存修改' : '发布' }}
    </button>
  </view>
</template>

<script setup>
/**
 * 商品发布/编辑页（options.id 存在即编辑模式）。
 * 图片契约遵守业务不变量：编辑传 images 为全量替换，不传则保留旧图。
 */
import { ref, computed } from 'vue'
import { onLoad , onShow } from '@dcloudio/uni-app'
import { getProduct, getProductCategories, createProduct, updateProduct } from '@/api/secondhand'
import { requireLogin } from '@/utils/auth'
import { mediaUrl } from '@/utils/format'
import { PRODUCT_CONDITION_MAP, PRODUCT_CONDITION_OPTIONS } from '@/constants/statusMaps'
import { EVENTS } from '@/constants'
import ImageUploader from '@/components/ImageUploader.vue'
import { track } from '@/utils/analytics'
const editId = ref(null)
const form = ref({ title: '', description: '', price: '', condition: '', category: null })
const categories = ref([])
// 新选择的本地临时图片路径；编辑模式加载出的远程图片仅作预览（交给 ImageUploader）
const existingImageUrls = ref([])
const newImages = ref([])
const submitting = ref(false)

const isEdit = computed(() => !!editId.value)
const categoryNames = computed(() => categories.value.map((c) => c.name))
const conditionLabels = PRODUCT_CONDITION_OPTIONS.map((o) => o.label)
const categoryName = computed(() => categories.value.find((c) => c.id === form.value.category)?.name || '')

onLoad(async (options) => {
  // 分类列表先就绪，编辑模式的分类回填才有目标可选
  try {
    const res = await getProductCategories()
    categories.value = res.data?.results || res.data || []
  } catch {
    /* 分类失败时仍可填写文本字段 */
  }
  if (options.id) {
    editId.value = options.id
    try {
      const res = await getProduct(editId.value)
      applyDetail(res.data)
    } catch {
      /* 提示由请求层处理 */
    }
  }
})

function applyDetail(detail) {
  form.value = {
    title: detail.title,
    description: detail.description,
    price: String(detail.price),
    condition: detail.condition,
    category: detail.category?.id ?? null,
  }
  existingImageUrls.value = (detail.images || []).map((it) => mediaUrl(it.image))
}

function onConditionChange(e) {
  form.value.condition = PRODUCT_CONDITION_OPTIONS[Number(e.detail.value)]?.value || ''
}
function onCategoryChange(e) {
  const cat = categories.value[Number(e.detail.value)]
  if (cat) form.value.category = cat.id
}

async function submit() {
  if (submitting.value) return
  if (!requireLogin()) return
  const f = form.value
  if (!f.title.trim()) return void uni.showToast({ title: '请填写标题', icon: 'none' })
  if (!f.price || Number.isNaN(Number(f.price)) || Number(f.price) <= 0)
    return void uni.showToast({ title: '请填写有效价格', icon: 'none' })
  if (!f.condition) return void uni.showToast({ title: '请选择成色', icon: 'none' })
  if (!f.category) return void uni.showToast({ title: '请选择分类', icon: 'none' })
  if (!f.description.trim()) return void uni.showToast({ title: '请描述物品信息', icon: 'none' })

  const payload = {
    title: f.title.trim(),
    description: f.description.trim(),
    price: f.price,
    condition: f.condition,
    category: f.category,
  }

  submitting.value = true
  try {
    if (isEdit.value) {
      // 业务不变量：传 images 即全量替换（删旧建新），不传则保留旧图
      const data = newImages.value.length ? { ...payload, images: newImages.value } : payload
      await updateProduct(editId.value, data)
    } else {
      payload.images = newImages.value
      await createProduct(payload)
    }
    uni.$emit(EVENTS.LIST_CHANGED)
    uni.showToast({ title: isEdit.value ? '保存成功' : '发布成功', icon: 'success' })
    track(isEdit.value ? 'product_update' : 'product_publish')
    setTimeout(() => uni.navigateBack(), 600)
  } catch {
    /* 提示由请求层处理 */
  } finally {
    submitting.value = false
  }
}

onShow(() => {
  if (!requireLogin()) return
})
</script>

<style scoped>
.create-page {
  padding-bottom: 60rpx;
}
.title-input {
  font-size: 34rpx;
  font-weight: 700;
  padding-bottom: 24rpx;
  border-bottom: 1rpx solid var(--oc-border);
}
.form-row {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-top: 26rpx;
}
.label {
  width: 100rpx;
  color: var(--oc-text-secondary);
  flex-shrink: 0;
}
.price-input {
  width: 240rpx;
}
.unit {
  color: var(--oc-text-secondary);
}
.picker-value {
  background: #f7f8fa;
  border-radius: 12rpx;
  padding: 18rpx 24rpx;
  min-width: 260rpx;
  font-size: 28rpx;
}
.content-area {
  width: auto;
  min-height: 300rpx;
  background: #f7f8fa;
  border-radius: 12rpx;
  padding: 20rpx 24rpx;
  font-size: 29rpx;
  line-height: 1.6;
  margin-top: 26rpx;
}
.submit-btn {
  margin-top: 32rpx;
}
</style>
