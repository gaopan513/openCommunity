"""
系统管理模块应用配置
"""
from django.apps import AppConfig


class AdminSystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.admin_system'
    verbose_name = '系统管理'
