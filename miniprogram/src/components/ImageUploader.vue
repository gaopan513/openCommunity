<template>
  <view>
    <!-- 本地新图（可删除）+ 远程旧图（只读预览，可选） -->
    <view class="img-grid">
      <template v-for="(url, i) in localImages" :key="'l' + i">
        <view class="img-item">
          <image class="img" :src="url" mode="aspectFill" @tap="preview(i)" />
          <view class="remove" @tap.stop="removeLocal(i)">×</view>
        </view>
      </template>
      <template v-for="(url, i) in remoteImages" :key="'r' + i">
        <view class="img-item">
          <image class="img remote" :src="url" mode="aspectFill" @tap="preview(localImages.length + i)" />
        </view>
      </template>
      <view v-if="localImages.length < max" class="img-add" @tap="chooseImages">＋</view>
    </view>
    <view class="count-hint"> {{ displayCount }}/{{ max }} 张{{ hint }} </view>
  </view>
</template>

<script setup>
/**
 * 多图上传组件（发帖 / 商品发布共用的本地选图网格）。
 *
 * 统一处理：选图（含隐私授权/权限被拒引导）、预览、删除、9 图上限。
 * - 本地新图：可删除，v-model 绑定到父组件 images 数组。
 * - 远程旧图（可选，编辑模式）：只读预览，不可删，用于展示已存在的资源。
 * - 父组件提交时，仅需上传本地新图（图片契约由业务层决定全量/增量）。
 */
import { ref, watch, computed } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  max: { type: Number, default: 9 },
  /** 编辑模式下的远程旧图（只读预览，不参与选择） */
  remoteImages: { type: Array, default: () => [] },
  /** 显示提示文案（如“保存后将替换全部旧图”） */
  hint: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const localImages = ref([...props.modelValue])
// 父组件 v-model 数据变化时同步（如编辑页加载完成后回填）
watch(
  () => props.modelValue,
  (v) => {
    localImages.value = [...(v || [])]
  }
)

const displayCount = computed(() =>
  props.remoteImages.length ? Math.max(localImages.value.length, props.remoteImages.length) : localImages.value.length
)

function sync() {
  emit('update:modelValue', [...localImages.value])
}

function chooseImages() {
  uni.chooseMedia({
    count: props.max - localImages.value.length,
    mediaType: ['image'],
    // 选图即压缩，避免多张原图一次性读入内存
    sizeType: ['compressed'],
    success: (res) => {
      res.tempFiles.forEach((f) => {
        if (localImages.value.length < props.max) localImages.value.push(f.tempFilePath)
      })
      sync()
    },
    fail: (err) => {
      // 不把失败静默吞掉：区分隐私未声明/权限被拒/其它，提示下一步动作
      const msg = (err && err.errMsg) || ''
      if (msg.includes('cancel')) return
      if (msg.includes('privacy agreement') || err.errno === 112) {
        uni.showModal({
          title: '需要授权相册',
          content: '请在微信公众平台「设置 → 服务内容声明 → 用户隐私保护指引」中声明相册能力后重试。',
          showCancel: false,
        })
        return
      }
      if (msg.includes('auth deny') || err.errno === 101) {
        uni.showToast({ title: '已拒绝相册权限，请在设置中开启', icon: 'none' })
        return
      }
      uni.showToast({ title: '无法选择图片', icon: 'none' })
      console.error('[chooseMedia]', err)
    },
  })
}

function removeLocal(index) {
  localImages.value.splice(index, 1)
  sync()
}

function preview(index) {
  // 本地 + 远程拼接为完整预览列表
  const all = [...localImages.value, ...props.remoteImages]
  uni.previewImage({ urls: all, current: index })
}
</script>

<style scoped>
.img-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 24rpx;
}
.img-item {
  position: relative;
  width: calc((100% - 24rpx) / 3);
  height: 200rpx;
}
.img {
  width: 100%;
  height: 200rpx;
  border-radius: 12rpx;
  background: #f0f0f0;
}
.img.remote {
  opacity: 0.85;
  border: 1rpx dashed var(--oc-border);
  box-sizing: border-box;
}
.remove {
  position: absolute;
  top: -12rpx;
  right: -12rpx;
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  text-align: center;
  line-height: 40rpx;
  font-size: 30rpx;
}
.img-add {
  width: calc((100% - 24rpx) / 3);
  height: 200rpx;
  border-radius: 12rpx;
  background: #f7f8fa;
  color: var(--oc-text-secondary);
  font-size: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
.count-hint {
  color: var(--oc-text-secondary);
  font-size: 22rpx;
  margin-top: 10rpx;
}
</style>
