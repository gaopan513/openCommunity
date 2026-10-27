/**
 * 业务状态映射常量
 *
 * 收编自 Web 端散落在 MyBookingsDrawer / ServiceDetail / MerchantDetail /
 * ProductList / ProductDetail 五处的重复定义，小程序端统一引用。
 * 与后端模型 TextChoices 取值一一对应。
 */

/** 家政预约状态（housekeeping.Booking.Status） */
export const BOOKING_STATUS_MAP = {
  pending: { label: '待确认', color: '#ff7d00' },
  confirmed: { label: '已确认', color: '#165dff' },
  in_service: { label: '服务中', color: '#722ed1' },
  completed: { label: '已完成', color: '#00b42a' },
  reviewed: { label: '已评价', color: '#86909c' },
  rejected: { label: '已拒绝', color: '#f53f3f' },
  cancelled: { label: '已取消', color: '#86909c' },
}

/** 二手商品状态（secondhand.Product.Status） */
export const PRODUCT_STATUS_MAP = {
  on_sale: { label: '在售', color: '#00b42a' },
  reserved: { label: '已预订', color: '#ff7d00' },
  sold: { label: '已售出', color: '#86909c' },
  off_shelf: { label: '已下架', color: '#86909c' },
}

/** 商品成色（secondhand.Product.Condition） */
export const PRODUCT_CONDITION_MAP = {
  brand_new: { label: '全新' },
  like_new: { label: '九成新' },
  good: { label: '八成新' },
  fair: { label: '七成新及以下' },
}
/** 商品成色 picker 可选项 */
export const PRODUCT_CONDITION_OPTIONS = [
  { value: 'brand_new', label: '全新' },
  { value: 'like_new', label: '九成新' },
  { value: 'good', label: '八成新' },
  { value: 'fair', label: '七成新及以下' },
]

/** 商家/服务商入驻审核状态（merchants.Merchant / housekeeping.ServiceProvider） */
export const AUDIT_STATUS_MAP = {
  pending: { label: '待审核', color: '#ff7d00' },
  approved: { label: '已通过', color: '#00b42a' },
  rejected: { label: '未通过', color: '#f53f3f' },
}

/** 帖子类型（discussion.Post.PostType；notice 仅管理员可发） */
export const POST_TYPE_MAP = {
  chat: { label: '闲聊', color: '#165dff' },
  help: { label: '求助', color: '#f53f3f' },
  share: { label: '分享', color: '#00b42a' },
}
/** 发帖类型 picker（不含 notice：仅管理员可发公告） */
export const POST_TYPE_OPTIONS = [
  { value: 'chat', label: '闲聊' },
  { value: 'help', label: '求助' },
  { value: 'share', label: '分享' },
]
