"""
用户模块 Django Admin 配置

提供用户管理的后台界面。
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """用户管理后台
    
    扩展 Django 默认用户管理，增加角色、手机号等字段。
    """
    list_display = [
        'username', 'role', 'phone', 'community_name',
        'is_active', 'created_at'
    ]
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['username', 'phone', 'community_name']
    ordering = ['-created_at']
    
    # 扩展字段集
    fieldsets = BaseUserAdmin.fieldsets + (
        ('扩展信息', {
            'fields': ('role', 'phone', 'avatar', 'community_name', 'address')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('扩展信息', {
            'fields': ('role', 'phone', 'community_name')
        }),
    )
