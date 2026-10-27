# 模块分解说明

## 模块总览

| 序号 | 模块名 | 职责 | 依赖 | 开发顺序 |
|------|--------|------|------|----------|
| 1 | common | 公共组件：权限类、分页、异常处理、工具函数 | 无 | 第 1 个 |
| 2 | users | 用户认证与管理 | common | 第 2 个 |
| 3 | discussion | 自由发言板块 | common, users | 第 3 个 |
| 4 | qa | 经验问答板块 | common, users | 第 4 个 |
| 5 | secondhand | 二手市场板块 | common, users | 第 5 个 |
| 6 | merchants | 商家板块 | common, users | 第 6 个 |
| 7 | housekeeping | 家政服务板块 | common, users | 第 7 个 |
| 8 | admin_system | 系统管理扩展 | common, users, 所有业务模块 | 第 8 个 |

---

## 模块详细说明

### 1. common — 公共组件

**职责**：提供所有业务模块共享的基础设施代码。

**文件结构**：
```
backend/common/
├── __init__.py
├── permissions.py      # 自定义 DRF 权限类（IsOwner, IsAdmin, IsMerchant 等）
├── pagination.py       # 统一分页器配置
├── exceptions.py       # 自定义异常 + 全局异常处理器
├── response.py         # 统一响应格式封装
├── validators.py       # 通用验证器（手机号、图片大小等）
└── utils.py            # 工具函数（文件上传路径生成、状态标签等）
```

**对外接口**：
- `permissions.IsOwnerOrReadOnly` — 对象所有者或只读
- `permissions.IsAdminUser` — 管理员权限
- `permissions.IsMerchantUser` — 商家角色权限
- `pagination.StandardPagination` — 标准分页（20条/页）
- `response.success_response(data)` / `response.error_response(msg)`
- `exceptions.BusinessError` — 业务异常基类

---

### 2. users — 用户认证模块

**职责**：用户注册、登录、Token 管理、角色权限、个人资料。

**文件结构**：
```
backend/apps/users/
├── __init__.py
├── models.py           # User 扩展模型（角色、头像、小区信息）
├── serializers.py      # 注册/登录/资料序列化器
├── views.py            # 注册、登录、Token刷新、资料CRUD
├── urls.py             # /api/v1/auth/*, /api/v1/users/*
├── services.py         # 用户业务逻辑（创建用户、分配角色）
├── admin.py            # Django Admin 配置
└── tests.py            # 单元测试
```

**数据模型**：
- `User`（扩展 AbstractUser）：role（resident/merchant/admin）、phone、avatar、community_name、address

**API 端点**：
- `POST /api/v1/auth/register/` — 注册
- `POST /api/v1/auth/login/` — 登录（获取 JWT）
- `POST /api/v1/auth/refresh/` — 刷新 Token
- `GET/PUT /api/v1/users/profile/` — 个人资料
- `PUT /api/v1/users/password/` — 修改密码

**依赖**：common（权限类、响应格式）

---

### 3. discussion — 自由发言模块

**职责**：帖子发布、浏览、评论、点赞、管理操作。

**文件结构**：
```
backend/apps/discussion/
├── __init__.py
├── models.py           # Post, Comment, PostImage, PostLike
├── serializers.py      # 帖子/评论序列化器
├── views.py            # 帖子CRUD、评论、点赞、置顶/加精
├── urls.py             # /api/v1/posts/*
├── services.py         # 业务逻辑（热度计算、置顶逻辑）
├── admin.py
└── tests.py
```

**数据模型**：
- `Post`：title, content, author(FK→User), post_type(闲聊/求助/分享/公告), tags, is_top, is_featured, view_count, created_at
- `PostImage`：post(FK), image
- `Comment`：post(FK), author(FK), content, parent(FK→self, 楼中楼), created_at
- `PostLike`：post(FK), user(FK), unique_together

**API 端点**：
- `GET /api/v1/posts/` — 帖子列表（筛选：type, tag, ordering）
- `POST /api/v1/posts/` — 发布帖子
- `GET /api/v1/posts/{id}/` — 帖子详情
- `PUT/DELETE /api/v1/posts/{id}/` — 编辑/删除（作者或管理员）
- `POST /api/v1/posts/{id}/comments/` — 发表评论
- `POST /api/v1/posts/{id}/like/` — 点赞/取消
- `PUT /api/v1/posts/{id}/feature/` — 置顶/加精（管理员）

**依赖**：common, users

---

### 4. qa — 经验问答模块

**职责**：问题发布、回答、采纳最佳答案、点赞、标签。

**文件结构**：
```
backend/apps/qa/
├── __init__.py
├── models.py           # Question, Answer, QuestionTag, QALike
├── serializers.py
├── views.py
├── urls.py             # /api/v1/questions/*
├── services.py         # 采纳逻辑、热度计算
├── admin.py
└── tests.py
```

**数据模型**：
- `Question`：title, content, author(FK), tags(M2M), is_solved, view_count, created_at
- `Answer`：question(FK), author(FK), content, is_accepted, like_count, created_at
- `QuestionTag`：name, slug
- `QALike`：user(FK), answer(FK), unique_together

**API 端点**：
- `GET /api/v1/questions/` — 问题列表（筛选：tag, status, ordering）
- `POST /api/v1/questions/` — 提问
- `GET /api/v1/questions/{id}/` — 问题详情+回答列表
- `POST /api/v1/questions/{id}/answers/` — 回答
- `PUT /api/v1/questions/{id}/accept/{answer_id}/` — 采纳（提问者）
- `POST /api/v1/answers/{id}/like/` — 点赞

**依赖**：common, users

---

### 5. secondhand — 二手市场模块

**职责**：闲置商品发布、浏览、留言、状态管理。

**文件结构**：
```
backend/apps/secondhand/
├── __init__.py
├── models.py           # Product, ProductImage, ProductComment, ProductCategory
├── serializers.py
├── views.py
├── urls.py             # /api/v1/products/*
├── services.py         # 状态流转逻辑
├── admin.py
└── tests.py
```

**数据模型**：
- `Product`：title, description, price, condition(全新/几成新), status(on_sale/reserved/sold/off_shelf), seller(FK), category(FK), view_count, created_at
- `ProductImage`：product(FK), image（最多9张）
- `ProductCategory`：name, slug, sort_order
- `ProductComment`：product(FK), author(FK), content, created_at

**API 端点**：
- `GET /api/v1/products/` — 商品列表（筛选：category, status, price_range, ordering）
- `POST /api/v1/products/` — 发布商品
- `GET /api/v1/products/{id}/` — 商品详情
- `PUT/DELETE /api/v1/products/{id}/` — 编辑/删除（卖家）
- `PUT /api/v1/products/{id}/status/` — 变更状态
- `GET/POST /api/v1/products/{id}/comments/` — 留言

**依赖**：common, users

---

### 6. merchants — 商家板块

**职责**：商家入驻、店铺展示、活动发布、评价评分。

**文件结构**：
```
backend/apps/merchants/
├── __init__.py
├── models.py           # Merchant, MerchantImage, Activity, MerchantReview, MerchantCategory
├── serializers.py
├── views.py
├── urls.py             # /api/v1/merchants/*, /api/v1/activities/*
├── services.py         # 入驻审核、评分计算
├── admin.py
└── tests.py
```

**数据模型**：
- `Merchant`：user(OneToOne→User), name, category(FK), address, phone, business_hours, description, license_image, status(pending/approved/rejected), avg_rating, created_at
- `MerchantImage`：merchant(FK), image
- `MerchantCategory`：name, slug, icon, sort_order
- `Activity`：merchant(FK), title, description, image, start_time, end_time, discount_info, status(active/ended)
- `MerchantReview`：merchant(FK), user(FK), rating(1-5), content, reply, replied_at, created_at

**API 端点**：
- `POST /api/v1/merchants/apply/` — 入驻申请
- `GET /api/v1/merchants/` — 商家列表（筛选：category, ordering）
- `GET /api/v1/merchants/{id}/` — 商家详情
- `PUT /api/v1/merchants/{id}/` — 编辑店铺信息（商家）
- `GET/POST /api/v1/merchants/{id}/activities/` — 活动列表/发布
- `GET/POST /api/v1/merchants/{id}/reviews/` — 评价列表/发表
- `PUT /api/v1/reviews/{id}/reply/` — 商家回复评价
- `PUT /api/v1/merchants/{id}/audit/` — 审核（管理员）

**依赖**：common, users

---

### 7. housekeeping — 家政服务模块

**职责**：服务分类展示、服务商入驻、在线预约、服务评价。

**文件结构**：
```
backend/apps/housekeeping/
├── __init__.py
├── models.py           # ServiceProvider, ServiceCategory, ServiceItem, Booking, ServiceReview
├── serializers.py
├── views.py
├── urls.py             # /api/v1/housekeeping/*
├── services.py         # 预约状态流转、评分计算
├── admin.py
└── tests.py
```

**数据模型**：
- `ServiceProvider`：user(OneToOne→User), name, service_area, description, qualification_image, phone, status(pending/approved/rejected), avg_rating
- `ServiceCategory`：name, slug, icon, sort_order
- `ServiceItem`：provider(FK), category(FK), title, description, price_range, duration
- `Booking`：user(FK), service_item(FK), provider(FK), preferred_date, preferred_time, status(pending/confirmed/in_service/completed/reviewed/rejected), remark, created_at
- `ServiceReview`：booking(FK), user(FK), provider(FK), rating(1-5), content, created_at

**API 端点**：
- `GET /api/v1/housekeeping/categories/` — 服务分类列表
- `GET /api/v1/housekeeping/providers/` — 服务商列表
- `GET /api/v1/housekeeping/providers/{id}/` — 服务商详情+服务项目
- `POST /api/v1/housekeeping/apply/` — 服务商入驻
- `POST /api/v1/housekeeping/bookings/` — 提交预约
- `GET /api/v1/housekeeping/bookings/` — 我的预约列表
- `PUT /api/v1/housekeeping/bookings/{id}/status/` — 更新预约状态
- `POST /api/v1/housekeeping/bookings/{id}/review/` — 服务评价

**依赖**：common, users

---

### 8. admin_system — 系统管理扩展

**职责**：在 Django Admin 基础上扩展公告管理、分类管理、数据统计接口。

**文件结构**：
```
backend/apps/admin_system/
├── __init__.py
├── models.py           # Announcement, Report
├── serializers.py
├── views.py            # 公告API、统计API
├── urls.py             # /api/v1/admin/*
├── services.py         # 统计查询逻辑
├── admin.py            # 增强版 Admin 配置
└── tests.py
```

**数据模型**：
- `Announcement`：title, content, author(FK), is_active, created_at
- `Report`：reporter(FK), content_type, object_id, reason, status(pending/handled), handled_at

**API 端点**：
- `GET /api/v1/announcements/` — 公告列表（公开）
- `POST/PUT/DELETE /api/v1/admin/announcements/` — 公告管理（管理员）
- `GET /api/v1/admin/statistics/` — 基础统计（管理员）
- `POST /api/v1/reports/` — 提交举报
- `GET /api/v1/admin/reports/` — 举报列表（管理员）

**依赖**：common, users, 所有业务模块（统计查询）

---

## 模块间依赖关系图

```
                    ┌──────────┐
                    │  common  │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │  users   │
                    └────┬─────┘
                         │
        ┌────────┬───────┼────────┬──────────┐
        ▼        ▼       ▼        ▼          ▼
  ┌──────────┐┌────┐┌────────┐┌────────┐┌────────────┐
  │discussion││ qa ││second- ││merchan-││housekeep-  │
  │          ││    ││  hand  ││  ts    ││   ing      │
  └──────────┘└────┘└────────┘└────────┘└────────────┘
        │        │       │        │          │
        └────────┴───────┼────────┴──────────┘
                         ▼
                  ┌──────────────┐
                  │ admin_system │
                  └──────────────┘
```

**无循环依赖**：所有业务模块仅依赖 common 和 users，admin_system 单向依赖所有模块。
