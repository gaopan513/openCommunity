"""
家政服务模块视图

提供服务分类、服务提供者、预约订单、服务评价的 API 接口。
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from common.permissions import IsAdminUser, IsMerchantUser
from common.response import success_response, created_response, error_response, list_response, no_content_response
from common.pagination import StandardPagination
from common.utils import calculate_average_rating
from apps.users.models import User

from .models import (
    ServiceCategory, ServiceProvider, ServiceItem,
    Booking, ServiceReview
)
from .serializers import (
    ServiceCategorySerializer,
    ServiceProviderListSerializer,
    ServiceProviderDetailSerializer,
    ServiceProviderApplySerializer,
    ServiceItemSerializer,
    BookingSerializer,
    BookingCreateSerializer,
    ServiceReviewSerializer,
    ServiceReviewCreateSerializer,
)


class ServiceCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """服务分类视图集

    仅提供列表查询，允许匿名访问（只读）。
    """
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        """获取所有服务分类"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """获取服务分类详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)


class ServiceProviderViewSet(viewsets.ReadOnlyModelViewSet):
    """服务提供者视图集

    - list: 仅展示已审核通过的提供者，支持分类筛选和名称搜索
    - retrieve: 提供者详情（含服务列表和近期评价）
    - apply: 商家申请成为服务提供者（@action）
    - audit: 管理员审核申请（@action）
    """
    pagination_class = StandardPagination

    def get_permissions(self):
        """根据操作动态分配权限

        apply: 任何登录用户可提交服务商申请（审核通过后授予商家角色）
        """
        if self.action == 'audit':
            return [IsAuthenticated(), IsAdminUser()]
        if self.action == 'apply':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        """获取查询集

        列表默认仅返回已通过的提供者；
        管理员可通过 ?status= 参数查看其他状态（如 pending）。
        prefetch services__category 供序列化器复用，避免列表 N+1。
        """
        status_filter = self.request.query_params.get('status')
        if status_filter and getattr(self.request.user, 'role', None) == 'admin':
            queryset = ServiceProvider.objects.filter(status=status_filter)
        else:
            queryset = ServiceProvider.objects.filter(
                status=ServiceProvider.Status.APPROVED
            )
        queryset = queryset.prefetch_related('services__category')
        # 按分类筛选
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(services__category__slug=category).distinct()
        # 按名称搜索
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(service_area__icontains=search)
            )
        return queryset

    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'retrieve':
            return ServiceProviderDetailSerializer
        if self.action == 'apply':
            return ServiceProviderApplySerializer
        return ServiceProviderListSerializer

    def list(self, request, *args, **kwargs):
        """获取已审核通过的服务提供者列表"""
        queryset = self.get_queryset()
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
        """获取服务提供者详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    @action(detail=False, methods=['post'])
    def apply(self, request):
        """申请成为服务提供者

        任何登录用户均可申请（审核通过后授予商家角色，角色只能由审核授予）；
        已有 pending 申请时禁止重复提交，
        被拒（rejected）后允许复用原记录重新申请（重置为 pending）。
        """
        # 检查是否已有申请记录
        existing = getattr(request.user, 'service_profile', None)
        if existing is not None and existing.status == ServiceProvider.Status.PENDING:
            return error_response('您有正在审核中的申请，请勿重复提交')
        # 已通过审核的服务商不能重新申请，否则 approved 被重置为 pending，
        # 店铺下线且名下服务项目立即无法被预约
        if existing is not None and existing.status == ServiceProvider.Status.APPROVED:
            return error_response('您的服务商资质已通过审核，无需重复申请')

        serializer = ServiceProviderApplySerializer(existing, data=request.data)
        if not serializer.is_valid():
            return error_response(
                '提交信息有误',
                data=serializer.errors
            )

        if existing is not None:
            # 复用被拒记录：更新资料并重置为待审核（两步写需原子完成）
            with transaction.atomic():
                serializer.save()
                existing.status = ServiceProvider.Status.PENDING
                existing.save(update_fields=['status', 'updated_at'])
        else:
            serializer.save(user=request.user)
        return created_response(serializer.data, '申请提交成功，请等待审核')

    @action(detail=True, methods=['put'])
    def audit(self, request, pk=None):
        """管理员审核服务提供者申请

        请求体：{"action": "approve"} 或 {"action": "reject"}
        审核通过时同步授予用户商家角色（角色只能由审核授予，不可自封）。
        """
        provider = self.get_object()

        if provider.status != ServiceProvider.Status.PENDING:
            return error_response('该申请已被处理，无需重复审核')

        audit_action = request.data.get('action')
        if audit_action == 'approve':
            # 审核状态与角色授予是多表写，必须原子完成，避免出现
            # 「provider 已通过但用户未获得商家角色」的中间态
            with transaction.atomic():
                provider.status = ServiceProvider.Status.APPROVED
                provider.save(update_fields=['status', 'updated_at'])
                user = provider.user
                if user.role != User.Role.MERCHANT:
                    user.role = User.Role.MERCHANT
                    user.save(update_fields=['role'])
            return success_response(message='审核通过')
        elif audit_action == 'reject':
            provider.status = ServiceProvider.Status.REJECTED
            provider.save(update_fields=['status', 'updated_at'])
            return success_response(message='已拒绝该申请')
        else:
            return error_response('无效的操作，action 必须为 approve 或 reject')

    def get_object(self):
        """获取对象时不限制状态（审核操作需要访问待审核记录）"""
        if self.action == 'audit':
            # 用 get_object_or_404 替代 Model.objects.get，避免传入不存在 pk 时
            # 抛 DoesNotExist（非 APIException，DEBUG=False 下被全局处理器兜底为 500）。
            return get_object_or_404(ServiceProvider, pk=self.kwargs['pk'])
        return super().get_object()


class BookingViewSet(viewsets.ModelViewSet):
    """预约订单视图集

    - list: 居民查看自己的预约；商家查看自己收到的预约
    - create: 居民创建预约
    - status: 更新订单状态（状态流转）
    - review: 服务完成后添加评价
    """
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """根据用户角色返回对应的订单列表

        select_related 覆盖 BookingSerializer 访问的全部外键链
        （service_item、service_item.category、service_item.provider、provider），
        避免列表页每行 4 次查询的 N+1。
        """
        user = self.request.user
        base = Booking.objects.select_related(
            'provider', 'service_item__category', 'service_item__provider'
        )
        if user.role == 'merchant' and hasattr(user, 'service_profile'):
            # 商家查看收到的预约
            return base.filter(provider=user.service_profile)
        # 居民查看自己的预约
        return base.filter(user=user)

    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'create':
            return BookingCreateSerializer
        return BookingSerializer

    def get_object(self):
        """获取订单对象

        status 和 review 操作需要从全量订单中查找，以便正确返回 403 而非 404。
        """
        if self.action in ('status', 'review'):
            obj = get_object_or_404(Booking, pk=self.kwargs['pk'])
            self.check_object_permissions(self.request, obj)
            return obj
        return super().get_object()

    def list(self, request, *args, **kwargs):
        """获取预约订单列表"""
        queryset = self.get_queryset()

        # 支持按状态筛选
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BookingSerializer(page, many=True)
            return list_response(
                results=serializer.data,
                total=self.paginator.page.paginator.count,
                page=self.paginator.page.number,
                page_size=self.paginator.get_page_size(request),
            )
        serializer = BookingSerializer(queryset, many=True)
        return success_response(serializer.data)

    def create(self, request, *args, **kwargs):
        """居民创建预约订单"""
        if request.user.role != 'resident':
            return error_response('仅居民用户可以创建预约')

        serializer = BookingCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('预约信息有误', data=serializer.errors)

        service_item = serializer.validated_data['service_item']
        booking = serializer.save(
            user=request.user,
            provider=service_item.provider
        )
        return created_response(
            BookingSerializer(booking).data,
            '预约提交成功，请等待服务方确认'
        )

    def retrieve(self, request, *args, **kwargs):
        """预约订单详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def update(self, request, *args, **kwargs):
        """更新预约订单

        仅待确认（pending）状态可修改预约日期/时段/备注；
        已确认及之后的状态属于履约记录，禁止篡改。
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        # 仅预约用户本人（或管理员）可改预约信息；服务商只能通过 status 动作处理订单
        if instance.user_id != request.user.id and request.user.role != 'admin':
            return error_response(
                '仅预约用户可修改预约信息',
                http_status=status.HTTP_403_FORBIDDEN
            )
        if instance.status != Booking.Status.PENDING:
            return error_response(
                f'当前状态「{instance.get_status_display()}」不允许修改，'
                '仅待确认的订单可修改预约信息'
            )
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, '更新成功')

    def destroy(self, request, *args, **kwargs):
        """取消预约订单（删除记录）

        仅允许删除待确认/已拒绝/已取消的订单；已确认及之后的状态需走
        status @action 流转，已评价（REVIEWED）订单删除会级联删除评价
        且不同步 provider 评分冗余字段，故禁止删除，避免脏数据。
        """
        instance = self.get_object()
        # 仅预约用户本人（或管理员）可删除订单；服务商拒单须走 status 的 rejected 流转
        if instance.user_id != request.user.id and request.user.role != 'admin':
            return error_response(
                '仅预约用户可以取消订单',
                http_status=status.HTTP_403_FORBIDDEN
            )
        allowed_cancel = (
            Booking.Status.PENDING,
            Booking.Status.REJECTED,
            Booking.Status.CANCELLED,
        )
        if instance.status not in allowed_cancel:
            return error_response(
                f'当前状态「{instance.get_status_display()}」不允许取消，'
                '请通过状态流转接口处理'
            )
        instance.delete()
        return no_content_response('已取消预约')

    @action(detail=True, methods=['put'])
    def status(self, request, pk=None):
        """更新订单状态

        状态流转规则：
        - pending → confirmed/rejected（服务提供者操作）
        - confirmed → in_service/rejected（服务提供者操作；rejected 供无法履约时退出）
        - in_service → completed（服务提供者操作）
        - completed → reviewed（评价后自动变更）
        - pending/confirmed → cancelled（预约用户本人取消，管理员亦可）

        cancelled 为终态，保证已确认订单也有出口，不会永久僵死。
        """
        booking = self.get_object()
        new_status = request.data.get('status')

        if not new_status:
            return error_response('请提供目标状态 status')

        user = request.user
        current_status = booking.status

        # 取消：仅预约用户本人（或管理员）可操作，限待确认/已确认的订单
        if new_status == Booking.Status.CANCELLED:
            if user != booking.user and user.role != 'admin':
                return error_response(
                    '仅预约用户可以取消订单', http_status=status.HTTP_403_FORBIDDEN
                )
            if current_status not in (Booking.Status.PENDING, Booking.Status.CONFIRMED):
                return error_response(
                    f'当前状态「{booking.get_status_display()}」不允许取消'
                )
            booking.status = new_status
            booking.save(update_fields=['status', 'updated_at'])
            return success_response(
                BookingSerializer(booking).data,
                f'订单状态已更新为「{booking.get_status_display()}」'
            )

        # 其余流转由服务提供者操作
        valid_transitions = {
            Booking.Status.PENDING: [Booking.Status.CONFIRMED, Booking.Status.REJECTED],
            Booking.Status.CONFIRMED: [Booking.Status.IN_SERVICE, Booking.Status.REJECTED],
            Booking.Status.IN_SERVICE: [Booking.Status.COMPLETED],
        }

        allowed = valid_transitions.get(current_status, [])

        if new_status not in allowed:
            return error_response(
                f'不允许从「{booking.get_status_display()}」变更为「{new_status}」'
            )

        # 权限检查：状态变更由服务提供者操作
        if user.role == 'merchant' and hasattr(user, 'service_profile'):
            if booking.provider != user.service_profile:
                return error_response('无权操作此订单', http_status=status.HTTP_403_FORBIDDEN)
        elif user.role == 'admin':
            pass  # 管理员可操作
        else:
            return error_response('无权变更订单状态', http_status=status.HTTP_403_FORBIDDEN)

        booking.status = new_status
        booking.save(update_fields=['status', 'updated_at'])
        return success_response(
            BookingSerializer(booking).data,
            f'订单状态已更新为「{booking.get_status_display()}」'
        )

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """服务完成后添加评价

        仅当订单状态为 completed 时，由预约用户提交评价。
        评价后订单状态自动变为 reviewed，并更新提供者平均评分。
        """
        booking = self.get_object()

        # 检查是否为预约用户
        if booking.user != request.user:
            return error_response('仅预约用户可以进行评价', http_status=status.HTTP_403_FORBIDDEN)

        # 检查订单状态
        if booking.status != Booking.Status.COMPLETED:
            return error_response('仅已完成的服务可以评价')

        # 检查是否已评价
        if hasattr(booking, 'review'):
            return error_response('该订单已评价，请勿重复提交')

        serializer = ServiceReviewCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('评价信息有误', data=serializer.errors)

        # 评价、订单状态流转、评分冗余字段重算三步写必须原子完成，
        # 部分失败会产生评价与订单/评分不一致的脏数据
        with transaction.atomic():
            review = serializer.save(
                booking=booking,
                user=request.user,
                provider=booking.provider
            )

            # 更新订单状态为已评价
            booking.status = Booking.Status.REVIEWED
            booking.save(update_fields=['status', 'updated_at'])

            # 更新提供者平均评分
            provider = booking.provider
            ratings = list(provider.reviews.values_list('rating', flat=True))
            provider.avg_rating = calculate_average_rating(ratings)
            provider.review_count = len(ratings)
            provider.save(update_fields=['avg_rating', 'review_count', 'updated_at'])

        return created_response(
            ServiceReviewSerializer(review).data,
            '评价提交成功'
        )
