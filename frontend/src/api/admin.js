/**
 * 系统管理模块 API
 */
import request from '@/utils/request'

/** 获取公告列表（公开） */
export function getAnnouncements(params) {
  return request.get('/announcements/', { params })
}

/** 获取统计数据（管理员） */
export function getStatistics() {
  return request.get('/admin/statistics/')
}

/** 提交举报 */
export function createReport(data) {
  return request.post('/admin/reports/', data)
}
