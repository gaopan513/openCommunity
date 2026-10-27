"""
二手市场模块应用配置
"""
from django.apps import AppConfig


class SecondhandConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.secondhand'
    verbose_name = '二手市场'
