/**
 * 集中路由路径常量
 *
 * 收敛所有跨页跳转的硬编码路径，避免 magic string 散落各页面。
 * - 分包根前缀（PACKAGE_ROOT）统一在此维护，分包调整时仅改此处 + pages.json
 * - 需要 id/query 的路径提供函数式出口（如 qaDetail(id)）
 *
 * 注意：tabBar 页必须用 switchTab 跳转（uni-app 约束），tab 路径保持直写。
 */
/** 各个分包根前缀（对应 pages.json subPackages[].root） */
export const PACKAGE_ROOT = {
  posts: 'modules/posts',
  qa: 'modules/qa',
  products: 'modules/products',
  housekeeping: 'modules/housekeeping',
  merchants: 'modules/merchants',
  bookings: 'modules/bookings',
}

/** Tab 常驻页路径（主包，switchTab 跳转） */
export const TAB = {
  home: '/pages/home/index',
  posts: '/pages/posts/list',
  products: '/pages/products/list',
  services: '/pages/services/index',
  profile: '/pages/profile/index',
}

/** 主包非 tab 页 */
export const PAGE = {
  login: '/pages/auth/login',
}

/** 业务页面路径（含分包路由），函数式入口用于拼 query */
export const ROUTE = {
  // posts
  postDetail: (id) => `/${PACKAGE_ROOT.posts}/detail?id=${id}`,
  postCreate: () => `/${PACKAGE_ROOT.posts}/create`,
  // qa
  qaList: () => `/${PACKAGE_ROOT.qa}/list`,
  qaDetail: (id) => `/${PACKAGE_ROOT.qa}/detail?id=${id}`,
  qaCreate: () => `/${PACKAGE_ROOT.qa}/create`,
  // products
  productDetail: (id) => `/${PACKAGE_ROOT.products}/detail?id=${id}`,
  productMine: () => `/${PACKAGE_ROOT.products}/mine`,
  productCreateEdit: (id) =>
    id ? `/${PACKAGE_ROOT.products}/create-edit?id=${id}` : `/${PACKAGE_ROOT.products}/create-edit`,
  // housekeeping / merchants
  housekeepingDetail: (id) => `/${PACKAGE_ROOT.housekeeping}/detail?id=${id}`,
  merchantDetail: (id) => `/${PACKAGE_ROOT.merchants}/detail?id=${id}`,
  // bookings
  bookingsMy: () => `/${PACKAGE_ROOT.bookings}/my`,
}
