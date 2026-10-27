<template>
  <view class="cb-bar oc-safe-bottom">
    <!-- 回复状态条（楼中楼回复场景，点击取消回到普通评论） -->
    <view v-if="replyTo" class="cb-replying">
      回复 {{ replyTo.author_info?.username }}
      <text class="cb-cancel" @tap="emit('cancel-reply')">取消</text>
    </view>
    <view class="cb-row">
      <input
        v-model="text"
        class="oc-input cb-input"
        :placeholder="replyTo ? `回复 ${replyTo.author_info?.username}…` : placeholder"
        confirm-type="send"
        @confirm="submit"
      />
      <button class="cb-send" size="mini" @tap="submit">{{ btnText }}</button>
    </view>
  </view>
</template>

<script setup>
/**
 * 详情页底部评论/回答/留言输入条（固定底栏）。
 * 帖子详情的楼中楼回复通过 replyTo 传入（显示回复条 + 动态 placeholder）。
 *
 * props: placeholder / btnText / replyTo（被回复的评论对象或 null）/ submitting
 * emits: submit（内容字符串，父级成功后调 clear() 清空输入框）、cancel-reply
 */
import { ref } from 'vue'

const props = defineProps({
  placeholder: { type: String, default: '友善评论，温暖邻里' },
  btnText: { type: String, default: '发送' },
  replyTo: { type: Object, default: null },
  submitting: { type: Boolean, default: false },
})
const emit = defineEmits(['submit', 'cancel-reply'])

const text = ref('')

function submit() {
  if (props.submitting) return
  const content = text.value.trim()
  if (!content) return
  emit('submit', content)
}

/** 父级提交成功后调用，清空输入内容 */
function clear() {
  text.value = ''
}

defineExpose({ clear })
</script>

<style scoped>
.cb-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  background: #fff;
  padding: 16rpx 24rpx;
  box-shadow: 0 -4rpx 16rpx rgba(0, 0, 0, 0.04);
  z-index: 100;
}
.cb-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.cb-input {
  flex: 1;
}
.cb-send {
  background: var(--oc-primary);
  color: #fff;
}
.cb-replying {
  font-size: 24rpx;
  color: var(--oc-text-secondary);
  margin-bottom: 10rpx;
}
.cb-cancel {
  color: var(--oc-primary);
  margin-left: 16rpx;
}
</style>
