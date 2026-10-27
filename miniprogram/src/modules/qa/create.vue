<template>
  <view class="oc-page create-page">
    <view class="oc-card">
      <input v-model="form.title" class="title-input" placeholder="问题标题（必填）" maxlength="200" />
      <textarea
        v-model="form.content"
        class="content-area"
        placeholder="详细描述你的问题，越具体越容易被解答（必填）"
        maxlength="5000"
      ></textarea>

      <!-- 标签添加 -->
      <view class="tag-add-row">
        <input
          v-model="newTag"
          class="oc-input tag-input"
          placeholder="添加标签，如：装修"
          confirm-type="done"
          @confirm="addTag"
        />
        <button class="add-tag-btn" size="mini" @tap="addTag">添加</button>
      </view>
      <view v-if="form.tags.length" class="tag-list">
        <view v-for="tag in form.tags" :key="tag" class="tag-chip" @tap="removeTag(tag)"> #{{ tag }} × </view>
      </view>
    </view>

    <button class="oc-btn submit-btn" :class="{ 'oc-btn--disabled': submitting }" @tap="submit">
      {{ submitting ? '提交中…' : '提交问题' }}
    </button>
  </view>
</template>

<script setup>
/**
 * 提问页：tags 为字符串数组（后端 QuestionCreateSerializer 自动创建不存在的标签）。
 */
import { ref } from 'vue'
import { createQuestion } from '@/api/qa'
import { requireLogin } from '@/utils/auth'
import { EVENTS } from '@/constants'
import { track } from '@/utils/analytics'
const form = ref({ title: '', content: '', tags: [] })
const newTag = ref('')
const submitting = ref(false)

function addTag() {
  const name = newTag.value.trim()
  if (!name || form.value.tags.includes(name)) {
    newTag.value = ''
    return
  }
  if (form.value.tags.length >= 5) {
    return void uni.showToast({ title: '最多添加 5 个标签', icon: 'none' })
  }
  form.value.tags.push(name)
  newTag.value = ''
}
function removeTag(tag) {
  form.value.tags = form.value.tags.filter((t) => t !== tag)
}

async function submit() {
  if (submitting.value) return
  if (!requireLogin()) return
  if (!form.value.title.trim()) return void uni.showToast({ title: '请填写标题', icon: 'none' })
  if (!form.value.content.trim()) return void uni.showToast({ title: '请描述你的问题', icon: 'none' })

  submitting.value = true
  try {
    await createQuestion({
      title: form.value.title.trim(),
      content: form.value.content.trim(),
      tags: form.value.tags,
    })
    uni.$emit(EVENTS.LIST_CHANGED)
    uni.showToast({ title: '提问成功', icon: 'success' })
    track('qa_create')
    setTimeout(() => uni.navigateBack(), 600)
  } catch {
    /* 提示由请求层处理 */
  } finally {
    submitting.value = false
  }
}
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
.content-area {
  width: auto;
  min-height: 360rpx;
  background: #f7f8fa;
  border-radius: 12rpx;
  padding: 20rpx 24rpx;
  font-size: 29rpx;
  line-height: 1.6;
  margin-top: 24rpx;
}
.tag-add-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 24rpx;
}
.tag-input {
  flex: 1;
}
.add-tag-btn {
  background: var(--oc-primary);
  color: #fff;
}
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
  margin-top: 18rpx;
}
.tag-chip {
  background: var(--oc-primary-light);
  color: var(--oc-primary);
  font-size: 25rpx;
  padding: 8rpx 22rpx;
  border-radius: 26rpx;
}
.submit-btn {
  margin-top: 32rpx;
}
</style>
