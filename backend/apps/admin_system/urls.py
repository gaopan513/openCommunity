"""
系统管理模块路由配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('announcements', views.AnnouncementViewSet, basename='announcement')
router.register('admin/reports', views.ReportViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/statistics/', views.statistics_view, name='statistics'),
]
