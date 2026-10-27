<template>
  <view class="oc-page create-page">
    <view class="oc-card">
      <input v-model="form.title" class="title-input" placeholder="标题（必填）" maxlength="100" />

      <!-- 类型选择 -->
      <view class="chips">
        <text
          v-for="opt in POST_TYPE_OPTIONS"
          :key="opt.value"
          class="oc-chip"
          :class="{ 'oc-chip--active': form.post_type === opt.value }"
          @tap="form.post_type = opt.value"
        >
          {{ opt.label }}
        </text>
      </view>

      <textarea v-model="form.content" class="content-area" placeholder="说点什么…（必填）" maxlength="5000"></textarea>

      <input v-model="tagsInput" class="oc-input tags-input" placeholder="话题标签，多个用逗号分隔，如：生活,美食" />

      <!-- 图片选择：≤9 张（公共上传组件） -->
      <ImageUploader v-model="images" :max="9" />
    </view>

    <button class="oc-btn submit-btn" :class="{ 'oc-btn--disabled': submitting }" @tap="submit">
      {{ submitting ? '发布中…' : '发布' }}
    </button>
  </view>
</template>

<script setup>
/**
 * 发布帖子：文本字段走 multipart 一并提交；图片经本地路径多文件上传（≤9 张）。
 */
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { createPost } from '@/api/discussion'
import { requireLogin } from '@/utils/auth'
import { POST_TYPE_OPTIONS } from '@/constants/statusMaps'
import { EVENTS } from '@/constants'
import ImageUploader from '@/components/ImageUploader.vue'
import { track } from '@/utils/analytics'
import { TAB } from '@/router/paths'

const userStore = useUserStore()
const form = ref({ title: '', content: '', post_type: 'chat' })
const tagsInput = ref('')
const images = ref([])
const submitting = ref(false)

async function submit() {
  if (submitting.value) return
  if (!requireLogin()) return
  if (!form.value.title.trim()) return void uni.showToast({ title: '请填写标题', icon: 'none' })
  if (!form.value.content.trim()) return void uni.showToast({ title: '请填写内容', icon: 'none' })

  // 身份兜底校验：发布接口要求已登录会话
  if (!userStore.isLoggedIn) return

  submitting.value = true
  try {
    await createPost({
      title: form.value.title.trim(),
      content: form.value.content.trim(),
      post_type: form.value.post_type,
      tags: tagsInput.value.trim(),
      images: images.value,
    })
    uni.$emit(EVENTS.LIST_CHANGED)
    uni.showToast({ title: '发布成功', icon: 'success' })
    track('post_publish', { post_type: form.value.post_type })
    // 有上一页则返回；无上级页（如分享/直接打开本页）时兜底回首页，避免 navigateBack 在首层报错
    setTimeout(() => {
      const pages = getCurrentPages()
      if (pages.length > 1) uni.navigateBack()
      else uni.reLaunch({ url: TAB.home })
    }, 600)
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
.chips {
  margin: 24rpx 0;
}
.content-area {
  width: auto;
  min-height: 320rpx;
  background: #f7f8fa;
  border-radius: 12rpx;
  padding: 20rpx 24rpx;
  font-size: 29rpx;
  line-height: 1.6;
}
.tags-input {
  margin-top: 20rpx;
}
.submit-btn {
  margin-top: 32rpx;
}
</style>
