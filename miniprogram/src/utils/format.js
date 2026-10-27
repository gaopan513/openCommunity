/**
 * 展示层格式化工具
 */
import { BASE_URL } from '@/utils/request'

// 媒体文件挂在源站根路径（/media/...），从 API 地址推导源站 origin
const ORIGIN = BASE_URL.replace(/\/api\/v\d+\/?$/, '')

/**
 * 后端返回的图片字段是相对路径（如 /media/products/x.jpg），
 * 小程序 <image> 需要绝对地址才能加载
 */
export function mediaUrl(url) {
  if (!url) return ''
  return /^https?:\/\//.test(url) ? url : ORIGIN + url
}

/** "YYYY-MM-DD HH:mm:ss" → "MM-DD" */
export function shortDate(datetime) {
  return datetime ? datetime.slice(5, 10) : ''
}

/** "YYYY-MM-DD HH:mm:ss" → "YYYY-MM-DD HH:mm" */
export function dateTime(datetime) {
  return datetime ? datetime.slice(0, 16) : ''
}

/** 评分（0-5）转五角星字符串（如 4 → "★★★★☆"），用于列表/详情展示 */
export function renderStars(rating) {
  const n = Math.max(0, Math.min(5, Math.round(Number(rating) || 0)))
  return '★★★★★'.slice(0, n) + '☆☆☆☆☆'.slice(n)
}
