/**
 * 用户登录态工具
 *
 * 写操作前的统一拦截：未登录时弹窗引导去登录页。
 * 游客可浏览所有公开内容，发布/预约/评价等写操作要求登录。
 */
import { useUserStore } from '@/stores/user'

/**
 * 校验登录态，未登录弹窗询问是否前往登录页
 * @returns {boolean} true=已登录可继续，false=已触发跳转提示，调用方直接 return
 */
export function requireLogin() {
  const userStore = useUserStore()
  if (userStore.isLoggedIn) return true

  uni.showModal({
    title: '需要登录',
    content: '请先使用微信授权登录后再进行此操作',
    confirmText: '去登录',
    success: (res) => {
      if (res.confirm) {
        // 携带当前页路径与 query，登录成功后回跳原页面（与 401 踢出路径行为一致）
        const pages = getCurrentPages()
        const current = pages[pages.length - 1]
        const opts = current ? current.options || current.$page?.options || {} : {}
        const qs = Object.entries(opts)
          .filter(([, v]) => v !== undefined && v !== null && v !== '')
          .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
          .join('&')
        const currentPath = (current ? '/' + current.route : '/pages/home/index') + (qs ? `?${qs}` : '')
        if (currentPath === '/pages/auth/login') return
        uni.navigateTo({ url: `/pages/auth/login?redirect=${encodeURIComponent(currentPath)}` })
      }
    },
  })
  return false
}
