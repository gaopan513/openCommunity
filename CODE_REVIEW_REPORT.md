# openCommunity 全量代码审查报告

> 审查日期：2026-08-06　|　审查方式：双 Agent 全量走查 + 人工关键路径核验 + 自动化基线验证
> 代码规模：后端 70 个源码文件（约 6,000 行）/ 前端 37 个源文件（约 8,700 行）

## 修复状态（2026-08-07 全部修复完成）

✅ 第一批（10 项）：P0-1、P1-2、P1-3、P1-4、P1-5、P1-6、P1-7、P2-8、P2-9、P2-10
✅ 第二批（13 项）：P2-11 ~ P2-19、P3-20、P3-21、P3-24、P3-25
✅ 第三批（2 项，方案 A）：
- **P3-22** 角色信任链：注册固定 resident（忽略 role 字段）；入驻申请放开为任意登录用户；审核通过时自动授予 merchant 角色（merchants/housekeeping 两个 audit）；前端注册页移除角色单选、入驻入口去掉角色门槛。**商家身份从此只能由审核授予**。
- **P3-23** Element Plus 按需引入：`unplugin-vue-components` + `unplugin-auto-import` + `ElementPlusResolver`；main.js 移除全量注册与全量 CSS，仅注册实际用到的 24 个图标；App.vue 用 `el-config-provider` 提供中文 locale。**主 JS chunk 768.6 kB → 239.0 kB（gzip 243 → 85.6 kB），CSS 368.4 → 76.4 kB，500kB 警告消除**。

**修复后验证**：`manage.py test` **142 用例全绿**（较修复前 +5）、`makemigrations --check` 无缺失、前端 `vite build` 成功（无 chunk 警告）、冒烟验证通过
（弱密码/非法图片拦截 ✓ / qa is_liked ✓ / pending 商家匿名 404 ✓ / 帖子详情 104→6 次查询 ✓ /
媒体删除信号清理物理文件 ✓ / 改密后旧 refresh 拉黑 ✓ / 禁用用户与密码错误统一 401 ✓ /
审核通过自动授予商家角色 ✓ / 注册角色字段被忽略 ✓）

## 一、验证基线（已实际执行）

| 项目 | 结果 |
|---|---|
| 后端测试 `python manage.py test` | ✅ 137 个用例全部通过（89s），系统检查 0 问题 |
| 前端构建 `vite build`（独立输出目录） | ✅ 构建成功，仅有 chunk > 500kB 警告 |
| 前端 API 路径与后端路由对齐 | ✅ 7 个 API 模块 58 个端点全部对齐，无 404 隐患 |
| XSS / 调试残留扫描 | ✅ 无 `v-html`、无 `console.log`、无 `TODO/FIXME` |

## 二、问题清单（按严重程度）

### 🔴 P0 严重（1 条，必须修）

1. ✅ **部署安全默认值全线放行**
   `backend/config/settings.py:22-31, 219`
   SECRET_KEY 明文硬编码兜底（`django-insecure-...`）+ `DEBUG` 默认 `True` + `ALLOWED_HOSTS='*'` + `CORS_ALLOW_ALL_ORIGINS=True`。任何"直接起服务"的部署都会导致：DEBUG 信息泄露 + JWT 密钥可伪造（签名密钥已知可签发任意身份 token）。虽然注释有警告，但默认值本身是定时炸弹。
   → **建议**：启动时强制校验 `DJANGO_SECRET_KEY` 存在（缺则拒绝启动），DEBUG/ALLOWED_HOSTS/CORS 默认取安全值。

### 🟠 P1 高（6 条，应尽快修）

2. ✅ **`AnswerViewSet` 缺少对象级权限（潜在 IDOR）**
   `backend/apps/qa/views.py:199-274`
   该 ViewSet 的 `update/destroy` 未像 `QuestionViewSet` 那样挂 `IsOwnerOrAdmin`，任何登录用户可改/删任意回答。当前因 `qa/urls.py` 未注册该路由而"不可达"，但代码是隐患。
   → **建议**：删除该死代码，或补上 `get_permissions` 权限分发后注册。

3. ✅ **帖子详情页 N+1 查询（约 120+ 次 SQL）**
   `backend/apps/discussion/serializers.py:101-104`（`get_comments`）+ `:35-40`（`get_replies`）
   详情页取 20 条顶级评论，每条再查 replies → 单次请求约 140 次查询。qa/merchants/housekeeping 详情页存在同类问题（`recent_reviews`/`get_reviews` 等）。
   → **建议**：`prefetch_related('comments__replies__author')` 或序列化器直接基于预取数据组装。

4. ✅ **图片大小/扩展名校验器全项目零引用**
   `backend/common/validators.py:63`（`validate_image`）
   定义了 5MB 大小限制 + jpg/png/webp 白名单，但 **7 个模块的所有 ImageField/序列化器都没有接入**（仅 Pillow 校验"是合法图片"+ 全局 10MB 上限）。与 AGENTS.md「图片大小/格式校验在 common/validators.py」的约定不符。
   → **建议**：在 `PostCreateSerializer`、`ProductCreateSerializer`、`MerchantApplySerializer`、`ServiceProviderApplySerializer` 的图片字段挂 `validate_image`。

5. ✅ **密码强度校验器未接线**
   `backend/config/settings.py:118-132` + `backend/apps/users/serializers.py:15-20` + `backend/apps/users/views.py:153-154`
   `AUTH_PASSWORD_VALIDATORS` 配了 4 个校验器（CommonPassword/NumericPassword 等），但注册和改密都只手动查了长度（`min_length=6` / `len() < 6`），未调用 Django 的 `validate_password()`，校验器形同虚设。
   → **建议**：`RegisterSerializer` 与 `ChangePasswordView` 中调用 `django.contrib.auth.password_validation.validate_password`。

6. ✅ **部分模块 update/destroy 绕过统一响应格式**
   `backend/apps/discussion/views.py`（PostViewSet）、`backend/apps/qa/views.py`（QuestionViewSet）、`backend/apps/merchants/views.py`（MerchantViewSet）未重写 update/destroy，DRF 默认返回裸 `serializer.data`（无 `{code, message, data}` 包装）；与 housekeeping/secondhand 的实现不一致，违反项目强制约定。
   → **建议**：统一补 `update/destroy` 包装（或全局自定义 `GenericAPIView.update` 兜底）。

7. ✅ **问答点赞状态无法回显**
   `frontend/src/views/qa/QuestionDetail.vue:31` 读取 `res.data.is_liked`，但后端 `QuestionListSerializer`/`QuestionDetailSerializer`（`backend/apps/qa/serializers.py:44-85`）均未定义 `is_liked` 字段 → 恒为 `undefined`，进详情页看到的是未点赞态，实际已点赞。（discussion 模块的 `PostListSerializer`/`PostDetailSerializer` 有该字段，正常。）
   → **建议**：qa 序列化器补 `is_liked`（参照 `AnswerSerializer:26-41`）。

### 🟡 P2 中（12 条，建议排期修）

8. ✅ **商家详情泄露待审核信息与营业执照**
   `backend/apps/merchants/views.py:80-93`
   `get_queryset` 仅对 `list` 过滤 `approved`，`retrieve` 返回**全部状态**的商家（含 `pending`），`MerchantDetailSerializer` 含 `license_image/status` → 匿名用户可枚举 ID 查看待审商家的营业执照图片。（对比 housekeeping 的 `ServiceProviderViewSet` 对 retrieve 也过滤状态，行为不一致。）
   → **建议**：retrieve 同样只放行 approved，或仅放行本人/admin。

9. ✅ **被拒商家无法重新提交入驻申请**
   `backend/apps/merchants/views.py:152`（`hasattr(user, 'merchant_profile')` 即拒绝重复申请）；`backend/apps/housekeeping/views.py:136` 同理。审核被拒后用户永远不能再申请，只能管理员在后台改，业务上走不通。
   → **建议**：仅当存在 `pending` 记录时拦截；`rejected` 允许重新提交（覆盖旧记录或开放 update）。

10. ✅ **服务商列表 N+1（每页 40+ 次查询）**
    `backend/apps/housekeeping/serializers.py:78-87`
    `get_categories` 与 `get_service_count` 对列表内每个 provider 各发一次查询（分页 20 条 → 40+ SQL）。`MerchantListSerializer`/`ProductListSerializer` 若含类似 SerializerMethodField 也需检查。
    → **建议**：`prefetch_related('services__category')` + 聚合计数。

11. **点赞/取消点赞并发下计数可能为负**
    `backend/apps/discussion/views.py:126`、`backend/apps/qa/views.py:191,268`
    取消点赞用 `F('like_count') - 1`，并发重复取消或表数据异常时计数可跌穿 0，且与 like 表失去一致性。
    → **建议**：计数改为基于 `PostLike` 表实时统计或加事务/唯一约束兜底。

12. **`feature` 接口布尔值未校验**
    `backend/apps/discussion/views.py:195-198` 直接 `post.is_top = request.data['is_top']`，传入字符串 `"false"` 会被 Python 判定为 truthy。
    → **建议**：用 `serializers.BooleanField` 校验后再赋值。

13. **登录接口存在用户枚举**
    `backend/apps/users/views.py:78-83` 对已禁用账号返回「账号已被禁用」，对不存在账号返回「用户名或密码错误」→ 攻击者可探测账号状态。
    → **建议**：统一返回「用户名或密码错误」。

14. **修改密码后旧 token 依然有效**
    `backend/apps/users/views.py:160-161` 仅 `set_password`，未轮换/拉黑 JWT；前端也提示"请重新登录"但旧 access token 2 小时内仍可用。
    → **建议**：配合 SimpleJWT 黑名单（settings 已启用 `token_blacklist`）将当前 refresh 加入黑名单。

15. **媒体文件删除残留**
   各模块 `destroy` 仅删数据库记录，物理图片留在 `media/`（无信号清理）。长期运行会积累孤儿文件。
    → **建议**：用 `post_delete` 信号删除文件（注意仅删本字段文件，勿误删复用图）。

16. **前端 401 处理丢 redirect + 并发重复弹窗**
    `frontend/src/utils/request.js:54-65`：清 token 后直接 `router.push('/login')`，未携带当前路径（用户登录后回不到原页面）；多个并发 401 会弹多个「登录已过期」。
    → **建议**：跳转带 `?redirect=`，并用全局 flag 防抖。

17. **user_info JSON 解析无兜底**
    `frontend/src/stores/user.js:12` `JSON.parse(localStorage.getItem('user_info') || 'null')` 在缓存损坏时抛异常 → 应用白屏。
    → **建议**：`try/catch` 包裹并回退 `null`。

18. **Token 存 localStorage 且 refresh 链路未实现**
    `frontend/src/stores/user.js:51-53` + `frontend/src/api/auth.js:28`：access 2h 过期直接踢回登录页，refresh_token 保存但从未使用；XSS 场景下 token 可被读取。
    → **建议**：接入 401 后静默 refresh 再重放请求（拦截器内实现）；安全要求高时换 HttpOnly Cookie。

19. **`ServiceDetail.vue` 空值保护缺失**
    `frontend/src/views/housekeeping/ServiceDetail.vue:114` `provider.name.charAt(0)` 在 name 为空时抛错（一般不会但缺防御）。

### 🟢 P3 低（代表性条目）

20. **列表页 `page` 参数可致 500**
    `backend/apps/merchants/views.py:126` `int(request.query_params.get('page', 1))` 直接强转，`?page=abc` → ValueError → 500（DRF 自带分页器可安全处理，此处手动解析绕过了）。
21. **`destroy` 状态码不一致**
    `backend/apps/secondhand/views.py:125` 删除商品返回 200 `success_response`，其余模块为 204 `no_content_response`。
22. **注册接口允许自封 merchant 角色**
    `backend/apps/users/serializers.py:30-34` 仅拦截 admin，`role=merchant` 可随意注册（配合第 9 条，商家权限链薄弱，建议确认业务预期）。
23. **前端包体积警告**
    `vite build` 报 chunk > 500kB（Element Plus 全量引入），建议按需引入/路由级代码分割。
24. **死代码与未使用导出**
    `frontend/src/api/auth.js` 的 `refreshToken`、`discussion.js` 的 `getComments`、`secondhand.js` 的 `getProductComments` 等当前无调用方。
25. **评论内容长度未受后端约束**：`discussion` 评论走 `Comment.objects.create` 手动创建，未用 serializer 校验 `max_length`。

## 三、亮点（值得保持）

- **状态机设计统一**：housekeeping `Booking` 的 `valid_transitions` + 权限/状态双重校验、secondhand 商品状态流转，规则清晰、可读性强。
- **对象级权限体系**：`IsOwnerOrAdmin`/`IsOwnerOrReadOnly` + `get_object()` 按 action 分流（审核走全量、展示走过滤），模块间有意识的一致。
- **统一响应与异常**：`common/response` + `common/exceptions` 兜底非 DRF 异常为 500 JSON（避免前端解析 HTML），设计完整。
- **F() 原子计数**：浏览量与点赞计数用 `F` 表达式，避免读改写竞态。
- **序列化器只读字段防绕过**：`QuestionListSerializer`/`PostListSerializer`/`BookingSerializer` 对敏感字段（状态/计数/归属）强制只读并附注释，防止越权篡改。
- **前端工程质量**：无 XSS 渲染点、统一走 request 实例、API 路径全部对齐、无调试残留。
- **测试覆盖完整**：137 用例覆盖 7 模块 CRUD/权限/状态流转，当前全绿。

## 四、测试覆盖总结

| 模块 | 用例数 | 覆盖要点 |
|---|---|---|
| users | 21 | 注册/登录/禁用/资料/改密/权限 |
| discussion | 18 | 发帖/评论/点赞/置顶加精/权限 |
| qa | 10 | 提问/回答/采纳/点赞/权限 |
| secondhand | 33 | 发布/筛选/状态流转/留言/权限 |
| merchants | 9 | 入驻/审核/活动/评价/回复 |
| housekeeping | 36 | 入驻/预约/状态流转/评价/权限 |
| admin_system | 10 | 公告/举报/统计/权限 |

**盲区**：① `AnswerViewSet`（未注册无测试）② 图片上传大小/类型校验（未接线故无测试）③ 分页边界（`page` 非法值）④ 并发点赞/重复提交评价 ⑤ 前端无任何单测（AGENTS.md 已注明靠手动点测）。

## 五、修复优先级建议

1. **立即**（1 天内）：P0-1 部署安全默认值；P1-2 删除/修复 AnswerViewSet；P1-6 统一 update/destroy 响应。
2. **本周**：P1-3 N+1、P1-4 图片校验接线、P1-5 密码校验、P1-7 qa is_liked；P2-8 商家详情泄露、P2-9 被拒重提。
3. **排期**：其余 P2/P3 按迭代消化，配合补对应测试。
