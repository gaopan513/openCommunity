/**
 * 用户状态管理（Pinia Store）
 * 
 * 管理用户登录状态、Token、用户信息。
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, register as registerApi, logout as logoutApi } from '@/api/auth'

/** 安全解析 localStorage 中的用户信息，缓存损坏时回退 null 并清理，避免应用白屏 */
function safeParseUser() {
  const raw = localStorage.getItem('user_info')
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    localStorage.removeItem('user_info')
    return null
  }
}

export const useUserStore = defineStore('user', () => {
  // 状态
  const userInfo = ref(safeParseUser())
  const accessToken = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  
  // 计算属性
  const isLoggedIn = computed(() => !!accessToken.value)
  const isMerchant = computed(() => userInfo.value?.role === 'merchant')
  const isAdmin = computed(() => userInfo.value?.role === 'admin')
  const username = computed(() => userInfo.value?.username || '')
  
  /**
   * 用户登录
   * @param {string} username - 用户名
   * @param {string} password - 密码
   */
  async function login(username, password) {
    const res = await loginApi({ username, password })
    setAuthData(res.data)
    return res
  }
  
  /**
   * 用户注册
   * @param {Object} data - 注册信息
   */
  async function register(data) {
    const res = await registerApi(data)
    setAuthData(res.data)
    return res
  }
  
  /**
   * 保存认证数据到状态和 localStorage
   */
  function setAuthData(data) {
    userInfo.value = data.user
    accessToken.value = data.access
    refreshToken.value = data.refresh
    
    localStorage.setItem('user_info', JSON.stringify(data.user))
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
  }
  
  /**
   * 仅清理本地登录态（store + localStorage），不请求后端。
   * 供 401 踢出场景复用（request.js 动态引入本 store 调用）。
   */
  function clearLocalAuth() {
    userInfo.value = null
    accessToken.value = ''
    refreshToken.value = ''

    localStorage.removeItem('user_info')
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  /**
   * 退出登录：先通知后端拉黑 refresh token（防止旧会话继续续期），
   * 再清除本地状态；后端调用失败不阻塞本地登出
   */
  async function logout() {
    const refresh = refreshToken.value || localStorage.getItem('refresh_token')
    if (refresh) {
      try {
        await logoutApi({ refresh })
      } catch {
        // token 已失效/网络异常等：本地照常登出
      }
    }
    clearLocalAuth()
  }
  
  /**
   * 更新用户资料
   */
  function updateUserInfo(info) {
    userInfo.value = { ...userInfo.value, ...info }
    localStorage.setItem('user_info', JSON.stringify(userInfo.value))
  }
  
  return {
    userInfo,
    accessToken,
    refreshToken,
    isLoggedIn,
    isMerchant,
    isAdmin,
    username,
    login,
    register,
    logout,
    clearLocalAuth,
    updateUserInfo,
  }
})
