"""
家政服务模块路由配置

使用 DRF Router 注册视图集，统一挂载在 /api/v1/ 下。
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceCategoryViewSet, ServiceProviderViewSet, BookingViewSet

router = DefaultRouter()
router.register('housekeeping/categories', ServiceCategoryViewSet, basename='service-category')
router.register('housekeeping/providers', ServiceProviderViewSet, basename='service-provider')
router.register('housekeeping/bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),
]
