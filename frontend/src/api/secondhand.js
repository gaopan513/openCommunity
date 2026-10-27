/**
 * 二手市场模块 API
 */
import request from '@/utils/request'

/** 获取商品列表 */
export function getProducts(params) {
  return request.get('/products/', { params })
}

/** 获取当前登录用户发布的商品（后端 ?mine=1 过滤） */
export function getMyProducts(params) {
  return request.get('/products/', { params: { ...params, mine: 1 } })
}

/** 获取商品详情 */
export function getProduct(id) {
  return request.get(`/products/${id}/`)
}

/** 发布商品（FormData，支持多图） */
export function createProduct(formData) {
  return request.post('/products/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/** 编辑商品 */
export function updateProduct(id, data) {
  return request.patch(`/products/${id}/`, data)
}

/** 删除商品 */
export function deleteProduct(id) {
  return request.delete(`/products/${id}/`)
}

/** 变更商品状态 */
export function changeProductStatus(id, status) {
  return request.put(`/products/${id}/status/`, { status })
}

/** 发表留言 */
export function addProductComment(id, data) {
  return request.post(`/products/${id}/comments/`, data)
}

/** 获取商品分类 */
export function getProductCategories() {
  return request.get('/product-categories/')
}
