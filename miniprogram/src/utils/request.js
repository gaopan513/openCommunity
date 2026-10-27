/**
 * 小程序统一请求封装
 *
 * 与 frontend/src/utils/request.js 的 axios 实例语义 1:1 对齐：
 * - 自动携带 Bearer Token（uni Storage 替代 localStorage）
 * - 统一错误提示（uni.showToast 替代 ElMessage）
 * - 401 静默刷新并重放一次，刷新失败清登录态并回登录页
 * - 对外暴露类 axios 签名（get/post/put/patch/delete），
 *   使 api/*.js 可从 Web 端近乎原样平移
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
// 生产构建漏配 VITE_API_BASE_URL 时静默回退到本机明文地址，必须尽早暴露
if (import.meta.env.PROD && !import.meta.env.VITE_API_BASE_URL) {
  console.error('[request] 生产环境未配置 VITE_API_BASE_URL，请求将指向不可用的本机回退地址')
}

// 并发 401 共享同一次刷新请求；登录过期跳转防抖
let refreshingPromise = null
let handled401 = false

/** 将查询参数对象拼接到 URL（跳过空值），等价于 axios 的 params */
function buildQuery(url, params) {
  if (!params) return url
  const qs = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join('&')
  return qs ? `${url}${url.includes('?') ? '&' : '?'}${qs}` : url
}

/** 底层 uni.request Promise 化（不注入 token、不做拦截） */
function rawRequest({ url, method = 'GET', data, header = {} }) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: url.startsWith('http') ? url : BASE_URL + url,
      method,
      data,
      header,
      timeout: 15000,
      success: resolve,
      fail: reject,
    })
  })
}

/** 使用 refresh_token 换取新 token（该端点为 SimpleJWT 原生视图，返回裸 JSON，无 code 信封） */
function refreshAccessToken() {
  const refresh = uni.getStorageSync('refresh_token')
  if (!refresh) return Promise.reject(new Error('no refresh token'))

  if (!refreshingPromise) {
    refreshingPromise = rawRequest({
      url: '/auth/refresh/',
      method: 'POST',
      data: { refresh },
    })
      .then((res) => {
        if (res.statusCode >= 300) throw new Error('refresh failed')
        const data = res.data || {}
        if (data.access) uni.setStorageSync('access_token', data.access)
        // ROTATE_REFRESH_TOKENS=True：后端会同时返回新 refresh，需更新
        if (data.refresh) uni.setStorageSync('refresh_token', data.refresh)
        return data
      })
      .finally(() => {
        refreshingPromise = null
      })
  }
  return refreshingPromise
}

/** 清除登录态并回到登录页（清 Storage 三键 + 同步清理 Pinia store，防抖） */
function clearAuthAndGoLogin() {
  if (handled401) return
  handled401 = true
  ;['user_info', 'access_token', 'refresh_token'].forEach((k) => uni.removeStorageSync(k))
  // 动态引入避免循环依赖，语义同 Web 端 clearLocalAuth
  import('@/stores/user').then(({ useUserStore }) => useUserStore().clearLocalAuth()).catch(() => {})
  uni.showToast({ title: '登录已过期，请重新登录', icon: 'none' })

  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  // 携带页面 query（详情页的 id 等），否则踢回后详情页拿不到参数
  const opts = current ? current.options || current.$page?.options || {} : {}
  const qs = Object.entries(opts)
    .filter(([, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join('&')
  const currentPath = (current ? '/' + current.route : '/pages/home/index') + (qs ? `?${qs}` : '')
  // 先让 toast 展示片刻再跳转，避免 reLaunch 动画立即吞掉提示
  setTimeout(() => {
    handled401 = false
    if (currentPath === '/pages/auth/login') return
    uni.reLaunch({
      url: `/pages/auth/login?redirect=${encodeURIComponent(currentPath)}`,
    })
  }, 400)
}

/** toast 提示工具（供本模块内部使用） */
function toast(title) {
  if (!title) return
  uni.showToast({ title, icon: 'none' })
}

/**
 * 核心请求函数
 * @param {Object} options - { url, method, data, params, header, retry }
 * @returns {Promise<object>} 成功时 resolve 后端信封 {code,message,data} 或裸数据
 */
function request(options) {
  const { url, method = 'GET', data, params, header = {}, retry = false } = options
  const fullUrl = buildQuery(url, params)
  const token = uni.getStorageSync('access_token')
  if (token) header.Authorization = `Bearer ${token}`

  return rawRequest({ url: fullUrl, method, data, header }).then(
    (res) => {
      const statusCode = res.statusCode
      if (statusCode >= 200 && statusCode < 300) return res.data

      const body = res.data || {}
      const message = body.message || '请求失败'
      const errObj = Object.assign(new Error(message), { statusCode, data: body })
      const isLoginReq = /\/auth\/(login|wechat-login|register)\/?$/.test(url)
      const isRefreshReq = /\/auth\/refresh\/?$/.test(url)

      if (statusCode === 401) {
        if (isLoginReq || isRefreshReq) {
          // 登录/刷新接口自身的 401 表示凭证无效，透传后端 message
          toast(message)
          throw errObj
        }
        if (!token) {
          toast(body.message || '请先登录')
          throw errObj
        }
        // 已有 token：静默刷新并重放原请求一次；重放仍 401 判定会话失效
        if (retry) {
          clearAuthAndGoLogin()
          throw errObj
        }
        return refreshAccessToken()
          .then(() => request({ ...options, retry: true }))
          .catch((e) => {
            // 网络错误（uni.request fail 带 errMsg）不判定会话失效，弱网下避免误踢登录
            if (e && e.errMsg) {
              toast('网络连接失败，请检查网络')
              throw errObj
            }
            if (e && e.statusCode) throw e
            clearAuthAndGoLogin()
            throw errObj
          })
      }

      if (statusCode === 403) {
        toast(body.message || '权限不足')
      } else if (statusCode === 404) {
        toast(body.message || '请求的资源不存在')
      } else if (statusCode >= 500) {
        toast('服务器错误，请稍后重试')
      } else if (!isRefreshReq) {
        toast(message)
      }
      throw errObj
    },
    () => {
      // fail 分支：网络不通/超时（带 errMsg 供上层区分网络错误与会话失效）
      toast('网络连接失败，请检查网络')
      const err = new Error('network error')
      err.errMsg = 'network error'
      throw err
    }
  )
}

/** 类 axios 出口：api/*.js 直接平移 */
export default {
  get: (url, config = {}) => request({ url, method: 'GET', params: config.params }),
  post: (url, data, config = {}) => request({ url, method: 'POST', data, params: config.params }),
  put: (url, data, config = {}) => request({ url, method: 'PUT', data, params: config.params }),
  patch: (url, data, config = {}) => request({ url, method: 'PATCH', data, params: config.params }),
  delete: (url, config = {}) => request({ url, method: 'DELETE', params: config.params }),
}

export { BASE_URL, rawRequest, toast, refreshAccessToken, clearAuthAndGoLogin }
