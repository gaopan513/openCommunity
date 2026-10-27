/**
 * 商家板块模块 API（自 frontend/src/api/merchants.js 平移，仅保留居民端所需：
 * 列表/详情/活动浏览/评价浏览与发表/分类；入驻、店铺管理、审核留 Web 端）
 */
import request from '@/utils/request'

/** 获取商家列表 @param {Object} params - page/page_size/category/search */
export function getMerchants(params) {
  return request.get('/merchants/', { params })
}

/** 获取商家详情（含图片、活动、最近 5 条评价） */
export function getMerchant(id) {
  return request.get(`/merchants/${id}/`)
}

/** 获取商家活动 @param {Object} [params] - 分页参数 */
export function getMerchantActivities(id, params) {
  return request.get(`/merchants/${id}/activities/`, { params })
}

/** 获取商家评价 @param {Object} [params] - 分页参数 */
export function getMerchantReviews(id, params) {
  return request.get(`/merchants/${id}/reviews/`, { params })
}

/**
 * 发表商家评价
 * @param {number|string} id - 商家 id
 * @param {Object} data - { rating: 1~5, content }
 */
export function addMerchantReview(id, data) {
  return request.post(`/merchants/${id}/reviews/`, data)
}

/** 获取商家分类 */
export function getMerchantCategories() {
  return request.get('/merchant-categories/')
}
