/**
 * 家政服务模块 API（自 frontend/src/api/housekeeping.js 平移，仅保留居民端所需：
 * 分类/服务商浏览、预约创建、我的预约查询与状态操作、服务评价；
 * 服务商申请与审核、服务商侧订单流转留 Web 端）
 */
import request from '@/utils/request'

/** 获取服务分类 */
export function getServiceCategories() {
  return request.get('/housekeeping/categories/')
}

/** 获取服务商列表 @param {Object} [params] - page/page_size/category(slug)/search */
export function getProviders(params) {
  return request.get('/housekeeping/providers/', { params })
}

/** 获取服务商详情（含 services 与 recent_reviews） */
export function getProvider(id) {
  return request.get(`/housekeeping/providers/${id}/`)
}

/**
 * 提交预约
 * @param {Object} data - { service_item, preferred_date 'YYYY-MM-DD', preferred_time 'HH:mm', remark }
 */
export function createBooking(data) {
  return request.post('/housekeeping/bookings/', data)
}

/** 获取我的预约 @param {Object} [params] - page/page_size/status */
export function getBookings(params) {
  return request.get('/housekeeping/bookings/', { params })
}

/**
 * 更新预约（仅 pending 可通过 PUT 修改预约信息）
 * @param {Object} data - { preferred_date?, preferred_time?, remark? }
 */
export function updateBooking(id, data) {
  return request.put(`/housekeeping/bookings/${id}/`, data)
}

/**
 * 更新预约状态（居民端合法动作：pending/confirmed → cancelled 取消）
 * @param {string} status
 */
export function updateBookingStatus(id, status) {
  return request.put(`/housekeeping/bookings/${id}/status/`, { status })
}

/** 服务评价（completed 后）@param {Object} data - { rating: 1~5, content } */
export function addBookingReview(id, data) {
  return request.post(`/housekeeping/bookings/${id}/review/`, data)
}
