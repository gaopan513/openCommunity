"""
二手市场模块视图

提供商品分类、商品的 CRUD 接口及状态变更、评论功能。
"""
from django.db.models import F
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated

from common.pagination import StandardPagination, SmallPagination
from common.permissions import IsOwnerOrAdmin, IsAuthenticatedOrCreate
from common.response import success_response, created_response, error_response, list_response, no_content_response
from .models import ProductCategory, Product, ProductComment
from .serializers import (
    ProductCategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateSerializer,
    ProductCommentSerializer,
)


class ProductCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """商品分类视图集

    仅提供列表查询功能，所有人可访问。
    """
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        """获取商品分类列表"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """二手商品视图集

    提供商品的增删改查、状态变更、评论管理功能。
    - list: 支持按分类、状态、成色筛选，支持搜索和排序
    - create: 已认证用户可发布商品
    - retrieve: 任何人可查看，自动增加浏览量
    - update/destroy: 仅卖家或管理员可操作
    - status: 变更商品状态（有状态转换限制）
    - comments: 获取/发表评论
    """
    queryset = Product.objects.select_related('seller', 'category').prefetch_related('images')
    pagination_class = StandardPagination
    filterset_fields = ['category', 'status', 'condition']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'price']
    ordering = ['-created_at']

    def get_queryset(self):
        """详情页额外预取评论作者，避免嵌套评论列表逐条查询

        ?mine=1 时（仅 list）过滤为当前登录用户发布的商品，
        供小程序「我的商品」页使用；未登录时返回空集，
        避免把全量商品误当「我的」下发。
        """
        queryset = super().get_queryset()
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('comments__author')
        if self.action == 'list' and self.request.query_params.get('mine') == '1':
            if self.request.user.is_authenticated:
                queryset = queryset.filter(seller=self.request.user)
            else:
                queryset = queryset.none()
        return queryset

    def get_permissions(self):
        """根据操作类型返回不同权限"""
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action == 'comments':
            if self.request.method == 'GET':
                return [AllowAny()]
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsOwnerOrAdmin()]

    def get_serializer_class(self):
        """根据操作类型返回不同序列化器"""
        if self.action == 'list':
            return ProductListSerializer
        if self.action == 'retrieve':
            return ProductDetailSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return ProductCreateSerializer
        return ProductListSerializer

    def list(self, request, *args, **kwargs):
        """获取商品列表（支持筛选、搜索、排序）"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return list_response(
                results=serializer.data,
                total=self.paginator.page.paginator.count,
                page=self.paginator.page.number,
                page_size=self.paginator.get_page_size(request),
            )
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """获取商品详情（自动增加浏览量）"""
        instance = self.get_object()
        # 使用 F 表达式原子性增加浏览量
        Product.objects.filter(pk=instance.pk).update(view_count=F('view_count') + 1)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def create(self, request, *args, **kwargs):
        """发布二手商品"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(seller=request.user)
        return created_response(serializer.data, '发布成功')

    def update(self, request, *args, **kwargs):
        """更新商品信息"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, '更新成功')

    def destroy(self, request, *args, **kwargs):
        """删除商品"""
        instance = self.get_object()
        instance.delete()
        return no_content_response('删除成功')

    @action(detail=True, methods=['put'], url_path='status')
    def change_status(self, request, pk=None):
        """变更商品状态

        状态转换规则：
        - on_sale → reserved / sold / off_shelf
        - reserved → on_sale / sold
        - sold → 不可变更
        - off_shelf → on_sale
        """
        product = self.get_object()
        new_status = request.data.get('status')

        if not new_status:
            return error_response('请提供目标状态', http_status=status.HTTP_400_BAD_REQUEST)

        # 验证状态值是否合法
        valid_statuses = [choice[0] for choice in Product.Status.choices]
        if new_status not in valid_statuses:
            return error_response(f'无效的状态值: {new_status}', http_status=status.HTTP_400_BAD_REQUEST)

        # 定义合法的状态转换
        allowed_transitions = {
            Product.Status.ON_SALE: [Product.Status.RESERVED, Product.Status.SOLD, Product.Status.OFF_SHELF],
            Product.Status.RESERVED: [Product.Status.ON_SALE, Product.Status.SOLD],
            Product.Status.SOLD: [],
            Product.Status.OFF_SHELF: [Product.Status.ON_SALE],
        }

        current_status = product.status
        if new_status == current_status:
            return error_response('商品已处于该状态', http_status=status.HTTP_400_BAD_REQUEST)

        if new_status not in allowed_transitions.get(current_status, []):
            return error_response(
                f'不允许从「{product.get_status_display()}」变更为「{dict(Product.Status.choices)[new_status]}」',
                http_status=status.HTTP_400_BAD_REQUEST
            )

        product.status = new_status
        product.save(update_fields=['status', 'updated_at'])
        serializer = ProductDetailSerializer(product, context={'request': request})
        return success_response(serializer.data, '状态更新成功')

    @action(detail=True, methods=['get', 'post'], url_path='comments')
    def comments(self, request, pk=None):
        """获取或发表商品评论"""
        product = self.get_object()

        if request.method == 'GET':
            comments = product.comments.select_related('author').all()
            paginator = SmallPagination()
            page = paginator.paginate_queryset(comments, request, view=self)
            if page is not None:
                serializer = ProductCommentSerializer(page, many=True, context={'request': request})
                return list_response(
                    results=serializer.data,
                    total=paginator.page.paginator.count,
                    page=paginator.page.number,
                    page_size=paginator.get_page_size(request),
                )
            serializer = ProductCommentSerializer(comments, many=True, context={'request': request})
            return success_response(serializer.data)

        # POST: 发表评论
        if not request.user.is_authenticated:
            return error_response('请先登录', http_status=status.HTTP_401_UNAUTHORIZED)

        content = request.data.get('content', '').strip()
        if not content:
            return error_response('评论内容不能为空', http_status=status.HTTP_400_BAD_REQUEST)
        # 手动 create 绕过了 serializer 校验，长度上限需在此对齐模型 max_length=500
        if len(content) > 500:
            return error_response('评论内容不能超过500字', http_status=status.HTTP_400_BAD_REQUEST)

        comment = ProductComment.objects.create(
            product=product,
            author=request.user,
            content=content
        )
        serializer = ProductCommentSerializer(comment, context={'request': request})
        return created_response(serializer.data, '评论成功')
