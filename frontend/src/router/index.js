/**
 * 路由配置
 * 
 * 定义所有页面路由和导航守卫。
 */
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/home/HomeView.vue'),
    meta: { title: '首页' },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { title: '登录', guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: { title: '注册', guest: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/auth/ProfileView.vue'),
    meta: { title: '个人中心', requiresAuth: true },
  },
  // 自由发言
  {
    path: '/discussion',
    name: 'Discussion',
    component: () => import('@/views/discussion/PostList.vue'),
    meta: { title: '自由发言' },
  },
  {
    path: '/discussion/:id',
    name: 'PostDetail',
    component: () => import('@/views/discussion/PostDetail.vue'),
    meta: { title: '帖子详情' },
  },
  // 经验问答
  {
    path: '/qa',
    name: 'QA',
    component: () => import('@/views/qa/QuestionList.vue'),
    meta: { title: '经验问答' },
  },
  {
    path: '/qa/:id',
    name: 'QuestionDetail',
    component: () => import('@/views/qa/QuestionDetail.vue'),
    meta: { title: '问题详情' },
  },
  // 二手市场
  {
    path: '/secondhand',
    name: 'SecondHand',
    component: () => import('@/views/secondhand/ProductList.vue'),
    meta: { title: '二手市场' },
  },
  {
    path: '/secondhand/:id',
    name: 'ProductDetail',
    component: () => import('@/views/secondhand/ProductDetail.vue'),
    meta: { title: '商品详情' },
  },
  // 商家板块
  {
    path: '/merchants',
    name: 'Merchants',
    component: () => import('@/views/merchant/MerchantList.vue'),
    meta: { title: '周边商家' },
  },
  {
    path: '/merchants/:id',
    name: 'MerchantDetail',
    component: () => import('@/views/merchant/MerchantDetail.vue'),
    meta: { title: '商家详情' },
  },
  // 家政服务
  {
    path: '/housekeeping',
    name: 'Housekeeping',
    component: () => import('@/views/housekeeping/ServiceList.vue'),
    meta: { title: '家政服务' },
  },
  {
    path: '/housekeeping/:id',
    name: 'ServiceDetail',
    component: () => import('@/views/housekeeping/ServiceDetail.vue'),
    meta: { title: '服务详情' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 全局前置守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 社区论坛` : '社区论坛'
  
  const token = localStorage.getItem('access_token')
  
  // 需要登录的页面
  if (to.meta.requiresAuth && !token) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }
  
  // 已登录用户不能访问登录/注册页
  if (to.meta.guest && token) {
    next({ name: 'Home' })
    return
  }
  
  next()
})

export default router
