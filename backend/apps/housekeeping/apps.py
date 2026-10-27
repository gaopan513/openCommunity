"""
家政服务模块应用配置
"""
from django.apps import AppConfig


class HousekeepingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.housekeeping'
    verbose_name = '家政服务'
