# openCommunity 微信小程序端代码审查报告

> **审查日期**：2026-09-18  
> **审查对象**：`miniprogram/`（微信小程序端，uni-app Vue 3 + Pinia + Vite 5）  
> **审查范围**：工程配置、构建产物与体积、网络层鉴权、公共组件、路由设计、6大业务分包及微信生态合规性  
> **审查基准**：`npm run check`（ESLint + Prettier）、`npm run build:mp-weixin` 生产构建、微信官方小程序设计规范与平台政策  
> **归档位置**：`docs/delivery/miniprogram-code-review.md`

---

## 一、 审查结论总览与度量基线

本次对 `miniprogram/` 目录进行了全量源码走查和构建验证，总体评价为 **优良（A级）**。  
工程整体分层清晰、分包策略科学、代码遵循 Vue 3 Composition API 规范，未发现内存泄漏或高危安全漏洞。

### 1. 核心工程度量

| 度量指标 | 实际测得数据 | 微信官方/工程指标标准 | 状态 |
| :--- | :--- | :--- | :--- |
| **构建结果** | 0 error, 0 warning，编译成功 | `npm run build:mp-weixin` 顺利退出 | ✅ 通过 |
| **代码规范 (Lint)** | 0 error, 0 warning | ESLint + Prettier 规范基线 | ✅ 通过 |
| **生产包总大小** | **215.59 KB (0.21 MB)** | 单包/总包上限 2MB / 20MB | 🌟 极致轻量 (远低于阈值) |
| **主包静态资源与页面** | 主包页面仅 31.84 KB，静态图标 15.91 KB | 建议主包尽可能小（< 1.5MB） | 🌟 秒级首屏冷启 |
| **分包设计** | 6 个独立业务分包（总计 64.70 KB） | 业务模块完全独立分包 | ✅ 架构健康 |
| **状态机与后端一致性** | 预约 7 态、商品 4 态流转与后端模型 1:1 对齐 | 严格遵守业务不变量 | ✅ 契约完备 |

### 2. 构建体积分布详情（`dist/build/mp-weixin`）

```text
Total Size: 215.59 KB (0.21 MB)
 ├── common/ (公共运行时与 vendor): 73.65 KB
 ├── modules/ (6大分包页面逻辑):    64.70 KB
 ├── pages/ (主包 5个Tab + 1登录): 31.84 KB
 ├── static/ (TabBar 图标资源):     15.91 KB
 ├── utils/ (请求/上传/格式化/埋点):  7.69 KB
 ├── components/ (业务共用组件):     7.57 KB
 ├── api/ (接口平移层):              4.01 KB
 ├── stores/ (Pinia 状态):           1.88 KB
 ├── composables/ (分页逻辑封装):    1.20 KB
 └── router/ (集中路由路径):         0.55 KB
```

---

## 二、 架构设计与优秀实践分析

### 1. 突破平台限制的高性能多图上传 (`src/utils/upload.js`)
- **背景挑战**：微信小程序原生 `wx.uploadFile` 仅支持单文件上传，而后端商品/帖子接口要求通过 `images: ListField(child=ImageField)` 一次性接收多个图片文件。
- **解决方案**：手工将文本字段与多张图片拼接为 `ArrayBuffer` 的 `multipart/form-data` 标准报文，借由 `uni.request` 发送。
- **可靠性防线**：
  - 上传前先利用 `FileSystemManager.getFileInfo` 进行单张大小预检（≤5MB），超限前置拦截；
  - 根据后缀推导部件 MIME 并限制白名单格式（jpg/jpeg/png/webp）；
  - 拦截 401 状态，复用 `refreshAccessToken()` 静默刷新并无感重放一次，弱网与会话失效容灾良好。

### 2. 健壮的双 Token 静默刷新与登录态还原机制 (`src/utils/request.js`)
- **并发互斥**：利用全局 `refreshingPromise` 保证并发请求多个接口遭遇 401 时，只发起一次刷新请求，避免重复消耗刷新令牌。
- **双令牌轮换**：对齐后端 `ROTATE_REFRESH_TOKENS=True` 策略，刷新成功时同步更新 `access_token` 与 `refresh_token`。
- **登录现场还原**：401 踢出与未登录拦截均提取当前页面路径及 URL options（含详情页 `id` 等参数），编码传入 `redirect` 参数；登录成功后通过 `reLaunch` 精确回跳，且具备内部路由前缀白名单校验，杜绝开放重定向。
- **弱网保护**：fail 回调中区分网络断开与 Token 失效，弱网环境下不误清登录态。

### 3. 请求防串台与生命周期解耦的分页 Composable (`src/composables/usePagedList.js`)
- **请求序号守卫 (`seq`)**：在搜索关键字或切换类型时，通过递增序号比对，主动废弃在途旧请求的响应，彻底消除异步竞态导致的列表数据串台。
- **生命周期解耦**：针对 uni-app 组合式生命周期（`onReachBottom` / `onPullDownRefresh`）仅在页面根组件 setup 生效的限制，设计 `active` 响应式守卫，使“服务圈”单页内承载“家政”与“商家”双列表时互不干扰，按需刷新。
- **全局新鲜度通知**：监听 `EVENTS.LIST_CHANGED`，在子页面发布、删除或修改后仅打标记，返回列表页触发 `onShow` 时才重载，避免不可见状态下的无效渲染。

### 4. 实时日志与错误容灾上报 (`src/utils/analytics.js`)
- 封装 `track`、`reportError`、`logWarn`，微信端优先接入官方 `wx.getRealtimeLogManager`，其他端平滑降级为控制台日志；
- 在 `App.vue` 的 `onError` 生命周期中全局捕获未处理异常并上报；
- 严格过滤埋点 payload，不记录手机号、地址等 PII 敏感信息。

---

## 三、 发现的问题清单与修复建议

---

### 🔴 P0 级问题：功能缺陷与运行时隐患（必须修复）

#### 问题 P0-1：`ImageUploader.vue` 计数字段未声明为 `computed` 导致模板渲染函数源码
- **位置**：`src/components/ImageUploader.vue` 第 18 行、第 52-53 行
- **缺陷表现**：
  ```javascript
  // 第 52 行
  const displayCount = () =>
    props.remoteImages.length ? Math.max(localImages.value.length, props.remoteImages.length) : localImages.value.length
  ```
  模板中直接写：
  ```html
  <view class="count-hint"> {{ displayCount }}/{{ max }} 张{{ hint }} </view>
  ```
  在真机及小程序编译产物中，`displayCount` 未带括号调用，页面会直接输出函数定义字符串（如 `() => .../9 张`），无法显示正确的张数。
- **修复方案**：引入 `computed` 声明：
  ```javascript
  import { ref, computed, watch } from 'vue'

  const displayCount = computed(() =>
    props.remoteImages.length ? Math.max(localImages.value.length, props.remoteImages.length) : localImages.value.length
  )
  ```

---

#### 问题 P0-2：`modules/qa/detail.vue` 模板使用了未定义变量 `solved`
- **位置**：`src/modules/qa/detail.vue` 第 10 行
- **缺陷表现**：
  ```html
  <text class="oc-tag" :style="solved ? solvedStyle : unsolvedStyle">
    {{ question.is_solved ? '已解决' : '待解答' }}
  </text>
  ```
  `<script setup>` 中从未声明过 `solved` 变量（仅有 `question.value.is_solved`）。这导致该三元表达式始终判断为 false，即使问题已被采纳解决，标签也始终显示为橙色的待解答样式。
- **修复方案**：
  ```html
  <text class="oc-tag" :style="question.is_solved ? solvedStyle : unsolvedStyle">
    {{ question.is_solved ? '已解决' : '待解答' }}
  </text>
  ```

---

#### 问题 P0-3：列表页截取摘要文本缺少安全判空，存在潜在白屏风险
- **位置**：
  - `src/pages/posts/list.vue` 第 56 行：`post.content.slice(0, 80)`
  - `src/modules/qa/list.vue` 第 45 行：`q.content.slice(0, 80)`
- **缺陷表现**：若由于网络抖动、历史脏数据或接口异常导致 `content` 字段为 `null` 或 `undefined`，调用 `.slice()` 会直接引发运行时 `TypeError`，中断渲染引发白屏。
- **修复方案**：添加安全判空兜底：
  ```html
  <!-- 帖子列表 -->
  <view class="post-excerpt">{{ (post.content || '').slice(0, 80) }}{{ (post.content || '').length > 80 ? '…' : '' }}</view>

  <!-- 问答列表 -->
  <view class="q-excerpt">{{ (q.content || '').slice(0, 80) }}{{ (q.content || '').length > 80 ? '…' : '' }}</view>
  ```

---

### 🟡 P1 级问题：微信生态体验与业务流程短板（建议近期排期）

#### 问题 P1-1：各业务详情页面缺失微信原生分享配置
- **位置**：
  - `src/modules/posts/detail.vue`（帖子详情）
  - `src/modules/products/detail.vue`（商品详情）
  - `src/modules/qa/detail.vue`（问答详情）
  - `src/modules/merchants/detail.vue`（商家详情）
  - `src/modules/housekeeping/detail.vue`（服务商详情）
- **缺陷表现**：未在页面内定义 `onShareAppMessage` 和 `onShareTimeline`。微信右上角胶囊菜单中的“转发给朋友”与“分享到朋友圈”将默认置灰禁用，严重制约社区小程序的社交传播。
- **修复方案**：引入 uni-app 的分享生命周期，如在 `modules/posts/detail.vue` 中补齐：
  ```javascript
  import { onShareAppMessage, onShareTimeline } from '@dcloudio/uni-app'

  onShareAppMessage(() => ({
    title: post.value.title || '邻里圈热帖',
    path: `/modules/posts/detail?id=${postId.value}`,
  }))

  onShareTimeline(() => ({
    title: post.value.title || '邻里社区',
    query: `id=${postId.value}`,
  }))
  ```

---

#### 问题 P1-2：发布页与私有列表页缺少前置登录门禁
- **位置**：
  - `src/modules/posts/create.vue`（发帖）
  - `src/modules/products/create-edit.vue`（商品发布）
  - `src/modules/bookings/my.vue`（我的预约）
  - `src/modules/products/mine.vue`（我的商品）
- **缺陷表现**：
  - 在发帖和发商品页面中，未登录游客可以正常输入标题、大段文字和选择图片，直到最后点击“发布”按钮时才触发 `requireLogin()` 弹窗。一旦跳转登录，未保存的输入内容将丢失。
  - 在“我的”私有列表中，未登录游客直接打开时接口返回 401 提示后页面显示“暂无数据”，易产生误解。
- **修复方案**：在发布页和私有列表页的 `onShow` 生命周期内增加前置拦截：
  ```javascript
  import { onShow } from '@dcloudio/uni-app'
  import { requireLogin } from '@/utils/auth'

  onShow(() => {
    if (!requireLogin()) return
  })
  ```

---

#### 问题 P1-3：`modules/bookings/my.vue` 存在并发拉取剩余分页的隐患
- **位置**：`src/modules/bookings/my.vue` 第 148-168 行（`fetchPage2`）
- **缺陷表现**：
  ```javascript
  async function fetchPage2(totalCount) {
    const pages = Math.ceil(totalCount / 20)
    const requests = []
    for (let p = 2; p <= Math.min(pages, 10); p++) {
      requests.push(fetchPage(p).catch(() => ({ results: [] })))
    }
    const settled = await Promise.all(requests)
    return settled.flatMap((d) => d.results || [])
  }
  ```
  当用户历史预约超过 20 条时，使用 `Promise.all` 瞬间发起多达 9 个 HTTP 请求。微信小程序网络底层对同时并发请求数有严格上限（默认 10 个），这种“并发打满”的做法在弱网下极易导致请求排队超时。
- **修复方案**：对齐二手市场和帖子列表，改用 `usePagedList` 实现标准的触底加载更多。

---

### 🟢 P2 级问题：规范与细节优化（建议后续维护）

#### 优化 P2-1：收敛零散的页面路径硬编码
- **位置**：
  - `pages/home/index.vue`（第 58, 74, 82 行）：硬编码 `'/pages/posts/list'`、`'/pages/products/list'` 等；
  - `pages/profile/index.vue`（第 169 行）：硬编码 `'/pages/auth/login?redirect=/pages/profile/index'`；
  - `pages/auth/login.vue`（第 68, 77, 80 行）：硬编码 `'/pages/home/index'`；
  - `modules/posts/create.vue`（第 77 行）：硬编码 `'/pages/home/index'`。
- **优化方案**：统一引入 `src/router/paths.js` 中的 `TAB`、`PAGE`、`ROUTE` 常量，保持单一信息源。

#### 优化 P2-2：移除 `pages/services/index.vue` 的冗余触底监听
- **位置**：`src/pages/services/index.vue` 第 165-168 行
- **缺陷表现**：页面内直接调用的 `usePagedList` 已在 setup 顶层自动监听了 `onReachBottom`；页面末尾又写了一次 `onReachBottom`，导致一次触底触发两次回调。直接删除页面底部的 `onReachBottom` 即可。

#### 优化 P2-3：微信隐私保护协议 (`__usePrivacyCheck__`) 评估
- **位置**：`src/manifest.json` 第 30 行 (`"__usePrivacyCheck__": false`)
- **建议**：因小程序使用了相册选择 (`uni.chooseMedia`)，上架发布前需确保微信公众平台后台已补充《用户隐私保护指引》，并配合基础库升级完成隐私协议弹窗合规。

---

## 四、 提审上线前的整改推进表

| 优先级 | 任务项 | 涉及文件 | 影响 |
| :---: | :--- | :--- | :--- |
| **P0** | 修复 `ImageUploader` 的 `displayCount` computed 计算属性 | `src/components/ImageUploader.vue` | 修复张数展示为源码的 Bug |
| **P0** | 修复问答详情中未定义变量 `solved` | `src/modules/qa/detail.vue` | 修复已采纳状态显示异常 |
| **P0** | 增强帖子与问答列表摘要截断的安全判空 | `src/pages/posts/list.vue`<br>`src/modules/qa/list.vue` | 杜绝脏数据引发白屏崩溃 |
| **P1** | 5 大详情页面补齐微信原生分享 (`onShareAppMessage`) | 各详情页 | 解除右上角“转发给朋友”置灰 |
| **P1** | 发布页与个人数据页增设前置登录门禁 | `create.vue`, `mine.vue`, `my.vue` | 保护用户草稿，避免重复登录 |
| **P1** | 改造“我的预约”为标准的触底分页加载 | `src/modules/bookings/my.vue` | 避免瞬间打满小程序并发连接池 |
| **P2** | 路径硬编码重构为引用 `router/paths.js` | 4 处散落文件 | 统一路由常数，提升可维护性 |
| **P2** | 清理服务圈冗余的 `onReachBottom` 监听 | `src/pages/services/index.vue` | 消除无意义的冗余调用 |

---

> **结语**：本次审查反映出该小程序在底层机制、分包控制和业务复现上有着扎实的工程水平。只要完成上述清单中 3 项 P0 缺陷及 P1 分享/门禁的修复，即可安心推进全链路真机联调与微信审核发布。
