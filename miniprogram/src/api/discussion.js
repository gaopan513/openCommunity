/**
 * 自由发言模块 API（自 frontend/src/api/discussion.js 平移）
 *
 * 发帖含图片时改走 uploadMultipart（wx.uploadFile 无法一次传多文件）。
 */
import request from '@/utils/request'
import { uploadMultipart } from '@/utils/upload'

/** 获取帖子列表 @param {Object} params - page/page_size/post_type/search/ordering */
export function getPosts(params) {
  return request.get('/posts/', { params })
}

/** 获取帖子详情 */
export function getPost(id) {
  return request.get(`/posts/${id}/`)
}

/**
 * 发布帖子（data.images 为本地临时路径数组时自动转 multipart 多文件提交）
 * @param {Object} data - { title, content, post_type, tags, images?: string[] }
 */
export function createPost(data) {
  const { images = [], ...fields } = data
  return uploadMultipart({ url: '/posts/', method: 'POST', fields, files: images })
}

/**
 * 编辑帖子（暂只支持文本字段；images 传入则全量替换）
 * @param {number|string} id
 * @param {Object} data - 文本字段 + 可选 images 本地路径数组
 */
export function updatePost(id, data) {
  const { images, ...textOnly } = data
  if (images && images.length) {
    return uploadMultipart({ url: `/posts/${id}/`, method: 'PATCH', fields: textOnly, files: images })
  }
  return request.patch(`/posts/${id}/`, textOnly)
}

/** 删除帖子 */
export function deletePost(id) {
  return request.delete(`/posts/${id}/`)
}

/** 点赞/取消点赞 */
export function likePost(id) {
  return request.post(`/posts/${id}/like/`)
}

/**
 * 发表评论（parent 为楼层评论 id 时回复楼中楼）
 * @param {number|string} id - 帖子 id
 * @param {Object} data - { content, parent? }
 */
export function addComment(id, data) {
  return request.post(`/posts/${id}/comments/`, data)
}
