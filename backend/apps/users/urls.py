"""
用户资料路由

提供个人资料查看/编辑、修改密码等接口。
"""
from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.ProfileView.as_view(), name='user-profile'),
    path('password/', views.ChangePasswordView.as_view(), name='change-password'),
]
