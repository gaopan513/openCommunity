/**
 * Axios 请求实例封装
 * 
 * 统一处理：
 * - 基础 URL 配置
 * - JWT Token 自动携带
 * - 响应拦截（错误提示、401 静默刷新并重放、登录过期跳转）
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建 Axios 实例
// baseURL 默认为相对路径：开发走 vite 代理（/api → 8000），生产走同域反代；
// 如需直连其他地址，通过 .env 的 VITE_API_BASE_URL 覆盖
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器：自动携带 Token + FormData 兼容
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // FormData 必须清除 Content-Type，让浏览器自动设置 multipart/form-data; boundary=...
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

/* ---------- token 自动刷新 ---------- */

// 并发 401 共享同一次刷新请求
let refreshingPromise = null
// 登录过期跳转防抖（并发多个 401 只跳一次）
let handled401 = false

/**
 * 使用 refresh_token 换取新的 access_token（走裸 axios，避免循环依赖）
 * @returns {Promise<object|null>} 刷新成功返回响应数据，失败抛出异常
 */
function refreshAccessToken() {
  const refresh = localStorage.getItem('refresh_token')
  if (!refresh) return Promise.reject(new Error('no refresh token'))

  if (!refreshingPromise) {
    refreshingPromise = axios
      .post(`${request.defaults.baseURL}/auth/refresh/`, { refresh })
      .then((res) => {
        const data = res.data
        if (data?.access) localStorage.setItem('access_token', data.access)
        // ROTATE_REFRESH_TOKENS=True：后端会同时返回新 refresh，需更新
        if (data?.refresh) localStorage.setItem('refresh_token', data.refresh)
        return data
      })
      .finally(() => {
        refreshingPromise = null
      })
  }
  return refreshingPromise
}

/** 清除登录态并跳转登录页（携带 redirect，防抖） */
function clearAuthAndGoLogin() {
  if (handled401) return
  handled401 = true
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user_info')
  // 同步清理 Pinia store，避免导航栏仍显示已登录、角色判断失真
  // （动态引入避免 request ↔ store 循环依赖）
  import('@/stores/user')
    .then(({ useUserStore }) => {
      useUserStore().clearLocalAuth()
    })
    .catch(() => {})
  ElMessage.error('登录已过期，请重新登录')
  const current = router.currentRoute.value
  // 已在登录页则不重复跳转
  if (current.name !== 'Login') {
    router.push({ name: 'Login', query: { redirect: current.fullPath } })
  }
  setTimeout(() => {
    handled401 = false
  }, 500)
}

/* ---------- 响应拦截器 ---------- */

request.interceptors.response.use(
  (response) => {
    return response.data
  },
  async (error) => {
    const { response } = error

    if (!response) {
      ElMessage.error('网络连接失败，请检查网络')
      return Promise.reject(error)
    }

    const { status, data, config } = response
    const message = data?.message || '请求失败'
    const url = config?.url || ''
    // 登录/刷新接口自身的 401 不触发自动刷新与跳转
    const isLoginRequest = /\/auth\/login\/?$/.test(url)
    const isRefreshRequest = /\/auth\/refresh\/?$/.test(url)

    if (status === 401 && !isLoginRequest && !isRefreshRequest) {
      // 未登录访问受限资源：仅提示，不跳转
      if (!localStorage.getItem('access_token')) {
        ElMessage.error(data?.message || '请先登录')
        return Promise.reject(error)
      }
      // 已有 token：静默刷新并重放原请求；重放仍 401 则判定会话失效
      try {
        // _retry 检查必须在刷新之前：重放请求再失败时不再发起第二次无效刷新
        if (config._retry) {
          throw new Error('refresh retry failed')
        }
        await refreshAccessToken()
        const retryConfig = { ...config, _retry: true }
        retryConfig.headers = {
          ...(config.headers || {}),
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        }
        return request(retryConfig)
      } catch (e) {
        clearAuthAndGoLogin()
        return Promise.reject(error)
      }
    }

    if (status === 401 && isLoginRequest) {
      // 登录接口 401 表示用户名/密码错误，透传后端 message
      ElMessage.error(message)
      return Promise.reject(error)
    }

    // 403/404 已有 message 时直接透传；无 message 时给语义化默认提示
    if (status === 403) {
      ElMessage.error(data?.message || '权限不足')
    } else if (status === 404) {
      ElMessage.error(data?.message || '请求的资源不存在')
    } else if (status >= 500) {
      ElMessage.error('服务器错误，请稍后重试')
    } else if (!isRefreshRequest) {
      ElMessage.error(message)
    }

    return Promise.reject(error)
  }
)

export default request
