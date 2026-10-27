# 微信小程序端开发计划

## 文档定位

本计划是 PRD「后续规划：功能完善后迁移至微信小程序」的落地实施方案，与 [milestone-plan.md](milestone-plan.md)（Web 主站 M1-M8）平行，里程碑编号采用 **MP** 前缀以避免混淆。

**技术选型决策（已评审确认）**：

| 决策点 | 结论 | 理由 |
|--------|------|------|
| 小程序框架 | uni-app + Vue3 + Pinia + uni-ui | 复用团队既有 Vue3 技能栈；一套代码未来可扩 H5/App |
| 后端 API | 直接复用 `/api/v1/` 现有全部接口 | 统一信封 `{code,message,data}` + JWT Bearer 天然端无关，不分叉版本 |
| 登录方式 | `wx.login` 静默登录，自动注册 resident 用户 | 居民无感知；本期不做绑定老账号、不做手机号绑定 |
| 本期角色范围 | 仅居民端功能 | 管理员审核、商家入驻/店铺管理仍走 Web 端 |

---

## 一、现状评估（调研结论）

### 1.1 后端就绪度：约 90%，可直接复用

- **API 面**：`/api/v1/` 下 11 个 ViewSet + 5 个 APIView + 约 20 个 @action，共 60+ 端点，统一 RESTful 规范（复数名词资源、`?page=&page_size=` 分页、`{code, message, data}` 信封）。
- **认证**：全局 SimpleJWT Bearer（access 2h / refresh 7d，轮换 + 黑名单），无 cookie/session 依赖，小程序天然兼容。
- **公共组件层 `common/`**：响应封装（response.py）、异常处理器（exceptions.py）、权限类（permissions.py）、分页器（pagination.py）、校验器（validators.py）全部为纯服务端机制，不含任何浏览器假设。
- **部署形态**：nginx 同域 HTTPS 反代（见 deployment.md），恰好满足微信小程序强制 HTTPS 合法域名的要求，上线链路无需新增组件。
- **唯一裸格式端点**：`/api/v1/auth/refresh/` 是 SimpleJWT 原生视图，返回裸 `{access}` 不带信封。Web 端 `frontend/src/utils/request.js` 已对其特判直连，小程序网络层照搬同样的特判即可，**不改后端**。

### 1.2 后端唯一真增量：微信登录

`User` 模型（apps/users/models.py）目前没有任何第三方身份字段；认证视图（apps/users/views.py）全部为手写 APIView + `RefreshToken.for_user()` 签发。新增一个 `WechatLoginView` 照抄既有模式即可，零侵入。

### 1.3 前端可复用资产与重写边界

| 资产 | 复用策略 |
|------|----------|
| `frontend/src/api/*.js`（7 文件 58 函数） | 接口定义不耦合 Element Plus，换同签名 request shim 后**近乎原样复制**，路径零改动 |
| `frontend/src/utils/request.js` 的语义 | 作为小程序网络层蓝本 **1:1 复刻**（Bearer 注入、401 静默刷新重放、登录态清理） |
| `frontend/src/stores/user.js` | 结构平移，登录入口改为静默微信登录 |
| 散落 5 处的 statusMap 等业务常量 | 在小程序内新建 `constants/` 统一沉淀（Web 侧本次不动） |
| Element Plus 模板层（15 页 + 8 弹窗，约 6000 行） | **零复用**，UI 全量重写为小程序页面 |

---

## 二、总体架构

```
┌──────────────────────────────┐      ┌──────────────────────────────┐
│   微信小程序（miniprogram/） │      │     Web SPA（frontend/）     │
│   uni-app + Vue3 + uni-ui    │      │   Vue3 + Element Plus        │
└──────────────┬───────────────┘      └──────────────┬───────────────┘
               │  HTTPS（request/uploadFile 合法域名）│  同域反代
               ▼                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              Nginx（现有域名，443 ssl，同域反代）                │
│         /api/ → gunicorn    /media/ → 静态媒体    / → dist       │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│            Django + DRF（同一套 /api/v1/ 接口）                  │
│    新增：POST /api/v1/auth/wechat-login/（唯一增量端点）          │
└─────────────────────────────────────────────────────────────────┘
                               ▼
                     PostgreSQL / SQLite（共用同一库）
```

两端共享用户与数据；Web 密码账号与小程序微信账号在本期是两个独立身份（已接受，见风险清单 R2）。

---

## 三、后端改造（MP0）

### 3.1 User 模型增加微信身份字段

```python
# apps/users/models.py — User 类内追加
openid = models.CharField(
    '微信openid',
    max_length=64,
    unique=True,
    null=True,
    blank=True          # 非 WeChat 用户保持 NULL（unique 允许多个 NULL）
)
unionid = models.CharField(
    '微信unionid',
    max_length=64,
    unique=True,
    null=True,
    blank=True          # 预留：后续开放平台多端身份打通使用
)
```

随后执行 `python manage.py makemigrations users && python manage.py migrate`。

### 3.2 新增 WechatLoginView

路由挂载到 `apps/users/urls_auth.py`：`path('wechat-login/', views.WechatLoginView.as_view(), name='wechat-login')`

**接口规范**：

```
POST /api/v1/auth/wechat-login/
Permission: AllowAny
请求体：{ "code": "<wx.login 返回的临时凭证>" }
```

处理流程：

1. `code` 缺失 → `error_response('缺少微信登录凭证', code=40001)`；
2. 未配置 `WECHAT_MINIAPP_APPID/SECRET` → `error_response('微信登录暂未配置', code=50101)` 并记录 ERROR 日志；
3. 以 `requests.get(jscode2session_url, timeout=5)` 换取 openid/session_key：
   - `errcode == 0` → 继续；
   - 其他 errcode（如 40029 无效 code、-1 系统繁忙、45011 频率限制）→ `error_response('微信登录失败，请重试', code=40102)`；
   - 网络异常/超时 → 同上错误码，WARN 日志。
4. 按 `openid` 查询 User：
   - **命中** → 直接签发；
   - **未命中** → 自动创建用户：`username = f"wx_{token_hex(4)}"`（碰撞时重试）、`set_unusable_password()`（静默注册用户不得拥有可登录密码）、`role` 不显式赋值（沿用模型默认 resident，遵守"角色只能由审核授予"不变量）、openid/unionid 写入。整体包 `transaction.atomic()`。
5. `RefreshToken.for_user(user)` 签发，返回与 LoginView 完全一致的结构：

```json
{ "code": 0, "message": "登录成功", "data": { "user": {...UserProfileSerializer}, "access": "...", "refresh": "..." } }
```

### 3.3 配置与环境变量

- `requirements.txt` 增加 `requests>=2.31`（用于调用 jscode2session，带超时与异常处理）。
- `config/settings.py` 读取环境变量 `WECHAT_MINIAPP_APPID`、`WECHAT_MINIAPP_SECRET`（默认空串表示未启用微信登录）。
- `.env.example` 补充上述两项及注释。

### 3.4 测试用例（mock jscode2session 响应）

| 用例 | 断言 |
|------|------|
| 首次登录 | 返回 200 新建 resident 用户，openid 落库，password 为 unusable，响应含 access/refresh/user |
| 二次登录 | openid 命中同一用户，不重复建号，JWT 正常签发 |
| code 缺失 | 400 + code=40001 |
| 微信返回 40029 | 400 + code=40102，不建用户 |
| 未配置 appid/secret | 错误码 50101 |
| Token 黑名单链路 | 登出后 refresh 无法续期（沿用 LogoutView，无需新代码，回归验证） |

**完成标准**：`python manage.py test apps.users` 全绿；存量接口零变更（diff 仅限 models.py / views.py / urls_auth.py / serializers 导入 / settings.py / requirements.txt / .env.example）。

---

## 四、小程序工程方案（MP1-MP2）

### 4.1 工程初始化

- 目录：仓库顶层 `miniprogram/`（与 frontend/ 平级）。
- 脚手架：`npx degit dcloudio/uni-preset-vue#vite miniprogram`（Vue3/Vite JS 版），运行 `npm run dev:mp-weixin` 后用微信开发者工具导入 `dist/dev/mp-weixin`。
- 依赖：Pinia（`pinia@2`，Vue3 版可用）、`@dcloudio/uni-ui`。
- 主题：导航栏/主色对齐 `frontend/src/styles/community.css` 的暖橙主色（#e8622c 系）。
- manifest.json：填写小程序 AppID（占位待注册后补）；源码视图开启 `"mp-weixin": { "setting": { ... } }` 默认值即可。
- .env.development / .env.production 定义 `VITE_API_BASE_URL`（开发指向本地 django 通过微信开发者工具勾选"不校验合法域名"，生产指向线上 HTTPS 域名）。

### 4.2 网络层 utils/request.js（1:1 复刻 Web 语义）

对照 `frontend/src/utils/request.js` 逐条实现：

| Web 行为 | 小程序实现 |
|----------|-----------|
| axios 实例 + baseURL env | Promise 化的 `uni.request` 封装，baseURL 读 `VITE_API_BASE_URL` |
| 请求拦截注入 `Bearer <localStorage.access_token>` | 注入 `Bearer <uni.getStorageSync('access_token')>` |
| 响应拦截直接解包 `response.data` | 解包 `res.data`，同时保留 statusCode 双层判断 |
| FormData 清 Content-Type | 上传走 `uni.uploadFile` 单独分支，不走本封装 |
| 401 静默刷新（裸 axios 调 `/auth/refresh/`，并发共享 refreshingPromise，回写双 token） | 同逻辑：裸 promise 调 refresh（该端点返回裸 `{access[,refresh]}`，与 Web 相同地跳过信封解析），Storage 回写 |
| `_retry` 重放一次，再失败判定会话失效 | 同逻辑 |
| `clearAuthAndGoLogin()`：清三键 + 动态 import store 调 `clearLocalAuth` + 500ms 防抖 | 清 Storage 三键 + `clearLocalAuth` + `uni.reLaunch` 到登录页，保留 redirect 参数 |
| 登录/刷新接口自身 401 只透传 message；403/404/500 语义化提示 | 同分支；ElMessage 替换为 `uni.showToast` |

### 4.3 API 层平移规则

- 复制 `frontend/src/api/*.js` 中居民端用到的模块（auth、discussion、qa、secondhand、merchants 只读+评价部分、housekeeping），函数签名与路径**零改动**。
- 例外改造点：
  - 单图上传（头像等）：改用 `uni.uploadFile({ name: 'avatar'|'logo', filePath })`，form 字段名与后端 serializer 一致；
  - 多图上传（发帖/商品）：见 4.6 专项方案。

### 4.4 用户状态 stores/user.js

- 平移 userInfo / accessToken / refreshToken 三态与 `isLoggedIn / isMerchant / isAdmin` getter（isMerchant/isAdmin 本期几乎不用，保留以对齐结构）。
- Storage 从 localStorage 换成 `uni.setStorageSync/getStorageSync/removeStorageSync`，键名与 Web 一致（user_info / access_token / refresh_token）。
- `login` 改为 `loginByWechat(code)`；保留 `logout`（先调后端拉黑 refresh 再本地清理）与 `clearLocalAuth`。

### 4.5 业务常量沉淀

新建 `miniprogram/src/constants/`：

- `statusMaps.js`：预约状态机（pending/confirmed/in_service/completed/reviewed/rejected/cancelled）、商品四态（on_sale/reserved/sold/off_shelf）、商家入驻状态（pending/approved/rejected）的中文映射与颜色；
- `enums.js`：板块类型、排序选项、举报原因等枚举。

内容以 `frontend/src` 各视图中现存定义为蓝本收编（MyBookingsDrawer.vue、ServiceDetail.vue、MerchantDetail.vue、ProductList.vue、ProductDetail.vue 共 5 处重复定义），**本次只在小程序侧落地，不回头改 Web**。

### 4.6 多图上传专项方案（关键技术风险，MP4 首个 spike）

后端约定：发帖/商品的 `images` 是一次 multipart 请求中的多个同名文件字段（DRF `ListField(child=ImageField, max_length=9)`，update 时全量替换 ≤9 张）。

而微信小程序 `wx.uploadFile` 每次只能传单个文件，无法原生满足"一次请求多文件"。方案：

1. **首选（纯客户端，零后端改动）**：封装 `utils/upload.js` —— 使用 `wx.request` + 手工构造 `multipart/form-data` 报文（ArrayBuffer 拼 boundary，业界成熟做法约 60 行），在一个请求中写入 N 个 `images` part + 其余文本字段；
2. Spike 验收：在真实小程序环境对「发帖」走通 3 张图发布 + 详情页回显，再用 curl 复核后端落盘路径符合 `media/{folder}/{YYYYMM}/{uuid}.ext`；
3. 若 spike 证实手工报文不可靠，启用备选：讨论是否新增后端独立上传端点（涉及序列化器契约调整，需单独评审，不在 MP0 范围）。

头像/营业执照类单图场景不受影响，直接 `uni.uploadFile` 即可。

---

## 五、页面设计与 tabBar

### 5.1 TabBar（5 个）

| Tab | 页面 | 内容 |
|-----|------|------|
| 首页 | pages/home/index | 板块入口宫格 + 公告列表 |
| 邻里圈 | pages/posts/list | 自由发言流（问答从首页/此页顶部入口进入二级页） |
| 二手市场 | pages/products/list | 分类筛选 + 价格排序 + 搜索 |
| 服务圈 | pages/services/index | 「家政服务 / 周边商家」双分段切换 |
| 我的 | pages/profile/index | 资料、我的预约、我的商品、退出登录 |

### 5.2 页面清单（17 页）

| 页面 | 承接的 Web 来源 | 主要 API（函数级对应 frontend/src/api） |
|------|----------------|----------------------------------------|
| home/index（Tab） | HomeView | admin.getAnnouncements + 板块入口跳转 |
| auth/login | LoginView 改造 | auth.wechatLogin；游客模式提示（各板块可浏览，写操作引导登录） |
| profile/index（Tab） | ProfileView | auth.getProfile / updateProfile（头像单图 uploadFile）/ logout |
| posts/list（Tab） | PostList | discussion.list / like |
| posts/detail | PostDetail | detail / comments(GET/POST) / like；自己的帖可删 |
| posts/create | PostCreateDialog → 独立页 | createPost（多图 spike 场景①） |
| qa/list | QuestionList | qa.list / like |
| qa/detail | QuestionDetail | detail / addAnswer / acceptAnswer（提问者可见）/ like |
| qa/create | QuestionCreateDialog → 独立页 | create |
| products/list（Tab） | ProductList | list / categories / changeProductStatus（本人商品快捷操作） |
| products/detail | ProductDetail | detail / addProductComment；卖家显示状态操作 |
| products/create-edit | ProductCreateDialog → 独立页 | create/update（多图 spike 场景②，≤9 张） |
| products/mine | （Web 内嵌于列表筛选）→ 独立页 | list + `mine` 过滤参数或本地过滤，状态机操作 |
| services/index（Tab） | ServiceList + MerchantList 合并 | housekeeping.categories / providers.list；merchants.list / merchant-categories |
| merchants/detail | MerchantDetail（只读化裁剪） | getDetail / activities / reviews(GET/POST 发表评价) |
| housekeeping/detail | ServiceDetail（居民视角） | providers.detail / bookings.createBooking |
| bookings/my | MyBookingsDrawer（居民视角） | listBookings / cancelBooking；状态机展示用 constants.statusMaps |

**明确不做**（Web 端职责或后续迭代）：管理员置顶/加精按钮、商家/服务商审核条、入驻申请与我的店铺管理、服务商订单流转操作、公告管理、统计页。

---

## 六、里程碑划分

| 里程碑 | 内容 | 估时 | 验收标准 |
|--------|------|------|----------|
| **MP0 后端微信登录** | openid 字段迁移、WechatLoginView、settings/env、测试 | 1~1.5 人日 | apps.users 测试全绿；curl 走通 mock code2session |
| **MP1 工程搭建** | uni-app 脚手架、tabBar 骨架、request shim、stores、api 平移、constants | 1 人日 | 开发者工具中骨架页可跑；mock 数据下 request 刷新/401 链路与 Web 行为一致 |
| **MP2 登录与个人中心** | 静默登录流程、游客态、资料查看/编辑（头像上传）、登出 | 0.5~1 人日 | 冷启自动登录；编辑资料头像可换 |
| **MP3 邻里圈 + 问答** | 帖子/问答 共 6 页（列表、详情、发布）+ 评论点赞采纳 | 2~2.5 人日 | 对应 Web 功能点逐条过检（DIS/QA 模块 P0 项） |
| **MP4 二手市场** | 多图上传 spike、4 页、状态机、留言 | 1.5~2 人日 | 三图发帖与九图商品发布/编辑均成功且图序正确 |
| **MP5 服务圈** | 商家浏览+评价、家政详情+预约、我的预约（居民视角） | 2~2.5 人日 | 预约创建/取消走通；取消在 confirmed 前受限规则与后端一致 |
| **MP6 首页与公告** | 板块宫格、公告展示 | 0.5 人日 | 公告可见、各入口跳转正确 |
| **MP7 联调与真机** | 58 接口对照联调、真机回归、错误态与弱网体验 | 1~1.5 人日 | 联调清单全绿；主流机型无致命 UI 问题 |
| **MP8 合规提审** | 合法域名配置、隐私指引、类目材料、体验版评审 | 0.5 人日 | 提审通过或仅有一次性整改意见 |
| **合计** | | **≈10~14 人日**（单人） | |

依赖关系：MP0 ∥ MP1 可并行；MP2→MP3→MP4→MP5→MP6 顺序执行保证风格一致；MP7/M8 收尾。

---

## 七、联调与发布要求（MP7-MP8）

### 7.1 联调方法

以 `frontend/src/api/*.js` 的 58 个函数为全集建立核对表，居民端范围的每一项标注「已联调 ✓」，确保路径、参数名、multipart 字段名逐一与后端 router.register/@action 实际 URL 一致（项目 Definition of Done 要求）。

### 7.2 部署与合规

- 微信公众平台配置 **request 合法域名 + uploadFile/downloadFile 合法域名** = 线上 HTTPS 域名（与 Web 同域，nginx 证书自然覆盖）；
- `deployment.md` 增补章节：小程序域名白名单、`WECHAT_MINIAPP_*` 环境变量、nginx 无需变更的说明；
- 后台完善「用户隐私保护指引」（声明收集头像/昵称用途），否则涉及隐私接口的页面无法过审；
- 类目：以「生活服务/社区服务」类目提交，若审核要求补充材料按平台指引处理。

---

## 八、业务不变量遵守清单（回归必查）

| 不变量 | 小程序端的落实点 |
|--------|------------------|
| Booking 状态机 pending→confirmed→in_service→completed→reviewed，cancelled 终态 | bookings/my 页仅暴露居民合法动作（pending 时可改可删可取消等由后端裁决，前端只发请求并回显） |
| 二手 images 全量替换 ≤9 张 | 编辑页始终回填旧图 + 新选图一并提交，上限 9 张硬控 |
| 商品/帖子 status 对 serializer 只读，走专用 @action | 全部经 changeProductStatus 等 action 函数调用，不尝试 PUT status 字段 |
| 注册固定 resident，忽略请求 role | 小程序不提供 role 入口；静默注册也不显式传 role |
| 登出走 POST /auth/logout/ 拉黑 + 双清 store/localStorage | stores/user.logout 与 401 路径均双清 |
| 列表一律分页，get_is_liked 依赖 prefetch | 分页参数沿用 page/page_size；滚动加载下一页而非改后端查询 |

---

## 九、风险与对策

| 编号 | 风险 | 等级 | 对策 |
|------|------|------|------|
| R1 | 微信小程序多文件上传与后端 ListField 的兼容性 | 高 | MP4 首 spike 验证手工 multipart 方案；备选方案需二次评审 |
| R2 | 静默注册导致 Web 密码账号与微信账号身份割裂 | 中 | 本期接受并在登录页注明；后续迭代可加"绑定已有账号"接口（openid 挂靠现用户） |
| R3 | 小程序类目/资质审核不通过 | 中 | 提前在 MP1 申请小程序账号与类目，材料并行准备 |
| R4 | WECHAT_MINIAPP 配置缺失导致线上登录不可用 | 低 | 启动健康检查不阻断，但 wechat-login 返回明确错误码 + ERROR 日志 |
| R5 | access/refresh 两端并存时的 token 轮换互踢 | 低 | 两端各自持有独立 token 对（不同登录会话），refresh 轮换按会话隔离，无冲突；禁止单账号一端多用同一 refresh |
| R6 | 小程序包体积超限（uni-ui 全量引入） | 低 | 按 easycom 按需引入、图片走 CDN/media 直链、分包非核心页 |

---

## 十、关联文档

- 需求：[PRD.md](../requirements/PRD.md)（「后续规划」章节）、[feature-list.md](../requirements/feature-list.md)（61 功能点对照）
- 架构：[architecture.md](../design/architecture.md)、[tech-stack-recommendation.md](../design/tech-stack-recommendation.md)（JWT 选型预留小程序的原始依据）
- 部署：[deployment.md](../delivery/deployment.md)（HTTPS 反代基线，MP8 增补小程序章节）
- 主站排期：[milestone-plan.md](milestone-plan.md)
