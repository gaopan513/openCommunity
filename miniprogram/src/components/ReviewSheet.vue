<template>
  <view v-if="show" class="rs-mask" @tap="close">
    <view class="rs-sheet oc-safe-bottom" @tap.stop>
      <view class="rs-title">{{ title }}</view>
      <!-- 点选目标星级（原“点击循环+1”交互无法直达想要的分数） -->
      <view class="rs-rate-row">
        <text v-for="i in 5" :key="i" class="rs-star" :class="{ on: i <= rating }" @tap="rating = i">★</text>
        <text class="rs-rate-num">{{ rating }} 分</text>
      </view>
      <textarea v-model="content" class="rs-area" :placeholder="placeholder" maxlength="500" />
      <button class="oc-btn rs-btn" :class="{ 'oc-btn--disabled': submitting }" @tap="submit">
        {{ submitting ? '提交中…' : '提交评价' }}
      </button>
    </view>
  </view>
</template>

<script setup>
/**
 * 评价弹层（底部上滑 sheet）：星级点选 + 评语输入。
 * 商家评价 / 家政预约评价共用；表单状态组件内部持有，每次打开自动重置。
 *
 * props: show / title / placeholder / submitting
 * emits: update:show（关闭）、submit（{rating, content}，父级负责调接口）
 */
import { ref, watch } from 'vue'

const props = defineProps({
  show: { type: Boolean, default: false },
  title: { type: String, default: '发表评价' },
  placeholder: { type: String, default: '说说你的体验…' },
  submitting: { type: Boolean, default: false },
})
const emit = defineEmits(['update:show', 'submit'])

const rating = ref(5)
const content = ref('')

// 每次打开重置表单（默认 5 分）
watch(
  () => props.show,
  (v) => {
    if (v) {
      rating.value = 5
      content.value = ''
    }
  }
)

function close() {
  if (props.submitting) return
  emit('update:show', false)
}

function submit() {
  if (props.submitting) return
  const text = content.value.trim()
  if (!text) return void uni.showToast({ title: '请填写评价内容', icon: 'none' })
  emit('submit', { rating: rating.value, content: text })
}
</script>

<style scoped>
.rs-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 200;
  display: flex;
  align-items: flex-end;
}
.rs-sheet {
  width: 100%;
  background: #fff;
  border-radius: 32rpx 32rpx 0 0;
  padding: 40rpx 32rpx;
  box-sizing: border-box;
}
.rs-title {
  font-size: 34rpx;
  font-weight: 700;
  text-align: center;
}
.rs-rate-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  margin: 30rpx 0;
}
.rs-star {
  font-size: 56rpx;
  color: #e5e6eb;
}
.rs-star.on {
  color: #ff9a2e;
}
.rs-rate-num {
  color: var(--oc-text-secondary);
  font-size: 25rpx;
  margin-left: 14rpx;
}
.rs-area {
  width: auto;
  min-height: 200rpx;
  background: #f7f8fa;
  border-radius: 12rpx;
  padding: 20rpx 24rpx;
  font-size: 28rpx;
}
.rs-btn {
  margin-top: 28rpx;
}
</style>
