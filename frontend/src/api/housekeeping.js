/**
 * 家政服务模块 API
 */
import request from '@/utils/request'

/** 获取服务分类 */
export function getServiceCategories() {
  return request.get('/housekeeping/categories/')
}

/** 获取服务商列表 */
export function getProviders(params) {
  return request.get('/housekeeping/providers/', { params })
}

/** 获取服务商详情 */
export function getProvider(id) {
  return request.get(`/housekeeping/providers/${id}/`)
}

/** 服务商入驻申请 */
export function applyProvider(data) {
  return request.post('/housekeeping/providers/apply/', data)
}

/** 管理员审核服务商（action: approve / reject） */
export function auditProvider(id, data) {
  return request.put(`/housekeeping/providers/${id}/audit/`, data)
}

/** 提交预约 */
export function createBooking(data) {
  return request.post('/housekeeping/bookings/', data)
}

/** 获取我的预约 */
export function getBookings(params) {
  return request.get('/housekeeping/bookings/', { params })
}

/** 更新预约信息（仅 pending 可通过 PUT 修改） */
export function updateBooking(id, data) {
  return request.put(`/housekeeping/bookings/${id}/`, data)
}

/** 更新预约状态 */
export function updateBookingStatus(id, status) {
  return request.put(`/housekeeping/bookings/${id}/status/`, { status })
}

/** 服务评价 */
export function addBookingReview(id, data) {
  return request.post(`/housekeeping/bookings/${id}/review/`, data)
}
