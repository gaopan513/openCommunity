# openCommunity

## Project Snapshot
社区服务平台，前后端分离架构。后端：Django 5 + DRF + SimpleJWT（`backend/`），数据库默认 SQLite、通过 `DJANGO_DB_*` 环境变量可切 PostgreSQL（见 `backend/.env.example`）。Web 前端：Vue 3 + Vite + Element Plus + Pinia（`frontend/`）。微信小程序端：uni-app (Vue 3) + Pinia + uni-ui（`miniprogram/`），仅居民侧功能，复用同一套 `/api/v1/` 后端接口。共 7 个业务模块：users / discussion / qa / secondhand / merchants / housekeeping / admin_system。子目录下有更详细的 AGENTS.md（backend、frontend），编辑某文件时优先读取最近的 AGENTS.md。

## Root Setup Commands
环境：Python 3.11+；Web 前端使用 Vite 8，Node.js 须满足 `^20.19.0 || >=22.12.0`。前端和小程序各有独立的 `package-lock.json`，安装依赖优先使用 `npm ci`。

```bash
# 后端（Django，端口 8000）
cd backend
python -m venv venv
venv\Scripts\activate                 # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser      # 可选
python manage.py runserver

# 前端（Vite，端口 3000，自动代理 /api /media → 8000）
cd frontend
npm ci
npm run dev
npm run build                         # 生产构建

# 小程序（uni-app；微信开发者工具导入 miniprogram/dist/dev/mp-weixin）
cd miniprogram
npm ci
npm run dev:mp-weixin                  # 开发构建（watch 模式）
npm run build:mp-weixin                # 生产构建 → dist/build/mp-weixin
npm run check                         # 格式检查 + ESLint
```

## Universal Conventions
- 所有 API 统一挂载在 `/api/v1/` 下；统一响应格式 `{code, message, data}`（`code=0` 表示成功）。
- 后端代码注释、Docstring、日志一律用中文；前端注释用中文，变量/函数名用英文。
- 用户角色三档：`resident`（居民）/ `merchant`（商家）/ `admin`（管理员），通过 `User.role` 字段控制。角色只能由审核授予/回收（入驻、服务商审核），注册固定 resident 且忽略请求中的 role。
- JWT 鉴权：Web/小程序均 `Authorization: Bearer <access_token>`，access 2h / refresh 7d，refresh 轮换 + 黑名单；登出走 `POST /api/v1/auth/logout/` 拉黑 refresh token。小程序另有微信静默登录 `POST /api/v1/auth/wechat-login/`（code 换 openid 自动注册 resident），后端需配置 `WECHAT_MINIAPP_APPID/SECRET`。
- 多表写入（主记录+图片、评价+评分冗余字段、审核+角色授予等）必须包 `transaction.atomic()`，项目内已有先例可参照。
- 提交规范：中文 commit message，前缀如 `fix: `、`feat: `、`refactor: `。

## Security & Secrets
- 生产环境（`DJANGO_DEBUG=False`）强制要求 `DJANGO_SECRET_KEY` 环境变量，缺失拒绝启动；开发用占位密钥。配置样例见 `backend/.env.example`、`frontend/.env.example`。后端当前直接读取进程环境变量，**不会自动加载 `.env`**；仅复制文件不会生效，应通过终端或部署环境注入配置。
- 根目录 `.gitignore` 排除 `backend/db.sqlite3` 及其辅助文件、`backend/media/`、虚拟环境、`__pycache__/`、`*.py[cod]`、依赖、构建产物、日志、`.workbuddy/`、`.codegraph/` 和 `project.private.config.json`。这些本地资料禁止提交，也不要把其中的账号、令牌、个人路径或操作记录复制到源码和文档。
- `.env` 与 `.env.*` 默认忽略；允许提交 `.env.example`、`.env.*.example`，以及仅含公开 API 地址的 `miniprogram/.env.development`、`miniprogram/.env.production`。示例和小程序环境配置不得含真实凭证；`VITE_*` 会进入客户端产物，不能放 AppSecret。
- 微信 AppID 位于 `miniprogram/src/manifest.json` 的 `mp-weixin.appid` 和 `miniprogram/project.config.json`，仓库统一使用 `touristappid` 占位。真实微信登录或发布时，在本地使用自己的 AppID 并保持两处一致，同时核对后端的 `WECHAT_MINIAPP_APPID`；提交前恢复占位值，不要把 uni-app 顶层 `appid` 与微信 AppID 混淆。AppID 虽不是密钥，本项目为避免应用关联不提交具体值。`WECHAT_MINIAPP_SECRET` 只由后端进程环境注入，小程序配置中禁止出现 AppSecret。
- 初始化 Git 仓库后，用 `git check-ignore -v` 核验敏感路径，再用 `git status --short` 和 `git diff --cached --name-only` 检查实际提交清单。`.gitignore` 不会移除已被跟踪的文件，也不控制手动上传或压缩打包；微信 `packOptions.ignore` 仅影响小程序打包。
- 用户头像、商家图片等上传走 `common/utils.py` 的 `generate_upload_path`，按 `media/{folder}/{YYYYMM}/{uuid}.ext` 落盘；图片字段统一挂 `common/validators.py` 的 `validate_image`（≤5MB、jpg/jpeg/png/webp）。
- PII（手机号、地址）仅限本人或管理员访问：本人资料用 `UserProfileSerializer`，公开场景嵌套一律用 `UserSimpleSerializer`（仅 id/用户名/头像/角色）；权限控制在 `common/permissions.py`。
- 前端**禁止用 `v-html` 渲染任何用户生成内容**（token 存 localStorage 的 XSS 防线，现有代码全部文本插值）。

## JIT Index
### Package Structure
- 后端根：`backend/` → [see backend/AGENTS.md](backend/AGENTS.md)
- 前端根：`frontend/` → [see frontend/AGENTS.md](frontend/AGENTS.md)
- 小程序根：`miniprogram/`（uni-app，无子级 AGENTS.md）— 主包页面在 `src/pages/`，业务分包在 `src/modules/{posts,qa,products,housekeeping,merchants,bookings}/`，统一路由路径在 `src/router/paths.js`；API 层 `src/api/*.js` 与 Web 端同签名（改后端字段时两端同步），网络层 `src/utils/request.js` 复刻 Web 版语义（Bearer 注入、401 静默刷新重放、清登录态），业务常量统一沉淀 `src/constants/`
- 模块代码映射表：[MODULE_MAPPING.md](MODULE_MAPPING.md)（每个文件的归属模块与功能）

### 项目文档（`docs/`，按需查阅）
- 需求：[docs/requirements/PRD.md](docs/requirements/PRD.md)、[docs/requirements/feature-list.md](docs/requirements/feature-list.md)
- 架构与规范：[docs/design/architecture.md](docs/design/architecture.md)、[docs/design/coding-standards.md](docs/design/coding-standards.md)、[docs/design/module-breakdown.md](docs/design/module-breakdown.md)
- 排期与交付：[docs/planning/milestone-plan.md](docs/planning/milestone-plan.md)、[docs/planning/miniprogram-plan.md](docs/planning/miniprogram-plan.md)、[docs/delivery/release-notes.md](docs/delivery/release-notes.md)、[docs/delivery/miniprogram-checklist.md](docs/delivery/miniprogram-checklist.md)（小程序接口联调对照表，改小程序功能前先查）、[docs/delivery/miniprogram-code-review.md](docs/delivery/miniprogram-code-review.md)（小程序代码审查报告，根目录同名 [MINIPROGRAM_CODE_REVIEW.md](MINIPROGRAM_CODE_REVIEW.md)）
- 生产部署（环境变量、PostgreSQL 切换、nginx 配置、安全清单）：[docs/delivery/deployment.md](docs/delivery/deployment.md)
- 一键启动（Windows Terminal 分屏跑前后端）：[start_openCommunity.bat](start_openCommunity.bat)

### API 路由前缀（挂载于 `/api/v1/`）
| 前缀 | 模块 |
|---|---|
| `/auth/` `/users/` | users（认证、资料） |
| `/posts/` | discussion |
| `/questions/` | qa |
| `/products/` `/product-categories/` | secondhand |
| `/merchants/` `/merchant-categories/` | merchants |
| `/housekeeping/categories|providers|bookings` | housekeeping |
| `/announcements/` `/admin/` | admin_system |
| `/health/` | 健康检查（config/urls.py 内联） |

### Quick Find Commands
- 后端类/函数：`rg -n "class |def " backend/apps backend/common backend/config`
- 找 DRF ViewSet：`rg -n "class \w+(ViewSet|APIView)" backend/apps`
- 找 @action：`rg -n "@action" backend/apps`
- 找某 URL 注册：`rg -n "router.register" backend/apps`
- 找前端 API 调用：`rg -n "request\.(get|post|put|delete)" frontend/src/api`
- 找 Vue 组件：`rg -n "<script setup|<template>" frontend/src/views frontend/src/components`
- 找路由定义：`rg -n "path:|name:" frontend/src/router/index.js`
- 找测试：`rg -n "class .*TestCase" backend/apps`

## 业务不变量（改动前必读，破坏即回归）
- 家政预约 `Booking` 状态机：`pending → confirmed/rejected/cancelled`、`confirmed → in_service/rejected/cancelled`、`in_service → completed`、`completed → reviewed`；`cancelled` 为终态。仅 `pending` 可通过 PUT 修改预约信息；`pending/rejected/cancelled` 可删除。
- 二手商品图片：update 传 `images` 为**全量替换**（删旧建新），不传则保留；总数恒 ≤9。商品/帖子 `status` 字段对 serializer 只读，状态变更只能走专用 @action（如 `/products/<pk>/status/`）。
- 商家/服务商审核：仅 `pending` 可审；approve 授予 merchant 角色，merchants reject 回收角色（用户持有已通过的 `ServiceProvider` 资质时保留）。
- 前端 axios `baseURL` 默认相对路径 `/api/v1`（开发走 vite 代理、生产走同域反代），勿改回绝对地址；401 踢出时 `request.js` 会同步清理 Pinia store（`clearLocalAuth`），登出与踢出两条路径都必须清 store + localStorage。
- 小程序接口基地址走环境变量 `VITE_API_BASE_URL`（开发直连 `http://127.0.0.1:8000/api/v1`，生产 HTTPS 合法域名，见 `.env.development`/`.env.production`），勿写死；网络层语义必须与 Web 端 `request.js` 保持一致。小程序本期只做居民端功能，管理员审核、商家入驻不要加进小程序页面。
- 列表接口一律走分页（`StandardPagination`/`SmallPagination`）；serializer 的 `get_is_liked` 依赖 prefetch 缓存，改 queryset 时保持相关 `prefetch_related`。

## Definition of Done
- 改后端 → `python manage.py test` 全绿；改某模块时跑该模块测试 `python manage.py test apps.<module>`。
- 改前端 → `npm run build` 无报错；涉及 API 路径时核对后端 `router.register` 与 `@action` 的实际 URL。
- 改小程序 → `npm run check` 与 `npm run build:mp-weixin` 通过；新增/改动接口调用时对照 [docs/delivery/miniprogram-checklist.md](docs/delivery/miniprogram-checklist.md) 的联调表。
- 新增/修改字段 → 生成并应用迁移 `python manage.py makemigrations && python manage.py migrate`。
- 接口字段变更 → 同步更新 `frontend/src/api/*.js`、`miniprogram/src/api/*.js` 与对应 `serializers.py`。
- 仅修改文档或忽略规则 → 核对路径、命令和配置说明；忽略规则有变更时执行 Git 规则检查，无需为此重跑全量构建或业务测试。
