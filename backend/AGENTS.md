# backend

## Package Identity
Django 5 + DRF REST 后端，承载 openCommunity 全部业务。自定义用户模型 `User`（带 `role` 字段），7 个业务 app，统一 JWT 鉴权、统一响应封装、统一分页与异常处理。开发库 SQLite，生产可切 PostgreSQL。

## Setup & Run
```bash
cd backend
python -m venv venv
venv\Scripts\activate                 # Windows；macOS/Linux 用 source venv/bin/activate
pip install -r requirements.txt       # Django>=5.0, DRF, SimpleJWT, django-filter, corsheaders, Pillow
python manage.py migrate
python manage.py createsuperuser      # 可选，Django Admin 入口 /admin/
python manage.py runserver            # http://127.0.0.1:8000

python manage.py test                 # 全量测试
python manage.py test apps.housekeeping   # 单模块测试
python manage.py makemigrations <app> && python manage.py migrate   # 字段变更
```

## Patterns & Conventions

### App 标准结构（每个 app 必备六件套）
- `models.py` — Django 模型，使用 `class Meta: verbose_name / ordering`，`__str__` 必填
- `serializers.py` — DRF 序列化器，列表/详情/创建/特殊操作分别建模（参考 `apps/housekeeping/serializers.py` 的 `ServiceProviderListSerializer` vs `ServiceProviderDetailSerializer` vs `ServiceProviderApplySerializer`）
- `views.py` — DRF `ModelViewSet` 为主，自定义动作用 `@action(detail=, methods=)`
- `urls.py` — `DefaultRouter` 注册资源，由 `config/urls.py` 统一 `include('apps.<name>.urls')`
- `admin.py` — Django Admin 注册 `list_display / list_filter / search_fields`
- `tests.py` — Django TestCase，每模块 10+ 测试，覆盖 CRUD/权限/状态流转

### URL 挂载约定（重要）
- 所有业务路由统一在 `config/urls.py` 用 `path('api/v1/', include('apps.<name>.urls'))` 挂载。
- 每个 app 的 `urls.py` 中 `router.register('<prefix>', <ViewSet>, basename='<basename>')`，prefix 不含 `api/v1/` 前缀。
- `@action` 生成的 URL 等于 `api/v1/<router prefix>/<action>/`（`detail=False`）或 `api/v1/<router prefix>/<pk>/<action>/`（`detail=True`）。

### 视图层返回规范（强制）
- 成功：`from common.response import success_response, created_response, list_response, no_content_response`，不要直接 `return Response(serializer.data)`。
- 失败：`error_response(message, code=, data=, http_status=)`，或抛 `BusinessError / NotFoundError / ForbiddenError / StatusTransitionError`（`common.exceptions`）。
- 列表分页：`list_response(results, total, page, page_size, message)`，配合 `StandardPagination`（默认 20/页，max 100）或 `SmallPagination`（10/页，用于评论/留言）。

### 权限约定（`common/permissions.py`）
- `IsOwnerOrReadOnly` — 对象所有者可写，其他人只读（按 `user/author/seller/owner` 字段顺序查找所有者）
- `IsOwnerOrAdmin` — 所有者或管理员
- `IsAdminUser` — `role='admin'`
- `IsMerchantUser` — `role='merchant'`
- `IsAuthenticatedOrCreate` — 匿名只读，已认证可创建
- ViewSet 内动态权限用 `get_permissions()` 按 `self.action` 分发（参考 `apps/housekeeping/views.py:60`）。

### 模型约定
- 自定义用户模型 `AUTH_USER_MODEL = 'users.User'`（`config/settings.py:102`），新 app 引用用户统一用 `settings.AUTH_USER_MODEL`，不要硬编码 `'users.User'`。
- 图片字段 `ImageField` 的 `upload_to` 必须用 `common/utils.py` 中的 `*_upload_path` 函数（如 `housekeeping_upload_path`、`merchant_upload_path`），按 `media/<folder>/<YYYYMM>/<uuid>.<ext>` 落盘。
- 手机号、评分等通用校验在 `common/validators.py`（`validate_phone_number`、`validate_rating` 等），不要在 app 内重复实现。
- 状态字段统一用 `models.TextChoices` 内嵌类（参考 `apps/housekeeping/models.py:37` 的 `ServiceProvider.Status`），状态流转逻辑集中在 ViewSet 的 `@action` 内（参考 `apps/housekeeping/views.py:250` 的 `valid_transitions`）。
- `related_name` 命名：从子表找父表用复数名词（如 `related_name='service_profile'` 一对一、`related_name='reviews'` 一对多）。

### 查询约定
- 列表接口默认 `get_queryset()` 内根据 `request.user.role` 过滤，参考 `apps/housekeeping/views.py:68` 的 `ServiceProviderViewSet`、`:183` 的 `BookingViewSet`。
- 过滤、搜索、排序通过 `django_filters` + DRF `SearchFilter` / `OrderingFilter`（在 `REST_FRAMEWORK['DEFAULT_FILTER_BACKENDS']` 全局开启），无需在视图内手写 query 参数解析。

## Key Files
- 全局配置：`config/settings.py`（DRF/JWT/CORS/数据库/权限/分页/异常处理器）
- 主路由：`config/urls.py`（健康检查 + 各 app 路由挂载）
- 自定义用户：`apps/users/models.py`（`User.role` 角色）、`apps/users/views.py`（注册/登录/资料/改密）
- 响应封装：`common/response.py`（`success_response / error_response / list_response / created_response / no_content_response`）
- 异常体系：`common/exceptions.py`（`BusinessError` 基类 + 4 个子类 + `custom_exception_handler`）
- 权限类：`common/permissions.py`
- 分页器：`common/pagination.py`（`StandardPagination` 20/页、`SmallPagination` 10/页）
- 工具函数：`common/utils.py`（`generate_upload_path` + 各模块上传路径别名、`calculate_average_rating`、`format_datetime`）
- 校验器：`common/validators.py`（手机号、图片大小/格式、评分）
- 典型 app 范例：`apps/housekeeping/`（含状态机、动态权限、@action 审核与流转、审核与评价闭环）

## JIT Index Hints
- 找 ViewSet 及其 action：`rg -n "class \w+ViewSet|@action" backend/apps`
- 找某模块路由：`rg -n "router.register" backend/apps/<module>/urls.py`
- 找响应封装用法：`rg -n "success_response|error_response|list_response" backend/apps`
- 找权限类引用：`rg -n "from common.permissions" backend/apps`
- 找模型字段定义：`rg -n "models\.(CharField|TextField|ImageField|ForeignKey|ManyToManyField|OneToOneField|DecimalField|TextChoices)" backend/apps`
- 找业务异常抛出：`rg -n "raise (BusinessError|NotFoundError|ForbiddenError|StatusTransitionError)" backend/apps`
- 找迁移文件：`rg --files backend/apps --glob "**/migrations/*.py" | rg -v __init__`

## Common Gotchas

### ⚠️ @action URL 与前端调用必须严格对齐
- DRF `DefaultRouter` 注册 `router.register('housekeeping/providers', ServiceProviderViewSet)` 后，`@action(detail=False)` 生成的 `apply` 动作的 URL 是 `/api/v1/housekeeping/providers/apply/`，**不是** `/api/v1/housekeeping/apply/`。
- 前端 `frontend/src/api/housekeeping.js` 必须用 `request.post('/housekeeping/providers/apply/', data)`，路径前缀不能漏掉 `providers/`。
- 404 时后端默认返回 `{"detail": "Not found."}`（无 `message` 字段），前端 `request.js` 会回退到"请求失败"提示，**排查 404 时务必核对 `router.register` 的 prefix 与 `@action` 的实际 URL**。历史曾因此导致服务商入驻申请失败。

### ⚠️ `get_object()` 重写时要小心状态过滤
- 默认 `get_queryset()` 已过滤状态（如 `ServiceProvider` 列表仅返回 `APPROVED`），但审核/状态流转的 `@action` 需要访问 `PENDING` 记录。
- 解决方式：在 `get_object()` 内按 `self.action` 走 `Model.objects.get(pk=...)`（绕过 queryset 过滤），参考 `apps/housekeeping/views.py:165` 与 `:198`。

### ⚠️ 全局异常处理器不兜底非 DRF 异常
- `common/exceptions.py:custom_exception_handler` 仅处理 DRF `APIException` 及其子类。Django 原生 `Http404`、`PermissionDenied`、未捕获的 `Exception` 在 `DEBUG=False` 下会直接 500，需自行 try/except 转为 `BusinessError`。

### ⚠️ 数据库迁移与测试隔离
- **永远不要在测试运行时执行迁移**，Django test runner 会自动创建测试库。
- `apps/*/migrations/` 目录必须保留 `__init__.py`，新增字段后必须 `makemigrations` 并提交迁移文件，否则他人 clone 后 `migrate` 会缺字段。
- `db.sqlite3` 是开发库，会被 `.gitignore`，但 `apps/<module>/migrations/0001_initial.py` 等必须入库。

## Pre-PR Checks
```bash
cd backend
venv\Scripts\activate
python manage.py test                                    # 全量
python manage.py test apps.<changed_module>              # 仅改动模块
python manage.py makemigrations --check --dry-run        # 字段变更是否已生成迁移
python manage.py check                                   # Django 系统检查
```
