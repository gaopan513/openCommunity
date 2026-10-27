/* eslint-disable no-console */
/**
 * 统一埋点与错误上报工具
 *
 * 基于 uni-app 跨端 API：wx 端走微信实时日志（运维中心可按用户检索），
 * 其他端（H5 等）回退 console，保证跨端不报错。
 *
 * 用法：
 *   track('post_publish', { post_type: 'chat' })   // 业务埋点
 *   reportError(err, 'context')                    // 非致命错误上报
 *   logWarn('wechat-login 失败', detail)           // 告警记录
 */

// 懒获取实时日志管理器（仅 wx 端存在）
let _rtLog = null
function rtLog() {
  if (_rtLog === null) {
    _rtLog = typeof wx !== 'undefined' && wx.getRealtimeLogManager ? wx.getRealtimeLogManager() : null
  }
  return _rtLog
}

function fmt(v) {
  if (typeof v === 'string') return v
  try {
    return JSON.stringify(v)
  } catch {
    return String(v)
  }
}

/**
 * 业务事件埋点（登录/发布/下单/评价等关键节点）
 * @param {string} event - 事件名（小写下划线，如 'post_publish'）
 * @param {Object} [payload] - 附加参数（不含 PII，避免日志泄露手机号/地址等）
 */
export function track(event, payload = {}) {
  const line = `[track] ${event}${Object.keys(payload).length ? ' ' + fmt(payload) : ''}`
  const log = rtLog()
  if (log && typeof log.info === 'function') log.info(line)
  else if (typeof console !== 'undefined') console.log(line)
}

/**
 * 非致命错误上报（带上下文，便于定位）
 * @param {Error|string} err
 * @param {string} [context] - 出现的业务上下文，如 'loadPost'
 */
export function reportError(err, context = '') {
  const detail = err instanceof Error ? err.message : fmt(err)
  const line = context ? `[error] ${context}: ${detail}` : `[error] ${detail}`
  const log = rtLog()
  if (log && typeof log.error === 'function') log.error(line)
  else if (typeof console !== 'undefined') console.error(line)
}

/**
 * 告警记录（弱网、权限被拒等非致命但需留痕的场景）
 * @param {string} message
 * @param {*} [detail]
 */
export function logWarn(message, detail) {
  const line = detail !== undefined ? `[warn] ${message} ${fmt(detail)}` : `[warn] ${message}`
  const log = rtLog()
  if (log && typeof log.warn === 'function') log.warn(line)
  else if (typeof console !== 'undefined') console.warn(line)
}
