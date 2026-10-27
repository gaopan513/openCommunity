# 编码规范文档

## 通用规范

### 语言与命名
- 代码语言：Python / JavaScript
- 注释语言：中文
- 变量/函数命名：Python 用 snake_case，JS 用 camelCase
- 类命名：PascalCase（如 `MerchantReview`）
- 常量：UPPER_SNAKE_CASE（如 `MAX_IMAGE_COUNT = 9`）
- 文件命名：Python 用 snake_case（如 `services.py`），Vue 组件用 PascalCase（如 `PostCard.vue`）

### 注释要求
- 每个文件头部：模块用途说明（docstring）
- 每个类：类职责说明
- 每个公共方法：功能描述、参数说明、返回值
- 关键业务逻辑：算法思路或业务规则说明
- 复杂条件判断：判断条件和预期结果

### 禁止事项
- 禁止 `# TODO` 或 `# 待实现` 占位符
- 禁止跨模块直接导入模型（通过 API 或 common 层交互）
- 禁止在 views.py 中写复杂业务逻辑（应放入 services.py）
- 禁止硬编码配置值（使用 settings 或常量）

---

## 后端规范（Django + DRF）

### 文件职责划分

| 文件 | 职责 | 规则 |
|------|------|------|
| models.py | 数据模型定义 | 每个模型必须有 `class Meta` 和 `__str__` 方法 |
| serializers.py | 数据序列化/验证 | 读写字段分离，验证逻辑在 serializer 中 |
| views.py | 请求处理 | 仅做参数接收、调用 service、返回响应 |
| services.py | 业务逻辑 | 核心逻辑在此，可被多处调用 |
| urls.py | 路由配置 | 使用 DRF Router，路径用复数名词 |
| admin.py | 后台配置 | 配置 list_display, search_fields, list_filter |
| tests.py | 单元测试 | 每个 API 端点至少一个测试用例 |

### Model 规范
```python
class Merchant(models.Model):
    """商家信息模型
    
    存储入驻商家的基本信息和审核状态。
    """
    class Status(models.TextChoices):
        PENDING = 'pending', '待审核'
        APPROVED = 'approved', '已通过'
        REJECTED = 'rejected', '已驳回'

    name = models.CharField('店铺名称', max_length=100)
    status = models.CharField('审核状态', max_length=20, 
                              choices=Status.choices, 
                              default=Status.PENDING)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '商家'
        verbose_name_plural = '商家'
        ordering = ['-created_at']

    def __str__(self):
        return self.name
```

### View 规范
```python
class MerchantViewSet(viewsets.ModelViewSet):
    """商家视图集
    
    提供商家列表、详情、入驻申请、审核等接口。
    """
    queryset = Merchant.objects.filter(status='approved')
    serializer_class = MerchantSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['category', 'status']
    ordering_fields = ['created_at', 'avg_rating']

    def perform_create(self, serializer):
        """创建商家时关联当前用户"""
        serializer.save(user=self.request.user)
```

### Service 规范
```python
class MerchantService:
    """商家业务逻辑服务
    
    处理商家入驻审核、评分计算等核心业务。
    """
    
    @staticmethod
    def approve_merchant(merchant_id: int, admin_user) -> Merchant:
        """审核通过商家入驻申请
        
        Args:
            merchant_id: 商家记录ID
            admin_user: 操作的管理员用户
            
        Returns:
            更新后的 Merchant 实例
            
        Raises:
            BusinessError: 商家不存在或状态不允许审核
        """
        # 业务逻辑实现...
        pass
```

### API 响应格式
```python
# 成功响应
{
    "code": 0,
    "message": "success",
    "data": { ... }
}

# 列表响应（带分页）
{
    "code": 0,
    "message": "success",
    "data": {
        "total": 100,
        "page": 1,
        "page_size": 20,
        "results": [ ... ]
    }
}

# 错误响应
{
    "code": 40001,
    "message": "商家名称已存在",
    "data": null
}
```

### 测试规范
- 使用 pytest + pytest-django
- 测试文件命名：`test_模块名.py`
- 测试函数命名：`test_功能描述`
- 使用 factory_boy 或 fixture 构造测试数据
- 每个 API 端点覆盖：正常流程 + 权限拒绝 + 参数错误

---

## 前端规范（Vue 3）

### 目录结构
```
frontend/src/
├── api/              # API 请求模块（按业务分文件）
│   ├── auth.js
│   ├── merchants.js
│   └── ...
├── views/            # 页面组件（按模块分目录）
│   ├── merchant/
│   ├── secondhand/
│   └── ...
├── components/       # 公共组件
│   ├── PostCard.vue
│   ├── RatingStars.vue
│   └── ...
├── stores/           # Pinia 状态管理
├── router/           # 路由配置
├── utils/            # 工具函数
└── styles/           # 全局样式
```

### 组件规范
- 使用 `<script setup>` 语法
- 组件名 PascalCase，文件名与组件名一致
- Props 必须声明类型和默认值
- 事件命名：kebab-case（如 `@status-change`）

### API 调用规范
```javascript
// api/merchants.js
import request from '@/utils/request'

/**
 * 获取商家列表
 * @param {Object} params - 查询参数
 * @param {string} params.category - 分类筛选
 * @param {number} params.page - 页码
 */
export function getMerchants(params) {
  return request.get('/merchants/', { params })
}
```

---

## Git 提交规范

- 格式：`<type>(<scope>): <subject>`
- type：feat / fix / refactor / docs / test / chore
- scope：模块名（users, merchants, secondhand 等）
- 示例：`feat(merchants): 实现商家入驻申请接口`

---

## 代码审查检查清单

### 即时审查（每个函数）
- [ ] 语法正确，可正常运行
- [ ] 注释完整且准确
- [ ] 函数职责单一
- [ ] 参数和返回值清晰
- [ ] 无明显逻辑错误

### 模块审查（每个模块）
- [ ] 所有函数通过即时审查
- [ ] 接口定义清晰
- [ ] 模块间依赖合理
- [ ] 单元测试覆盖 > 80%
- [ ] 无代码重复
- [ ] 性能关键路径已优化
- [ ] 无安全常见问题（SQL注入、XSS、越权）
