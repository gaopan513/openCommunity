"""
用户认证路由

提供注册、登录、微信小程序登录、Token 刷新、登出等认证相关接口。
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('wechat-login/', views.WechatLoginView.as_view(), name='wechat-login'),
    path('debug-login/', views.DebugWechatLoginView.as_view(), name='debug-login'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
]
