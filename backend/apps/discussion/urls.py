"""
自由发言模块路由配置

使用 DRF Router 自动注册 ViewSet 路由。
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('posts', views.PostViewSet, basename='post')

urlpatterns = [
    path('', include(router.urls)),
]
