"""
二手市场模块路由配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, ProductCategoryViewSet

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('product-categories', ProductCategoryViewSet, basename='product-category')

urlpatterns = [
    path('', include(router.urls)),
]
