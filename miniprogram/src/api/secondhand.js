/**
 * 二手市场模块 API（自 frontend/src/api/secondhand.js 平移）
 *
 * 发布/编辑含图片时改走 uploadMultipart；编辑传 images 为全量替换语义（≤9 张）。
 */
import request from '@/utils/request'
import { uploadMultipart } from '@/utils/upload'

/** 获取商品列表 @param {Object} params - page/page_size/category/status/condition/search/ordering */
export function getProducts(params) {
  return request.get('/products/', { params })
}

/** 获取当前登录用户发布的商品（后端 ?mine=1 过滤） @param {Object} params - page/page_size */
export function getMyProducts(params) {
  return request.get('/products/', { params: { ...params, mine: 1 } })
}

/** 获取商品详情 */
export function getProduct(id) {
  return request.get(`/products/${id}/`)
}

/**
 * 发布商品
 * @param {Object} data - { title, description, price, condition, category, images: string[] }
 */
export function createProduct(data) {
  const { images = [], ...fields } = data
  return uploadMultipart({ url: '/products/', method: 'POST', fields, files: images })
}

/**
 * 编辑商品：不传 images 仅更新文本字段；传 images 则删旧建新全量替换
 * @param {number|string} id
 * @param {Object} data
 */
export function updateProduct(id, data) {
  const { images, ...textOnly } = data
  if (images && images.length) {
    return uploadMultipart({ url: `/products/${id}/`, method: 'PATCH', fields: textOnly, files: images })
  }
  return request.patch(`/products/${id}/`, textOnly)
}

/** 删除商品 */
export function deleteProduct(id) {
  return request.delete(`/products/${id}/`)
}

/** 变更商品状态（专用 action：on_sale/reserved/sold/off_shelf） */
export function changeProductStatus(id, status) {
  return request.put(`/products/${id}/status/`, { status })
}

/** 发表留言 @param {Object} data - { content } */
export function addProductComment(id, data) {
  return request.post(`/products/${id}/comments/`, data)
}

/** 获取商品分类 */
export function getProductCategories() {
  return request.get('/product-categories/')
}
