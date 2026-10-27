"""
经验问答模块路由配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('questions', views.QuestionViewSet, basename='question')

urlpatterns = [
    path('', include(router.urls)),
]
