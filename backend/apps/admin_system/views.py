"""
系统管理模块视图

提供公告管理、举报处理、基础数据统计等接口。
"""
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated

from common.permissions import IsAdminUser
from common.response import success_response, created_response, error_response, list_response, no_content_response
from common.pagination import StandardPagination
from .models import Announcement, Report
from .serializers import (
    AnnouncementSerializer, ReportSerializer, ReportCreateSerializer
)


class AnnouncementViewSet(viewsets.ModelViewSet):
    """公告视图集

    - list: 公开接口，仅返回已激活的公告
    - retrieve: 公告详情
    - create/update/destroy: 仅管理员
    """
    serializer_class = AnnouncementSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        """列表/详情仅返回已激活公告，管理接口返回全部

        retrieve 与 list 同样对匿名公开，必须一并过滤 is_active=True，
        否则匿名用户可枚举 ID 读取未激活（下线/未发布）公告内容。
        """
        if self.action in ('list', 'retrieve'):
            return Announcement.objects.filter(is_active=True).select_related('author')
        return Announcement.objects.select_related('author')

    def get_permissions(self):
        """列表和详情公开，其他操作需管理员权限"""
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAdminUser()]

    def perform_create(self, serializer):
        """创建公告时关联当前管理员"""
        serializer.save(author=self.request.user)

    def list(self, request, *args, **kwargs):
        """公告列表"""
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
        """公告详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def create(self, request, *args, **kwargs):
        """创建公告"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return created_response(serializer.data, '创建成功')

    def update(self, request, *args, **kwargs):
        """更新公告"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, '更新成功')

    def destroy(self, request, *args, **kwargs):
        """删除公告"""
        instance = self.get_object()
        instance.delete()
        return no_content_response('删除成功')


class ReportViewSet(viewsets.ModelViewSet):
    """举报视图集

    - create: 已认证用户提交举报
    - list: 管理员查看举报列表
    - handle: 管理员处理举报
    """
    pagination_class = StandardPagination

    def get_queryset(self):
        """普通用户只能看自己的举报，管理员看全部"""
        if self.request.user.is_authenticated and self.request.user.role == 'admin':
            return Report.objects.select_related('reporter')
        return Report.objects.filter(reporter=self.request.user).select_related('reporter')

    def get_serializer_class(self):
        if self.action == 'create':
            return ReportCreateSerializer
        return ReportSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def perform_create(self, serializer):
        """创建举报时关联举报人"""
        serializer.save(reporter=self.request.user)

    def list(self, request, *args, **kwargs):
        """举报列表"""
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
        """举报详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def create(self, request, *args, **kwargs):
        """提交举报"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return created_response(serializer.data, '举报已提交')

    def update(self, request, *args, **kwargs):
        """更新举报"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, '更新成功')

    def destroy(self, request, *args, **kwargs):
        """删除举报"""
        instance = self.get_object()
        instance.delete()
        return no_content_response('删除成功')
    
    @action(detail=True, methods=['put'], permission_classes=[IsAdminUser])
    def handle(self, request, pk=None):
        """处理举报
        
        请求体：
            status: handled 或 dismissed
            handle_note: 处理备注（选填）
        """
        report = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in ('handled', 'dismissed'):
            return error_response('状态值无效，仅支持 handled 或 dismissed')
        
        report.status = new_status
        report.handle_note = request.data.get('handle_note', '')
        report.handled_at = timezone.now()
        report.save()
        
        serializer = ReportSerializer(report)
        return success_response(data=serializer.data, message='处理完成')


@api_view(['GET'])
@permission_classes([IsAdminUser])
def statistics_view(request):
    """基础数据统计接口（管理员）
    
    返回各模块的核心数据量。
    """
    from apps.users.models import User
    from apps.discussion.models import Post
    from apps.qa.models import Question
    from apps.secondhand.models import Product
    from apps.merchants.models import Merchant
    from apps.housekeeping.models import Booking
    
    data = {
        'users': {
            'total': User.objects.count(),
            'residents': User.objects.filter(role='resident').count(),
            'merchants': User.objects.filter(role='merchant').count(),
        },
        'posts': Post.objects.count(),
        'questions': Question.objects.count(),
        'products': Product.objects.count(),
        'merchants': {
            'total': Merchant.objects.count(),
            'approved': Merchant.objects.filter(status='approved').count(),
            'pending': Merchant.objects.filter(status='pending').count(),
        },
        'bookings': Booking.objects.count(),
        'reports': {
            'total': Report.objects.count(),
            'pending': Report.objects.filter(status='pending').count(),
        },
    }
    
    return success_response(data=data, message='统计获取成功')
