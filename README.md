# openCommunity 社区服务平台

一个面向小区居民的综合社区服务平台，涵盖自由发言、经验问答、二手市场、商家入驻、家政服务及系统管理六大核心板块。提供 Web 端与微信小程序端两种入口，后端基于 Django REST Framework 统一提供 `/api/v1/` 接口，Web 前端基于 Vue 3 + Element Plus，小程序端基于 uni-app（Vue 3），复用同一套后端 API。

## 技术栈

**后端**：Python 3.11+ / Django 5.0+ / Django REST Framework / SimpleJWT / django-filter / Pillow

**前端**：Vue 3 / Vite / Element Plus / Pinia / Vue Router / Axios

**小程序**：uni-app (Vue 3) / Vite / Pinia / uni-ui（微信开发者工具中运行）

**数据库**：开发环境 SQLite，生产环境可切换 PostgreSQL

## 功能模块

- **用户认证**：注册、登录（JWT）、Token 自动刷新与静默续期、登出（服务端拉黑 refresh token）、微信静默登录（`wx.login` 换取 code 自动注册居民账号）、个人资料管理、角色体系（居民 / 商家 / 管理员）
- **自由发言**：帖子发布（支持多图）、楼中楼评论、点赞、置顶 / 加精
- **经验问答**：提问、回答、采纳最佳答案、标签分类、点赞
- **二手市场**：闲置发布、分类筛选、价格排序、状态流转（在售 / 已售 / 下架）、买家留言
- **商家板块**：商家入驻申请与审核、店铺展示、活动发布、用户评价与商家回复
- **家政服务**：服务商入驻、服务项目展示、在线预约、订单状态推进（含取消终态）、服务评价
- **系统管理**：公告发布、举报处理、基础数据统计
- **微信小程序端**：面向居民的移动端（首页、帖子、问答、二手商品、商家/家政服务、我的预约、个人资料），管理员审核与商家入驻仍走 Web 端

## 项目结构

```
openCommunity/
├── .gitignore                # 本地数据、凭证、缓存和构建产物的提交排除规则
├── AGENTS.md                 # 开发约定与业务不变量
├── backend/
│   ├── apps/
│   │   ├── users/            # 用户认证
│   │   ├── discussion/       # 自由发言
│   │   ├── qa/               # 经验问答
│   │   ├── secondhand/       # 二手市场
│   │   ├── merchants/        # 商家板块
│   │   ├── housekeeping/     # 家政服务
│   │   └── admin_system/     # 系统管理
│   ├── common/               # 公共工具（权限、分页、异常、响应封装）
│   ├── config/               # Django 配置与主路由
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example          # 环境变量样例（密钥、数据库、CORS）
├── frontend/
│   ├── src/
│   │   ├── api/              # 各模块 API 调用层
│   │   ├── views/            # 页面组件
│   │   ├── components/       # 通用 / 业务组件
│   │   ├── router/           # 路由配置
│   │   ├── stores/           # Pinia 状态管理
│   │   ├── styles/           # 全局样式与设计系统
│   │   └── utils/            # 工具函数（Axios 封装等）
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example          # 环境变量样例（API 地址）
├── miniprogram/              # 微信小程序端（uni-app）
│   ├── src/
│   │   ├── api/              # 各模块 API 调用层（与 Web 端同签名）
│   │   ├── pages/            # 主包页面（首页、帖子列表、商品列表、服务、个人资料、登录）
│   │   ├── modules/          # 业务分包（posts/qa/products/housekeeping/merchants/bookings）
│   │   ├── router/           # 统一路由路径常量
│   │   ├── manifest.json     # uni-app 与微信小程序配置
│   │   ├── constants/        # 业务常量（状态映射等）
│   │   ├── stores/           # Pinia 状态管理
│   │   └── utils/            # 网络层封装（Bearer 注入、401 静默刷新重放）
│   ├── project.config.json   # 微信开发者工具工程配置
│   ├── package.json          # dev:mp-weixin / build:mp-weixin 脚本
│   ├── .env.development      # 开发 API 地址（VITE_API_BASE_URL）
│   └── .env.production       # 生产 API 地址占位配置，上线前需调整
├── docs/                     # 项目文档（需求、设计、开发、交付、小程序计划）
└── MODULE_MAPPING.md         # 模块代码映射表
```

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 满足 `^20.19.0 || >=22.12.0`（Web 前端 Vite 8 的要求；同一版本可用于小程序）
- npm（前端和小程序分别提供 `package-lock.json`）
- 微信开发者工具（运行小程序端时需要）

> 安装依赖并完成数据库迁移后，Windows 下可运行根目录的 [start_openCommunity.bat](start_openCommunity.bat)，自动分屏启动前后端。

后端本地开发默认使用 SQLite 与开发占位密钥。公开仓库不包含本地数据库、用户账号或上传图片；首次运行需要执行迁移，并按需创建管理员。生产部署见 [docs/delivery/deployment.md](docs/delivery/deployment.md)。

后端通过进程环境变量读取配置，**当前不会自动加载 `.env` 文件**。`backend/.env.example` 用于说明配置项；自定义密钥、PostgreSQL、CORS 或微信登录时，应在启动终端或部署环境注入变量。小程序微信登录需要 `WECHAT_MINIAPP_APPID` 与 `WECHAT_MINIAPP_SECRET`，AppSecret 只配置在后端。

例如在 PowerShell 中，启动后端前可设置微信配置（将占位符替换为自己的值，配置不写入公开文件）：

```powershell
$env:WECHAT_MINIAPP_APPID = '<your-miniapp-appid>'
$env:WECHAT_MINIAPP_SECRET = '<your-miniapp-secret>'
```

前端和小程序的环境文件由 Vite 加载。`VITE_*` 变量会被编译进客户端，只能放公开配置，不能放密钥。

### 启动后端

```bash
cd backend

# 创建并激活虚拟环境
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 执行数据库迁移
python manage.py migrate

# 创建超级管理员（可选）
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver
```

后端默认运行在 `http://127.0.0.1:8000`，API 统一挂载在 `/api/v1/` 下。

### 启动前端

```bash
cd frontend

# 安装依赖
npm ci

# 启动开发服务器
npm run dev
```

前端开发服务器已配置代理，会自动将 `/api` 请求转发至后端。

### 启动小程序

```bash
cd miniprogram

# 安装依赖
npm ci

# 开发模式（微信小程序）
npm run dev:mp-weixin
```

然后用微信开发者工具「导入项目」，目录选择 `miniprogram/dist/dev/mp-weixin`（生产构建则为 `npm run build:mp-weixin` 生成 `dist/build/mp-weixin`）。开发联调注意：

- 在开发者工具「详情 → 本地设置」勾选**不校验合法域名**，即可直连本地后端 `http://127.0.0.1:8000/api/v1`（见 `.env.development`）。
- 仓库使用 `touristappid` 占位，便于导入预览。真实微信登录和发布需要自己的 AppID：在本地修改 `miniprogram/src/manifest.json` 的 `mp-weixin.appid` 与 `miniprogram/project.config.json`，并核对后端 `WECHAT_MINIAPP_APPID`，三者须对应同一应用。提交代码前恢复占位值，避免暴露应用关联；AppID 不是 AppSecret。
- 登录由小程序调用 `wx.login` 获取 code，再交由后端换取 openid。具体联调项见 [docs/delivery/miniprogram-checklist.md](docs/delivery/miniprogram-checklist.md)。
- 上线前将 `miniprogram/.env.production` 的示例 API 域名替换为实际 HTTPS 服务地址，并在微信后台配置对应的请求和上传域名。

## GitHub 提交与隐私

根目录 [.gitignore](.gitignore) 已排除本地数据库及其辅助文件、`backend/media/` 上传资料、虚拟环境、Python 字节码缓存、依赖、构建产物、日志、AI 工具记忆和代码索引，以及微信开发者工具的 `project.private.config.json`。

`.env` 和 `.env.*` 默认不提交；公开示例文件及小程序的 `.env.development`、`.env.production` 允许提交，后两者只应包含公开 API 地址。小程序工程配置仍会提交，AppID 统一保留为 `touristappid` 占位。不要把数据库中的账号、密码哈希、令牌、联系方式或本机路径复制到源码、截图和文档中。

初始化 Git 仓库后，可在项目根目录核验：

```bash
git check-ignore -v backend/db.sqlite3 backend/media/example.png .workbuddy/memory/MEMORY.md miniprogram/project.private.config.json
git status --short
git diff --cached --name-only
```

`.gitignore` 不会移除已被 Git 跟踪的文件，也不控制网页手动上传或压缩包内容；微信开发者工具的 `packOptions.ignore` 仅影响小程序打包。

## API 概览

| 路径前缀 | 模块 |
|---|---|
| `/api/v1/auth/` | 注册、登录、Token 刷新、登出、微信登录 |
| `/api/v1/users/` | 用户资料 |
| `/api/v1/posts/` | 自由发言 |
| `/api/v1/questions/` | 经验问答 |
| `/api/v1/products/` | 二手市场 |
| `/api/v1/merchants/` | 商家板块 |
| `/api/v1/housekeeping/` | 家政服务 |
| `/api/v1/announcements/` | 公告 |
| `/api/v1/admin/` | 系统管理（举报、统计） |
| `/api/v1/health/` | 健康检查 |

## 测试

后端各模块包含认证、权限、状态机、校验等测试，可通过以下命令运行；用例数量和结果以实际运行输出为准：

```bash
cd backend
python manage.py test
```

前端和小程序的常用检查：

```bash
# 在 frontend/ 中执行
npm run build

# 在 miniprogram/ 中执行
npm run check
npm run build:mp-weixin
```

## 开发说明

- 所有接口采用统一响应格式（`code` / `message` / `data`），由 `common/response.py` 封装。
- 权限控制通过 `common/permissions.py` 中的自定义权限类实现（IsOwnerOrReadOnly、IsAdminUser、IsMerchantUser 等）。
- 分页统一使用 `common/pagination.py` 中的 StandardPagination / SmallPagination。
- 多表写入（主记录+图片、评价+评分冗余字段、审核+角色授予等）必须包在 `transaction.atomic()` 中。
- 前端 Axios `baseURL` 默认为相对路径 `/api/v1`（开发走 vite 代理、生产走同域反代），禁止改回绝对地址；渲染用户生成内容禁止使用 `v-html`。
- 项目约定与业务不变量详见 [AGENTS.md](AGENTS.md)；模块代码归属见 [MODULE_MAPPING.md](MODULE_MAPPING.md)。
- 前端设计系统定义在 `frontend/src/styles/community.css`，提供社区暖色调变量与通用组件类。
