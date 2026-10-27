<template>
  <view class="login-page">
    <!-- 品牌区 -->
    <view class="brand">
      <view class="brand-logo">邻</view>
      <view class="brand-title">邻里社区</view>
      <view class="brand-sub">家门口的互助生活圈</view>
    </view>

    <!-- 登录操作 -->
    <button class="oc-btn wechat-btn" :class="{ 'oc-btn--disabled': loggingIn }" @tap="handleLogin">
      {{ loggingIn ? '登录中…' : '微信一键登录' }}
    </button>
    <view class="guest-link" @tap="goHome">先逛逛，游客浏览</view>

    <template v-if="isDev">
      <view class="dev-divider">— 本地开发调试 —</view>
      <button class="oc-btn dev-btn" :class="{ 'oc-btn--disabled': loggingIn }" @tap="handleTestLogin">
        {{ loggingIn ? '登录中…' : '本地测试登录' }}
      </button>
    </template>

    <view class="tips">首次登录将自动创建账号（居民身份）</view>
  </view>
</template>

<script setup>
/**
 * 登录页：默认微信静默登录入口。
 * 开发模式下额外提供「本地测试登录」旁路，用于无真实小程序 AppID 时联调。
 */
import { ref } from 'vue'
import { useUserStore } from '@/stores/user'
import { TAB } from '@/router/paths'

const userStore = useUserStore()
const loggingIn = ref(false)

// 生产构建（npm run build:mp-weixin）下即 false，测试登录入口不会出现
const isDev = import.meta.env.DEV

async function handleLogin() {
  if (loggingIn.value) return
  loggingIn.value = true
  try {
    await userStore.loginByWechat()
    uni.showToast({ title: '登录成功', icon: 'success' })
    setTimeout(() => backOrHome(), 600)
  } catch {
    // 失败提示由请求层统一弹出；常见原因是未配置 AppID 或合法域名
    loggingIn.value = false
  }
}

/** 本地测试登录：走 debug-login 旁路，仅供开发联调 */
async function handleTestLogin() {
  if (loggingIn.value) return
  loggingIn.value = true
  try {
    await userStore.loginByWechatTest()
    uni.showToast({ title: '登录成功', icon: 'success' })
    setTimeout(() => backOrHome(), 600)
  } catch {
    loggingIn.value = false
  }
}

function goHome() {
  uni.reLaunch({ url: TAB.home })
}

/** 返回来源页或首页（支持 tabBar 页面：reLaunch 均可打开） */
function backOrHome() {
  const pages = getCurrentPages()
  const options = pages[pages.length - 1]?.$page?.options || pages[pages.length - 1]?.options || {}
  const redirect = decodeURIComponent(options.redirect || '')
  // 仅接受站内路径（主包 pages/ 或分包 modules/），非法值回首页；跳转失败兜底回首页避免卡死
  const url = /^\/(pages|modules)\//.test(redirect) ? redirect : TAB.home
  uni.reLaunch({
    url,
    fail: () => uni.reLaunch({ url: TAB.home }),
  })
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  padding: 120rpx 64rpx;
  box-sizing: border-box;
  background: #fff;
}
.brand {
  text-align: center;
  margin-bottom: 140rpx;
}
.brand-logo {
  width: 140rpx;
  height: 140rpx;
  border-radius: 36rpx;
  margin: 0 auto 32rpx;
  background: var(--oc-primary);
  color: #fff;
  font-size: 72rpx;
  font-weight: 700;
  line-height: 140rpx;
}
.brand-title {
  font-size: 44rpx;
  font-weight: 700;
}
.brand-sub {
  color: var(--oc-text-secondary);
  font-size: 26rpx;
  margin-top: 12rpx;
}
.wechat-btn {
  width: 100%;
}
.guest-link {
  text-align: center;
  color: var(--oc-text-secondary);
  font-size: 26rpx;
  margin-top: 40rpx;
}
.dev-divider {
  text-align: center;
  color: var(--oc-text-secondary);
  font-size: 24rpx;
  margin: 48rpx 0 24rpx;
}
.dev-btn {
  width: 100%;
  background: #f5f6f7;
  color: var(--oc-text-primary);
}
.tips {
  position: fixed;
  left: 0;
  right: 0;
  bottom: calc(60rpx + constant(safe-area-inset-bottom));
  bottom: calc(60rpx + env(safe-area-inset-bottom));
  text-align: center;
  color: var(--oc-text-secondary);
  font-size: 24rpx;
}
</style>
