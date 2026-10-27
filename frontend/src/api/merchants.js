/**
 * 商家板块模块 API
 */
import request from '@/utils/request'

/** 获取商家列表 */
export function getMerchants(params) {
  return request.get('/merchants/', { params })
}

/** 获取商家详情 */
export function getMerchant(id) {
  return request.get(`/merchants/${id}/`)
}

/** 商家入驻申请 */
export function applyMerchant(data) {
  return request.post('/merchants/apply/', data)
}

/** 获取当前用户的店铺信息 */
export function getMyShop() {
  return request.get('/merchants/my_shop/')
}

/** 更新当前用户的店铺信息 */
export function updateMyShop(data) {
  return request.patch('/merchants/my_shop/', data)
}

/** 管理员审核商家（approved / rejected） */
export function auditMerchant(id, data) {
  return request.put(`/merchants/${id}/audit/`, data)
}

/** 获取商家活动 */
export function getMerchantActivities(id) {
  return request.get(`/merchants/${id}/activities/`)
}

/** 发布活动 */
export function createActivity(id, data) {
  return request.post(`/merchants/${id}/activities/`, data)
}

/** 更新活动 */
export function updateActivity(id, activityId, data) {
  return request.patch(`/merchants/${id}/activities/${activityId}/`, data)
}

/** 删除活动 */
export function deleteActivity(id, activityId) {
  return request.delete(`/merchants/${id}/activities/${activityId}/`)
}

/** 获取商家评价 */
export function getMerchantReviews(id) {
  return request.get(`/merchants/${id}/reviews/`)
}

/** 发表评价 */
export function addMerchantReview(id, data) {
  return request.post(`/merchants/${id}/reviews/`, data)
}

/** 商家回复评价 */
export function replyMerchantReview(id, reviewId, data) {
  return request.put(`/merchants/${id}/reviews/${reviewId}/reply/`, data)
}

/** 获取商家分类 */
export function getMerchantCategories() {
  return request.get('/merchant-categories/')
}
