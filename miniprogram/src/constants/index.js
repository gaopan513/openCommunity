/**
 * 全局业务常量汇总
 *
 * 统一收敛跨页面共享的「隐式契约」，避免 magic string 散落各处导致失配：
 * - EVENTS：页面间数据新鲜度通知的事件名（替代散落的 'community:changed' 字面量）
 *
 * 状态映射（BOOKING_STATUS_MAP 等）见 ./statusMaps.js，前端统一引用。
 */

/** 全局事件名 */
export const EVENTS = {
  /** 列表数据已变更（发帖/发布商品/评价/删除等），列表页 onShow 时据此自动重载 */
  LIST_CHANGED: 'list:changed',
}
