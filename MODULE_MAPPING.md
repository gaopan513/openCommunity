# MODULE_MAPPING.md

## 模块代码映射表

### 公共工具（common）

| 代码文件路径 | 所属模块 | 功能描述 |
|---|---|---|
| backend/common/__init__.py | 公共工具 | 模块初始化 |
| backend/common/permissions.py | 公共工具 | 自定义 DRF 权限类（IsOwnerOrReadOnly, IsAdminUser, IsMerchantUser, IsOwnerOrAdmin），被所有业务模块依赖 |
| backend/common/pagination.py | 公共工具 | 统一分页器配置（StandardPagination, SmallPagination），被所有列表接口依赖 |
| backend/common/exceptions.py | 公共工具 | 自定义业务异常 + 全局异常处理器，被 settings.py 引用 |
| backend/common/response.py | 公共工具 | 统一响应格式封装（success_response, error_response 等），被所有视图依赖 |
| backend/common/validators.py | 公共工具 | 通用验证器（手机号、图片大小/格式、评分），被 users/merchants/housekeeping 依赖 |
| backend/common/utils.py | 公共工具 | 工具函数（文件上传路径生成、平均评分计算），被所有含图片上传的模块依赖 |

### 项目配置（config）

| 代码文件路径 | 所属模块 | 功能描述 |
|---|---|---|
| backend/config/settings.py | 项目配置 | Django 全局配置：DRF、JWT、CORS、应用注册、数据库 |
| backend/config/urls.py | 项目配置 | 主路由配置，挂载所有模块 API 到 /api/v1/ |
| backend/config/wsgi.py | 项目配置 | WSGI 入口 |
| backend/config/asgi.py | 项目配置 | ASGI 入口 |
| backend/manage.py | 项目配置 | Django 管理命令入口 |

### 用户认证（users）

| 代码文件路径 | 所属模块 | 功能描述 |
|---|---|---|
| backend/apps/users/models.py | 用户认证 | User 扩展模型：角色（resident/merchant/admin）、手机号、头像、小区信息 |
| backend/apps/users/serializers.py | 用户认证 | 注册/资料序列化器（RegisterSerializer, UserProfileSerializer, UserSimpleSerializer） |
| backend/apps/users/views.py | 用户认证 | 注册、登录（JWT）、Token刷新、个人资料CRUD、修改密码接口 |
| backend/apps/users/urls.py | 用户认证 | 用户资料路由（/api/v1/users/） |
| backend/apps/users/urls_auth.py | 用户认证 | 认证路由（/api/v1/auth/：register, login, refresh） |
| backend/apps/users/admin.py | 用户认证 | Django Admin 用户管理配置 |
| backend/apps/users/tests.py | 用户认证 | 21 个单元测试：注册、登录、权限、资料、密码 |

### 自由发言（discussion）

| 代码文件路径 | 所属模块 | 功能描述 |
|---|---|---|
| backend/apps/discussion/models.py | 自由发言 | Post、PostImage、Comment（楼中楼）、PostLike 模型 |
| backend/apps/discussion/serializers.py | 自由发言 | 帖子列表/详情/创建序列化器、评论序列化器 |
| backend/apps/discussion/views.py | 自由发言 | PostViewSet：CRUD、点赞、评论、置顶/加精 |
| backend/apps/discussion/urls.py | 自由发言 | Router 注册 /api/v1/posts/ |
| backend/apps/discussion/admin.py | 自由发言 | 帖子/评论后台管理 |
| backend/apps/discussion/tests.py | 自由发言 | 18 个单元测试：发帖、评论、点赞、权限、管理操作 |

### 经验问答（qa）

| 代码文件路径 | 所属模块 | 功能描述 |
|---|---|---|
| backend/apps/qa/models.py | 经验问答 | Question、Answer、QuestionTag、AnswerLike、QuestionLike 模型 |
| backend/apps/qa/serializers.py | 经验问答 | 问题列表/详情/创建、回答序列化器 |
| backend/apps/qa/views.py | 经验问答 | QuestionViewSet：CRUD、回答、采纳、点赞；AnswerViewSet：点赞 |
| backend/apps/qa/urls.py | 经验问答 | Router 注册 /api/v1/questions/ |
| backend/apps/qa/admin.py | 经验问答 | 问题/回答/标签后台管理 |
| backend/apps/qa/tests.py | 经验问答 | 10 个单元测试：提问、回答、采纳、点赞、权限 |

### 二手市场（secondhand）

| 代码文件路径 | 所属模块 | 功能描述 |
|---|---|---|
| backend/apps/secondhand/models.py | 二手市场 | Product、ProductImage、ProductComment、ProductCategory 模型 |
| backend/apps/secondhand/serializers.py | 二手市场 | 商品列表/详情/创建、分类、评论序列化器 |
| backend/apps/secondhand/views.py | 二手市场 | ProductViewSet：CRUD、状态流转、留言；CategoryViewSet |
| backend/apps/secondhand/urls.py | 二手市场 | Router 注册 /api/v1/products/, /api/v1/product-categories/ |
| backend/apps/secondhand/admin.py | 二手市场 | 商品/分类/评论后台管理 |
| backend/apps/secondhand/tests.py | 二手市场 | 33 个单元测试：发布、筛选、状态流转、留言、权限 |

### 商家板块（merchants）

| 代码文件路径 | 所属模块 | 功能描述 |
|---|---|---|
| backend/apps/merchants/models.py | 商家板块 | Merchant、MerchantImage、MerchantCategory、Activity、MerchantReview 模型 |
| backend/apps/merchants/serializers.py | 商家板块 | 商家列表/详情/申请、活动、评价序列化器 |
| backend/apps/merchants/views.py | 商家板块 | MerchantViewSet：入驻申请、审核、活动管理、评价管理；CategoryViewSet |
| backend/apps/merchants/urls.py | 商家板块 | Router 注册 /api/v1/merchants/, /api/v1/merchant-categories/ |
| backend/apps/merchants/admin.py | 商家板块 | 商家/分类/活动/评价后台管理 |
| backend/apps/merchants/tests.py | 商家板块 | 9 个单元测试：入驻、审核、活动、评价、回复 |

### 家政服务（housekeeping）

| 代码文件路径 | 所属模块 | 功能描述 |
|---|---|---|
| backend/apps/housekeeping/models.py | 家政服务 | ServiceProvider、ServiceCategory、ServiceItem、Booking、ServiceReview 模型 |
| backend/apps/housekeeping/serializers.py | 家政服务 | 服务商/服务项目/预约/评价序列化器 |
| backend/apps/housekeeping/views.py | 家政服务 | ProviderViewSet：入驻、审核；BookingViewSet：预约、状态流转、评价；CategoryViewSet |
| backend/apps/housekeeping/urls.py | 家政服务 | Router 注册 /api/v1/housekeeping/ 下三个子路由 |
| backend/apps/housekeeping/admin.py | 家政服务 | 服务商/分类/预约/评价后台管理 |
| backend/apps/housekeeping/tests.py | 家政服务 | 36 个单元测试：入驻、预约、状态流转、评价、权限 |

### 系统管理（admin_system）

| 代码文件路径 | 所属模块 | 功能描述 |
|---|---|---|
| backend/apps/admin_system/models.py | 系统管理 | Announcement（公告）、Report（举报）模型 |
| backend/apps/admin_system/serializers.py | 系统管理 | 公告/举报序列化器 |
| backend/apps/admin_system/views.py | 系统管理 | 公告CRUD、举报处理、基础数据统计接口 |
| backend/apps/admin_system/urls.py | 系统管理 | Router 注册 /api/v1/announcements/, /api/v1/admin/ |
| backend/apps/admin_system/admin.py | 系统管理 | 公告/举报后台管理 |
| backend/apps/admin_system/tests.py | 系统管理 | 10 个单元测试：公告、举报、统计、权限 |

### 前端（frontend）

| 代码文件路径 | 所属模块 | 功能描述 |
|---|---|---|
| frontend/src/main.js | 前端入口 | Vue 3 + Element Plus + Router + Pinia 初始化 |
| frontend/src/App.vue | 前端布局 | 全局导航栏 + 路由视图 + 底部 |
| frontend/src/router/index.js | 前端路由 | 所有页面路由定义 + 导航守卫 |
| frontend/src/stores/user.js | 状态管理 | 用户登录状态、Token、角色管理（Pinia） |
| frontend/src/utils/request.js | HTTP 工具 | Axios 实例封装：Token 携带、错误拦截 |
| frontend/src/styles/community.css | 设计系统 | 社区暖色调设计变量与通用组件类（oc-page/oc-card/oc-tag 等） |
| frontend/src/api/auth.js | API 层 | 认证相关 API 调用（注册、登录、资料） |
| frontend/src/api/discussion.js | API 层 | 自由发言 API（帖子 CRUD、点赞、评论、加精） |
| frontend/src/api/qa.js | API 层 | 经验问答 API（问题 CRUD、回答、采纳、点赞） |
| frontend/src/api/secondhand.js | API 层 | 二手市场 API（商品 CRUD、状态流转、留言、分类） |
| frontend/src/api/merchants.js | API 层 | 商家板块 API（商家列表/详情、入驻申请、审核、活动、评价及回复） |
| frontend/src/api/housekeeping.js | API 层 | 家政服务 API（分类、服务商、入驻申请、审核、预约、状态流转、评价） |
| frontend/src/api/admin.js | API 层 | 系统管理 API（公告、统计、举报） |
| frontend/src/views/home/HomeView.vue | 首页 | 板块入口展示 |
| frontend/src/views/auth/LoginView.vue | 用户认证 | 登录页面 |
| frontend/src/views/auth/RegisterView.vue | 用户认证 | 注册页面 |
| frontend/src/views/auth/ProfileView.vue | 用户认证 | 个人中心（资料编辑、密码修改） |
| frontend/src/views/discussion/PostList.vue | 自由发言 | 帖子列表：类型页签、搜索、排序、帖子卡片、分页 |
| frontend/src/views/discussion/PostDetail.vue | 自由发言 | 帖子详情：正文、图集、点赞、楼中楼评论、管理操作 |
| frontend/src/components/discussion/PostCreateDialog.vue | 自由发言 | 发帖对话框（支持最多 9 张图片上传） |
| frontend/src/views/qa/QuestionList.vue | 经验问答 | 问题列表：状态页签、标签、回答数徽标 |
| frontend/src/views/qa/QuestionDetail.vue | 经验问答 | 问题详情：回答列表、采纳最佳答案、写回答 |
| frontend/src/components/qa/QuestionCreateDialog.vue | 经验问答 | 提问对话框（多选标签、支持自建标签） |
| frontend/src/views/secondhand/ProductList.vue | 二手市场 | 商品列表：分类筛选、价格排序、商品网格 |
| frontend/src/views/secondhand/ProductDetail.vue | 二手市场 | 商品详情：图集轮播、卖家信息、状态管理、买家留言 |
| frontend/src/components/secondhand/ProductCreateDialog.vue | 二手市场 | 发布闲置对话框（价格、成色、分类、图片） |
| frontend/src/views/merchant/MerchantList.vue | 商家板块 | 商家列表：分类筛选、搜索、店铺卡片（评分/评价数）、入驻入口 |
| frontend/src/views/merchant/MerchantDetail.vue | 商家板块 | 商家详情：店招、活动列表与发布、评价与商家回复、管理员审核 |
| frontend/src/components/merchant/MerchantApplyDialog.vue | 商家板块 | 商家入驻申请对话框（含营业执照上传） |
| frontend/src/views/housekeeping/ServiceList.vue | 家政服务 | 服务商列表：分类筛选（slug）、搜索、我的预约入口、入驻入口 |
| frontend/src/views/housekeeping/ServiceDetail.vue | 家政服务 | 服务商详情：服务项目与预约下单、邻居评价、管理员审核 |
| frontend/src/components/housekeeping/ProviderApplyDialog.vue | 家政服务 | 服务商入驻申请对话框（含资质图片上传） |
| frontend/src/components/housekeeping/BookingDialog.vue | 家政服务 | 预约下单对话框（日期、时段选择、备注） |
| frontend/src/components/housekeeping/MyBookingsDrawer.vue | 家政服务 | 我的预约抽屉：状态筛选、订单状态推进（服务商）、服务评价（居民） |
| frontend/vite.config.js | 前端配置 | Vite 构建配置 + 开发代理 |
