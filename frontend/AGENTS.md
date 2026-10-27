# frontend

## Package Identity
Vue 3 + Vite 8 单页应用，配合 Element Plus UI、Pinia 状态管理、Vue Router 4、Axios HTTP。开发端口 3000，自动代理 `/api`、`/media` 到后端 8000。无单测框架，验证靠 `npm run build` 与浏览器手动点测。

## Setup & Run
```bash
cd frontend
npm install
npm run dev          # http://localhost:3000，自动代理 /api /media → 8000
npm run build        # 生产构建，产物在 dist/
npm run preview      # 预览构建产物
```
前置：后端 `python manage.py runserver` 必须先起来（见 [backend/AGENTS.md](../backend/AGENTS.md)）。

## Patterns & Conventions

### 目录组织
- `src/api/<module>.js` — 每个后端模块对应一个 API 文件，按业务模块拆分（参考 `src/api/housekeeping.js`）
- `src/views/<module>/<Page>.vue` — 页面组件，按后端模块分子目录
- `src/components/<module>/<Component>.vue` — 业务对话框/抽屉等组件，按模块分子目录
- `src/stores/<name>.js` — Pinia store，目前仅 `user.js`
- `src/router/index.js` — 所有路由集中定义，懒加载 `() => import('@/views/...')`
- `src/utils/request.js` — 唯一的 Axios 实例，所有 API 调用必须复用，不要新建 axios 实例
- `src/styles/community.css` — 设计系统：CSS 变量（`--oc-*`）+ 通用类（`oc-page` / `oc-card` / `oc-tag` 等），全局暖橙墨绿色调

### API 调用约定（强制）
- 所有请求一律 `import request from '@/utils/request'`，禁止直接 `import axios from 'axios'`。
- 函数命名：`get/list/create/update/delete` + 资源单数（如 `getProvider(id)`、`getProviders(params)`、`createBooking(data)`）。
- URL 路径**必须严格对齐后端 `router.register` 与 `@action` 的实际 URL**，详见下方"Common Gotchas"。
- 拦截器已统一处理 JWT 携带、401 跳登录、错误 toast，API 函数**不要**再写 try/catch toast。
- 列表接口透传 query params：`request.get('/xxx/', { params })`，由后端 `django_filters` + DRF SearchFilter 处理。
- 文件上传：`request.post('/xxx/', formData, { headers: { 'Content-Type': 'multipart/form-data' } })`。

### 组件写法约定
- 统一使用 Vue 3 `<script setup>` 语法糖，不要用 Options API。
- 业务对话框（CreateDialog/ApplyDialog）模式：`<el-dialog v-model="visible">` + `defineProps(['modelValue'])` + `defineEmits(['success', 'update:modelValue'])`，参考 `src/components/housekeeping/ProviderApplyDialog.vue`。
- 页面列表组件：分页用 `<el-pagination>`，筛选用 `el-select` / `el-input` + `el-button`，列表用 `el-card` 包裹。
- 状态展示用 `<el-tag>` + 后端状态字符串（`pending` / `approved` / `rejected` 等），配色参考现有页面（`type="warning"` `type="success"` `type="danger"`）。

### 路由与鉴权约定
- 路由 `meta` 字段：`{ title, requiresAuth?, guest? }`。
  - `requiresAuth: true` — 未登录跳 `/login?redirect=<fullPath>`
  - `guest: true` — 已登录用户禁止访问（如登录、注册页）
- 路由名遵循 PascalCase（如 `PostDetail`、`ServiceDetail`），路径用 kebab-case。
- 用户态来自 `useUserStore()`（`src/stores/user.js`），不要直接读 `localStorage`，统一走 store。
- 角色判定用计算属性：`isMerchant` / `isAdmin`（store 已封装），用于条件渲染菜单与按钮。

### 设计系统约定
- 颜色变量定义在 `src/styles/community.css` 顶部 `:root`，主色 `--oc-primary`（暖橙 #e8622c）、点缀 `--oc-accent`（墨绿 #1f6f54）。
- 字体：标题用 `--oc-font-display`（Fraunces 衬线），正文用 `--oc-font-body`。
- 新增页面优先使用 `oc-page` / `oc-card` / `oc-tag` 等通用类，避免写死颜色值。
- Element Plus 主题色与 `--oc-primary` 对齐（通过 `community.css` 内的覆盖）。

## Key Files
- 入口：`src/main.js`（Vue + Element Plus + Pinia + Router 初始化）
- 全局布局：`src/App.vue`（导航栏 + `<router-view>` + 页脚）
- 路由表：`src/router/index.js`（98 行覆盖全部页面 + beforeEach 守卫）
- 用户 store：`src/stores/user.js`（登录/登出/注册/资料更新，Token 持久化到 localStorage）
- HTTP 工具：`src/utils/request.js`（Axios 实例 + 拦截器 + JWT 携带 + 401 跳转）
- 设计系统：`src/styles/community.css`（暖橙墨绿色调 + 纸感纹理）
- Vite 配置：`vite.config.js`（端口 3000 + `/api` `/media` 代理）
- API 调用层：`src/api/*.js`（每模块一文件，共 7 个）

## JIT Index Hints
- 找某模块的全部 API 调用：`rg -n "export function" frontend/src/api/<module>.js`
- 找页面组件：`rg -n "<script setup>" frontend/src/views`
- 找业务组件：`rg -n "<script setup>" frontend/src/components`
- 找路由定义：`rg -n "path:|name:|component:" frontend/src/router/index.js`
- 找 Pinia store：`rg -n "defineStore" frontend/src/stores`
- 找 Element Plus 用法：`rg -n "el-(dialog|table|pagination|form|select|tag|button)" frontend/src`
- 找某资源的前端调用 URL（核对后端）：`rg -n "/<module>/" frontend/src/api`
- 找设计 token：`rg -n "^\s*--oc-" frontend/src/styles/community.css`

## Common Gotchas

### ⚠️ API 路径必须与后端 `router.register` + `@action` 严格对齐
- 后端 DRF `DefaultRouter` 注册 `router.register('housekeeping/providers', ServiceProviderViewSet)` 后，`@action(detail=False, methods=['post']) def apply` 生成的 URL 是 `/api/v1/housekeeping/providers/apply/`。
- 前端 `src/api/housekeeping.js` 必须写 `request.post('/housekeeping/providers/apply/', data)`，**不能**写 `/housekeeping/apply/`。
- 历史教训：曾因前端漏掉 `providers/` 段，导致服务商入驻提交报"请求失败"（404 后端返回 `{"detail":"Not found."}` 无 `message` 字段，前端 `request.js:46` 回退到通用错误提示）。
- **核对方法**：打开 `backend/apps/<module>/urls.py` 看 `router.register` 的 prefix；`@action` 的实际 URL = `/api/v1/<prefix>/<action>/`（detail=False）或 `/api/v1/<prefix>/<pk>/<action>/`（detail=True）。

### ⚠️ 404 错误提示会丢失上下文
- 后端 404 默认响应体 `{"detail": "Not found."}` 没有 `message` 字段，`utils/request.js:46` 的 `data?.message || '请求失败'` 会回退到"请求失败"。
- 排查任何"请求失败"提示时，**第一时间看 Network 面板的实际 URL 与状态码**，不要只看 toast 文案。

### ⚠️ baseURL 与开发代理
- `utils/request.js:15` 的 `baseURL` 默认 `http://localhost:8000/api/v1`，可用 `VITE_API_BASE_URL` 覆盖。
- `vite.config.js` 配了 `/api` 代理到 8000，但 `baseURL` 已经带完整后端地址，所以实际不走 vite 代理（直连后端）。CORS 由后端 `django-cors-headers` 处理。
- 生产部署时改用同源相对路径（去掉 `http://localhost:8000`），让 nginx 反代。

### ⚠️ Token 持久化与刷新
- `access_token` / `refresh_token` / `user_info` 三件套存在 localStorage，登录/登出由 `stores/user.js` 的 `setAuthData` / `logout` 统一管理。
- access 过期（2h）后端返回 401，`request.js:48` 自动清 localStorage 并跳 `/login`。**当前未实现自动 refresh**，刷新 token 字段虽保存但未使用。

### ⚠️ `@` 别名指向 `src`
- `vite.config.js:10` 配置 `@` → `src/`，导入一律用 `@/api/xxx`、`@/components/xxx`，不要用相对路径 `../../`。

## Pre-PR Checks
```bash
cd frontend
npm run build                  # 必须无 error 无 warning
# 涉及 API 路径改动时，同步核对 backend/apps/<module>/urls.py 与 backend/apps/<module>/views.py 的 @action
# 涉及新页面时，在 src/router/index.js 注册路由，并在 App.vue 导航栏添加入口（如需）
```
