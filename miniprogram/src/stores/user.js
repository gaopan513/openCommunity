/**
 * 用户状态管理（Pinia Store）
 *
 * 与 frontend/src/stores/user.js 结构对齐：
 * - 三键存储：user_info / access_token / refresh_token（uni Storage 替代 localStorage）
 * - 登录入口为微信静默登录 loginByWechat
 * - clearLocalAuth 供 request 层 401 踢出复用
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { wechatLogin as wechatLoginApi, debugLogin as debugLoginApi, logout as logoutApi } from '@/api/auth'

/**
 * 安全解析 Storage 中的用户信息：
 * uni.setStorageSync 存对象时读回即是对象；兼容历史字符串形式，损坏时清理避免白屏
 */
function safeParseUser() {
  const raw = uni.getStorageSync('user_info')
  if (!raw) return null
  if (typeof raw === 'object') return raw
  try {
    return JSON.parse(raw)
  } catch {
    uni.removeStorageSync('user_info')
    return null
  }
}

/** Promise 化 wx.login */
function wxLogin() {
  return new Promise((resolve, reject) => {
    uni.login({
      provider: 'weixin',
      success: resolve,
      fail: reject,
    })
  })
}

export const useUserStore = defineStore('user', () => {
  // 状态
  const userInfo = ref(safeParseUser())
  const accessToken = ref(uni.getStorageSync('access_token') || '')
  const refreshToken = ref(uni.getStorageSync('refresh_token') || '')

  // 计算属性（与 Web 端一致，保留以对齐结构）
  const isLoggedIn = computed(() => !!accessToken.value)
  const isMerchant = computed(() => userInfo.value?.role === 'merchant')
  const isAdmin = computed(() => userInfo.value?.role === 'admin')
  const username = computed(() => userInfo.value?.username || '')

  /**
   * 微信静默登录：wx.login 取 code → 后端换取 JWT 并自动注册 resident
   * 失败向上抛出，由调用方决定是否提示（冷启动调用需静默吞掉）
   */
  async function loginByWechat() {
    const loginRes = await wxLogin()
    if (!loginRes.code) throw new Error('wx.login 未返回 code')
    const res = await wechatLoginApi({ code: loginRes.code })
    setAuthData(res.data)
    return res.data.user
  }

  /**
   * 本地测试登录：wx.login 取 code 后按固定规则映射为归一化 openid，
   * 交给后端 debug-login 接口换取 JWT，绕开 jscode2session。
   * 仅在无真实小程序 AppID/Secret 时用于本地联调，生产该接口返回 404。
   */
  async function loginByWechatTest() {
    const loginRes = await wxLogin()
    if (!loginRes.code) throw new Error('wx.login 未返回 code')
    const openid = `dev_${loginRes.code}`.slice(0, 64)
    const res = await debugLoginApi({ openid })
    setAuthData(res.data)
    return res.data.user
  }

  /** 保存认证数据到状态和 Storage */
  function setAuthData(data) {
    userInfo.value = data.user
    accessToken.value = data.access
    refreshToken.value = data.refresh

    uni.setStorageSync('user_info', data.user)
    uni.setStorageSync('access_token', data.access)
    uni.setStorageSync('refresh_token', data.refresh)
  }

  /**
   * 仅清理本地登录态（store + Storage），不请求后端。
   * 供 401 踢出场景复用（request.js 动态引入本 store 调用）。
   */
  function clearLocalAuth() {
    userInfo.value = null
    accessToken.value = ''
    refreshToken.value = ''

    ;['user_info', 'access_token', 'refresh_token'].forEach((k) => uni.removeStorageSync(k))
  }

  /** 退出登录：先通知后端拉黑 refresh token，再清本地状态 */
  async function logout() {
    const refresh = refreshToken.value || uni.getStorageSync('refresh_token')
    if (refresh) {
      try {
        await logoutApi({ refresh })
      } catch {
        // token 已失效/网络异常等：本地照常登出
      }
    }
    clearLocalAuth()
  }

  /** 更新用户资料缓存 */
  function updateUserInfo(info) {
    userInfo.value = { ...userInfo.value, ...info }
    uni.setStorageSync('user_info', userInfo.value)
  }

  return {
    userInfo,
    accessToken,
    refreshToken,
    isLoggedIn,
    isMerchant,
    isAdmin,
    username,
    loginByWechat,
    loginByWechatTest,
    logout,
    clearLocalAuth,
    updateUserInfo,
  }
})
