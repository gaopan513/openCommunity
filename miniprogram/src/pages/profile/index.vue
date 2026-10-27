<template>
  <view class="oc-page">
    <!-- 用户卡片 -->
    <view class="oc-card user-card">
      <block v-if="userStore.isLoggedIn">
        <image class="oc-avatar avatar" :src="avatarUrl" mode="aspectFill" @tap="changeAvatar" />
        <view class="user-info">
          <view class="username">{{ userStore.username }}</view>
          <view class="role-tag" :style="{ background: 'var(--oc-primary-light)', color: 'var(--oc-primary)' }">
            {{ profile?.role_display || '居民' }}
          </view>
        </view>
      </block>
      <block v-else>
        <view class="avatar avatar--empty">邻</view>
        <view class="user-info">
          <view class="username">未登录</view>
          <view class="hint">游客可浏览，登录后可发布互动</view>
        </view>
        <button class="login-btn" size="mini" @tap="goLogin">去登录</button>
      </block>
    </view>

    <!-- 资料编辑（仅已登录） -->
    <template v-if="userStore.isLoggedIn">
      <view class="oc-card">
        <view class="form-title">基本资料</view>
        <view class="form-row">
          <text class="label">手机号</text>
          <input v-model="profile.phone" class="oc-input grow" type="number" maxlength="11" placeholder="选填" />
        </view>
        <view class="form-row">
          <text class="label">所属小区</text>
          <input v-model="profile.community_name" class="oc-input grow" placeholder="如：阳光花园" />
        </view>
        <view class="form-row">
          <text class="label">详细地址</text>
          <input v-model="profile.address" class="oc-input grow" placeholder="如：3栋2单元501" />
        </view>
        <button class="oc-btn save-btn" :class="{ 'oc-btn--disabled': saving }" @tap="saveProfile">
          {{ saving ? '保存中…' : '保存资料' }}
        </button>
      </view>
    </template>

    <!-- 功能入口 -->
    <view class="oc-card menu">
      <view v-for="(item, i) in menus" :key="i" class="menu-item" hover-class="menu-item--hover" @tap="go(item)">
        <text>{{ item.label }}</text>
        <text class="arrow">›</text>
      </view>
    </view>

    <button v-if="userStore.isLoggedIn" class="oc-btn oc-btn--plain logout-btn" @tap="handleLogout">退出登录</button>
  </view>
</template>

<script setup>
/**
 * 个人中心：资料查看/编辑、头像更换、我的预约/商品入口、退出登录。
 * 微信静默登录用户同样走 /users/profile/ 编辑资料。
 */
import { ref, computed } from 'vue'
import { onShow, onPullDownRefresh } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { getProfile, updateProfile } from '@/api/auth'
import { uploadMultipart } from '@/utils/upload'
import { mediaUrl } from '@/utils/format'
import { ROUTE, PAGE, TAB } from '@/router/paths'

const userStore = useUserStore()
const profile = ref({})
const saving = ref(false)

const menus = [
  { label: '我的预约', to: () => uni.navigateTo({ url: ROUTE.bookingsMy() }) },
  { label: '我的商品', to: () => uni.navigateTo({ url: ROUTE.productMine() }) },
]

const avatarUrl = computed(() => mediaUrl(profile.value.avatar))

onShow(async () => {
  if (!userStore.isLoggedIn) return
  try {
    const res = await getProfile()
    profile.value = res.data || {}
    userStore.updateUserInfo(res.data)
  } catch {
    // 提示由请求层处理；保持本地缓存展示
  }
})

onPullDownRefresh(async () => {
  if (userStore.isLoggedIn) {
    try {
      const res = await getProfile()
      profile.value = res.data || {}
    } catch {
      /* 忽略刷新失败 */
    }
  }
  uni.stopPullDownRefresh()
})

/** 头像更换：微信选图 → multipart PUT /users/profile/（单文件，字段名 avatar） */
function changeAvatar() {
  uni.chooseMedia({
    count: 1,
    mediaType: ['image'],
    sizeType: ['compressed'],
    success: async (res) => {
      const path = res.tempFiles[0].tempFilePath
      try {
        const result = await uploadMultipart({
          url: '/users/profile/',
          method: 'PUT',
          fields: {},
          files: [{ path }],
          name: 'avatar',
        })
        profile.value = result.data
        userStore.updateUserInfo(result.data)
        uni.showToast({ title: '头像已更新', icon: 'success' })
      } catch {
        /* 错误提示已在工具层弹出 */
      }
    },
  })
}

async function saveProfile() {
  if (saving.value) return
  saving.value = true
  try {
    const res = await updateProfile({
      phone: profile.value.phone || '',
      community_name: profile.value.community_name || '',
      address: profile.value.address || '',
    })
    profile.value = res.data
    userStore.updateUserInfo(res.data)
    uni.showToast({ title: '保存成功', icon: 'success' })
  } catch {
    /* 请求层已提示 */
  } finally {
    saving.value = false
  }
}

async function handleLogout() {
  const confirmed = await new Promise((resolve) => {
    uni.showModal({
      title: '退出登录',
      content: '确定要退出当前账号吗？',
      success: (r) => resolve(r.confirm),
    })
  })
  if (!confirmed) return
  await userStore.logout()
  profile.value = {}
  uni.showToast({ title: '已退出登录', icon: 'none' })
}

function go(item) {
  item.to()
}

function goLogin() {
  uni.navigateTo({ url: `${PAGE.login}?redirect=${TAB.profile}` })
}
</script>

<style scoped>
.user-card {
  display: flex;
  align-items: center;
  gap: 24rpx;
}
.avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: #ececec;
}
.avatar--empty {
  line-height: 120rpx;
  text-align: center;
  color: #fff;
  font-size: 48rpx;
  background: var(--oc-primary);
}
.user-info {
  flex: 1;
}
.username {
  font-size: 34rpx;
  font-weight: 700;
}
.hint {
  font-size: 24rpx;
  color: var(--oc-text-secondary);
  margin-top: 8rpx;
}
.role-tag {
  display: inline-block;
  margin-top: 10rpx;
  padding: 4rpx 16rpx;
  border-radius: 8rpx;
  font-size: 22rpx;
}
.login-btn {
  background: var(--oc-primary);
  color: #fff;
}
.form-title {
  font-size: 30rpx;
  font-weight: 700;
  margin-bottom: 24rpx;
}
.form-row {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-bottom: 22rpx;
}
.label {
  width: 140rpx;
  color: var(--oc-text-secondary);
  flex-shrink: 0;
}
.grow {
  flex: 1;
}
.save-btn {
  margin-top: 8rpx;
}
.menu-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx 8rpx;
  font-size: 30rpx;
  border-bottom: 1rpx solid var(--oc-border);
}
.menu-item:last-child {
  border-bottom: none;
}
.menu-item--hover {
  background: #fafafa;
}
.arrow {
  color: var(--oc-text-secondary);
  font-size: 36rpx;
}
.logout-btn {
  margin-top: 12rpx;
}
</style>
