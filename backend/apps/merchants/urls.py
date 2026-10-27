"""
商家管理模块路由配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('merchants', views.MerchantViewSet, basename='merchant')
router.register('merchant-categories', views.MerchantCategoryViewSet, basename='merchant-category')

urlpatterns = [
    path('', include(router.urls)),
]
