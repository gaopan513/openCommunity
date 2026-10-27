# 技术栈推荐方案

## 推荐方案：Django + DRF + Vue 3（前后端分离）

---

## 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 运行环境 |
| Django | 5.x | Web 框架、ORM、Admin |
| Django REST Framework | 3.15+ | RESTful API 构建 |
| djangorestframework-simplejwt | 5.x | JWT 认证 |
| django-filter | 24.x | 列表筛选/过滤 |
| django-cors-headers | 4.x | 跨域资源共享 |
| Pillow | 10.x | 图片上传验证与处理 |
| PostgreSQL | 16.x | 生产数据库（开发可用 SQLite） |

## 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.4+ | 前端框架 |
| Vite | 5.x | 构建工具 |
| Vue Router | 4.x | 前端路由 |
| Pinia | 2.x | 状态管理 |
| Element Plus | 2.x | UI 组件库 |
| Axios | 1.x | HTTP 请求 |

## 开发工具

| 工具 | 用途 |
|------|------|
| pip / venv | Python 依赖管理 |
| npm / pnpm | 前端依赖管理 |
| pytest + pytest-django | 后端测试 |
| Django Admin | 管理后台（直接复用） |

## 项目结构概览

```
openCommunity/
├── backend/                  # Django 后端
│   ├── config/               # Django 项目配置
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── apps/                 # 业务模块（Django Apps）
│   │   ├── users/            # 用户与认证
│   │   ├── merchants/        # 商家板块
│   │   ├── secondhand/       # 二手市场
│   │   ├── qa/               # 经验问答
│   │   ├── discussion/       # 自由发言
│   │   ├── housekeeping/     # 家政服务
│   │   └── admin_system/     # 系统管理扩展
│   ├── common/               # 公共工具（权限类、分页、异常处理）
│   ├── media/                # 上传文件存储
│   ├── manage.py
│   └── requirements.txt
├── frontend/                 # Vue 3 前端
│   ├── src/
│   │   ├── views/            # 页面组件
│   │   ├── components/       # 公共组件
│   │   ├── api/              # API 请求封装
│   │   ├── stores/           # Pinia 状态
│   │   ├── router/           # 路由配置
│   │   └── utils/            # 工具函数
│   ├── package.json
│   └── vite.config.js
├── docs/                     # 项目文档
└── MODULE_MAPPING.md         # 代码→需求追溯映射
```

## 关键技术决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 认证方案 | JWT (SimpleJWT) | 无状态、适合前后端分离、后续小程序可复用 |
| 权限模型 | Django Group + 自定义 Permission 类 | 成熟稳定、RBAC 开箱即用 |
| 管理后台 | Django Admin | MVP 阶段零开发成本，功能完整 |
| 图片存储 | 本地 Media 目录 | MVP 简化，后续迁移 OSS |
| 数据库 | 开发 SQLite / 生产 PostgreSQL | 开发零配置，生产高性能 |
| API 风格 | RESTful | DRF 原生支持，规范清晰 |
| 前端 UI | Element Plus | 组件丰富、中文文档完善、适合管理类系统 |
