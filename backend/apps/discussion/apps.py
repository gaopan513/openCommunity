"""
自由发言模块应用配置
"""
from django.apps import AppConfig


class DiscussionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.discussion'
    verbose_name = '自由发言'
