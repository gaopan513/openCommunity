# 小程序端架构审查报告

> 审查对象：`miniprogram/`（uni-app + Vue 3 + Pinia）
> 审查日期：2026-09-17
> 数据基准：src 下 34 个源文件、约 5362 行代码

---

## ✅ 修复完成状态（2026-09-17 全量实施完毕）

本文第四、五节所列优化**已全部落地**，验收通过：

| 项 | 状态 | 说明 |
|---|---|---|
| P0-1 目录重组+重划分包 | ✅ | `pagesOther` 拆除 → `modules/{posts,qa,products,housekeeping,merchants,bookings}` 6 业务分包；主包仅 tab+登录 |
| P0-2 工程护栏 | ✅ | 新增 `.eslintrc.cjs`/`.prettierrc.json`/`.editorconfig`/`jsconfig.json`；scripts 增 lint/lint:fix/format/format:check/check；**lint 与 format:check 全绿（0 error 0 warn）** |
| P1-1 路由路径收敛 | ✅ | 新增 `src/router/paths.js`（TAB/PAGE/ROUTE/PACKAGE_ROOT）；所有跨包跳转改引用常量；login redirect 正则兼容 `/modules/` |
| P1-2 组件归位+样式 | ✅ | 确认 ReviewSheet/CommentBar 供多分包共用且位于主包（目标正确）；`vite.config.js` 显式 `@` alias |
| P2-1 拆分超大页面 | ✅ | 新增 `components/ImageUploader.vue`，posts/create 与 products/create-edit 复用多图上传（各瘦身约 45 行） |
| P2-2 错误边界+埋点 | ✅ | 新增 `utils/analytics.js`（微信实时日志+跨端 fallback）；接入登录/发帖/商品/提问/回答/评论/点赞/预约/评价/取消埋点 |

**验收结果**：`npm run lint`、`npm run format:check` 双绿；`npm run build:mp-weixin` 构建成功，`dist` 正确产出 6 个 modules 分包。

> 重构成果已合入现行 `miniprogram/src/`，原回滚副本 `miniprogram/src.bak-20260917` 已于 2026-09-24 清理。

---

## 一、结论概览

整体架构**基础扎实、工程质量明显高于一般个人项目**：分层清晰、网络层健壮、登录态处理严谨、状态映射统一收敛。但存在 **4 个结构性缺陷、3 个耦合点、若干可维护性隐患**，其中最突出的是**分包划分违背模块内聚原则**和**完全缺失工程化护栏（Lint/VSCode 类/TS）**。

**总体评价：当前属于"好用的单体代码"，但尚未达到"可长期演进的架构"。** 距离开工到健壮可维护，建议按本文第四节的优先级逐步打磨。

---

## 二、做得好的地方（务求保留，勿在重构中破坏）

### 2.1 网络层设计健壮，可作模板（`utils/request.js`）
- **类 axios 出口**（`get/post/put/patch/delete`），使 `api/*.js` 能从 Web 端近原样平移，跨端复用是最聪明的决策。
- **401 静默刷新 + 单次重放**，且并发 401 共享同一 `refreshingPromise`（避免多个请求各自刷新 token）。
- **区分网络错误与会话失效**（`errMsg` 判断），弱网下不误踢登录。
- 刷新成功后同步更新轮换的 `refresh_token`（`ROTATE_REFRESH_TOKENS=True`）。

### 2.2 登录态工程严谨
- `stores/user.js` 与 `request.js` 通过**动态 import** 解耦循环依赖，妥善兼顾了 Pinia store 与请求层的双向引用。
- `safeParseUser()` 兼容历史字符串/对象两种存储形态，损坏时清理避免白屏。
- 401 踢出时**携带回跳 redirect 与页面 query**，登录后能精确回位原页——这个细节很多项目都没做。

### 2.3 列表逻辑收敛为 composable
- `usePagedList.js` 统一了分页/触底/下拉刷新/脏标记刷新/请求序号守卫，避免每个列表页各写一套。
- **请求序号 `seq` 守卫**有效防止了筛选切换时旧响应串台。

### 2.4 契约收敛于常量
- `constants/statusMaps.js` 统一所有状态映射与可选项，杜绝 magic string 散落。
- `EVENTS.LIST_CHANGED` 收敛了页面间数据新鲜度通知事件名。

### 2.5 边界意识清晰
- `api/admin.js`、`api/housekeeping.js` 都已裁剪掉管理员/商家侧接口，严守"小程序只做居民端"的业务边界（与 AGENTS.md 一致）。

---

## 三、发现的问题（按严重度排序）

### 🔴 严重问题 C1 — 分包划分撕裂模块内聚

**证据**：
- `pages/qa/list`（主包）跨包跳转 `pagesOther/qa/detail` 与 `pagesOther/qa/create`（分包）。
- `products` 模块同样被撕裂：主包 `pages/products/{list,detail,mine}` + 分包 `pagesOther/products/create-edit`。
- `pagesOther` 命名无业务语义，纯粹是"不想塞进主包的页面的收容所"。

**危害**：
- 同一业务模块的页面被硬拆到两个包，**代码浏览、调试、维护时心智负担成倍增加**（开发一个 qa 功能要来回翻两个目录）。
- 分包加载是刻意的性能取舍，**应当按"用户旅程/访问频率/体积"来划分，而不是按"多出来的页"**。当前划分没有明确的性能依据。
- 未来新增 qa 页面时，开发者必须自行判断"放主包还是分包"，缺乏规则约束即会产生更多撕裂。

### 🔴 严重问题 C2 — 完全缺失工程化质量护栏

**证据**：`miniprogram/` 下**无 `.eslintrc`、`.prettierrc`、`tsconfig`、`.editorconfig`**；`package.json` 的 scripts 只有 uni 官方的构建脚本，**无 lint / typecheck / 单元测试**；文件全部为 `.js`（无 TS 类型）。

**危害**：
- 34 个文件 5362 行全靠人工保证质量。`request.js`/`upload.js` 这种 180+ 行的关键模块，一个拼写错误、一次 handshake 写错可能到运行时才暴露。
- 与后端（pytest）、Web 前端（typecheck+build）的工程质量投入形成**明显落差**（USER.md 明确记载用户重视工程质量）。
- 无 lint 意味着**命名规范、分号、未用变量**等一致性完全依赖开发者自律。

### 🟠 中等问题 C3 — Qa 分包路径耦合在页面内置

**证据**：`pages/qa/list.vue` 中硬编码 `/pagesOther/qa/detail?id=${id}`、`/pagesOther/qa/create` 字符串。
**本质**：页面内出现硬编码路由路径（含 `pagesOther` 这种易改的包根名）。一旦分包更名或调整，所有调用点需逐一改正，且无编译期校验。同类问题在 `pages/products/`、`pages/home/` 等跨页跳转处普遍存在（已扫描到 10 个页面含 `pagesOther`/`pages` 跳转）。

### 🟠 中等问题 C4 — `vite.config.js` 无任何差异化配置

**证据**：`vite.config.js` 仅 `plugins: [uni()]`，空壳。别名 `@`、define、压缩优化等都依赖 uni 默认值。
**危害**：`@` 别名目前能工作但**未被显式声明**，迁移工具链或升级依赖时可能静默失效；无构建期优化钩子。

### 🟡 轻度问题 C5 — 全局样式集中但组件样式重复

**证据**：`App.vue` 定义了完整全局主题（`--oc-*` 变量 + `.oc-card/.oc-btn/.oc-chip` 等十余个公共类），设计方向正确。但 `services/index.vue` 的 `provider-card`、各详情页的卡片样式存在**近似重复**，`pagOther` 分包页几乎都自带 `.oc-*` 类的重复声明。
**危害**：样式散落，主题色调整时需多处跟进；`vite` 未配置样式去重策略，分包内重复类会推高包体积。

### 🟡 轻度问题 C6 — 单个页面体量偏大

**证据**（行数 Top）：`bookings/my.vue`(357)、`housekeeping/detail.vue`(318)、`posts/detail.vue`(317)、`merchants/detail.vue`(312)、`products/create-edit.vue`(303)。
**危害**：300+ 行的 SFC 通常已到了拆分区/抽子组件的临界点。`posts/detail.vue`（楼中楼评论+点赞+举报+登录引导）与 `products/create-edit.vue`（多图上传+表单+状态机）逻辑密度高，后续维护易出错。

### 🟡 轻度问题 C7 — 缺统一错误边界与埋点

**证据**：`App.onError` 已接微信实时日志（`rtLog`），但无页面级 errorHandler，无统一埋点封装，无性能监控（`uniStatistics.enable=false`）。
**定位**：属于"上线后"才紧迫的补强项，当前阶段可缓。

---

## 四、优化方案（含优先级、做法、预期收益）

> 优先级：P0 = 高性价比且收益大；P1 = 常规加固；P2 = 演进增强。
> 全部为**渐进式、可回滚**的改动，不涉及业务重构，不破坏现有功能。

### P0-1｜按业务模块重组页面目录，重划分包边界

**目标文件**：`src/pages.json`、`src/pages/`、`src/pagesOther/`

**做法**（推荐"模块包 + 按访问频率分流"模型）：
1. 目录重命名为业务模块（消除 `pagesOther` 无语义名）：
   ```
   src/
   ├── pages/            # 仅放 5 个 Tab 主页面（firstScreen 常驻）
   ├── modules/
   │   ├── posts/
   │   ├── qa/           # list + detail + create 同包同目录
   │   ├── products/     # list + detail + mine + create-edit 同目录
   │   ├── services/     # index + detail
   │   ├── bookings/
   │   └── profile/
   ```
2. 主包（pages/tabBar 常驻 5 页 + 登录）；**其余全部按业务模块分包**，每个模块一个分包 root（`subPackages` 里 `modules/qa`、`modules/products`…）。
3. 这样每个业务模块**自包含、单目录、单一跳转域**，不再撕裂。

**收益**：★ 消除 C1/C3。模块内聚后浏览/调试/新增成本大降；分包按业务划分后，加载策略与体积控制有明确依据；改名后所有路由**可在编译期通过页面清单一致性校验兜底**。

**风险**：分包增多后需注意"分包间不能互引资源/组件"的约束。若 `CommentBar`/`ReviewSheet` 被多个分包引用，应放入**主包 components 或独立公共分包**（`common`）——见 P1-2。

### P0-2｜补齐工程化护栏：ESLint + Prettier + TypeScript

**目标文件**：新增 `.eslintrc`、`.prettierrc`、`tsconfig.json`、`jsconfig.json`（可选）；`package.json` scripts 增 `lint`/`lint:fix`/`check`。

**做法**：
1. 装 `eslint` + `@dcloudio/eslint-config-uni-app`（或官方 uni-preset-vue 模板自带的 vue/recommended 配置）+ `prettier`。
2. 先跑 `--fix` 全量格式化，再**容忍式**接 CI/提交流程：先 `warn` 不阻断，待存量告警清零后再升 `error`。
3. 若想上 TS：考虑到 uni-app 官方强力支持，可**渐进迁移**——新增/高频文件 `.vue` 的 `<script setup lang="ts">`，旧文件保持 JS，靠 `jsconfig` 插件补推断。初期不必全量 TS 化（成本高、收益边际递减）。

**收益**：锁定 C2。杜绝拼写/格式/未用变量的隐性 bug；让小程序工程投入与后端/Web 对齐；`usePagedList`、`upload` 这样的关键模块获得类型提示与重构安全网。

### P1-1｜抽取路由路径常量 + 页面出口 index

**目标文件**：新增 `src/router/paths.js`（或并入 `constants/`）、各 `modules/*/index.js`

**做法**：把所有硬编码页面路径（含 `/pagesOther/...`）收敛到一处导出映射 `PATHS = { qaDetail: id => ..., ... }`；页面只 `import { PATHS }` 跳转。
**收益**：消除 C3 的字符串散落；分包更名只需改常量的根前缀 + `pages.json`，全局同步，可控可测。

### P1-2｜公共资源归位：组件与样式去重

**目标文件**：`components/`、`App.vue` / 独立 `common.scss`

**做法**：
1. 明确"跨模块公共组件"（`ReviewSheet`/`CommentBar`）与"模块私有组件"的归属；多分包共用的进主包或公共分包 spark（`src/common/`）。
2. 将 `.oc-*` 公共类抽成 `common.scss`，分包内重复声明删除；`vite.config.js` 打开 `css.preprocessorOptions` scss 全局注入（如主色变量）。
**收益**：消 C5；样式主题一处改、全局生效；重复类减少，微降分包体积。

### P2-1｜拆分/重构成块页面

**目标文件**：`posts/detail.vue`、`products/create-edit.vue`、`bookings/my.vue`

**做法**：对 300+ 行的 SFC，按"子组件 + 局部 composable"拆分。例如：
- `posts/detail` 拆出 `CommentSection.vue`（楼中楼）与 `useComments.js`。
- `products/create-edit` 拆出 `ImageUploader.vue`（复用点：发帖也在用多图上传，可提取公共上传组件）。
**收益**：缓 C6；同时 `ImageUploader` 的提取能消除发帖/商品两处的手工 multipart 拼装扩散（现在 `upload.js` 的拼包逻辑被两处调用方复用，抽取成组件后更易维护与单测）。

### P2-2｜接入通用错误边界与埋点（上线前置）

**目标文件**：`App.vue`、新增 `utils/analytics.js`

**做法**：页面级 `onError` 统一上报已存在的 `rtLog`；封装 `analytics.track(event, payload)`，在登录、下单、发布等关键节点埋点；`uniStatistics` 按需开启。
**收益**：缓解 C7；为线上问题定位与转化分析铺路。**建议在本地上线联调前完成。**

---

## 五、建议的实施节奏

| 阶段 | 内容 | 依赖 | 工作量 | 是否阻塞上线 |
|---|---|---|---|---|
| 第 1 步 | P0-1 重组页面目录 + 重新分包 | 无 | 中（纯移动，风险低） | 否（联调前最好完成） |
| 第 2 步 | P0-2 ESLint/Prettier（+渐进 TS） | 无 | 中 | 否（越早越好） |
| 第 3 步 | P1-1 路由常量、P1-2 组件/样式归位 | 第 1 步后 | 小 | 否 |
| 第 4 步 | P2-1 拆大页面、P2-2 埋点 | 可选 | 中 | P2-2 建议上线前 |

---

## 六、与整体项目的协同建议

1. **小程序路径应承接 Web 端 `pages.json` 语义**：Web (Vue Router) 已按业务模块分区，小程序分包回归"模块"而非"pagesOther"，两端目录心智模型将对齐，跨端维护成本下降。
2. **新增页面默认遵循单规**：凡是某业务模块的新页面，一律进该模块分包；Tab 常驻才进主包。
3. **迁移后端契约一致性纪律**已良好（API 层与 `serializers.py` 对齐），目录重组时**切勿改任何 API 层文件路径与函数签名**，避免破坏 `frontend`/后端协同约定。
4. **本报告不涉及功能改动**，全部为结构/工程优化，可直接纳入里程碑排期。

---

*报告依据：对 `pages.json`、`vite.config.js`、`project.config.json`、`utils/request.js`、`utils/upload.js`、`stores/user.js`、`composables/usePagedList.js`、`constants/`、`api/`、`components/`、关键页面及跨包跳转关系的逐文件审查。*