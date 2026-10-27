/**
 * 认证相关 API（自 frontend/src/api/auth.js 平移）
 *
 * 提供微信登录、登出、资料管理等接口调用。
 * 注：token 自动刷新在 @/utils/request 内部实现，不暴露为 API 函数。
 */
import request from '@/utils/request'

/**
 * 微信小程序静默登录
 * @param {Object} data - { code } wx.login 获取的临时凭证
 */
export function wechatLogin(data) {
  return request.post('/auth/wechat-login/', data)
}

/**
 * 本地测试登录（联调旁路）：无真实小程序 AppID/Secret 时用于本地登录测试。
 * 仅后端 DEBUG 阶段（/auth/debug-login/）可用，生产该接口返回 404。
 */
export function debugLogin(data) {
  return request.post('/auth/debug-login/', data)
}

/** 退出登录：通知后端拉黑 refresh token */
export function logout(data) {
  return request.post('/auth/logout/', data)
}

/** 获取当前用户资料 */
export function getProfile() {
  return request.get('/users/profile/')
}

/**
 * 更新个人资料
 * @param {Object} data - 资料字段 phone/community_name/address 等
 */
export function updateProfile(data) {
  return request.put('/users/profile/', data)
}
