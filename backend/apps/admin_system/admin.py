"""
系统管理模块 Django Admin 配置
"""
from django.contrib import admin
from .models import Announcement, Report


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """公告管理后台"""
    list_display = ['title', 'author', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'content']
    list_editable = ['is_active']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """举报管理后台"""
    list_display = ['content_type', 'object_id', 'reporter', 'status', 'created_at']
    list_filter = ['status', 'content_type', 'created_at']
    search_fields = ['reason', 'reporter__username']
    readonly_fields = ['reporter', 'content_type', 'object_id', 'reason', 'created_at']
