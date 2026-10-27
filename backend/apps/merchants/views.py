"""
商家模块视图

提供商家分类管理、商家入驻申请、审核、活动管理、评价管理等功能。
"""
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated

from common.pagination import StandardPagination
from common.permissions import IsAdminUser, IsMerchantUser, IsOwnerOrAdmin
from common.response import (
    success_response, created_response, error_response, list_response, no_content_response
)
from common.utils import calculate_average_rating
from apps.users.models import User
from apps.housekeeping.models import ServiceProvider
from .models import MerchantCategory, Merchant, Activity, MerchantReview
from .serializers import (
    MerchantCategorySerializer,
    MerchantListSerializer,
    MerchantDetailSerializer,
    MerchantApplySerializer,
    ActivitySerializer,
    ActivityCreateSerializer,
    MerchantReviewSerializer,
    MerchantReviewCreateSerializer,
)


class MerchantCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """商家分类视图集

    list/retrieve: 所有人可访问（只读）
    """

    queryset = MerchantCategory.objects.all()
    serializer_class = MerchantCategorySerializer
    pagination_class = None

    def list(self, request, *args, **kwargs):
        """获取商家分类列表"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """获取商家分类详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)


class MerchantViewSet(viewsets.ModelViewSet):
    """商家视图集

    提供商家列表、详情、入驻申请、审核、活动管理、评价管理等功能。
    """

    pagination_class = StandardPagination

    def get_permissions(self):
        """根据操作动态分配权限

        - apply: 已认证用户（任何登录用户可提交入驻申请，审核通过后授予商家角色）
        - my_shop: 已认证商家角色（仅本人店铺，视图内再校验）
        - audit: 管理员
        - update/partial_update/destroy: 已认证 + 所有者或管理员（对象级）
        - 其他（list/retrieve/activities/reviews）: 默认 IsAuthenticatedOrReadOnly
        """
        if self.action == 'apply':
            return [IsAuthenticated()]
        if self.action == 'my_shop':
            return [IsAuthenticated(), IsMerchantUser()]
        if self.action == 'audit':
            return [IsAdminUser()]
        if self.action in ('update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        """获取查询集

        列表接口默认仅返回已审核通过的商家；
        管理员可通过 ?status= 参数查看其他状态（如 pending）。
        详情接口仅返回已审核通过的商家，所有者/管理员可查看任意状态
        （防止匿名枚举 ID 读取待审商家的营业执照等敏感资料）。
        """
        if self.action == 'list':
            queryset = Merchant.objects.select_related('category', 'user')
            status_filter = self.request.query_params.get('status')
            if status_filter and getattr(self.request.user, 'role', None) == 'admin':
                return queryset.filter(status=status_filter)
            return queryset.filter(status='approved')
        if self.action == 'retrieve':
            user = self.request.user
            queryset = Merchant.objects.select_related('category', 'user')
            if getattr(user, 'role', None) == 'admin':
                return queryset
            if user.is_authenticated:
                return queryset.filter(Q(status='approved') | Q(user=user))
            return queryset.filter(status='approved')
        return Merchant.objects.all().select_related('category', 'user')

    def get_serializer_class(self):
        """根据操作类型返回不同序列化器"""
        if self.action == 'list':
            return MerchantListSerializer
        if self.action == 'retrieve':
            return MerchantDetailSerializer
        if self.action == 'apply':
            return MerchantApplySerializer
        return MerchantDetailSerializer

    def list(self, request, *args, **kwargs):
        """商家列表（支持分类筛选和名称搜索）"""
        queryset = self.get_queryset()

        # 按分类筛选
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)

        # 按名称搜索
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return list_response(
                results=serializer.data,
                total=queryset.count(),
                # 用分页器实际页码，避免手动 int() 解析非法 page 参数导致 500
                page=self.paginator.page.number,
                page_size=self.paginator.get_page_size(request),
            )

        serializer = self.get_serializer(queryset, many=True)
        return list_response(
            results=serializer.data,
            total=queryset.count(),
            page=1,
            page_size=queryset.count(),
        )

    def retrieve(self, request, *args, **kwargs):
        """商家详情（统一响应格式包装）"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def update(self, request, *args, **kwargs):
        """编辑商家资料（所有者或管理员；status/user 等敏感字段不可改）

        使用 MerchantApplySerializer（MerchantDetailSerializer 全字段只读，
        ModelViewSet 默认 update 会静默保存空变更，故此处显式指定）。
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = MerchantApplySerializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            MerchantDetailSerializer(instance).data,
            '商家信息已更新'
        )

    def destroy(self, request, *args, **kwargs):
        """删除商家（所有者或管理员）"""
        instance = self.get_object()
        instance.delete()
        return no_content_response('删除成功')

    @action(detail=False, methods=['post'])
    def apply(self, request):
        """商家入驻申请

        任何登录用户均可提交（审核通过后授予商家角色，角色只能由审核授予）；
        已有 pending 申请时禁止重复提交，
        被拒（rejected）后允许复用原记录重新申请（重置为 pending）。
        """
        existing = getattr(request.user, 'merchant_profile', None)
        if existing is not None and existing.status == Merchant.Status.PENDING:
            return error_response(
                '您有正在审核中的申请，请勿重复提交',
                http_status=status.HTTP_400_BAD_REQUEST
            )
        # 已通过审核的店铺不能重新申请：否则会把 approved 重置为 pending，
        # 店铺立即从公开列表下线；资料变更走 my_shop 编辑
        if existing is not None and existing.status == Merchant.Status.APPROVED:
            return error_response(
                '您的店铺已通过审核，如需变更资料请直接编辑店铺信息',
                http_status=status.HTTP_400_BAD_REQUEST
            )

        serializer = MerchantApplySerializer(existing, data=request.data)
        serializer.is_valid(raise_exception=True)
        if existing is not None:
            # 复用被拒记录：更新资料并重置为待审核（两步写需原子完成）
            with transaction.atomic():
                serializer.save()
                existing.status = Merchant.Status.PENDING
                existing.save(update_fields=['status', 'updated_at'])
        else:
            serializer.save(user=request.user, status='pending')
        return created_response(serializer.data, '入驻申请已提交')

    @action(detail=False, methods=['get', 'put', 'patch'],
            permission_classes=[IsAuthenticated, IsMerchantUser])
    def my_shop(self, request):
        """商家查看/编辑自己的店铺信息

        GET: 获取当前用户关联的店铺详情
        PUT/PATCH: 更新店铺资料（仅允许商家所有者，不可改 status/user 等敏感字段）
        """
        if not hasattr(request.user, 'merchant_profile'):
            return error_response(
                '您还没有店铺，请先提交入驻申请',
                http_status=status.HTTP_404_NOT_FOUND
            )

        merchant = request.user.merchant_profile

        if request.method == 'GET':
            serializer = MerchantDetailSerializer(merchant)
            return success_response(serializer.data)

        # PUT/PATCH：仅审核通过的商家可编辑；待审核/被拒的商家请重新提交申请
        if merchant.status != Merchant.Status.APPROVED:
            return error_response(
                '当前店铺状态不允许编辑，请先联系管理员完成审核'
            )

        serializer = MerchantApplySerializer(
            merchant,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, '店铺信息已更新')

    @action(detail=True, methods=['put'],
            permission_classes=[IsAdminUser])
    def audit(self, request, pk=None):
        """商家审核

        管理员审核商家入驻申请，设置状态为 approved 或 rejected。
        仅待审核（pending）的申请可被处理，避免重复审核覆盖结果。
        审核通过时同步授予用户商家角色；拒绝时回收商家角色
        （若用户还持有已通过的家政服务商资质则保留角色）。
        角色只能由审核授予或回收，不可自封。
        """
        merchant = self.get_object()

        if merchant.status != Merchant.Status.PENDING:
            return error_response('该申请已被处理，无需重复审核')

        new_status = request.data.get('status')

        if new_status not in ('approved', 'rejected'):
            return error_response('状态值无效，仅支持 approved 或 rejected')

        user = merchant.user
        with transaction.atomic():
            merchant.status = new_status
            merchant.save(update_fields=['status', 'updated_at'])

            if new_status == 'approved':
                if user.role != User.Role.MERCHANT:
                    user.role = User.Role.MERCHANT
                    user.save(update_fields=['role'])
            else:
                # 回收商家角色，但保留通过家政服务商审核获得的角色
                has_approved_provider = ServiceProvider.objects.filter(
                    user=user, status=ServiceProvider.Status.APPROVED
                ).exists()
                if user.role == User.Role.MERCHANT and not has_approved_provider:
                    user.role = User.Role.RESIDENT
                    user.save(update_fields=['role'])

        return success_response(
            {'id': merchant.id, 'status': merchant.status},
            '审核完成'
        )

    @action(detail=True, methods=['get', 'post'])
    def activities(self, request, pk=None):
        """商家活动管理

        GET: 获取商家的活动列表
        POST: 商家所有者创建活动
        """
        merchant = self.get_object()

        if request.method == 'GET':
            activities = merchant.activities.all()
            page = self.paginate_queryset(activities)
            if page is not None:
                serializer = ActivitySerializer(page, many=True)
                return list_response(
                    results=serializer.data,
                    total=self.paginator.page.paginator.count,
                    page=self.paginator.page.number,
                    page_size=self.paginator.get_page_size(request),
                )
            serializer = ActivitySerializer(activities, many=True)
            return success_response(serializer.data)

        # POST: 仅商家所有者可创建
        if merchant.user != request.user:
            return error_response('无权操作', http_status=status.HTTP_403_FORBIDDEN)

        serializer = ActivityCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(merchant=merchant)
        return created_response(serializer.data, '活动创建成功')

    @action(detail=True, methods=['put', 'patch', 'delete'],
            url_path=r'activities/(?P<activity_pk>\d+)')
    def activity_item(self, request, pk=None, activity_pk=None):
        """商家活动详情操作

        PUT/PATCH: 商家所有者更新活动
        DELETE: 商家所有者删除活动
        """
        merchant = self.get_object()

        # 仅商家所有者可操作
        if merchant.user != request.user:
            return error_response('无权操作', http_status=status.HTTP_403_FORBIDDEN)

        try:
            activity = merchant.activities.get(pk=activity_pk)
        except Activity.DoesNotExist:
            return error_response('活动不存在', http_status=status.HTTP_404_NOT_FOUND)

        if request.method == 'DELETE':
            activity.delete()
            return success_response(None, '活动已删除')

        # PUT/PATCH：更新活动
        serializer = ActivityCreateSerializer(
            activity,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, '活动已更新')

    @action(detail=True, methods=['get', 'post'])
    def reviews(self, request, pk=None):
        """商家评价管理

        GET: 获取商家的评价列表
        POST: 已认证用户发表评价（每个用户对每个商家仅限一次）
        """
        merchant = self.get_object()

        if request.method == 'GET':
            reviews = merchant.reviews.select_related('user').all()
            page = self.paginate_queryset(reviews)
            if page is not None:
                serializer = MerchantReviewSerializer(page, many=True)
                return list_response(
                    results=serializer.data,
                    total=self.paginator.page.paginator.count,
                    page=self.paginator.page.number,
                    page_size=self.paginator.get_page_size(request),
                )
            serializer = MerchantReviewSerializer(reviews, many=True)
            return success_response(serializer.data)

        # POST: 已认证用户可评价
        if not request.user.is_authenticated:
            return error_response('请先登录', http_status=status.HTTP_401_UNAUTHORIZED)

        # 仅已通过审核的商家可被评价：本 action 的 queryset 不过滤状态，
        # 不拦截会导致对 pending/rejected 商家"预置/刷分"评价，过审后直接公开
        if merchant.status != Merchant.Status.APPROVED:
            return error_response(
                '该商家尚未通过审核，暂不可评价',
                http_status=status.HTTP_400_BAD_REQUEST
            )

        # 检查是否已评价
        if MerchantReview.objects.filter(merchant=merchant, user=request.user).exists():
            return error_response('您已评价过该商家', http_status=status.HTTP_400_BAD_REQUEST)

        serializer = MerchantReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 评价与评分冗余字段重算两步写必须原子完成，避免评分与评价表脱节
        with transaction.atomic():
            serializer.save(merchant=merchant, user=request.user)
            self._update_merchant_rating(merchant)

        return created_response(serializer.data, '评价成功')

    @action(detail=True, methods=['put'],
            url_path='reviews/(?P<review_id>[^/.]+)/reply')
    def reply_review(self, request, pk=None, review_id=None):
        """商家回复评价

        仅商家所有者可回复自己商家的评价。
        """
        merchant = self.get_object()

        # 仅商家所有者可回复
        if merchant.user != request.user:
            return error_response('无权操作', http_status=status.HTTP_403_FORBIDDEN)

        try:
            review = merchant.reviews.get(pk=review_id)
        except MerchantReview.DoesNotExist:
            return error_response('评价不存在', http_status=status.HTTP_404_NOT_FOUND)

        reply_content = request.data.get('reply', '')
        if not reply_content:
            return error_response('回复内容不能为空')

        review.reply = reply_content
        review.replied_at = timezone.now()
        review.save(update_fields=['reply', 'replied_at'])

        return success_response(
            MerchantReviewSerializer(review).data,
            '回复成功'
        )

    @staticmethod
    def _update_merchant_rating(merchant):
        """重新计算商家的平均评分和评价数量"""
        reviews = merchant.reviews.all()
        ratings = [r.rating for r in reviews]
        merchant.avg_rating = calculate_average_rating(ratings)
        merchant.review_count = reviews.count()
        merchant.save(update_fields=['avg_rating', 'review_count'])
