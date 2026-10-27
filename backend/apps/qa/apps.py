"""
经验问答模块应用配置
"""
from django.apps import AppConfig


class QaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.qa'
    verbose_name = '经验问答'
