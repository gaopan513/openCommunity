/**
 * 认证相关 API
 * 
 * 提供注册、登录、资料管理等接口调用。
 * 注：token 自动刷新在 @/utils/request 内部实现（裸 axios），不暴露为 API 函数。
 */
import request from '@/utils/request'

/**
 * 用户注册
 * @param {Object} data - { username, password, role, phone, community_name }
 */
export function register(data) {
  return request.post('/auth/register/', data)
}

/**
 * 用户登录
 * @param {Object} data - { username, password }
 */
export function login(data) {
  return request.post('/auth/login/', data)
}

/**
 * 退出登录：通知后端拉黑 refresh token
 * @param {Object} data - { refresh }
 */
export function logout(data) {
  return request.post('/auth/logout/', data)
}

/**
 * 获取当前用户资料
 */
export function getProfile() {
  return request.get('/users/profile/')
}

/**
 * 更新个人资料
 * @param {Object} data - 资料字段
 */
export function updateProfile(data) {
  return request.put('/users/profile/', data)
}

/**
 * 修改密码
 * @param {Object} data - { old_password, new_password }
 */
export function changePassword(data) {
  return request.put('/users/password/', data)
}
