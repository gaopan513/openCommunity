/**
 * 系统公告 API（自 frontend/src/api/admin.js 裁剪，居民端仅需公开公告列表；
 * 统计与举报管理属管理员职责，留 Web 管理后台）
 */
import request from '@/utils/request'

/** 获取公告列表（公开只读）@param {Object} [params] - page/page_size */
export function getAnnouncements(params) {
  return request.get('/announcements/', { params })
}
