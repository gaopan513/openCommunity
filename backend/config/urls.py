"""
openCommunity 主路由配置

所有 API 路由统一挂载在 /api/v1/ 下。
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """健康检查接口
    
    用于验证后端服务是否正常运行。
    """
    return Response({
        'code': 0,
        'message': 'success',
        'data': {
            'status': 'healthy',
            'service': 'openCommunity API',
            'version': '1.0.0'
        }
    })


urlpatterns = [
    # Django Admin 后台
    path('admin/', admin.site.urls),
    
    # 健康检查
    path('api/v1/health/', health_check, name='health-check'),
    
    # 业务模块路由
    path('api/v1/auth/', include('apps.users.urls_auth')),
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/', include('apps.discussion.urls')),
    path('api/v1/', include('apps.qa.urls')),
    path('api/v1/', include('apps.secondhand.urls')),
    path('api/v1/', include('apps.merchants.urls')),
    path('api/v1/', include('apps.housekeeping.urls')),
    path('api/v1/', include('apps.admin_system.urls')),
]

# 开发环境提供媒体文件访问
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
