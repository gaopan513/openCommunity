/**
 * 自由发言模块 API
 */
import request from '@/utils/request'

/** 获取帖子列表 */
export function getPosts(params) {
  return request.get('/posts/', { params })
}

/** 获取帖子详情 */
export function getPost(id) {
  return request.get(`/posts/${id}/`)
}

/** 发布帖子（FormData，支持图片） */
export function createPost(formData) {
  return request.post('/posts/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/** 编辑帖子 */
export function updatePost(id, data) {
  return request.patch(`/posts/${id}/`, data)
}

/** 删除帖子 */
export function deletePost(id) {
  return request.delete(`/posts/${id}/`)
}

/** 点赞/取消点赞 */
export function likePost(id) {
  return request.post(`/posts/${id}/like/`)
}

/** 发表评论 */
export function addComment(id, data) {
  return request.post(`/posts/${id}/comments/`, data)
}

/** 置顶/加精（管理员） */
export function featurePost(id, data) {
  return request.put(`/posts/${id}/feature/`, data)
}
